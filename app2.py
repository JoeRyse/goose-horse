import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import os
import json
import time
import re
import subprocess
import base64
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Exacta AI", page_icon="🏇", layout="wide")

# PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEETINGS_DIR = os.path.join(DOCS_DIR, "meetings")
LOGS_DIR = os.path.join(BASE_DIR, "logs") 
LOGIC_DIR = os.path.join(BASE_DIR, "logic")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

for d in [DATA_DIR, DOCS_DIR, MEETINGS_DIR, LOGIC_DIR, TEMP_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

# --- DATABASE SETUP ---
DB_PATH = os.path.join(LOGS_DIR, "master_betting_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Table 1: Predictions
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, track TEXT, race_number TEXT, distance TEXT, surface TEXT, condition TEXT,
            p1_num TEXT, p1_barrier TEXT, p1_name TEXT, p1_reason TEXT,
            p2_num TEXT, p2_barrier TEXT, p2_name TEXT, p2_reason TEXT,
            p3_num TEXT, p3_barrier TEXT, p3_name TEXT, p3_reason TEXT,
            p4_num TEXT, p4_barrier TEXT, p4_name TEXT, p4_reason TEXT,
            danger_num TEXT, danger_barrier TEXT, danger_name TEXT, danger_reason TEXT,
            confidence TEXT, ai_model TEXT, temperature REAL, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Table 2: Actual Results
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, track TEXT, race_number TEXT,
            win_num TEXT, place_num TEXT, show_num TEXT,
            UNIQUE(date, track, race_number) ON CONFLICT REPLACE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def get_base64_logo():
    path = os.path.join(BASE_DIR, "logo.png")
    if not os.path.exists(path):
        path = os.path.join(DOCS_DIR, "logo.png")
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}", path
    return "", None

def clean_json_string(json_str):
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*$', '', json_str)
    return json_str.strip()

def is_valid_pick(pick):
    if not pick: return False
    if pick is None: return False
    name = str(pick.get('name', '')).strip().lower()
    invalid = ['none', 'n/a', 'null', 'no danger', 'no threat', 'tbd', 'horse name', '', 'no significant danger']
    return name and name not in invalid

def get_all_tracks_from_region(data):
    tracks = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and ("bias_notes" in v or "location" in v):
                tracks.append(k)
            elif isinstance(v, dict):
                tracks.extend(get_all_tracks_from_region(v))
    return sorted(list(set(tracks)))

def find_track_data(data, target_name):
    if isinstance(data, dict):
        if target_name in data:
            return data[target_name]
        for k, v in data.items():
            if isinstance(v, dict):
                result = find_track_data(v, target_name)
                if result: return result
    return None

def update_homepage():
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    grouped_files = {}
    for f in files:
        country = "International"
        try:
            with open(os.path.join(MEETINGS_DIR, f), 'r', encoding='utf-8') as file_obj:
                content = file_obj.read(500)
                if "META_COUNTRY" in content: 
                    match = re.search(r'META_COUNTRY:([^\s]+)', content)
                    if match: country = match.group(1).strip()
        except: pass
        if "Aus" in f: country = "Australia"
        elif "USA" in f: country = "USA"
        elif "UK" in f: country = "UK"

        if country not in grouped_files: grouped_files[country] = []
        grouped_files[country].append(f)

    logo_src, _ = get_base64_logo()
    logo_html = f'<img src="{logo_src}" class="logo">' if logo_src else '<span style="font-size:3rem; margin-right:20px;">🏇</span>'

    html = f"""<!DOCTYPE html><html lang="en"><head><title>Exacta AI</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>
    body {{ margin: 0; font-family: 'Segoe UI', sans-serif; background: #f8fafc; color: #333; }}
    .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
    .header {{ display: flex; align-items: center; border-bottom: 4px solid #003366; padding-bottom: 20px; margin-bottom: 20px; background: #fff; padding: 20px; }}
    .logo {{ max-height: 80px; margin-right: 20px; }}
    .header-info h1 {{ margin: 0; font-size: 2.5rem; color: #003366; text-transform: uppercase; font-weight: 800; }}
    .header-info .meta {{ color: #64748b; font-weight: 600; margin-top: 5px; font-size: 1.1rem; }}
    .section-title {{ border-bottom: 3px solid #ff6b00; padding-bottom: 10px; margin: 40px 0 20px 0; font-size: 1.5rem; color: #003366; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
    .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; text-decoration: none; color: #333; display: block; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform 0.2s; }}
    .card:hover {{ transform: translateY(-3px); border-color: #ff6b00; }}
    .card-body {{ padding: 20px; }}
    .track-name {{ font-size: 1.2rem; font-weight: 700; color: #0f172a; display: block; }}
    .status {{ color: #ff6b00; font-size: 0.8rem; font-weight: 700; margin-top: 10px; display: block; text-transform: uppercase; }}
    </style></head><body>
    <div class="header">{logo_html}<div class="header-info"><h1>Race Intelligence</h1><div class="meta">Professional Handicapping Database</div></div></div>
    <div class="container">"""
    
    for key in grouped_files.keys():
         html += f'<div class="section-title">{key} Racing</div><div class="grid">'
         for f in sorted(grouped_files[key], reverse=True):
             display_name = f.replace(".html","").replace("_"," ")
             html += f'<a href="meetings/{f}" class="card"><div class="card-body"><span class="track-name">{display_name}</span><span class="status">● View Form</span></div></a>'
         html += "</div>"
    html += "</div></body></html>"
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding='utf-8') as f: f.write(html)

