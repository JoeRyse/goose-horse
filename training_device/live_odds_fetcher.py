#!/usr/bin/env python3
"""
Standalone Live Odds & Race Status Fetcher
Fetches free TAB Australia live racing feeds and Equibase public chart URLs.
Zero-cost: No API keys or paid subscriptions required.
"""

import urllib.request
import json
from datetime import datetime

TAB_MEETINGS_URL = "https://api.tab.com.au/v1/tab-info-service/racing/dates/{date}/meetings?jurisdiction=VIC"
TAB_RACE_URL = "https://api.tab.com.au/v1/tab-info-service/racing/dates/{date}/meetings/{meeting_id}/races/{race_num}"
EQUIBASE_SUMMARY_BASE = "https://www.equibase.com/static/chart/summary/"

TRACK_CODES_US = {
    "saratoga": "SAR",
    "del mar": "DMR",
    "gulfstream park": "GP",
    "keeneland": "KEE",
    "churchill downs": "CD",
    "aqueduct": "AQU",
    "belmont park": "BEL",
    "monmouth park": "MTH",
    "woodbine": "WO"
}

def fetch_live_tab_meetings(date_str=None):
    """
    Fetches live Australian race meetings from free TAB Australia API.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    url = TAB_MEETINGS_URL.format(date=date_str)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode('utf-8'))
                meetings = payload.get("meetings", [])
                
                parsed_meetings = []
                for m in meetings:
                    parsed_meetings.append({
                        "meeting_id": m.get("meetingId"),
                        "name": m.get("meetingName"),
                        "mnemonic": m.get("venueMnemonic"),
                        "location": m.get("location"),
                        "race_type": m.get("raceType"),
                        "race_count": len(m.get("races", [])),
                        "races": m.get("races", [])
                    })
                return parsed_meetings
    except Exception as e:
        pass
    return []

def get_equibase_chart_url(track_name, date_str=None):
    """
    Constructs free official Equibase summary chart URL for US races.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    clean_track = track_name.lower().strip()
    code = TRACK_CODES_US.get(clean_track, clean_track[:3].upper())
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        mmddyy = dt.strftime("%m%d%y")
    except Exception:
        mmddyy = date_str.replace("-", "")[4:] + date_str[:4][2:]
        
    return f"{EQUIBASE_SUMMARY_BASE}{code}{mmddyy}USA-EQB.html"

if __name__ == "__main__":
    print("Testing TAB Australia Live Racing API...")
    meetings = fetch_live_tab_meetings()
    print(f"Fetched {len(meetings)} live AU meetings.")
    print("Equibase Del Mar Chart URL:", get_equibase_chart_url("Del Mar", "2026-07-30"))
