import sqlite3
import os

DB_FILE = "racing_ledger.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def ensure_table_exists():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, race_uuid TEXT, winner_number TEXT, 
            second_number TEXT, third_number TEXT, win_payout REAL, 
            exacta_payout REAL, trifecta_payout REAL)''')
    conn.commit()
    conn.close()

def get_pending_meetings():
    """Get list of meetings (Track, Date) that have pending races."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT r.track, r.date, COUNT(r.race_number) as count
    FROM races r
    LEFT JOIN results res ON r.race_uuid = res.race_uuid
    WHERE res.race_uuid IS NULL
    GROUP BY r.track, r.date
    ORDER BY r.date DESC, r.track
    """
    try: cursor.execute(query); rows = cursor.fetchall()
    except: rows = []
    conn.close()
    return rows

def get_races_for_meeting(track, date):
    """Get pending races for a specific meeting."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT r.race_uuid, r.race_number
    FROM races r
    LEFT JOIN results res ON r.race_uuid = res.race_uuid
    WHERE res.race_uuid IS NULL AND r.track = ? AND r.date = ?
    ORDER BY r.race_number
    """
    cursor.execute(query, (track, date))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_meeting(track, date):
    """Delete an entire meeting and its related data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Get UUIDs
    cursor.execute("SELECT race_uuid FROM races WHERE track = ? AND date = ?", (track, date))
    uuids = [row[0] for row in cursor.fetchall()]
    
    if not uuids:
        print("No races found to delete.")
        conn.close()
        return

    print(f"\n⚠️  WARNING: You are about to DELETE the card for: {track} ({date})")
    confirm = input(f"    This will remove {len(uuids)} races and all predictions. Type 'yes' to confirm: ").strip().lower()
    
    if confirm != 'yes':
        print("    Cancelled.")
        conn.close()
        return

    # 2. Delete
    # SQLite requires ? placeholders for IN clause
    placeholders = ','.join(['?'] * len(uuids))
    
    cursor.execute(f"DELETE FROM predictions WHERE race_uuid IN ({placeholders})", uuids)
    cursor.execute(f"DELETE FROM results WHERE race_uuid IN ({placeholders})", uuids)
    cursor.execute("DELETE FROM races WHERE track = ? AND date = ?", (track, date))
    
    conn.commit()
    conn.close()
    print(f"\n🗑️  Deleted meeting: {track} ({date})")

def grade_race_logic(race_uuid, track, race_num):
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"\n" + "-"*40)
    print(f"🏁 Grading: {track} Race {race_num}")
    print("-"*40)
    
    # Show Strategy
    cursor.execute("SELECT betting_strategy FROM races WHERE race_uuid = ?", (race_uuid,))
    row = cursor.fetchone()
    if row and row[0]:
        print(f"📜 STRATEGY: {row[0]}")
        print("-" * 20)
        
    # Show Picks
    cursor.execute("SELECT horse_number, horse_name, rank_prediction, confidence_level FROM predictions WHERE race_uuid = ? ORDER BY rank_prediction ASC", (race_uuid,))
    picks = cursor.fetchall()
    
    print("🔮 AI Picks:")
    for p in picks:
        # p: num, name, rank, confidence
        label = p[3] if p[3] else f"Rank {p[2]}"
        print(f"   {label:<12} #{p[0]:<4} {p[1]}")
        
    print("\n📝 Enter Results (or 's' to skip/back):")
    winner = input("   1st Place #: ").strip()
    if winner.lower() in ['s', 'skip', 'b', 'back', 'q']: 
        conn.close()
        return

    second = input("   2nd Place #: ").strip()
    third  = input("   3rd Place #: ").strip()
    
    try:
        w = float(input("   Win Payout ($): ") or 0)
        e = float(input("   Exacta Pay ($): ") or 0)
        t = float(input("   Trifecta Pay($): ") or 0)
    except:
        w, e, t = 0, 0, 0
        
    cursor.execute('''INSERT INTO results (race_uuid, winner_number, second_number, third_number, win_payout, exacta_payout, trifecta_payout)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', (race_uuid, winner, second, third, w, e, t))
    conn.commit()
    conn.close()
    print("✅ Saved!")

def meeting_menu(track, date):
    while True:
        races = get_races_for_meeting(track, date)
        if not races:
            print(f"\n✅ Completed all races for {track}!")
            break
            
        print(f"\n" + "="*40)
        print(f"📍 {track} [{date}]")
        print(f"   {len(races)} races remaining")
        print("="*40)
        
        # Display simplified list
        race_nums = [r[1] for r in races]
        print(f"Races: {', '.join(map(str, race_nums))}")
        
        # Auto-suggest first race
        next_race = races[0]
        
        print(f"\nNext up: Race {next_race[1]}")
        cmd = input(f"Press ENTER to grade Race {next_race[1]}, type 'r#' for specific race, or 'b' to back: ").strip().lower()
        
        if cmd == 'b': break
        
        target_race = next_race # Default
        
        if cmd.startswith('r'):
            # try find specific race number
            try:
                r_num = int(cmd[1:])
                found = next((r for r in races if r[1] == r_num), None)
                if found: target_race = found
            except: pass
            
        grade_race_logic(target_race[0], track, target_race[1])

def main_menu():
    ensure_table_exists()
    
    while True:
        meetings = get_pending_meetings()
        if not meetings:
            print("\n🎉 All caught up! No pending races found.")
            break

        print("\n" + "="*60)
        print(f"📅 PENDING MEETINGS ({len(meetings)})")
        print("="*60)
        print(f"{'ID':<4} {'Date':<12} {'Track':<30} {'Pending'}")
        print("-" * 60)
        
        for i, m in enumerate(meetings):
            # m = (track, date, count)
            print(f"{i+1:<4} {m[1]:<12} {m[0]:<30} {m[2]} races")
            
        print("\nOptions:")
        print("  [#]      Select a meeting to grade (e.g., '1')")
        print("  [del #]  Delete a meeting (e.g., 'del 1')")
        print("  [q]      Quit")
        
        choice = input("\nChoice > ").strip().lower()
        
        if choice in ['q', 'quit']:
            break
            
        if choice.startswith('del '):
            try:
                idx = int(choice.split(' ')[1]) - 1
                if 0 <= idx < len(meetings):
                    delete_meeting(meetings[idx][0], meetings[idx][1])
            except:
                print("Invalid delete command.")
            continue
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(meetings):
                meeting_menu(meetings[idx][0], meetings[idx][1])
        except ValueError:
            pass

if __name__ == "__main__":
    main_menu()
