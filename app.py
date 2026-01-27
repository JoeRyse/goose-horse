import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import os
import json
import time
import re
import subprocess
import base64
import csv
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

# Ensure folders exist
for d in [DATA_DIR, DOCS_DIR, MEETINGS_DIR, LOGIC_DIR, TEMP_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

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
    name = str(pick.get('name', '')).strip().lower()
    invalid = ['none', 'n/a', 'null', 'no danger', 'no threat', 'tbd', 'horse name', '', 'no significant danger']
    return name and name not in invalid

# --- TRACK DB RECURSIVE HELPERS (THE FIX) ---
def get_all_tracks_from_region(data):
    """Recursively finds all track names in a nested JSON region."""
    tracks = []
    if isinstance(data, dict):
        for k, v in data.items():
            # If it has "bias_notes" or "location", it's a TRACK
            if isinstance(v, dict) and ("bias_notes" in v or "location" in v):
                tracks.append(k)
            # If it's a folder (like "New_South_Wales"), dig deeper
            elif isinstance(v, dict):
                tracks.extend(get_all_tracks_from_region(v))
    return sorted(list(set(tracks)))

def find_track_data(data, target_name):
    """Recursively searches for the specific track object."""
    if isinstance(data, dict):
        if target_name in data:
            return data[target_name]
        for k, v in data.items():
            if isinstance(v, dict):
                result = find_track_data(v, target_name)
                if result: return result
    return None

# --- HOMEPAGE GENERATION ---

def update_homepage():
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    grouped_files = {}
    
    for f in files:
        country = "International"
        try:
            with open(os.path.join(MEETINGS_DIR, f), 'r', encoding='utf-8') as file_obj:
                content = file_obj.read(500)
                if "META_COUNTRY" in content: 
                    match = re.search(r'META_COUNTRY:([^\s]+)', content_start)
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

# --- CLEAN CSS (NO SIDEBAR, CENTERED, ROBUST HEADER) ---
CLEAN_CSS = """
    body { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #0f172a; margin: 0; background: #f8fafc; }
    * { box-sizing: border-box; }
    
    /* HIDE SIDEBAR & HOME BUTTONS COMPLETELY */
    .sidebar, .sidebar-title, .sidebar-links, .side-link, .mobile-nav, .back-home, .top-nav { display: none !important; }
    
    /* MAIN LAYOUT - CENTERED */
    .main-content { margin: 0 auto; padding: 20px; max-width: 1000px; }
    
    /* HEADER - ROBUST LAYOUT */
    .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 4px solid #003366; padding-bottom: 15px; margin-bottom: 15px; background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 0; }
    .header-branding { display: flex; align-items: center; flex: 1; } 
    .logo { max-height: 50px; margin-right: 15px; width: auto; }
    .header-info h1 { margin: 0; font-size: 1.8rem; color: #003366; text-transform: uppercase; font-weight: 800; line-height: 1.1; }
    .meta { color: #64748b; font-weight: 600; margin-top: 5px; font-size: 0.9rem; }
    
    .print-btn { background: #fff; border: 1px solid #003366; color: #003366; padding: 8px 12px; cursor: pointer; font-weight: 700; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px; }
    
    /* RACES */
    .nav-bar { background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
    .nav-btn { background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: 600; font-size: 0.9rem; }
    .nav-btn:hover { background: #003366; color: white; border-color: #003366; }
    
    .race-section { margin-bottom: 25px; border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); page-break-inside: avoid; }
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

    /* RESPONSIVE */
    @media (max-width: 768px) {
        .main-content { padding: 10px; }
        .header { flex-direction: column; text-align: center; gap: 10px; padding: 15px; }
        .logo { margin: 0; }
        .header-tools { width: 100%; display: flex; justify-content: center; }
        .picks-grid { flex-direction: column; }
        .race-header { flex-direction: column; gap: 5px; align-items: flex-start; }
    }
    
    /* PRINT OPTIMIZATION (STRICT) */
    @media print { 
        .print-btn, .nav-bar, .mobile-nav, .back-home, .top-nav { display: none !important; } 
        .main-content { margin: 0 !important; padding: 0 !important; max-width: 100% !important; }
        body { background: white !important; font-size: 11pt; }
        .header { box-shadow: none; border: none; border-bottom: 2px solid #000; padding: 0; margin-bottom: 10px; margin-top: 0; }
        .race-section { box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }
        .picks-grid { background: #fff; border: none; }
        .pick-box { border: 1px solid #000; }
        th { background: #eee !important; -webkit-print-color-adjust: exact; }
    }
"""

def generate_meeting_html(data, region_override, is_preview_mode=False):
    """Generates CLEAN HTML with NO SIDEBAR & NO HOME BUTTON. Handles legacy pick structure."""
    country = data.get('meta', {}).get('jurisdiction', region_override)
    track_name = data.get('meta', {}).get('track', 'Unknown Track')
    track_date = data.get('meta', {}).get('date', 'Unknown Date')
    track_cond = data.get('meta', {}).get('track_condition', 'Standard')
    
    logo_src, _ = get_base64_logo()
    logo_html = f'<img src="{logo_src}" class="logo">' if logo_src else '<span style="font-size:2rem; margin-right:15px;">🏇</span>'

    # BEST BETS LOGIC (ROBUST VERSION)
    best_bets = []
    for r in data.get('races', []):
        conf = str(r.get('confidence_level', ''))
        
        # ----------------------------------------------------
        # DATA NORMALIZATION: HANDLE 'SELECTIONS' VS 'PICKS'
        # ----------------------------------------------------
        selections = r.get('selections', [])
        if not selections and 'picks' in r:
            # Fallback for old JSON format
            p = r['picks']
            selections = [p.get('top_pick', {}), p.get('danger_horse', {}), p.get('value_bet', {})]
            # Clean up empty dicts
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
        best_bets_html = '<div style="background:#fffbeb; border:2px solid #fbbf24; padding:15px; margin-bottom:20px; border-radius:8px;">'
        best_bets_html += '<h2 style="margin-top:0; color:#b45309; font-size:1.2rem; display:flex; align-items:center;">🔥 <span style="margin-left:8px">PRIME BETS</span></h2><div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px;">'
        for bb in best_bets[:3]:
            best_bets_html += f'<div><div style="font-weight:bold; font-size:1.1em;">R{bb["race"]}: {bb["horse"]}</div><div style="font-size:0.9em; color:#555;">{bb["reason"]}</div></div>'
        best_bets_html += '</div></div>'

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
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>{CLEAN_CSS}</style></head><body>
    
    <div class="main-content">
        <div class="header">
            <div class="header-branding">
                {logo_html}
                <div class="header-info">
                    <h1>{track_name}</h1>
                    <div class="meta">{track_date} • {track_cond}</div>
                </div>
            </div>
            <div class="header-tools">
                <button onclick="window.print()" class="print-btn">🖨️ PRINT</button>
            </div>
        </div>
        
        {best_bets_html}
        
        <div class="nav-bar">
            <span style="font-weight:700; color:#64748b; margin-right:10px;">JUMP TO:</span>
            {nav_links}
        </div>"""

    for r in data.get('races', []):
        r_num = r.get('number', '?')
        confidence = str(r.get('confidence_level', ''))
        surface = str(r.get('surface', ''))
        if surface: surface = f" ({surface})"
        
        is_best_bet = "High" in confidence or "Strong" in confidence or "5 Stars" in confidence
        
        # ----------------------------------------------------
        # DATA NORMALIZATION (AGAIN, PER RACE LOOP)
        # ----------------------------------------------------
        selections = r.get('selections', [])
        if not selections and 'picks' in r:
            p = r['picks']
            selections = [p.get('top_pick', {}), p.get('danger_horse', {}), p.get('value_bet', {})]
            selections = [s for s in selections if s and s.get('name')]

        top = selections[0] if len(selections) > 0 else {}
        
        top_name = top.get('name', 'N/A')
        top_class = "panel-best" if is_best_bet else "panel-top"
        top_label = "🔥 BEST BET" if is_best_bet else "🏁 TOP PICK"
        
        dang = r.get('danger_horse', {})
        show_danger = is_valid_pick(dang)
        
        exacta_strat = r.get('exotic_strategy', {}).get('strategy', '')
        if not exacta_strat: exacta_strat = r.get('exotic_strategy', {}).get('exacta', '') # Fallback
        
        exacta_class = "exacta-gold" if is_best_bet and len(exacta_strat) > 3 else "exacta-box"

        html += f"""<div id="race-{r_num}" class="race-section">
        <div class="race-header"><div>RACE {r_num} - {r.get('distance','')}{surface}</div><div style="font-size:0.9em; opacity:0.8">{confidence}</div></div>
        <div class="picks-grid">
            <div class="pick-box {top_class}"><b>{top_label}: #{top.get('number','')} {top_name}</b><br><small>{top.get('reason','')}</small></div>"""
            
        if show_danger:
            html += f"""<div class="pick-box panel-danger"><b>⚠️ DANGER: #{dang.get('number','')} {dang.get('name','')}</b><br><small>{dang.get('reason','')}</small></div>"""
            
        html += f"""</div>
        <div class="table-container"><table><thead><tr><th>#</th><th>Horse</th><th>Reasoning / Notes</th></tr></thead><tbody>"""
        
        for s in selections[:3]:
            style = ' class="row-top"' if str(s.get('number')) == str(top.get('number')) else ''
            html += f"<tr{style}><td>{s.get('number')}</td><td>{s.get('name')}</td><td>{s.get('reason')}</td></tr>"
            
        if len(exacta_strat) > 3:
            html += f"""</tbody></table></div><div class="{exacta_class}"><b>BETTING STRATEGY:</b> {exacta_strat}</div></div>"""
        else:
            html += "</tbody></table></div></div>"
    
    html += "</div></body></html>"
    return html

# --- AUTO-UPDATE INDEX ON START ---
update_homepage()

# --- SIDEBAR UI ---
st.sidebar.header("⚙️ Settings")

default_key = ""
try:
    if "GOOGLE_API_KEY" in st.secrets:
        default_key = st.secrets["GOOGLE_API_KEY"]
except: pass

api_key = st.sidebar.text_input("Gemini API Key", value=default_key, type="password")

st.sidebar.markdown("---")
st.sidebar.header("🚀 Admin")
if st.sidebar.button("🔄 Sync Nav & Deploy"):
    update_homepage()
    st.sidebar.success(f"Updated Dashboard Index.")
    try:
        subprocess.Popen("deploy.bat", shell=True, cwd=BASE_DIR)
        st.sidebar.success("Deploying...")
    except: st.sidebar.error("Deploy script missing.")

# --- AGGRESSIVE FIXER (UPDATED FOR HEADER PROTECTION) ---
if st.sidebar.button("🛠️ Fix Legacy Layouts"):
    count = 0
    with st.spinner("Removing Home buttons and Sidebars, protecting Headers..."):
        for f in os.listdir(MEETINGS_DIR):
            if f.endswith(".html"):
                fp = os.path.join(MEETINGS_DIR, f)
                try:
                    with open(fp, "r", encoding="utf-8") as file:
                        content = file.read()
                    
                    # 1. REMOVE OLD SIDEBAR
                    content = re.sub(r'<div class="sidebar">.*?</div>', '', content, flags=re.DOTALL)
                    
                    # 2. REMOVE "RACE MEETINGS" TEXT DUMP
                    content = re.sub(r'RACE MEETINGS.*?2026\)', '', content, flags=re.DOTALL)
                    
                    # 3. REMOVE "TOP NAV" and "HOME BUTTONS"
                    content = re.sub(r'<div class="top-nav">.*?</div>', '', content, flags=re.DOTALL)
                    content = re.sub(r'<a href=.*?class="mobile-nav".*?>.*?</a>', '', content, flags=re.DOTALL)
                    content = re.sub(r'<a href=.*?class="back-home".*?>.*?</a>', '', content, flags=re.DOTALL)
                    
                    # 4. REPLACE CSS WITH CLEAN CSS
                    content = re.sub(r'<style>.*?</style>', f'<style>{CLEAN_CSS}</style>', content, flags=re.DOTALL)
                    
                    # 5. ENSURE HEADER BRANDING WRAPPER EXISTS (Fixes collapsed headers)
                    if 'class="header-branding"' not in content and 'class="header"' in content:
                         content = content.replace('<div style="display:flex;align-items:center">', '<div class="header-branding">')
                    
                    with open(fp, "w", encoding="utf-8") as file:
                        file.write(content)
                    count += 1
                except: pass
    st.sidebar.success(f"Cleaned {count} legacy files!")

st.sidebar.markdown("---")
st.sidebar.header("📜 Logic Logs")
log_files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
log_files.sort(reverse=True)
if log_files:
    selected_log = st.sidebar.selectbox("Select Log", ["None"] + log_files)
    if selected_log != "None":
        with open(os.path.join(LOGS_DIR, selected_log), 'r') as f:
            st.sidebar.json(json.load(f))

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI Model")

model_options = [
    "gemini-3-pro-preview", 
    "gemini-2.0-flash-exp", 
    "gemini-1.5-pro", 
    "gemini-1.5-flash"
]
target_model = st.sidebar.selectbox("Select Model", model_options, index=0)

if st.sidebar.checkbox("Type a Custom Model Name?"):
    target_model = st.sidebar.text_input("Model Name", value="gemini-experimental")

creativity_temp = st.sidebar.slider("Creativity (Temperature)", 0.0, 1.0, 0.4, 0.1)

if api_key:
    genai.configure(api_key=api_key)
    st.sidebar.success(f"Ready: {target_model}")

# --- TRACK DB LOADER (UPDATED) ---
track_db = {}
try:
    with open(os.path.join(DATA_DIR, "track_db.json"), "r") as f: track_db = json.load(f)
except: pass

# MAPPING REGIONS TO JSON KEYS
REGION_MAP = {
    "Australia": "Australia_Thoroughbred",
    "USA (Thoroughbred)": "USA_Thoroughbred",
    "USA (Harness)": "USA_Harness",
    "Europe": "Europe_Thoroughbred",
    "Asia": "Asia_Thoroughbred",
    "Australia (Harness)": "Australia_Harness",
    "Canada (Harness)": "Canada_Harness",
    "Europe (Harness)": "Europe_Harness"
}

# Country selection
country_options = list(REGION_MAP.keys())
selected_country_label = st.sidebar.selectbox("Region/Type", country_options)
selected_country_key = REGION_MAP[selected_country_label]

selected_track_data = None
selected_track_name = "Unknown"

# --- FLATTEN TRACK LIST (THE FIX) ---
if track_db and selected_country_key in track_db:
    # Use the helper to find ALL tracks in this region (including nested ones)
    track_list = get_all_tracks_from_region(track_db[selected_country_key])
    track_list = ["Other (Manual Entry)"] + track_list
    selected_track_name = st.sidebar.selectbox("Track", track_list)
    
    if selected_track_name == "Other (Manual Entry)":
        selected_track_name = st.sidebar.text_input("Enter Track Name", value="Unknown Track")
        has_passing_lane = st.sidebar.checkbox("Has Passing Lane?", value=False)
        selected_track_data = {
            "bias_notes": f"Manual Entry. Passing Lane: {has_passing_lane}.",
            "passing_lane": has_passing_lane
        }
    else:
        # Use helper to FIND the specific track object deep in the JSON
        selected_track_data = find_track_data(track_db[selected_country_key], selected_track_name)

# --- SYSTEM LOGIC SELECTOR ---
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

# Fallback if file doesn't exist
if not os.path.exists(os.path.join(LOGIC_DIR, system_file)): 
    # Try generic fallback
    if "Harness" in region_code:
         # Write default harness logic if missing
         pass # Assume user will create it or use existing logic
    else:
         system_file = "system_usa.md" # Default fallback

# --- MAIN PAGE ---
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
                      "number": 1,
                      "distance": "6 Furlongs",
                      "surface": "Dirt", 
                      "confidence_level": "High (or Low/Medium)",
                      "selections": [
                        {{ "number": "1", "barrier": "4", "name": "Horse A", "reason": "Detailed reasoning..." }},
                        {{ "number": "2", "barrier": "2", "name": "Horse B", "reason": "Detailed reasoning..." }},
                        {{ "number": "3", "barrier": "9", "name": "Horse C", "reason": "Detailed reasoning..." }}
                      ],
                      "danger_horse": {{ "number": "4", "barrier": "1", "name": "Horse D", "reason": "Why it is a threat" }},
                      "exotic_strategy": {{ "strategy": "Win Bet #1, Exacta Box 1-2, Trifecta 1 / 2,3 / ALL" }}
                    }}
                  ]
                }}
                """

                user_prompt = f"""
                [TASK]
                Analyze the attached PDF race card.
                Identify EVERY race. Extract the data and apply the handicapping logic defined in the system instructions.
                
                [UPDATES/SCRATCHES]
                {scratches}
                
                [CRITICAL INSTRUCTIONS]
                1. Start at Race 1.
                2. Provide exactly 3 selections per race in order of preference (1st, 2nd, 3rd).
                3. EXTRACT SURFACE: Identify the surface (Dirt, Turf, Synthetic) for each race individually from the PDF.
                4. EXTRACT BARRIER/POST: You must extract the post position (barrier) for every selection. If only one number exists, use that.
                5. DANGER HORSE: Only list a danger horse if there is a LEGITIMATE THREAT. If none, set name to "None".
                6. STRATEGY: Provide a specific betting strategy based on confidence.
                """
                
                model = genai.GenerativeModel(
                    target_model, 
                    system_instruction=system_instruction,
                    generation_config={"response_mime_type": "application/json", "temperature": creativity_temp}
                )
                
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
                
            except Exception as e:
                st.error(f"Error: {e}")

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

                master_csv_path = os.path.join(LOGS_DIR, "master_betting_history.csv")
                file_exists = os.path.exists(master_csv_path)
                
                try:
                    with open(master_csv_path, mode='a', newline='', encoding='utf-8') as csvfile:
                        fieldnames = [
                            'date', 'track', 'race_number', 'distance', 'surface', 'condition',
                            'p1_num', 'p1_barrier', 'p1_name', 'p1_reason', 
                            'p2_num', 'p2_barrier', 'p2_name', 'p2_reason', 
                            'p3_num', 'p3_barrier', 'p3_name', 'p3_reason', 
                            'danger_num', 'danger_barrier', 'danger_name', 'danger_reason',
                            'confidence', 'ai_model', 'temperature'
                        ]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        if not file_exists:
                            writer.writeheader()
                        
                        meta = st.session_state.json_data.get("meta", {})
                        for race in st.session_state.json_data.get("races", []):
                            
                            # ----------------------------------------------------
                            # DATA NORMALIZATION FOR CSV (PER RACE)
                            # ----------------------------------------------------
                            selections = race.get('selections', [])
                            if not selections and 'picks' in race:
                                p = race['picks']
                                selections = [p.get('top_pick', {}), p.get('danger_horse', {}), p.get('value_bet', {})]
                                selections = [s for s in selections if s and s.get('name')]
                            
                            while len(selections) < 3: selections.append({})
                            
                            dang = race.get('danger_horse', {})
                            
                            writer.writerow({
                                'date': meta.get('date'),
                                'track': meta.get('track'),
                                'race_number': race.get('number'),
                                'distance': race.get('distance', ''),
                                'surface': race.get('surface', ''),
                                'condition': meta.get('track_condition', ''),
                                
                                'p1_num': selections[0].get('number', 'N/A'),
                                'p1_barrier': selections[0].get('barrier', ''),
                                'p1_name': selections[0].get('name', 'N/A'),
                                'p1_reason': selections[0].get('reason', 'N/A'),
                                
                                'p2_num': selections[1].get('number', ''),
                                'p2_barrier': selections[1].get('barrier', ''),
                                'p2_name': selections[1].get('name', ''),
                                'p2_reason': selections[1].get('reason', ''),
                                
                                'p3_num': selections[2].get('number', ''),
                                'p3_barrier': selections[2].get('barrier', ''),
                                'p3_name': selections[2].get('name', ''),
                                'p3_reason': selections[2].get('reason', ''),
                                
                                'danger_num': dang.get('number', ''),
                                'danger_barrier': dang.get('barrier', ''),
                                'danger_name': dang.get('name', ''),
                                'danger_reason': dang.get('reason', ''),
                                
                                'confidence': race.get('confidence_level', ''),
                                'ai_model': target_model,
                                'temperature': creativity_temp
                            })
                except Exception as e:
                    st.error(f"Failed to log to CSV: {e}")
            
            if update_idx:
                update_homepage()
                st.success(f"Saved HTML & Updated Dashboard.")
            
            try:
                subprocess.Popen("deploy.bat", shell=True, cwd=BASE_DIR)
                st.success("Deploying to Web...")
            except: pass
            
    with col2:
        st.download_button("⬇️ Download HTML", st.session_state.html_content, st.session_state.report_filename, "text/html")
    
    st.markdown("### 📝 Live Report Preview")
    components.html(st.session_state.preview_html, height=800, scrolling=True)

if st.session_state.raw_response:
    with st.expander("🔍 View Raw AI Response (Debug)"):
        st.text(st.session_state.raw_response)