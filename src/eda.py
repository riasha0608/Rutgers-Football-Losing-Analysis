from sqlqueries import run_query
import pandas as pd

def run_eda():
    print("--- Starting Exploratory Data Analysis ---")
    
    #getting query results from master table and storing it in dataframe
    df_master_results = run_query("prediction_model_ready_table")
    
    #error checking step if no results returned from above query
    if df_master_results.empty:
        print("Master table is empty. Check your SQL join logic.")
        return

    #getting summary stats of table (aka across all games)
    print("\n(1) Summary Statistics for All Games:")
    #rounding for simple and easy view of the summary stats
    print(df_master_results.describe().round(2))

    #average stats of columns (features) in table for wins versus losses (grouping them by wins vs losses) to see the difference
    #can help depict differences in features for wins vs losses and thus possible factors of losses
    print("\n(2) Comparing the Average Statistics in Wins vs. Losses:")
    #only calculating mean for numeric data cause not possible for categorical stuff
    win_loss_comparison = df_master_results.groupby('Win_Loss_Binary').mean(numeric_only=True).round(3)
    print(win_loss_comparison)

    #creating correlation matrix to see each feature's correlation to the y variable (win vs loss)
    print("\n(3) Each x variable's (feature's) correlation with win vs loss:")
    #making the actual correlation matrix and only getting win loss column since we only want features correlation with this variable
    matrix_of_all_correlation_coefficients = df_master_results.corr(numeric_only=True)
    correlation_to_winning = matrix_of_all_correlation_coefficients['Win_Loss_Binary'].sort_values(ascending=False)
    #correlations stored from most correlated to least
    print(correlation_to_winning)


    print("\n(4) Top 3 Key Performance Indicators (KPIs):")
    #looking at both strongly positive and strongly negative correlation to get most related to winning and most related to losing
    #will help see what team is doing well to get wins and what team needs to work on when they face losses
    kpis = correlation_to_winning[correlation_to_winning.index != 'Win_Loss_Binary']
    #gives the factors and their correlations based on correlation matrix list for win loss column
    #used iloc to get data by index location since location in list is what matters (i.e at top - most related to winnings)
    print(f"1. Most tied to Winning: {kpis.index[0]} ({kpis.iloc[0]:.2f})")
    print(f"2. Most tied to Losing: {kpis.index[-1]} ({kpis.iloc[-1]:.2f})")

if __name__ == "__main__":
    run_eda()