import os
import sqlite3
import warnings

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings('ignore')

SCARLET = '#CC0033'
WIN_CLR = '#1D9E75'
LOSS_CLR = '#CC0033'
OPP_CLR = '#5F5E5A'
DARK_GRAY = '#2C2C2A'
MID_GRAY = '#888780'
LIGHT_BG = '#F8F5F0'

sns.set_theme(
    style='whitegrid',
    font='DejaVu Sans',
    rc={
        'axes.facecolor': LIGHT_BG,
        'figure.facecolor':'#FFFFFF',
        'grid.color':'#DEDAD5',
        'grid.linewidth': 0.6,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'text.color': DARK_GRAY,
        'axes.labelcolor': DARK_GRAY,
        'xtick.color': MID_GRAY,
        'ytick.color': MID_GRAY,
    }
)

conn = sqlite3.connect('data/database/rutgersfootball.db')
df_games = pd.read_sql("SELECT * FROM clean_combined_football_stats", conn)
df_schedule = pd.read_sql("SELECT * FROM clean_schedule", conn)
df_rushing = pd.read_sql("SELECT * FROM clean_rushing", conn)
df_receiving = pd.read_sql("SELECT * FROM clean_receiving", conn)
df_passing = pd.read_sql("SELECT * FROM clean_passing", conn)
df_team = pd.read_sql("SELECT * FROM clean_team_stats", conn)
conn.close()

# use clean_schedule as ground-truth W/L
df_schedule['Win_Loss'] = df_schedule['Result'].str.strip().str[0]
df_schedule['Rutgers_Score'] = df_schedule['Result'].str.extract(r'(\d+)-').astype(int)
df_schedule['Opponent_Score'] = df_schedule['Result'].str.extract(r'-(\d+)').astype(int)

schedule_wl = df_schedule.set_index('Opponent')['Win_Loss'].to_dict()
score_rut = df_schedule.set_index('Opponent')['Rutgers_Score'].to_dict()
score_opp = df_schedule.set_index('Opponent')['Opponent_Score'].to_dict()

df_games['Win_Loss'] = df_games['Opponent'].map(schedule_wl)
df_games['Rutgers_Score'] = df_games['Opponent'].map(score_rut)
df_games['Opponent_Score'] = df_games['Opponent'].map(score_opp)

df_games['Is_Win'] = (df_games['Win_Loss'] == 'W').astype(int)
df_games['Point_Diff'] = df_games['Rutgers_Score'] - df_games['Opponent_Score']
df_games['TO_Diff'] = df_games['Opp_Turnovers'] - df_games['Rutgers_Turnovers']

game_order = list(df_schedule['Opponent'])
df_games['_idx'] = df_games['Opponent'].map({o: i for i, o in enumerate(game_order)})
df_games = df_games.sort_values('_idx').reset_index(drop=True)

os.makedirs(os.path.join('results', 'visualizationchartsgraphs'), exist_ok=True)


def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


#scocre bar chart
def plot_score_bars():
    fig, ax = plt.subplots(figsize=(13, 5))
    rut_colors = [WIN_CLR if wl == 'W' else LOSS_CLR for wl in df_schedule['Win_Loss']]
    for i, opp in enumerate(game_order):
        rs = score_rut[opp]; os_ = score_opp[opp]; wl = schedule_wl[opp]
        clr = WIN_CLR if wl == 'W' else LOSS_CLR
        ax.bar(i - 0.19, rs,  width=0.38, color=clr,    alpha=0.88, zorder=3)
        ax.bar(i + 0.19, os_, width=0.38, color=OPP_CLR, alpha=0.50, zorder=3)
        ax.text(i - 0.19, rs  + 0.5, str(rs),  ha='center', va='bottom', fontsize=8, fontweight='bold', color=DARK_GRAY)
        ax.text(i + 0.19, os_ + 0.5, str(os_), ha='center', va='bottom', fontsize=8, color=MID_GRAY)
    ax.set_xticks(range(len(game_order)))
    ax.set_xticklabels(game_order, rotation=35, ha='right', fontsize=9.5)
    ax.set_xlabel(''); ax.set_ylabel('Points', fontsize=11)
    ax.set_title('Score by Game — Rutgers vs Opponent', fontsize=13, fontweight='bold', pad=12)
    handles = [mpatches.Patch(color=WIN_CLR, label='Rutgers (W)'),
               mpatches.Patch(color=LOSS_CLR, label='Rutgers (L)'),
               mpatches.Patch(color=OPP_CLR, alpha=0.50, label='Opponent')]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '01_score_by_game.png'))


