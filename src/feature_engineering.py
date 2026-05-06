import pandas as pd
import numpy as np
import sqlite3

conn = sqlite3.connect('data/database/rutgersfootball.db')

#data already split up in data_cleaning into rutgers columns vs opponents stats columns

#getting the data from the clean SQL table for this using .read_sql_query function in pandas and storing it into a dataframe
df_for_combined_football_stats = pd.read_sql_query("SELECT * FROM clean_combined_football_stats", conn)

#creating all the different features for combined football stats table by doing differences or percentages
df_for_combined_football_stats['Penalty_Yds_Diff'] = df_for_combined_football_stats['Rutgers_PenaltyYards'] - df_for_combined_football_stats['Opp_PenaltyYards']

#below is assuming total plays is greater than 0 since it is not possible to even have a game with 0 total plays
df_for_combined_football_stats['Penalty_Efficiency'] = df_for_combined_football_stats['Rutgers_PenaltyYards'] / df_for_combined_football_stats['Rutgers_TotalPlays']

#doing the same thing as above for 3rd and 4th down completion percentage since same logic
#if no attempts made for 3rd or 4th down then not possible to have 3rd or 4th down success (made)
#will be using np.where to do this because it is a conditional just like above one
df_for_combined_football_stats['Rutgers_3rdPct'] = np.where(df_for_combined_football_stats['Rutgers_3rdAtt'] == 0, 0, df_for_combined_football_stats['Rutgers_3rdMade'] / df_for_combined_football_stats['Rutgers_3rdAtt'])
df_for_combined_football_stats['Rutgers_4thPct'] = np.where(df_for_combined_football_stats['Rutgers_4thAtt'] == 0, 0, df_for_combined_football_stats['Rutgers_4thMade'] / df_for_combined_football_stats['Rutgers_4thAtt'])

df_for_combined_football_stats['3rdDown_Advantage'] = df_for_combined_football_stats['Rutgers_3rdPct'] - df_for_combined_football_stats['Opp_3rdPct']
df_for_combined_football_stats['YPP_Diff'] = df_for_combined_football_stats['Rutgers_AvgYdsPlay'] - df_for_combined_football_stats['Opp_AvgYdsPlay']

#creating a check here to ensure that if attempts is 0, then completion is also 0 because completion is number of successful attempts so not possible to have more than 0 if attempts is 0
#will be using np.where to do this because it is a conditional depending on values of each row for this column
df_for_combined_football_stats['Rutgers_Comp_Pct'] = np.where(df_for_combined_football_stats['Rutgers_Att'] == 0, 0, df_for_combined_football_stats['Rutgers_Comp'] / df_for_combined_football_stats['Rutgers_Att'])


df_for_combined_football_stats['Punt_Advantage'] = df_for_combined_football_stats['Rutgers_PuntAvg'] - df_for_combined_football_stats['Opp_PuntAvg']

#adding in a date column into this table for future querying
df_schedule = pd.read_sql("SELECT * FROM clean_schedule", conn)
df_for_combined_football_stats = df_for_combined_football_stats.merge(df_schedule[['Opponent', 'Date']], on='Opponent', how='left')

#made changes to the dataframe so we save it back to the clean table
#replace the old table with this updated one with the features added
df_for_combined_football_stats.to_sql('clean_combined_football_stats', conn, if_exists='replace', index=False)
conn.close()

print("done with combined football stats feature engineering!")


#feature engineering for the combined player stats table

conn = sqlite3.connect('data/database/rutgersfootball.db')

df_for_combined_player_stats = pd.read_sql_query("SELECT * FROM clean_combined_player_stats", conn)


