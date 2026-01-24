import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px

# --- CONFIG ---
st.set_page_config(page_title="Exacta AI Optimizer", page_icon="📈", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# --- HELPER FUNCTIONS ---
def load_log(filename):
    with open(os.path.join(LOGS_DIR, filename), 'r') as f:
        return json.load(f)

def save_log(filename, data):
    with open(os.path.join(LOGS_DIR, filename), 'w') as f:
        json.dump(data, f, indent=4)

def calculate_stats():
    """Scans all logs to build a performance dataset."""
    files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
    records = []
    
    for f in files:
        try:
            data = load_log(f)
            track = data.get("meta", {}).get("track", "Unknown")
            date = data.get("meta", {}).get("date", "Unknown")
            
            for race in data.get("races", []):
                # Check if results have been entered
                result = race.get("actual_result", {})
                if result.get("winner_number"):
                    top_pick = race.get("picks", {}).get("top_pick", {})
                    top_num = str(top_pick.get("number", "X"))
                    
                    winner_num = str(result.get("winner_number"))
                    odds = float(result.get("winner_odds", 0))
                    
                    is_win = (top_num == winner_num)
                    profit = (odds - 1) if is_win else -1
                    
                    records.append({
                        "Track": track,
                        "Date": date,
                        "Race": race["number"],
                        "Top Pick": top_num,
                        "Winner": winner_num,
                        "Won": is_win,
                        "Odds": odds,
                        "Profit": profit
                    })
        except: pass
        
    return pd.DataFrame(records)

# --- SIDEBAR: FILE SELECTION ---
st.sidebar.header("📁 Race Logs")
log_files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
log_files.sort(reverse=True)

if not log_files:
    st.error("No logs found! Run the main app to generate data.")
    st.stop()

selected_file = st.sidebar.selectbox("Select Meeting to Grade", log_files)
current_data = load_log(selected_file)

# --- MAIN DASHBOARD ---
st.title("📈 System Optimizer")

# TABS
tab1, tab2 = st.tabs(["📝 Grade Results", "📊 Performance Stats"])

# --- TAB 1: DATA ENTRY ---
with tab1:
    st.subheader(f"Grading: {current_data['meta'].get('track')} ({current_data['meta'].get('date')})")
    
    with st.form("grading_form"):
        races = current_data.get("races", [])
        
        for i, race in enumerate(races):
            r_num = race.get("number")
            top_pick = race.get("picks", {}).get("top_pick", {})
            
            # Existing result data?
            existing_res = race.get("actual_result", {})
            ex_winner = existing_res.get("winner_number", "")
            ex_odds = existing_res.get("winner_odds", 0.0)
            
            c1, c2, c3, c4 = st.columns([1, 3, 2, 2])
            with c1:
                st.markdown(f"**R{r_num}**")
            with c2:
                st.info(f"Top Pick: #{top_pick.get('number')} {top_pick.get('name')}")
            with c3:
                # User inputs Winner
                new_winner = st.text_input(f"Winner #", value=ex_winner, key=f"w_{i}", placeholder="e.g. 4")
            with c4:
                # User inputs Odds
                new_odds = st.number_input(f"Pay ($)", value=float(ex_odds), key=f"o_{i}", step=0.1)
                
            # Update data in memory
            if "actual_result" not in race: race["actual_result"] = {}
            race["actual_result"]["winner_number"] = new_winner
            race["actual_result"]["winner_odds"] = new_odds
            
        submit = st.form_submit_button("💾 Save Results")
        
        if submit:
            save_log(selected_file, current_data)
            st.success("Results Saved! Check the Stats tab.")

# --- TAB 2: ANALYTICS ---
with tab2:
    df = calculate_stats()
    
    if df.empty:
        st.info("No graded races yet. Go to 'Grade Results' and enter some winners!")
    else:
        # KPI ROW
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        total_races = len(df)
        total_wins = df[df["Won"] == True].shape[0]
        strike_rate = (total_wins / total_races) * 100
        net_profit = df["Profit"].sum()
        roi = (net_profit / total_races) * 100
        
        kpi1.metric("Races Graded", total_races)
        kpi2.metric("Strike Rate", f"{strike_rate:.1f}%")
        kpi3.metric("Net Profit (Units)", f"{net_profit:.2f}")
        kpi4.metric("ROI", f"{roi:.1f}%")
        
        st.markdown("---")
        
        # CHARTS
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Performance by Track")
            track_stats = df.groupby("Track")["Profit"].sum().reset_index()
            fig = px.bar(track_stats, x="Track", y="Profit", color="Profit", 
                         color_continuous_scale=["red", "green"])
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.subheader("Win Rate by Track")
            win_stats = df.groupby("Track")["Won"].mean().reset_index()
            fig2 = px.bar(win_stats, x="Track", y="Won", title="Strike Rate")
            st.plotly_chart(fig2, use_container_width=True)
            
        # RAW DATA
        st.subheader("Detailed Ledger")
        st.dataframe(df)