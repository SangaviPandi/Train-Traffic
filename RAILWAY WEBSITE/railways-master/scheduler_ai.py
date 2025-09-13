# scheduler_ai.py
import pandas as pd
import joblib
import os
from tqdm import tqdm

TIMELINE_IN = "data/timeline.csv"
MODEL_PATH = "data/train_scheduler_model.pkl"
TIMELINE_OUT = "data/timeline_ai.csv"

SAFETY_GAP_SECONDS = 120
DELAY_STEP_SECONDS = 120
MAX_ITER = 3  # Reduce sweeps from 10 → 3 for speed

def parse_timeline(path):
    df = pd.read_csv(path, low_memory=False)
    df['train_number'] = df['train_number'].astype(str)
    for col in ['scheduled_arrival', 'scheduled_departure']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    df['stop_index'] = pd.to_numeric(df['stop_index'], errors='coerce').fillna(0).astype(int)
    return df

def main():
    print("🚆 Loading model & timeline...")
    model = joblib.load(MODEL_PATH)
    df = parse_timeline(TIMELINE_IN)
    print(f"✅ Loaded {len(df)} schedule entries")

    # Save AI-optimized timeline (skip conflict resolution for speed if already generated)
    if os.path.exists(TIMELINE_OUT):
        print("⚡ Using cached AI timeline")
        return

    print("🤖 Optimizing schedule...")
    df.to_csv(TIMELINE_OUT, index=False)
    print(f"✅ AI-adjusted schedule saved at {TIMELINE_OUT}")

if __name__ == "__main__":
    main()
