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
    """Cleans Markdown formatting from JSON string."""
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*$', '', json_str)
    return json_str.strip()

def is_valid_pick(pick):
    """Checks if a pick object is valid/meaningful."""
    if not pick: return False
    name = str(pick.get('name', '')).strip().lower()
    invalid = ['none', 'n/a', 'null', 'no danger', 'no threat', 'tbd', 'horse name', '']
    return name and name not in invalid

# --- NAVIGATION & SYNC LOGIC ---

def generate_sidebar_content():
    """Generates the HTML sidebar for the static site."""
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    files.sort(reverse=True)
    
    links_html = ""
    for f in files:
        name = f.replace(".html", "").replace("_", " ")
        if "202" in name: 
            parts = name.split("202")
            name = f"{parts[0]} ({'202'+parts[1][:1]})"
        links_html += f'<a href="{f}" class="side-link">{name}</a>'
        
    return f"""
    <div class="sidebar">
        <div class="sidebar-header">
            <a href="../index.html" class="back-home">🏠 DASHBOARD</a>
        </div>
        <div class="sidebar-title">RACE MEETINGS</div>
        <div class="sidebar-links">
            {links_html}
        </div>
    </div>
    """

def sync_global_navigation():
    """Updates the sidebar on ALL historical HTML files."""
    new_sidebar = generate_sidebar_content()
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    count = 0
    for f in files:
        filepath = os.path.join(MEETINGS_DIR, f)
        try:
            with open(filepath, "r", encoding="utf-8") as file: content = file.read()
            pattern = r'<div class="sidebar">.*?</div>'
            if re.search(pattern, content, re.DOTALL):
                new_content = re.sub(pattern, new_sidebar, content, flags=re.DOTALL, count=1)
                with open(filepath, "w", encoding="utf-8") as file: file.write(new_content)
                count += 1
        except: pass
    return count

