import sqlite3
import json
import os
import glob
import uuid

DB_FILE = "racing_ledger.db"
LOGS_DIR = "logs"

def get_connection():
    return sqlite3.connect(DB_FILE)

def setup_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Races Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS races (
        race_uuid TEXT PRIMARY KEY,
        track TEXT,
        date TEXT,
        race_number INTEGER,
        distance TEXT,
        surface TEXT,
        class TEXT,
        betting_strategy TEXT
    )
    ''')

    # 2. Predictions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_uuid TEXT,
        horse_number TEXT,
        horse_name TEXT,
        rank_prediction INTEGER, 
        confidence_level TEXT,
        FOREIGN KEY (race_uuid) REFERENCES races (race_uuid)
    )
    ''')

    # 3. Results Table (for completeness)
    cursor.execute('''CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            race_uuid TEXT UNIQUE, 
            winner_number TEXT, 
            second_number TEXT, 
            third_number TEXT, 
            win_payout REAL, 
            exacta_payout REAL, 
            trifecta_payout REAL,
            FOREIGN KEY (race_uuid) REFERENCES races (race_uuid)
    )''')

    conn.commit()
    conn.close()

def migrate_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    columns_to_add = {
        'distance': 'TEXT',
        'surface': 'TEXT',
        'class': 'TEXT',
        'betting_strategy': 'TEXT'
    }
    
    print("Checking database schema...")
    for col, dtype in columns_to_add.items():
        try:
            cursor.execute(f"ALTER TABLE races ADD COLUMN {col} {dtype}")
            print(f"   [Migrate] Added column '{col}' to 'races'")
        except sqlite3.OperationalError:
            pass # Column likely exists
            
    conn.commit()
    conn.close()

def generate_uuid(track, date, race_num):
    # Create a consistent UUID based on track/date/race
    # Sanitize inputs
    s_track = str(track).lower().strip().replace(" ", "_")
    s_date = str(date).strip()
    s_num = str(race_num).strip()
    return f"{s_track}_{s_date}_R{s_num}"

def import_logs():
    conn = get_connection()
    cursor = conn.cursor()
    
    json_files = glob.glob(os.path.join(LOGS_DIR, "*.json"))
    print(f"Found {len(json_files)} log files in {LOGS_DIR}/")
    
    new_races = 0
    new_preds = 0
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle list of races or single object
            if isinstance(data, list):
                # Old format or raw list
                print(f"[Skip] {filepath}: Unexpected root list format.")
                continue
                
            meta = data.get('meta', {})
            track = meta.get('track', 'Unknown')
            date = meta.get('date', 'Unknown')
            
            for race in data.get('races', []):
                r_num = race.get('number')
                race_uuid = generate_uuid(track, date, r_num)
                
                # Check if race exists
                cursor.execute("SELECT 1 FROM races WHERE race_uuid = ?", (race_uuid,))
                if cursor.fetchone():
                    continue # Skip existing
                
                # Insert Race
                strategy = race.get('exotic_strategy', {}).get('strategy', '')
                cursor.execute("""
                    INSERT INTO races (race_uuid, track, date, race_number, distance, surface, betting_strategy)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (race_uuid, track, date, r_num, race.get('distance'), race.get('surface'), strategy))
                
                new_races += 1
                
                # Insert Selections
                selections = race.get('selections', [])
                
                # Normalize picks
                if not selections and 'picks' in race:
                     p = race['picks']
                     selections = [p.get('top_pick',{}), p.get('danger_horse',{}), p.get('value_bet',{})]
                
                for i, horse in enumerate(selections):
                    if not horse or not horse.get('number'): continue
                    
                    rank = i + 1
                    conf = "Top Pick" if i == 0 else "Contender"
                    
                    cursor.execute("""
                        INSERT INTO predictions (race_uuid, horse_number, horse_name, rank_prediction, confidence_level)
                        VALUES (?, ?, ?, ?, ?)
                    """, (race_uuid, horse.get('number'), horse.get('name'), rank, conf))
                    new_preds += 1
                
                # Insert Danger Horse as rank 4 (or special tag)
                danger = race.get('danger_horse', {})
                if danger and danger.get('number'):
                     cursor.execute("""
                        INSERT INTO predictions (race_uuid, horse_number, horse_name, rank_prediction, confidence_level)
                        VALUES (?, ?, ?, ?, ?)
                    """, (race_uuid, danger.get('number'), danger.get('name'), 99, "Danger"))
                     new_preds += 1

        except Exception as e:
            print(f"[Error] {filepath}: {e}")
            
    conn.commit()
    conn.close()
    
    print("\n" + "="*30)
    print(f"IMPORT COMPLETE")
    print(f"   Races Added: {new_races}")
    print(f"   Predictions: {new_preds}")
    print("="*30)

if __name__ == "__main__":
    setup_db()
    migrate_db()
    import_logs()
