import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "master_betting_history.db")

def upgrade_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add a new column to store the raw JSON features
        cursor.execute("ALTER TABLE predictions ADD COLUMN raw_features TEXT")
        print("✅ Success: Added 'raw_features' column to the predictions table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ The 'raw_features' column already exists. You are good to go!")
        else:
            print(f"⚠️ Error: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_database()