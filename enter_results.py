import sqlite3

DB_NAME = "racing_data.db"

def get_tracks_with_data(conn):
    """Returns a list of unique tracks that exist in the DB."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT track FROM meetings ORDER BY track ASC")
    return [row[0] for row in c.fetchall()]

def enter_results():
    conn = sqlite3.connect(DB_NAME)
    
    while True:
        # --- SCREEN 1: SELECT TRACK ---
        tracks = get_tracks_with_data(conn)
        
        if not tracks:
            print("\n✅ Database is empty. No results to enter.")
            break

        print("\n" + "="*40)
        print("   🏆  ENTER RESULTS (Top 4) 🏆")
        print("="*40)
        
        for idx, t in enumerate(tracks):
            print(f"[{idx+1}] {t}")
            
        print("-" * 40)
        val = input("Select Track # (or 'q' to quit): ").strip()
        
        if val.lower() == 'q': break
        
        try:
            track_idx = int(val) - 1
            if track_idx < 0 or track_idx >= len(tracks): raise ValueError
            selected_track = tracks[track_idx]
        except ValueError:
            print("❌ Invalid selection.")
            continue

        # --- SCREEN 2: SELECT MEETING ---
        while True:
            c = conn.cursor()
            c.execute("SELECT id, date, track_condition FROM meetings WHERE track = ? ORDER BY date DESC", (selected_track,))
            meetings = c.fetchall()
            
            if not meetings:
                print(f"\nNo meetings found for {selected_track}.")
                break 

            print(f"\n--- Grading: {selected_track} ---")
            print(f"{'ID':<6} {'Date':<15} {'Condition'}")
            print("-" * 40)
            for m in meetings:
                print(f"[{m[0]:<4}] {m[1]:<15} {m[2]}")
            print("-" * 40)
            
            val = input(f"Enter Meeting ID to GRADE (or 'b' for Back): ").strip()
            
            if val.lower() == 'b': break 
            
            try:
                meeting_id = int(val)
            except ValueError:
                print("❌ Invalid ID.")
                continue

            c.execute("SELECT id FROM meetings WHERE id = ? AND track = ?", (meeting_id, selected_track))
            if not c.fetchone():
                print("❌ ID mismatch.")
                continue

            # --- SCREEN 3: GRADE THE RACES (1st - 4th) ---
            c.execute("SELECT id, race_number FROM races WHERE meeting_id = ? ORDER BY race_number", (meeting_id,))
            races = c.fetchall()

            if not races:
                print("⚠️  No races found.")
                continue

            print(f"\n📝 Grading {len(races)} Races...")
            
            for r in races:
                race_id, race_num = r
                print(f"\n🏁 Race {race_num}")
                
                # Show Picks
                c.execute("SELECT rank, horse_number, horse_name, finish_position FROM selections WHERE race_id = ? ORDER BY rank", (race_id,))
                picks = c.fetchall()
                
                picks_display = []
                for p in picks:
                    # Show previous grade if exists (e.g. "1st", "2nd")
                    status = f" [Finished {p[3]}]" if p[3] else ""
                    picks_display.append(f"{p[0]}.[#{p[1]}] {p[2]}{status}")
                
                print(f"   AI Picks: " + ", ".join(picks_display))

                # If already fully graded (has a 1st place), ask to skip
                has_winner = any(p[3] == 1 for p in picks)
                if has_winner:
                    skip = input("   (Race already graded. Press Enter to Skip, or type 'r' to Re-grade): ")
                    if skip.lower() != 'r': continue

                # Clear old results for this race
                c.execute("UPDATE selections SET finish_position = NULL WHERE race_id = ?", (race_id,))

                # Loop for 1st, 2nd, 3rd, 4th
                positions = ["1st", "2nd", "3rd", "4th"]
                for i, pos_name in enumerate(positions):
                    rank_num = i + 1
                    
                    winner_num = input(f"   {pos_name} Place #: ").strip()
                    if not winner_num: break # Stop if they stop entering

                    # Mark result in DB
                    # We match by Race ID + Horse Number
                    # Note: This only marks it IF the AI picked it.
                    c.execute("""
                        UPDATE selections 
                        SET finish_position = ? 
                        WHERE race_id = ? AND horse_number = ?
                    """, (rank_num, race_id, winner_num))
                    
                    if c.rowcount > 0:
                        # Fetch name for confirmation
                        c.execute("SELECT horse_name FROM selections WHERE race_id = ? AND horse_number = ?", (race_id, winner_num))
                        row = c.fetchone()
                        print(f"     ✅ AI hit! {row[0]} finished {pos_name}.")
                    # Note: We don't print "Miss" anymore to keep it clean, 
                    # but the DB simply won't update a row if the horse wasn't in our selections table.

            conn.commit()
            print("\n✅ Meeting Graded. Returning to list...")

    conn.close()
    print("Exited.")

if __name__ == "__main__":
    enter_results()