CLEAN_CSS = """
    body { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #0f172a; margin: 0; background: #f8fafc; padding-top: 70px; }
    * { box-sizing: border-box; }
    .sidebar, .sidebar-title, .sidebar-links, .side-link, .mobile-nav, .back-home, .top-nav { display: none !important; }
    .main-content { margin: 0 auto; padding: 20px; max-width: 1000px; }
    .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 4px solid #003366; padding-bottom: 15px; margin-bottom: 15px; background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 0; }
    .header-branding { display: flex; align-items: center; flex: 1; } 
    .logo { max-height: 50px; margin-right: 15px; width: auto; }
    .header-info h1 { margin: 0; font-size: 1.8rem; color: #003366; text-transform: uppercase; font-weight: 800; line-height: 1.1; }
    .meta { color: #64748b; font-weight: 600; margin-top: 5px; font-size: 0.9rem; }
    .header-tools { display: flex; gap: 10px; align-items: center; }
    .print-btn { background: #fff; border: 1px solid #003366; color: #003366; padding: 8px 12px; cursor: pointer; font-weight: 700; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px; }
    .btn-home { background: #64748b; border: 1px solid #475569; color: #fff; padding: 8px 12px; cursor: pointer; font-weight: 700; border-radius: 4px; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; font-size: 14px; }
    .btn-home:hover { background: #475569; }
    .nav-bar { position: fixed; top: 0; left: 0; right: 0; background: #003366; padding: 10px 20px; z-index: 1000; display: flex; align-items: center; overflow-x: auto; white-space: nowrap; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    .nav-label { font-weight: 700; color: #fff; margin-right: 15px; font-size: 0.9rem; }
    .nav-btn { background: rgba(255,255,255,0.15); color: #fff; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: 600; font-size: 0.9rem; margin-right: 8px; transition: background 0.2s; border: 1px solid rgba(255,255,255,0.2); }
    .nav-btn:hover { background: #ff6b00; border-color: #ff6b00; }
    .race-section { margin-bottom: 25px; border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); scroll-margin-top: 80px; }
    .race-header { background: #fff; border-bottom: 2px solid #ff6b00; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; font-weight: 800; color: #003366; font-size: 1.1rem; }
    .picks-grid { display: flex; gap: 10px; padding: 15px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
    .pick-box { flex: 1; background: #fff; padding: 10px; border: 1px solid #e2e8f0; border-top: 4px solid #94a3b8; border-radius: 4px; }
    .panel-best { border-top-color: #fbbf24; background-color: #fffbeb; }
    .panel-top { border-top-color: #3b82f6; }
    .panel-danger { border-top-color: #d97706; }
    .table-container { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; margin-top: 0; min-width: 500px; }
    th { background: #f1f5f9; text-align: left; padding: 8px; font-size: 0.9rem; color: #475569; }
    td { padding: 8px; border-bottom: 1px solid #eee; font-size: 0.95rem; }
    .row-top { background: #f0f9ff; font-weight: 700; color: #003366; }
    .exacta-box { margin: 15px; padding: 10px; background: #f1f5f9; border-left: 4px solid #64748b; border-radius: 4px; font-size: 0.95rem; }
    .exacta-gold { background: #fffbeb; border-left-color: #fbbf24; }
    @media (max-width: 768px) {
        .main-content { padding: 10px; }
        .header { flex-direction: column; text-align: center; gap: 10px; padding: 15px; }
        .picks-grid { flex-direction: column; }
    }
    @media print { 
        .nav-bar, .print-btn, .btn-home { display: none !important; } 
        body { padding-top: 0; background: white; }
        .race-section { break-inside: avoid; border: 1px solid #ccc; box-shadow: none; }
    }
"""