#using pivot_table to allow for future improvements when multiple seasons are added
#when multiple seasons, will have same player and same category across different rows so to create single row will use the average of the rows which pivot_table allows for while pivot would throw error
#need to make this table have each player and a respective category as unique row so we assign index to that
#making values in stat column, as columns to make it wide format
#filling in any missing values with 0 since stat values are column but possible that player has for example interception but no TD (touchdown) so need to fill TD column with 0 
df_pivoted_combined_player_stats_table = df_for_combined_player_stats.pivot_table(index=['Player', 'Category'], columns='Stat', values='Value').reset_index().fillna(0)

#grouping together all the categories together and summing stats; total yards for passing, total yards for rushing, etc using agg function
#did sum of yards and touchdowns since that was common in stat field among all the different players in original table
team_total_sums = df_pivoted_combined_player_stats_table.groupby('Category').agg({'Yards': 'sum','TD': 'sum'}).rename(columns={'Yards': 'Team_Yards', 'TD': 'Team_TD'})

#adding these sums to each player, category row in table; i.e including total rushing yards for a player with rushing category row
#can now compare individual player stats for that category to the overall team's stats for that category
df_pivoted_combined_player_stats_table = df_pivoted_combined_player_stats_table.merge(team_total_sums, on='Category')

#with team stat and player stat for respective categories yards and touchdowns, can calculate their contribution by dividing
#assuming that team_yards is more than 0 since that would mean essentially a game was not played
df_pivoted_combined_player_stats_table['Yardage_Share'] = (df_pivoted_combined_player_stats_table['Yards'] / df_pivoted_combined_player_stats_table['Team_Yards'])

#same thing as above but for touchdown
#measures individual player's contribution towards team touchdowns
df_pivoted_combined_player_stats_table['TD_Share'] = (df_pivoted_combined_player_stats_table['TD'] / df_pivoted_combined_player_stats_table['Team_TD'])


#saving it as a new separate copy since it is an entirely different structure with the pivot
#helps preserve original version while including this newly created one
#note: useful for future analysis on individual's performance and seeing if team is too reliant on a select few players (i.e if these above percentages are high)
df_pivoted_combined_player_stats_table.to_sql('pivoted_combined_player_stats', conn, if_exists='replace', index=False)
conn.close()

print("done with combined player stats feature engineering!")



#feature engineering for the passing, rushing and receiving tables

conn = sqlite3.connect('data/database/rutgersfootball.db')

df_for_passing = pd.read_sql("SELECT * FROM clean_passing", conn)

#edge case with this since it is possible to have passing touchdowns and no interceptions in a game but leads to division by zero issue creating infinity
#in football and sports broadcasts, ratio is simply number of touchdowns if interceptions is 0 so we are using that by replacing interceptions with 1 if 0
#can see how many successful passes (passing touchdowns) compared to failed successes (interceptions)
df_for_passing['TD_INT_Ratio'] = np.where(df_for_passing['Interceptions'] == 0, df_for_passing['TD'], df_for_passing['TD'] / df_for_passing['Interceptions'])

#no edge case for this since if no attempts, no interceptions
#so if attempts is 0 then interceptions must be 0 as well since no attempts were made for ball to get intercepted and so int rate would be 0
#measures percentage of all passes that were failures (interceptions) so essentially quarterback error rate
df_for_passing['INT_Rate'] = np.where(df_for_passing['Att'] == 0, 0, df_for_passing['Interceptions'] / df_for_passing['Att'])

#no edge for this either because if no attempts, then no yards possible
#no attempt to pass the ball so passing yards not possible
#measures percentage of yards they were able to get for every passing attempt
df_for_passing['YPA'] = np.where(df_for_passing['Att'] == 0, 0, df_for_passing['Yards'] / df_for_passing['Att'])

#saving back to the clean SQL table so it has these new feature engineered aspects
df_for_passing.to_sql('clean_passing', conn, if_exists='replace', index=False)

#feature engineering for rushing

df_for_rushing = pd.read_sql("SELECT * FROM clean_rushing", conn)

