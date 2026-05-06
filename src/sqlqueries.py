import sqlite3
import pandas as pd

#defining queries here that will be used later on in the queryanalysis.py file
#used list so queryanalysis can go through each of these queries one by one (elements of list)
QUERIES = {
    #shows all data like opponent, days of rest, penalty yards difference, etc., for all losses
    #ordered by yard per play (efficiency of plays) with worst performance efficiency at the top of list
    #checks in losses the stats most associated with those worst efficiency performances
    "ordered_losses_data": """
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

    #filters players responsible for more than 40% of total yards and orders them from most to least yard %
    #top most players will be most dominant in the team --> can show over reliance on those players
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

    #measures qb season discipline alongside team losses
    #using cross join since not a large set so won't become too messy
    "quarterback_players_discipline_alongside_losses": """
        SELECT 
            p.Player AS Quarterback,
            p.INT_Rate,
            p.TD_INT_Ratio,

            l.avg_penalty_efficiency_in_losses,
            l.avg_rutgers_score_in_losses,
            l.avg_opponent_score_in_losses
        FROM clean_passing p

        CROSS JOIN (
            SELECT
                AVG(Penalty_Efficiency) AS avg_penalty_efficiency_in_losses,
                AVG(Rutgers_Score) AS avg_rutgers_score_in_losses,
                AVG(Opponent_Score) AS avg_opponent_score_in_losses
            FROM clean_combined_football_stats
            WHERE Is_Win = 0
        ) l
        ORDER BY p.INT_Rate DESC;
    """,

    #gets all players (rushing and passing) and removes those with no yards (no useful contribution to team)
    #gets most impactful and versatile players
    "ranked_versatility": """
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

    #includes win/loss variable (y variable for prediction model)
    #gets all the various features like efficiencies, penalties, etc
    #prep for the prediction model (gets dependent variables and independent variable ready for prediction model)
    "prediction_model_ready_table": """
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

#takes in an individual query from above list, connects to database, reads in query and creates a dataframe which is then returned (the table of results from query)
#will use this in query analysis
def run_query(query_name, db_path='data/database/rutgersfootball.db'):
    """Helper function to run a query by its name and return a DataFrame."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(QUERIES[query_name], conn)
    conn.close()
    return df