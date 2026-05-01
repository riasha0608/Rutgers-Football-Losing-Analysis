import sqlite3
import pandas as pd
 
conn = sqlite3.connect('data/database/rutgersfootball.db')
 
#raw_rutgers_schedule_2025
df_schedule = pd.read_sql("SELECT * FROM raw_rutgers_schedule_2025", conn)
 
df_schedule['Date'] = pd.to_datetime(df_schedule['Date'], format='%m/%d/%Y')
df_schedule['Win_Loss'] = df_schedule['Result'].str.split(' ').str[0]
df_schedule['Score'] = df_schedule['Result'].str.split(' ').str[1]
df_schedule['Rutgers_Score'] = df_schedule['Score'].str.split('-').str[0].astype(int)
df_schedule['Opponent_Score'] = df_schedule['Score'].str.split('-').str[1].astype(int)
df_schedule['Point_Differential'] = df_schedule['Rutgers_Score'] - df_schedule['Opponent_Score']
df_schedule = df_schedule.drop(columns=['Result', 'Score'])
 
df_schedule.to_sql('clean_schedule', conn, if_exists='replace', index=False)
print(f"clean_schedule: {df_schedule.shape[0]} rows")
 

# raw_rutgers_team_stats_2025
df_team = pd.read_sql("SELECT * FROM raw_rutgers_team_stats_2025", conn)
 
df_team['Rutgers'] = pd.to_numeric(df_team['Rutgers'], errors='coerce')
df_team['Opponents'] = pd.to_numeric(df_team['Opponents'], errors='coerce')
 
df_team.to_sql('clean_team_stats', conn, if_exists='replace', index=False)
print(f"clean_team_stats: {df_team.shape[0]} rows")
 

# 3. raw_combined_football_stats
df_combined = pd.read_sql("SELECT * FROM raw_combined_football_stats", conn)
 
def split_pair(series, rutgers_name, opp_name, cast_func=float):
    """Split 'RUT_val / OPP_val' or 'RUT_val/OPP_val' into two typed columns."""
    normalised = series.str.replace(r'\s*/\s*', '|', regex=True)
    split = normalised.str.split('|', expand=True)
    return split[0].str.strip().apply(cast_func), split[1].str.strip().apply(cast_func)
 
def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None
 

df_combined['Win_Loss'] = df_combined['Score'].str.split('-').apply(
    lambda parts: 'W' if int(parts[0]) > int(parts[1]) else 'L'
)
df_combined['Rutgers_Score'] = df_combined['Score'].str.split('-').str[0].astype(int)
df_combined['Opponent_Score'] = df_combined['Score'].str.split('-').str[1].astype(int)
df_combined['Point_Differential'] = df_combined['Rutgers_Score'] - df_combined['Opponent_Score']
 
for col, rut_col, opp_col in [
    ('Total',        'Rutgers_FirstDowns',       'Opp_FirstDowns'),
    ('Rush',         'Rutgers_RushFirstDowns',   'Opp_RushFirstDowns'),
    ('Pass',         'Rutgers_PassFirstDowns',   'Opp_PassFirstDowns'),
    ('Pen',          'Rutgers_PenFirstDowns',    'Opp_PenFirstDowns'),
    ('Return-Yards', 'Rutgers_ReturnYards',      'Opp_ReturnYards'),
]:
    df_combined[rut_col], df_combined[opp_col] = split_pair(df_combined[col], rut_col, opp_col, int)
 
df_combined['Rutgers_Turnovers'], df_combined['Opp_Turnovers'] = split_pair(
    df_combined['Turnovers'], 'Rutgers_Turnovers', 'Opp_Turnovers', int
)
df_combined['Turnover_Differential'] = df_combined['Opp_Turnovers'] - df_combined['Rutgers_Turnovers']
 
for col, rut_col, opp_col in [
    ('AvgYdsRush', 'Rutgers_AvgYdsRush', 'Opp_AvgYdsRush'),
    ('AvgYdsPass', 'Rutgers_AvgYdsPass', 'Opp_AvgYdsPass'),
    ('AvgYdsPlay', 'Rutgers_AvgYdsPlay', 'Opp_AvgYdsPlay'),
]:
    df_combined[rut_col], df_combined[opp_col] = split_pair(df_combined[col], rut_col, opp_col, float)
 
yards_split = df_combined['Yards'].str.replace(' ', '').str.split('/', expand=True)
df_combined['Rutgers_PassYards'] = yards_split[0].astype(int)
df_combined['Opp_PassYards'] = yards_split[1].astype(int)
 
att_yards = df_combined['Att-Yards'].str.split(' / ', expand=True)
rut_parts = att_yards[0].str.split('-', expand=True)
opp_parts = att_yards[1].str.split('-', expand=True)
df_combined['Rutgers_RushAtt']  = rut_parts[0].astype(int)
df_combined['Rutgers_RushYards'] = rut_parts[1].astype(int)
df_combined['Opp_RushAtt']      = opp_parts[0].astype(int)
df_combined['Opp_RushYards']    = opp_parts[1].astype(int)
 
plays_yards = df_combined['Plays-Yards'].str.split(' / ', expand=True)
rut_py = plays_yards[0].str.split('-', expand=True)
opp_py = plays_yards[1].str.split('-', expand=True)
df_combined['Rutgers_TotalPlays'] = rut_py[0].astype(int)
df_combined['Rutgers_TotalYards'] = rut_py[1].astype(int)
df_combined['Opp_TotalPlays']     = opp_py[0].astype(int)
df_combined['Opp_TotalYards']     = opp_py[1].astype(int)
 
