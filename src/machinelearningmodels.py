import pandas as pd
from sqlqueries import run_query
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler # Added for scaling
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

def run_machine_learning():
    # 1. LOAD DATA
    df = run_query("master_analysis_table")
    
    # 2. FEATURE SELECTION
    features = ['Rutgers_Comp_Pct', 'YPP_Diff', 'Days_Rest', 'Penalty_Efficiency']
    X = df[features]
    y = df['Win_Loss_Binary']

    # 3. SPLIT DATA
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # 4. FEATURE SCALING (Standardization)
    # We "fit" the scaler on the training data and then "transform" both sets
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. INITIALIZE & TRAIN MODEL (Using scaled data)
    model = LogisticRegression()
    model.fit(X_train_scaled, y_train)

    # 6. MAKE PREDICTIONS
    y_pred = model.predict(X_test_scaled)

    # 7. ANALYZE EFFICIENCY
    print("--- Machine Learning Model Results (With Scaling) ---")
    print(f"\nModel Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\nDetailed Performance Report:")
    print(classification_report(y_test, y_pred))

    # 8. FEATURE IMPORTANCE
    # Now that data is scaled, these weights are much more "fair" comparisons
    importance = pd.DataFrame({'Feature': features, 'Weight': model.coef_[0]})
    print("\nFeature Importance (Standardized Weights):")
    print(importance.sort_values(by='Weight', ascending=False))

if __name__ == "__main__":
    run_machine_learning()