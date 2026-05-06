from sqlqueries import run_query, QUERIES

#making list of titles for each query so can be easily identified and understood
QUERY_TITLES = {
    "ordered_losses_data": "Stats Most Associated With Losses in Low Efficiency Performances (Low Yards Per Play)",
    "over_reliance": "Checking over-reliance on select few players (via >40% yardage share)",
    "quarterback_players_discipline_alongside_losses": "Quarterback's Season Discipline Alongside Team's Average Loss Stats",
    "ranked_versatility": "Player Contribution, Versatility, and Dual/Triple Threat Identification",
    "prediction_model_ready_table": "Master Dataset: Combined View of all Dependent and Independent Variables necessary for Predictive Modeling"
}

#takes and runs all queries in sqlqueries file with run_query function (one by one goes through each query in list)
#does the respective formatting to clearly print
def display_all_results():
    print("\n" + "#"*60)
    print("      RUTGERS FOOTBALL ANALYSIS: INDIVIDUAL QUERY RESULTS")
    print("#"*60)

    for query_name in QUERIES.keys():
        #getting respective query title from above list based on query name (making assumption and creating such that both are same)
        title = QUERY_TITLES.get(query_name, query_name.replace('_', ' ').upper())
        
        #formatting the title of each query
        print("\n" + "="*60)
        print(f"REPORT: {title}")
        print("-" * 60)
        
        #running the query and printing the results with proper formatting
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

    #marking end of analysis report clearly so easy to differentiate between query results
    print("\n" + "="*60)
    print("END OF ANALYSIS REPORT")
    print("="*60)

if __name__ == "__main__":
    display_all_results()