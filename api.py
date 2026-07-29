import http.server
import socketserver
import json
import os
import sqlite3
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
API_OUTPUT_DIR = os.path.join(BASE_DIR, "api", "output")
DB_PATH = os.path.join(LOGS_DIR, "master_betting_history.db")
DEFAULT_PIN = os.environ.get("EXACTA_PIN", "7777")

for d in [LOGS_DIR, API_OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

# Helper function to detect region based on track name
def get_region_for_track(track_name):
    t = track_name.lower()
    if any(k in t for k in ["ascot_uk", "goodwood", "redcar", "wolverhampton", "leicester", "carlisle", "kempton"]):
        return "UK"
    elif any(k in t for k in ["albury", "ascot", "balaklava", "ballarat", "ballina", "bathurst", "belmont_park_wa", 
                            "broome", "bunbury", "cairns", "canberra", "canterbury", "caulfield", "doomben", 
                            "eagle_farm", "echuca", "flemington", "gold_coast", "gosford", "goulburn", "grafton",
                            "hawkesbury", "ipswich", "kalgoorlie", "kembla", "morphettville", "murray", "newcastle",
                            "rosehill", "randwick", "sandown", "sunshine", "tamworth", "taree", "wagga", "wyong"]):
        return "AUS"
    elif any(k in t for k in ["busan", "seoul", "funabashi", "kawasaki", "mombetsu", "nagoya", "tokyo_city", "happy_valley", "sha_tin"]):
        return "ASIA"
    elif any(k in t for k in ["hoosier", "meadowlands", "monticello", "northfield", "saratoga_harness", "yonkers", "woodbine_mohawk"]):
        return "HARNESS"
    else:
        return "USA"

def compute_race_exotics_suggestions(contenders):
    if not contenders or len(contenders) < 2:
        return []

    c_nums = [str(c.get("number") or c.get("program_number") or "") for c in contenders if (c.get("number") or c.get("program_number"))]
    if len(c_nums) < 2:
        return []

    top_1 = c_nums[0]
    top_2 = c_nums[1]
    top_3 = c_nums[2] if len(c_nums) > 2 else c_nums[1]
    top_4 = c_nums[3] if len(c_nums) > 3 else top_3

    suggestions = []

    # 1. Exacta Box
    box_horses = ", ".join([f"#{n}" for n in c_nums[:3]])
    suggestions.append({
        "type": "Exacta Box",
        "ticket": f"$2 Exacta Box: {box_horses}",
        "cost": "$12.00 (6 combos)" if len(c_nums) >= 3 else "$4.00 (2 combos)",
        "icon": "🎟️"
    })

    # 2. Exacta Key
    key_under = ", ".join([f"#{n}" for n in c_nums[1:3]])
    suggestions.append({
        "type": "Exacta Key",
        "ticket": f"$2 Exacta Key: #{top_1} over {key_under}",
        "cost": "$4.00 (2 combos)",
        "icon": "🔑"
    })

    # 3. Trifecta Key
    if len(c_nums) >= 3:
        tri_under = ", ".join([f"#{n}" for n in c_nums[1:4]])
        suggestions.append({
            "type": "Trifecta Key",
            "ticket": f"$1 Trifecta Key: #{top_1} over #{top_2}, #{top_3} over {tri_under}",
            "cost": "$4.00 (4 combos)",
            "icon": "💎"
        })

    # 4. 10c Superfecta
    if len(c_nums) >= 4:
        suggestions.append({
            "type": "10c Superfecta Wheel",
            "ticket": f"10c Superfecta: #{top_1} / #{top_2}, #{top_3} / #{top_2}, #{top_3}, #{top_4} / ALL",
            "cost": "$2.40 (24 combos)",
            "icon": "⚡"
        })

    return suggestions

def compute_race_enrichments(races):
    enriched = []
    for race in races:
        race_copy = dict(race)
        contenders = race_copy.get("all_contenders") or race_copy.get("selections") or []
        
        # Calculate rating gap between top 2 horses
        sorted_contenders = sorted(contenders, key=lambda x: float(x.get("rating", 0)), reverse=True)
        top_rating = float(sorted_contenders[0].get("rating", 0)) if len(sorted_contenders) > 0 else 0
        second_rating = float(sorted_contenders[1].get("rating", 0)) if len(sorted_contenders) > 1 else 0
        gap = round(top_rating - second_rating, 1)
        
        enriched_contenders = []
        for i, c in enumerate(sorted_contenders):
            c_copy = dict(c)
            r = float(c_copy.get("rating", 0))
            is_top = (i == 0)
            
            c_copy["is_solo_lock"] = is_top and (r >= 90.0) and (gap >= 5.0)
            c_copy["is_best_bet"] = is_top and (gap >= 3.0) and not c_copy["is_solo_lock"]
            c_copy["win_lock_amount"] = 25.0 if is_top and (r >= 85.0 or gap >= 3.0) else 0.0
            c_copy["gap_to_next"] = gap if is_top else 0.0
            enriched_contenders.append(c_copy)
            
        race_copy["all_contenders"] = enriched_contenders
        race_copy["rating_gap"] = gap
        race_copy["has_solo_lock"] = any(c.get("is_solo_lock") for c in enriched_contenders)
        race_copy["has_best_bet"] = any(c.get("is_best_bet") for c in enriched_contenders)
        race_copy["exotic_suggestions"] = compute_race_exotics_suggestions(enriched_contenders)
        enriched.append(race_copy)
    return enriched

def compute_exotic_tickets(races):
    race_legs = {}
    for r in races:
        r_num = r.get("number") or 1
        contenders = r.get("all_contenders") or r.get("selections") or []
        
        parsed_c = []
        for c in contenders:
            if isinstance(c, dict):
                num = str(c.get("number") or c.get("program_number") or "")
                rating = float(c.get("rating") or c.get("features", {}).get("ai_holistic_score", 0) or 0)
                name = c.get("name") or c.get("horse_name") or ""
            elif isinstance(c, str):
                num = ""
                rating = 75.0
                name = ""
                m_num = re.search(r"number[:=](\w+)", c)
                if m_num: num = m_num.group(1)
                m_rat = re.search(r"rating[:=]([\d\.]+)", c)
                if m_rat: rating = float(m_rat.group(1))
            else:
                continue
            if num:
                parsed_c.append({"number": num, "rating": rating, "name": name})

        sorted_c = sorted(parsed_c, key=lambda x: x["rating"], reverse=True)
        if not sorted_c:
            continue
        
        top_r = sorted_c[0]["rating"]
        r2_r = sorted_c[1]["rating"] if len(sorted_c) > 1 else 0
        gap = top_r - r2_r
        
        if top_r >= 90.0 and gap >= 5.0:
            # Single Lock Anchor
            leg_horses = [f"#{sorted_c[0]['number']} (SOLO LOCK)"]
        else:
            # Multi-horse spread (top 2 or 3)
            cutoff = 2 if len(sorted_c) >= 2 else 1
            if len(sorted_c) >= 3 and (sorted_c[1]["rating"] - sorted_c[2]["rating"]) < 2.0:
                cutoff = 3
            leg_horses = [f"#{c['number']}" for c in sorted_c[:cutoff]]
        
        race_legs[r_num] = ", ".join(leg_horses)

    race_nums = sorted(race_legs.keys())
    n = len(race_nums)
    if n == 0:
        return {}

    exotics = {
        "daily_doubles": [],
        "pick_3": [],
        "pick_4": [],
        "pick_5": [],
        "pick_6": []
    }

    # Daily Doubles (consecutive pairs)
    for i in range(n - 1):
        r1, r2 = race_nums[i], race_nums[i+1]
        exotics["daily_doubles"].append(f"R{r1}-R{r2} Double: R{r1} [{race_legs[r1]}] / R{r2} [{race_legs[r2]}]")

    # Pick 3
    for i in range(n - 2):
        r1, r2, r3 = race_nums[i], race_nums[i+1], race_nums[i+2]
        exotics["pick_3"].append(f"Pick 3 (R{r1}-R{r3}): R{r1} [{race_legs[r1]}] / R{r2} [{race_legs[r2]}] / R{r3} [{race_legs[r3]}]")

    # Pick 4
    for i in range(n - 3):
        r1, r2, r3, r4 = race_nums[i], race_nums[i+1], race_nums[i+2], race_nums[i+3]
        exotics["pick_4"].append(f"Pick 4 (R{r1}-R{r4}): R{r1} [{race_legs[r1]}] / R{r2} [{race_legs[r2]}] / R{r3} [{race_legs[r3]}] / R{r4} [{race_legs[r4]}]")

    # Pick 5
    for i in range(n - 4):
        r1, r2, r3, r4, r5 = race_nums[i], race_nums[i+1], race_nums[i+2], race_nums[i+3], race_nums[i+4]
        exotics["pick_5"].append(f"Pick 5 (R{r1}-R{r5}): R{r1} [{race_legs[r1]}] / R{r2} [{race_legs[r2]}] / R{r3} [{race_legs[r3]}] / R{r4} [{race_legs[r4]}] / R{r5} [{race_legs[r5]}]")

    # Pick 6
    for i in range(n - 5):
        r1, r2, r3, r4, r5, r6 = race_nums[i], race_nums[i+1], race_nums[i+2], race_nums[i+3], race_nums[i+4], race_nums[i+5]
        exotics["pick_6"].append(f"Pick 6 (R{r1}-R{r6}): R{r1} [{race_legs[r1]}] / R{r2} [{race_legs[r2]}] / R{r3} [{race_legs[r3]}] / R{r4} [{race_legs[r4]}] / R{r5} [{race_legs[r5]}] / R{r6} [{race_legs[r6]}]")

    return exotics

class ExactaAPIHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data, code=200):
        self.send_response(code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # 1. GET /api/meetings
        if path == "/api/meetings" or path == "/api/output":
            meetings = []
            seen_files = set()
            
            # Check docs/meetings for currently published cards
            published_files = set()
            docs_meetings_dir = os.path.join(BASE_DIR, "docs", "meetings")
            if os.path.exists(docs_meetings_dir):
                for f in os.listdir(docs_meetings_dir):
                    if f.endswith(".html"):
                        published_files.add(f.replace(".html", ".json"))
            
            # Look in both api/output and logs
            for dir_path in [API_OUTPUT_DIR, LOGS_DIR]:
                if not os.path.exists(dir_path): continue
                for fname in os.listdir(dir_path):
                    if not fname.endswith(".json") or fname in seen_files:
                        continue
                    seen_files.add(fname)
                    
                    filepath = os.path.join(dir_path, fname)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
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
                            enriched_races = compute_race_enrichments(races)
                            
                            solo_locks = sum(1 for r in enriched_races if r.get("has_solo_lock"))
                            best_bets = sum(1 for r in enriched_races if r.get("has_best_bet"))
                            region = meta.get("region") or get_region_for_track(track)
                            is_published = (fname in published_files)
                            
                            meetings.append({
                                "id": fname,
                                "filename": fname,
                                "track": track,
                                "date": date_str,
                                "track_condition": meta.get("track_condition", "Standard"),
                                "race_count": len(races),
                                "solo_locks_count": solo_locks,
                                "best_bets_count": best_bets,
                                "region": region,
                                "is_published": is_published,
                                "last_modified": os.path.getmtime(filepath)
                            })
                    except Exception as e:
                        continue

            # Sort: published first, then newest date
            meetings.sort(key=lambda x: (1 if x.get("is_published") else 0, x.get("date", ""), x.get("last_modified", 0)), reverse=True)
            return self._send_json({"status": "success", "meetings": meetings})

        # 2. GET /api/output/{filename}
        elif path.startswith("/api/output/") or path.startswith("/api/meetings/"):
            fname = path.split("/")[-1]
            if not fname.endswith(".json"):
                fname += ".json"
                
            filepath = os.path.join(API_OUTPUT_DIR, fname)
            if not os.path.exists(filepath):
                filepath = os.path.join(LOGS_DIR, fname)
                
            if not os.path.exists(filepath):
                return self._send_json({"error": "Meeting not found"}, 404)
                
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                    if isinstance(data, str): data = json.loads(data)
                    if isinstance(data, list) and len(data) > 0: data = data[0]
                    
                    # Enrich races with gap and lock properties
                    if "races" in data:
                        data["races"] = compute_race_enrichments(data["races"])
                        data["exotic_tickets"] = compute_exotic_tickets(data["races"])
                    if "meta" in data and "region" not in data["meta"]:
                        data["meta"]["region"] = get_region_for_track(data["meta"].get("track", ""))
                        
                    return self._send_json({"status": "success", "data": data})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        # 3. GET /api/stats
        elif path == "/api/stats":
            try:
                if not os.path.exists(DB_PATH):
                    return self._send_json({"status": "success", "stats": {"total_bets": 0, "total_staked": 0.0, "total_payout": 0.0, "roi": 0.0, "win_rate": 0.0}})
                    
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                c.execute("SELECT COUNT(*), SUM(win_paid) FROM selections WHERE finish_position IS NOT NULL")
                row = c.fetchone()
                total_settled = row[0] or 0
                total_payout = row[1] or 0.0
                
                c.execute("SELECT COUNT(*) FROM selections WHERE finish_position = 1")
                total_wins = c.fetchone()[0] or 0
                
                win_rate = round((total_wins / total_settled * 100), 1) if total_settled > 0 else 0.0
                
                conn.close()
                return self._send_json({
                    "status": "success",
                    "stats": {
                        "total_bets": total_settled,
                        "wins": total_wins,
                        "total_payout": round(total_payout, 2),
                        "win_rate": win_rate
                    }
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        else:
            return self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        
        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            payload = {}

        # 1. POST /api/verify-pin
        if path == "/api/verify-pin":
            submitted_pin = str(payload.get("pin", "")).strip()
            if submitted_pin == DEFAULT_PIN:
                return self._send_json({
                    "success": True,
                    "token": f"exacta_token_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                })
            else:
                return self._send_json({"success": False, "error": "Invalid PIN"}, 401)

        # 2. POST /api/bets
        elif path == "/api/bets":
            bets = payload.get("bets", [])
            track = payload.get("track", "Unknown")
            date_str = payload.get("date", datetime.now().strftime("%Y-%m-%d"))
            
            if not bets:
                return self._send_json({"error": "No bets provided"}, 400)
                
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # Ensure table exists
                c.execute('''CREATE TABLE IF NOT EXISTS bet_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    track TEXT,
                    date TEXT,
                    race_number INTEGER,
                    horse_number TEXT,
                    horse_name TEXT,
                    bet_type TEXT,
                    stake REAL,
                    status TEXT DEFAULT 'PENDING'
                )''')
                
                now_str = datetime.now().isoformat()
                logged_count = 0
                for bet in bets:
                    c.execute('''INSERT INTO bet_ledger (timestamp, track, date, race_number, horse_number, horse_name, bet_type, stake)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                                     now_str,
                                     track,
                                     date_str,
                                     bet.get("race_number"),
                                     bet.get("horse_number"),
                                     bet.get("horse_name"),
                                     bet.get("bet_type", "WIN"),
                                     bet.get("stake", 25.0)
                                 ))
                    logged_count += 1
                    
                conn.commit()
                conn.close()
                return self._send_json({"success": True, "logged_count": logged_count})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        else:
            return self._send_json({"error": "Endpoint not found"}, 404)

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    server_address = ("", PORT)
    httpd = socketserver.TCPServer(server_address, ExactaAPIHandler)
    print(f"[API SERVER] Exacta AI Local Engine API server running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
