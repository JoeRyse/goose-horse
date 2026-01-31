import sqlite3
import json
import os
import glob

# DB CONFIG
DB_NAME = "racing_data.db"
LOGS_DIR = "logs"  # Where your JSON files live

def init_db():
    """Creates the database tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. MEETINGS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track TEXT,
        date TEXT,
        track_condition TEXT,
        UNIQUE(track, date)
    )''')

    # 2. RACES TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS races (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        race_number INTEGER,
        distance TEXT,
        surface TEXT,
        confidence TEXT,
        strategy TEXT,
        danger_horse_name TEXT,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id),
        UNIQUE(meeting_id, race_number)
    )''')

    # 3. SELECTIONS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS selections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id INTEGER,
        rank INTEGER,
        horse_number TEXT,
        horse_name TEXT,
        barrier TEXT,
        reason TEXT,
        finish_position INTEGER DEFAULT NULL,
        win_paid REAL DEFAULT 0.0,
        FOREIGN KEY (race_id) REFERENCES races(id)
    )''')

    conn.commit()
    conn.close()
    print(f"✅ Database {DB_NAME} ready.")

def ingest_json_logs():
    """Reads all JSON files in logs/ and inserts them into DB."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    files = glob.glob(os.path.join(LOGS_DIR, "*.json"))
    print(f"📂 Found {len(files)} log files. Scanning...")

    new_records = 0
    skipped_files = 0

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content: continue # Skip empty files
                data = json.loads(content)

            # --- DATA VALIDATION (The Fix) ---
            # 1. If data is a string (double-encoded JSON), try to parse it again
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    print(f"⚠️ Skipping {filepath}: Invalid JSON string format.")
                    skipped_files += 1
                    continue

            # 2. If data is a List (rare but possible), grab the first item
            if isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    data = data[0]
                else:
                    print(f"⚠️ Skipping {filepath}: Data is a list without a dictionary.")
                    skipped_files += 1
                    continue

            # 3. Final check: Data MUST be a dictionary
            if not isinstance(data, dict):
                print(f"⚠️ Skipping {filepath}: Root data is not a dictionary.")
                skipped_files += 1
                continue

            # --- IMPORT LOGIC ---
            # Safe Access to Meta
            meta = data.get('meta')
            if not isinstance(meta, dict): meta = {}
            
            track = meta.get('track', 'Unknown')
            date = meta.get('date', 'Unknown')
            cond = meta.get('track_condition', 'Unknown')

            # Insert Meeting
            c.execute('INSERT OR IGNORE INTO meetings (track, date, track_condition) VALUES (?, ?, ?)', 
                      (track, date, cond))
            
            c.execute('SELECT id FROM meetings WHERE track = ? AND date = ?', (track, date))
            meeting_row = c.fetchone()
            if not meeting_row: continue
            meeting_id = meeting_row[0]

            # Process Races
            races = data.get('races')
            if not isinstance(races, list): 
                # print(f"ℹ️ {filepath} has no races list.") 
                continue

            for race in races:
                # Ensure race is a dictionary
                if not isinstance(race, dict): continue

                r_num = race.get('number')
                if r_num is None: continue # Skip races without numbers

                # Check duplicates
                c.execute('SELECT id FROM races WHERE meeting_id = ? AND race_number = ?', (meeting_id, r_num))
                if c.fetchone(): continue 

                # Insert Race
                danger = race.get('danger_horse')
                # Handle danger if it's not a dict (sometimes null)
                danger_name = danger.get('name') if isinstance(danger, dict) else None
                
                strat_obj = race.get('exotic_strategy')
                strat = strat_obj.get('strategy', '') if isinstance(strat_obj, dict) else ''

                c.execute('''INSERT INTO races (meeting_id, race_number, distance, surface, confidence, strategy, danger_horse_name)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (meeting_id, r_num, race.get('distance'), race.get('surface'), 
                           race.get('confidence_level'), strat, danger_name))
                
                race_id = c.lastrowid

                # Insert Selections
                picks = race.get('selections', [])
                if isinstance(picks, list):
                    for i, horse in enumerate(picks):
                        if not isinstance(horse, dict): continue
                        
                        rank = i + 1
                        c.execute('''INSERT INTO selections (race_id, rank, horse_number, horse_name, barrier, reason)
                                     VALUES (?, ?, ?, ?, ?, ?)''',
                                  (race_id, rank, horse.get('number'), horse.get('name'), horse.get('barrier'), horse.get('reason')))
                
                new_records += 1

        except Exception as e:
            print(f"❌ Critical Error on {filepath}: {e}")
            skipped_files += 1

    conn.commit()
    conn.close()
    print(f"🚀 DONE. Added {new_records} races. Skipped {skipped_files} invalid files.")

if __name__ == "__main__":
    init_db()
    ingest_json_logs()