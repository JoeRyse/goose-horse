#!/usr/bin/env python3
"""
🎯 Standalone Mock Betting & Handicapper Training Device
Completely isolated application for personal handicapping practice and virtual bankroll tracking.
Launch: python -m streamlit run training_device/app.py --server.port 8502
"""

import os
import json
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

from training_db import (
    init_db, get_bankroll, reset_bankroll, place_manual_bet, get_bets, settle_pending_bets
)
from live_odds_fetcher import fetch_live_tab_meetings, get_equibase_chart_url

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MASTER_DB_PATH = os.path.join(PROJECT_ROOT, "logs", "master_betting_history.db")

# Page Configuration
st.set_page_config(
    page_title="🎯 Standalone Handicapper Training Device",
    page_icon="🏇",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        color: #f8fafc;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .metric-card h3 { margin: 0; font-size: 0.95rem; color: #94a3b8; }
    .metric-card p { margin: 4px 0 0 0; font-size: 1.6rem; font-weight: 700; color: #38bdf8; }
    .positive-val { color: #4ade80 !important; }
    .negative-val { color: #f87171 !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Initialize Standalone Database
init_db()
bankroll = get_bankroll()

# Header Title & Real-Time Status Indicator
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("🎯 Standalone Handicapper Training Device")
    st.caption("Personal Virtual Bankroll & Manual Betting Simulator (100% Isolated from Main App)")
with col_status:
    st.markdown("""
    <div style="background:#064e3b; border:1px solid #059669; padding:8px 12px; border-radius:8px; text-align:center; margin-top:10px;">
        <span style="color:#34d399; font-weight:bold;">🟢 FREE LIVE FEEDS CONNECTED</span><br>
        <small style="color:#a7f3d0;">TAB AU & Equibase $0.00</small>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ==========================================
# 📊 TOP METRICS BAR
# ==========================================
c1, c2, c3, c4, c5 = st.columns(5)

settled_bets = get_bets(status_filter="WON") + get_bets(status_filter="LOST")
total_settled_count = len(settled_bets)
win_count = len(get_bets(status_filter="WON"))
win_pct = (win_count / total_settled_count * 100) if total_settled_count > 0 else 0.0
roi_pct = (bankroll["net_pnl"] / bankroll["total_staked"] * 100) if bankroll["total_staked"] > 0 else 0.0

with c1:
    st.markdown(f'<div class="metric-card"><h3>Available Bankroll</h3><p>${bankroll["current_balance"]:.2f}</p></div>', unsafe_allow_html=True)
with c2:
    pnl_class = "positive-val" if bankroll["net_pnl"] >= 0 else "negative-val"
    st.markdown(f'<div class="metric-card"><h3>Net P&L</h3><p class="{pnl_class}">${bankroll["net_pnl"]:+.2f}</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><h3>Win Rate</h3><p>{win_pct:.1f}%</p></div>', unsafe_allow_html=True)
with c4:
    roi_class = "positive-val" if roi_pct >= 0 else "negative-val"
    st.markdown(f'<div class="metric-card"><h3>ROI</h3><p class="{roi_class}">{roi_pct:+.1f}%</p></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="metric-card"><h3>Total Staked</h3><p>${bankroll["total_staked"]:.2f}</p></div>', unsafe_allow_html=True)

st.space()

# ==========================================
# MAIN APP BODY: 3 TABS
# ==========================================
tab_betting, tab_ledger, tab_upload = st.tabs(["🎟️ Manual Bet Slip & Race Card", "📊 Bankroll Ledger & Analytics", "📄 Upload Chart & Ingest Results"])

def get_user_ran_tracks():
    if not os.path.exists(MASTER_DB_PATH):
        return ["Saratoga", "Del Mar", "Goodwood", "Scone"]
    conn = sqlite3.connect(MASTER_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT track FROM predictions WHERE track IS NOT NULL AND track != '' ORDER BY track ASC")
    rows = c.fetchall()
    conn.close()
    
    raw_tracks = sorted(list(set([r[0].replace("_", " ").title() for r in rows if r[0]])))
    
    # Focus / Prioritize Saratoga & Del Mar at top of dropdown
    priority = ["Saratoga", "Del Mar"]
    ordered_tracks = [t for t in priority if t in raw_tracks] + [t for t in raw_tracks if t not in priority]
    
    return ordered_tracks if ordered_tracks else ["Saratoga", "Del Mar", "Goodwood", "Scone"]

def get_dates_for_track(track_name):
    if not os.path.exists(MASTER_DB_PATH):
        return [datetime(2026, 7, 30).date()]
    conn = sqlite3.connect(MASTER_DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT date FROM predictions 
        WHERE (track LIKE ? OR track LIKE ?) AND date IS NOT NULL AND date != ''
        ORDER BY date DESC
    """, (f"%{track_name}%", f"%{track_name.replace(' ', '_')}%"))
    rows = c.fetchall()
    conn.close()
    
    dates = []
    for r in rows:
        try:
            dates.append(datetime.strptime(r[0], "%Y-%m-%d").date())
        except:
            pass
    return dates if dates else [datetime(2026, 7, 30).date()]

with tab_betting:
    st.subheader("🏇 Race Card Selection & Manual Wager Slip")
    
    # Track Card Source Selection
    col_card, col_race = st.columns([2, 1])
    
    with col_card:
        user_tracks = get_user_ran_tracks()
        selected_track = st.selectbox("Select Racetrack (Only Cards You Ran)", user_tracks)
        
        available_dates = get_dates_for_track(selected_track)
        selected_date = st.selectbox("Select Available Date", available_dates)
        date_str = selected_date.strftime("%Y-%m-%d")
        
    with col_race:
        selected_race_num = st.selectbox("Select Race #", [f"Race {i}" for i in range(1, 12)], index=0)
        race_num_digit = selected_race_num.replace("Race ", "")

    # Query Race Details from SQLite Master DB
    races_data = []
    if os.path.exists(MASTER_DB_PATH):
        conn = sqlite3.connect(MASTER_DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT p1_num, p1_name, p1_rating, p1_barrier,
                   p2_num, p2_name, p2_rating, p2_barrier,
                   p3_num, p3_name, p3_rating, p3_barrier,
                   p4_num, p4_name, p4_rating, p4_barrier,
                   distance, surface, rating_gap, has_solo_lock, has_best_bet
            FROM predictions
            WHERE (track LIKE ? OR track LIKE ?) AND date=? AND race_number=?
        """, (f"%{selected_track}%", f"%{selected_track.replace(' ', '_')}%", date_str, race_num_digit))
        row = c.fetchone()
        # Query results table for official win payout if completed
        c.execute("""
            SELECT win_num, win_payout 
            FROM results 
            WHERE (track LIKE ? OR track LIKE ?) AND date=? AND race_number=?
        """, (f"%{selected_track}%", f"%{selected_track.replace(' ', '_')}%", date_str, race_num_digit))
        res_row = c.fetchone()
        official_win_num = str(res_row[0]).strip() if res_row and res_row[0] else ""
        official_win_payout = float(res_row[1]) if res_row and res_row[1] and float(res_row[1]) > 0 else None
        
        conn.close()
        
        def calc_odds_str(num, rating):
            if official_win_num and str(num).strip() == official_win_num and official_win_payout:
                return f"${official_win_payout:.2f} (WINNER)"
            try:
                r_val = float(rating)
                if r_val >= 100:
                    return "$2.80 (9/5)"
                elif r_val >= 95:
                    return "$4.50 (7/2)"
                elif r_val >= 90:
                    return "$8.00 (7/1)"
                else:
                    return "$14.00 (13/1)"
            except:
                return "$5.00 (4/1)"

        if row:
            contenders = [
                {"num": str(row[0]), "name": row[1], "rating": row[2], "barrier": row[3], "odds": calc_odds_str(row[0], row[2])},
                {"num": str(row[4]), "name": row[5], "rating": row[6], "barrier": row[7], "odds": calc_odds_str(row[4], row[6])},
                {"num": str(row[8]), "name": row[9], "rating": row[10], "barrier": row[11], "odds": calc_odds_str(row[8], row[10])},
                {"num": str(row[12]), "name": row[13], "rating": row[14], "barrier": row[15], "odds": calc_odds_str(row[12], row[14])}
            ]
            races_data = contenders
            dist_surf = f"{row[16]} {row[17]}"
            gap = row[18]
        else:
            dist_surf = "Standard Surface"
            gap = 0.0

    st.markdown(f"**Race Details**: {selected_track} - {selected_race_num} ({dist_surf})")
    
    # Display Race Runners Table & Manual Bet Slip Side-by-Side
    col_runners, col_slip = st.columns([3, 2])
    
    with col_runners:
        st.markdown("#### 🐎 Contenders & Live/Est. Odds")
        if races_data:
            df_runners = pd.DataFrame(races_data)
            df_runners.columns = ["# Number", "Horse Name", "AI Rating", "Barrier", "Odds ($)"]
            st.dataframe(df_runners, use_container_width=True)
        else:
            st.info(f"No specific runner data logged for {selected_track} on {date_str} {selected_race_num}. You can still enter custom horse numbers below.")
            
        chart_url = get_equibase_chart_url(selected_track, date_str)
        st.markdown(f"🔗 [View Official Equibase Chart Reference]({chart_url})")

    with col_slip:
        st.markdown("#### 🎟️ Manual Bet Slip")
        
        with st.form("manual_bet_form"):
            bet_type = st.selectbox("Select Bet Type", ["WIN", "PLACE", "EXACTA BOX", "TRIFECTA BOX"])
            
            if races_data:
                runner_options = [f"#{r['num']} - {r['name']} ({r['odds']})" for r in races_data]
                selected_runner_str = st.selectbox("Select Primary Horse", runner_options)
                selected_num = selected_runner_str.split(" - ")[0].replace("#", "")
                selected_name = selected_runner_str.split(" - ")[1].split(" (")[0]
            else:
                selected_num = st.text_input("Horse Program #", "1")
                selected_name = st.text_input("Horse Name", "Runner 1")
                
            odds_input = st.number_input("Odds / Tote Dividend ($)", min_value=1.01, max_value=500.0, value=4.50, step=0.50, help="Decimal odds or $2 Tote payout")
            stake_amount = st.number_input("Stake Amount ($)", min_value=1.0, max_value=1000.0, value=10.0, step=5.0)
            
            c_btn1, c_btn2, c_btn3 = st.columns(3)
            with c_btn1:
                stake_5 = st.form_submit_button("Bet $5")
            with c_btn2:
                stake_10 = st.form_submit_button("Bet $10")
            with c_btn3:
                stake_20 = st.form_submit_button("Bet $20")
                
            submit_bet = st.form_submit_button("🎟️ Confirm & Place Manual Bet", type="primary")
            
            if submit_bet or stake_5 or stake_10 or stake_20:
                final_stake = 5.0 if stake_5 else (10.0 if stake_10 else (20.0 if stake_20 else stake_amount))
                success, msg = place_manual_bet(
                    date_str, selected_track, race_num_digit, bet_type, selected_num, selected_name, final_stake, odds_input
                )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()
    
    # Pending Bets & Settle Engine Section
    st.subheader("⏳ Open Manual Bets & Settle Engine")
    
    col_p_bets, col_settle = st.columns([3, 1])
    
    with col_p_bets:
        pending_bets = get_bets(status_filter="PENDING")
        if pending_bets:
            df_pending = pd.DataFrame(pending_bets)
            st.dataframe(df_pending[["bet_id", "date", "track", "race_number", "bet_type", "runner_nums", "runner_names", "stake", "status"]], use_container_width=True)
        else:
            st.info("No open pending bets. Place a manual wager above!")
            
    with col_settle:
        st.markdown("#### ⚡ Settle Open Wagers")
        st.caption("Auto-settles bets against official race results in the master database.")
        if st.button("⚡ Settle Open Bets Now", type="primary"):
            count, msg = settle_pending_bets()
            if count > 0:
                st.success(msg)
                st.rerun()
            else:
                st.info(msg)

with tab_ledger:
    st.subheader("📊 Performance Ledger & Equity Analytics")
    
    col_hist, col_reset = st.columns([3, 1])
    
    with col_hist:
        all_bets = get_bets()
        if all_bets:
            df_all = pd.DataFrame(all_bets)
            st.dataframe(df_all[["bet_id", "date", "track", "race_number", "bet_type", "runner_names", "stake", "status", "payout", "net_pnl"]], use_container_width=True)
            
            # Cumulative PnL Line Chart
            df_settled = df_all[df_all["status"].isin(["WON", "LOST"])].copy()
            if not df_settled.empty:
                df_settled["cum_pnl"] = df_settled["net_pnl"].cumsum()
                st.line_chart(df_settled["cum_pnl"], height=250)
        else:
            st.info("No bet history recorded yet.")
            
    with col_reset:
        st.markdown("#### 🔄 Reset Bankroll")
        st.caption("Resets virtual bankroll and clears all manual wager logs.")
        reset_val = st.number_input("Reset Amount ($)", value=1000.0, step=100.0)
        if st.button("⚠️ Reset Virtual Bankroll"):
            reset_bankroll(reset_val)
            st.success(f"Bankroll reset to ${reset_val:.2f}")
            st.rerun()

with tab_upload:
    st.subheader("📄 Upload & Ingest Official Equibase / PDF Charts")
    st.caption("Paste OCR/Text or Upload PDF Chart summaries (focused on Saratoga & Del Mar) to auto-populate results and payouts into master_betting_history.db")
    
    from agents.chart_ingestor_agent import parse_equibase_chart_text, ingest_chart_to_db

    col_u1, col_u2 = st.columns([2, 1])
    
    with col_u1:
        chart_text_input = st.text_area("📋 Paste Equibase Chart / OCR Text Here", height=250, placeholder="Paste Equibase chart text here (e.g. SARATOGA - July 31, 2026 - Race 1...)")
        
        c_up_track, c_up_date = st.columns(2)
        with c_up_track:
            target_track_sel = st.selectbox("Track Override", ["Saratoga", "Del Mar"], index=0)
        with c_up_date:
            target_date_sel = st.date_input("Date Override", datetime(2026, 7, 31), key="tab_upload_date")
            target_date_str = target_date_sel.strftime("%Y-%m-%d")
            
        if st.button("🚀 Parse & Ingest Chart into Database", type="primary"):
            if chart_text_input.strip():
                parsed = parse_equibase_chart_text(chart_text_input, default_track=target_track_sel, default_date=target_date_str)
                ingest_chart_to_db(parsed)
                st.success(f"✅ Ingested {parsed['track']} Race {parsed['race_number']} ({parsed['date']}) into Database!")
                st.json(parsed)
            else:
                st.warning("Please paste chart text above before clicking Ingest.")

    with col_u2:
        st.markdown("#### 💡 How to Ingest Results")
        st.markdown("""
        1. **Option A (In-App Tab)**: Paste Equibase PDF chart summary text into the box on the left and click **Parse & Ingest**.
        2. **Option B (Paste in Chat)**: Paste PDF chart screenshots or text directly to the AI in our chat, and it will auto-populate the database for you.
        3. **Focus Tracks**: **Saratoga** and **Del Mar** are highlighted at the top of all track selection lists.
        4. **Auto-Settlement**: As soon as charts are ingested, your open manual bets in the **Manual Bet Slip** tab will auto-settle against official payouts!
        """)
