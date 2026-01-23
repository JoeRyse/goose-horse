import os
import time
import pandas as pd
import PyPDF2
import google.generativeai as genai
import json

# --- SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(BASE_DIR, "data", "history")
LOGIC_FILE = os.path.join(BASE_DIR, "logic", "master_system.md")
OUTPUT_FILE = os.path.join(BASE_DIR, "backtest_log.csv")

# --- API KEY LOADING ---
# Try loading from streamlit secrets if available, otherwise check env var
try:
    from streamlit.runtime.secrets import secrets
    if "GEMINI_API_KEY" in secrets:
        genai.configure(api_key=secrets["GEMINI_API_KEY"])
        print("✅ API Key loaded from Streamlit Secrets.")
except ImportError:
    # Fallback to environment variable or manual input
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        print("✅ API Key loaded from Environment Variable.")
    else:
        print("⚠️ No API Key found in secrets or env vars.")
        # Optional: Ask user for input if running interactively
        # api_key = input("Enter Gemini API Key: ")
        # genai.configure(api_key=api_key)

def analyze_backtest():
    # 1. Load System Logic
    if not os.path.exists(LOGIC_FILE):
        print(f"❌ Logic file not found at {LOGIC_FILE}")
        return

    with open(LOGIC_FILE, 'r', encoding='utf-8') as f:
        system_logic = f.read()

    # 2. Find PDFs
    if not os.path.exists(HISTORY_DIR):
        print(f"❌ History directory not found at {HISTORY_DIR}")
        return

    pdf_files = [f for f in os.listdir(HISTORY_DIR) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"ℹ️ No PDF files found in {HISTORY_DIR}")
        return

    print(f"🚀 Starting Backtest on {len(pdf_files)} Race Cards...")
    
    for pdf_file in pdf_files:
        print(f"Analyzing {pdf_file}...")
        path = os.path.join(HISTORY_DIR, pdf_file)
        
        try:
            # Read PDF
            reader = PyPDF2.PdfReader(path)
            text = "".join([page.extract_text() for page in reader.pages])
            
            # Call AI
            model = genai.GenerativeModel('gemini-1.5-pro-latest') # Use 1.5 Pro for faster batching
            prompt = f"{system_logic}\n\nSTRICT INSTRUCTION: Analyze this PAST race card. Return JSON.\n\nDATA:\n{text}"
            
            response = model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(clean_json)
            except json.JSONDecodeError:
                # Attempt rudimentary cleanup if JSON is messy
                clean_json = clean_json.split('{', 1)[1].rsplit('}', 1)[0]
                clean_json = '{' + clean_json + '}'
                data = json.loads(clean_json)

            # Extract Picks
            if 'races' in data:
                for race in data['races']:
                    picks = race.get('picks', {})
                    top = picks.get('top_pick', {})
                    val = picks.get('value_bet', {})
                    
                    row = {
                        "File": pdf_file,
                        "Track": data.get('meta', {}).get('track', 'Unknown'),
                        "Date": data.get('meta', {}).get('date', 'Unknown'),
                        "Race": race.get('number'),
                        "Top_Pick": f"#{top.get('number', '?')} {top.get('name', 'N/A')}",
                        "Rating": top.get('rating', '-'),
                        "Confidence": race.get('confidence_level', '-'),
                        "Value_Play": f"#{val.get('number', '?')} {val.get('name', 'N/A')}",
                        "Odds": val.get('odds', '-')
                    }
                    
                    # Save incrementally
                    df = pd.DataFrame([row])
                    header = not os.path.exists(OUTPUT_FILE)
                    df.to_csv(OUTPUT_FILE, mode='a', header=header, index=False)
            
            print(f"✅ Processed {pdf_file}")

        except Exception as e:
            print(f"❌ Error on {pdf_file}: {e}")
        
        time.sleep(2) # Prevent rate limits

    print(f"✅ Backtest Complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_backtest()