comp_att = df_combined['Comp-Att-Int'].str.split(' / ', expand=True)
rut_cai = comp_att[0].str.split('-', expand=True)
opp_cai = comp_att[1].str.split('-', expand=True)
df_combined['Rutgers_Comp'] = rut_cai[0].astype(int)
df_combined['Rutgers_Att']  = rut_cai[1].astype(int)
df_combined['Rutgers_INT']  = rut_cai[2].astype(int)
df_combined['Opp_Comp']     = opp_cai[0].astype(int)
df_combined['Opp_Att']      = opp_cai[1].astype(int)
df_combined['Opp_INT']      = opp_cai[2].astype(int)
 
def parse_down_conv(series, rut_made, rut_att, opp_made, opp_att):
    split = series.str.split(' / ', expand=True)
    rut = split[0].str.split('-', expand=True)
    opp = split[1].str.split('-', expand=True)
    return rut[0].astype(int), rut[1].astype(int), opp[0].astype(int), opp[1].astype(int)
 
df_combined['Rutgers_3rdMade'], df_combined['Rutgers_3rdAtt'], \
df_combined['Opp_3rdMade'],    df_combined['Opp_3rdAtt'] = \
    parse_down_conv(df_combined['ThirdDownConversions'], *[''] * 4)
 
df_combined['Rutgers_4thMade'], df_combined['Rutgers_4thAtt'], \
df_combined['Opp_4thMade'],    df_combined['Opp_4thAtt'] = \
    parse_down_conv(df_combined['FourthDownConversions'], *[''] * 4)
 
df_combined['Rutgers_3rdPct'] = (
    df_combined['Rutgers_3rdMade'] / df_combined['Rutgers_3rdAtt'].replace(0, None)
).round(3)
df_combined['Opp_3rdPct'] = (
    df_combined['Opp_3rdMade'] / df_combined['Opp_3rdAtt'].replace(0, None)
).round(3)
 
punts = df_combined['PuntsAvg'].str.split(' / ', expand=True)
rut_p = punts[0].str.split('-', expand=True)
opp_p = punts[1].str.split('-', expand=True)
df_combined['Rutgers_Punts']   = rut_p[0].astype(int)
df_combined['Rutgers_PuntAvg'] = rut_p[1].apply(safe_float)
df_combined['Opp_Punts']       = opp_p[0].astype(int)
df_combined['Opp_PuntAvg']     = opp_p[1].apply(safe_float)

pen = df_combined['PenaltiesYards'].str.split(' / ', expand=True)
rut_pen = pen[0].str.split('-', expand=True)
opp_pen = pen[1].str.split('-', expand=True)
df_combined['Rutgers_Penalties']    = rut_pen[0].astype(int)
df_combined['Rutgers_PenaltyYards'] = rut_pen[1].astype(int)
df_combined['Opp_Penalties']        = opp_pen[0].astype(int)
df_combined['Opp_PenaltyYards']     = opp_pen[1].astype(int)
 
def top_to_seconds(time_str):
    try:
        m, s = time_str.strip().split(':')
        return int(m) * 60 + int(s)
    except Exception:
        return None
 
top_split = df_combined['TimeOfPossession'].str.split(' / ', expand=True)
df_combined['Rutgers_TOP_sec'] = top_split[0].apply(top_to_seconds)
df_combined['Opp_TOP_sec']     = top_split[1].apply(top_to_seconds)
 
def margin_to_seconds(time_str):
    try:
        time_str = time_str.strip()
        negative = time_str.startswith('-')
        time_str = time_str.lstrip('-')
        m, s = time_str.split(':')
        total = int(m) * 60 + int(s)
        return -total if negative else total
    except Exception:
        return None
 
df_combined['TOP_Margin_sec'] = df_combined['TopMargin'].apply(margin_to_seconds)
 
raw_cols = [
    'Score', 'Total', 'Rush', 'Pass', 'Pen', 'Att-Yards', 'Comp-Att-Int',
    'Yards', 'Plays-Yards', 'Return-Yards', 'Turnovers', 'ThirdDownConversions',
    'FourthDownConversions', 'TimeOfPossession', 'TopMargin', 'AvgYdsRush',
    'AvgYdsPass', 'AvgYdsPlay', 'PuntsAvg', 'PenaltiesYards'
]
df_combined = df_combined.drop(columns=raw_cols)
 
df_combined.to_sql('clean_combined_football_stats', conn, if_exists='replace', index=False)
print(f"clean_combined_football_stats: {df_combined.shape[0]} rows, {df_combined.shape[1]} columns")
 
# pass through
passthrough = [
    ('raw_rutgers_2025_combined_player_stats', 'clean_combined_player_stats'),
    ('raw_rutgers_2025_player_dataset', 'clean_player_dataset'),
    ('raw_rutgers_passing_2025', 'clean_passing'),
    ('raw_rutgers_receiving_2025', 'clean_receiving'),
    ('raw_rutgers_rushing_2025', 'clean_rushing'),
]
 
for raw_table, clean_table in passthrough:
    df = pd.read_sql(f"SELECT * FROM {raw_table}", conn)
    df.to_sql(clean_table, conn, if_exists='replace', index=False)
    print(f"{clean_table}: {df.shape[0]} rows")
 
conn.close()
print("\nAll cleaned tables written to rutgersfootball.db successfully!")