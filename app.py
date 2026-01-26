import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import json
import time
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="World Handicapper Pro", page_icon="🏇", layout="wide")

# PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "history")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEETINGS_DIR = os.path.join(DOCS_DIR, "meetings")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SYSTEM_PATH = os.path.join(BASE_DIR, "logic", "master_system.md")
PROFILES_DIR = os.path.join(BASE_DIR, "logic", "profiles")

# Ensure directories exist
for d in [DATA_DIR, DOCS_DIR, MEETINGS_DIR, PROFILES_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

# --- 1. SIDEBAR CONFIGURATION ---
st.sidebar.header("🔑 Setup & Config")

# API Key
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
    genai.configure(api_key=api_key)

# --- HARDCODED MODEL ---
# Forcing the specific preview model as requested
model_name = "gemini-3-pro-preview"

# --- TRACK PROFILES ---
st.sidebar.subheader("📍 Track Profile")
profile_files = ["None (Generic)"] + [f for f in os.listdir(PROFILES_DIR) if f.endswith(".md") or f.endswith(".txt")]
selected_profile = st.sidebar.selectbox("Select Profile Logic", profile_files)

# --- REGION & TRACK SELECTION ---
st.sidebar.subheader("🌍 Race Settings")

TRACK_LISTS = {
    "UK/Ireland": ["Wolverhampton", "Kempton", "Lingfield", "Newcastle", "Southwell", "Chelmsford", "Ascot", "Other"],
    "USA": ["Gulfstream Park", "Santa Anita", "Aqueduct", "Other"],
    "Australia": ["Flemington", "Randwick", "Moonee Valley", "Wagga", "Other"],
    "Hong Kong": ["Sha Tin", "Happy Valley", "Other"],
    "Japan": ["Tokyo", "Nakayama", "Other"],
    "International": ["Other"]
}

region = st.sidebar.selectbox("Region", list(TRACK_LISTS.keys()), index=0)

if region in TRACK_LISTS:
    selected_track = st.sidebar.selectbox("Track Name", TRACK_LISTS[region])
    if selected_track == "Other":
        track_name = st.sidebar.text_input("Enter Manual Track Name", placeholder="e.g. Brighton")
    else:
        track_name = selected_track
else:
    track_name = st.sidebar.text_input("Track Name", placeholder="e.g. Wolverhampton")

if not api_key:
    st.warning("⚠️ Enter API Key to start.")
    st.stop()

# --- 2. HTML GENERATOR ---
def generate_meeting_html(data):
    meta = data.get('meta', {})
    track_display = meta.get('track', 'Unknown Track')
    date_display = meta.get('date', 'Unknown Date')
    
    html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{track_display} - Pro Form</title>
        <style>
            /* SCREEN STYLES */
            body {{ font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #0f172a; margin: 0; background: #f1f5f9; padding-bottom: 50px; }}
            .container {{ max_width: 1000px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #fff; padding: 20px; border-radius: 8px; border-bottom: 4px solid #003366; display: flex; align-items: center; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            .logo {{ max-height: 80px; margin-right: 20px; }}
            .header h1 {{ margin: 0; color: #003366; font-size: 28px; text-transform: uppercase; }}
            .meta {{ color: #64748b; font-weight: 600; margin-top: 5px; }}
            .nav-bar {{ background: #003366; padding: 10px; border-radius: 8px; margin-bottom: 20px; overflow-x: auto; white-space: nowrap; display: flex; gap: 10px; }}
            .nav-btn {{ color: #fff; text-decoration: none; padding: 8px 15px; background: rgba(255,255,255,0.1); border-radius: 4px; font-weight: bold; font-size: 13px; transition: background 0.2s; }}
            .nav-btn:hover {{ background: #ff6b00; }}
            
            .race-section {{ background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); scroll-margin-top: 20px; }}
            .race-header {{ background: #fff; border-bottom: 3px solid #ff6b00; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }}
            .race-title {{ font-size: 18px; font-weight: 800; color: #003366; }}
            .race-conf {{ background: #003366; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            
            .picks-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; padding: 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
            .pick-panel {{ background: #fff; padding: 15px; border: 1px solid #e2e8f0; border-radius: 6px; }}
            .panel-top {{ border-top: 4px solid #003366; }}
            .panel-danger {{ border-top: 4px solid #d97706; }}
            .panel-value {{ border-top: 4px solid #ff6b00; }}
            
            .label {{ font-size: 10px; font-weight: 900; color: #64748b; letter-spacing: 0.5px; text-transform: uppercase; display: block; margin-bottom: 5px; }}
            .horse-name {{ font-size: 16px; font-weight: 800; color: #0f172a; }}
            .reason {{ font-size: 12px; color: #475569; margin-top: 5px; line-height: 1.4; font-style: italic; }}
            
            .table-container {{ padding: 0 20px 20px 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
            th {{ text-align: left; padding: 10px; background: #f1f5f9; color: #475569; font-weight: 700; border-bottom: 2px solid #cbd5e1; }}
            td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; color: #334155; }}
            .highlight-row {{ background: #f0f9ff; font-weight: 600; border-left: 3px solid #003366; }}
            .strategy-box {{ margin: 0 20px 20px 20px; background: #fff7ed; border: 1px solid #ffedd5; border-left: 4px solid #ff6b00; padding: 15px; border-radius: 4px; color: #9a3412; font-size: 13px; }}
            
            .btn-print {{ position: fixed; bottom: 20px; right: 20px; background: #003366; color: #fff; padding: 12px 25px; border-radius: 30px; font-weight: bold; cursor: pointer; border: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2); z-index: 999; }}

            /* PRINT STYLES */
            @media print {{
                .btn-print, .nav-bar {{ display: none !important; }}
                body {{ background: #fff; margin: 0; padding: 0; font-size: 11px; }}
                .container {{ width: 100%; max-width: 100%; margin: 0; padding: 0; }}
                .header {{ border-bottom: 2px solid #003366; padding: 10px; margin-bottom: 15px; border-radius: 0; box-shadow: none; }}
                .header h1 {{ font-size: 22px; }}
                .logo {{ max-height: 50px; margin-right: 15px; }}
                .race-section {{ break-inside: avoid; page-break-inside: avoid; border: 1px solid #ccc; margin-bottom: 15px; box-shadow: none; border-radius: 4px; }}
                .race-header {{ padding: 8px 12px; border-bottom: 2px solid #ff6b00; }}
                .race-title {{ font-size: 14px; }}
                .race-conf {{ padding: 2px 8px; font-size: 10px; }}
                .picks-container {{ display: flex; gap: 10px; padding: 10px; }}
                .pick-panel {{ flex: 1; padding: 8px; border: 1px solid #eee; }}
                .horse-name {{ font-size: 13px; }}
                .reason {{ font-size: 10px; line-height: 1.2; }}
                .table-container {{ padding: 0 10px 10px 10px; }}
                table {{ font-size: 10px; }}
                th, td {{ padding: 4px 6px; }}
                .strategy-box {{ margin: 0 10px 10px 10px; padding: 8px; font-size: 11px; }}
            }}
        </style>
    </head>
    <body>
        <button class="btn-print" onclick="window.print()">🖨️ Print Form</button>
        <div class="container">
            <div class="header">
                <img src="../logo.png" class="logo" alt="World Handicapper">
                <div class="header-info">
                    <h1>{track_display}</h1>
                    <div class="meta">{date_display} • {meta.get('track_condition', 'N/A')}</div>
                </div>
            </div>
            <div class="nav-bar">
    """
    for race in data.get('races', []):
        r_num = race.get('number', '?')
        html += f'<a href="#race-{r_num}" class="nav-btn">Race {r_num}</a>'
    
    html += """</div>"""

    for race in data.get('races', []):
        r_num = race.get('number', '?')
        picks = race.get('picks', {})
        top = picks.get('top_pick', {})
        danger = picks.get('danger_horse', {})
        value = picks.get('value_bet', {})
        strat = race.get('exotic_strategy', {})
        
        html += f"""
        <div id="race-{r_num}" class="race-section">
            <div class="race-header">
                <div class="race-title">RACE {r_num} - {race.get('distance','')}</div>
                <div class="race-conf">{race.get('confidence_level', 'Standard')}</div>
            </div>
            <div class="picks-container">
                <div class="pick-panel panel-top">
                    <span class="label">⭐ BEST BET</span>
                    <div class="horse-name">#{top.get('number', '?')} {top.get('name', 'TBD')}</div>
                    <div class="reason">{top.get('reason', 'Analysis pending...')}</div>
                </div>
                <div class="pick-panel panel-danger">
                    <span class="label">⚠️ DANGER</span>
                    <div class="horse-name">#{danger.get('number', '?')} {danger.get('name', 'TBD')}</div>
                    <div class="reason">{danger.get('reason', 'Analysis pending...')}</div>
                </div>
                <div class="pick-panel panel-value">
                    <span class="label">💰 VALUE</span>
                    <div class="horse-name">#{value.get('number', '?')} {value.get('name', 'TBD')}</div>
                    <div class="reason">{value.get('odds', 'TBD')}</div>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead><tr><th>#</th><th>Horse</th><th>Rating</th><th>Barrier</th><th>Verdict</th></tr></thead>
                    <tbody>
        """
        for c in race.get('contenders', [])[:6]:
            row_class = "highlight-row" if str(c.get('number')) == str(top.get('number')) else ""
            html += f'<tr class="{row_class}"><td>{c.get("number")}</td><td>{c.get("name")}</td><td>{c.get("rating")}</td><td>{c.get("barrier")}</td><td>{c.get("verdict", "")}</td></tr>'
        html += f"""
                    </tbody>
                </table>
            </div>
            <div class="strategy-box">
                <b>BETTING STRATEGY:</b> Exacta: {strat.get('exacta')} | Trifecta: {strat.get('trifecta')}
            </div>
        </div>
        """
    html += "</div></body></html>"
    return html

# --- 3. HOMEPAGE UPDATER ---
def update_homepage():
    if not os.path.exists(MEETINGS_DIR): return
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    grouped_files = {}
    for f in files:
        country = "International"
        try:
            with open(os.path.join(MEETINGS_DIR, f), 'r', encoding='utf-8') as file_obj:
                content = file_obj.read()
                if "Australia" in content: country = "Australia"
                elif "USA" in content: country = "USA"
                elif "UK" in content or "Great Britain" in content: country = "UK/Ireland"
        except: pass
        if country not in grouped_files: grouped_files[country] = []
        grouped_files[country].append(f)

    html = """<!DOCTYPE html><html><head><title>World Handicapper HQ</title>
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
    </style></head><body>
    <div class="hero"><img src="logo.png" class="logo"><h1>World Handicapper</h1><div class="subtitle">Professional Racing Intelligence</div></div>
    <div class="container">"""
    
    for country, files in grouped_files.items():
        flag = "🇦🇺" if "Australia" in country else "🇺🇸" if "USA" in country else "🌍"
        html += f'<div class="section-title">{flag} {country} Racing</div><div class="grid">'
        for f in sorted(files, reverse=True):
            html += f'<a href="meetings/{f}" class="card"><div class="card-body"><span class="track-name">{f.replace(".html","").replace("_"," ")}</span><span class="status">● View Form</span></div></a>'
        html += "</div>"
    html += "</div></body></html>"
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding='utf-8') as f: f.write(html)

# --- 4. MAIN APP LOGIC ---
st.title("🏆 World Handicapper Pro")
uploaded_file = st.file_uploader("Upload Race Card (PDF)", type="pdf")
scratches = st.text_area("📋 Scratchings & Updates", height=100, placeholder="e.g. Race 1: #4 Scratched")

DEFAULT_SYSTEM_PROMPT = """
You are a professional horse racing handicapper.
Analyze the provided race card data and output your response in strict JSON format.
**IMPORTANT:** 1. If the race card uses TIMES (e.g. 17:30), treat them as Race 1, Race 2, etc.
2. Ensure every race has a 'number' key (1, 2, 3...).
"""

if uploaded_file:
    if st.button("Analyze Meeting"):
        with st.spinner("Analyzing..."):
            try:
                # 1. Read PDF
                reader = PyPDF2.PdfReader(uploaded_file)
                text = "".join([page.extract_text() for page in reader.pages])
                
                # 2. Load Logic
                if os.path.exists(SYSTEM_PATH):
                    with open(SYSTEM_PATH, 'r') as f: system_logic = f.read()
                else:
                    system_logic = DEFAULT_SYSTEM_PROMPT

                # 3. Profile Logic
                profile_logic = ""
                profile_source = "None"
                
                auto_filename_1 = f"{track_name}.md"
                auto_filename_2 = f"{track_name.replace(' ', '_')}.md"
                path_1 = os.path.join(PROFILES_DIR, auto_filename_1)
                path_2 = os.path.join(PROFILES_DIR, auto_filename_2)
                
                if os.path.exists(path_1):
                    with open(path_1, 'r') as f: profile_logic = f.read()
                    profile_source = f"✅ Auto-Loaded: {auto_filename_1}"
                elif os.path.exists(path_2):
                    with open(path_2, 'r') as f: profile_logic = f.read()
                    profile_source = f"✅ Auto-Loaded: {auto_filename_2}"
                elif selected_profile != "None (Generic)":
                    p_path = os.path.join(PROFILES_DIR, selected_profile)
                    if os.path.exists(p_path):
                        with open(p_path, 'r') as f: profile_logic = f.read()
                        profile_source = f"📂 Manual Selection: {selected_profile}"

                st.session_state['profile_source'] = profile_source 

                # 4. Prompt with UK Fix
                model = genai.GenerativeModel(model_name)
                prompt = f"""
                {system_logic}
                
                *** TRACK PROFILE ({profile_source}) ***
                {profile_logic}
                
                *** CONTEXT ***
                Region: {region}
                Track: {track_name}
                Updates: {scratches}
                
                *** CRITICAL DATA INSTRUCTIONS ***
                1. SEARCH FOR 'RACE CODES': Look for codes like 'wol01', 'wol02', 'kem01'. 
                   - 'wol01' = Race 1
                   - 'wol02' = Race 2
                   - etc.
                2. SEARCH FOR 'RACE HEADERS': Look for "Race 1", "R1", "First Race".
                3. IF NO NUMBERS FOUND: Use the Start Time. The earliest time is Race 1.
                
                *** OUTPUT FORMAT ***
                Return valid JSON only. Every race MUST have a "number": integer field.
                
                DATA:
                {text} 
                """

                # 5. AI Call
                response = model.generate_content(prompt)
                
                # 6. Process Output
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                try:
                    data = json.loads(clean_json)
                    
                    # --- AUTO-FIX RACE NUMBERS (Self-Healing) ---
                    # If AI still messes up, force sequential numbering
                    if 'races' in data:
                        for i, race in enumerate(data['races']):
                            if 'number' not in race or not str(race['number']).isdigit():
                                race['number'] = i + 1

                    st.session_state['data'] = data
                except json.JSONDecodeError:
                    st.error("AI returned invalid JSON. Try again.")
                    st.stop()
                
                # 7. AUTO-SAVE LOGIC
                meta = data.get('meta', {})
                track_safe = meta.get('track', track_name).replace(' ', '_')
                date_safe = meta.get('date', 'Unknown_Date')
                
                # A. Save JSON
                json_filename = f"{track_safe}_{date_safe}.json"
                json_path = os.path.join(LOGS_DIR, json_filename)
                with open(json_path, "w", encoding='utf-8') as f:
                    f.write(clean_json)
                st.session_state['json_path'] = json_path
                
                # B. Save HTML
                html_filename = f"{track_safe}_{date_safe}.html"
                html_path = os.path.join(MEETINGS_DIR, html_filename)
                st.session_state['html_path'] = html_path
                
                html_content = generate_meeting_html(data)
                with open(html_path, "w", encoding='utf-8') as f: f.write(html_content)
                
                update_homepage()
                
                st.success(f"✅ Analysis Complete! (Saved to logs/{json_filename})")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- POST-ANALYSIS UI (Persistent) ---
if 'data' in st.session_state:
    st.info(f"🧠 Logic Engine: {st.session_state.get('profile_source', 'Unknown')}")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        html_path = st.session_state.get('html_path')
        if html_path:
            st.markdown(f"### 📄 [View Form Guide](file:///{html_path})")
            
    with col2:
        # Download JSON Button
        json_str = json.dumps(st.session_state['data'], indent=2)
        track_display = st.session_state['data'].get('meta', {}).get('track', 'RaceData').replace(' ', '_')
        st.download_button(
            label="⬇️ Download JSON",
            data=json_str,
            file_name=f"{track_display}.json",
            mime="application/json"
        )
    
    with col3:
        if st.button("🚀 Publish to Website"):
            st.info("Triggering deployment...")
            try:
                os.system("deploy.bat")
                st.success("Deployment Script Started.")
            except Exception as e:
                st.error(f"Failed to run deploy.bat: {e}")