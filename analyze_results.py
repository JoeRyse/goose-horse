import sqlite3
import pandas as pd
import sys

DB_NAME = "racing_data.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def run_global_analysis():
    conn = get_connection()
    
    print("\n" + "="*60)
    print(" 📊  EXACTA AI: PERFORMANCE REPORT (Graded Only)")
    print("="*60)

    # FILTER: Only look at races where at least one horse has a finish position
    # This prevents the "Backlog" of ungraded races from dragging down stats.
    graded_filter = "r.id IN (SELECT DISTINCT race_id FROM selections WHERE finish_position IS NOT NULL)"

    # 1. OVERALL WIN & TOP 4 RATES
    query_overall = f"""
    SELECT 
        COUNT(DISTINCT r.id) as total_races,
        SUM(CASE WHEN s.rank = 1 AND s.finish_position = 1 THEN 1 ELSE 0 END) as top_pick_wins,
        SUM(CASE WHEN s.finish_position = 1 THEN 1 ELSE 0 END) as winner_in_top_4
    FROM races r
    JOIN selections s ON s.race_id = r.id
    WHERE {graded_filter}
    """
    df_overall = pd.read_sql_query(query_overall, conn)
    total = df_overall['total_races'][0]
    wins = df_overall['top_pick_wins'][0]
    in_four = df_overall['winner_in_top_4'][0]
    
    if total > 0:
        print(f"\n🏆 GLOBAL ACCURACY ({total} Races Graded)")
        print(f"   - Top Pick Winner:      {wins}  ({(wins/total)*100:.1f}%)")
        print(f"   - Winner in Top 4:      {in_four}  ({(in_four/total)*100:.1f}%)")
    else:
        print("No races graded yet.")
        conn.close()
        return

    # 2. TRACK SUMMARY
    print("\n🌍 TRACK SUMMARY (Top Pick Win %)")
    query_track = f"""
    SELECT 
        m.track,
        COUNT(DISTINCT r.id) as races,
        ROUND(CAST(SUM(CASE WHEN s.rank = 1 AND s.finish_position = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(DISTINCT r.id) * 100, 1) as win_pct,
        -- Winner found in Top 4 rate
        ROUND(CAST(SUM(CASE WHEN s.finish_position = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(DISTINCT r.id) * 100, 1) as top4_hit_rate
    FROM races r
    JOIN meetings m ON r.meeting_id = m.id
    JOIN selections s ON s.race_id = r.id
    WHERE s.rank = 1 AND {graded_filter}
    GROUP BY m.track
    ORDER BY races DESC
    """
    df_track = pd.read_sql_query(query_track, conn)
    if not df_track.empty:
        print(df_track.to_string(index=False))

    conn.close()

