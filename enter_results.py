import sqlite3
import sys
from datetime import datetime

# Import the scraper helper (Must be in the same folder as race_scraper.py)
try:
    import race_scraper
except ImportError:
    print("⚠️  WARNING: 'race_scraper.py' not found. Auto-fill will not work.")
    print("   Please save the race_scraper code in the same folder.")
    race_scraper = None

DB_NAME = "racing_data.db"

def get_categorized_tracks(conn):
    """Separates tracks into 'Pending' (0 results) and 'Entered' (Partial/Done)."""
    c = conn.cursor()
    
    # 1. All tracks
    c.execute("SELECT DISTINCT track FROM meetings")
    all_tracks = {row[0] for row in c.fetchall()}

    # 2. Tracks with at least one result
    c.execute("""
        SELECT DISTINCT m.track 
        FROM meetings m
        JOIN races r ON m.id = r.meeting_id
        JOIN selections s ON r.id = s.race_id
        WHERE s.finish_position IS NOT NULL
    """)
    entered_set = {row[0] for row in c.fetchall()}

    pending_list = sorted(list(all_tracks - entered_set))
    entered_list = sorted(list(entered_set))

    return pending_list, entered_list

def enter_results():
    conn = sqlite3.connect(DB_NAME)
    
    while True:
        # --- SCREEN 0: MAIN MENU ---
        print("\n" + "="*40)
        print("      🚀  RACE RESULT ENTRY  🚀")
        print("="*40)
        
        pending_tracks, entered_tracks = get_categorized_tracks(conn)
        
        print(f"[1] Enter NEW Results (To Do: {len(pending_tracks)})")
        print(f"[2] View/Edit ENTERED Results (Done: {len(entered_tracks)})")
        print("[q] Quit")
        print("-" * 40)
        
        mode = input("Select Option: ").strip().lower()
        if mode == 'q': break
        
        if mode == '1':
            current_track_list = pending_tracks
            list_name = "PENDING TRACKS"
        elif mode == '2':
            current_track_list = entered_tracks
            list_name = "ALREADY ENTERED"
        else:
            continue

        if not current_track_list:
            print(f"\n✅ No {list_name.lower()} found!")
            continue

        # --- SCREEN 1: SELECT TRACK ---
        while True:
            print(f"\n--- {list_name} ---")
            for idx, t in enumerate(current_track_list):
                print(f"[{idx+1}] {t}")
            
            val = input("\nSelect Track # (or 'b' for Back): ").strip()
            if val.lower() == 'b': break
            
            try:
                track_idx = int(val) - 1
                if track_idx < 0 or track_idx >= len(current_track_list): raise ValueError
                selected_track = current_track_list[track_idx]
            except ValueError:
                print("❌ Invalid selection.")
                continue

            # --- SCREEN 2: SELECT MEETING ---
            while True:
                c = conn.cursor()
                c.execute("SELECT id, date, track_condition FROM meetings WHERE track = ? ORDER BY date DESC", (selected_track,))
                meetings = c.fetchall()
                
                if not meetings:
                    print(f"No meetings for {selected_track}.")
                    break 

                print(f"\n--- {selected_track} Meetings ---")
                for m in meetings:
                    # Visual check: Do we have results for this meeting?
                    c.execute("""
                        SELECT count(*) FROM races r 
                        JOIN selections s ON r.id = s.race_id 
                        WHERE r.meeting_id = ? AND s.finish_position IS NOT NULL
                    """, (m[0],))
                    count = c.fetchone()[0]
                    status = "✅ Done" if count > 0 else ".."
                    print(f"ID: [{m[0]}]  Date: {m[1]}  {status}")
                    
                val = input(f"\nEnter Meeting ID to GRADE (or 'b' for Back): ").strip()
                if val.lower() == 'b': break 
                
                try:
                    meeting_id = int(val)
                    # Verify ID belongs to track
                    c.execute("SELECT date FROM meetings WHERE id = ? AND track = ?", (meeting_id, selected_track))
                    m_row = c.fetchone()
                    if not m_row: raise ValueError
                    meeting_date_str = m_row[0]
                except ValueError:
                    print("❌ Invalid ID.")
                    continue

                # --- SCREEN 3: GRADING LOOP ---
                c.execute("SELECT id, race_number FROM races WHERE meeting_id = ? ORDER BY race_number", (meeting_id,))
                races = c.fetchall()
                if not races: continue

                # --- AUTO-FILL CHECK ---
                web_data = {}
                if race_scraper:
                    print("\n🌎 Checking for Web Results...")
                    # Convert date string (YYYY-MM-DD) to Object
                    try:
                        date_obj = datetime.strptime(meeting_date_str, "%Y-%m-%d")
                        
                        # Determine Country (Simple Logic)
                        if selected_track in race_scraper.US_TRACK_CODES:
                            web_data = race_scraper.get_us_results(selected_track, date_obj)
                        else:
                            # For AU, we might just open the browser or try scraping
                            print("   (Australian Track detected - Attempting scraper...)")
                            web_data = race_scraper.get_au_results(selected_track, date_obj)
                            
                        if web_data:
                            print(f"   🎉 Found results for {len(web_data)} races!")
                        else:
                            print("   ⚠️  No automated results found (or track not mapped).")
                    except Exception as e:
                        print(f"   ⚠️  Auto-fill Error: {e}")

                # Proceed to Grade Races
                print(f"\n📝 Grading {len(races)} Races...")
                
                for r in races:
                    race_id, race_num = r
                    print(f"\n🏁 Race {race_num}")
                    
                    # 1. Check Auto-Fill
                    auto_success = False
                    if race_num in web_data:
                        res = web_data[race_num] # Dict {1: '4', 2: '1', ...}
                        print(f"   🤖 WEB Result: 1st:[#{res.get(1)}] 2nd:[#{res.get(2)}] 3rd:[#{res.get(3)}] 4th:[#{res.get(4)}]")
                        confirm = input("   Use this result? (y/n/e to edit): ").lower()
                        
                        if confirm == 'y':
                            # Clear old
                            c.execute("UPDATE selections SET finish_position = NULL WHERE race_id = ?", (race_id,))
                            # Save new
                            for rank, horse_num in res.items():
                                c.execute("""
                                    UPDATE selections SET finish_position = ? 
                                    WHERE race_id = ? AND horse_number = ?
                                """, (rank, race_id, str(horse_num)))
                            conn.commit()
                            print("   ✅ Saved.")
                            auto_success = True

                    if auto_success: continue 

                    # 2. Manual Entry (Fallback)
                    # Show Picks
                    c.execute("SELECT rank, horse_number, horse_name, finish_position FROM selections WHERE race_id = ? ORDER BY rank", (race_id,))
                    picks = c.fetchall()
                    
                    # Skip logic
                    has_winner = any(p[3] == 1 for p in picks)
                    if has_winner:
                        skip = input("   (Already graded. Enter to Skip, 'r' to Re-grade): ")
                        if skip != 'r': continue

                    # Display Picks
                    picks_str = ", ".join([f"{p[0]}.[#{p[1]}] {p[2]}" for p in picks])
                    print(f"   AI Picks: {picks_str}")

                    # Manual Input Loop
                    c.execute("UPDATE selections SET finish_position = NULL WHERE race_id = ?", (race_id,))
                    positions = ["1st", "2nd", "3rd", "4th"]
                    for i, pos_name in enumerate(positions):
                        rank_num = i + 1
                        winner_num = input(f"   {pos_name} Place #: ").strip()
                        if not winner_num: break 

                        c.execute("UPDATE selections SET finish_position = ? WHERE race_id = ? AND horse_number = ?", (rank_num, race_id, winner_num))
                        if c.rowcount > 0:
                            print(f"     ✅ Match!")
                    conn.commit()
    
    conn.close()

if __name__ == "__main__":
    enter_results()