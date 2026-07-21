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

# ==========================================
# FILE-BASED TRACK CATALOG LOADER
# ==========================================
TRACKS_DIR = os.path.join(BASE_DIR, "tracks")

def load_track_catalog():
    """
    Scans individual files and groups them into:
    Catalog[Category][Region] = [Tracks]
    """
    catalog = {}
    if not os.path.exists(TRACKS_DIR):
        return catalog
        
    for filename in os.listdir(TRACKS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(TRACKS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_group = str(data.get("region_group", "")).upper()
                    
                    # 1. Determine Category (Thoroughbred vs Harness)
                    if "HARNESS" in raw_group:
                        category = "Harness"
                    else:
                        category = "Thoroughbred"
                        
                    # 2. Determine Region (CHECK AUSTRALIA FIRST)
                    if "AUSTRALIA" in raw_group or "AUS" in raw_group:
                        region = "Australia"
                    elif "NEW_ZEALAND" in raw_group or "NZ" in raw_group:
                        region = "New Zealand"
                    elif "ASIA" in raw_group or "HONG_KONG" in raw_group or "JAPAN" in raw_group or "KOREA" in raw_group:
                        region = "Asia"
                    elif "CANADA" in raw_group:
                        region = "Canada"
                    elif "EUROPE" in raw_group or "UK" in raw_group or "FRANCE" in raw_group:
                        region = "Europe"
                    elif "USA" in raw_group or "US" in raw_group:
                        region = "USA"
                    else:
                        region = "Other"
                        
                    track_display_name = filename.replace(".json", "").replace("_", " ").title()
                    
                    # Build the nested structure
                    if category not in catalog:
                        catalog[category] = {}
                    if region not in catalog[category]:
                        catalog[category][region] = []
                        
                    catalog[category][region].append(track_display_name)
            except:
                continue
                
    # Sort tracks alphabetically inside their regions
    for cat in catalog:
        for reg in catalog[cat]:
            catalog[cat][reg] = sorted(catalog[cat][reg])
            
    return catalog

def find_track_data(target_name):
    """
    Loads an individual track's configuration dictionary directly 
    from its dedicated file in the tracks/ folder.
    """
    filename = f"{target_name.lower().replace(' ', '_').replace('-', '_')}.json"
    filepath = os.path.join(TRACKS_DIR, filename)
    
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# ==========================================
# OPTIMIZED WEIGHTS LOADER (FOR APP SCORING)
# ==========================================
OPTIMIZED_WEIGHTS_PATH = os.path.join(DATA_DIR, "optimized_weights.json")

def get_weights_for_track(track_name):
    """
    Pulls track-specific weights generated by run_optimizer.py.
    Falls back to safe defaults if the track hasn't been optimized yet.
    """
    default_weights = {
        "lone_speed_bonus": 4,
        "trouble_trip_bonus": 4,
        "sprint_route_bonus": -2
    }
    
    if os.path.exists(OPTIMIZED_WEIGHTS_PATH):
        try:
            with open(OPTIMIZED_WEIGHTS_PATH, "r", encoding="utf-8") as f:
                all_weights = json.load(f)
                for stored_track, data in all_weights.items():
                    if stored_track.lower() == track_name.lower():
                        return data.get("weights", default_weights)
        except:
            pass
            
    return default_weights

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
model_options = ["gemini-3.5-flash","gemini-3.1-pro-preview", "gemini-2.0-flash-exp", "gemini-1.5-flash"]
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


# ==========================================
# 3-TIER SIDEBAR SELECTION MENU
# ==========================================
track_catalog = load_track_catalog()

if track_catalog:
    st.sidebar.markdown("### 🏟️ Meeting Selection")
    
    # Tier 1: Select Category (Thoroughbred vs Harness)
    categories = sorted(list(track_catalog.keys()))
    selected_category = st.sidebar.selectbox("Category", categories, key="app_cat_select")
    
    # Tier 2: Select Region/Continent (US, Australia, Asia, etc. under that category)
    regions_in_cat = sorted(list(track_catalog[selected_category].keys()))
    selected_region = st.sidebar.selectbox("Region", regions_in_cat, key="app_reg_select")
    
    # Tier 3: Select Track
    tracks_in_region = track_catalog[selected_category][selected_region]
    selected_track = st.sidebar.selectbox("Track", tracks_in_region, key="app_track_select")
    
    # Load profile data and optimized weights for the selected track
    current_track_profile = find_track_data(selected_track)
    active_weights = get_weights_for_track(selected_track)
    
    st.sidebar.success(f"Loaded: {selected_track}")
else:
    st.sidebar.warning("No track files found in the 'tracks/' folder.")
    selected_track = "Saratoga"
    current_track_profile = {}
    active_weights = get_weights_for_track(selected_track)
    
# ==========================================
# APP ROUTING (TABS)
# ==========================================
tab_handicap, tab_analytics, tab_results = st.tabs(["🏇 Handicapping Engine", "📈 Performance Analytics", "📝 Input Results"])

# ==========================================
# TAB 1: HANDICAPPING ENGINE
# ==========================================
with tab_handicap:
    st.title(f"🏆 Exacta AI: {selected_track}")
    uploaded_file = st.file_uploader(f"Upload {selected_region} PDF", type="pdf")
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

                    # Define your logic directory and the prompt filename explicitly
                    LOGIC_DIR = "prompts" # Or whatever folder holds your text files
                    system_file = "handicapper_instructions.txt" # Change this to your actual prompt filename if different

                    logic_path = os.path.join(LOGIC_DIR, system_file)
                    logic_content = open(logic_path, 'r', encoding='utf-8').read() if os.path.exists(logic_path) else "You are an expert handicapper."
                    track_facts = json.dumps(current_track_profile) if current_track_profile else "No historical bias data."

                    system_instruction = f"""
                    You are a Data Extraction Engine for racing ({selected_region}).
                    [SYSTEM RULES & LOGIC]
                    {logic_content}
                    [TRACK BIAS & FACTS]
                    {track_facts}
                    [STRICT OUTPUT SCHEMA]
                    Return ONLY a valid JSON array. No Markdown blocks.
                    [
                      {{
                        "race_number": 1,
                        "distance_surface": "1200m Soft5",
                        "confidence_level": "High", 
                        "contenders": [
                          {{
                            "program_number": "1",
                            "barrier": "4",
                            "horse_name": "Horse Name",
                            "handicapper_notes": "Professional note here.",
                            "features": {{
                                "ai_holistic_score": 95,
                                "running_style": "Leader",
                                "is_lone_speed": true,
                                "distance_transition": "None",
                                "trouble_trip": "None",
                                "is_danger_horse": false
                            }}
                          }}
                        ]
                      }}
                    ]
                    """

                    user_prompt = f"""
                    [TASK] Analyze the attached PDF. Extract features for EVERY active horse.
                    [UPDATES/SCRATCHES] {scratches}
                    [CRITICAL INSTRUCTIONS]
                    1. YOU MUST PROCESS EVERY SINGLE RACE ON THE CARD. Do not stop early! If there are 10 races, output 10 races.
                    2. Evaluate EVERY active horse in each race.
                    3. Assign a "confidence_level" ("High", "Medium", or "Low") to each race based on how competitive or chaotic the field is.
                    """
                    
                    model = genai.GenerativeModel(target_model, system_instruction=system_instruction, generation_config={"response_mime_type": "application/json", "temperature": creativity_temp})
                    response = model.generate_content([user_prompt, remote_file])
                    st.session_state.raw_response = response.text 
                    
                    json_str = clean_json_string(response.text)
                    raw_extracted_data = json.loads(json_str)
                    
                    # 1. LOAD OPTIMIZED WEIGHTS (Defaults to Saratoga baseline)
                    track_weights = {"lone_speed_bonus": 3, "trouble_trip_bonus": 2, "sprint_route_bonus": -2}
                    try:
                        with open(os.path.join(DATA_DIR, "optimized_weights.json"), "r") as f:
                            all_weights = json.load(f)
                            if selected_track in all_weights:
                                track_weights = all_weights[selected_track]
                    except: pass

                    # 2. THE BULLETPROOF LOCAL MATH ENGINE
                    def calculate_local_rating(features):
                        # Safely grab base speed as a float
                        try:
                            score = float(features.get('ai_holistic_score', 80))
                        except:
                            score = 80.0
                        
                        # Handle AI sometimes sending strings instead of booleans
                        is_lone = str(features.get('is_lone_speed', '')).strip().lower()
                        if is_lone == 'true':
                            score += float(track_weights.get('lone_speed_bonus', 3))
                            
                        dist_trans = str(features.get('distance_transition', '')).strip()
                        if dist_trans == "Stretch-Out":
                            score += float(track_weights.get('sprint_route_bonus', -2))
                            
                        trip = str(features.get('trouble_trip', '')).strip()
                        if trip == "Grade A":
                            score += float(track_weights.get('trouble_trip_bonus', 2))
                        elif trip == "Grade B":
                            score += float(track_weights.get('trouble_trip_bonus', 1))
                            
                        return round(score, 1)

                    # 3. THE DATA BRIDGE
                    data = {
                        "meta": {
                            "track": selected_track if selected_track != "Unknown" else "Track",
                            "date": datetime.today().strftime('%Y-%m-%d'),
                            "track_condition": "Standard"
                        },
                        "races": []
                    }
                    
                    races_list = raw_extracted_data if isinstance(raw_extracted_data, list) else raw_extracted_data.get('races', [])
                    
                    for race in races_list:
                        new_race = {
                            "number": race.get("race_number", 0),
                            "distance": race.get("distance_surface", ""),
                            "surface": race.get("distance_surface", "").split(" ")[-1] if " " in race.get("distance_surface", "") else "",
                            "confidence_level": race.get("confidence_level", "Medium"),
                            "raw_features_dump": race,
                            "selections": []
                        }
                        
                        scored_contenders = []
                        for horse in race.get("contenders", []):
                            feats = horse.get("features", {})
                            rating = calculate_local_rating(feats)
                            ai_notes = horse.get("handicapper_notes", "No notes provided.")
                            
                            # This is the critical fix to stop mixing up numbers and gates
                            prog_num = str(horse.get("program_number", horse.get("number", "")))
                            barrier_num = str(horse.get("barrier", ""))
                            
                            reason = f"{ai_notes}"
                            tags = []
                            if str(feats.get('is_lone_speed')).lower() == 'true': tags.append("🔥 Lone Speed")
                            if feats.get('trouble_trip') and feats.get('trouble_trip') != "None": tags.append(f"⚠️ {feats.get('trouble_trip')}")
                            if feats.get('distance_transition') and feats.get('distance_transition') != "None": tags.append(f"📏 {feats.get('distance_transition')}")
                            if tags:
                                reason += f" | <i>{' • '.join(tags)}</i>"
                            
                            scored_contenders.append({
                                "number": prog_num,         # Maps to the program number column
                                "barrier": barrier_num,     # Maps to the barrier (PP) column
                                "name": horse.get("horse_name", "Unknown"),
                                "rating": rating,
                                "reason": reason
                            })
                        
                        # 1. Sort everyone by their score first
                        scored_contenders.sort(key=lambda x: x["rating"], reverse=True)
                        
                        # 2. Hunt for the AI's explicitly designated Danger Horse
                        danger_horse = {}
                        danger_index_to_remove = -1
                        
                        for horse in race.get("contenders", []):
                            if str(horse.get("features", {}).get("is_danger_horse", "")).strip().lower() == 'true':
                                target_name = horse.get("horse_name", "Unknown")
                                for idx, sc in enumerate(scored_contenders):
                                    if sc["name"] == target_name:
                                        danger_index_to_remove = idx
                                        break
                                break
                                
                        # 3. Pull the true Danger Horse out of the sorting queue
                        if danger_index_to_remove != -1:
                            danger_horse = scored_contenders.pop(danger_index_to_remove)
                        elif len(scored_contenders) >= 5:
                            danger_horse = scored_contenders.pop(4)
                        else:
                            danger_horse = scored_contenders.pop() if scored_contenders else {}

                        # 4. Top 4 remaining become your main selections, and the AI's pick becomes Danger
                        new_race["selections"] = scored_contenders[:4]
                        new_race["danger_horse"] = danger_horse
                        
                        data["races"].append(new_race)
                    st.session_state.json_data = data

                    html_full = generate_meeting_html(data, selected_region, is_preview_mode=False)
                    html_preview = generate_meeting_html(data, selected_region, is_preview_mode=True)
                    
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
                                    danger_num, danger_barrier, danger_name, danger_reason, confidence, ai_model, temperature, raw_features
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                meta.get('date'), meta.get('track'), str(race.get('number')), race.get('distance', ''), race.get('surface', ''), meta.get('track_condition', ''),
                                selections[0].get('number', 'N/A'), selections[0].get('barrier', ''), selections[0].get('name', 'N/A'), selections[0].get('reason', 'N/A'),
                                selections[1].get('number', ''), selections[1].get('barrier', ''), selections[1].get('name', ''), selections[1].get('reason', ''),
                                selections[2].get('number', ''), selections[2].get('barrier', ''), selections[2].get('name', ''), selections[2].get('reason', ''),
                                selections[3].get('number', ''), selections[3].get('barrier', ''), selections[3].get('name', ''), selections[3].get('reason', ''),
                                dang.get('number', ''), dang.get('barrier', ''), dang.get('name', ''), dang.get('reason', ''),
                                race.get('confidence_level', ''), target_model, creativity_temp, json.dumps(race.get('raw_features_dump', {}))
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
    
    # --- CARD DELETION UTILITY (MEETING CLEANER) ---
    with st.expander("🗑️ Delete / Remove a Race Card (Meeting Cleaner)", expanded=False):
        st.markdown("If a meeting was canceled or imported with the wrong date, select the track and date below to completely wipe it from the database and saved files.")
        
        try:
            conn_del = sqlite3.connect(DB_PATH)
            del_history_df = pd.read_sql_query("SELECT DISTINCT date, track FROM predictions ORDER BY date DESC", conn_del)
            conn_del.close()
        except:
            del_history_df = pd.DataFrame(columns=['date', 'track'])
            
        if not del_history_df.empty:
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                all_del_tracks = sorted(del_history_df['track'].unique())
                del_track = st.selectbox("Track to Delete", all_del_tracks, key="cleaner_track_select")
            with col_del2:
                valid_del_dates = del_history_df[del_history_df['track'] == del_track]['date'].unique()
                del_date = st.selectbox("Date to Delete", sorted(valid_del_dates, reverse=True), key="cleaner_date_select")
            
            confirm_delete = st.checkbox("I understand this will permanently delete predictions and results for this card.", key="cleaner_confirm_box")
            
            if st.button("❌ Permanently Delete Selected Card", type="secondary"):
                if confirm_delete:
                    try:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("DELETE FROM predictions WHERE track=? AND date=?", (del_track, del_date))
                        c.execute("DELETE FROM results WHERE track=? AND date=?", (del_track, del_date))
                        conn.commit()
                        conn.close()
                        
                        json_filename = f"{del_track}_{del_date}.json"
                        json_filepath = os.path.join(MEETINGS_DIR, json_filename)
                        if os.path.exists(json_filepath):
                            os.remove(json_filepath)
                            
                        # Reset tracking states so it safely hops to the next available track
                        if "saved_track_name" in st.session_state:
                            del st.session_state["saved_track_name"]
                            
                        st.success(f"Successfully deleted card for {del_track} on {del_date}.")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting card: {e}")
                else:
                    st.warning("Please check the confirmation box above to enable deletion.")
        else:
            st.info("No saved race cards found in the database to delete.")

    st.markdown("---")
    st.markdown("Select a track first, then pick a date to log official results. The app automatically detects missing data.")
    
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        
        # --- THE MAGIC TOGGLE ---
        view_mode = st.radio("Filter Meetings:", ["🔴 Needs Results (Pending)", "🟢 Edit Completed Results"], horizontal=True, key="res_view_mode_toggle")
        
        if "Pending" in view_mode:
            query = """
                SELECT DISTINCT p.date, p.track 
                FROM predictions p
                LEFT JOIN results r ON p.date = r.date AND p.track = r.track AND p.race_number = r.race_number
                WHERE r.win_num IS NULL OR r.win_num = ''
                ORDER BY p.date DESC
            """
        else:
            query = "SELECT DISTINCT date, track FROM results ORDER BY date DESC"
            
        history_df = pd.read_sql_query(query, conn)
        
        if not history_df.empty:
            available_tracks = sorted(history_df['track'].unique())
            
            # --- ROBUST STATE RETENTION ---
            if "saved_track_name" not in st.session_state or st.session_state["saved_track_name"] not in available_tracks:
                st.session_state["saved_track_name"] = available_tracks[0]
                
            current_track_index = available_tracks.index(st.session_state["saved_track_name"])
            
            col_t, col_d = st.columns(2)
            
            with col_t:
                res_track = st.selectbox(
                    "Select Track", 
                    available_tracks, 
                    index=current_track_index, 
                    key="results_unique_track_select"
                )
                # Immediately capture selection changes
                if res_track != st.session_state["saved_track_name"]:
                    st.session_state["saved_track_name"] = res_track
                    st.rerun()
                
            with col_d:
                valid_dates = sorted(history_df[history_df['track'] == res_track]['date'].unique(), reverse=True)
                
                if not valid_dates:
                    st.warning(f"No remaining dates found for {res_track}.")
                    conn.close()
                    st.stop()
                
                if "saved_date_val" not in st.session_state or st.session_state["saved_date_val"] not in valid_dates:
                    st.session_state["saved_date_val"] = valid_dates[0]
                    
                current_date_index = valid_dates.index(st.session_state["saved_date_val"]) if st.session_state["saved_date_val"] in valid_dates else 0
                
                res_date = st.selectbox(
                    "Select Date", 
                    valid_dates, 
                    index=current_date_index, 
                    key="results_unique_date_select"
                )
                if res_date != st.session_state["saved_date_val"]:
                    st.session_state["saved_date_val"] = res_date
                    st.rerun()
            
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
                disabled=["Race Number"],
                key="results_data_editor_grid"
            )
            
            if st.button("💾 Save Results to Database", type="primary", key="save_results_db_btn"):
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
                    st.success("✅ Results Saved!")
                    time.sleep(0.3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {e}")
        else:
            if "Pending" in view_mode:
                st.success("🎉 You are all caught up! There are no pending meetings awaiting results.")
            else:
                st.info("No completed results found. Go to the 'Pending' tab to add some!")
            conn.close()

            # ==========================================
# ==========================================
# SIDEBAR: ONE-CLICK OPTIMIZER TRIGGER
# ==========================================
with st.sidebar:
    st.markdown("---")
    st.subheader("⚡ Automated Tools")
    
    if st.button("🚀 Run Race Optimizer"):
        with st.spinner("Running optimizer script... Please wait."):
            try:
                # Updated to point to your exact file name: run_optimizer.py
                result = subprocess.run(
                    ["python", "run_optimizer.py"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                st.success("✅ Optimizer finished running successfully!")
                if result.stdout:
                    with st.expander("View Optimizer Output"):
                        st.text(result.stdout)
            except subprocess.CalledProcessError as e:
                st.error(f"Optimizer script failed: {e.stderr}")
            except Exception as e:
                st.error(f"Could not execute script: {e}")

                # ==========================================
# PASTE-AND-CREATE TRACK INGESTION
# ==========================================
with st.sidebar.expander("📋 Paste Track JSON"):
    st.markdown("Paste your raw track JSON block below to instantly create its file.")
    
    with st.form("paste_track_form"):
        pasted_json_input = st.text_area("Track JSON Data", height=150, placeholder='{"Moe": { ... }}')
        submit_paste = st.form_submit_button("Generate Track File")
        
        if submit_paste:
            if pasted_json_input.strip():
                try:
                    # Clean markdown wrappers if any were accidentally pasted
                    cleaned_input = pasted_json_input.strip()
                    if cleaned_input.startswith("```"):
                        cleaned_input = cleaned_input.split("```")[1]
                        if cleaned_input.startswith("json"):
                            cleaned_input = cleaned_input[4:]
                    
                    parsed_data = json.loads(cleaned_input.strip())
                    
                    # Handle both top-level wrapper dicts ("Moe": {...}) and direct payloads
                    if len(parsed_data) == 1 and isinstance(list(parsed_data.values())[0], dict):
                        track_name = list(parsed_data.keys())[0]
                        track_payload = parsed_data[track_name]
                    else:
                        st.error("Invalid JSON structure. Ensure it is keyed by the track name.")
                        track_payload = None
                        
                    if track_payload:
                        # Automatically determine region tag based on location string (e.g., "VIC")
                        location_str = str(track_payload.get("location", "")).upper()
                        if any(k in location_str for k in ["VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "AUSTRALIA"]):
                            region_tag = "Australia_Thoroughbred"
                        elif any(k in location_str for k in ["NY", "FL", "CA", "KY", "AR", "OH", "MN"]):
                            region_tag = "USA_Thoroughbred"
                        else:
                            region_tag = "Australia_Thoroughbred" # Default fallback
                            
                        track_payload["region_group"] = region_tag
                        
                        # Format filename and save
                        filename = f"{track_name.lower().replace(' ', '_').replace('-', '_')}.json"
                        filepath = os.path.join(TRACKS_DIR, filename)
                        
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(track_payload, f, indent=4)
                            
                        st.success(f"Successfully created {filename}!")
                        st.rerun() # Refresh app to update sidebar dropdowns immediately
                except Exception as e:
                    st.error(f"JSON Parsing Error: {e}")
            else:
                st.warning("Please paste a valid JSON block.")