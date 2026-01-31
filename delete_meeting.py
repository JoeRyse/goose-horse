import sqlite3
import os
import json
import glob
import shutil

DB_NAME = "racing_data.db"
LOGS_DIR = "logs"
TRASH_DIR = os.path.join(LOGS_DIR, "deleted")

def archive_log_file(track_name, date_str):
    """Finds the JSON file matching this track/date and moves it to trash."""
    if not os.path.exists(TRASH_DIR):
        os.makedirs(TRASH_DIR)

    files = glob.glob(os.path.join(LOGS_DIR, "*.json"))
    found = False

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content: continue
                data = json.loads(content)
                if isinstance(data, str): data = json.loads(data)
                
                meta = data.get('meta', {})
                if meta.get('track') == track_name and meta.get('date') == date_str:
                    filename = os.path.basename(filepath)
                    new_path = os.path.join(TRASH_DIR, filename)
                    f.close() 
                    shutil.move(filepath, new_path)
                    print(f"   📦 Archived file: {filename}")
                    found = True
                    break 
        except Exception:
            continue

def get_tracks_with_data(conn):
    """Returns a list of unique tracks that actually have meetings."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT track FROM meetings ORDER BY track ASC")
    return [row[0] for row in c.fetchall()]

def delete_process():
    conn = sqlite3.connect(DB_NAME)
    
    while True:
        # --- SCREEN 1: SELECT TRACK ---
        tracks = get_tracks_with_data(conn)
        
        if not tracks:
            print("\n✅ Database is empty. Nothing to delete.")
            break

        print("\n" + "="*40)
        print("   🗑️  SELECT TRACK TO MANAGE")
        print("="*40)
        
        for idx, t in enumerate(tracks):
            print(f"[{idx+1}] {t}")
            
        print("-" * 40)
        val = input("Select Track # (or 'q' to quit): ").strip()
        
        if val.lower() == 'q': break
        
        try:
            track_idx = int(val) - 1
            if track_idx < 0 or track_idx >= len(tracks): raise ValueError
            selected_track = tracks[track_idx]
        except ValueError:
            print("❌ Invalid selection.")
            continue

        # --- SCREEN 2: SELECT MEETING FOR THAT TRACK ---
        while True:
            c = conn.cursor()
            c.execute("SELECT id, date, track_condition FROM meetings WHERE track = ? ORDER BY date DESC", (selected_track,))
            meetings = c.fetchall()
            
            if not meetings:
                print(f"\nNo more meetings for {selected_track}.")
                break # Go back to track list

            print(f"\n--- Managing: {selected_track} ---")
            print(f"{'ID':<6} {'Date':<15} {'Condition'}")
            print("-" * 40)
            for m in meetings:
                print(f"[{m[0]:<4}] {m[1]:<15} {m[2]}")
            print("-" * 40)
            
            val = input(f"Enter ID to DELETE for {selected_track} (or 'b' for Back): ").strip()
            
            if val.lower() == 'b': break # Break inner loop, back to tracks
            
            try:
                meeting_id = int(val)
            except ValueError:
                print("❌ Invalid ID.")
                continue

            # Verify ID belongs to this track (safety check)
            c.execute("SELECT date FROM meetings WHERE id = ? AND track = ?", (meeting_id, selected_track))
            target = c.fetchone()
            
            if not target:
                print("❌ ID not found for this track.")
                continue
                
            date_str = target[0]

            # PERFORM DELETE
            try:
                # Cascade delete races/selections
                c.execute("SELECT id FROM races WHERE meeting_id = ?", (meeting_id,))
                races = c.fetchall()
                race_ids = [r[0] for r in races]

                if race_ids:
                    placeholders = ','.join(['?'] * len(race_ids))
                    c.execute(f"DELETE FROM selections WHERE race_id IN ({placeholders})", race_ids)
                    c.execute("DELETE FROM races WHERE meeting_id = ?", (meeting_id,))
                    
                c.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
                conn.commit()
                print(f"✅ Deleted {selected_track} - {date_str}")
                
                # File cleanup
                archive_log_file(selected_track, date_str)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                conn.rollback()

    conn.close()
    print("Exited.")

if __name__ == "__main__":
    delete_process()