import pandas as pd
from sqlqueries import run_query
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler # Added for scaling
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

def run_machine_learning():
    #loading in the data from the master table's query results that we will use for predictive modeling
    df_initial_query_results = run_query("prediction_model_ready_table")
    
    #selecting the features based on the correlation matrix from eda
    #chose the 2 most related to winning and 2 most related to losses
    features_selecting_based_on_corr_matrix = ['Rutgers_Comp_Pct', 'YPP_Diff', 'Days_Rest', 'Penalty_Efficiency']
    #storing the respective features and their data into X and the data for win loss into y
    X = df_initial_query_results[features_selecting_based_on_corr_matrix]
    y = df_initial_query_results['Win_Loss_Binary']

    #splitting the train test sets
    #took notation from lab 3
    #split into 70 training and 30 test since data set is too small to do traditional 80-20 split
    #included random_state 42 to ensure same set produced for every run to ensure reproducibility
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    #using StandardScaler to zscore normalize the X data for train and test so all features are treated fairly
    #did this since the scale of the data for each of these features varies a lot for example penalty efficiency vs days_rest is a large gap in scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    #want to use binary logistic regression (to predict win vs loss) so using that here to create the model and fit it to our data
    model = LogisticRegression()
    model.fit(X_train_scaled, y_train)

    #making predictions based on the X test values
    y_pred = model.predict(X_test_scaled)

    #seeing our accurate model was by checking the actual win/loss results vs the predicted ones from the model and finding percentage accuracy
    print("--- Machine Learning Model Results (With Scaling) ---")
    print(f"\nModel Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")

    #making confusion matrix and getting classification report
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\nDetailed Performance Report:")
    print(classification_report(y_test, y_pred))

    #feature importance; seeing how important each feature was toward prediction
    #table style display to easily read and analyze
    feature_scaled_importance = pd.DataFrame({'Feature': features_selecting_based_on_corr_matrix, 'Weight': model.coef_[0]})
    print("\nFeature Importance (Standardized Weights):")
    print(feature_scaled_importance.sort_values(by='Weight', ascending=False))

if __name__ == "__main__":
    run_machine_learning()