import google.generativeai as genai
import os
import json
import time
import PyPDF2
from datetime import datetime

# --- CONFIG ---
# 1. ENTER YOUR API KEY HERE OR SET AS ENV VARIABLE
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("⚠️ API Key not found in environment variables.")
    API_KEY = input("👉 Please paste your Gemini API Key here: ").strip()

genai.configure(api_key=API_KEY)

# MODEL CONFIG
MODEL_NAME = "gemini-3-pro-preview" # Stable model
TEMP_DIR = "temp"
DATA_DIR = "data"
LOGS_DIR = "logs"
TRACK_DB_PATH = os.path.join(DATA_DIR, "track_db.json")

def load_track_db():
    try:
        with open(TRACK_DB_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def flatten_track_list(data):
    """Helper to find track data in nested DB"""
    tracks = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and "bias_notes" in v:
                tracks[k] = v
            elif isinstance(v, dict):
                tracks.update(flatten_track_list(v))
    return tracks

def clean_json(text):
    text = text.replace("```json", "").replace("```", "").strip()
    return text

def ingest_race_card():
    # 1. Find PDF
    pdf_files = [f for f in os.listdir(TEMP_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"❌ No PDF found in {TEMP_DIR}/. Please put a race card there.")
        return

    target_pdf = os.path.join(TEMP_DIR, pdf_files[0])
    print(f"📄 Found Race Card: {pdf_files[0]}")

    # 2. Extract Text
    print("⏳ Extracting text...")
    reader = PyPDF2.PdfReader(target_pdf)
    text_content = ""
    for page in reader.pages:
        text_content += page.extract_text() + "\n"

    # 3. Load Intelligence
    track_db = load_track_db()
    flat_tracks = flatten_track_list(track_db)
    
    # Try to auto-detect track name from filename or text
    detected_track = "Unknown"
    track_profile = "No specific profile found."
    
    print("🌍 Analyzing Track Profile...")
    for name, data in flat_tracks.items():
        if name.lower().replace("_", " ") in text_content.lower():
            detected_track = name
            track_profile = json.dumps(data, indent=2)
            print(f"✅ Auto-Detected Track: {name}")
            break
    
    if detected_track == "Unknown":
        print("⚠️ Could not auto-detect track from DB. Using Generic Logic.")

    # 4. Prompt AI
    print(f"🤖 Sending to {MODEL_NAME}...")
    
    system_prompt = f"""
    You are a Professional Handicapper.
    
    [TRACK INTELLIGENCE]
    Target Track: {detected_track}
    Profile Data: {track_profile}
    
    [INSTRUCTIONS]
    Analyze the provided race card text.
    Use the Track Intelligence to adjust your analysis (e.g., if Bias Notes say 'Speed Favoring', upgrade leaders).
    
    Return a JSON object containing:
    - meta: {{ track, date, condition }}
    - races: [ {{ number, distance, surface, selections: [{{number, name, reason}}], danger_horse, confidence_level, exotic_strategy }} ]
    """
    
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=system_prompt)
    
    try:
        response = model.generate_content(text_content)
        json_str = clean_json(response.text)
        data = json.loads(json_str)
        
        # 5. Save Results
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"{detected_track}_{timestamp}.json"
        save_path = os.path.join(LOGS_DIR, filename)
        
        with open(save_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        print(f"\n✅ Analysis Complete!")
        print(f"📂 Saved to: {save_path}")
        
        # Quick Preview
        for r in data.get('races', [])[:3]:
            print(f"   Race {r.get('number')}: Top Pick #{r['selections'][0]['number']} {r['selections'][0]['name']}")

    except Exception as e:
        print(f"\n❌ AI Error: {e}")
        # print(response.text) # Uncomment to debug raw output

if __name__ == "__main__":
    ingest_race_card()