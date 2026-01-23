import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
import json
import re
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Exacta AI", page_icon="🏇", layout="wide")

# PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEETINGS_DIR = os.path.join(DOCS_DIR, "meetings")
LOGIC_DIR = os.path.join(BASE_DIR, "logic")

# Ensure directories exist
for d in [DATA_DIR, DOCS_DIR, MEETINGS_DIR, LOGIC_DIR]:
    os.makedirs(d, exist_ok=True)

# --- SESSION STATE ---
if 'results' not in st.session_state: st.session_state.results = None
if 'raw_pdf_text' not in st.session_state: st.session_state.raw_pdf_text = ""
if 'raw_ai_json' not in st.session_state: st.session_state.raw_ai_json = ""

# --- 1. LOAD DATABASES ---
track_db = {}
track_db_path = os.path.join(DATA_DIR, "track_db.json")
try:
    if os.path.exists(track_db_path):
        with open(track_db_path, "r", encoding="utf-8") as f:
            track_db = json.load(f)
except: pass

# --- 2. SIDEBAR SETUP ---
st.sidebar.header("🔑 Setup")
if "GEMINI_API_KEY" in os.environ: del os.environ["GEMINI_API_KEY"]
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# --- MODEL SELECTOR (THE FIX) ---
st.sidebar.subheader("🤖 AI Model")
model_options = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "Custom"]
model_choice = st.sidebar.selectbox("Select Model", model_options, index=0)

if model_choice == "Custom":
    target_model = st.sidebar.text_input("Enter Model Name", value="gemini-3-pro-preview")
else:
    target_model = model_choice

if api_key:
    genai.configure(api_key=api_key)
    st.sidebar.success(f"Ready: {target_model}")

st.sidebar.markdown("---")

# Country/Track Selection
country_options = list(track_db.keys()) if track_db else ["USA", "Australia", "UK", "Japan", "International"]
selected_country = st.sidebar.selectbox("🌍 1. Select Region", country_options)

selected_track_data = None
selected_track_name = "Unknown Track"
if track_db and selected_country in track_db:
    track_list = list(track_db[selected_country].keys())
    selected_track_name = st.sidebar.selectbox("📍 2. Select Track", track_list)
    selected_track_data = track_db[selected_country][selected_track_name]
    st.sidebar.info(f"**Info:** {selected_track_data['direction']} • {selected_track_data.get('bias_notes', 'N/A')[:100]}...")

# Logic Mapping
if "USA" in selected_country: region_code, system_file = "USA", "system_usa.md"
elif "Australia" in selected_country: region_code, system_file = "Australia", "system_aus.md"
elif "UK" in selected_country: region_code, system_file = "UK", "system_uk.md"
else: region_code, system_file = "International", "system_aus.md"

if not os.path.exists(os.path.join(LOGIC_DIR, system_file)) and "UK" in region_code: system_file = "system_aus.md"

# --- 3. MAIN UI ---
st.title(f"🏆 Exacta AI: {selected_track_name}")
if not api_key: st.warning("👈 Please enter API Key.")

uploaded_file = st.file_uploader(f"Upload {region_code} Race Card (PDF)", type="pdf")
scratches = st.text_area("📋 Scratchings / Updates", height=70, placeholder="e.g. Race 1: #4 Scratched")

