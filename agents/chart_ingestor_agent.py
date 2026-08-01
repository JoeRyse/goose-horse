#!/usr/bin/env python3
"""
Official Equibase Chart & PDF Results Ingestor Agent
Ingests PDF race charts or OCR/text chart summaries, parses winning numbers and payouts,
and logs them directly into master_betting_history.db results table.
"""

import os
import re
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "logs", "master_betting_history.db")

def init_results_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            date TEXT,
            track TEXT,
            race_number TEXT,
            win_num TEXT,
            place_num TEXT,
            show_num TEXT,
            win_payout REAL DEFAULT 0.0,
            place_payout REAL DEFAULT 0.0,
            show_payout REAL DEFAULT 0.0,
            p2_place_payout REAL DEFAULT 0.0,
            p2_show_payout REAL DEFAULT 0.0,
            p3_show_payout REAL DEFAULT 0.0,
            exacta_payout REAL DEFAULT 0.0,
            trifecta_payout REAL DEFAULT 0.0,
            superfecta_payout REAL DEFAULT 0.0,
            scratches TEXT DEFAULT 'None',
            PRIMARY KEY (date, track, race_number)
        )
    """)
    conn.commit()
    conn.close()

def parse_equibase_chart_text(chart_text, default_track="Saratoga", default_date="2026-07-31"):
    """
    Parses OCR / PDF text of an Equibase chart page into structured result dict.
    """
    # 1. Parse Track, Date, Race #
    track_match = re.search(r"([A-Z\s]+)\s*-\s*([A-Za-z]+\s+\d+,\s*\d{4})\s*-\s*Race\s*(\d+)", chart_text, re.IGNORECASE)
    if track_match:
        track = track_match.group(1).strip().title()
        raw_date = track_match.group(2).strip()
        race_number = track_match.group(3).strip()
        try:
            date_dt = datetime.strptime(raw_date, "%B %d, %Y")
            date_str = date_dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = default_date
    else:
        track = default_track
        date_str = default_date
        race_num_match = re.search(r"Race\s*(\d+)", chart_text, re.IGNORECASE)
        race_number = race_num_match.group(1).strip() if race_num_match else "1"

    # 2. Parse Mutuel Payouts Table
    # Pattern e.g. "1 Wood Island 2.94 2.10" or "4 Unlock the Value 10.88 5.50 3.04"
    win_num, place_num, show_num = "", "", ""
    win_payout, place_payout, show_payout = 0.0, 0.0, 0.0
    exacta_payout, trifecta_payout, superfecta_payout = 0.0, 0.0, 0.0

    # Search for Pgm Horse Win Place Show rows
    # Example 1: 1 Wood Island 2.94 2.10
    # Example 2: 4 Unlock the Value 10.88 5.50 3.04
    runner_rows = re.findall(r"^\s*(\d+)\s+([A-Za-z0-9'\s\.\-]+?)\s+(\d+\.\d{2})(?:\s+(\d+\.\d{2}))?(?:\s+(\d+\.\d{2}))?", chart_text, re.MULTILINE)
    
    if runner_rows:
        # First row is 1st place winner
        win_num = runner_rows[0][0].strip()
        win_payout = float(runner_rows[0][2])
        if len(runner_rows[0]) > 3 and runner_rows[0][3]:
            place_payout = float(runner_rows[0][3])
            
        # Second row is 2nd place runner
        if len(runner_rows) > 1:
            place_num = runner_rows[1][0].strip()
            
        # Third row is 3rd place runner
        if len(runner_rows) > 2:
            show_num = runner_rows[2][0].strip()

    # Parse Wager Type Payoffs (Exacta, Trifecta, Superfecta)
    # e.g., "$1.00 Exacta 1-3 2.21" or "$1.00 Exacta 4-3 17.48"
    exacta_match = re.search(r"Exacta\s+[\d\-]+\s+(\d+\.\d{2})", chart_text, re.IGNORECASE)
    if exacta_match:
        exacta_payout = float(exacta_match.group(1))

    trifecta_match = re.search(r"Trifecta\s+[\d\-]+\s+(\d+\.\d{2})", chart_text, re.IGNORECASE)
    if trifecta_match:
        trifecta_payout = float(trifecta_match.group(1))

    superfecta_match = re.search(r"Superfecta\s+[\d\-]+\s+(\d+\.\d{2})", chart_text, re.IGNORECASE)
    if superfecta_match:
        superfecta_payout = float(superfecta_match.group(1))

    # Scratches
    scratches_match = re.search(r"Scratched Horse\(s\):\s*([^\n]+)", chart_text, re.IGNORECASE)
    scratches = scratches_match.group(1).strip() if scratches_match else "None"

    return {
        "date": date_str,
        "track": track,
        "race_number": race_number,
        "win_num": win_num,
        "place_num": place_num,
        "show_num": show_num,
        "win_payout": win_payout,
        "place_payout": place_payout,
        "show_payout": show_payout,
        "exacta_payout": exacta_payout,
        "trifecta_payout": trifecta_payout,
        "superfecta_payout": superfecta_payout,
        "scratches": scratches
    }

def ingest_chart_to_db(parsed_result):
    """
    Inserts or replaces the parsed result record in master_betting_history.db
    """
    init_results_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        INSERT OR REPLACE INTO results (
            date, track, race_number, win_num, place_num, show_num,
            win_payout, place_payout, show_payout, exacta_payout, trifecta_payout
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        parsed_result["date"],
        parsed_result["track"],
        parsed_result["race_number"],
        parsed_result["win_num"],
        parsed_result["place_num"],
        parsed_result["show_num"],
        parsed_result["win_payout"],
        parsed_result["place_payout"],
        parsed_result["show_payout"],
        parsed_result["exacta_payout"],
        parsed_result["trifecta_payout"]
    ))
    
    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    sample_ocr_page1 = """
    SARATOGA - July 31, 2026 - Race 1
    Total WPS Pool: $224,871
    Pgm Horse Win Place
    1 Wood Island 2.94 2.10
    3 Jackpot Jackie 2.14
    5 Mambo Jazz
    Wager Type Winning Numbers Payoff Pool
    $1.00 Exacta 1-3 2.21 112,259
    """
    
    res1 = parse_equibase_chart_text(sample_ocr_page1)
    print("Parsed Page 1 Sample:", res1)
    ingest_chart_to_db(res1)
    print("[SUCCESS] Ingested into database!")
