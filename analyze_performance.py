import sqlite3
import pandas as pd

DB_FILE = "racing_ledger.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def analyze_performance():
    conn = get_connection()
    
    # 1. FETCH DATA (Joined Predictions + Results)
    # We fetch ALL predictions for races that have results
    query = """
    SELECT 
        r.date,
        r.track,
        r.race_number,
        r.race_uuid,
        p.horse_number as pick_num,
        p.rank_prediction as rank,
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
    ORDER BY r.date DESC, r.track, r.race_number
    """
    
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        print("Could not query database. Make sure you ran 'ingest_results.py' first.")
        return

    if df.empty:
        print("No graded races found yet.")
        return

    # --- DATA STRUCTURES ---
    track_stats = {} # { "Gulfstream": {bets: 0, return: 0, wins: 0, races: 0} }
    
    # Exotic Ledgers (Simulating a $2 Box of Top 3 Picks)
    exacta_ledger = {"cost": 0, "return": 0, "hits": 0, "races": 0} # Cost $12 for 3-horse box ($2 base) OR $6 for $1 box. Let's assume $1 Box ($6 cost)
    trifecta_ledger = {"cost": 0, "return": 0, "hits": 0, "races": 0} # Cost $6 for $1 Box of 3 horses

    # Win Betting Ledger (Your $10/$2 Rule)
    win_ledger = {"cost": 0, "return": 0}
    
    # Group by Race to analyze the "Set" of picks
    races = df.groupby('race_uuid')
    
    print("\n" + "="*80)
    print(f"🏁 ADVANCED PERFORMANCE AUDIT")
    print("="*80)
    
    for race_uuid, group in races:
        # 1. Extract Race Info
        meta = group.iloc[0]
        track = meta['track']
        winner = str(meta['winner_number']).strip()
        second = str(meta['second_number']).strip()
        third = str(meta['third_number']).strip()
        
        # 2. Extract Our Picks
        # We look for 'Top Pick', 'Danger', 'Value'
        picks_map = {row['rank']: str(row['pick_num']).strip() for i, row in group.iterrows()}
        
        top_pick = picks_map.get('Top Pick')
        danger = picks_map.get('Danger')
        value = picks_map.get('Value')
        
        # Create a "Box Set" of our available picks (ignoring missing ones)
        box_set = {p for p in [top_pick, danger, value] if p}
        
        # --- A. TRACK STATS (Win Bet on Top Pick Only) ---
        if track not in track_stats:
            track_stats[track] = {"bets": 0, "return": 0, "wins": 0, "count": 0}
            
        if top_pick:
            # Staking Rule: $10 if 'Best of Day', else $2
            confidence = group.loc[group['rank'] == 'Top Pick', 'confidence_level'].iloc[0]
            stake = 10.0 if confidence == 'Best of Day' else 2.0
            
            payout = 0
            if top_pick == winner:
                payout = (meta['win_payout'] / 2) * stake # Adjust to stake
                track_stats[track]['wins'] += 1
                
            track_stats[track]['bets'] += stake
            track_stats[track]['return'] += payout
            track_stats[track]['count'] += 1
            
            win_ledger['cost'] += stake
            win_ledger['return'] += payout

        # --- B. EXACTA AUDIT (Box Top 3) ---
        # Strategy: $1 Box of Top 3 Horses = 6 combinations. Cost: $6.00.
        # Logic: If Winner AND Second are in our Box Set -> WIN.
        if len(box_set) >= 2:
            exacta_ledger['races'] += 1
            exacta_ledger['cost'] += 6.00 
            
            if winner in box_set and second in box_set:
                # We hit the exacta!
                # Database stores $2.00 payout. 
                # Since we bet $1.00 base, we get Half the posted payout.
                pay = meta['exacta_payout'] / 2
                exacta_ledger['return'] += pay
                exacta_ledger['hits'] += 1

        # --- C. TRIFECTA AUDIT (Box Top 3) ---
        # Strategy: $0.50 Box of Top 3 Horses = 6 combs. Cost: $3.00.
        # Logic: If Winner AND Second AND Third in Box Set -> WIN.
        if len(box_set) >= 3:
            trifecta_ledger['races'] += 1
            trifecta_ledger['cost'] += 3.00
            
            if winner in box_set and second in box_set and third in box_set:
                # We hit the trifecta!
                # Database stores $2.00 payout.
                # $0.50 bet is 1/4th of the $2.00 payout.
                pay = meta['trifecta_payout'] / 4
                trifecta_ledger['return'] += pay
                trifecta_ledger['hits'] += 1

    # --- OUTPUT SECTION ---
    
    # 1. TRACK BREAKDOWN
    print(f"\n📍 TRACK STATS (Win Bets)")
    print(f"{'TRACK':<20} {'RACES':<6} {'WIN %':<8} {'P/L':<10} {'ROI'}")
    print("-" * 65)
    
    for trk, stats in track_stats.items():
        n = stats['count']
        if n == 0: continue
        win_pct = (stats['wins'] / n) * 100
        profit = stats['return'] - stats['bets']
        roi = (profit / stats['bets']) * 100
        
        color_pl = f"+${profit:.2f}" if profit > 0 else f"-${abs(profit):.2f}"
        print(f"{trk:<20} {n:<6} {win_pct:.1f}%   {color_pl:<10} {roi:+.1f}%")

    # 2. EXOTIC PERFORMANCE
    print(f"\n📦 EXOTIC 'BOX' PERFORMANCE (Top 3 Picks)")
    print("-" * 65)
    
    # Exacta
    ex_net = exacta_ledger['return'] - exacta_ledger['cost']
    ex_roi = (ex_net / exacta_ledger['cost'] * 100) if exacta_ledger['cost'] > 0 else 0
    print(f"🔹 EXACTA ($1 Box of Top 3 / Cost $6)")
    print(f"   Hits: {exacta_ledger['hits']}/{exacta_ledger['races']}")
    print(f"   Cost: ${exacta_ledger['cost']:.2f} | Return: ${exacta_ledger['return']:.2f}")
    print(f"   P/L:  ${ex_net:.2f} (ROI: {ex_roi:+.1f}%)")
    
    # Trifecta
    tri_net = trifecta_ledger['return'] - trifecta_ledger['cost']
    tri_roi = (tri_net / trifecta_ledger['cost'] * 100) if trifecta_ledger['cost'] > 0 else 0
    print(f"\n🔹 TRIFECTA ($0.50 Box of Top 3 / Cost $3)")
    print(f"   Hits: {trifecta_ledger['hits']}/{trifecta_ledger['races']}")
    print(f"   Cost: ${trifecta_ledger['cost']:.2f} | Return: ${trifecta_ledger['return']:.2f}")
    print(f"   P/L:  ${tri_net:.2f} (ROI: {tri_roi:+.1f}%)")

    # 3. GRAND TOTAL
    total_net = (win_ledger['return'] - win_ledger['cost'])
    print(f"\n" + "="*80)
    print(f"💰 OVERALL WIN BET P/L: ${total_net:+.2f}")
    print("="*80)

    conn.close()

if __name__ == "__main__":
    analyze_performance()