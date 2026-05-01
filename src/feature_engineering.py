import pandas as pd
import sqlite3
import os

# This ensures the database folder exists before we try to save to it
if not os.path.exists('data/database'):
    os.makedirs('data/database')

conn = sqlite3.connect('data/database/rutgersfootball.db')

#now adding some basic columns first to combined football stats clean table
#for now, all data is combined so splitting it up so separate columns for rutgers vs opponent

query = "SELECT * FROM clean_combined_football_stats"
df = pd.read_sql_query(query, conn)

def apply_advanced_features(df):
    df['Penalty_Yds_Diff'] = df['Rutgers_PenaltyYards'] - df['Opp_PenaltyYards']
    
    df['Penalty_Efficiency'] = df['Rutgers_PenaltyYards'] / df['Rutgers_TotalPlays']

    df['3rdDown_Advantage'] = df['Rutgers_3rdPct'] - df['Opp_3rdPct']

    df['YPP_Diff'] = df['Rutgers_AvgYdsPlay'] - df['Opp_AvgYdsPlay']

    df['Rutgers_Comp_Pct'] = (df['Rutgers_Comp'] / df['Rutgers_Att'].replace(0, 1)).round(3)

    df['Rutgers_4thPct'] = (df['Rutgers_4thMade'] / df['Rutgers_4thAtt'].replace(0, 1)).round(3)

    df['Punt_Advantage'] = df['Rutgers_PuntAvg'] - df['Opp_PuntAvg']

    return df


df_advanced = apply_advanced_features(df)

# 4. Save the table back
# We use 'replace' to ensure all your new "Advantage" columns are added to her clean table
df_advanced.to_sql('clean_combined_football_stats', conn, if_exists='replace', index=False)
conn.close()

print("Advanced Feature Engineering Complete! SQL table updated with KPI differentials.")


#now doing feature engineering for the combined_player_stats table

conn = sqlite3.connect('data/database/rutgersfootball.db')

query = "SELECT * FROM clean_combined_player_stats"
df_players = pd.read_sql_query(query, conn)

def apply_player_feature_engineering(df):
    # Pivot so each player has one row with columns for Yards, TD, etc.
    df_pivot = df.pivot_table(index=['Player', 'Category'], 
                              columns='Stat', 
                              values='Value').reset_index().fillna(0)
    
    # Calculate Total Team Stats for Market Share analysis
    # This helps explain if the offense is 'unbalanced' in losses
    team_totals = df_pivot.groupby('Category').agg({
        'Yards': 'sum',
        'TD': 'sum'
    }).rename(columns={'Yards': 'Team_Yards', 'TD': 'Team_TD'})

    df_pivot = df_pivot.merge(team_totals, on='Category')

    # CREATE CLUES FOR LOSING ANALYSIS:
    # 1. Market Share (Over-reliance on one player)
    df_pivot['Yardage_Share'] = (df_pivot['Yards'] / df_pivot['Team_Yards']).round(3)
    
    # 2. Touchdown Dependency 
    df_pivot['TD_Share'] = (df_pivot['TD'] / df_pivot['Team_TD']).round(3)

    return df_pivot

# Run the engineering
df_player_advanced = apply_player_feature_engineering(df_players)

# Save to the SQL database so you can query it later
df_player_advanced.to_sql('advanced_player_stats', conn, if_exists='replace', index=False)
conn.close()

print("Player Analysis Complete! Data saved to 'advanced_player_stats' table.")

#now adding features for the passing, rushing, and receiving tables

conn = sqlite3.connect('data/database/rutgersfootball.db')

# --- 1. PASSING ADVANCED FEATURES ---
df_pass = pd.read_sql("SELECT * FROM clean_passing", conn)
def engineer_passing(df):
    # TD/INT Ratio (Safety: replace 0 INT with 1 to avoid infinity)
    df['TD_INT_Ratio'] = (df['TD'] / df['Interceptions'].replace(0, 1)).round(2)
    # Interception Rate (Careless Mistake metric)
    df['INT_Rate'] = (df['Interceptions'] / df['Att'].replace(0, 1)).round(4)
    # Yards Per Attempt
    df['YPA'] = (df['Yards'] / df['Att'].replace(0, 1)).round(2)
    return df

df_pass_adv = engineer_passing(df_pass)
df_pass_adv.to_sql('clean_passing', conn, if_exists='replace', index=False)

# --- 2. RUSHING ADVANCED FEATURES ---
df_rush = pd.read_sql("SELECT * FROM clean_rushing", conn)
def engineer_rushing(df):
    # TD per Attempt
    df['TD_Rate'] = (df['TD'] / df['Attempts'].replace(0, 1)).round(4)
    # Relative Performance (Workload vs Efficiency)
    avg_team_yds = df['Net_Yards'].mean()
    df['Above_Avg_Yards'] = (df['Net_Yards'] - avg_team_yds).round(2)
    return df

