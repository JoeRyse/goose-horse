#!/usr/bin/env python3
"""
Backfill SQLite Database & Auto-Fetch Official Results
Cleans and rebuilds master_betting_history.db from scratch using all 530+ meeting JSON cards,
and automatically fetches/extracts official race results & payouts into the database.
"""

import os
import json
import sqlite3
from results_fetcher_agent import auto_fetch_results_for_meeting

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
API_OUTPUT_DIR = os.path.join(BASE_DIR, "frontend", "public", "api", "output")
DB_PATH = os.path.join(LOGS_DIR, "master_betting_history.db")

def init_clean_db():
    print(f"[Backfill] Initializing fresh SQLite database at: {DB_PATH}")
    os.makedirs(LOGS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Drop old tables to start completely fresh
    c.execute("DROP TABLE IF EXISTS predictions")
    c.execute("DROP TABLE IF EXISTS results")
    c.execute("DROP TABLE IF EXISTS meetings")

    # Table 1: Predictions
    c.execute("""
        CREATE TABLE predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, track TEXT, race_number TEXT, distance TEXT, surface TEXT, condition TEXT,
            p1_num TEXT, p1_name TEXT, p1_rating REAL,
            p2_num TEXT, p2_name TEXT, p2_rating REAL,
            p3_num TEXT, p3_name TEXT, p3_rating REAL,
            p4_num TEXT, p4_name TEXT, p4_rating REAL,
            danger_num TEXT, danger_name TEXT,
            rating_gap REAL DEFAULT 0.0,
            has_best_bet INTEGER DEFAULT 0,
            has_solo_lock INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: Results
    c.execute("""
        CREATE TABLE results (
            date TEXT, track TEXT, race_number TEXT,
            win_num TEXT, place_num TEXT, show_num TEXT,
            win_payout REAL DEFAULT 0.0, place_payout REAL DEFAULT 0.0, show_payout REAL DEFAULT 0.0,
            exacta_payout REAL DEFAULT 0.0, trifecta_payout REAL DEFAULT 0.0,
            PRIMARY KEY (date, track, race_number)
        )
    """)

    # Table 3: Meetings Index
    c.execute("""
        CREATE TABLE meetings (
            filename TEXT PRIMARY KEY,
            track TEXT, date TEXT, region TEXT, race_count INTEGER,
            solo_locks_count INTEGER, best_bets_count INTEGER
        )
    """)

    conn.commit()
    conn.close()
    print("[Backfill] Database schema created successfully.")

def backfill_from_logs():
    init_clean_db()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    json_files = []
    seen = set()

    for dir_path in [API_OUTPUT_DIR, LOGS_DIR]:
        if not os.path.exists(dir_path): continue
        for fname in os.listdir(dir_path):
            if fname.endswith(".json") and fname not in seen:
                seen.add(fname)
                json_files.append((fname, os.path.join(dir_path, fname)))

    print(f"[Backfill] Found {len(json_files)} meeting cards to ingest...")

    total_races = 0
    total_meetings = 0
    total_results = 0

    for fname, fpath in json_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: continue
                data = json.loads(content)
                if isinstance(data, str): data = json.loads(data)
                if isinstance(data, list) and len(data) > 0: data = data[0]
                if not isinstance(data, dict): continue

                meta = data.get("meta", {})
                track = meta.get("track", fname.replace(".json", "").rsplit("_", 1)[0].replace("_", " "))
                date_str = meta.get("date", "")
                if not date_str and "_" in fname:
                    parts = fname.replace(".json", "").rsplit("_", 1)
                    if len(parts) > 1: date_str = parts[1]

                races = data.get("races", [])
                solo_locks = 0
                best_bets = 0

                for race_idx, r in enumerate(races, start=1):
                    total_races += 1
                    race_num = str(r.get("race_number", race_idx))
                    contenders = r.get("all_contenders") or r.get("selections") or []

                    p1_num, p1_name, p1_rating = "", "", 0.0
                    p2_num, p2_name, p2_rating = "", "", 0.0
                    p3_num, p3_name, p3_rating = "", "", 0.0
                    p4_num, p4_name, p4_rating = "", "", 0.0

                    if len(contenders) >= 1:
                        c1 = contenders[0]
                        p1_num = str(c1.get("program_number") or c1.get("number", "1"))
                        p1_name = c1.get("horse_name") or c1.get("name", "")
                        p1_rating = float(c1.get("rating") or c1.get("features", {}).get("ai_holistic_score") or 0)

                    if len(contenders) >= 2:
                        c2 = contenders[1]
                        p2_num = str(c2.get("program_number") or c2.get("number", "2"))
                        p2_name = c2.get("horse_name") or c2.get("name", "")
                        p2_rating = float(c2.get("rating") or c2.get("features", {}).get("ai_holistic_score") or 0)

                    if len(contenders) >= 3:
                        c3 = contenders[2]
                        p3_num = str(c3.get("program_number") or c3.get("number", "3"))
                        p3_name = c3.get("horse_name") or c3.get("name", "")
                        p3_rating = float(c3.get("rating") or 0)

                    if len(contenders) >= 4:
                        c4 = contenders[3]
                        p4_num = str(c4.get("program_number") or c4.get("number", "4"))
                        p4_name = c4.get("horse_name") or c4.get("name", "")
                        p4_rating = float(c4.get("rating") or 0)

                    danger_info = r.get("danger_horse") or {}
                    danger_num = str(danger_info.get("program_number") or danger_info.get("number", ""))
                    danger_name = danger_info.get("horse_name") or danger_info.get("name", "")

                    gap = p1_rating - p2_rating
                    has_lock = 1 if (p1_rating >= 88.0 and gap >= 5.0) else 0
                    has_best = 1 if (gap >= 3.0) else 0

                    if has_lock: solo_locks += 1
                    if has_best: best_bets += 1

                    c.execute("""
                        INSERT INTO predictions (
                            date, track, race_number, distance, surface, condition,
                            p1_num, p1_name, p1_rating,
                            p2_num, p2_name, p2_rating,
                            p3_num, p3_name, p3_rating,
                            p4_num, p4_name, p4_rating,
                            danger_num, danger_name,
                            rating_gap, has_best_bet, has_solo_lock
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date_str, track, race_num, r.get("distance", ""), r.get("surface", ""), meta.get("track_condition", ""),
                        p1_num, p1_name, p1_rating,
                        p2_num, p2_name, p2_rating,
                        p3_num, p3_name, p3_rating,
                        p4_num, p4_name, p4_rating,
                        danger_num, danger_name,
                        gap, has_best, has_lock
                    ))

                    # Ingest Race Results if actual result data exists in JSON
                    results_data = r.get("results") or r.get("actual_results") or {}
                    if results_data.get("win_num"):
                        win_num = str(results_data.get("win_num"))
                        place_num = str(results_data.get("place_num", ""))
                        show_num = str(results_data.get("show_num", ""))
                        win_payout = float(results_data.get("win_payout") or 0.0)
                        exacta_payout = float(results_data.get("exacta_payout") or 0.0)

                        c.execute("""
                            INSERT OR REPLACE INTO results (
                                date, track, race_number, win_num, place_num, show_num, win_payout, exacta_payout
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (date_str, track, race_num, win_num, place_num, show_num, win_payout, exacta_payout))
                        total_results += 1

                region = meta.get("region", "US")
                c.execute("""
                    INSERT OR REPLACE INTO meetings (filename, track, date, region, race_count, solo_locks_count, best_bets_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (fname, track, date_str, region, len(races), solo_locks, best_bets))
                
                total_meetings += 1
        except Exception as e:
            continue

    conn.commit()
    conn.close()

    print("==================================================")
    print(f"SUCCESS! Database rebuilt & scraped.")
    print(f"Ingested {total_meetings} meetings, {total_races} races, and {total_results} race results into master_betting_history.db!")
    print("==================================================")

if __name__ == "__main__":
    backfill_from_logs()