def update_homepage():
    """Rebuilds the index.html dashboard."""
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    grouped_files = {}
    
    for f in files:
        country = "International"
        try:
            with open(os.path.join(MEETINGS_DIR, f), 'r', encoding='utf-8') as file_obj:
                content_start = file_obj.read(500)
                if "META_COUNTRY" in content_start: 
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
    .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 20px; }}
    .header {{ display: flex; align-items: center; border-bottom: 4px solid #003366; padding-bottom: 20px; margin-bottom: 30px; background: #fff; padding: 30px; }}
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

def generate_meeting_html(data, region_override, is_preview_mode=False):
    """Generates the individual race meeting HTML page with PRINT FIXES."""
    country = data.get('meta', {}).get('jurisdiction', region_override)
    track_name = data.get('meta', {}).get('track', 'Unknown Track')
    track_date = data.get('meta', {}).get('date', 'Unknown Date')
    track_cond = data.get('meta', {}).get('track_condition', 'Standard')
    
    logo_src, _ = get_base64_logo()
    logo_html = f'<img src="{logo_src}" class="logo">' if logo_src else '<span style="font-size:2rem; margin-right:15px;">🏇</span>'

    sidebar_content = generate_sidebar_content()

    best_bets = []
    for r in data.get('races', []):
        conf = str(r.get('confidence_level', ''))
        top_pick = r.get('picks', {}).get('top_pick', {})
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
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #0f172a; margin: 0; background: #f8fafc; }}
    * {{ box-sizing: border-box; }}
    
    /* SIDEBAR */
    .sidebar {{ position: fixed; left: 0; top: 0; bottom: 0; width: 240px; background: #003366; overflow-y: auto; padding: 20px; color: white; display: flex; flex-direction: column; z-index: 100; }}
    .sidebar-title {{ font-size: 0.9rem; font-weight: 800; margin-bottom: 10px; margin-top: 20px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; }}
    .side-link {{ color: rgba(255,255,255,0.8); text-decoration: none; padding: 10px; display: block; border-radius: 4px; margin-bottom: 2px; transition: 0.2s; font-size: 0.95rem; }}
    .side-link:hover {{ background: rgba(255,255,255,0.1); color: white; padding-left: 15px; }}
    .back-home {{ background: #ff6b00; color: white; text-align: center; padding: 12px; border-radius: 4px; text-decoration: none; font-weight: 700; display: block; }}
    
    /* MAIN LAYOUT (TIGHTENED FOR WHITESPACE) */
    .main-content {{ margin-left: 240px; padding: 20px; max-width: 1100px; }}
    
    /* HEADER (TIGHTENED) */
    .header {{ display: flex; align-items: center; justify-content: space-between; border-bottom: 4px solid #003366; padding-bottom: 15px; margin-bottom: 15px; background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .logo {{ max-height: 50px; margin-right: 15px; }}
    .header-info h1 {{ margin: 0; font-size: 1.8rem; color: #003366; text-transform: uppercase; font-weight: 800; line-height: 1.1; }}
    .meta {{ color: #64748b; font-weight: 600; margin-top: 5px; font-size: 0.9rem; }}
    
    .print-btn {{ background: #fff; border: 1px solid #003366; color: #003366; padding: 8px 12px; cursor: pointer; font-weight: 700; border-radius: 4px; display: inline-flex; align-items: center; gap: 5px; }}
    
    /* NAV & RACES */
    .nav-bar {{ background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }}
    .nav-btn {{ background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: 600; font-size: 0.9rem; }}
    .nav-btn:hover {{ background: #003366; color: white; border-color: #003366; }}
    
    .race-section {{ margin-bottom: 25px; border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); page-break-inside: avoid; }}
    .race-header {{ background: #fff; border-bottom: 2px solid #ff6b00; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; font-weight: 800; color: #003366; font-size: 1.1rem; }}
    
    .picks-grid {{ display: flex; gap: 10px; padding: 15px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
    .pick-box {{ flex: 1; background: #fff; padding: 10px; border: 1px solid #e2e8f0; border-top: 4px solid #94a3b8; border-radius: 4px; }}
    .panel-best {{ border-top-color: #fbbf24; background-color: #fffbeb; }}
    .panel-top {{ border-top-color: #3b82f6; }}
    .panel-danger {{ border-top-color: #d97706; }}
    .panel-value {{ border-top-color: #10b981; }}
    
    .table-container {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 0; min-width: 500px; }}
    th {{ background: #f1f5f9; text-align: left; padding: 8px; font-size: 0.9rem; color: #475569; }}
    td {{ padding: 8px; border-bottom: 1px solid #eee; font-size: 0.95rem; }}
    .row-top {{ background: #f0f9ff; font-weight: 700; color: #003366; }}
    .exacta-box {{ margin: 15px; padding: 10px; background: #f1f5f9; border-left: 4px solid #64748b; border-radius: 4px; font-size: 0.95rem; }}
    .exacta-gold {{ background: #fffbeb; border-left-color: #fbbf24; }}

    /* RESPONSIVE */
    @media (max-width: 768px) {{
        .sidebar {{ display: none; }}
        .main-content {{ margin-left: 0; padding: 10px; }}
        .header {{ flex-direction: column; text-align: center; gap: 10px; padding: 15px; }}
        .logo {{ margin: 0; }}
        .header-tools {{ width: 100%; display: flex; justify-content: center; }}
        .picks-grid {{ flex-direction: column; }}
        .race-header {{ flex-direction: column; gap: 5px; align-items: flex-start; }}
        .mobile-nav {{ display: block; background: #003366; color: white; padding: 10px; text-align: center; font-weight: bold; text-decoration: none; margin: -10px -10px 15px -10px; }}
    }}
    @media (min-width: 769px) {{ .mobile-nav {{ display: none; }} }}
    
    /* PRINT OPTIMIZATION (THE FIX) */
    @media print {{ 
        .sidebar, .print-btn, .mobile-nav, .nav-bar {{ display: none !important; }} 
        .main-content {{ margin: 0 !important; padding: 0 !important; max-width: 100% !important; }}
        body {{ background: white !important; font-size: 11pt; }}
        .header {{ box-shadow: none; border: none; border-bottom: 2px solid #000; padding: 0; margin-bottom: 10px; }}
        .race-section {{ box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }}
        .picks-grid {{ background: #fff; border: none; }}
        .pick-box {{ border: 1px solid #000; }}
        th {{ background: #eee !important; -webkit-print-color-adjust: exact; }}
    }}
    </style></head><body>
    
    {sidebar_content}

    <div class="main-content">
        <a href="../index.html" class="mobile-nav">🏠 HOME / DASHBOARD</a>

        <div class="header">
            <div style="display:flex;align-items:center">
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
        is_best_bet = "High" in confidence or "Strong" in confidence or "5 Stars" in confidence
        
        top = r.get('picks', {}).get('top_pick', {})
        top_name = top.get('name', 'N/A')
        top_class = "panel-best" if is_best_bet else "panel-top"
        top_label = "🔥 BEST BET" if is_best_bet else "🏁 TOP PICK"
        
        dang = r.get('picks', {}).get('danger_horse', {})
        show_danger = is_valid_pick(dang)
        val = r.get('picks', {}).get('value_bet', {})
        show_value = is_valid_pick(val)
        exacta_strat = r.get('exotic_strategy', {}).get('exacta', '')
        exacta_class = "exacta-gold" if is_best_bet and len(exacta_strat) > 3 else "exacta-box"

        html += f"""<div id="race-{r_num}" class="race-section">
        <div class="race-header"><div>RACE {r_num} - {r.get('distance','')}</div><div style="font-size:0.9em; opacity:0.8">{confidence}</div></div>
        <div class="picks-grid">
            <div class="pick-box {top_class}"><b>{top_label}: #{top.get('number','')} {top_name}</b><br><small>{top.get('reason','')}</small></div>"""
            
        if show_danger:
            html += f"""<div class="pick-box panel-danger"><b>⚠️ DANGER: #{dang.get('number','')} {dang.get('name','')}</b><br><small>{dang.get('reason','')}</small></div>"""
        if show_value:
            html += f"""<div class="pick-box panel-value"><b>💰 VALUE: #{val.get('number','')} {val.get('name','')}</b><br><small>{val.get('reason','')}</small></div>"""
            
        html += f"""</div>
        <div class="table-container"><table><thead><tr><th>#</th><th>Horse</th><th>Rating</th><th>Verdict</th></tr></thead><tbody>"""
        
        for c in r.get('contenders', [])[:6]:
            style = ' class="row-top"' if str(c.get('number')) == str(top.get('number')) else ''
            html += f"<tr{style}><td>{c.get('number')}</td><td>{c.get('name')}</td><td>{c.get('rating')}</td><td>{c.get('verdict')}</td></tr>"
            
        if len(exacta_strat) > 3:
            html += f"""</tbody></table></div><div class="{exacta_class}"><b>EXACTA STRATEGY:</b> {exacta_strat}</div></div>"""
        else:
            html += "</tbody></table></div></div>"
    
    html += "</div></body></html>"
    return html

# --- AUTO-UPDATE INDEX ON START ---
update_homepage()

# --- SIDEBAR UI ---
st.sidebar.header("⚙️ Settings")

# 1. API Key Handling (Manual Override)
default_key = ""
try:
    if "GOOGLE_API_KEY" in st.secrets:
        default_key = st.secrets["GOOGLE_API_KEY"]
except: pass

api_key = st.sidebar.text_input("Gemini API Key", value=default_key, type="password")

st.sidebar.markdown("---")
st.sidebar.header("🚀 Admin")
if st.sidebar.button("🔄 Sync Nav & Deploy"):
    count = sync_global_navigation()
    update_homepage()
    st.sidebar.success(f"Synced {count} files & Updated Index.")
    try:
        subprocess.Popen("deploy.bat", shell=True, cwd=BASE_DIR)
        st.sidebar.success("Deploying...")
    except: st.sidebar.error("Deploy script missing.")

# --- PAST LOGS VIEWER ---
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

# 2. Model Selector (Default to Gemini 3.0 Pro Preview)
model_options = [
    "gemini-3.0-pro-preview",
    "gemini-2.0-flash-exp", 
    "gemini-1.5-pro", 
    "gemini-1.5-flash"
]
target_model = st.sidebar.selectbox("Select Model", model_options, index=0)

if st.sidebar.checkbox("Type a Custom Model Name?"):
    target_model = st.sidebar.text_input("Model Name", value="gemini-experimental")

if api_key:
    genai.configure(api_key=api_key)
    st.sidebar.success(f"Ready: {target_model}")

# --- TRACK DB LOADER ---
track_db = {}
try:
    with open(os.path.join(DATA_DIR, "track_db.json"), "r") as f: track_db = json.load(f)
except: pass

country_options = list(track_db.keys()) if track_db else ["USA", "Australia", "International"]
selected_country = st.sidebar.selectbox("Region", country_options)

selected_track_data = None
selected_track_name = "Unknown"
if track_db and selected_country in track_db:
    track_list = list(track_db[selected_country].keys()) + ["Other (Manual Entry)"]
    selected_track_name = st.sidebar.selectbox("Track", track_list)
    if selected_track_name == "Other (Manual Entry)":
        selected_track_name = st.sidebar.text_input("Enter Track Name", value="Unknown Track")
        selected_track_data = None
    else:
        selected_track_data = track_db[selected_country][selected_track_name]

# Logic File Selection
if "USA" in selected_country: region_code, system_file = "USA", "system_usa.md"
elif "Australia" in selected_country: region_code, system_file = "Australia", "system_aus.md"
elif "UK" in selected_country: region_code, system_file = "UK", "system_uk.md"
else: region_code, system_file = "International", "system_aus.md"
if not os.path.exists(os.path.join(LOGIC_DIR, system_file)) and "UK" in region_code: system_file = "system_aus.md"

# --- MAIN PAGE ---
st.title(f"🏆 Exacta AI: {selected_track_name}")
uploaded_file = st.file_uploader(f"Upload {region_code} PDF", type="pdf")
scratches = st.text_area("📋 Scratchings / Updates", height=70)

# Session State Initialization
if 'html_content' not in st.session_state: st.session_state.html_content = None
if 'preview_html' not in st.session_state: st.session_state.preview_html = None
if 'report_filename' not in st.session_state: st.session_state.report_filename = None
if 'raw_response' not in st.session_state: st.session_state.raw_response = ""
if 'data_ready' not in st.session_state: st.session_state.data_ready = False
if 'json_data' not in st.session_state: st.session_state.json_data = None

# --- ANALYSIS ACTION ---
if st.button("Analyze Race Card (Preview Only)", type="primary"):
    if not uploaded_file or not api_key:
        st.error("Please provide an API Key and a PDF file.")
    else:
        with st.spinner(f"Reading and Analyzing with {target_model}..."):
            try:
                # 1. Save PDF locally temp
                temp_pdf_path = os.path.join(TEMP_DIR, "current_card.pdf")
                with open(temp_pdf_path, "wb") as f: f.write(uploaded_file.getbuffer())

                # 2. Upload to Gemini
                remote_file = genai.upload_file(temp_pdf_path, mime_type="application/pdf")
                while remote_file.state.name == "PROCESSING":
                    time.sleep(1)
                    remote_file = genai.get_file(remote_file.name)

                # 3. Load Logic & Data
                logic_path = os.path.join(LOGIC_DIR, system_file)
                logic_content = open(logic_path, 'r', encoding='utf-8').read() if os.path.exists(logic_path) else ""
                track_facts = json.dumps(selected_track_data) if selected_track_data else "No historical bias data."

                # 4. Construct Prompt
                model = genai.GenerativeModel(target_model, generation_config={"response_mime_type": "application/json"})
                
                prompt = f"""
                You are a Professional Handicapper ({region_code}).
                
                [TASK]
                Look at the PDF. Identify EVERY race (Race 1, Race 2...). 
                Extract the data.
                
                [INSTRUCTIONS]
                - Do NOT output 'Race 0'. Start at Race 1.
                - If NO danger/value exists, set name to "None".
                
                [STRICT OUTPUT SCHEMA]
                {{
                  "meta": {{ "track": "Track Name", "date": "YYYY-MM-DD", "track_condition": "Fast/Firm" }},
                  "races": [
                    {{
                      "number": 1,
                      "distance": "6 Furlongs",
                      "confidence_level": "High (or Low/Medium)",
                      "picks": {{
                        "top_pick": {{ "number": "1", "name": "Horse Name", "reason": "Reason" }},
                        "danger_horse": {{ "number": "2", "name": "Horse Name", "reason": "Reason" }},
                        "value_bet": {{ "number": "3", "name": "Horse Name", "odds": "10-1", "reason": "Reason" }}
                      }},
                      "exotic_strategy": {{ "exacta": "Box 1,2", "trifecta": "..." }},
                      "contenders": [
                        {{ "number": "1", "name": "Horse Name", "rating": 95, "verdict": "Top Pick" }}
                      ]
                    }}
                  ]
                }}
                
                [TRACK FACTS] {track_facts}
                [SYSTEM RULES] {logic_content}
                [UPDATES] {scratches}
                """
                
                # 5. Execute
                response = model.generate_content([prompt, remote_file])
                st.session_state.raw_response = response.text 
                
                # 6. Parse
                json_str = clean_json_string(response.text)
                data = json.loads(json_str)
                st.session_state.json_data = data
                
                # Sanitize Data
                if isinstance(data, list): data = data[0] if data else {}
                if "meta" not in data: data["meta"] = {}
                if selected_track_name != "Unknown" and "Manual" not in selected_track_name: 
                    data["meta"]["track"] = selected_track_name
                
                if not data["meta"].get("date"): data["meta"]["date"] = datetime.today().strftime('%Y-%m-%d')
                if not data["meta"].get("track_condition"): data["meta"]["track_condition"] = "Standard"
                
                if data.get('races') and str(data['races'][0].get('number')) == "0":
                    st.warning("⚠️ Warning: AI returned 'Race 0'. It may have failed to read the PDF text.")

                # 7. Generate HTML
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

# --- SAVE & PUBLISH SECTION ---
if st.session_state.data_ready:
    st.markdown("---")
    st.success("✅ Analysis Complete! Review below.")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        update_idx = st.checkbox("Auto-Update Index.html", value=True)
        if st.button("💾 Save & Publish", type="primary"):
            # A. SAVE HTML PAGE
            filepath = os.path.join(MEETINGS_DIR, st.session_state.report_filename)
            with open(filepath, "w", encoding='utf-8') as f:
                f.write(st.session_state.html_content)
            
            # B. SAVE RAW JSON LOG
            if st.session_state.json_data:
                log_filename = st.session_state.report_filename.replace(".html", ".json")
                with open(os.path.join(LOGS_DIR, log_filename), "w", encoding='utf-8') as f:
                    json.dump(st.session_state.json_data, f, indent=4)

                # C. APPEND TO MASTER CSV (OPTIMIZER MEMORY)
                master_csv_path = os.path.join(LOGS_DIR, "master_betting_history.csv")
                file_exists = os.path.exists(master_csv_path)
                
                try:
                    with open(master_csv_path, mode='a', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['date', 'track', 'race_number', 'top_pick_num', 'top_pick_name', 'value_pick_num', 'value_pick_name', 'confidence', 'ai_model']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        if not file_exists:
                            writer.writeheader()
                        
                        # Flatten data
                        meta = st.session_state.json_data.get("meta", {})
                        for race in st.session_state.json_data.get("races", []):
                            writer.writerow({
                                'date': meta.get('date'),
                                'track': meta.get('track'),
                                'race_number': race.get('number'),
                                'top_pick_num': race.get('picks', {}).get('top_pick', {}).get('number', 'N/A'),
                                'top_pick_name': race.get('picks', {}).get('top_pick', {}).get('name', 'N/A'),
                                'value_pick_num': race.get('picks', {}).get('value_bet', {}).get('number', ''),
                                'value_pick_name': race.get('picks', {}).get('value_bet', {}).get('name', ''),
                                'confidence': race.get('confidence_level', ''),
                                'ai_model': target_model
                            })
                except Exception as e:
                    st.error(f"Failed to log to CSV: {e}")
            
            # D. GLOBAL SYNC
            count = sync_global_navigation()
            
            if update_idx:
                update_homepage()
                st.success(f"Saved HTML, Logged to CSV & Synced {count} files.")
            
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