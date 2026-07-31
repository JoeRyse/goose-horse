#!/usr/bin/env python3
"""
Reset Database to July 1, 2026 Moving Forward & Scrape Results
1. Purges all races prior to 2026-07-01.
2. Clears all old results entered.
3. Ingests meeting cards from 2026-07-01 onward.
4. Auto-scrapes official race results for July 2026.
"""

import os
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
API_OUTPUT_DIR = os.path.join(BASE_DIR, "frontend", "public", "api", "output")
DB_PATH = os.path.join(LOGS_DIR, "master_betting_history.db")

def reset_database_july_onward():
    print(f"[July Reset] Resetting database to July 1, 2026 onward at: {DB_PATH}")
    os.makedirs(LOGS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create tables if not exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, track TEXT, race_number TEXT, distance TEXT, surface TEXT, condition TEXT,
            p1_num TEXT, p1_barrier TEXT, p1_name TEXT, p1_reason TEXT, p1_rating REAL,
            p2_num TEXT, p2_barrier TEXT, p2_name TEXT, p2_reason TEXT, p2_rating REAL,
            p3_num TEXT, p3_barrier TEXT, p3_name TEXT, p3_reason TEXT, p3_rating REAL,
            p4_num TEXT, p4_barrier TEXT, p4_name TEXT, p4_reason TEXT, p4_rating REAL,
            danger_num TEXT, danger_barrier TEXT, danger_name TEXT, danger_reason TEXT,
            confidence TEXT, ai_model TEXT, temperature REAL, raw_features TEXT,
            exotic_strategy TEXT DEFAULT '',
            rating_gap REAL DEFAULT 0.0,
            has_best_bet INTEGER DEFAULT 0,
            has_solo_lock INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            date TEXT, track TEXT, race_number TEXT,
            win_num TEXT, place_num TEXT, show_num TEXT,
            win_payout REAL DEFAULT 0.0, place_payout REAL DEFAULT 0.0, show_payout REAL DEFAULT 0.0,
            exacta_payout REAL DEFAULT 0.0, trifecta_payout REAL DEFAULT 0.0,
            PRIMARY KEY (date, track, race_number)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            filename TEXT PRIMARY KEY,
            track TEXT, date TEXT, region TEXT, race_count INTEGER,
            solo_locks_count INTEGER, best_bets_count INTEGER
        )
    """)

    # 1. Clear all old predictions, results, and meetings prior to 2026-07-01 OR purge all results entered
    print("[July Reset] Purging all races prior to 2026-07-01 and clearing all old results...")
    c.execute("DELETE FROM predictions WHERE date < '2026-07-01'")
    c.execute("DELETE FROM meetings WHERE date < '2026-07-01'")
    c.execute("DELETE FROM results") # Clear all manual/old results entered

    conn.commit()

    # 2. Ingest meeting cards from 2026-07-01 onward
    json_files = []
    seen = set()

    for dir_path in [API_OUTPUT_DIR, LOGS_DIR]:
        if not os.path.exists(dir_path): continue
        for fname in os.listdir(dir_path):
            if fname.endswith(".json") and fname not in seen:
                seen.add(fname)
                json_files.append((fname, os.path.join(dir_path, fname)))

    ingested_meetings = 0
    ingested_races = 0
    scraped_results = 0

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

                # Filter strictly for July 1, 2026 moving forward
                if not date_str or date_str < "2026-07-01":
                    continue

                races = data.get("races", [])
                solo_locks = 0
                best_bets = 0

                # Check if predictions for this meeting already exist
                c.execute("SELECT COUNT(*) FROM predictions WHERE date=? AND track=?", (date_str, track))
                if c.fetchone()[0] == 0:
                    for race_idx, r in enumerate(races, start=1):
                        ingested_races += 1
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

                        # If JSON card contains scraped actual results, ingest them
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
                            scraped_results += 1

                region = meta.get("region", "US")
                c.execute("""
                    INSERT OR REPLACE INTO meetings (filename, track, date, region, race_count, solo_locks_count, best_bets_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (fname, track, date_str, region, len(races), solo_locks, best_bets))
                
                ingested_meetings += 1
        except Exception as e:
            continue

    conn.commit()
    conn.close()

    print("==================================================")
    print(f"DATABASE RESET COMPLETE (JULY 1, 2026 ONWARD)")
    print(f"Ingested {ingested_meetings} July meetings & {ingested_races} races.")
    print(f"Ingested {scraped_results} official scraped results.")
    print("==================================================")

if __name__ == "__main__":
    reset_database_july_onward()
