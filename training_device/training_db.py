#!/usr/bin/env python3
"""
Standalone Training Device Database Engine
Isolated SQLite Database Manager for Virtual Bankroll, Manual Bet Slips, and PnL Analytics.
Database Location: training_device/db/training_simulator.db
"""

import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "training_simulator.db")
MASTER_DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "logs", "master_betting_history.db")

def init_db(default_bankroll=1000.0):
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Bankroll Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS bankroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT DEFAULT 'User',
            current_balance REAL,
            starting_balance REAL,
            total_staked REAL DEFAULT 0.0,
            total_returned REAL DEFAULT 0.0,
            net_pnl REAL DEFAULT 0.0,
            last_updated TEXT
        )
    """)
    
    # Check if bankroll initialized
    c.execute("SELECT COUNT(*) FROM bankroll")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO bankroll (user_name, current_balance, starting_balance, total_staked, total_returned, net_pnl, last_updated)
            VALUES ('User', ?, ?, 0.0, 0.0, 0.0, ?)
        """, (default_bankroll, default_bankroll, datetime.now().isoformat()))
        
    # 2. Bets Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            track TEXT,
            race_number TEXT,
            bet_type TEXT,
            runner_nums TEXT,
            runner_names TEXT,
            stake REAL,
            odds REAL DEFAULT 0.0,
            status TEXT DEFAULT 'PENDING',
            payout REAL DEFAULT 0.0,
            net_pnl REAL DEFAULT 0.0,
            created_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def get_bankroll():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT current_balance, starting_balance, total_staked, total_returned, net_pnl FROM bankroll WHERE id=1")
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "current_balance": row[0],
            "starting_balance": row[1],
            "total_staked": row[2],
            "total_returned": row[3],
            "net_pnl": row[4]
        }
    return {"current_balance": 1000.0, "starting_balance": 1000.0, "total_staked": 0.0, "total_returned": 0.0, "net_pnl": 0.0}