#if attempt to rush is 0, then rushing touchdown should not be possible (aka also 0) so we just give td_rate a value of 0
#measuring percentage of rushing touchdowns for all rushing attempts (how many successful rush attempts)
df_for_rushing['TD_Rate'] = np.where(df_for_rushing['Attempts'] == 0, 0, df_for_rushing['TD'] / df_for_rushing['Attempts'])

#getting average of rushing yards across all players (mean)
avg_team_yds = df_for_rushing['Net_Yards'].mean()
#subtracting mean from individual values to determine if each player's rushing yards is above or below team average
#can aid with detecting over reliance or bad individual performance bringing team down
df_for_rushing['Above_Avg_Yards'] = (df_for_rushing['Net_Yards'] - avg_team_yds)

#saving back to clean sql table with updated features
df_for_rushing.to_sql('clean_rushing', conn, if_exists='replace', index=False)

#feature engineering for receiving table

df_for_receiving = pd.read_sql("SELECT * FROM clean_receiving", conn)

#capturing the efficiency per catch
#if no receptions, then automatically no reception yards
df_for_receiving['YPR'] = np.where(df_for_receiving['Receptions'] == 0, 0, df_for_receiving['Yards'] / df_for_receiving['Receptions'])

#getting total receiving touchdowns
total_tds = df_for_receiving['TD'].sum()
#if total receiving touchdowns is 0, then no individual can have receiving touchdowns by default and definition of addition
df_for_receiving['TD_Contribution_Pct'] = np.where(total_tds == 0, 0, df_for_receiving['TD'] / total_tds)

#saving it back to the clean sql table
df_for_receiving.to_sql('clean_receiving', conn, if_exists='replace', index=False)

conn.close()
#printing success message for passing, rushing, receiving feature engineering
print("done with passing, rushing, receiving feature engineering!")


#feature engineering for schedule

conn = sqlite3.connect('data/database/rutgersfootball.db')

df_schedule = pd.read_sql("SELECT * FROM clean_schedule", conn)
#converting the date to actual datetime type for calculation
df_schedule['Date'] = pd.to_datetime(df_schedule['Date'])
#calculating number of rest days between games via diff and dt function with first game having automatic rest days of 7 as default (assumption we made)
df_schedule['Days_Rest'] = df_schedule['Date'].diff().dt.days.fillna(7)

#saving back to clean sql table with this updated new feature
df_schedule.to_sql('clean_schedule', conn, if_exists='replace', index=False)



#feature engineering into clean_player_dataset to measure player's versatility
df_player_dataset = pd.read_sql("SELECT * FROM clean_player_dataset", conn)

#measures each player's total yards across all categories of rushing, passing, receiving
df_player_dataset['Total_Utility_Yards'] = df_player_dataset['Rush_Yds'] + df_player_dataset['Rec_Yds'] + df_player_dataset['Pass_Yds']
#measures each player's total touchdowns across all categories of rushing, passing, receiving
df_player_dataset['Total_Utility_TDs'] = df_player_dataset['Rush_TD'] + df_player_dataset['Rec_TD'] + df_player_dataset['Pass_TD']

#choosing to calculate their versatility based on if they are a dual or triple threat
#checking individual categories' yards first to determine how many roles they have (if 0 then not a role)
#using number of roles to determine if dual or triple threat (i.e if versatile)

#assinging number of roles; each part is either 1 or 0 of below so add them up to get range of 0 to 3
df_player_dataset['Versatility_Score'] = ((df_player_dataset['Rush_Yds'] > 0).astype(int) +(df_player_dataset['Rec_Yds'] > 0).astype(int) + (df_player_dataset['Pass_Yds'] > 0).astype(int))

#based on versatility score will determine if dual/triple threat using filtering
df_player_dataset['Is_Dual_Threat'] = (df_player_dataset['Versatility_Score'] >= 2).astype(int)

#saving to clean sql table with updated features above
df_player_dataset.to_sql('clean_player_dataset', conn, if_exists='replace', index=False)

conn.close()
print("feature engineering is complete!")