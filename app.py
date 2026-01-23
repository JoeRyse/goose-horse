import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="World Handicapper Pro", page_icon="🏇", layout="wide")

# PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "history")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEETINGS_DIR = os.path.join(DOCS_DIR, "meetings")
SYSTEM_PATH = os.path.join(BASE_DIR, "logic", "master_system.md")

# Ensure directories exist
for d in [DATA_DIR, DOCS_DIR, MEETINGS_DIR]:
    os.makedirs(d, exist_ok=True)

# --- 1. AUTHENTICATION (MANUAL ONLY) ---
st.sidebar.header("🔑 Setup")

# Force clear old environment variables
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    st.sidebar.success(f"Key Set (Ends in ...{api_key[-4:]})")
else:
    st.warning("⚠️ Enter API Key to start.")
    st.stop()

# --- 2. HTML GENERATOR (NAVY & ORANGE THEME) ---
def generate_meeting_html(data):
    country = data['meta'].get('jurisdiction', 'International')
    
    # Header Section
    html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{data['meta']['track']} - Pro Form</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; font-size: 12px; color: #0f172a; margin: 0; padding: 30px; background: #fff; }}
            .container {{ max_width: 1000px; margin: 0 auto; }}
            .header {{ display: flex; align-items: center; border-bottom: 4px solid #003366; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ max-height: 120px; margin-right: 30px; }}
            .header-info h1 {{ margin: 0; font-size: 32px; color: #003366; text-transform: uppercase; font-weight: 800; }}
            .race-section {{ margin-bottom: 40px; border: 1px solid #e2e8f0; break-inside: avoid; background: #fff; }}
            .race-header {{ background: #fff; color: #003366; padding: 12px 20px; border-bottom: 3px solid #ff6b00; display: flex; justify-content: space-between; align-items: center; }}
            .race-title {{ font-weight: 800; font-size: 20px; text-transform: uppercase; }}
            .race-conf {{ background: #003366; color: #fff; padding: 4px 10px; border-radius: 4px; font-weight: 700; }}
            .picks-container {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; padding: 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
            .pick-panel {{ background: #fff; padding: 15px; border: 1px solid #e2e8f0; }}
            .panel-top {{ border-top: 5px solid #003366; }}
            .panel-danger {{ border-top: 5px solid #d97706; }}
            .panel-value {{ border-top: 5px solid #ff6b00; }}
            .panel-label {{ font-weight: 900; font-size: 11px; color: #64748b; display: block; margin-bottom: 5px; }}
            .pick-main {{ font-size: 16px; font-weight: 700; color: #0f172a; }}
            .pick-detail {{ font-size: 12px; color: #444; font-style: italic; line-height: 1.4; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ background: #f1f5f9; color: #003366; border-bottom: 2px solid #003366; padding: 10px; text-align: left; font-weight: 800; }}
            td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; }}
            .row-top-pick {{ background-color: #f0f9ff; font-weight: 700; border-left: 4px solid #ff6b00; }}
            .btn-print {{ position: fixed; top: 20px; right: 20px; background: #ff6b00; color: #fff; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }}
            @media print {{ .btn-print {{ display: none; }} body {{ padding: 0; }} .race-section {{ border: 1px solid #000; }} }}
        </style>
    </head>
    <body>
        <button class="btn-print" onclick="window.print()">🖨️ PRINT FORM</button>
        <div class="container">
            <div class="header">
                <img src="../logo.png" class="logo" alt="Logo">
                <div class="header-info">
                    <h1>{data['meta']['track']}</h1>
                    <div class="meta">{data['meta']['date']} • {data['meta']['track_condition']}</div>
                </div>
            </div>
    """

    # Loop Races
    for race in data['races']:
        picks = race.get('picks', {})
        top = picks.get('top_pick', {})
        danger = picks.get('danger_horse', {})
        value = picks.get('value_bet', {})
        strat = race.get('exotic_strategy', {})
        
        html += f"""
        <div class="race-section">
            <div class="race-header">
                <div class="race-title">RACE {race['number']} - {race.get('distance','')}</div>
                <div class="race-conf">{race.get('confidence_level', 'Standard')}</div>
            </div>
            <div class="picks-container">
                <div class="pick-panel panel-top"><span class="panel-label">⭐ BEST BET</span><div class="pick-main">#{top.get('number')} {top.get('name')}</div><div class="pick-detail">{top.get('reason')}</div></div>
                <div class="pick-panel panel-danger"><span class="panel-label">⚠️ DANGER</span><div class="pick-main">#{danger.get('number')} {danger.get('name')}</div><div class="pick-detail">{danger.get('reason')}</div></div>
                <div class="pick-panel panel-value"><span class="panel-label">💰 VALUE</span><div class="pick-main">#{value.get('number')} {value.get('name')}</div><div class="pick-detail">{value.get('odds')}</div></div>
            </div>
            <div style="padding: 20px;">
                <table>
                    <thead><tr><th>#</th><th>Horse</th><th>Rating</th><th>Barrier</th><th>Verdict</th></tr></thead>
                    <tbody>
        """
        for c in race.get('contenders', [])[:6]:
            row_class = "row-top-pick" if str(c.get('number')) == str(top.get('number')) else ""
            html += f'<tr class="{row_class}"><td>{c.get("number")}</td><td>{c.get("name")}</td><td>{c.get("rating")}</td><td>{c.get("barrier")}</td><td>{c.get("verdict", "")}</td></tr>'
        
        html += f"""
                    </tbody>
                </table>
                <div style="margin-top:15px; padding:10px; background:#f8fafc; border-top:1px solid #e2e8f0; color:#334155;">
                    <b>STRATEGY:</b> Exacta: {strat.get('exacta')} | Trifecta: {strat.get('trifecta')}
                </div>
            </div>
        </div>
        """
        
    html += "</div></body></html>"
    return html

# --- 3. HOMEPAGE UPDATER ---
def update_homepage():
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    grouped_files = {}
    
    for f in files:
        country = "International"
        try:
            with open(os.path.join(MEETINGS_DIR, f), 'r', encoding='utf-8') as file_obj:
                line = file_obj.readline()
                if "META_COUNTRY" in line:
                    country = line.split("META_COUNTRY:")[1].split("-->")[0].strip()
        except:
            pass
        if country not in grouped_files:
            grouped_files[country] = []
        grouped_files[country].append(f)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>World Handicapper HQ</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { margin: 0; font-family: 'Segoe UI', sans-serif; background: #ffffff; color: #333; }
            .hero { text-align: center; padding: 50px 20px; background: #fff; border-bottom: 4px solid #003366; }
            .logo { max-height: 120px; margin-bottom: 20px; }
            h1 { margin: 0; color: #003366; text-transform: uppercase; font-size: 2.2rem; font-weight: 800; }
            .subtitle { color: #666; font-size: 1.1rem; margin-top: 5px; }
            .container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; }
            .section-title { border-bottom: 3px solid #ff6b00; padding-bottom: 10px; margin: 50px 0 30px 0; font-size: 1.6rem; color: #003366; font-weight: 700; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }
            .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; transition: all 0.2s; text-decoration: none; color: #333; display: block; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .card:hover { transform: translateY(-4px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); border-color: #ff6b00; }
            .card-body { padding: 20px; }
            .track-name { font-size: 1.3rem; font-weight: 700; color: #003366; display: block; }
            .status { color: #ff6b00; font-size: 0.8rem; font-weight: 800; margin-top: 15px; display: block; text-transform: uppercase; }
        </style>
    </head>
    <body>
        <div class="hero">
            <img src="logo.png" class="logo">
            <h1>World Handicapper</h1>
            <div class="subtitle">Professional Racing Intelligence</div>
        </div>
        <div class="container">
    """
    
    for country, files in grouped_files.items():
        flag = "🇦🇺" if "Australia" in country else "🇺🇸" if "USA" in country else "🌍"
        html += f'<div class="section-title">{flag} {country} Racing</div><div class="grid">'
        
        for f in sorted(files, reverse=True):
            display_name = f.replace(".html","").replace("_"," ")
            html += f"""
            <a href="meetings/{f}" class="card">
                <div class="card-body">
                    <span class="track-name">{display_name}</span>
                    <span class="status">● View Form</span>
                </div>
            </a>
            """
            
        html += "</div>"
        
    html += """
        </div>
    </body>
    </html>
    """
    
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding='utf-8') as f:
        f.write(html)

# --- 4. MAIN APP LOGIC ---
st.title("🏆 World Handicapper Pro")
uploaded_file = st.file_uploader("Upload Race Card (PDF)", type="pdf")

# SCRATCHINGS BOX (Restored)
scratches = st.text_area("📋 Scratchings & Track Updates", height=100, 
    placeholder="e.g., Race 4: #3 Scratched. Track downgraded to Heavy 8.")

if uploaded_file:
    if st.button("Analyze Meeting"):
        with st.spinner("Analyzing Race Card (Gemini 3)..."):
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                text = "".join([page.extract_text() for page in reader.pages])
                
                # Force UTF-8 encoding
                with open(SYSTEM_PATH, 'r', encoding='utf-8') as f: 
                    system_logic = f.read()
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3-pro-preview')
                
                prompt = f"{system_logic}\n\nIMPORTANT UPDATES/SCRATCHINGS:\n{scratches}\n\nANALYZE THIS RACE CARD. Return valid JSON only.\n\nDATA:\n{text}"
                response = model.generate_content(prompt)
                
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                
                # --- FIX: SANITIZE FILENAME (Remove / and ,) ---
                safe_date = data['meta']['date'].replace('/', '-').replace(',', '').replace(' ', '_')
                safe_track = data['meta']['track'].replace(' ', '_')
                filename = f"{safe_track}_{safe_date}.html"
                
                filepath = os.path.join(MEETINGS_DIR, filename)
                with open(filepath, "w", encoding='utf-8') as f: f.write(generate_meeting_html(data))
                
                update_homepage()
                st.success(f"✅ Analysis Complete! Saved to {filename}")
                st.markdown(f"[View Report](file:///{filepath})", unsafe_allow_html=True)
                
                if st.button("🚀 Publish to Website"): st.info("Files updated. Run deploy.bat to push.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")