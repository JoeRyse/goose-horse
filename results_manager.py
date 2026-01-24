import pandas as pd
import os
from datetime import datetime

# File paths
PREDICTIONS_FILE = "output_data/master_race_data.csv"
RESULTS_FILE = "output_data/results_log.csv"

def log_results():
    if not os.path.exists(PREDICTIONS_FILE):
        print("No predictions found! Run main.py first.")
        return

    # Load the predictions
    df = pd.read_csv(PREDICTIONS_FILE)
    
    # Filter for races that haven't been graded yet (you'll need to add a 'graded' column later)
    # For now, let's just ask about specific races
    
    print("\n--- RESULTS LOGGER ---")
    print("Type 'skip' to skip a race, or enter the payouts.")
    
    # Check if results file exists to append, else create
    if os.path.exists(RESULTS_FILE):
        results_log = pd.read_csv(RESULTS_FILE)
    else:
        results_log = pd.DataFrame(columns=["date", "track", "race_number", "ai_top_pick", "ai_value_pick", "winner_program_num", "win_payout", "ai_win_profit", "ai_value_profit"])

    # Loop through unique races in your data
    # (Assuming you have columns 'race_number' and 'track' or similar)
    unique_races = df[['race_number']].drop_duplicates()

    for index, row in unique_races.iterrows():
        race_num = row['race_number']
        
        # Get AI picks for this race
        race_data = df[df['race_number'] == race_num]
        
        # Simple logic: Find horse with highest 'speed_fig_last' (Top Pick) and 'value_flag' (Value Pick)
        # You might want to refine how you define "AI's Pick"
        try:
            top_pick = race_data.loc[race_data['speed_fig_last'].idxmax()]['program_number']
        except:
            top_pick = "N/A"
            
        try:
            value_pick = race_data[race_data['value_flag'] == True].iloc[0]['program_number']
        except:
            value_pick = "None"

        print(f"\nRace {race_num}:")
        print(f"AI Top Pick: #{top_pick}")
        print(f"AI Value Pick: #{value_pick}")
        
        winner = input(f"Who won Race {race_num}? (Enter Program #): ")
        if winner.lower() == 'skip': continue
        
        payout = float(input(f"What was the Win Payout for #{winner}? $"))
        
        # Calculate Profit/Loss (assuming $2 bet)
        top_profit = -2.0
        if str(winner) == str(top_pick):
            top_profit = payout - 2.0
            
        value_profit = 0.0 # Only bet value if it exists
        if value_pick != "None":
            value_profit = -2.0
            if str(winner) == str(value_pick):
                value_profit = payout - 2.0

        # Log it
        new_row = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "race_number": race_num,
            "ai_top_pick": top_pick,
            "ai_value_pick": value_pick,
            "winner_program_num": winner,
            "win_payout": payout,
            "ai_win_profit": top_profit,
            "ai_value_profit": value_profit
        }
        
        # Append using concat (pandas 2.0 style)
        new_df = pd.DataFrame([new_row])
        results_log = pd.concat([results_log, new_df], ignore_index=True)

    # Save
    results_log.to_csv(RESULTS_FILE, index=False)
    
    # Show Stats
    total_roi = results_log['ai_win_profit'].sum()
    print(f"\n---------------------------")
    print(f"SESSION COMPLETE")
    print(f"Total Profit/Loss (Top Picks): ${total_roi:.2f}")
    print(f"Data saved to {RESULTS_FILE}")

if __name__ == "__main__":
    log_results()