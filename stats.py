import streamlit as st
import sqlite3
import pandas as pd
import datetime

# --- CONFIG ---
st.set_page_config(page_title="Handicapping Stats", page_icon="📈", layout="wide")
DB_FILE = "racing_ledger.db"

# --- DB HELPERS ---
def get_connection():
    return sqlite3.connect(DB_FILE)

def load_data():
    conn = get_connection()
    query = """
    SELECT 
        r.race_uuid,
        r.track,
        r.date,
        r.race_number,
        r.betting_strategy,
        p.horse_number,
        p.rank_prediction,
        p.confidence_level,
        res.winner_number,
        res.second_number,
        res.third_number,
        res.win_payout
    FROM predictions p
    JOIN results res ON p.race_uuid = res.race_uuid
    JOIN races r ON p.race_uuid = r.race_uuid
    """
    try:
        df = pd.read_sql_query(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except:
        return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🔍 Filters")
df = load_data()

if df.empty:
    st.error("No graded races found in database. Please run 'enter_results.py' first.")
    st.stop()

# Track Filter
all_tracks = sorted(df['track'].unique())
selected_tracks = st.sidebar.multiselect("Select Tracks", all_tracks, default=all_tracks)

# Date Filter
min_date = df['date'].min().date()
max_date = df['date'].max().date()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date])

# APPLY FILTERS
mask = (df['track'].isin(selected_tracks)) & \
       (df['date'].dt.date >= date_range[0]) & \
       (df['date'].dt.date <= date_range[1])

filtered_df = df[mask].copy()

if filtered_df.empty:
    st.warning("No races match your filters.")
    st.stop()

# --- MAIN ANALYSIS LOGIC ---
st.title("📈 Performance Dashboard")

# 1. Process Data
def check_win(row):
    return str(row['horse_number']).strip() == str(row['winner_number']).strip()

def check_place(row):
    h = str(row['horse_number']).strip()
    return h in [str(row['winner_number']).strip(), 
                 str(row['second_number']).strip(), 
                 str(row['third_number']).strip()]

filtered_df['won'] = filtered_df.apply(check_win, axis=1)
filtered_df['placed'] = filtered_df.apply(check_place, axis=1)

# SUBSETS
top_picks = filtered_df[filtered_df['rank_prediction'] == 1]
danger_picks = filtered_df[filtered_df['rank_prediction'] == 99]

# Identify Prime Bets (High Confidence)
# Logic: Strategy contains 'High' OR confidence_level = 'Best of Day'
prime_mask = (filtered_df['rank_prediction'] == 1) & \
             ((filtered_df['betting_strategy'].str.contains('High', case=False, na=False)) | 
              (filtered_df['confidence_level'] == 'Best of Day'))
prime_picks = filtered_df[prime_mask]

# --- METRICS ROW 1 ---
st.subheader("🏆 Top Pick Performance")
c1, c2, c3, c4 = st.columns(4)

# Win Rate
win_pct = top_picks['won'].mean() * 100
c1.metric("Win Rate", f"{win_pct:.1f}%")

# Place Rate
place_pct = top_picks['placed'].mean() * 100
c2.metric("Place Rate (Top 3)", f"{place_pct:.1f}%")

# ROI Calculation ($2 Flat Bet)
cost = len(top_picks) * 2
returns = top_picks[top_picks['won']]['win_payout'].sum()
net = returns - cost
roi_pct = (net / cost) * 100 if cost > 0 else 0

c3.metric("Net Profit ($2 Bet)", f"${net:+.2f}", delta_color="normal")
c4.metric("ROI", f"{roi_pct:+.1f}%", delta_color="normal")

# --- METRICS ROW 2 (Prime & Danger) ---
st.markdown("---")
col_prime, col_danger = st.columns(2)

with col_prime:
    st.subheader("🔥 Prime Bets (High Conf.)")
    if not prime_picks.empty:
        p_win = prime_picks['won'].mean() * 100
        p_cost = len(prime_picks) * 2
        p_ret = prime_picks[prime_picks['won']]['win_payout'].sum()
        p_net = p_ret - p_cost
        p_roi = (p_net / p_cost) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Count", len(prime_picks))
        c2.metric("Win Rate", f"{p_win:.1f}%")
        c3.metric("ROI", f"{p_roi:+.1f}%")
    else:
        st.info("No Prime Bets in selection.")

with col_danger:
    st.subheader("⚠️ Danger Horses")
    if not danger_picks.empty:
        d_win = danger_picks['won'].mean() * 100
        d_cost = len(danger_picks) * 2
        d_ret = danger_picks[danger_picks['won']]['win_payout'].sum()
        d_net = d_ret - d_cost
        d_roi = (d_net / d_cost) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Count", len(danger_picks))
        c2.metric("Win Rate", f"{d_win:.1f}%")
        c3.metric("ROI", f"{d_roi:+.1f}%")
    else:
        st.info("No Danger Horses recorded.")

# --- TRACK BREAKDOWN TABLE ---
st.markdown("---")
st.subheader("📍 Track Breakdown (Top Picks)")

# Group by Track
track_stats = []
for track in selected_tracks:
    t_df = top_picks[top_picks['track'] == track]
    if t_df.empty: continue
    
    t_wins = t_df['won'].sum()
    t_count = len(t_df)
    t_cost = t_count * 2
    t_ret = t_df[t_df['won']]['win_payout'].sum()
    t_net = t_ret - t_cost
    t_roi = (t_net / t_cost) * 100 if t_cost > 0 else 0
    
    track_stats.append({
        "Track": track,
        "Races": t_count,
        "Wins": t_wins,
        "Win %": f"{(t_wins/t_count)*100:.1f}%",
        "Profit ($2)": t_net,
        "ROI": f"{t_roi:+.1f}%"
    })

if track_stats:
    stats_df = pd.DataFrame(track_stats).sort_values("Profit ($2)", ascending=False)
    # Formatting for display
    st.dataframe(
        stats_df.style.format({"Profit ($2)": "${:+.2f}"}),
        use_container_width=True,
        hide_index=True
    )

# --- RECENT RESULTS ---
st.markdown("---")
st.subheader("📝 Recent Graded Races")
recent_df = filtered_df[['date', 'track', 'race_number', 'horse_number', 'winner_number', 'win_payout', 'won']].copy()
recent_df = recent_df[filtered_df['rank_prediction'] == 1].sort_values(['date', 'track', 'race_number'], ascending=False)

def highlight_win(s):
    return ['background-color: #d4edda' if v else '' for v in s]

st.dataframe(
    recent_df,
    use_container_width=True,
    hide_index=True
)
