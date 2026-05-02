from sqlqueries import run_query, QUERIES

# Dictionary to map query keys to helpful, descriptive titles
QUERY_TITLES = {
    "loss_autopsy": "GAME TRENDS: Analyzing Efficiency & Rest in Rutgers Losses",
    "over_reliance": "PLAYER DEPENDENCY: Identifying 'One-Man Show' Risks (>40% Share)",
    "discipline_mistakes": "DISCIPLINE CHECK: Quarterback Errors & Team Penalties in Losses",
    "versatility_impact": "PLAYER VERSATILITY: Impact of 'Dual-Threat' Players vs. Raw Stats",
    "master_analysis_table": "MASTER DATASET: The Combined View for Statistical Correlation"
}

def display_all_results():
    print("\n" + "#"*60)
    print("      RUTGERS FOOTBALL ANALYSIS: INDIVIDUAL QUERY RESULTS")
    print("#"*60)

    for query_name in QUERIES.keys():
        # Get the descriptive title; fall back to the name if title is missing
        title = QUERY_TITLES.get(query_name, query_name.replace('_', ' ').upper())
        
        print("\n" + "="*60)
        print(f"REPORT: {title}")
        print("-" * 60)
        
        try:
            df = run_query(query_name)
            
            if df.empty:
                print("STATUS: No relevant data found for this specific criteria.")
            else:
                # Print the data
                print(df.head(10)) 
                print("-" * 60)
                print(f"SUMMARY: Found {len(df)} relevant data points.")
                
        except Exception as e:
            print(f"ERROR running '{query_name}': {e}")

    print("\n" + "="*60)
    print("END OF ANALYSIS REPORT")
    print("="*60)

if __name__ == "__main__":
    display_all_results()