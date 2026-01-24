import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import os
import json
import time
import re
import subprocess
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Exacta AI", page_icon="🏇", layout="wide")

# PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEETINGS_DIR = os.path.join(DOCS_DIR, "meetings")
LOGIC_DIR = os.path.join(BASE_DIR, "logic")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Ensure directories exist
for d in [DATA_DIR, DOCS_DIR, MEETINGS_DIR, LOGIC_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

# --- SESSION STATE ---
if 'html_content' not in st.session_state: st.session_state.html_content = None
if 'preview_html' not in st.session_state: st.session_state.preview_html = None
if 'report_filename' not in st.session_state: st.session_state.report_filename = None
if 'raw_response' not in st.session_state: st.session_state.raw_response = ""
if 'data_ready' not in st.session_state: st.session_state.data_ready = False

# --- HELPER FUNCTIONS ---

def clean_json_string(json_str):
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*$', '', json_str)
    return json_str.strip()

def update_homepage():
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    grouped_files = {}
    for f in files:
        country = "International"
        try:
            with open(os.path.join(MEETINGS_DIR, f), 'r', encoding='utf-8') as file_obj:
                line = file_obj.readline()
                if "META_COUNTRY" in line: country = line.split("META_COUNTRY:")[1].split("-->")[0].strip()
        except: pass
        if country not in grouped_files: grouped_files[country] = []
        grouped_files[country].append(f)

    html = """<!DOCTYPE html><html><head><title>Exacta AI</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body { margin: 0; font-family: 'Segoe UI', sans-serif; background: #f8fafc; color: #333; } .hero { background: #fff; border-bottom: 4px solid #003366; padding: 40px 0; } .container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; } .section-title { border-bottom: 3px solid #ff6b00; padding-bottom: 10px; margin: 40px 0 20px 0; font-size: 1.5rem; color: #003366; font-weight: 700; } .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; } .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; text-decoration: none; color: #333; display: block; box-shadow: 0 2px 4px rgba(0,0,0,0.05); } .card:hover { transform: translateY(-3px); border-color: #ff6b00; } .card-body { padding: 20px; } .track-name { font-size: 1.2rem; font-weight: 700; color: #0f172a; display: block; } .status { color: #ff6b00; font-size: 0.8rem; font-weight: 700; margin-top: 10px; display: block; text-transform: uppercase; }</style></head><body><div class="hero"><div class="container" style="padding:0"><h1>Race Intelligence</h1></div></div><div class="container">"""
    
    display_order = ["USA", "Australia", "UK", "Japan", "International"]
    for key in display_order:
        if key in grouped_files:
            html += f'<div class="section-title">{key} Racing</div><div class="grid">'
            for f in sorted(grouped_files[key], reverse=True):
                display_name = f.replace(".html","").replace("_"," ")
                html += f'<a href="meetings/{f}" class="card"><div class="card-body"><span class="track-name">{display_name}</span><span class="status">● View Form</span></div></a>'
            html += "</div>"
            del grouped_files[key]
    
    for key, files in grouped_files.items():
        html += f'<div class="section-title">{key} Racing</div><div class="grid">'
        for f in sorted(files, reverse=True):
            display_name = f.replace(".html","").replace("_"," ")
            html += f'<a href="meetings/{f}" class="card"><div class="card-body"><span class="track-name">{display_name}</span><span class="status">● View Form</span></div></a>'
        html += "</div>"
    
    html += "</div></body></html>"
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding='utf-8') as f: f.write(html)

