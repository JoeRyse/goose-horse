import sqlite3

DB_FILE = "racing_ledger.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def analyze_blindspots():
    conn = get_connection()
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("🕵️  BLIND SPOT ANALYSIS (125+ RACES)")
    print("="*60)

    # Filter out cancelled
    base_filter = "AND r.winner_number NOT IN ('CANCELLED', 'Cancelled', '00')"

    # 1. WHO IS WINNING? (The Breakdown)
    print(f"\n📊 WHO IS WINNING?")
    print(f"   {'-'*40}")
    
    # We need to look at EVERY race and see which prediction 'bucket' the winner came from
    cursor.execute(f"""
        SELECT r.race_uuid, r.winner_number, r.win_payout
        FROM results r
        WHERE 1=1 {base_filter}
    """)
    results = cursor.fetchall()

    stats = {
        "Top Pick": 0,
        "Danger": 0,
        "Value": 0,
        "Best of Day": 0,
        "In The Lists (Other)": 0,
        "COMPLETE MISS": 0
    }
    
    total_races = 0
    total_miss_payout = 0.0

    for row in results:
        uuid, winner, payout = row
        total_races += 1
        
        # Get predictions for this race
        cursor.execute("SELECT horse_number, rank_prediction, confidence_level FROM predictions WHERE race_uuid = ?", (uuid,))
        preds = cursor.fetchall()
        
        found = False
        
        # Check Best of Day first
        for p in preds:
            if str(p[0]) == str(winner) and p[2] == 'Best of Day':
                stats["Best of Day"] += 1 # Overlap note: Best of Day is also a Top Pick usually
                # We won't count 'found=True' here to allow it to count in its rank category too
        
        # Check Rank
        for p in preds:
            h_num, rank, conf = p
            if str(h_num) == str(winner):
                if rank == 'Top Pick': stats["Top Pick"] += 1
                elif rank == 'Danger': stats["Danger"] += 1
                elif rank == 'Value': stats["Value"] += 1
                else: stats["In The Lists (Other)"] += 1
                found = True
                break
        
        if not found:
            stats["COMPLETE MISS"] += 1
            total_miss_payout += payout

    # Print Stats
    for cat, count in stats.items():
        pct = (count / total_races) * 100
        print(f"   {cat:<20} | {count:<3} Wins | {pct:.1f}%")

    # 2. ANALYSIS OF THE MISSES
    avg_miss_price = (total_miss_payout / stats["COMPLETE MISS"]) if stats["COMPLETE MISS"] > 0 else 0
    
    print(f"\n📉 THE 'GHOST' HORSES (Complete Misses)")
    print(f"   When the AI misses completely...")
    print(f"   Avg Winner Payout: ${avg_miss_price:.2f}")
    
    if avg_miss_price > 20.00:
        print("   👉 DIAGNOSIS: The system is ignoring Longshots. It is too conservative.")
    elif avg_miss_price < 8.00:
        print("   👉 DIAGNOSIS: The system is missing obvious favorites. Check your data inputs.")
    else:
        print("   👉 DIAGNOSIS: The misses are average priced. This is normal variance.")

    conn.close()

if __name__ == "__main__":
    analyze_blindspots()