import http.server
import socketserver
import json
import os
import sqlite3
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse

PORT = 8888
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
API_OUTPUT_DIR = os.path.join(BASE_DIR, "frontend", "public", "api", "output")
DB_PATH = os.path.join(LOGS_DIR, "master_betting_history.db")
DEFAULT_PIN = os.environ.get("EXACTA_PIN", "0518")

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

US_TIER1_TRACKS = ["Saratoga", "Del Mar", "Gulfstream Park", "Keeneland", "Churchill Downs", "Belmont Park", "Aqueduct"]
AUS_HIGH_HIT_TRACKS = ["Flemington", "Randwick", "Caulfield", "Doomben", "Rosehill", "Moonee Valley", "Eagle Farm"]

def calculate_roi_analytics(
    filter_group="ALL", target_track="", start_date="", end_date="", 
    surface="ALL", condition="ALL", dist_type="ALL", race_class="ALL"
):
    """
    Queries SQLite database master_betting_history.db with granular filters:
    Track, Date Range, Dirt vs Turf, Track Condition, Sprint vs Route, Maiden vs Non-Maiden.
    """
    if not os.path.exists(DB_PATH):
        return {}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = """
        SELECT 
            p.date, p.track, p.race_number, p.p1_num, p.p1_name, p.p2_num, p.p1_rating, p.rating_gap, p.has_best_bet, p.has_solo_lock,
            p.distance, p.surface, p.condition,
            r.win_num, r.place_num, r.show_num, r.win_payout, r.exacta_payout
        FROM predictions p
        LEFT JOIN results r ON p.date = r.date AND p.track = r.track AND p.race_number = r.race_number
    """
    c.execute(query)
    rows = c.fetchall()
    conn.close()

    total_races = 0
    top_pick_wins = 0
    best_bet_wins = 0
    best_bet_count = 0
    solo_lock_wins = 0
    solo_lock_count = 0

    staked_top = 0.0
    payout_top = 0.0
    staked_best = 0.0
    payout_best = 0.0
    staked_lock = 0.0
    payout_lock = 0.0

    multi_tracker = {
        "pick_3": {"attempted": 0, "hits": 0},
        "pick_4": {"attempted": 0, "hits": 0},
        "pick_5": {"attempted": 0, "hits": 0},
        "pick_6": {"attempted": 0, "hits": 0},
    }

    race_logs = []

    meetings_dict = {}
    for row in rows:
        (
            date_str, track, race_num, p1_num, p1_name, p2_num, p1_rating, gap, has_best, has_lock,
            dist_str, surf_str, cond_str,
            win_num, place_num, show_num, win_paid, ex_paid
        ) = row

        # 1. Track / Tier Filter
        if target_track and target_track.lower() not in ["", "all"]:
            if target_track.lower() not in track.lower():
                continue
        elif filter_group == "US_TIER1" and not any(t.lower() in track.lower() for t in US_TIER1_TRACKS):
            continue
        elif filter_group == "AUS_HIGH_HIT" and not any(t.lower() in track.lower() for t in AUS_HIGH_HIT_TRACKS):
            continue

        # 2. Date Range Filter
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue

        # 3. Surface Filter (Dirt vs Turf vs Synthetic)
        surf_lower = str(surf_str or "").lower()
        if surface == "DIRT" and "dirt" not in surf_lower and "main" not in surf_lower:
            continue
        elif surface == "TURF" and "turf" not in surf_lower and "grass" not in surf_lower:
            continue
        elif surface == "SYNTHETIC" and "synth" not in surf_lower and "tapeta" not in surf_lower and "poly" not in surf_lower:
            continue

        # 4. Condition Filter
        cond_lower = str(cond_str or "").lower()
        if condition == "FAST_FIRM" and not any(c in cond_lower for c in ["fast", "firm", "standard"]):
            continue
        elif condition == "OFF_TRACK" and not any(c in cond_lower for c in ["good", "yielding", "soft", "muddy", "sloppy", "wet", "heavy"]):
            continue

        # 5. Distance Filter (Sprint vs Route)
        dist_lower = str(dist_str or "").lower()
        is_route = any(k in dist_lower for k in ["1m", "1 1/", "1-1/", "8f", "8.5f", "9f", "10f", "1600", "1800", "2000"])
        if dist_type == "SPRINT" and is_route:
            continue
        elif dist_type == "ROUTE" and not is_route:
            continue

        # 6. Race Class Filter (Maiden vs Non-Maiden)
        is_maiden = "maiden" in dist_lower or "msw" in dist_lower or "mcl" in dist_lower
        if race_class == "MAIDEN" and not is_maiden:
            continue
        elif race_class == "NON_MAIDEN" and is_maiden:
            continue

        m_key = f"{track}_{date_str}"
        if m_key not in meetings_dict:
            meetings_dict[m_key] = []
        meetings_dict[m_key].append(row)

    filtered_meetings_count = len(meetings_dict)

    for m_key, race_rows in meetings_dict.items():
        top2_hits = []
        for r in race_rows:
            (
                date_str, track, race_num, p1_num, p1_name, p2_num, p1_rating, gap, has_best, has_lock,
                dist_str, surf_str, cond_str,
                win_num, place_num, show_num, win_paid, ex_paid
            ) = r
            total_races += 1

            p1_rating_val = float(p1_rating or 80.0)
            gap_val = float(gap or 0.0)
            has_lock_val = bool(has_lock or (p1_rating_val >= 88.0 and gap_val >= 5.0))
            has_best_val = bool(has_best or gap_val >= 3.0)

            # Determine authentic win match from scraped results table
            has_official_result = bool(win_num and str(win_num).strip() not in ["", "None", "0"])
            is_top_win = False
            actual_win_paid = 0.0

            if has_official_result:
                is_top_win = (str(p1_num).strip() == str(win_num).strip())
                actual_win_paid = float(win_paid) if (win_paid and float(win_paid) > 0) else 0.0

            is_top2_hit = False
            if has_official_result:
                is_top2_hit = is_top_win or (place_num and str(p2_num).strip() == str(place_num).strip())
                top2_hits.append(is_top2_hit)

            stake_val = 20.0 if has_lock_val else (10.0 if has_best_val else 5.0)
            
            if has_official_result:
                payout_val = (stake_val * (actual_win_paid / 2.0)) if is_top_win else 0.0
                pnl_val = payout_val - stake_val
            else:
                payout_val = 0.0
                pnl_val = 0.0
                stake_val = 0.0

            race_logs.append({
                "date": date_str,
                "track": track,
                "race_number": race_num,
                "p1_num": p1_num,
                "p1_name": p1_name or f"Horse #{p1_num}",
                "rating": round(p1_rating_val, 1),
                "gap": round(gap_val, 1),
                "bet_tag": "SOLO LOCK ($20)" if has_lock_val else ("BEST BET ($10)" if has_best_val else "TOP PICK ($5)"),
                "is_win": is_top_win,
                "has_result": has_official_result,
                "status": "WIN" if (has_official_result and is_top_win) else ("LOSS" if has_official_result else "UNSETTLED"),
                "winner_num": str(win_num).strip() if has_official_result else "UNSETTLED",
                "stake": stake_val,
                "payout": round(payout_val, 2),
                "pnl": round(pnl_val, 2)
            })

            # Only count settled races with scraped results into ROI statistics
            if has_official_result:
                staked_top += 5.0
                if is_top_win:
                    top_pick_wins += 1
                    payout_top += 5.0 * (actual_win_paid / 2.0)

                if has_best_val and not has_lock_val:
                    best_bet_count += 1
                    staked_best += 10.0
                    if is_top_win:
                        best_bet_wins += 1
                        payout_best += 10.0 * (actual_win_paid / 2.0)

                if has_lock_val:
                    solo_lock_count += 1
                    staked_lock += 20.0
                    if is_top_win:
                        solo_lock_wins += 1
                        payout_lock += 20.0 * (actual_win_paid / 2.0)

        n = len(top2_hits)
        for i in range(n - 2):
            multi_tracker["pick_3"]["attempted"] += 1
            if all(top2_hits[i:i+3]): multi_tracker["pick_3"]["hits"] += 1
        for i in range(n - 3):
            multi_tracker["pick_4"]["attempted"] += 1
            if all(top2_hits[i:i+4]): multi_tracker["pick_4"]["hits"] += 1
        for i in range(n - 4):
            multi_tracker["pick_5"]["attempted"] += 1
            if all(top2_hits[i:i+5]): multi_tracker["pick_5"]["hits"] += 1
        for i in range(n - 5):
            multi_tracker["pick_6"]["attempted"] += 1
            if all(top2_hits[i:i+6]): multi_tracker["pick_6"]["hits"] += 1

    total_staked = staked_top + staked_best + staked_lock
    total_payout = payout_top + payout_best + payout_lock
    overall_pnl = total_payout - total_staked
    overall_roi = round(((total_payout - total_staked) / total_staked * 100), 1) if total_staked > 0 else 0.0

    return {
        "meetings_analyzed": filtered_meetings_count,
        "total_races": total_races,
        "race_logs": race_logs[::-1][:200], # Return 200 most recent races for instant auditing
        "overall": {
            "total_staked": round(total_staked, 2),
            "total_payout": round(total_payout, 2),
            "pnl": round(overall_pnl, 2),
            "roi": overall_roi
        },
        "top_pick_win": {
            "wager_size": 5.0,
            "wins": top_pick_wins,
            "total_bets": total_races,
            "win_rate": round((top_pick_wins / total_races * 100), 1) if total_races > 0 else 0.0,
            "staked": round(staked_top, 2),
            "payout": round(payout_top, 2),
            "pnl": round(payout_top - staked_top, 2),
            "roi": round(((payout_top - staked_top) / staked_top * 100), 1) if staked_top > 0 else 0.0
        },
        "best_bet": {
            "wager_size": 10.0,
            "wins": best_bet_wins,
            "total_bets": best_bet_count,
            "win_rate": round((best_bet_wins / best_bet_count * 100), 1) if best_bet_count > 0 else 0.0,
            "staked": round(staked_best, 2),
            "payout": round(payout_best, 2),
            "pnl": round(payout_best - staked_best, 2),
            "roi": round(((payout_best - staked_best) / staked_best * 100), 1) if staked_best > 0 else 0.0
        },
        "solo_lock": {
            "wager_size": 20.0,
            "wins": solo_lock_wins,
            "total_bets": solo_lock_count,
            "win_rate": round((solo_lock_wins / solo_lock_count * 100), 1) if solo_lock_count > 0 else 0.0,
            "staked": round(staked_lock, 2),
            "payout": round(payout_lock, 2),
            "pnl": round(payout_lock - staked_lock, 2),
            "roi": round(((payout_lock - staked_lock) / staked_lock * 100), 1) if staked_lock > 0 else 0.0
        },
        "multi_race_tracker": {
            "pick_3": {
                "attempted": multi_tracker["pick_3"]["attempted"],
                "hits": multi_tracker["pick_3"]["hits"],
                "hit_rate": round((multi_tracker["pick_3"]["hits"] / multi_tracker["pick_3"]["attempted"] * 100), 1) if multi_tracker["pick_3"]["attempted"] > 0 else 0.0
            },
            "pick_4": {
                "attempted": multi_tracker["pick_4"]["attempted"],
                "hits": multi_tracker["pick_4"]["hits"],
                "hit_rate": round((multi_tracker["pick_4"]["hits"] / multi_tracker["pick_4"]["attempted"] * 100), 1) if multi_tracker["pick_4"]["attempted"] > 0 else 0.0
            },
            "pick_5": {
                "attempted": multi_tracker["pick_5"]["attempted"],
                "hits": multi_tracker["pick_5"]["hits"],
                "hit_rate": round((multi_tracker["pick_5"]["hits"] / multi_tracker["pick_5"]["attempted"] * 100), 1) if multi_tracker["pick_5"]["attempted"] > 0 else 0.0
            },
            "pick_6": {
                "attempted": multi_tracker["pick_6"]["attempted"],
                "hits": multi_tracker["pick_6"]["hits"],
                "hit_rate": round((multi_tracker["pick_6"]["hits"] / multi_tracker["pick_6"]["attempted"] * 100), 1) if multi_tracker["pick_6"]["attempted"] > 0 else 0.0
            }
        }
    }

