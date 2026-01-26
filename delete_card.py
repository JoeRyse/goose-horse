import sqlite3

DB_FILE = "racing_ledger.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def delete_meeting():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Find all unique meetings (Track + Date)
    try:
        cursor.execute("SELECT DISTINCT track, date FROM races ORDER BY date DESC, track")
        meetings = cursor.fetchall()
    except sqlite3.OperationalError:
        print("[Error] Could not read database. Make sure 'racing_ledger.db' exists.")
        return

    if not meetings:
        print("\n[Info] Database is empty. Nothing to delete.")
        return

    print("\n" + "="*40)
    print("🗑️  DELETE RACE CARD")
    print("="*40)
    
    for i, m in enumerate(meetings):
        print(f"  {i+1}. {m[0]} ({m[1]})")
    print("  Q. Quit")

    choice = input("\nSelect a meeting to DELETE (Number): ").strip().lower()

    if choice == 'q':
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(meetings):
            print("Invalid selection.")
            return
        target_track, target_date = meetings[idx]
    except ValueError:
        print("Invalid input.")
        return

    # Confirmation
    confirm = input(f"\n⚠️  ARE YOU SURE you want to delete ALL data for {target_track} on {target_date}? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    print(f"\nDeleting {target_track} ({target_date})...")

    # 2. Get the UUIDs for that meeting
    cursor.execute("SELECT race_uuid FROM races WHERE track = ? AND date = ?", (target_track, target_date))
    uuids = [row[0] for row in cursor.fetchall()]

    if not uuids:
        print("No races found for this meeting.")
        return

    # 3. Delete from Child Tables first (Predictions & Results)
    # We use a trick with "IN" clause to delete multiple UUIDs at once
    placeholders = ','.join(['?'] * len(uuids))
    
    cursor.execute(f"DELETE FROM predictions WHERE race_uuid IN ({placeholders})", uuids)
    bets_deleted = cursor.rowcount
    
    cursor.execute(f"DELETE FROM results WHERE race_uuid IN ({placeholders})", uuids)
    results_deleted = cursor.rowcount

    # 4. Delete from Parent Table (Races)
    cursor.execute(f"DELETE FROM races WHERE race_uuid IN ({placeholders})", uuids)
    races_deleted = cursor.rowcount

    conn.commit()
    conn.close()

    print("-" * 30)
    print(f"✅ Success! Removed:")
    print(f"   - {races_deleted} Races")
    print(f"   - {bets_deleted} Predictions")
    print(f"   - {results_deleted} Results")

if __name__ == "__main__":
    delete_meeting()