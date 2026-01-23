import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="World Handicapper Pro", layout="wide")

# --- CONFIG & SETUP ---
# Use absolute paths to avoid file not found errors
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEETINGS_DIR = os.path.join(DOCS_DIR, "meetings")
LOGIC_FILE = os.path.join(BASE_DIR, "logic", "master_system.md")

# Ensure directories exist
os.makedirs(MEETINGS_DIR, exist_ok=True)

if 'track_data' not in st.session_state:
    st.session_state.track_data = {}

# --- SIDEBAR ---
st.sidebar.title("🏇 World Handicapper")

# --- API KEY LOADING (Safe Mode) ---
api_key = None
try:
    # Try to load from secrets file
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    pass # File doesn't exist, ignore and fall back to manual input
except Exception:
    pass # Any other error, ignore

# If no key found in secrets, ask user
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)

st.sidebar.markdown("---")
st.sidebar.header("📂 Dashboard")
tracks = list(st.session_state.track_data.keys())
selected_track = st.sidebar.selectbox("Select Meeting:", tracks) if tracks else None

# --- WEBSITE GENERATOR FUNCTIONS ---

def generate_meeting_html(data):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{data['meta']['track']} - Pro Form</title>
        <style>
            /* BASE STYLES */
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 12px; color: #000; margin: 0; padding: 30px; background: #fff; }}
            .container {{ max_width: 1000px; margin: 0 auto; }}
            a {{ text-decoration: none; color: #000; }}
            
            /* HEADER (Logo Left) */
            .header {{ display: flex; align-items: center; border-bottom: 3px solid #000; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ max-height: 90px; margin-right: 30px; display: block; }}
            .header-info h1 {{ margin: 0; font-size: 28px; text-transform: uppercase; letter-spacing: 1px; line-height: 1; }}
            .meta {{ font-size: 14px; color: #333; margin-top: 8px; font-weight: 500; }}
            
            /* RACE SECTION Container */
            .race-section {{ margin-bottom: 40px; break-inside: avoid; border: 1px solid #ccc; background: #fff; }}
            
            /* RACE HEADER (Black Bar) */
            .race-header {{ background: #000; color: #fff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .race-title {{ font-weight: 700; font-size: 18px; }}
            .race-conf {{ font-weight: 600; font-size: 13px; background: #fff; color: #000; padding: 4px 10px; border-radius: 2px; text-transform: uppercase; }}
            
            /* DETAILED PICKS PANELS */
            .picks-container {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; padding: 20px; background: #f9f9f9; border-bottom: 1px solid #ccc; }}
            .pick-panel {{ background: #fff; border: 1px solid #ddd; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            /* Strong top borders for B&W distinction */
            .panel-top {{ border-top: 4px solid #000; }}
            .panel-danger {{ border-top: 4px solid #555; }}
            .panel-value {{ border-top: 4px solid #999; }}
            
            .panel-label {{ font-weight: 900; font-size: 11px; text-transform: uppercase; margin-bottom: 10px; display: block; letter-spacing: 0.5px; }}
            .pick-main {{ font-size: 16px; font-weight: 700; margin-bottom: 5px; }}
            .pick-detail {{ font-size: 12px; color: #444; font-style: italic; line-height: 1.4; }}
            .rating-box {{ display: inline-block; background: #000; color: #fff; padding: 2px 6px; font-size: 11px; margin-left: 5px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            
            /* CONTENDERS TABLE */
            .table-container {{ padding: 0 20px 20px 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ text-align: left; background: #eee; border-bottom: 2px solid #000; padding: 8px 12px; font-size: 11px; text-transform: uppercase; font-weight: 700; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            td {{ padding: 8px 12px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }}
            tr:last-child td {{ border-bottom: none; }}
            
            /* Highlight Top Pick Row */
            .row-top-pick {{ background-color: #f0f0f0; font-weight: 700; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .row-top-pick td {{ border-bottom: 1px solid #ccc; }}
            
            /* STRATEGY FOOTER */
            .strategy-footer {{ background: #f4f4f4; border-top: 1px solid #ccc; padding: 15px 20px; font-size: 12px; }}
            .strat-row {{ margin-bottom: 8px; }}
            .strat-label {{ font-weight: 900; text-decoration: underline; margin-right: 8px; }}
            
            /* UTILS */
            .btn-print {{ position: fixed; top: 20px; right: 20px; background: #000; color: #fff; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 4px; cursor: pointer; border: none; font-size: 14px; z-index: 100; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .btn-print:hover {{ background: #333; }}
            
            /* PRINT MEDIA QUERY */
            @media print {{
                body {{ padding: 0; background: #fff; }}
                .container {{ max-width: 100%; }}
                .btn-print {{ display: none !important; }}
                .race-section {{ page-break-inside: avoid; border: 2px solid #000; margin-bottom: 30px; }}
                .race-header {{ background: #000 !important; color: #fff !important; }}
                .picks-container {{ background: #fff !important; border-bottom: 2px solid #000; }}
                .pick-panel {{ box-shadow: none; border: 1px solid #000; }}
                .row-top-pick {{ background-color: #eee !important; border: 1px solid #000; }}
                th {{ background: #ddd !important; border-bottom: 2px solid #000; }}
            }}
        </style>
    </head>
    <body>
        <button class="btn-print" onclick="window.print()">🖨️ PRINT FORM GUIDE</button>
    
        <div class="container">
            <div class="header">
                <img src="../logo.png" class="logo" alt="Logo">
                <div class="header-info">
                    <h1>{data['meta']['track']} Professional Form</h1>
                    <div class="meta">{data['meta']['date']} • {data['meta']['track_condition']} • Weather: {data['meta'].get('weather','N/A')}</div>
                </div>
            </div>
    """
    
    for race in data['races']:
        # Safe Getters
        picks = race.get('picks', {})
        top = picks.get('top_pick', {})
        danger = picks.get('danger_horse', {})
        value = picks.get('value_bet', {})
        strat = race.get('exotic_strategy', {})
        
        html += f"""
        <div class="race-section">
            <div class="race-header">
                <div class="race-title">RACE {race['number']} - {race.get('distance','')}</div>
                <div class="race-conf">{race.get('confidence_level', 'Standard Conf')}</div>
            </div>
            
            <div class="picks-container">
                <div class="pick-panel panel-top">
                    <span class="panel-label">⭐ BEST BET / TOP PICK</span>
                    <div class="pick-main">
                        #{top.get('number','')} {top.get('name','N/A')} 
                        <span class="rating-box">{top.get('rating','-')}</span>
                    </div>
                    <div class="pick-detail">{top.get('reason','')}</div>
                </div>
                
                <div class="pick-panel panel-danger">
                    <span class="panel-label">⚠️ THE DANGER</span>
                    <div class="pick-main">
                        #{danger.get('number','')} {danger.get('name','N/A')}
                        <span class="rating-box" style="background:#555">{danger.get('rating','-')}</span>
                    </div>
                    <div class="pick-detail">{danger.get('reason','')}</div>
                </div>
                
                <div class="pick-panel panel-value">
                    <span class="panel-label">💰 VALUE PLAY</span>
                    <div class="pick-main">
                        #{value.get('number','')} {value.get('name','N/A')}
                    </div>
                    <div class="pick-detail">Odds: {value.get('odds','-')} <br> {value.get('reason','')}</div>
                </div>
            </div>
            
            <div class="table-container">
                <table>
                    <thead><tr><th>#</th><th>Horse</th><th>Rating</th><th>Barrier</th><th>Verdict</th></tr></thead>
                    <tbody>
        """
        
        for c in race.get('contenders', [])[:6]: # Show top 6 in table
            is_top = str(c.get('number')) == str(top.get('number'))
            row_class = "row-top-pick" if is_top else ""
            
            # Verdict handling
            verdict = c.get('verdict', "")
            v_text = verdict[0] if isinstance(verdict, list) and verdict else str(verdict)
            if not v_text: v_text = "-"
            
            html += f"""
            <tr class="{row_class}">
                <td style="font-weight:bold">{c.get('number','')}</td>
                <td>{c.get('name','')}</td>
                <td><span style="font-weight:700">{c.get('rating','')}</span></td>
                <td>{c.get('barrier','')}</td>
                <td>{v_text}</td>
            </tr>
            """
            
        html += f"""
                    </tbody>
                </table>
            </div>
            
            <div class="strategy-footer">
                <div class="strat-row"><span class="strat-label">EXACTA STAKE:</span> {strat.get('exacta','-')}</div>
                <div class="strat-row"><span class="strat-label">TRIFECTA STAKE:</span> {strat.get('trifecta','-')}</div>
                <div style="margin-top:8px; font-style:italic;">Note: {strat.get('rationale','')}</div>
            </div>
        </div>
        """
        
    html += "</div></body></html>"
    return html

def update_homepage():
    """Scans the meetings folder and rebuilds index.html"""
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>World Handicapper HQ</title>
        <style>
            body { font-family: sans-serif; background: #0f172a; color: white; padding: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { text-align: center; color: #f1c40f; text-transform: uppercase; letter-spacing: 2px; }
            .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 40px; }
            .card { background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; transition: transform 0.2s; }
            .card:hover { transform: translateY(-5px); border-color: #f1c40f; }
            .card h3 { margin: 0 0 10px 0; }
            .btn { display: inline-block; background: #f1c40f; color: #0f172a; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>World Handicapper Pro</h1>
            <p style="text-align:center; color:#94a3b8;">Latest Professional Analysis</p>
            <div class="card-grid">
    """
    for f in files:
        name = f.replace(".html", "").replace("_", " ").title()
        html += f"""
            <div class="card">
                <h3>{name}</h3>
                <span style="color:#64748b; font-size:0.9em;">Analysis Complete</span><br>
                <a href="meetings/{f}" class="btn">View Analysis</a>
            </div>
        """

    html += """
            </div>
        </div>
    </body>
    </html>
    """

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding='utf-8') as f:
        f.write(html)

# --- MAIN APP LOGIC ---
st.title("🏆 World Handicapper Pro")

with st.expander("📥 Import Race Card", expanded=not selected_track):
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    context = st.text_area("Context / Scratches", height=60)
    
    if st.button("Analyze Meeting"):
        if uploaded_file and api_key:
            with st.spinner("Analyzing..."):
                try:
                    # PDF Load
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = "".join([page.extract_text() for page in reader.pages])
                    
                    # Logic Load - Using Absolute Path
                    if not os.path.exists(LOGIC_FILE):
                        st.error(f"Logic file not found at: {LOGIC_FILE}")
                        st.stop()
                        
                    with open(LOGIC_FILE, "r", encoding="utf-8") as f:
                        system = f.read()
                    
                    # AI Call
                    model = genai.GenerativeModel('gemini-3-pro-preview')
                    prompt = f"{system}\\n\\nUPDATES: {context}\\n\\nDATA:\\n{text}"
                    response = model.generate_content(prompt)
                    
                    # Parse
                    clean_json = response.text.replace("```json","").replace("```","").strip()
                    data = json.loads(clean_json)
                    
                    # Save to Session
                    track_name = data['meta']['track']
                    st.session_state.track_data[track_name] = data
                    st.success(f"Analyzed {track_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- VIEW & PUBLISH ---
if selected_track:
    data = st.session_state.track_data[selected_track]

    # PUBLISH BUTTON
    if st.sidebar.button("🚀 Publish to Website"):
        try:
            # 1. Save Meeting HTML
            filename = f"{selected_track}_{data['meta']['date']}".replace(" ", "_").replace("/", "-") + ".html"
            html_content = generate_meeting_html(data)
            
            with open(os.path.join(MEETINGS_DIR, filename), "w", encoding='utf-8') as f:
                f.write(html_content)
                
            # 2. Update Homepage
            update_homepage()
            st.sidebar.success(f"Published to {filename}")
        except Exception as e:
            st.sidebar.error(f"Publishing failed: {e}")

    # DASHBOARD DISPLAY
    st.header(f"📍 {selected_track}")

    tabs = st.tabs([f"R{r['number']}" for r in data['races']])
    for i, race in enumerate(data['races']):
        with tabs[i]:
            # Display Logic with Error Handling
            c1, c2, c3 = st.columns(3)
            picks = race.get('picks', {})

            with c1:
                st.success(f"🏆 #{picks.get('top_pick', {}).get('number', '?')} {picks.get('top_pick', {}).get('name', 'N/A')}")
                st.caption(picks.get('top_pick', {}).get('reason', ''))
            with c2:
                st.warning(f"⚠️ #{picks.get('danger_horse', {}).get('number', '?')} {picks.get('danger_horse', {}).get('name', 'N/A')}")
                st.caption(picks.get('danger_horse', {}).get('reason', ''))
            with c3:
                st.info(f"💰 #{picks.get('value_bet', {}).get('number', '?')} {picks.get('value_bet', {}).get('name', 'N/A')}")
                st.caption(f"Odds: {picks.get('value_bet', {}).get('odds', '-')}")
            
            st.divider()
            
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                st.subheader("Field Analysis")
                # Safe DataFrame Creation
                contenders = race.get('contenders', [])
                if contenders:
                    df = pd.DataFrame(contenders)
                    display_df = pd.DataFrame()
                    display_df['#'] = df.get('number', '')
                    display_df['Horse'] = df.get('name', '')
                    display_df['Rating'] = df.get('rating', '')
                    
                    # THE BUG FIX: Check if verdict exists
                    if 'verdict' in df.columns:
                        display_df['Verdict'] = df['verdict'].apply(lambda x: x[0] if isinstance(x, list) and x else str(x) if x else "")
                    else:
                        display_df['Verdict'] = ""
                        
                    st.table(display_df.set_index('#'))
                else:
                    st.info("No detailed contender data for this race.")
                
            with sc2:
                st.subheader("🎯 Exotic Strategy")
                strat = race.get('exotic_strategy', {})
                st.markdown(f"**Exacta:** {strat.get('exacta', '-')}")
                st.markdown(f"**Trifecta:** {strat.get('trifecta', '-')}")
                st.caption(strat.get('rationale', ''))
