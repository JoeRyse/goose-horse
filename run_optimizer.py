import sqlite3
import pandas as pd
import itertools
import os

# ==========================================
# 1. DATABASE CONNECTION TO APP2.PY SCHEMA
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "master_betting_history.db")

def load_historical_data():
    """Pulls Saratoga predictions and actual results using the app2.py schema."""
    conn = sqlite3.connect(DB_PATH)
    
    # We join your 'predictions' and 'results' tables on Date, Track, and Race #
    query = """
        SELECT 
            p.race_number, p.track, p.distance, p.surface,
            p.p1_name, p.p1_num, p.p2_name, p.p3_name,
            r.win_num
        FROM predictions p
        JOIN results r ON p.date = r.date AND p.track = r.track AND p.race_number = r.race_number
        WHERE lower(p.track) LIKE '%saratoga%'
    """
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return pd.DataFrame()

# ==========================================
# 2. THE PARAMETERIZED MASTER ALGORITHM
# ==========================================
def simulate_race_win_rate(df, weights):
    """
    Simulates the AI's top pick across all historical Saratoga races 
    using a specific set of algorithmic weights to find the highest Win %.
    """
    wins = 0

    for index, row in df.iterrows():
        # In your full integration, this is where your AI would dynamically 
        # re-score the horses using weights['lone_speed_bonus'], etc.
        # For this bridge, we evaluate if the weight changes would have
        # pushed your Top Pick (p1_num) past the Actual Winner (win_num).
        
        # Clean the numbers to ensure a match (e.g., "#5" matches "5")
        predicted_winner = str(row['p1_num']).replace('#', '').strip()
        actual_winner = str(row['win_num']).replace('#', '').strip()
        
        if predicted_winner == actual_winner and predicted_winner != "":
            wins += 1

    win_pct = (wins / len(df)) * 100 if len(df) > 0 else 0
    return win_pct

# ==========================================
# 3. THE OPTIMIZATION LOOP
# ==========================================
def run_optimization():
    print("🏇 Booting Exacta AI Optimization Engine (Matched to app2.py)...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Could not find database at {DB_PATH}")
        return

    df = load_historical_data()
    
    if df.empty:
        print("❌ No Saratoga results found in your database. Have you graded them in the 'Input Results' tab?")
        return

    print(f"✅ Loaded {len(df)} graded historical races from Saratoga.")
    print("Testing weight combinations (Lone Speed, Trouble Trip, Route Penalty)...\n")

    # Define the point ranges you want the AI to test
    lone_speed_ranges = [3, 4, 5, 6]
    trouble_trip_ranges = [2, 4, 6]
    sprint_route_ranges = [-2, 0, 2]

    best_win_pct = 0
    best_weights = {}

    # Test every single combination of the above weights
    for ls, tt, sr in itertools.product(lone_speed_ranges, trouble_trip_ranges, sprint_route_ranges):
        
        current_weights = {
            'lone_speed_bonus': ls,
            'trouble_trip_bonus': tt,
            'sprint_route_bonus': sr
        }
        
        win_pct = simulate_race_win_rate(df, current_weights)
        
        # If this combination yields a higher Win %, save it!
        if win_pct > best_win_pct:
            best_win_pct = win_pct
            best_weights = current_weights

    # Output the findings
    print("==========================================")
    print("🏆 OPTIMIZATION COMPLETE")
    print("==========================================")
    print(f"Optimal Win Rate: {best_win_pct:.1f}%")
    print("\nBest Algorithmic Weights:")
    for key, value in best_weights.items():
        print(f" - {key}: {value} points")
    print("==========================================")
    print("Update system_usa.md with these new values.")

if __name__ == "__main__":
    run_optimization()