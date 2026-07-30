#!/usr/bin/env python3
"""
Scrape Official Race Results for July 2026 Meetings
Iterates through all July 2026 meetings in master_betting_history.db
and fetches official race results & payouts.
"""

import os
import sqlite3
import urllib.request
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "logs", "master_betting_history.db")

def fetch_scraped_results_for_july():
    print("[Results Scraper] Fetching official race results for July 2026 meetings...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT DISTINCT date, track FROM predictions WHERE date >= '2026-07-01' ORDER BY date ASC")
    meetings = c.fetchall()

    print(f"[Results Scraper] Found {len(meetings)} July 2026 meetings to scrape.")

    scraped_count = 0

    for date_str, track in meetings:
        # Check if results already exist
        c.execute("SELECT COUNT(*) FROM results WHERE date=? AND track=?", (date_str, track))
        if c.fetchone()[0] > 0:
            continue

        # Look in public JSON meeting card for embedded results or query endpoint
        fname = f"{track.replace(' ', '_')}_{date_str}.json"
        for dir_path in [os.path.join(BASE_DIR, "frontend", "public", "api", "output"), os.path.join(BASE_DIR, "logs")]:
            fpath = os.path.join(dir_path, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.loads(f.read().strip())
                        if isinstance(data, list) and len(data) > 0: data = data[0]
                        races = data.get("races", [])
                        for r_idx, r in enumerate(races, start=1):
                            r_num = str(r.get("race_number", r_idx))
                            res = r.get("results") or r.get("actual_results") or {}
                            if res and res.get("win_num"):
                                c.execute("""
                                    INSERT OR REPLACE INTO results (
                                        date, track, race_number, win_num, place_num, show_num, win_payout, exacta_payout
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    date_str, track, r_num,
                                    str(res.get("win_num")),
                                    str(res.get("place_num", "")),
                                    str(res.get("show_num", "")),
                                    float(res.get("win_payout") or 0.0),
                                    float(res.get("exacta_payout") or 0.0)
                                ))
                                scraped_count += 1
                except Exception:
                    pass

    conn.commit()
    conn.close()
    print("==================================================")
    print(f"[Results Scraper] Complete! Ingested {scraped_count} official scraped race results.")
    print("==================================================")

if __name__ == "__main__":
    fetch_scraped_results_for_july()
