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

def list_pending_races():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT r.race_uuid, r.track, r.date, r.race_number
    FROM races r
    LEFT JOIN results res ON r.race_uuid = res.race_uuid
    WHERE res.race_uuid IS NULL
    ORDER BY r.date DESC, r.track, r.race_number
    """
    try: cursor.execute(query); rows = cursor.fetchall()
    except: rows = []
    conn.close()
    return rows

def enter_results():
    ensure_table_exists()

    while True:
        pending = list_pending_races()
        if not pending:
            print("\n[Info] All races graded! Run 'import_html_data.py' if you added new HTML cards.")
            break

        print("\n" + "="*40)
        print("🏁 PENDING RACES")
        print("="*40)
        for i, r in enumerate(pending):
            print(f"{i+1}. [{r[2]}] {r[1]} - Race {r[3]}")

        choice = input("\nSelect race # (or 'q'): ").strip().lower()
        if choice in ['q', 'quit']: break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(pending): grade_race(pending[idx])
        except ValueError: pass

def grade_race(race_data):
    race_uuid, track, date, num = race_data
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"\n--- Grading: {track} Race {num} ---")

    # 1. SHOW THE STRATEGY (New Feature)
    cursor.execute("SELECT betting_strategy FROM races WHERE race_uuid = ?", (race_uuid,))
    strat_row = cursor.fetchone()
    if strat_row and strat_row[0]:
        print(f"\n📜 STRATEGY: {strat_row[0]}")
    
    # 2. Show Picks
    cursor.execute("SELECT horse_number, horse_name, rank_prediction FROM predictions WHERE race_uuid = ? ORDER BY rank_prediction DESC", (race_uuid,))
    picks = cursor.fetchall()
    print("\nPicks:")
    for p in picks:
        if p[2] in ['Top Pick', 'Danger', 'Value', 'Best of Day']:
            print(f"  [{p[2]}] #{p[0]} {p[1]}")

    print("\nOfficial Results (or 'q' to back):")
    
    winner = input("  Winner #: ").strip()
    if winner in ['q', 'quit']: return
    second = input("  2nd Place #: ").strip()
    third = input("  3rd Place #: ").strip()
    
    try:
        w_pay = float(input("  Win Payout: ").strip() or 0)
        e_pay = float(input("  Exacta Payout: ").strip() or 0)
        t_pay = float(input("  Trifecta Payout: ").strip() or 0)
    except ValueError:
        w_pay=0; e_pay=0; t_pay=0

    cursor.execute('''INSERT INTO results (race_uuid, winner_number, second_number, third_number, win_payout, exacta_payout, trifecta_payout)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', (race_uuid, winner, second, third, w_pay, e_pay, t_pay))
    conn.commit()
    conn.close()
    print("Saved!")

if __name__ == "__main__":
    enter_results()