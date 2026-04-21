import os
import json
import sqlite3

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(LOGS_DIR, "master_betting_history.db")

def migrate_old_jsons():
    print("🚀 Starting JSON to SQLite Migration...")
    
    if not os.path.exists(DB_PATH):
        print("❌ Database not found! Please run app.py once to create the database.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    files_processed = 0
    races_inserted = 0

    # Loop through everything in the logs folder
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".json") and filename != "track_db.json":
            filepath = os.path.join(LOGS_DIR, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    
                    # Handle if the AI wrapped it in a list
                    if isinstance(data, list): data = data[0] if data else {}
                    
                    meta = data.get("meta", {})
                    date = meta.get('date', 'Unknown Date')
                    track = meta.get('track', 'Unknown Track')
                    condition = meta.get('track_condition', 'Standard')
                    
                    for race in data.get("races", []):
                        selections = race.get('selections', [])
                        
                        # Handle legacy formatting just in case
                        if not selections and 'picks' in race:
                            p = race['picks']
                            selections = [p.get('top_pick', {}), p.get('danger_horse', {}), p.get('value_bet', {})]
                            selections = [s for s in selections if s and s.get('name')]
                        
                        while len(selections) < 4: selections.append({})
                        dang = race.get('danger_horse') or {}
                        
                        # Insert into the database
                        c.execute('''
                            INSERT INTO predictions (
                                date, track, race_number, distance, surface, condition,
                                p1_num, p1_barrier, p1_name, p1_reason,
                                p2_num, p2_barrier, p2_name, p2_reason,
                                p3_num, p3_barrier, p3_name, p3_reason,
                                p4_num, p4_barrier, p4_name, p4_reason,
                                danger_num, danger_barrier, danger_name, danger_reason,
                                confidence, ai_model, temperature
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            date, track, str(race.get('number')), race.get('distance', ''), race.get('surface', ''), condition,
                            selections[0].get('number', 'N/A'), selections[0].get('barrier', ''), selections[0].get('name', 'N/A'), selections[0].get('reason', 'N/A'),
                            selections[1].get('number', ''), selections[1].get('barrier', ''), selections[1].get('name', ''), selections[1].get('reason', ''),
                            selections[2].get('number', ''), selections[2].get('barrier', ''), selections[2].get('name', ''), selections[2].get('reason', ''),
                            selections[3].get('number', ''), selections[3].get('barrier', ''), selections[3].get('name', ''), selections[3].get('reason', ''),
                            dang.get('number', ''), dang.get('barrier', ''), dang.get('name', ''), dang.get('reason', ''),
                            race.get('confidence_level', ''), 'Legacy JSON Import', 0.0
                        ))
                        races_inserted += 1
                        
                    files_processed += 1
                    print(f"✅ Migrated: {filename}")
                
                except Exception as e:
                    print(f"⚠️ Failed to parse {filename}: {e}")

    conn.commit()
    conn.close()
    
    print("\n" + "="*40)
    print(f"🎉 MIGRATION COMPLETE!")
    print(f"📁 Files Processed: {files_processed}")
    print(f"🏇 Total Races Added: {races_inserted}")
    print("="*40)

if __name__ == "__main__":
    migrate_old_jsons()