import sqlite3
import json

DB_PATH = 'logs/master_betting_history.db'

def repair_and_backfill():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("1. Checking database columns...")
    # Ensure exotic_strategy exists in predictions
    c.execute("PRAGMA table_info(predictions)")
    cols = [col[1] for col in c.fetchall()]
    if "exotic_strategy" not in cols:
        c.execute("ALTER TABLE predictions ADD COLUMN exotic_strategy TEXT DEFAULT ''")
        print("   -> Added 'exotic_strategy' column to predictions table.")

    # Ensure all payout columns exist in results
    c.execute("PRAGMA table_info(results)")
    res_cols = [col[1] for col in c.fetchall()]
    needed_res_cols = [
        ("win_payout", "REAL DEFAULT 0.0"),
        ("place_payout", "REAL DEFAULT 0.0"),
        ("show_payout", "REAL DEFAULT 0.0"),
        ("p2_place_payout", "REAL DEFAULT 0.0"),
        ("p2_show_payout", "REAL DEFAULT 0.0"),
        ("p3_show_payout", "REAL DEFAULT 0.0"),
        ("exacta_payout", "REAL DEFAULT 0.0"),
        ("trifecta_payout", "REAL DEFAULT 0.0"),
        ("superfecta_payout", "REAL DEFAULT 0.0"),
        ("scratches", "TEXT DEFAULT 'None'")
    ]
    for col_name, col_type in needed_res_cols:
        if col_name not in res_cols:
            c.execute(f"ALTER TABLE results ADD COLUMN {col_name} {col_type}")

    conn.commit()

    print("2. Backfilling 'exotic_strategy' for past predictions...")
    rows = c.execute("SELECT id, raw_features, exotic_strategy FROM predictions").fetchall()
    updated_count = 0

    for row_id, raw_feat, current_strat in rows:
        strat_to_save = ""
        # Try to extract strategy from raw_features blob if current column is empty
        if raw_feat:
            try:
                # Fix single quote JSON formatting if present
                clean_blob = raw_feat.replace("'", '"').replace("True", "true").replace("False", "false")
                parsed = json.loads(clean_blob)
                if isinstance(parsed, dict):
                    strat_to_save = str(parsed.get("exotic_strategy", ""))
            except Exception:
                # Fallback regex if JSON parsing fails
                if "exotic_strategy" in raw_feat:
                    strat_to_save = raw_feat

        # Clean out any rogue #$ typos
        strat_to_save = strat_to_save.replace("#$", "#")
        
        # If strategy found, update the database record
        if strat_to_save:
            c.execute("UPDATE predictions SET exotic_strategy = ? WHERE id = ?", (strat_to_save, row_id))
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Success! Backfilled and updated {updated_count} prediction rows.")

if __name__ == "__main__":
    repair_and_backfill()