def generate_meeting_html(data, region_override, is_preview_mode=False):
    country = data.get('meta', {}).get('jurisdiction', region_override)
    track_name = data.get('meta', {}).get('track', 'Unknown Track')
    track_date = data.get('meta', {}).get('date', 'Unknown Date')
    track_cond = data.get('meta', {}).get('track_condition', 'Standard')
    
    # --- FIND BEST BETS OF THE DAY ---
    # We look for races with "High" confidence or "5 Stars"
    best_bets = []
    for r in data.get('races', []):
        conf = str(r.get('confidence_level', ''))
        top_pick = r.get('picks', {}).get('top_pick', {})
        if ("High" in conf or "5 Stars" in conf or "Best Bet" in conf) and top_pick.get('name'):
            best_bets.append({
                "race": r.get('number'),
                "horse": f"#{top_pick.get('number')} {top_pick.get('name')}",
                "reason": top_pick.get('reason', '')[:100] + "..."
            })
    
    best_bets_html = ""
    if best_bets:
        best_bets_html = '<div style="background:#fffbeb; border:2px solid #fbbf24; padding:20px; margin-bottom:30px; border-radius:8px;">'
        best_bets_html += '<h2 style="margin-top:0; color:#b45309;">🔥 PRIME BETS OF THE DAY</h2><div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); gap:15px;">'
        for bb in best_bets[:3]: # Top 3 only
            best_bets_html += f'<div><div style="font-weight:bold; font-size:1.1em;">Race {bb["race"]}: {bb["horse"]}</div><div style="font-size:0.9em; color:#555;">{bb["reason"]}</div></div>'
        best_bets_html += '</div></div>'

    # --- NAVIGATION ---
    nav_links = ""
    if not is_preview_mode:
        for r in data.get('races', []):
            r_num = r.get('number', '0')
            nav_links += f'<a href="#race-{r_num}" class="nav-btn">R{r_num}</a>'
    else:
        for r in data.get('races', []):
            r_num = r.get('number', '0')
            nav_links += f'<span class="nav-btn" style="cursor:default; opacity:0.7">R{r_num}</span>'

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{track_name}</title>
    <style>body{{font-family:'Segoe UI',sans-serif;background:#fff;color:#0f172a;padding:30px}}
    .header{{border-bottom:4px solid #003366;padding-bottom:20px;margin-bottom:20px}}
    .race-section{{margin-bottom:40px;border:1px solid #e2e8f0;background:#fff}}
    .race-header{{background:#fff;border-bottom:3px solid #ff6b00;padding:12px 20px;display:flex;justify-content:space-between;font-weight:800;color:#003366;font-size:20px}}
    .nav-btn{{background:#fff;border:1px solid #003366;color:#003366;padding:5px 10px;text-decoration:none;margin-right:5px;border-radius:4px;font-weight:700}}
    .nav-btn:hover{{background:#003366;color:#fff}}
    .picks-grid{{display:flex; gap:10px; padding:15px; background:#f8fafc; border-bottom:1px solid #e2e8f0; flex-wrap:wrap;}}
    .pick-box{{flex:1; min-width:200px; background:#fff; padding:10px; border:1px solid #e2e8f0; border-top:4px solid #94a3b8}}
    
    .panel-best{{border-top-color:#fbbf24; background-color:#fffbeb}}
    .panel-top{{border-top-color:#3b82f6}}
    .panel-danger{{border-top-color:#d97706}}
    .panel-value{{border-top-color:#10b981}}
    
    .exacta-box{{margin-top:10px; padding:10px; background:#f1f5f9; border-left:4px solid #64748b;}}
    .exacta-gold{{background:#fffbeb; border-left-color:#fbbf24;}}
    
    table{{width:100%;border-collapse:collapse;margin-top:10px}} th{{background:#f1f5f9;text-align:left;padding:8px}} td{{padding:8px;border-bottom:1px solid #eee}}
    .row-top{{background:#f0f9ff;font-weight:700}}
    </style></head><body>
    <div style="max-width:1000px;margin:0 auto">
    <div class="header"><h1>{track_name}</h1><div>{track_date} • {track_cond}</div></div>
    
    {best_bets_html}
    
    <div style="margin-bottom:20px"><b>RACES:</b> {nav_links}</div>"""

    for r in data.get('races', []):
        r_num = r.get('number', '?')
        confidence = str(r.get('confidence_level', ''))
        
        # --- DYNAMIC DISPLAY LOGIC ---
        is_best_bet = "High" in confidence or "Strong" in confidence or "5 Stars" in confidence
        
        # Top Pick (Always Show)
        top = r.get('picks', {}).get('top_pick', {})
        top_name = top.get('name', 'N/A')
        top_class = "panel-best" if is_best_bet else "panel-top"
        top_label = "🔥 BEST BET" if is_best_bet else "🏁 TOP PICK"
        
        # Danger (Hide if empty or None)
        dang = r.get('picks', {}).get('danger_horse', {})
        dang_name = dang.get('name', '')
        show_danger = dang_name and str(dang_name).lower() not in ['none', 'n/a', 'null']
        
        # Value (Hide if empty or None)
        val = r.get('picks', {}).get('value_bet', {})
        val_name = val.get('name', '')
        show_value = val_name and str(val_name).lower() not in ['none', 'n/a', 'null']
        
        # Exacta Styling
        exacta_strat = r.get('exotic_strategy', {}).get('exacta', '')
        exacta_class = "exacta-gold" if is_best_bet and len(exacta_strat) > 3 else "exacta-box"

        html += f"""<div id="race-{r_num}" class="race-section">
        <div class="race-header"><div>RACE {r_num} - {r.get('distance','')}</div><div>{confidence}</div></div>
        <div class="picks-grid">
            <div class="pick-box {top_class}"><b>{top_label}: #{top.get('number','')} {top_name}</b><br><small>{top.get('reason','')}</small></div>"""
            
        if show_danger:
            html += f"""<div class="pick-box panel-danger"><b>⚠️ DANGER: #{dang.get('number','')} {dang.get('name','')}</b><br><small>{dang.get('reason','')}</small></div>"""
            
        if show_value:
            html += f"""<div class="pick-box panel-value"><b>💰 VALUE: #{val.get('number','')} {val.get('name','')}</b><br><small>{val.get('reason','')}</small></div>"""
            
        html += f"""</div>
        <div style="padding:15px"><table><thead><tr><th>#</th><th>Horse</th><th>Rating</th><th>Verdict</th></tr></thead><tbody>"""
        
        for c in r.get('contenders', [])[:6]:
            style = ' class="row-top"' if str(c.get('number')) == str(top.get('number')) else ''
            html += f"<tr{style}><td>{c.get('number')}</td><td>{c.get('name')}</td><td>{c.get('rating')}</td><td>{c.get('verdict')}</td></tr>"
            
        if len(exacta_strat) > 3:
            html += f"""</tbody></table><div class="{exacta_class}"><b>EXACTA STRATEGY:</b> {exacta_strat}</div></div></div>"""
        else:
            html += "</tbody></table></div></div>"
    
    html += "</div></body></html>"
    return html

# --- AUTO-UPDATE INDEX ---
update_homepage()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Settings")
if "GEMINI_API_KEY" in os.environ: del os.environ["GEMINI_API_KEY"]
api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.subheader("🤖 AI Model")
model_options = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
    "gemini-3-pro-preview",
    "Custom"
]
target_model = st.sidebar.selectbox("Select Model", model_options, index=0)
if target_model == "Custom":
    target_model = st.sidebar.text_input("Enter Model Name", value="gemini-1.5-pro")

if api_key:
    genai.configure(api_key=api_key)
    st.sidebar.success(f"Ready: {target_model}")

# Country/Track Selection
track_db = {}
try:
    with open(os.path.join(DATA_DIR, "track_db.json"), "r") as f: track_db = json.load(f)
except: pass

st.sidebar.markdown("---")
country_options = list(track_db.keys()) if track_db else ["USA", "Australia", "International"]
selected_country = st.sidebar.selectbox("Region", country_options)

selected_track_data = None
selected_track_name = "Unknown"
if track_db and selected_country in track_db:
    selected_track_name = st.sidebar.selectbox("Track", list(track_db[selected_country].keys()))
    selected_track_data = track_db[selected_country][selected_track_name]

# Logic Mapping
if "USA" in selected_country: region_code, system_file = "USA", "system_usa.md"
elif "Australia" in selected_country: region_code, system_file = "Australia", "system_aus.md"
elif "UK" in selected_country: region_code, system_file = "UK", "system_uk.md"
else: region_code, system_file = "International", "system_aus.md"
if not os.path.exists(os.path.join(LOGIC_DIR, system_file)) and "UK" in region_code: system_file = "system_aus.md"

# --- MAIN UI ---
st.title(f"🏆 Exacta AI: {selected_track_name}")

uploaded_file = st.file_uploader(f"Upload {region_code} PDF", type="pdf")
scratches = st.text_area("📋 Scratchings / Updates", height=70)

if st.button("Analyze Race Card (Preview Only)", type="primary"):
    if not uploaded_file or not api_key:
        st.error("Please provide an API Key and a PDF file.")
    else:
        with st.spinner(f"Reading and Analyzing with {target_model}..."):
            try:
                # 1. SAVE UPLOAD TO TEMP FILE
                temp_pdf_path = os.path.join(TEMP_DIR, "current_card.pdf")
                with open(temp_pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 2. UPLOAD TO GEMINI (VISION API)
                remote_file = genai.upload_file(temp_pdf_path, mime_type="application/pdf")
                while remote_file.state.name == "PROCESSING":
                    time.sleep(1)
                    remote_file = genai.get_file(remote_file.name)

                # 3. LOAD LOGIC
                logic_path = os.path.join(LOGIC_DIR, system_file)
                logic_content = open(logic_path, 'r', encoding='utf-8').read() if os.path.exists(logic_path) else ""
                track_facts = json.dumps(selected_track_data) if selected_track_data else ""

                # 4. SEND TO AI
                model = genai.GenerativeModel(target_model, generation_config={"response_mime_type": "application/json"})
                
                prompt = f"""
                You are a Professional Handicapper ({region_code}).
                
                [TASK]
                Analyze the uploaded PDF. Extract structured data for EVERY RACE found.
                
                [STRICT OUTPUT SCHEMA]
                Return JSON with this structure:
                {{
                  "meta": {{ "track": "Track Name", "date": "YYYY-MM-DD", "track_condition": "Fast/Firm" }},
                  "races": [
                    {{
                      "number": 1,
                      "distance": "6 Furlongs",
                      "confidence_level": "High (or Low/Medium)",
                      "picks": {{
                        "top_pick": {{ "number": "1", "name": "Horse Name", "reason": "Reason" }},
                        "danger_horse": {{ "number": "2", "name": "Horse Name", "reason": "Reason (or 'None')" }},
                        "value_bet": {{ "number": "3", "name": "Horse Name", "odds": "10-1", "reason": "Reason (or 'None')" }}
                      }},
                      "exotic_strategy": {{ "exacta": "Box 1,2 or 1 Standout / 2,3,4", "trifecta": "..." }},
                      "contenders": [
                        {{ "number": "1", "name": "Horse Name", "rating": 95, "verdict": "Top Pick" }},
                        {{ "number": "2", "name": "Horse Name", "rating": 90, "verdict": "Danger" }}
                      ]
                    }}
                  ]
                }}
                
                [TRACK FACTS] {track_facts}
                [SYSTEM RULES] {logic_content}
                [UPDATES] {scratches}
                """
                
                response = model.generate_content([prompt, remote_file])
                st.session_state.raw_response = response.text 
                
                # 5. PARSE
                json_str = clean_json_string(response.text)
                data = json.loads(json_str)
                
                if isinstance(data, list): data = data[0] if data else {}
                if "meta" not in data: data["meta"] = {}
                if not data["meta"].get("track"): data["meta"]["track"] = selected_track_name
                if not data["meta"].get("date"): data["meta"]["date"] = datetime.today().strftime('%Y-%m-%d')
                if not data["meta"].get("track_condition"): data["meta"]["track_condition"] = "Standard"

                # 6. GENERATE PREVIEW (No Write to Disk)
                html_full = generate_meeting_html(data, region_code, is_preview_mode=False)
                html_preview = generate_meeting_html(data, region_code, is_preview_mode=True)
                
                safe_date = str(data['meta']['date']).replace('/', '-').replace(',', '').replace(' ', '_').replace(':', '')
                safe_track = str(data['meta']['track']).replace(' ', '_')
                filename = f"{safe_track}_{safe_date}.html"
                
                # 7. UPDATE STATE (But Don't Save Yet)
                st.session_state.html_content = html_full
                st.session_state.preview_html = html_preview
                st.session_state.report_filename = filename
                st.session_state.data_ready = True
                
            except Exception as e:
                st.error(f"Error: {e}")

# --- DISPLAY RESULTS & DEPLOY BUTTON ---
if st.session_state.data_ready:
    st.markdown("---")
    st.success("✅ Analysis Complete! Review below.")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        # DEPLOY BUTTON
        if st.button("💾 Save & Publish to Website", type="primary"):
            filepath = os.path.join(MEETINGS_DIR, st.session_state.report_filename)
            with open(filepath, "w", encoding='utf-8') as f:
                f.write(st.session_state.html_content)
            
            update_homepage()
            try:
                subprocess.Popen("deploy.bat", shell=True, cwd=BASE_DIR)
                st.success("Published & Deploying!")
            except:
                st.success("Saved locally (Deploy script not found).")
            
    with col2:
        st.download_button(
            label="⬇️ Download HTML",
            data=st.session_state.html_content,
            file_name=st.session_state.report_filename,
            mime="text/html"
        )
    
    st.markdown("### 📝 Live Report Preview")
    components.html(st.session_state.preview_html, height=800, scrolling=True)

# --- DEBUG EXPANDER ---
if st.session_state.raw_response:
    with st.expander("🔍 View Raw AI Response (Debug)"):
        st.text(st.session_state.raw_response)