def analyze_specific_track(track_name):
    conn = get_connection()
    print("\n" + "*"*60)
    print(f" 🔎 DEEP DIVE: {track_name.upper()}")
    print("*"*60)

    graded_filter = "r.id IN (SELECT DISTINCT race_id FROM selections WHERE finish_position IS NOT NULL)"

    # 1. SURFACE BREAKDOWN
    print("\n--- 🌱 SURFACE PERFORMANCE ---")
    query_surface = f"""
    SELECT 
        r.surface,
        COUNT(DISTINCT r.id) as races,
        SUM(CASE WHEN s.rank = 1 AND s.finish_position = 1 THEN 1 ELSE 0 END) as wins,
        ROUND(CAST(SUM(CASE WHEN s.rank = 1 AND s.finish_position = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(DISTINCT r.id) * 100, 1) as win_pct
    FROM races r
    JOIN meetings m ON r.meeting_id = m.id
    JOIN selections s ON s.race_id = r.id
    WHERE s.rank = 1 AND m.track = ? AND {graded_filter}
    GROUP BY r.surface
    ORDER BY races DESC
    """
    df_surf = pd.read_sql_query(query_surface, conn, params=(track_name,))
    if not df_surf.empty:
        print(df_surf.to_string(index=False))
    else:
        print("No graded data for this track.")

    # 2. DISTANCE BREAKDOWN
    print("\n--- 📏 DISTANCE PERFORMANCE ---")
    query_dist = f"""
    SELECT 
        r.distance,
        COUNT(DISTINCT r.id) as races,
        SUM(CASE WHEN s.rank = 1 AND s.finish_position = 1 THEN 1 ELSE 0 END) as wins,
        ROUND(CAST(SUM(CASE WHEN s.rank = 1 AND s.finish_position = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(DISTINCT r.id) * 100, 1) as win_pct
    FROM races r
    JOIN meetings m ON r.meeting_id = m.id
    JOIN selections s ON s.race_id = r.id
    WHERE s.rank = 1 AND m.track = ? AND {graded_filter}
    GROUP BY r.distance
    ORDER BY races DESC
    LIMIT 5
    """
    df_dist = pd.read_sql_query(query_dist, conn, params=(track_name,))
    if not df_dist.empty:
        print(df_dist.to_string(index=False))

    # 3. BARRIER (POST POSITION) BIAS
    print("\n--- 🚪 WINNING BARRIERS (Actual Results) ---")
    query_barrier = f"""
    SELECT 
        s.barrier,
        COUNT(*) as wins
    FROM selections s
    JOIN races r ON s.race_id = r.id
    JOIN meetings m ON r.meeting_id = m.id
    WHERE s.finish_position = 1 AND m.track = ?
    GROUP BY s.barrier
    ORDER BY wins DESC
    LIMIT 5
    """
    df_bar = pd.read_sql_query(query_barrier, conn, params=(track_name,))
    if not df_bar.empty:
        print("Top 5 Winningest Posts (from graded races):")
        print(df_bar.to_string(index=False))
    
    # 4. PICK RANKING ACCURACY
    print("\n--- 🎯 AI RANKING ACCURACY ---")
    query_ranks = f"""
    SELECT 
        s.rank as ai_pick_rank,
        COUNT(*) as wins,
        ROUND(CAST(COUNT(*) AS FLOAT) * 100 / (SELECT COUNT(DISTINCT r.id) FROM races r JOIN meetings m ON r.meeting_id = m.id WHERE m.track = ? AND {graded_filter}), 1) as win_rate
    FROM selections s
    JOIN races r ON s.race_id = r.id
    JOIN meetings m ON r.meeting_id = m.id
    WHERE s.finish_position = 1 AND m.track = ?
    GROUP BY s.rank
    ORDER BY s.rank ASC
    """
    df_ranks = pd.read_sql_query(query_ranks, conn, params=(track_name, track_name))
    if not df_ranks.empty:
        print(df_ranks.to_string(index=False))

    conn.close()

def main_menu():
    run_global_analysis()
    
    conn = get_connection()
    # Get list of tracks that actually have GRADED races
    # We filter the menu too, so you don't waste time selecting a track with 0 results
    tracks_query = """
    SELECT DISTINCT m.track 
    FROM meetings m
    JOIN races r ON r.meeting_id = m.id
    JOIN selections s ON s.race_id = r.id
    WHERE s.finish_position IS NOT NULL
    ORDER BY m.track ASC
    """
    tracks = [row[0] for row in conn.execute(tracks_query).fetchall()]
    conn.close()

    while True:
        print("\n" + "-"*40)
        print("🔎 TRACK DEEP DIVE MENU (Graded Tracks Only)")
        print("-"*40)
        
        if not tracks:
            print("No tracks have been graded yet.")
            break

        for i, t in enumerate(tracks):
            print(f"[{i+1}] {t}")
        
        val = input("\nSelect Track # to Analyze (or 'q' to quit): ").strip()
        if val.lower() == 'q': break
        
        try:
            idx = int(val) - 1
            if 0 <= idx < len(tracks):
                selected_track = tracks[idx]
                analyze_specific_track(selected_track)
                input("\nPress Enter to continue...")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Invalid input.")

if __name__ == "__main__":
    main_menu()