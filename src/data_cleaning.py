import sqlite3
import pandas as pd

conn = sqlite3.connect('data/database/rutgersfootball.db')

def split_pair(series, cast_func=float):
    """
    Split 'RUT_val / OPP_val' or 'RUT_val/OPP_val' into two typed columns.
    Normalises both ' / ' and '/' to a common separator before splitting.
    """
    normalised = series.str.replace(r'\s*/\s*', '|', regex=True)
    split = normalised.str.split('|', expand=True)
    return split[0].str.strip().apply(cast_func), split[1].str.strip().apply(cast_func)

def top_to_seconds(time_str):
    """Convert 'MM:SS' string to total seconds (int)."""
    try:
        m, s = time_str.strip().split(':')
        return int(m) * 60 + int(s)
    except Exception:
        return None

def margin_to_seconds(time_str):
    """Convert signed 'MM:SS' margin string to signed seconds (int)."""
    try:
        time_str = time_str.strip()
        negative = time_str.startswith('-')
        time_str = time_str.lstrip('-')
        m, s = time_str.split(':')
        total = int(m) * 60 + int(s)
        return -total if negative else total
    except Exception:
        return None

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def standardize_player_name(name):
    """
    Convert 'Last, First' to 'First Last'.
    Leaves names already in 'First Last' format unchanged.
    """
    if pd.isna(name):
        return name
    name = name.strip()
    if ',' in name:
        parts = name.split(',', 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def parse_down_conv(series):
    """
    Parse '1-10 / 5-10' style down conversion strings.
    Returns (rut_made, rut_att, opp_made, opp_att) as int Series.
    """
    split = series.str.split(' / ', expand=True)
    rut = split[0].str.split('-', expand=True)
    opp = split[1].str.split('-', expand=True)
    return (
        rut[0].astype(int), rut[1].astype(int),
        opp[0].astype(int), opp[1].astype(int)
    )

#clean_schedule
df_schedule = pd.read_sql("SELECT * FROM clean_schedule", conn)

df_schedule['Date'] = pd.to_datetime(df_schedule['Date'])
df_schedule['Opponent'] = df_schedule['Opponent'].str.strip()
df_schedule['Is_Win'] = (df_schedule['Win_Loss'] == 'W').astype(int)

df_schedule.to_sql('clean_schedule', conn, if_exists='replace', index=False)
print(f"Good clean_schedule:                {df_schedule.shape[0]} rows, {df_schedule.shape[1]} cols")

#clean_team_stats
df_team = pd.read_sql("SELECT * FROM raw_rutgers_team_stats_2025", conn)

df_team['Metric'] = df_team['Metric'].str.strip()

compound_mask = df_team['Rutgers'].str.contains('-', na=False)
simple_rows = df_team[~compound_mask].copy()
compound_rows  = df_team[compound_mask].copy()

simple_rows['Rutgers'] = pd.to_numeric(simple_rows['Rutgers'],   errors='coerce')
simple_rows['Opponents'] = pd.to_numeric(simple_rows['Opponents'], errors='coerce')

compound_suffix_map = {
    'Fumbles-Lost': ('Fumbles', 'FumblesLost'),
    'Penalties-Yards': ('Penalties', 'PenaltyYards'),
    'Punts-Yards': ('Punts', 'PuntYards'),
    'Kickoffs-Yards': ('Kickoffs', 'KickoffYards'),
    '3rd Down Conversions': ('3rdMade', '3rdAtt'),
    '4th Down Conversions': ('4thMade', '4thAtt'),
    'Sacks By-Yards': ('Sacks', 'SackYards'),
    'Field Goals-Attempts': ('FGMade', 'FGAtt'),
}

expanded_records = []
for _, row in compound_rows.iterrows():
    metric = row['Metric']
    rut_parts = str(row['Rutgers']).split('-')
    opp_parts = str(row['Opponents']).split('-')
    suffixes = compound_suffix_map.get(metric, ('Part1', 'Part2'))
    expanded_records.append({'Metric': f"{metric}_{suffixes[0]}", 'Rutgers': float(rut_parts[0]), 'Opponents': float(opp_parts[0])})
    expanded_records.append({'Metric': f"{metric}_{suffixes[1]}", 'Rutgers': float(rut_parts[1]), 'Opponents': float(opp_parts[1])})

df_team_clean = pd.concat([simple_rows, pd.DataFrame(expanded_records)], ignore_index=True)

df_team_clean.to_sql('clean_team_stats', conn, if_exists='replace', index=False)
print(f"Good clean_team_stats:              {df_team_clean.shape[0]} rows, {df_team_clean.shape[1]} cols")

#clean_combined_football_stats
df_combined = pd.read_sql("SELECT * FROM raw_combined_football_stats", conn)

df_combined['Opponent'] = df_combined['Opponent'].str.strip()

df_combined['Rutgers_Score'] = df_combined['Score'].str.split('-').str[0].astype(int)
df_combined['Opponent_Score'] = df_combined['Score'].str.split('-').str[1].astype(int)
df_combined['Win_Loss'] = df_combined.apply(lambda r: 'W' if r['Rutgers_Score'] > r['Opponent_Score'] else 'L', axis=1)
df_combined['Is_Win'] = (df_combined['Win_Loss'] == 'W').astype(int)
df_combined['Point_Differential'] = df_combined['Rutgers_Score'] - df_combined['Opponent_Score']

for col, rut_col, opp_col in [
    ('Total', 'Rutgers_FirstDowns', 'Opp_FirstDowns'),
    ('Rush', 'Rutgers_RushFirstDowns', 'Opp_RushFirstDowns'),
    ('Pass', 'Rutgers_PassFirstDowns', 'Opp_PassFirstDowns'),
    ('Pen', 'Rutgers_PenFirstDowns',  'Opp_PenFirstDowns'),
    ('Return-Yards', 'Rutgers_ReturnYards', 'Opp_ReturnYards'),
    ('Turnovers', 'Rutgers_Turnovers', 'Opp_Turnovers'),
]:
    df_combined[rut_col], df_combined[opp_col] = split_pair(df_combined[col], int)

df_combined['Turnover_Differential'] = df_combined['Opp_Turnovers'] - df_combined['Rutgers_Turnovers']

for col, rut_col, opp_col in [
    ('AvgYdsRush', 'Rutgers_AvgYdsRush', 'Opp_AvgYdsRush'),
    ('AvgYdsPass', 'Rutgers_AvgYdsPass', 'Opp_AvgYdsPass'),
    ('AvgYdsPlay', 'Rutgers_AvgYdsPlay', 'Opp_AvgYdsPlay'),
]:
    df_combined[rut_col], df_combined[opp_col] = split_pair(df_combined[col], float)

yards_split = df_combined['Yards'].str.replace(' ', '').str.split('/', expand=True)
df_combined['Rutgers_PassYards'] = yards_split[0].astype(int)
df_combined['Opp_PassYards'] = yards_split[1].astype(int)

att_yards = df_combined['Att-Yards'].str.split(' / ', expand=True)
rut_ay = att_yards[0].str.split('-', expand=True)
opp_ay = att_yards[1].str.split('-', expand=True)
df_combined['Rutgers_RushAtt'] = rut_ay[0].astype(int)
df_combined['Rutgers_RushYards'] = rut_ay[1].astype(int)
df_combined['Opp_RushAtt'] = opp_ay[0].astype(int)
df_combined['Opp_RushYards'] = opp_ay[1].astype(int)

plays_yards = df_combined['Plays-Yards'].str.split(' / ', expand=True)
rut_py = plays_yards[0].str.split('-', expand=True)
opp_py = plays_yards[1].str.split('-', expand=True)
df_combined['Rutgers_TotalPlays'] = rut_py[0].astype(int)
df_combined['Rutgers_TotalYards'] = rut_py[1].astype(int)
df_combined['Opp_TotalPlays'] = opp_py[0].astype(int)
df_combined['Opp_TotalYards'] = opp_py[1].astype(int)

comp_att = df_combined['Comp-Att-Int'].str.split(' / ', expand=True)
rut_cai = comp_att[0].str.split('-', expand=True)
opp_cai = comp_att[1].str.split('-', expand=True)
df_combined['Rutgers_Comp'] = rut_cai[0].astype(int)
df_combined['Rutgers_Att'] = rut_cai[1].astype(int)
df_combined['Rutgers_Interceptions'] = rut_cai[2].astype(int)
df_combined['Opp_Comp'] = opp_cai[0].astype(int)
df_combined['Opp_Att'] = opp_cai[1].astype(int)
df_combined['Opp_Interceptions'] = opp_cai[2].astype(int)

(df_combined['Rutgers_3rdMade'], df_combined['Rutgers_3rdAtt'],
 df_combined['Opp_3rdMade'], df_combined['Opp_3rdAtt']) = parse_down_conv(df_combined['ThirdDownConversions'])

(df_combined['Rutgers_4thMade'], df_combined['Rutgers_4thAtt'],
 df_combined['Opp_4thMade'], df_combined['Opp_4thAtt']) = parse_down_conv(df_combined['FourthDownConversions'])

df_combined['Rutgers_3rdPct'] = (df_combined['Rutgers_3rdMade'] / df_combined['Rutgers_3rdAtt'].replace(0, None)).round(3)
df_combined['Opp_3rdPct'] = (df_combined['Opp_3rdMade']     / df_combined['Opp_3rdAtt'].replace(0, None)).round(3)

punts = df_combined['PuntsAvg'].str.split(' / ', expand=True)
rut_p = punts[0].str.split('-', expand=True)
opp_p = punts[1].str.split('-', expand=True)
df_combined['Rutgers_Punts'] = rut_p[0].astype(int)
df_combined['Rutgers_PuntAvg'] = rut_p[1].apply(safe_float)
df_combined['Opp_Punts'] = opp_p[0].astype(int)
df_combined['Opp_PuntAvg'] = opp_p[1].apply(safe_float)

pen = df_combined['PenaltiesYards'].str.split(' / ', expand=True)
rut_pen = pen[0].str.split('-', expand=True)
opp_pen = pen[1].str.split('-', expand=True)
df_combined['Rutgers_Penalties'] = rut_pen[0].astype(int)
df_combined['Rutgers_PenaltyYards'] = rut_pen[1].astype(int)
df_combined['Opp_Penalties'] = opp_pen[0].astype(int)
df_combined['Opp_PenaltyYards'] = opp_pen[1].astype(int)

top_split = df_combined['TimeOfPossession'].str.split(' / ', expand=True)
df_combined['Rutgers_TOP_sec'] = top_split[0].apply(top_to_seconds)
df_combined['Opp_TOP_sec'] = top_split[1].apply(top_to_seconds)
df_combined['TOP_Margin_sec'] = df_combined['TopMargin'].apply(margin_to_seconds)

raw_cols = [
    'Score', 'Total', 'Rush', 'Pass', 'Pen', 'Att-Yards', 'Comp-Att-Int',
    'Yards', 'Plays-Yards', 'Return-Yards', 'Turnovers', 'ThirdDownConversions',
    'FourthDownConversions', 'TimeOfPossession', 'TopMargin', 'AvgYdsRush',
    'AvgYdsPass', 'AvgYdsPlay', 'PuntsAvg', 'PenaltiesYards',
]
df_combined = df_combined.drop(columns=raw_cols)

df_combined.to_sql('clean_combined_football_stats', conn, if_exists='replace', index=False)
print(f"Good clean_combined_football_stats: {df_combined.shape[0]} rows, {df_combined.shape[1]} cols")

# clean_player_dataset
df_players = pd.read_sql("SELECT * FROM clean_player_dataset", conn)

df_players['Player'] = df_players['Player'].apply(standardize_player_name)
df_players['Unit'] = df_players['Unit'].str.strip().str.title()
df_players['Is_Offense'] = (df_players['Unit'] == 'Offense').astype(int)
df_players['Is_Defense'] = (df_players['Unit'] == 'Defense').astype(int)

df_players.to_sql('clean_player_dataset', conn, if_exists='replace', index=False)
print(f"Good clean_player_dataset:          {df_players.shape[0]} rows, {df_players.shape[1]} cols")

#clean_passing
df_passing = pd.read_sql("SELECT * FROM clean_passing", conn)

df_passing['Player'] = df_passing['Player'].apply(standardize_player_name)
df_passing = df_passing.rename(columns={'INT': 'Interceptions'})

df_passing.to_sql('clean_passing', conn, if_exists='replace', index=False)
print(f"Good clean_passing:                 {df_passing.shape[0]} rows, {df_passing.shape[1]} cols")

# clean_receiving
df_receiving = pd.read_sql("SELECT * FROM clean_receiving", conn)

df_receiving['Player'] = df_receiving['Player'].apply(standardize_player_name)

df_receiving.to_sql('clean_receiving', conn, if_exists='replace', index=False)
print(f"Good clean_receiving:               {df_receiving.shape[0]} rows, {df_receiving.shape[1]} cols")

#clean_rushing
df_rushing = pd.read_sql("SELECT * FROM clean_rushing", conn)

df_rushing['Player'] = df_rushing['Player'].apply(standardize_player_name)
df_rushing = df_rushing.rename(columns={'Avg': 'Avg_Yards'})

df_rushing.to_sql('clean_rushing', conn, if_exists='replace', index=False)
print(f"Good clean_rushing:                 {df_rushing.shape[0]} rows, {df_rushing.shape[1]} cols")

#clean_combined_player_stats
df_cps = pd.read_sql("SELECT * FROM raw_rutgers_2025_combined_player_stats", conn)

df_cps['Player'] = df_cps['Player'].apply(standardize_player_name)
df_cps['Category'] = df_cps['Category'].str.strip().str.title()

category_dummies = pd.get_dummies(df_cps['Category'], prefix='Cat').astype(int)
df_cps = pd.concat([df_cps, category_dummies], axis=1)

df_cps.to_sql('clean_combined_player_stats', conn, if_exists='replace', index=False)
print(f"Good clean_combined_player_stats:   {df_cps.shape[0]} rows, {df_cps.shape[1]} cols")

#final check
print("\nNull check across all clean tables")
clean_tables = [
    'clean_schedule', 'clean_team_stats', 'clean_combined_football_stats',
    'clean_player_dataset', 'clean_passing', 'clean_receiving',
    'clean_rushing', 'clean_combined_player_stats',
]
all_clear = True
for table in clean_tables:
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    nulls = df.isnull().sum().sum()
    status = "Good" if nulls == 0 else f"{nulls} nulls"
    print(f"  {status}  {table}")
    if nulls > 0:
        all_clear = False

conn.close()
print(f"\n{'All tables clean — no nulls remaining!' if all_clear else 'Some nulls remain — review above.'}")