# --- 4. HTML GENERATOR ---
def generate_meeting_html(data, region_override):
    country = data.get('meta', {}).get('jurisdiction', region_override)
    track_name = data.get('meta', {}).get('track', 'Unknown Track')
    track_date = data.get('meta', {}).get('date', 'Unknown Date')
    track_cond = data.get('meta', {}).get('track_condition', 'Standard')
    
    nav_links = ""
    races = data.get('races', [])
    for r in races:
        r_num = r.get('number', '0')
        nav_links += f'<a href="#race-{r_num}" class="nav-btn">R{r_num}</a>'

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{track_name}</title>
    <style>body{{font-family:'Segoe UI',sans-serif;background:#fff;color:#0f172a;padding:30px}}
    .header{{border-bottom:4px solid #003366;padding-bottom:20px;margin-bottom:20px}}
    .race-section{{margin-bottom:40px;border:1px solid #e2e8f0;background:#fff}}
    .race-header{{background:#fff;border-bottom:3px solid #ff6b00;padding:12px 20px;display:flex;justify-content:space-between;font-weight:800;color:#003366;font-size:20px}}
    .nav-btn{{background:#fff;border:1px solid #003366;color:#003366;padding:5px 10px;text-decoration:none;margin-right:5px;border-radius:4px;font-weight:700}}
    .nav-btn:hover{{background:#003366;color:#fff}}
    .picks-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:15px;background:#f8fafc;border-bottom:1px solid #e2e8f0}}
    .pick-box{{background:#fff;padding:10px;border:1px solid #e2e8f0;border-top:4px solid #003366}}
    .pick-box.danger{{border-top-color:#d97706}} .pick-box.value{{border-top-color:#ff6b00}}
    table{{width:100%;border-collapse:collapse;margin-top:10px}} th{{background:#f1f5f9;text-align:left;padding:8px}} td{{padding:8px;border-bottom:1px solid #eee}}
    .row-top{{background:#f0f9ff;font-weight:700}}
    </style></head><body>
    <div style="max-width:1000px;margin:0 auto">
    <div class="header"><h1>{track_name}</h1><div>{track_date} • {track_cond}</div></div>
    <div style="margin-bottom:20px"><b>JUMP TO:</b> {nav_links}</div>"""

    for r in races:
        r_num = r.get('number', '?')
        top = r.get('picks', {}).get('top_pick', {})
        dang = r.get('picks', {}).get('danger_horse', {})
        val = r.get('picks', {}).get('value_bet', {})
        
        html += f"""<div id="race-{r_num}" class="race-section">
        <div class="race-header"><div>RACE {r_num} - {r.get('distance','')}</div><div>{r.get('confidence_level','')}</div></div>
        <div class="picks-grid">
            <div class="pick-box"><b>⭐ BEST: #{top.get('number','')} {top.get('name','')}</b><br><small>{top.get('reason','')}</small></div>
            <div class="pick-box danger"><b>⚠️ DANGER: #{dang.get('number','')} {dang.get('name','')}</b><br><small>{dang.get('reason','')}</small></div>
            <div class="pick-box value"><b>💰 VALUE: #{val.get('number','')} {val.get('name','')}</b><br><small>{val.get('reason','')}</small></div>
        </div>
        <div style="padding:15px"><table><thead><tr><th>#</th><th>Horse</th><th>Rating</th><th>Verdict</th></tr></thead><tbody>"""
        
        for c in r.get('contenders', [])[:6]:
            style = ' class="row-top"' if str(c.get('number')) == str(top.get('number')) else ''
            html += f"<tr{style}><td>{c.get('number')}</td><td>{c.get('name')}</td><td>{c.get('rating')}</td><td>{c.get('verdict')}</td></tr>"
            
        html += f"""</tbody></table><div style="margin-top:10px;padding:10px;background:#f8fafc"><b>STRATEGY:</b> {r.get('exotic_strategy',{}).get('exacta','')}</div></div></div>"""
    
    html += "</div></body></html>"
    return html

# --- 5. EXECUTION ---
if uploaded_file and api_key and st.button("Analyze Meeting"):
    with st.spinner(f"Analying with {target_model}..."):
        try:
            # 1. READ PDF
            reader = PyPDF2.PdfReader(uploaded_file)
            pdf_text = "".join([page.extract_text() for page in reader.pages])
            st.session_state.raw_pdf_text = pdf_text

            # 2. LOAD LOGIC
            logic_path = os.path.join(LOGIC_DIR, system_file)
            if not os.path.exists(logic_path): logic_content = "Focus on Speed and Class."
            else: 
                with open(logic_path, 'r', encoding='utf-8') as f: logic_content = f.read()

            track_facts = json.dumps(selected_track_data) if selected_track_data else "No specific track data."

            # 3. AI GENERATION
            genai.configure(api_key=api_key)
            
            # --- USE SELECTED MODEL ---
            model = genai.GenerativeModel(target_model, generation_config={"response_mime_type": "application/json"})
            
            prompt = f"""
            ROLE: Expert Handicapper ({region_code}).
            TASK: Analyze this race card text and extract structured betting data.
            
            [TRACK DATABASE]
            {track_facts}
            
            [SYSTEM RULES]
            {logic_content}
            
            [USER UPDATES]
            {scratches}
            
            [RACE CARD TEXT]
            {pdf_text[:100000]} 
            
            OUTPUT INSTRUCTION:
            - Return JSON ONLY.
            - MUST extract EVERY RACE found in the text.
            - DO NOT return empty templates.
            - For 'meta', extract track name, date, and surface conditions from text.
            """
            
            response = model.generate_content(prompt)
            raw_json = response.text
            st.session_state.raw_ai_json = raw_json

            # 4. PARSE & SANITIZE
            data = json.loads(raw_json)
            
            # Handle List Wrapper
            if isinstance(data, list): data = data[0] if data else {}
            
            # Ensure Structure
            if "meta" not in data: data["meta"] = {}
            if "races" not in data: data["races"] = []
            
            # Defaults
            if not data["meta"].get("track"): data["meta"]["track"] = selected_track_name
            if not data["meta"].get("date"): data["meta"]["date"] = datetime.today().strftime('%Y-%m-%d')
            if not data["meta"].get("track_condition"): data["meta"]["track_condition"] = "Standard"
            
            # 5. SAVE
            filename = f"{selected_track_name.replace(' ','_')}_{data['meta']['date']}.html"
            save_path = os.path.join(MEETINGS_DIR, filename)
            
            with open(save_path, "w", encoding='utf-8') as f:
                f.write(generate_meeting_html(data, region_code))
                
            st.session_state.results = save_path

        except Exception as e:
            st.error(f"Error: {str(e)}")

# --- 6. DISPLAY RESULTS (PERSISTENT) ---
if st.session_state.results:
    st.success("✅ Analysis Complete!")
    st.markdown(f"### [📂 Open Handicapping Report](file:///{st.session_state.results})")
    
    st.markdown("---")
    st.subheader("🔍 Debug Console")
    tab1, tab2 = st.tabs(["📄 Extracted PDF Text", "🤖 Raw AI JSON"])
    
    with tab1:
        st.caption("Check this to ensure the PDF was read correctly.")
        st.text_area("PDF Content", st.session_state.raw_pdf_text, height=300)
    
    with tab2:
        st.caption("This is what the AI returned.")
        st.code(st.session_state.raw_ai_json, language='json')