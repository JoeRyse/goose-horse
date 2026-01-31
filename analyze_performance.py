import sqlite3
import pandas as pd
import sys

DB_FILE = "racing_ledger.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def analyze_performance(target_track=None):
    conn = get_connection()
    
    # Base Query
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
        res.win_payout,
        res.exacta_payout,
        res.trifecta_payout
    FROM predictions p
    JOIN results res ON p.race_uuid = res.race_uuid
    JOIN races r ON p.race_uuid = r.race_uuid
    """
    
    try:
        df = pd.read_sql_query(query, conn)
    except:
        print("No data found. Grade some races first!")
        return

    if df.empty:
        print("No results logged yet.")
        return

    # FILTER BY TRACK if provided
    if target_track:
        # Normalize for comparison
        df['track_lower'] = df['track'].str.lower().str.strip()
        search_term = target_track.lower().strip()
        df = df[df['track_lower'].str.contains(search_term)]
        
        if df.empty:
            print(f"No graded races found for track: {target_track}")
            return
            
    # --- METRICS ---
    
    # 1. Overall Win % (Top Pick)
    top_picks = df[df['rank_prediction'] == 1].copy()
    
    def check_win(row):
        return str(row['horse_number']).strip() == str(row['winner_number']).strip()
    
    top_picks['won'] = top_picks.apply(check_win, axis=1)
    
    def check_place(row):
        h = str(row['horse_number']).strip()
        w = str(row['winner_number']).strip()
        s = str(row['second_number']).strip()
        t = str(row['third_number']).strip()
        return h in [w, s, t]

    top_picks['placed'] = top_picks.apply(check_place, axis=1)
    
    win_rate = top_picks['won'].mean() * 100
    place_rate = top_picks['placed'].mean() * 100
    
    # ROI (Flat Bet $2 Win)
    roi_cost = len(top_picks) * 2
    roi_return = top_picks[top_picks['won']]['win_payout'].sum()
    net = roi_return - roi_cost
    roi_pct = (net / roi_cost) * 100 if roi_cost > 0 else 0

    # 4. Danger Bets
    danger_bets = df[df['rank_prediction'] == 99].copy()
    if not danger_bets.empty:
        danger_bets['won'] = danger_bets.apply(check_win, axis=1)
        danger_bets['placed'] = danger_bets.apply(check_place, axis=1)

    # 5. Prime Bets (Best of Day)
    # Filter original DF for high confidence matches
    # We join logic manually since simple filtering is complex with multiple rows per race
    cursor = conn.cursor()
    
    # Construct SQL for Primes, adding Track filter if needed
    prime_sql = """
        SELECT r.race_uuid, r.track, res.winner_number, res.win_payout, p.horse_number
        FROM races r
        JOIN results res ON r.race_uuid = res.race_uuid
        JOIN predictions p ON r.race_uuid = p.race_uuid
        WHERE p.rank_prediction = 1 
        AND (r.betting_strategy LIKE '%High%' OR p.confidence_level = 'Best of Day')
    """
    if target_track:
        prime_sql += " AND lower(r.track) LIKE ?"
        params = (f"%{target_track.lower()}%",)
        cursor.execute(prime_sql, params)
    else:
        cursor.execute(prime_sql)
        
    primes = cursor.fetchall()
    
    # --- PRINT REPORT ---
    title = f"PERFORMANCE REPORT: {target_track.upper()}" if target_track else "PERFORMANCE REPORT: ALL TRACKS"
    
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)
    
    print(f"Total Races Graded: {df['race_uuid'].nunique()}")
    
    # TOP PICKS
    print(f"\n🏆 TOP PICK PERFORMANCE")
    print(f"   Win Rate:   {win_rate:.1f}% ({top_picks['won'].sum()}/{len(top_picks)})")
    print(f"   Place Rate: {place_rate:.1f}% ({top_picks['placed'].sum()}/{len(top_picks)})")
    print(f"   ROI ($2 Win): ${net:+.2f} ({roi_pct:+.1f}%)")

    # PRIME BETS
    if primes:
        p_wins = 0
        p_ret = 0
        for p in primes:
            if str(p[2]).strip() == str(p[4]).strip():
                p_wins += 1
                p_ret += p[3]
        
        p_rate = (p_wins / len(primes)) * 100
        p_net = p_ret - (len(primes) * 2)
        print(f"\n🔥 PRIME BETS (High Confidence)")
        print(f"   Count:      {len(primes)}")
        print(f"   Win Rate:   {p_rate:.1f}%")
        print(f"   ROI ($2):   ${p_net:+.2f}")

    # DANGER HORSES
    if not danger_bets.empty:
        print(f"\n⚠️ DANGER HORSE PERFORMANCE")
        d_win = danger_bets['won'].mean() * 100
        d_plc = danger_bets['placed'].mean() * 100
        d_cost = len(danger_bets) * 2
        d_ret = danger_bets[danger_bets['won']]['win_payout'].sum()
        d_net = d_ret - d_cost
        print(f"   Win Rate:   {d_win:.1f}%")
        print(f"   Place Rate: {d_plc:.1f}%")
        print(f"   ROI ($2 Win): ${d_net:+.2f}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    # Allow command line arg: python analyze_performance.py "Gulfstream"
    if len(sys.argv) > 1:
        track_arg = sys.argv[1]
        analyze_performance(track_arg)
    else:
        # Interactive mode
        print("Tip: You can provide a track name argument.")
        t = input("Enter Track Filter (or Enter for All): ").strip()
        analyze_performance(t if t else None)
