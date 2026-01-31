import sqlite3
import json
import os
import glob
from db_manager import ingest_json_logs

DB_NAME = "racing_data.db"
LOGS_DIR = "logs"

def repair_meeting():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    print("\n" + "="*40)
    print("   🚑  DATABASE REPAIR TOOL")
    print("="*40)
    print("Use this if a meeting shows up but has no picks.")

    # 1. List Meetings
    c.execute("SELECT id, track, date FROM meetings ORDER BY date DESC, track ASC")
    meetings = c.fetchall()

    if not meetings:
        print("Database is empty.")
        return

    for m in meetings:
        # Check how many picks exist for this meeting to help identify broken ones
        c.execute("""
            SELECT COUNT(s.id) 
            FROM selections s 
            JOIN races r ON s.race_id = r.id 
            WHERE r.meeting_id = ?
        """, (m[0],))
        pick_count = c.fetchone()[0]
        
        status = "✅ OK" if pick_count > 0 else "❌ BROKEN (0 Picks)"
        print(f"[{m[0]:<3}] {m[1]:<20} ({m[2]}) - {status}")

    # 2. Select Broken Meeting
    val = input("\nEnter ID to REPAIR (or 'q' to quit): ").strip()
    if val.lower() == 'q': return

    try:
        meeting_id = int(val)
        c.execute("SELECT track, date FROM meetings WHERE id = ?", (meeting_id,))
        target = c.fetchone()
        if not target:
            print("❌ ID not found.")
            return
        
        track_name, date_str = target
        print(f"\n⚡ Repairing {track_name} ({date_str})...")

        # 3. DELETE SQL DATA (But keep JSON)
        # Find race IDs first
        c.execute("SELECT id FROM races WHERE meeting_id = ?", (meeting_id,))
        races = c.fetchall()
        race_ids = [r[0] for r in races]
        
        if race_ids:
            placeholders = ','.join(['?'] * len(race_ids))
            c.execute(f"DELETE FROM selections WHERE race_id IN ({placeholders})", race_ids)
            c.execute("DELETE FROM races WHERE meeting_id = ?", (meeting_id,))
        
        c.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        conn.commit()
        print("   - Corrupt SQL data wiped.")

    except Exception as e:
        print(f"❌ Error deleting SQL data: {e}")
        return
    finally:
        conn.close()

    # 4. TRIGGER RE-IMPORT
    print("   - Attempting re-import from JSON...")
    
    # We call the function from your existing db_manager.py
    # Make sure db_manager.py is in the same folder!
    try:
        ingest_json_logs()
        print("\n✅ REPAIR COMPLETE. Try entering results now.")
    except Exception as e:
        print(f"❌ Re-import failed: {e}")

if __name__ == "__main__":
    repair_meeting()