def generate_meeting_html(data, region_override, is_preview_mode=False):
    country = data.get('meta', {}).get('jurisdiction', region_override)
    track_name = data.get('meta', {}).get('track', 'Unknown Track')
    track_date = data.get('meta', {}).get('date', 'Unknown Date')
    track_cond = data.get('meta', {}).get('track_condition', 'Standard')
    
    logo_src, _ = get_base64_logo()
    logo_html = f'<img src="{logo_src}" class="logo">' if logo_src else '<span style="font-size:2rem; margin-right:15px;">🏇</span>'

    best_bets = []
    for r in data.get('races', []):
        conf = str(r.get('confidence_level', ''))
        selections = r.get('selections', [])
        if not selections and 'picks' in r:
            p = r['picks']
            selections = [p.get('top_pick', {}), p.get('danger_horse', {}), p.get('value_bet', {})]
            selections = [s for s in selections if s and s.get('name')]

        if selections:
            top_pick = selections[0]
            if ("High" in conf or "5 Stars" in conf or "Best Bet" in conf) and is_valid_pick(top_pick):
                best_bets.append({
                    "race": r.get('number'),
                    "horse": f"#{top_pick.get('number')} {top_pick.get('name')}",
                    "reason": top_pick.get('reason', '')[:100] + "..."
                })
    
    best_bets_html = ""
    if best_bets:
        best_bets_html = '<div class="prime-bets" style="background:#fffbeb; border:2px solid #fbbf24; padding:15px; margin-bottom:20px; border-radius:8px;">'
        best_bets_html += '<h2 style="margin-top:0; color:#b45309; font-size:1.2rem; display:flex; align-items:center;">🔥 <span style="margin-left:8px">PRIME BETS</span></h2><div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px;">'
        for bb in best_bets[:3]:
            best_bets_html += f'<div><div style="font-weight:bold; font-size:1.1em;">R{bb["race"]}: {bb["horse"]}</div><div style="font-size:0.9em; color:#555;">{bb["reason"]}</div></div>'
        best_bets_html += '</div></div>'

    nav_links = ""
    for r in data.get('races', []):
        r_num = r.get('number', '0')
        nav_links += f'<a href="#race-{r_num}" class="nav-btn">Race {r_num}</a>'

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{track_name}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>{CLEAN_CSS}</style></head><body>
    <div class="nav-bar"><span class="nav-label">{track_name}</span>{nav_links}</div>
    <div class="main-content">
        <div class="header">
            <div class="header-branding">{logo_html}<div class="header-info"><h1>{track_name}</h1><div class="meta">{track_date} • {track_cond}</div></div></div>
            <div class="header-tools"><a href="../index.html" class="btn-home">🏠 Dashboard</a><button onclick="window.print()" class="print-btn">🖨️ PRINT</button></div>
        </div>
        {best_bets_html}"""

    for r in data.get('races', []):
        r_num = r.get('number', '?')
        confidence = str(r.get('confidence_level', ''))
        surface = str(r.get('surface', ''))
        if surface: surface = f" ({surface})"
        
        is_best_bet = "High" in confidence or "Strong" in confidence or "5 Stars" in confidence
        
        selections = r.get('selections', [])
        if not selections and 'picks' in r:
            p = r['picks']
            selections = [p.get('top_pick', {}), p.get('danger_horse', {}), p.get('value_bet', {})]
            selections = [s for s in selections if s and s.get('name')]

        top = selections[0] if len(selections) > 0 else {}
        top_name = top.get('name', 'N/A')
        top_class = "panel-best" if is_best_bet else "panel-top"
        top_label = "🔥 BEST BET" if is_best_bet else "🏁 TOP PICK"
        
        dang = r.get('danger_horse') or {}
        show_danger = is_valid_pick(dang)
        
        exotic_data = r.get('exotic_strategy', {})
        if isinstance(exotic_data, dict):
            exacta_strat = exotic_data.get('strategy', '')
            if not exacta_strat: exacta_strat = exotic_data.get('exacta', '')
        elif isinstance(exotic_data, str):
            exacta_strat = exotic_data
        else:
            exacta_strat = "No exotic strategy provided."
            
        exacta_class = "exacta-gold" if is_best_bet and len(exacta_strat) > 3 else "exacta-box"

        html += f"""<div id="race-{r_num}" class="race-section">
        <div class="race-header"><div>RACE {r_num} - {r.get('distance','')}{surface}</div><div style="font-size:0.9em; opacity:0.8">{confidence}</div></div>
        <div class="picks-grid">
            <div class="pick-box {top_class}"><b>{top_label}: #{top.get('number','')} {top_name}</b><br><small>{top.get('reason','')}</small></div>"""
            
        if show_danger:
            html += f"""<div class="pick-box panel-danger"><b>⚠️ DANGER: #{dang.get('number','')} {dang.get('name','')}</b><br><small>{dang.get('reason','')}</small></div>"""
            
        html += f"""</div><div class="table-container"><table><thead><tr><th>#</th><th>Horse</th><th>Reasoning / Notes</th></tr></thead><tbody>"""
        
        for s in selections[:4]:
            style = ' class="row-top"' if str(s.get('number')) == str(top.get('number')) else ''
            html += f"<tr{style}><td>{s.get('number')}</td><td>{s.get('name')}</td><td>{s.get('reason')}</td></tr>"
            
        if len(exacta_strat) > 3:
            html += f"""</tbody></table></div><div class="{exacta_class}"><b>BETTING STRATEGY:</b> {exacta_strat}</div></div>"""
        else:
            html += "</tbody></table></div></div>"
    
    html += "</div></div></body></html>"
    return html

