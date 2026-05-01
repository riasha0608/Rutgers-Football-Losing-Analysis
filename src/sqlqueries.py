import sqlite3
import pandas as pd

# Define your queries as a dictionary for easy access
QUERIES = {
    "loss_autopsy": """
        SELECT 
            s.Opponent,
            s.Win_Loss,
            s.Days_Rest,
            f.YPP_Diff,
            f.Penalty_Yds_Diff,
            f."3rdDown_Advantage", 
            f.Rutgers_Comp_Pct,
            f.Punt_Advantage
        FROM clean_schedule s
        JOIN clean_combined_football_stats f ON s.Opponent = f.Opponent
        WHERE s.Is_Win = 0
        ORDER BY f.YPP_Diff ASC;
    """,

    "over_reliance": """
        SELECT 
            Category,
            Player,
            Yardage_Share,
            TD_Share,
            Team_Yards,
            Team_TD
        FROM advanced_player_stats
        WHERE Yardage_Share > 0.40
        ORDER BY Yardage_Share DESC;
    """,

    "discipline_mistakes": """
        SELECT 
            p.Player as Quarterback,
            p.INT_Rate,
            p.TD_INT_Ratio,
            f.Penalty_Efficiency,
            f.Rutgers_Score,
            f.Opponent_Score
        FROM clean_passing p
        JOIN clean_player_dataset d ON p.Player = d.Player
        JOIN clean_combined_football_stats f ON f.Is_Win = 0
        GROUP BY p.Player, f.Opponent
        ORDER BY p.INT_Rate DESC;
    """,

    "versatility_impact": """
        SELECT 
            d.Player,
            d.Total_Utility_Yards,
            d.Is_Dual_Threat,
            pass.YPA,
            rush.TD_Rate
        FROM clean_player_dataset d
        LEFT JOIN clean_passing pass ON d.Player = pass.Player
        LEFT JOIN clean_rushing rush ON d.Player = rush.Player
        WHERE d.Total_Utility_Yards > 0
        ORDER BY d.Total_Utility_Yards DESC;
    """,

    "master_analysis_table": """
        SELECT 
            s.Date,
            s.Opponent,
            s.Is_Win AS Win_Loss_Binary,
            s.Days_Rest,
            f.YPP_Diff,
            f.Penalty_Yds_Diff,
            f.Penalty_Efficiency,
            f."3rdDown_Advantage", 
            f.Rutgers_Comp_Pct,
            f.Punt_Advantage
        FROM clean_schedule s
        JOIN clean_combined_football_stats f ON s.Opponent = f.Opponent
        ORDER BY s.Date ASC;
    """
}

def run_query(query_name, db_path='data/database/rutgersfootball.db'):
    """Helper function to run a query by its name and return a DataFrame."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(QUERIES[query_name], conn)
    conn.close()
    return df