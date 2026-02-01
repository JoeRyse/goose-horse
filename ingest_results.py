import sqlite3
import os
import json
import re
from google import genai
from google.genai import types
import PyPDF2
import glob

# --- CONFIGURATION ---
DB_FILE = "racing_ledger.db"
RESULTS_DIR = "results"

# --- API KEY SETUP ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    try:
        # Try to find a local key file or prompt
        api_key = input("🔑 Enter your Gemini API Key: ").strip()
    except:
        pass

# Initialize Client
try:
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
except Exception as e:
    print(f"Error initializing AI: {e}")
    exit()

SYSTEM_PROMPT = """
You are a Data Extraction Specialist for horse racing.
Your goal is to extract official results from a race chart PDF text.

**TASK:**
Return a valid JSON object containing the metadata and results for every race found in the text.

**REQUIRED JSON STRUCTURE:**
{
  "meta": {
    "track_name": "Gulfstream Park",
    "date": "2026-01-25" (Format: YYYY-MM-DD)
  },
  "races": [
    {
      "race_number": 1,
      "winner_pgm": "5",
      "second_pgm": "2",
      "third_pgm": "9",
      "win_payout": 12.40,
      "exacta_payout": 45.20,
      "trifecta_payout": 120.50
    }
  ]
}

**RULES:**
1. **Program Numbers (PGM):** Extract the horse number (e.g., "5", "1A"). NOT the post position.
2. **Payouts:** Extract the standard $2.00 payout.
   - If the chart lists a $1.00 Exacta, MULTIPLY by 2.
   - If the chart lists a $0.50 Trifecta, MULTIPLY by 4.
   - All exotic payouts must be standardized to a $2.00 base.
   - If a payout is missing (e.g. no winner), return 0.00.
3. **Date:** Convert date to YYYY-MM-DD.
"""

def get_connection():
    return sqlite3.connect(DB_FILE)

def ensure_results_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results'")
    table_exists = cursor.fetchone()

    if table_exists:
        # Check if race_uuid is unique
        cursor.execute("PRAGMA index_list('results')")
        indexes = cursor.fetchall()
        is_unique = any(idx[2] == 1 for idx in indexes) # Index 2 is 'unique' flag
        
        if not is_unique:
            print("   ⚠️ Database Schema Fix Required: Rebuilding 'results' table...")
            # Rename old table
            cursor.execute("ALTER TABLE results RENAME TO results_old")
            # Create new correct table
            cursor.execute('''CREATE TABLE results (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                race_uuid TEXT UNIQUE, 
                winner_number TEXT, 
                second_number TEXT, 
                third_number TEXT, 
                win_payout REAL, 
                exacta_payout REAL, 
                trifecta_payout REAL
            )''')
            # Copy data back
            cursor.execute("INSERT INTO results (race_uuid, winner_number, second_number, third_number, win_payout, exacta_payout, trifecta_payout) SELECT race_uuid, winner_number, second_number, third_number, win_payout, exacta_payout, trifecta_payout FROM results_old")
            cursor.execute("DROP TABLE results_old")
            print("   ✅ Database fixed.")
    else:
        cursor.execute('''CREATE TABLE results (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                race_uuid TEXT UNIQUE, 
                winner_number TEXT, 
                second_number TEXT, 
                third_number TEXT, 
                win_payout REAL, 
                exacta_payout REAL, 
                trifecta_payout REAL
                )''')
    
    conn.commit()
    conn.close()

def extract_text_from_pdf(filepath):
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def parse_results_with_ai(text):
    print("   🤖 Asking AI to extract results (this takes a few seconds)...")
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=f"{SYSTEM_PROMPT}\n\nDATA:\n{text[:50000]}", 
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"   [Error] AI extraction failed: {e}")
        return None

def safe_float(value):
    """Safely converts a value to float, returning 0.0 if None or invalid."""
    try:
        if value is None: return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def save_results_to_db(data):
    if isinstance(data, list):
        if len(data) > 0: data = data[0]
        else: return

    if 'meta' not in data:
        print(f"   [Error] JSON missing 'meta' key.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    
    raw_track = data['meta'].get('track_name', 'Unknown')
    raw_date = data['meta'].get('date', 'Unknown')
    
    clean_track = raw_track.lower().strip().replace(" ", "_").replace("gulfstr_eam", "gulfstream")
    
    updates = 0
    print(f"   Processing results for: {clean_track} on {raw_date}")

    for race in data.get('races', []):
        r_num = race.get('race_number')
        race_uuid = f"{clean_track}_{raw_date}_R{r_num}"
        
        try:
            cursor.execute("""
                INSERT INTO results (race_uuid, winner_number, second_number, third_number, win_payout, exacta_payout, trifecta_payout)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(race_uuid) DO UPDATE SET
                    winner_number=excluded.winner_number,
                    second_number=excluded.second_number,
                    third_number=excluded.third_number,
                    win_payout=excluded.win_payout,
                    exacta_payout=excluded.exacta_payout,
                    trifecta_payout=excluded.trifecta_payout
            """, (
                race_uuid,
                str(race.get('winner_pgm', '')),
                str(race.get('second_pgm', '')),
                str(race.get('third_pgm', '')),
                safe_float(race.get('win_payout')),     # Use safe_float wrapper
                safe_float(race.get('exacta_payout')),  # Use safe_float wrapper
                safe_float(race.get('trifecta_payout')) # Use safe_float wrapper
            ))
            updates += 1
            print(f"     ✅ Graded Race {r_num} (Winner: #{race.get('winner_pgm')} - Pay: ${safe_float(race.get('win_payout')):.2f})")
        except Exception as e:
            print(f"     ❌ Error saving Race {r_num}: {e}")

    conn.commit()
    conn.close()
    print(f"\n   🎉 Successfully graded {updates} races.")

def main():
    ensure_results_table() # This will now auto-fix your DB schema
    
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        return

    # Recursive search for PDFs
    files = glob.glob(os.path.join(RESULTS_DIR, "**/*.pdf"), recursive=True)
    
    for filename in files:
        print(f"\n📄 Reading: {filename}...")
        filepath = filename
        text = extract_text_from_pdf(filepath)
        data = parse_results_with_ai(text)
        if data:
            save_results_to_db(data)
            
            # Optional: Move processed files
            # new_path = filename.replace("results", "results/processed")
            # os.rename(filename, new_path)

if __name__ == "__main__":
    main()