class ExactaAPIHandler(http.server.BaseHTTPRequestHandler):
    def address_string(self):
        return self.client_address[0]

    def log_message(self, format, *args):
        try:
            sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))
            sys.stdout.flush()
        except Exception:
            pass

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            print(f"[HTTP GET] {self.path}", flush=True)
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")
            query = parse_qs(parsed.query)

            # 0. GET /api/analytics/roi
            if path == "/api/analytics/roi":
                filter_group = query.get("filter", ["ALL"])[0]
                target_track = query.get("track", [""])[0]
                start_date = query.get("start_date", [""])[0]
                end_date = query.get("end_date", [""])[0]
                surface = query.get("surface", ["ALL"])[0]
                condition = query.get("condition", ["ALL"])[0]
                dist_type = query.get("dist_type", ["ALL"])[0]
                race_class = query.get("race_class", ["ALL"])[0]

                analytics_data = calculate_roi_analytics(
                    filter_group=filter_group,
                    target_track=target_track,
                    start_date=start_date,
                    end_date=end_date,
                    surface=surface,
                    condition=condition,
                    dist_type=dist_type,
                    race_class=race_class
                )
                return self._send_json({"status": "success", "analytics": analytics_data})

            # GET /api/analytics/tracks
            if path == "/api/analytics/tracks":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT DISTINCT track FROM predictions ORDER BY track ASC")
                tracks_list = [row[0] for row in c.fetchall() if row[0]]
                conn.close()
                return self._send_json({"status": "success", "tracks": tracks_list})

            # 1. GET /api/meetings
            if path == "/api/meetings" or path == "/api/output":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""
                    SELECT filename, track, date, region, race_count, solo_locks_count, best_bets_count 
                    FROM meetings 
                    ORDER BY date DESC, track ASC
                """)
                rows = c.fetchall()
                conn.close()

                meetings = []
                for row in rows:
                    fname, track, date_str, region, race_cnt, locks_cnt, bests_cnt = row
                    meetings.append({
                        "id": fname,
                        "filename": fname,
                        "track": track,
                        "date": date_str,
                        "track_condition": "Standard",
                        "race_count": race_cnt,
                        "solo_locks_count": locks_cnt,
                        "best_bets_count": bests_cnt,
                        "region": region,
                        "is_published": True
                    })
                return self._send_json({"status": "success", "meetings": meetings})

            # 2. GET /api/output/{filename}
            if path.startswith("/api/output/") or path.startswith("/api/meetings/"):
                fname = path.split("/")[-1]
                if not fname.endswith(".json"):
                    fname += ".json"
                    
                filepath = os.path.join(API_OUTPUT_DIR, fname)
                if not os.path.exists(filepath):
                    filepath = os.path.join(LOGS_DIR, fname)
                    
                if not os.path.exists(filepath):
                    return self._send_json({"error": "Meeting not found"}, 404)
                    
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                    if isinstance(data, str): data = json.loads(data)
                    if isinstance(data, list) and len(data) > 0: data = data[0]
                    
                    if "races" in data:
                        data["races"] = compute_race_enrichments(data["races"])
                        data["exotic_tickets"] = compute_exotic_tickets(data["races"])
                    if "meta" in data and "region" not in data["meta"]:
                        data["meta"]["region"] = get_region_for_track(data["meta"].get("track", ""))
                        
                    return self._send_json({"status": "success", "data": data})

            # 3. GET /api/stats
            if path == "/api/stats":
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

            return self._send_json({"error": "Endpoint not found"}, 404)
        except Exception as e:
            import traceback
            print(f"[API ERROR] do_GET failed: {e}", flush=True)
            traceback.print_exc()
            return self._send_json({"status": "error", "error": str(e)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        
        if path == "/api/publish-github":
            def _push_bg():
                try:
                    script_path = os.path.join(BASE_DIR, "update_and_push.ps1")
                    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], check=False)
                except Exception as e:
                    print("Publish error:", e)

            threading.Thread(target=_push_bg, daemon=True).start()
            return self._send_json({"status": "success", "message": "Publishing updates to GitHub & Vercel!"})
        
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
    server_address = ("127.0.0.1", PORT)
    try:
        http.server.HTTPServer.allow_reuse_address = True
        httpd = http.server.HTTPServer(server_address, ExactaAPIHandler)
        print(f"[API SERVER] Exacta AI Multi-Threaded Engine running on http://127.0.0.1:{PORT}", flush=True)
        httpd.serve_forever()
    except Exception as e:
        import traceback
        print(f"[API SERVER ERROR] {e}", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    run_server()
