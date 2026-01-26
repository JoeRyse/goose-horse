import sqlite3
import os
import re
from bs4 import BeautifulSoup

DB_FILE = "racing_ledger.db"
# Your specific path
LOGS_DIR = r"C:\Users\joery\OneDrive\Desktop\RacingAI\world-handicapper\docs\old"

def get_connection():
    return sqlite3.connect(DB_FILE)

def ensure_db_columns():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE races ADD COLUMN betting_strategy TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def clean_strategy_text(text):
    # Remove the label "BETTING STRATEGY:" and cleanup whitespace
    text = re.sub(r'BETTING STRATEGY:?', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def extract_horse_number(text):
    # Matches "#11" or "(11)" or just "11" at the start of a string
    match = re.search(r'[#\(]?(\d+)', text)
    if match: return match.group(1)
    return None

def import_html_data():
    ensure_db_columns()
    conn = get_connection()
    cursor = conn.cursor()

    if not os.path.exists(LOGS_DIR):
        print(f"Error: Directory not found: {LOGS_DIR}")
        return

    files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.html')]
    print(f"\nScanning {len(files)} HTML files in docs/old...")

    strat_updates = 0
    best_updates = 0

    for filename in files:
        filepath = os.path.join(LOGS_DIR, filename)
        
        # Parse Date from filename (Wagga_2026-01-26.html)
        try:
            name_parts = filename.replace('.html', '').split('_')
            date_part = name_parts[-1]
        except:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        races = soup.find_all('div', class_='race-section')
        
        for race_div in races:
            # 1. Identify Race Number
            header = race_div.find('div', class_='race-header')
            if not header: continue
            
            race_match = re.search(r'RACE\s+(\d+)', header.get_text(), re.IGNORECASE)
            if not race_match: continue
            race_num = int(race_match.group(1))

            # 2. Extract Betting Strategy (Text Search Method)
            strategy_label = race_div.find('b', string=re.compile('BETTING STRATEGY', re.IGNORECASE))
            if strategy_label and strategy_label.parent:
                raw_strat = strategy_label.parent.get_text()
                clean_strat = clean_strategy_text(raw_strat)
                
                cursor.execute("""
                    UPDATE races SET betting_strategy = ?
                    WHERE date = ? AND race_number = ?
                """, (clean_strat, date_part, race_num))
                if cursor.rowcount > 0: strat_updates += 1

            # 3. Extract Best Bets (The GOLD Highlight)
            # We look specifically for <div class="pick-box panel-best">
            best_panel = race_div.find('div', class_='panel-best')
            if best_panel:
                # The text usually looks like "🏁 BEST BET: #4 Horse Name"
                # We need to extract the number carefully.
                text_content = best_panel.get_text()
                
                # Regex to find the number after a '#'
                h_match = re.search(r'#(\d+)', text_content)
                if h_match:
                    h_num = h_match.group(1)
                    
                    # Update DB
                    cursor.execute("""
                        UPDATE predictions SET confidence_level = 'Best of Day'
                        WHERE horse_number = ? AND race_uuid IN (
                            SELECT race_uuid FROM races WHERE date = ? AND race_number = ?
                        )
                    """, (h_num, date_part, race_num))
                    if cursor.rowcount > 0: best_updates += 1

    conn.commit()
    conn.close()
    print(f"\nImport Complete.")
    print(f"  - Strategies Imported: {strat_updates}")
    print(f"  - Gold 'Best Bets' Tagged: {best_updates}")

if __name__ == "__main__":
    import_html_data()