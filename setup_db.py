import sqlite3
import os

DB_FILE = "racing_ledger.db"

def create_tables():
    if os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} already exists.")
        # Optional: Ask to overwrite or just append/update. We'll leave it to avoid data loss.
    else:
        print(f"Creating new database: {DB_FILE}")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # --- RACES TABLE ---
    # Stores metadata about the race event
    c.execute('''
        CREATE TABLE IF NOT EXISTS races (
            race_uuid TEXT PRIMARY KEY,
            track TEXT NOT NULL,
            date TEXT NOT NULL,
            race_number INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(track, date, race_number)
        )
    ''')

    # --- PREDICTIONS TABLE ---
    # Stores the AI's analysis for each contender
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_uuid TEXT NOT NULL,
            horse_number TEXT,
            horse_name TEXT,
            rating INTEGER,
            rank_prediction TEXT, -- e.g., "Top Pick", "Danger", "Value", "Contender"
            confidence_level TEXT,
            reasoning TEXT,
            FOREIGN KEY (race_uuid) REFERENCES races (race_uuid)
        )
    ''')

    # --- RESULTS TABLE ---
    # Stores the actual outcome and payouts
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_uuid TEXT NOT NULL,
            winner_number TEXT,
            second_number TEXT,
            third_number TEXT,
            win_payout REAL,
            exacta_payout REAL,
            trifecta_payout REAL,
            FOREIGN KEY (race_uuid) REFERENCES races (race_uuid)
        )
    ''')

    conn.commit()
    conn.close()
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()
