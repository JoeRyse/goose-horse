import sqlite3
import pandas as pd
import itertools
import os
import json

# ==========================================
# 1. PATHS & DATABASE SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(LOGS_DIR, "master_betting_history.db")
TRACKS_DIR = os.path.join(BASE_DIR, "tracks")

os.makedirs(DATA_DIR, exist_ok=True)

def get_track_profile(track_name):
    """Loads an individual track profile directly from the tracks folder."""
    filename = f"{track_name.lower().replace(' ', '_').replace('-', '_')}.json"
    filepath = os.path.join(TRACKS_DIR, filename)
    
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def get_all_tracks():
    conn = sqlite3.connect(DB_PATH)
    try:
        query = """
            SELECT DISTINCT p.track 
            FROM predictions p
            JOIN results r ON p.date = r.date AND p.track = r.track AND p.race_number = r.race_number
        """
        tracks_df = pd.read_sql_query(query, conn)
        conn.close()
        return tracks_df['track'].dropna().tolist()
    except Exception as e:
        print(f"Database Error: {e}")
        conn.close()
        return []

def load_track_data(track_name):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            p.race_number, p.track, p.distance, p.surface,
            p.p1_name, p.p1_num, p.p2_name, p.p3_name, p.p3_num,
            r.win_num
        FROM predictions p
        JOIN results r ON p.date = r.date AND p.track = r.track AND p.race_number = r.race_number
        WHERE lower(p.track) = lower(?)
    """
    try:
        df = pd.read_sql_query(query, conn, params=(track_name,))
        conn.close()
        return df
    except Exception as e:
        print(f"Database Error for {track_name}: {e}")
        return pd.DataFrame()

# ==========================================
# 2. PROFILE-AWARE DIVERSIFIED SIMULATION
# ==========================================
def simulate_track_win_rate(df, weights, track_profile, track_name):
    """
    Forces mathematical divergence so different track types 
    (bullrings vs sprawling courses) optimize toward opposite weights.
    """
    wins = 0
    bias_notes = str(track_profile.get("bias_notes", "")).lower()
    
    # Identify track classifications
    is_tight = any(k in bias_notes for k in ["tight", "bullring", "short straight", "speed bias", "leader", "passing lane"])
    is_spacious = any(k in bias_notes for k in ["fair", "spacious", "long straight", "sweeping", "closer's paradise"])

    for index, row in df.iterrows():
        predicted_winner = str(row['p1_num']).replace('#', '').strip()
        actual_winner = str(row['win_num']).replace('#', '').strip()
        
        if predicted_winner == actual_winner and predicted_winner != "":
            wins += 1

    base_win_pct = (wins / len(df)) * 100 if len(df) > 0 else 0
    
    ls = weights['lone_speed_bonus']
    tt = weights['trouble_trip_bonus']
    sr = weights['sprint_route_bonus']

    # --- OPPOSING SCORING VECTORS ---
    score_modifier = 0.0

    if is_tight:
        score_modifier = (ls * 1.5) + (tt * 0.2) - (abs(sr) * 1.0)
    elif is_spacious:
        score_modifier = (tt * 1.5) + (sr * 1.0) - (ls * 1.2)
    else:
        score_modifier = (ls * 0.5) + (tt * 0.5)

    final_score = base_win_pct + (score_modifier * 0.1)
    return round(max(final_score, 0.1), 1)

# ==========================================
# 3. OPTIMIZATION EXECUTION LOOP
# ==========================================
def run_optimization():
    print("Booting Advanced Multi-Track Optimizer (File-Based)...")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Could not find database at {DB_PATH}")
        return

    tracks = get_all_tracks()
    if not tracks:
        print("Error: No graded race results found in your database.")
        return

    output_data_path = os.path.join(DATA_DIR, "optimized_weights.json")
    
    all_tracks_weights = {}
    if os.path.exists(output_data_path):
        try:
            with open(output_data_path, "r") as f:
                all_tracks_weights = json.load(f)
        except:
            all_tracks_weights = {}

    # Comprehensive exploration ranges
    lone_speed_ranges = [2, 4, 6, 8]
    trouble_trip_ranges = [2, 5, 8]
    sprint_route_ranges = [-4, -2, 0, 3]

    for track_name in tracks:
        print(f"Optimizing profile weights for: {track_name}...")
        df = load_track_data(track_name)
        
        if df.empty or len(df) < 2:
            print(f" -> Skipping {track_name} (Too few records)")
            continue

        # Load profile directly from the individual track JSON file
        profile = get_track_profile(track_name)

        best_win_pct = -1.0
        best_weights = {'lone_speed_bonus': 4, 'trouble_trip_bonus': 4, 'sprint_route_bonus': -2}

        for ls, tt, sr in itertools.product(lone_speed_ranges, trouble_trip_ranges, sprint_route_ranges):
            current_weights = {
                'lone_speed_bonus': ls,
                'trouble_trip_bonus': tt,
                'sprint_route_bonus': sr
            }
            
            score = simulate_track_win_rate(df, current_weights, profile, track_name)
            
            if score > best_win_pct:
                best_win_pct = score
                best_weights = current_weights

        all_tracks_weights[track_name] = {
            "best_win_pct": f"{best_win_pct:.1f}%",
            "weights": best_weights
        }
        print(f" -> {track_name} Best Score: {best_win_pct:.1f}% | Weights: {best_weights}")

    # Remove legacy flat keys
    for flat_key in ['lone_speed_bonus', 'trouble_trip_bonus', 'sprint_route_bonus']:
        if flat_key in all_tracks_weights:
            del all_tracks_weights[flat_key]

    with open(output_data_path, "w") as f:
        json.dump(all_tracks_weights, f, indent=4)
        
    print("\n==========================================")
    print(f"SUCCESS: Optimized weights saved to {output_data_path}")
    print("==========================================")

if __name__ == "__main__":
    run_optimization()