# train_scheduler.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
import os

IN_CSV = "data/synthetic_training_pairs.csv"
MODEL_OUT = "data/train_scheduler_model.pkl"

def main():
    df = pd.read_csv(IN_CSV)
    # Features: diffs (priority_diff, speed_diff, time_diff, dist_diff), plus station_capacity
    features = ['priority_diff', 'speed_diff', 'time_diff', 'dist_diff', 'station_capacity']
    X = df[features].fillna(0.0)
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    print("Training RandomForest...")
    clf.fit(X_train, y_train)
    print("Evaluating on test set...")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    os.makedirs(os.path.dirname(MODEL_OUT) or ".", exist_ok=True)
    joblib.dump(clf, MODEL_OUT)
    print(f"Saved model to {MODEL_OUT}")

if __name__ == "__main__":
    main()