#point diff
def plot_point_differential():
    df = df_schedule.copy()
    df['Point_Diff'] = df['Rutgers_Score'] - df['Opponent_Score']
    colors = [WIN_CLR if wl == 'W' else LOSS_CLR for wl in df['Win_Loss']]
    fig, ax = plt.subplots(figsize=(13, 5))
    sns.barplot(data=df, x='Opponent', y='Point_Diff', palette=colors,
                order=game_order, width=0.65, alpha=0.88, ax=ax, legend=False)
    ax.axhline(0, color=DARK_GRAY, linewidth=0.8, zorder=4)
    df_idx = df.set_index('Opponent')
    for i, opp in enumerate(game_order):
        d = df_idx.loc[opp, 'Point_Diff']
        ypos = d + 0.5 if d >= 0 else d - 1.5
        ax.text(i, ypos, f'{d:+d}', ha='center', va='bottom' if d >= 0 else 'top',
                fontsize=9, fontweight='bold', color=DARK_GRAY)
    ax.set_xticklabels(game_order, rotation=35, ha='right', fontsize=9.5)
    ax.set_xlabel(''); ax.set_ylabel('Point Differential', fontsize=11)
    ax.set_title('Point Differential — Win/Loss by Margin', fontsize=13, fontweight='bold', pad=12)
    handles = [mpatches.Patch(color=WIN_CLR, label='Win'), mpatches.Patch(color=LOSS_CLR, label='Loss')]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '02_point_differential.png'))


#total yards
def plot_total_yards():
    fig, ax = plt.subplots(figsize=(13, 5))
    df_idx = df_games.set_index('Opponent')
    for i, opp in enumerate(game_order):
        row = df_idx.loc[opp]
        clr = WIN_CLR if row['Win_Loss'] == 'W' else LOSS_CLR
        ax.bar(i - 0.19, row['Rutgers_TotalYards'], width=0.38, color=clr,    alpha=0.88, zorder=3)
        ax.bar(i + 0.19, row['Opp_TotalYards'],     width=0.38, color=OPP_CLR, alpha=0.50, zorder=3)
    ax.set_xticks(range(len(game_order)))
    ax.set_xticklabels(game_order, rotation=35, ha='right', fontsize=9.5)
    ax.set_xlabel(''); ax.set_ylabel('Total Yards', fontsize=11)
    ax.set_title('Total Offensive Yards — Rutgers vs Opponent', fontsize=13, fontweight='bold', pad=12)
    handles = [mpatches.Patch(color=WIN_CLR, label='Rutgers (W)'),
               mpatches.Patch(color=LOSS_CLR, label='Rutgers (L)'),
               mpatches.Patch(color=OPP_CLR, alpha=0.50, label='Opponent')]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '03_total_yards.png'))


#rushing leaders
def plot_rushing_leaders():
    df = df_rushing[df_rushing['Net_Yards'] > 0].sort_values('Net_Yards').reset_index(drop=True)
    colors = [SCARLET if y == df['Net_Yards'].max() else '#B0AEAA' for y in df['Net_Yards']]
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=df, y='Player', x='Net_Yards', palette=colors,
                orient='h', alpha=0.88, ax=ax, legend=False)
    for i, (_, row) in enumerate(df.iterrows()):
        ax.text(row['Net_Yards'] + 10, i,
                f"{int(row['Net_Yards'])} yds  |  {int(row['TD'])} TD",
                va='center', fontsize=8.5, color=DARK_GRAY)
    ax.set_xlim(0, df['Net_Yards'].max() + 230)
    ax.set_xlabel('Net Rushing Yards', fontsize=11); ax.set_ylabel('')
    ax.set_title('Rushing Leaders — 2025 Season', fontsize=13, fontweight='bold', pad=12)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '04_rushing_leaders.png'))


#rec leaders
def plot_receiving_leaders():
    df = df_receiving.sort_values('Yards').reset_index(drop=True)
    colors = [SCARLET if y == df['Yards'].max() else '#B0AEAA' for y in df['Yards']]
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=df, y='Player', x='Yards', palette=colors,
                orient='h', alpha=0.88, ax=ax, legend=False)
    for i, (_, row) in enumerate(df.iterrows()):
        ax.text(row['Yards'] + 8, i,
                f"{int(row['Yards'])} yds  |  {int(row['Receptions'])} rec  |  {int(row['TD'])} TD",
                va='center', fontsize=8.5, color=DARK_GRAY)
    ax.set_xlim(0, df['Yards'].max() + 380)
    ax.set_xlabel('Receiving Yards', fontsize=11); ax.set_ylabel('')
    ax.set_title('Receiving Leaders — 2025 Season', fontsize=13, fontweight='bold', pad=12)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '05_receiving_leaders.png'))


