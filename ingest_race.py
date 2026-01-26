import os
import json
import sqlite3
import time
from google import genai
from google.genai import types

# --- CONFIGURATION ---
DB_FILE = "racing_ledger.db"
LOGS_DIR = "logs"
PROCESSED_DIR = "logs/processed"

# 🔑 API KEY SETUP
# Make sure your API key is set in your environment variables.
# If not, you can hardcode it here (not recommended for sharing): os.environ["GOOGLE_API_KEY"] = "YOUR_KEY"
client = genai.Client(http_options={'api_version': 'v1alpha'})

# --- THE NEW "AGGRESSIVE" SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are a professional, high-stakes horse racing handicapper. 
Your goal is NOT just to find the most likely winner, but to find the "Correct Wager" based on value and race shape.

You will be given a JSON dataset of a horse race.
You must analyze the runners and output your analysis in strict JSON format.

*** CRITICAL HANDICAPPING INSTRUCTIONS ***
You are currently too conservative. You are missing longshot winners (Avg Payout $22.00) because you over-penalize poor recent form (e.g., 8th, 9th place finishes).

ADJUST YOUR "DANGER" AND "VALUE" LOGIC IMMEDIATELY:

1. THE "FORGIVENESS" RULE:
   - If a horse has bad recent form (e.g., 8-9-0) but is DROPPING IN CLASS today, you must consider them.
   - If a horse is switching surface (Turf to Dirt) and has a pedigree for it, ignore the bad turf form.
   - If a horse had a "Troubled Trip" (check comments) last time, forgive the result.

2. THE "LONE SPEED" RULE:
   - If a horse is the ONLY one with "Run Style: Leader" or "Early Pace", UPGRADE THEM SIGNIFICANTLY.
   - Uncontested speed is the most dangerous angle in racing. Even if they look slow on paper, they can steal the race.

3. DANGER VS TOP PICK:
   - "Top Pick": The most logical winner (Best Speed + Best Class).
   - "Danger": The "High Ceiling" horse. Do NOT pick a "safe" 2nd favorite here. Pick the horse that could blow up the tote board if they run their best race.
   - "Value": A horse with hidden merit (bad trip last time, sneaky trainer angle, huge jockey switch).

4. CONFIDENCE LEVELS:
   - "Best of Day": Only use this if the horse is a "Lock" (Lone Speed, Dropping in Class, Best Figures).
   - "High": Solid favorite, hard to beat.
   - "Medium": Competitive race, 2-3 horses could win.
   - "Low": Chaos race, anything could happen.

*** OUTPUT FORMAT ***
You must return a single JSON object with this exact structure:
{
  "summary": "Brief analysis of the race shape (e.g., 'Fast pace favors closers').",
  "confidence_level": "Best of Day" | "High" | "Medium" | "Low",
  "picks": {
    "top_pick": { "number": "1", "name": "Horse Name", "reason": "Why it wins." },
    "danger":   { "number": "4", "name": "Horse Name", "reason": "Why it threatens." },
    "value":    { "number": "7", "name": "Horse Name", "reason": "Why it's a good price." }
  }
}
"""

def get_connection():
    return sqlite3.connect(DB_FILE)

def ensure_dirs():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

def load_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_races(track_date_slug):
    """
    Returns a list of race numbers specifically for this track/date that are already in the DB.
    Useful so we don't re-ingest the same race twice if we re-run the script.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # We construct a partial UUID search: "gulfstream_park_2025-01-01%"
    cursor.execute("SELECT race_number FROM races WHERE race_uuid LIKE ?", (f"{track_date_slug}%",))
    existing_races = [row[0] for row in cursor.fetchall()]
    conn.close()
    return existing_races

def save_analysis(race_data, analysis, track_name, race_date):
    conn = get_connection()
    cursor = conn.cursor()

    race_num = race_data['race_number']
    
    # Create a unique ID: "gulfstream_park_2025-01-01_R1"
    clean_track = track_name.lower().replace(" ", "_")
    race_uuid = f"{clean_track}_{race_date}_R{race_num}"

    print(f"   Saving Race {race_num} to Database...")

    # 1. Insert Race (Ignore if exists)
    cursor.execute('''
        INSERT OR IGNORE INTO races (race_uuid, track, date, race_number, distance, surface, conditions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (race_uuid, track_name, race_date, race_num, 
          race_data.get('distance', ''), 
          race_data.get('surface', ''), 
          race_data.get('conditions', '')))

    # 2. Insert Predictions
    # We map the JSON keys (top_pick, danger, value) to our DB columns
    rank_map = {
        'top_pick': 'Top Pick',
        'danger': 'Danger',
        'value': 'Value'
    }

    # We need to loop through the AI's picks
    for key, pick_data in analysis['picks'].items():
        if not pick_data or 'number' not in pick_data: continue

        horse_num = pick_data['number']
        horse_name = pick_data['name']
        reason = pick_data['reason']
        rank = rank_map.get(key, 'Unknown')
        confidence = analysis.get('confidence_level', 'Medium')

        cursor.execute('''
            INSERT INTO predictions (race_uuid, horse_number, horse_name, rank_prediction, reasoning, confidence_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (race_uuid, horse_num, horse_name, rank, reason, confidence))

    conn.commit()
    conn.close()

def analyze_race(race_data):
    # Convert the single race object to a string for the AI
    race_json_str = json.dumps(race_data, indent=2)

    # Call Gemini
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=f"{SYSTEM_PROMPT}\n\nANALYZE THIS RACE:\n{race_json_str}",
        config=types.GenerateContentConfig(
            response_mime_type='application/json'
        )
    )
    
    # Parse the response
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        return None

def process_file(filename):
    filepath = os.path.join(LOGS_DIR, filename)
    data = load_json_file(filepath)

    # Extract Meta Data
    track_name = data.get('track_name', 'Unknown Track')
    race_date = data.get('date', '2025-01-01')
    
    # Check which races we have already done
    clean_track = track_name.lower().replace(" ", "_")
    track_slug = f"{clean_track}_{race_date}"
    existing_races = get_db_races(track_slug)

    print(f"\n--- INGESTING: {filename} ---")
    print(f"    Track: {track_name} | Date: {race_date}")

    races_processed = 0

    for race in data['races']:
        r_num = race['race_number']
        
        if r_num in existing_races:
            print(f"    Skipping Race {r_num} (Already in DB)")
            continue

        print(f"    Processing Race {r_num}...")
        
        # 1. Ask AI to handicap
        analysis = analyze_race(race)
        
        if analysis:
            # 2. Save to SQLite
            save_analysis(race, analysis, track_name, race_date)
            races_processed += 1
            # Sleep briefly to be nice to the API
            time.sleep(1) 
        else:
            print(f"    [Error] AI failed to handicap Race {r_num}")

    # Move file to processed folder ONLY if we did something
    if races_processed > 0:
        new_path = os.path.join(PROCESSED_DIR, filename)
        os.rename(filepath, new_path)
        print(f"    Done. Moved {filename} to processed folder.")
    elif len(existing_races) > 0:
         # If we skipped everything because it was done, still move it
        new_path = os.path.join(PROCESSED_DIR, filename)
        os.rename(filepath, new_path)
        print(f"    All races already in DB. Moved file.")
    else:
        print("    No races processed.")

def main():
    ensure_dirs()
    
    # Look for JSON files in the logs folder
    files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
    
    if not files:
        print("No JSON files found in 'logs/'. Please add a race file.")
        return

    for f in files:
        process_file(f)

if __name__ == "__main__":
    main()