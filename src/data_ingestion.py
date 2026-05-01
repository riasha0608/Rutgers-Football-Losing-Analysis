import pandas as pd
import sqlite3
import os

# This ensures the database folder exists before we try to save to it
if not os.path.exists('data/database'):
    os.makedirs('data/database')

conn = sqlite3.connect('data/database/rutgersfootball.db')

df_combined_football_stats = pd.read_csv('data/rawcsvdatafiles/combined_football_stats.csv')
df_combined_football_stats.to_sql('raw_combined_football_stats', conn, if_exists='replace', index=False)

df_combined_player_stats = pd.read_csv('data/rawcsvdatafiles/rutgers_2025_combined_player_stats.csv')
df_combined_player_stats.to_sql('raw_rutgers_2025_combined_player_stats', conn, if_exists='replace', index=False)

df_player_dataset = pd.read_csv('data/rawcsvdatafiles/rutgers_2025_player_dataset.csv')
df_player_dataset.to_sql('raw_rutgers_2025_player_dataset', conn, if_exists='replace', index=False)

df_passing = pd.read_csv('data/rawcsvdatafiles/rutgers_passing_2025.csv')
df_passing.to_sql('raw_rutgers_passing_2025', conn, if_exists='replace', index=False)

df_receiving = pd.read_csv('data/rawcsvdatafiles/rutgers_receiving_2025.csv')
df_receiving.to_sql('raw_rutgers_receiving_2025', conn, if_exists='replace', index=False)

df_rushing = pd.read_csv('data/rawcsvdatafiles/rutgers_rushing_2025.csv')
df_rushing.to_sql('raw_rutgers_rushing_2025', conn, if_exists='replace', index=False)

df_schedule_2025 = pd.read_csv('data/rawcsvdatafiles/rutgers_schedule_2025.csv')
df_schedule_2025.to_sql('raw_rutgers_schedule_2025', conn, if_exists='replace', index=False)

df_team_stats_2025 = pd.read_csv('data/rawcsvdatafiles/rutgers_team_stats_2025.csv')
df_team_stats_2025.to_sql('raw_rutgers_team_stats_2025', conn, if_exists='replace', index=False)

conn.close()
print("All 8 files loaded into rutgers.db successfully!")