# yards and margin scatterplot
def plot_scatter_yards_vs_margin():
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=df_games, x='Rutgers_TotalYards', y='Point_Diff',
                    hue='Win_Loss', palette={'W': WIN_CLR, 'L': LOSS_CLR},
                    s=110, alpha=0.88, edgecolor='white', linewidth=0.7, ax=ax)
    sns.regplot(data=df_games, x='Rutgers_TotalYards', y='Point_Diff',
                scatter=False, line_kws={'color': MID_GRAY, 'linewidth': 1.3,
                                         'linestyle': '--', 'alpha': 0.6}, ax=ax)
    for _, row in df_games.iterrows():
        ax.annotate(row['Opponent'], (row['Rutgers_TotalYards'], row['Point_Diff']),
                    textcoords='offset points', xytext=(6, 4), fontsize=7.5, color=DARK_GRAY)
    ax.axhline(0, color=DARK_GRAY, linewidth=0.7)
    ax.set_xlabel('Rutgers Total Yards', fontsize=11)
    ax.set_ylabel('Point Differential', fontsize=11)
    ax.set_title('Offensive Output vs Game Margin', fontsize=13, fontweight='bold', pad=12)
    ax.legend(title='Result', fontsize=9, title_fontsize=9)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '06_scatter_yards_margin.png'))


# turnovers v margin
def plot_scatter_turnovers():
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.scatterplot(data=df_games, x='TO_Diff', y='Point_Diff',
                    hue='Win_Loss', palette={'W': WIN_CLR, 'L': LOSS_CLR},
                    s=110, alpha=0.88, edgecolor='white', linewidth=0.7, ax=ax)
    for _, row in df_games.iterrows():
        ax.annotate(row['Opponent'], (row['TO_Diff'], row['Point_Diff']),
                    textcoords='offset points', xytext=(5, 5), fontsize=7.5, color=DARK_GRAY)
    ax.axhline(0, color=DARK_GRAY, linewidth=0.7)
    ax.axvline(0, color=DARK_GRAY, linewidth=0.7)
    ax.set_xlabel('Turnover Differential (Opp − Rutgers)', fontsize=11)
    ax.set_ylabel('Point Differential', fontsize=11)
    ax.set_title('Turnover Differential vs Game Margin', fontsize=13, fontweight='bold', pad=12)
    ax.legend(title='Result', fontsize=9, title_fontsize=9)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '07_scatter_turnovers.png'))


# 3rd down
def plot_scatter_3rd_down():
    df = df_games.copy()
    df['3rd_Pct'] = df['Rutgers_3rdPct'] * 100
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.scatterplot(data=df, x='3rd_Pct', y='Point_Diff',
                    hue='Win_Loss', palette={'W': WIN_CLR, 'L': LOSS_CLR},
                    s=110, alpha=0.88, edgecolor='white', linewidth=0.7, ax=ax)
    sns.regplot(data=df, x='3rd_Pct', y='Point_Diff',
                scatter=False, line_kws={'color': MID_GRAY, 'linewidth': 1.3,
                                         'linestyle': '--', 'alpha': 0.6}, ax=ax)
    for _, row in df.iterrows():
        ax.annotate(row['Opponent'], (row['3rd_Pct'], row['Point_Diff']),
                    textcoords='offset points', xytext=(5, 4), fontsize=7.5, color=DARK_GRAY)
    ax.axhline(0, color=DARK_GRAY, linewidth=0.7)
    ax.set_xlabel('Rutgers 3rd-Down Conv. %', fontsize=11)
    ax.set_ylabel('Point Differential', fontsize=11)
    ax.set_title('3rd-Down Efficiency vs Game Margin', fontsize=13, fontweight='bold', pad=12)
    ax.legend(title='Result', fontsize=9, title_fontsize=9)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '08_scatter_3rddown.png'))


# corr heatmap
def plot_correlation_heatmap():
    cols = {
        'Rutgers_TotalYards': 'Rut Total Yards',
        'Opp_TotalYards': 'Opp Total Yards',
        'Rutgers_RushYards': 'Rut Rush Yards',
        'Rutgers_PassYards': 'Rut Pass Yards',
        'Rutgers_Turnovers': 'Rut Turnovers',
        'Opp_Turnovers': 'Opp Turnovers',
        'Rutgers_3rdPct': 'Rut 3rd-Down %',
        'Opp_3rdPct': 'Opp 3rd-Down %',
        'Rutgers_PenaltyYards': 'Rut Penalty Yds',
        'Rutgers_TOP_sec': 'Rut Time-of-Poss',
        'Point_Diff': 'Point Diff',
    }
    corr = df_games[list(cols.keys())].rename(columns=cols).corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt='.2f', annot_kws={'size': 8, 'weight': 'bold'},
                cmap='RdYlGn', vmin=-1, vmax=1,
                linewidths=0.5, linecolor='white', square=True, ax=ax,
                cbar_kws={'shrink': 0.75, 'label': 'Correlation coefficient'})
    ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha='right', fontsize=8.5)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=8.5)
    ax.set_facecolor('#FFFFFF')
    ax.set_title('Correlation Heatmap — Game Statistics', fontsize=13, fontweight='bold', pad=14)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '09_correlation_heatmap.png'))


