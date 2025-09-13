# generate_training_data.py
import pandas as pd
import numpy as np
from datetime import timedelta
import os

# Config
TIMELINE_CSV = "data/timeline.csv"
OUT_CSV = "data/synthetic_training_pairs.csv"
TIME_WINDOW_MIN = 10  # consider trains arriving within +/- this many minutes

# priority mapping (customize if your train_type values differ)
PRIORITY_MAP = {
    "Express": 1,
    "Mail": 2,
    "Passenger": 3,
    "Freight": 4,
    None: 3
}

def to_minutes_of_day(ts):
    if pd.isna(ts):
        return None
    return ts.hour * 60 + ts.minute

def priority_from_type(t):
    return PRIORITY_MAP.get(t, PRIORITY_MAP.get(None))

def load_timeline(path):
    df = pd.read_csv(path, low_memory=False)
    # Ensure columns exist and types
    df['train_number'] = df['train_number'].astype(str)
    # Parse times
    for col in ['scheduled_arrival', 'scheduled_departure']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def build_prev_next(df):
    # Build prev/next station_code per train to compute "segment"
    df = df.sort_values(['train_number', 'stop_index'])
    df['prev_station_code'] = df.groupby('train_number')['station_code'].shift(1)
    df['next_station_code'] = df.groupby('train_number')['station_code'].shift(-1)
    return df

def make_pairs(df):
    rows = []
    # group by station_code: potential conflicts at the same station
    for station, g in df.groupby('station_code'):
        g = g.dropna(subset=['scheduled_arrival']).sort_values('scheduled_arrival')
        if len(g) < 2:
            continue
        # convert to minutes
        g = g.copy()
        g['arr_min'] = g['scheduled_arrival'].apply(to_minutes_of_day)
        # sliding window: for each train, compare with trains that arrive within TIME_WINDOW_MIN
        for i, row_i in g.iterrows():
            for j, row_j in g.iterrows():
                if i == j:
                    continue
                if row_i['arr_min'] is None or row_j['arr_min'] is None:
                    continue
                if abs(row_i['arr_min'] - row_j['arr_min']) <= TIME_WINDOW_MIN:
                    # build feature pair (A = row_i, B = row_j)
                    prio_a = priority_from_type(row_i.get('train_type'))
                    prio_b = priority_from_type(row_j.get('train_type'))
                    speed_a = float(row_i.get('max_speed_kmph') or 0.0)
                    speed_b = float(row_j.get('max_speed_kmph') or 0.0)
                    dist_a = float(row_i.get('segment_distance_km') or 0.0)
                    dist_b = float(row_j.get('segment_distance_km') or 0.0)
                    time_a = row_i['arr_min']
                    time_b = row_j['arr_min']
                    trains_at_station = len(g)
                    station_capacity = max(1, min(6, int(trains_at_station/50)+1))  # cheap proxy

                    # label: deterministic rule-based oracle
                    # lower priority value wins (1 highest). If equal, higher speed wins. If equal, earlier arrival wins.
                    if prio_a < prio_b:
                        label = 1
                    elif prio_a > prio_b:
                        label = 0
                    else:
                        # same priority
                        if speed_a > speed_b + 1e-6:
                            label = 1
                        elif speed_a < speed_b - 1e-6:
                            label = 0
                        else:
                            # earlier arrival wins
                            label = 1 if time_a <= time_b else 0

                    rows.append({
                        "station_code": station,
                        "train_a": row_i['train_number'],
                        "train_b": row_j['train_number'],
                        "priority_a": prio_a,
                        "priority_b": prio_b,
                        "speed_a": speed_a,
                        "speed_b": speed_b,
                        "time_a_min": time_a,
                        "time_b_min": time_b,
                        "dist_a_km": dist_a,
                        "dist_b_km": dist_b,
                        "station_capacity": station_capacity,
                        # diff features are handy
                        "priority_diff": prio_a - prio_b,
                        "speed_diff": speed_a - speed_b,
                        "time_diff": time_a - time_b,
                        "dist_diff": dist_a - dist_b,
                        "label": label
                    })
    return pd.DataFrame(rows)

def main():
    print("Loading timeline...")
    df = load_timeline(TIMELINE_CSV)
    df = build_prev_next(df)
    print("Building pairwise samples (this may take some time)...")
    pairs = make_pairs(df)
    if pairs.empty:
        print("No pairs generated. Check timeline.csv and scheduled_arrival values.")
        return
    # Shuffle and save
    pairs = pairs.sample(frac=1.0, random_state=42).reset_index(drop=True)
    os.makedirs(os.path.dirname(OUT_CSV) or ".", exist_ok=True)
    pairs.to_csv(OUT_CSV, index=False)
    print(f"Saved {len(pairs)} synthetic pairwise samples to {OUT_CSV}")

if __name__ == "__main__":
    main()