df_rush_adv = engineer_rushing(df_rush)
df_rush_adv.to_sql('clean_rushing', conn, if_exists='replace', index=False)

# --- 3. RECEIVING ADVANCED FEATURES ---
df_rec = pd.read_sql("SELECT * FROM clean_receiving", conn)
def engineer_receiving(df):
    # Yards Per Reception
    df['YPR'] = (df['Yards'] / df['Receptions'].replace(0, 1)).round(2)
    # Scoring Reliance
    total_tds = df['TD'].sum()
    df['TD_Contribution_Pct'] = (df['TD'] / (total_tds if total_tds > 0 else 1)).round(3)
    return df

df_rec_adv = engineer_receiving(df_rec)
df_rec_adv.to_sql('clean_receiving', conn, if_exists='replace', index=False)

conn.close()
print("All individual file feature engineering complete!")


#finally some feature engineering for schedule, player dataset and team stats files

conn = sqlite3.connect('data/database/rutgersfootball.db')

# --- 1. SCHEDULE ANALYSIS (Rest & Pressure) ---
df_sched = pd.read_sql("SELECT * FROM clean_schedule", conn)
def engineer_schedule(df):
    df['Date'] = pd.to_datetime(df['Date'])
    # Days since last game
    df['Days_Rest'] = df['Date'].diff().dt.days.fillna(7) # Default first game to 7
    
    # Identify "Close Games" (1 possession / 8 points)
    # Partner's cleaning script should have Rutgers_Score and Opponent_Score 
    # if it doesn't, we can skip or add logic to parse 'Result'
    return df

df_sched_adv = engineer_schedule(df_sched)
df_sched_adv.to_sql('clean_schedule', conn, if_exists='replace', index=False)

# --- 2. PLAYER VERSATILITY (Total Impact) ---
df_p_data = pd.read_sql("SELECT * FROM clean_player_dataset", conn)
def engineer_versatility(df):
    # Total Yards (all categories)
    df['Total_Utility_Yards'] = df['Rush_Yds'] + df['Rec_Yds'] + df['Pass_Yds']
    # Total TDs
    df['Total_Utility_TDs'] = df['Rush_TD'] + df['Rec_TD'] + df['Pass_TD']
    # Versatility Score: Does the player produce in more than one category?
    df['Is_Dual_Threat'] = ((df['Rush_Yds'] > 50) & (df['Rec_Yds'] > 50)).astype(int)
    return df

df_p_adv = engineer_versatility(df_p_data)
df_p_adv.to_sql('clean_player_dataset', conn, if_exists='replace', index=False)

# --- 3. TEAM STATS (Efficiency) ---
df_t_stats = pd.read_sql("SELECT * FROM clean_team_stats", conn)

# 1. Clean up Metric names immediately
# This removes the "3rd" number issue that causes the '3_r' collision
df_t_stats['Metric'] = df_t_stats['Metric'].str.replace('3rd', 'Third').str.replace('4th', 'Fourth')
df_t_stats = df_t_stats.dropna(subset=['Metric'])

# 2. Pivot the data
df_t_pivot = pd.pivot_table(df_t_stats, values=['Rutgers', 'Opponents'], columns='Metric', aggfunc='first')

# 3. Create unique column names using a counter to prevent ANY duplicate
new_cols = []
seen = {}

for col in df_t_pivot.columns.values:
    # Build a base name: e.g., "Rutgers_Third_Down_Conv"
    base = f"{col[0]}_{col[1]}".replace(' ', '_').replace('%', 'Pct').replace('-', '_')
    
    # If the name is already in our list, append a number to make it unique
    if base in seen:
        seen[base] += 1
        final_name = f"{base}_{seen[base]}"
    else:
        seen[base] = 0
        final_name = base
        
    new_cols.append(final_name)

df_t_pivot.columns = new_cols
df_t_pivot = df_t_pivot.reset_index(drop=True)

# 4. Math Logic (Finding columns flexibly since names changed)
off_col = [c for c in df_t_pivot.columns if 'Total_Offense' in c and 'Rutgers' in c]
pts_col = [c for c in df_t_pivot.columns if 'Scoring' in c and 'Rutgers' in c]

if off_col and pts_col:
    df_t_pivot['Rutgers_Pts_Per_Yard'] = (df_t_pivot[pts_col[0]] / df_t_pivot[off_col[0]]).round(4)

# 5. Save with a fresh start
df_t_pivot.to_sql('advanced_team_stats', conn, if_exists='replace', index=False)

conn.close()
print("All remaining files have been feature engineered!")