# time of poss
def plot_time_of_possession():
    df = df_games.copy()
    df['Rut_TOP_pct'] = df['Rutgers_TOP_sec'] / (df['Rutgers_TOP_sec'] + df['Opp_TOP_sec']) * 100
    df['Opp_TOP_pct'] = 100 - df['Rut_TOP_pct']
    colors = [WIN_CLR if wl == 'W' else LOSS_CLR for wl in df.set_index('Opponent').loc[game_order, 'Win_Loss']]
    df_ordered = df.set_index('Opponent').loc[game_order].reset_index()
    fig, ax = plt.subplots(figsize=(13, 4.5))
    sns.barplot(data=df_ordered, x='Opponent', y='Rut_TOP_pct', palette=colors,
                order=game_order, alpha=0.88, ax=ax, legend=False)
    for i, (_, row) in enumerate(df_ordered.iterrows()):
        ax.bar(i, row['Opp_TOP_pct'], bottom=row['Rut_TOP_pct'],
               color=OPP_CLR, alpha=0.38, zorder=3)
        rt = int(row['Rutgers_TOP_sec'])
        mins, secs = divmod(rt, 60)
        ax.text(i, row['Rut_TOP_pct'] / 2, f"{mins}:{secs:02d}",
                ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    ax.axhline(50, color='white', linewidth=1.2, linestyle='--', alpha=0.7, zorder=4)
    ax.set_xticklabels(game_order, rotation=35, ha='right', fontsize=9.5)
    ax.set_xlabel(''); ax.set_ylabel('% Time of Possession', fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_title('Time of Possession Share per Game', fontsize=13, fontweight='bold', pad=12)
    handles = [mpatches.Patch(color=WIN_CLR, label='Rutgers (W)'),
               mpatches.Patch(color=LOSS_CLR, label='Rutgers (L)'),
               mpatches.Patch(color=OPP_CLR, alpha=0.38, label='Opponent')]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '10_time_of_possession.png'))


# summary of team stats
def plot_team_stats_summary():
    metric_map = {
        'Points Per Game': ('PPG', True),
        'Rushing Yardage': ('Rush Yards', True),
        'Passing Yardage': ('Pass Yards', True),
        'Total Offense': ('Total Offense', True),
        'First Downs': ('First Downs', True),
        'Sacks By-Yards_Sacks': ('Sacks Allowed', False),
    }
    labels, rut_vals, opp_vals, advantages = [], [], [], []
    for key, (label, hib) in metric_map.items():
        row = df_team[df_team['Metric'] == key]
        if not row.empty:
            rv = float(row['Rutgers'].values[0])
            ov = float(row['Opponents'].values[0])
            labels.append(label); rut_vals.append(rv); opp_vals.append(ov)
            advantages.append(rv > ov if hib else rv < ov)
    fig, ax = plt.subplots(figsize=(11, 5))
    for i, (label, rv, ov, adv) in enumerate(zip(labels, rut_vals, opp_vals, advantages)):
        clr = WIN_CLR if adv else LOSS_CLR
        ax.bar(i - 0.2, rv, width=0.38, color=clr,    alpha=0.88, zorder=3)
        ax.bar(i + 0.2, ov, width=0.38, color=OPP_CLR, alpha=0.50, zorder=3)
        ax.text(i - 0.2, rv + rv * 0.01, f'{rv:.0f}', ha='center', va='bottom',
                fontsize=8.5, fontweight='bold', color=DARK_GRAY)
        ax.text(i + 0.2, ov + ov * 0.01, f'{ov:.0f}', ha='center', va='bottom',
                fontsize=8.5, color=MID_GRAY)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=10)
    ax.set_xlabel('')
    ax.set_title('Season Team Stats — Rutgers vs Opponents', fontsize=13, fontweight='bold', pad=12)
    handles = [mpatches.Patch(color=WIN_CLR,  label='Rutgers (advantage)'),
               mpatches.Patch(color=LOSS_CLR, label='Rutgers (disadvantage)'),
               mpatches.Patch(color=OPP_CLR,  alpha=0.50, label='Opponents')]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85)
    save(fig, os.path.join('results', 'visualizationchartsgraphs', '11_team_stats_summary.png'))


#main
print("Generating Rutgers Football 2025 visualizations (seaborn)...\n")
plot_score_bars()
plot_point_differential()
plot_total_yards()
plot_rushing_leaders()
plot_receiving_leaders()
plot_scatter_yards_vs_margin()
plot_scatter_turnovers()
plot_scatter_3rd_down()
plot_correlation_heatmap()
plot_time_of_possession()
plot_team_stats_summary()
print("\nAll 11 figures saved to results/visualizationchartsgraphs/")