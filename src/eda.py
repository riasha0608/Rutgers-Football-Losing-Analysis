from sqlqueries import run_query
import pandas as pd

def run_eda():
    print("--- Starting Exploratory Data Analysis ---")
    
    # 1. Pull the Master Analysis Table
    # This is the table that joins schedule and team efficiency
    df = run_query("master_analysis_table")
    
    if df.empty:
        print("Master table is empty. Check your SQL join logic.")
        return

    # 2. Basic Descriptive Statistics
    # This tells you the 'average' game for Rutgers
    print("\n[1] Summary Statistics for All Games:")
    print(df.describe().round(2))

    # 3. Win vs. Loss Comparison
    # This is huge. It shows you the average stats when they WIN vs when they LOSE.
    print("\n[2] Comparison: Average Stats in Wins vs. Losses:")
    # We group by the binary column we made (1 = Win, 0 = Loss)
    comparison = df.groupby('Win_Loss_Binary').mean(numeric_only=True).round(3)
    print(comparison)

    # 4. The Correlation Matrix
    # This mathematically ranks which factors move the needle toward a Win (1)
    print("\n[3] Correlation with Winning (Win_Loss_Binary):")
    # We only care about how other columns relate to 'Win_Loss_Binary'
    corr_matrix = df.corr(numeric_only=True)
    winning_correlations = corr_matrix['Win_Loss_Binary'].sort_values(ascending=False)
    print(winning_correlations)

    # 5. Identifying the "Red Flags" (Strongest predictors of a Loss)
    print("\n[4] Top 3 Key Performance Indicators (KPIs):")
    # We look for the strongest positive or negative correlations (excluding itself)
    kpis = winning_correlations[winning_correlations.index != 'Win_Loss_Binary']
    print(f"1. Most tied to Winning: {kpis.index[0]} ({kpis.iloc[0]:.2f})")
    print(f"2. Most tied to Losing: {kpis.index[-1]} ({kpis.iloc[-1]:.2f})")

if __name__ == "__main__":
    run_eda()