update_homepage()

# --- SIDEBAR UI ---
st.sidebar.header("⚙️ Settings")

default_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
    elif "GOOGLE_API_KEY" in st.secrets:
        default_key = st.secrets["GOOGLE_API_KEY"]
except: pass

api_key = st.sidebar.text_input("Gemini API Key", value=default_key, type="password").strip()

if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GEMINI_API_KEY"] = api_key

st.sidebar.markdown("---")
st.sidebar.header("🚀 Admin")
if st.sidebar.button("🔄 Sync Nav & Deploy"):
    update_homepage()
    st.sidebar.success("Updated Dashboard Index.")
    try:
        subprocess.Popen("deploy.bat", shell=True, cwd=BASE_DIR)
        st.sidebar.success("Deploying...")
    except: st.sidebar.error("Deploy script missing.")

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI Model")
model_options = ["gemini-3.1-pro-preview", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
target_model = st.sidebar.selectbox("Select Model", model_options, index=0)
if st.sidebar.checkbox("Type a Custom Model Name?"):
    target_model = st.sidebar.text_input("Model Name", value="gemini-experimental")
creativity_temp = st.sidebar.slider("Creativity (Temperature)", 0.0, 1.0, 0.4, 0.1)

if api_key: genai.configure(api_key=api_key)

# --- TRACK DB LOADER ---
track_db = {}
try:
    with open(os.path.join(DATA_DIR, "track_db.json"), "r") as f: track_db = json.load(f)
except: pass

REGION_MAP = {
    "Australia": "Australia_Thoroughbred", "New Zealand": "New_Zealand_Thoroughbred",
    "USA (Thoroughbred)": "USA_Thoroughbred", "USA (Harness)": "USA_Harness",
    "Europe": "Europe_Thoroughbred", "Asia": "Asia_Thoroughbred",
    "Australia (Harness)": "Australia_Harness", "Canada (Harness)": "Canada_Harness",
    "Europe (Harness)": "Europe_Harness"
}
country_options = list(REGION_MAP.keys())
selected_country_label = st.sidebar.selectbox("Region/Type", country_options)
selected_country_key = REGION_MAP[selected_country_label]

selected_track_data = None
selected_track_name = "Unknown"

if track_db and selected_country_key in track_db:
    track_list = get_all_tracks_from_region(track_db[selected_country_key])
    track_list = ["Other (Manual Entry)"] + track_list
    selected_track_name = st.sidebar.selectbox("Track", track_list)
    
    if selected_track_name == "Other (Manual Entry)":
        selected_track_name = st.sidebar.text_input("Enter Track Name", value="Unknown Track")
        has_passing_lane = st.sidebar.checkbox("Has Passing Lane?", value=False)
        selected_track_data = {"bias_notes": f"Manual Entry. Passing Lane: {has_passing_lane}.", "passing_lane": has_passing_lane}
    else:
        selected_track_data = find_track_data(track_db[selected_country_key], selected_track_name)

if "Harness" in selected_country_key: 
    region_code = "Harness"
    system_file = "system_harness.md"
elif "USA" in selected_country_key: 
    region_code = "USA" 
    system_file = "system_usa.md"
elif "Australia" in selected_country_key: 
    region_code = "Australia" 
    system_file = "system_aus.md"
elif "Europe" in selected_country_key or "UK" in selected_country_key: 
    region_code = "Europe" 
    system_file = "system_uk.md"
else: 
    region_code = "International" 
    system_file = "system_aus.md"

if not os.path.exists(os.path.join(LOGIC_DIR, system_file)): 
    if "Harness" not in region_code: system_file = "system_usa.md"

# ==========================================
# APP ROUTING (TABS)
# ==========================================
tab_handicap, tab_analytics, tab_results = st.tabs(["🏇 Handicapping Engine", "📈 Performance Analytics", "📝 Input Results"])

# ==========================================
# TAB 1: HANDICAPPING ENGINE
# ==========================================
with tab_handicap:
    st.title(f"🏆 Exacta AI: {selected_track_name}")
    uploaded_file = st.file_uploader(f"Upload {region_code} PDF", type="pdf")
    scratches = st.text_area("📋 Scratchings / Updates", height=70)

    if 'html_content' not in st.session_state: st.session_state.html_content = None
    if 'preview_html' not in st.session_state: st.session_state.preview_html = None
    if 'report_filename' not in st.session_state: st.session_state.report_filename = None
    if 'raw_response' not in st.session_state: st.session_state.raw_response = ""
    if 'data_ready' not in st.session_state: st.session_state.data_ready = False
    if 'json_data' not in st.session_state: st.session_state.json_data = None

    if st.button("Analyze Race Card (Preview Only)", type="primary"):
        if not uploaded_file or not api_key:
            st.error("Please provide an API Key and a PDF file.")
        else:
            with st.spinner(f"Reading and Analyzing with {target_model} (Temp: {creativity_temp})..."):
                try:
                    temp_pdf_path = os.path.join(TEMP_DIR, "current_card.pdf")
                    with open(temp_pdf_path, "wb") as f: f.write(uploaded_file.getbuffer())

                    remote_file = genai.upload_file(temp_pdf_path, mime_type="application/pdf")
                    while remote_file.state.name == "PROCESSING":
                        time.sleep(1)
                        remote_file = genai.get_file(remote_file.name)

                    logic_path = os.path.join(LOGIC_DIR, system_file)
                    logic_content = open(logic_path, 'r', encoding='utf-8').read() if os.path.exists(logic_path) else ""
                    track_facts = json.dumps(selected_track_data) if selected_track_data else "No historical bias data."

                    system_instruction = f"""
                    You are a Professional Handicapper ({region_code}).
                    [SYSTEM RULES & LOGIC]
                    {logic_content}
                    [TRACK BIAS & FACTS]
                    {track_facts}
                    [STRICT OUTPUT SCHEMA]
                    Return ONLY a valid JSON object. No Markdown blocks.
                    {{
                      "meta": {{ "track": "Track Name", "date": "YYYY-MM-DD", "track_condition": "Fast/Firm" }},
                      "races": [
                        {{
                          "number": 1, "distance": "6 Furlongs", "surface": "Dirt", "confidence_level": "High (or Low/Medium)",
                          "selections": [
                            {{ "number": "1", "barrier": "4", "name": "Horse A", "rating": 105, "reason": "Reasoning..." }},
                            {{ "number": "2", "barrier": "2", "name": "Horse B", "rating": 100, "reason": "Reasoning..." }},
                            {{ "number": "3", "barrier": "9", "name": "Horse C", "rating": 95, "reason": "Reasoning..." }},
                            {{ "number": "4", "barrier": "5", "name": "Horse D", "rating": 92, "reason": "Reasoning..." }}
                          ],
                          "danger_horse": {{ "number": "5", "barrier": "1", "name": "Horse E", "rating": 98, "reason": "Why it is a threat" }},
                          "exotic_strategy": {{ "strategy": "Win Bet #1, Exacta Box 1-2, Trifecta 1 / 2,3 / ALL" }}
                        }}
                      ]
                    }}
                    """

                    user_prompt = f"""
                    [TASK] Analyze the attached PDF. Extract data and apply logic.
                    [UPDATES/SCRATCHES] {scratches}
                    [CRITICAL INSTRUCTIONS]
                    1. Provide exactly 4 selections per race.
                    2. EXTRACT SURFACE for each race (Dirt, Turf, Synthetic).
                    3. EXTRACT BARRIER/POST for every selection.
                    4. DANGER HORSE: Set to null if no legitimate threat exists.
                    """
                    
                    model = genai.GenerativeModel(target_model, system_instruction=system_instruction, generation_config={"response_mime_type": "application/json", "temperature": creativity_temp})
                    response = model.generate_content([user_prompt, remote_file])
                    st.session_state.raw_response = response.text 
                    
                    json_str = clean_json_string(response.text)
                    data = json.loads(json_str)
                    st.session_state.json_data = data
                    
                    if isinstance(data, list): data = data[0] if data else {}
                    if "meta" not in data: data["meta"] = {}
                    if selected_track_name != "Unknown" and "Manual" not in selected_track_name: 
                        data["meta"]["track"] = selected_track_name
                    
                    if not data["meta"].get("date"): data["meta"]["date"] = datetime.today().strftime('%Y-%m-%d')
                    if not data["meta"].get("track_condition"): data["meta"]["track_condition"] = "Standard"
                    
                    if data.get('races') and str(data['races'][0].get('number')) == "0":
                        st.warning("⚠️ Warning: AI returned 'Race 0'. It may have failed to read the PDF text.")

                    html_full = generate_meeting_html(data, region_code, is_preview_mode=False)
                    html_preview = generate_meeting_html(data, region_code, is_preview_mode=True)
                    
                    safe_date = str(data['meta']['date']).replace('/', '-').replace(',', '').replace(' ', '_').replace(':', '')
                    safe_track = str(data['meta']['track']).replace(' ', '_')
                    filename = f"{safe_track}_{safe_date}.html"
                    
                    st.session_state.html_content = html_full
                    st.session_state.preview_html = html_preview
                    st.session_state.report_filename = filename
                    st.session_state.data_ready = True
                    
                except Exception as e: st.error(f"Error: {e}")

    if st.session_state.data_ready:
        st.markdown("---")
        st.success("✅ Analysis Complete! Review below.")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            update_idx = st.checkbox("Auto-Update Index.html", value=True)
            if st.button("💾 Save & Publish", type="primary"):
                filepath = os.path.join(MEETINGS_DIR, st.session_state.report_filename)
                with open(filepath, "w", encoding='utf-8') as f:
                    f.write(st.session_state.html_content)
                
                if st.session_state.json_data:
                    log_filename = st.session_state.report_filename.replace(".html", ".json")
                    with open(os.path.join(LOGS_DIR, log_filename), "w", encoding='utf-8') as f:
                        json.dump(st.session_state.json_data, f, indent=4)
                    
                    try:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        meta = st.session_state.json_data.get("meta", {})
                        for race in st.session_state.json_data.get("races", []):
                            selections = race.get('selections', [])
                            if not selections and 'picks' in race:
                                p = race['picks']
                                selections = [p.get('top_pick', {}), p.get('danger_horse', {}), p.get('value_bet', {})]
                                selections = [s for s in selections if s and s.get('name')]
                            
                            while len(selections) < 4: selections.append({})
                            dang = race.get('danger_horse') or {}
                            
                            c.execute('''
                                INSERT INTO predictions (
                                    date, track, race_number, distance, surface, condition,
                                    p1_num, p1_barrier, p1_name, p1_reason, p2_num, p2_barrier, p2_name, p2_reason,
                                    p3_num, p3_barrier, p3_name, p3_reason, p4_num, p4_barrier, p4_name, p4_reason,
                                    danger_num, danger_barrier, danger_name, danger_reason, confidence, ai_model, temperature
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                meta.get('date'), meta.get('track'), str(race.get('number')), race.get('distance', ''), race.get('surface', ''), meta.get('track_condition', ''),
                                selections[0].get('number', 'N/A'), selections[0].get('barrier', ''), selections[0].get('name', 'N/A'), selections[0].get('reason', 'N/A'),
                                selections[1].get('number', ''), selections[1].get('barrier', ''), selections[1].get('name', ''), selections[1].get('reason', ''),
                                selections[2].get('number', ''), selections[2].get('barrier', ''), selections[2].get('name', ''), selections[2].get('reason', ''),
                                selections[3].get('number', ''), selections[3].get('barrier', ''), selections[3].get('name', ''), selections[3].get('reason', ''),
                                dang.get('number', ''), dang.get('barrier', ''), dang.get('name', ''), dang.get('reason', ''),
                                race.get('confidence_level', ''), target_model, creativity_temp
                            ))
                        conn.commit()
                        conn.close()
                    except Exception as e: st.error(f"Failed to log to SQLite Database: {e}")
                
                if update_idx: update_homepage()
                try: subprocess.Popen("deploy.bat", shell=True, cwd=BASE_DIR)
                except: pass
                
        with col2: st.download_button("⬇️ Download HTML", st.session_state.html_content, st.session_state.report_filename, "text/html")
        components.html(st.session_state.preview_html, height=800, scrolling=True)


# ==========================================
# TAB 2: ANALYTICS DASHBOARD
# ==========================================
with tab_analytics:
    st.title("📈 Model Performance & Backtesting")
    
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        preds_df = pd.read_sql_query("SELECT * FROM predictions", conn) 
        results_df = pd.read_sql_query("SELECT * FROM results", conn)
        conn.close()
        
        if not results_df.empty and not preds_df.empty:
            preds_df['race_number'] = preds_df['race_number'].astype(str)
            results_df['race_number'] = results_df['race_number'].astype(str)
            
            # Drop duplicate predictions (keeps your most recently saved run)
            preds_df = preds_df.sort_values('id').drop_duplicates(subset=['date', 'track', 'race_number'], keep='last')
            
            merged_df = pd.merge(preds_df, results_df, on=['date', 'track', 'race_number'], how='inner')
            
            if not merged_df.empty:
                # --- CORE CALCULATIONS ---
                merged_df['top_pick_win'] = merged_df.apply(lambda x: str(x['p1_num']) in str(x['win_num']), axis=1)
                
                # Danger Horse Win Calculation (Ignoring blanks/nulls)
                merged_df['danger_win'] = merged_df.apply(
                    lambda x: (str(x['danger_num']) in str(x['win_num'])) and 
                              (str(x['danger_num']).strip() not in ['', 'nan', 'None']), axis=1)
                              
                merged_df['top_pick_board'] = merged_df.apply(
                    lambda x: str(x['p1_num']) in str(x['win_num']) or 
                              str(x['p1_num']) in str(x['place_num']) or 
                              str(x['p1_num']) in str(x['show_num']), axis=1)
                
                merged_df['exacta_hit'] = merged_df.apply(
                    lambda x: (str(x['win_num']) in [str(x['p1_num']), str(x['p2_num'])]) and 
                              (str(x['place_num']) in [str(x['p1_num']), str(x['p2_num'])]), axis=1)
                
                merged_df['exacta_top3_hit'] = merged_df.apply(
                    lambda x: (str(x['win_num']) in [str(x['p1_num']), str(x['p2_num']), str(x['p3_num'])]) and 
                              (str(x['place_num']) in [str(x['p1_num']), str(x['p2_num']), str(x['p3_num'])]), axis=1)

                merged_df['trifecta_top3_hit'] = merged_df.apply(
                    lambda x: (str(x['win_num']) in [str(x['p1_num']), str(x['p2_num']), str(x['p3_num'])]) and 
                              (str(x['place_num']) in [str(x['p1_num']), str(x['p2_num']), str(x['p3_num'])]) and
                              (str(x['show_num']) in [str(x['p1_num']), str(x['p2_num']), str(x['p3_num'])]), axis=1)

                # --- GLOBAL FILTER ---
                st.markdown("---")
                all_tracks = sorted(merged_df['track'].unique().tolist())
                col_f1, col_f2 = st.columns([3, 1])
                with col_f1:
                    selected_tracks = st.multiselect("🌍 Filter by Track (Leave blank to view all)", all_tracks, default=[])
                
                if selected_tracks:
                    display_df = merged_df[merged_df['track'].isin(selected_tracks)]
                    st.write(f"*Graded {len(display_df)} completed races from selected tracks.*")
                else:
                    display_df = merged_df
                    st.write(f"*Graded {len(display_df)} completed races across all tracks.*")

                # --- DISPLAY DASHBOARD ---
                st.header("📊 Grading Report")
                
                st.subheader("⚔️ The Danger Test")
                m1, m2, m3 = st.columns(3)
                m1.metric("Top Pick Win %", f"{(display_df['top_pick_win'].mean() * 100):.1f}%")
                m2.metric("Danger Horse Win %", f"{(display_df['danger_win'].mean() * 100):.1f}%")
                m3.metric("Top Pick In The Money %", f"{(display_df['top_pick_board'].mean() * 100):.1f}%")
                
                st.markdown("---")
                st.subheader("🎟️ Exotics Performance")
                e1, e2, e3 = st.columns(3)
                e1.metric("Top 2 Exacta Box", f"{(display_df['exacta_hit'].mean() * 100):.1f}%")
                e2.metric("Top 3 Exacta Box", f"{(display_df['exacta_top3_hit'].mean() * 100):.1f}%")
                e3.metric("Top 3 Trifecta Box", f"{(display_df['trifecta_top3_hit'].mean() * 100):.1f}%")
                
                st.markdown("---")
                col_a, col_b = st.columns(2)
                
                # --- DRILL DOWNS WITH DANGER HORSE ---
                with col_a:
                    st.subheader("By Surface")
                    surface_stats = display_df.groupby('surface').agg(
                        Top_Pick_Win=('top_pick_win', 'mean'),
                        Danger_Win=('danger_win', 'mean'),
                        Races=('top_pick_win', 'count')
                    ).reset_index()
                    surface_stats.rename(columns={'Top_Pick_Win': 'Top Pick Win', 'Danger_Win': 'Danger Win'}, inplace=True)
                    surface_stats['Top Pick Win'] = (surface_stats['Top Pick Win'] * 100).round(1).astype(str) + '%'
                    surface_stats['Danger Win'] = (surface_stats['Danger Win'] * 100).round(1).astype(str) + '%'
                    st.dataframe(surface_stats, use_container_width=True, hide_index=True)
                    
                with col_b:
                    st.subheader("By Confidence Level")
                    conf_stats = display_df.groupby('confidence').agg(
                        Top_Pick_Win=('top_pick_win', 'mean'),
                        Danger_Win=('danger_win', 'mean'),
                        Races=('top_pick_win', 'count')
                    ).reset_index()
                    conf_stats.rename(columns={'Top_Pick_Win': 'Top Pick Win', 'Danger_Win': 'Danger Win'}, inplace=True)
                    conf_stats['Top Pick Win'] = (conf_stats['Top Pick Win'] * 100).round(1).astype(str) + '%'
                    conf_stats['Danger Win'] = (conf_stats['Danger Win'] * 100).round(1).astype(str) + '%'
                    st.dataframe(conf_stats, use_container_width=True, hide_index=True)
            else:
                st.info("No matching results found. Use the 'Input Results' tab to add official results.")
        else:
            st.info("No prediction history or results found in the database yet.")
# ==========================================
# TAB 3: INPUT RESULTS (THE DATA EDITOR)
# ==========================================
with tab_results:
    st.title("📝 Input Official Results")
    st.markdown("Select a meeting to log official results. The app automatically detects which meetings are missing data.")
    
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        
        # --- THE MAGIC TOGGLE ---
        view_mode = st.radio("Filter Meetings:", ["🔴 Needs Results (Pending)", "🟢 Edit Completed Results"], horizontal=True)
        
        if "Pending" in view_mode:
            # SQL: Find predictions that DO NOT have a matching, filled-out result
            query = """
                SELECT DISTINCT p.date, p.track 
                FROM predictions p
                LEFT JOIN results r ON p.date = r.date AND p.track = r.track AND p.race_number = r.race_number
                WHERE r.win_num IS NULL OR r.win_num = ''
                ORDER BY p.date DESC
            """
        else:
            # SQL: Find tracks that DO have results
            query = "SELECT DISTINCT date, track FROM results ORDER BY date DESC"
            
        history_df = pd.read_sql_query(query, conn)
        
        if not history_df.empty:
            col_d, col_t = st.columns(2)
            with col_d:
                res_date = st.selectbox("Select Date", history_df['date'].unique())
            with col_t:
                valid_tracks = history_df[history_df['date'] == res_date]['track'].unique()
                res_track = st.selectbox("Select Track", valid_tracks)
            
            # Fetch the races
            races_df = pd.read_sql_query(
                "SELECT DISTINCT race_number FROM predictions WHERE date=? AND track=? ORDER BY CAST(race_number AS INTEGER)", 
                conn, params=(res_date, res_track)
            )
            
            # Fetch existing results (if any)
            existing_results_df = pd.read_sql_query(
                "SELECT race_number, win_num, place_num, show_num FROM results WHERE date=? AND track=?", 
                conn, params=(res_date, res_track)
            )
            conn.close()

            # Merge to create grid
            editor_df = pd.merge(races_df, existing_results_df, on="race_number", how="left")
            editor_df.fillna("", inplace=True)
            editor_df.rename(columns={"race_number": "Race Number", "win_num": "Win", "place_num": "Place", "show_num": "Show"}, inplace=True)
            
            st.markdown("---")
            st.subheader(f"Results for {res_track} ({res_date})")
            
            edited_df = st.data_editor(
                editor_df,
                use_container_width=True,
                num_rows="dynamic",
                hide_index=True,
                disabled=["Race Number"]
            )
            
            if st.button("💾 Save Results to Database", type="primary"):
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    
                    for index, row in edited_df.iterrows():
                        win = str(row['Win']).strip()
                        place = str(row['Place']).strip()
                        show = str(row['Show']).strip()
                        
                        if win: 
                            c.execute('''
                                INSERT INTO results (date, track, race_number, win_num, place_num, show_num)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (res_date, res_track, str(row['Race Number']), win, place, show))
                            
                    conn.commit()
                    conn.close()
                    st.success("✅ Results Saved! Check the Analytics tab for updated stats.")
                    st.rerun() # Instantly refreshes the UI so the completed track vanishes from the Pending list
                except Exception as e:
                    st.error(f"Database error: {e}")
        else:
            if "Pending" in view_mode:
                st.success("🎉 You are all caught up! There are no pending meetings awaiting results.")
            else:
                st.info("No completed results found. Go to the 'Pending' tab to add some!")
            conn.close()