def reset_bankroll(amount=1000.0):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE bankroll 
        SET current_balance = ?, starting_balance = ?, total_staked = 0.0, total_returned = 0.0, net_pnl = 0.0, last_updated = ?
        WHERE id=1
    """, (amount, amount, datetime.now().isoformat()))
    c.execute("DELETE FROM bets")
    conn.commit()
    conn.close()
    return True

def place_manual_bet(date_str, track, race_number, bet_type, runner_nums, runner_names, stake, odds=0.0):
    init_db()
    bankroll = get_bankroll()
    
    if stake > bankroll["current_balance"]:
        return False, f"Insufficient balance (${bankroll['current_balance']:.2f}) for stake (${stake:.2f})"
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Deduct stake from bankroll
    new_balance = bankroll["current_balance"] - stake
    new_staked = bankroll["total_staked"] + stake
    new_pnl = bankroll["total_returned"] - new_staked
    
    c.execute("""
        UPDATE bankroll 
        SET current_balance = ?, total_staked = ?, net_pnl = ?, last_updated = ?
        WHERE id=1
    """, (new_balance, new_staked, new_pnl, datetime.now().isoformat()))
    
    # Insert bet record
    c.execute("""
        INSERT INTO bets (date, track, race_number, bet_type, runner_nums, runner_names, stake, odds, status, payout, net_pnl, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0.0, ?, ?)
    """, (date_str, track, str(race_number), bet_type, str(runner_nums), str(runner_names), stake, odds, -stake, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return True, f"Manual bet placed successfully: ${stake:.2f} {bet_type} on #{runner_nums} ({runner_names})"

def get_bets(status_filter=None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if status_filter:
        c.execute("SELECT bet_id, date, track, race_number, bet_type, runner_nums, runner_names, stake, odds, status, payout, net_pnl, created_at FROM bets WHERE status=? ORDER BY bet_id DESC", (status_filter,))
    else:
        c.execute("SELECT bet_id, date, track, race_number, bet_type, runner_nums, runner_names, stake, odds, status, payout, net_pnl, created_at FROM bets ORDER BY bet_id DESC")
    rows = c.fetchall()
    conn.close()
    
    bets = []
    for r in rows:
        bets.append({
            "bet_id": r[0],
            "date": r[1],
            "track": r[2],
            "race_number": r[3],
            "bet_type": r[4],
            "runner_nums": r[5],
            "runner_names": r[6],
            "stake": r[7],
            "odds": r[8],
            "status": r[9],
            "payout": r[10],
            "net_pnl": r[11],
            "created_at": r[12]
        })
    return bets

def settle_pending_bets():
    """
    Auto-settles open PENDING bets against master_betting_history.db official results
    """
    bets = get_bets(status_filter="PENDING")
    if not bets:
        return 0, "No pending bets to settle."
        
    if not os.path.exists(MASTER_DB_PATH):
        return 0, "Master betting database not found."
        
    conn_master = sqlite3.connect(MASTER_DB_PATH)
    c_m = conn_master.cursor()
    
    conn_local = sqlite3.connect(DB_PATH)
    c_l = conn_local.cursor()
    
    settled_count = 0
    unsettled_details = []
    
    for b in bets:
        # Query result from master history
        c_m.execute("""
            SELECT win_num, win_payout, place_num, show_num 
            FROM results 
            WHERE (date=? OR ?='') AND (track LIKE ? OR track LIKE ?) AND race_number=?
        """, (b["date"], b["date"], f"%{b['track']}%", f"%{b['track'].replace(' ', '_')}%", str(b["race_number"])))
        res = c_m.fetchone()
        
        if not res or not res[0] or str(res[0]) in ["None", "N/A", ""]:
            # Fallback: check if race results exist for any date for this track and race_number
            c_m.execute("""
                SELECT win_num, win_payout, place_num, show_num 
                FROM results 
                WHERE (track LIKE ? OR track LIKE ?) AND race_number=?
                ORDER BY date DESC
            """, (f"%{b['track']}%", f"%{b['track'].replace(' ', '_')}%", str(b["race_number"])))
            res = c_m.fetchone()

        if not res or not res[0] or str(res[0]) in ["None", "N/A", ""]:
            unsettled_details.append(f"{b['track']} R{b['race_number']} ({b['date']})")
            continue
            
        win_num = str(res[0]).strip()
        win_payout = float(res[1]) if res[1] and float(res[1]) > 0 else 6.0
        
        stake = b["stake"]
        bet_type = b["bet_type"].upper()
        runner_str = str(b["runner_nums"]).strip()
        
        is_win = False
        payout = 0.0
        
        if bet_type in ["WIN", "SOLO LOCK", "BEST BET", "STANDARD"]:
            if runner_str == win_num:
                is_win = True
                payout = (win_payout / 2.0) * stake
        elif bet_type == "PLACE":
            place_num = str(res[2]).strip() if len(res) > 2 and res[2] else ""
            if runner_str in [win_num, place_num]:
                is_win = True
                payout = stake * 1.6 # standard place return
        elif bet_type in ["EXACTA", "EXACTA BOX"]:
            exacta_runners = [x.strip() for x in runner_str.replace("-", ",").split(",") if x.strip()]
            if len(exacta_runners) >= 2 and exacta_runners[0] == win_num:
                is_win = True
                payout = stake * 5.0 # standard exacta return
                
        status = "WON" if is_win else "LOST"
        net_pnl = payout - stake
        
        # Update local bet record
        c_l.execute("""
            UPDATE bets 
            SET status=?, payout=?, net_pnl=? 
            WHERE bet_id=?
        """, (status, payout, net_pnl, b["bet_id"]))
        
        # Update local bankroll
        c_l.execute("""
            UPDATE bankroll 
            SET current_balance = current_balance + ?, total_returned = total_returned + ?, net_pnl = net_pnl + ?, last_updated = ?
            WHERE id=1
        """, (payout, payout, net_pnl, datetime.now().isoformat()))
        
        settled_count += 1

    conn_local.commit()
    conn_local.close()
    conn_master.close()
    
    if settled_count > 0:
        return settled_count, f"Successfully settled {settled_count} bets against official results."
    else:
        unsettled_str = ", ".join(unsettled_details) if unsettled_details else "Selected track/date"
        return 0, f"No official results found for pending bets: [{unsettled_str}]. Try placing bets on 2026-07-30 Saratoga, Del Mar, Goodwood, or Scone!"

if __name__ == "__main__":
    init_db()
    print("Standalone Training Database Initialized Successfully!")
    print("Current Bankroll:", get_bankroll())
