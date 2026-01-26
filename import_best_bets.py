import sqlite3
import os
import re
from bs4 import BeautifulSoup

DB_FILE = "racing_ledger.db"
LOGS_DIR = "logs"

def get_connection():
    return sqlite3.connect(DB_FILE)

def clean_strategy_text(text):
    # Removes "BETTING STRATEGY:" prefix and extra whitespace
    text = re.sub(r'BETTING STRATEGY:?', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def extract_horse_number(text):
    match = re.search(r'[#\(](\d+)', text)
    if match: return match.group(1)
    return None

def import_html_data():
    conn = get_connection()
    cursor = conn.cursor()

    files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.html')]
    
    if not files:
        print(f"No .html files found in {LOGS_DIR}.")
        return

    print(f"\nScanning {len(files)} HTML files for Strategies & Best Bets...")

    for filename in files:
        filepath = os.path.join(LOGS_DIR, filename)
        
        # Parse Filename (Format: Track_Date.html)
        try:
            name_parts = filename.replace('.html', '').split('_')
            date_part = name_parts[-1]
            # Reconstruct track name (e.g. "Gulfstream Park")
            track_part = " ".join(name_parts[:-1]).replace("-", " ") 
        except:
            print(f"Skipping {filename} (Unknown naming format)")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        races = soup.find_all('div', class_='race-section')
        strat_updates = 0
        best_updates = 0
        
        for race_div in races:
            # 1. Identify Race
            header = race_div.find('div', class_='race-header')
            if not header: continue
            
            race_match = re.search(r'RACE\s+(\d+)', header.get_text(), re.IGNORECASE)
            if not race_match: continue
            race_num = int(race_match.group(1))

            # 2. Extract Betting Strategy
            # Look for <div class="exacta-box">
            strat_box = race_div.find('div', class_='exacta-box')
            if strat_box:
                raw_strat = strat_box.get_text()
                clean_strat = clean_strategy_text(raw_strat)
                
                # Save to Database
                cursor.execute("""
                    UPDATE races 
                    SET betting_strategy = ?
                    WHERE date = ? AND race_number = ?
                """, (clean_strat, date_part, race_num))
                
                if cursor.rowcount > 0:
                    strat_updates += 1

            # 3. Extract Best Bets (Yellow Panel)
            best_panel = race_div.find('div', class_='panel-best')
            if best_panel:
                h_num = extract_horse_number(best_panel.get_text())
                if h_num:
                    cursor.execute("""
                        UPDATE predictions SET confidence_level = 'Best of Day'
                        WHERE horse_number = ? AND race_uuid IN (
                            SELECT race_uuid FROM races WHERE date = ? AND race_number = ?
                        )
                    """, (h_num, date_part, race_num))
                    if cursor.rowcount > 0: best_updates += 1

    conn.commit()
    conn.close()
    print(f"\nSummary for {date_part}:")
    print(f"  - Strategies Imported: {strat_updates}")
    print(f"  - Best Bets Tagged:    {best_updates}")

if __name__ == "__main__":
    import_html_data()