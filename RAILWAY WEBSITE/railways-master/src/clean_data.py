import json
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_stations():
    with open(os.path.join(DATA_DIR, "stations.json")) as f:
        data = json.load(f)
    # Extract properties from GeoJSON
    stations = [feature["properties"] for feature in data["features"]]
    return pd.DataFrame(stations)

def load_trains():
    with open(os.path.join(DATA_DIR, "trains.json")) as f:
        data = json.load(f)
    trains = [feature["properties"] for feature in data["features"]]
    return pd.DataFrame(trains)

def load_schedules():
    with open(os.path.join(DATA_DIR, "schedules.json")) as f:
        data = json.load(f)
    return pd.DataFrame(data)

def clean_schedules(df):
    df = df.dropna(thresh=5)  # drop rows with many missing
    df['arrival'] = pd.to_datetime(df['arrival'], format='%H:%M:%S', errors='coerce').dt.time
    df['departure'] = pd.to_datetime(df['departure'], format='%H:%M:%S', errors='coerce').dt.time
    df['day'] = pd.to_numeric(df['day'], errors='coerce').fillna(1).astype(int)
    return df

def clean_trains(df):
    df['departure'] = pd.to_datetime(df['departure'], format='%H:%M:%S', errors='coerce').dt.time
    df['arrival'] = pd.to_datetime(df['arrival'], format='%H:%M:%S', errors='coerce').dt.time
    df['duration_h'] = pd.to_numeric(df['duration_h'], errors='coerce')
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce')
    return df
