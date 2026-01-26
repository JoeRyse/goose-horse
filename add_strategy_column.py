import sqlite3

DB_FILE = "racing_ledger.db"

def upgrade_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE races ADD COLUMN betting_strategy TEXT")
        print("✅ Success: Added 'betting_strategy' column to races table.")
    except sqlite3.OperationalError:
        print("ℹ️  Column 'betting_strategy' already exists. No changes needed.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_db()