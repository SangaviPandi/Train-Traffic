# backend_schedule.py
import pandas as pd
from fastapi import APIRouter, Query

router = APIRouter()

TIMELINE_AI = r"railways-master/data/timeline_ai.csv"

def load_schedule():
    df = pd.read_csv(TIMELINE_AI, low_memory=False)
    return df

def format_time(dt):
    try:
        return pd.to_datetime(dt).strftime("%H:%M")
    except:
        return "NA"

df_schedule = load_schedule()

def format_results(df):
    if df.empty:
        return []
    # Format times
    df['scheduled_arrival'] = df['scheduled_arrival'].apply(format_time)
    df['scheduled_departure'] = df['scheduled_departure'].apply(format_time)
    columns_to_show = ['train_number', 'station_code', 'station_name', 'scheduled_arrival', 'scheduled_departure']
    if 'train_name' in df.columns:
        columns_to_show.insert(1, 'train_name')
    limited = df[columns_to_show].head(15)
    return limited.to_dict(orient='records')

@router.get("/api/schedule/train")
def get_schedule_by_train(train_number: str = Query(..., min_length=1)):
    result = df_schedule[df_schedule['train_number'].astype(str) == train_number]
    return format_results(result)

@router.get("/api/schedule/station")
def get_schedule_by_station(station_code: str = Query(..., min_length=1)):
    result = df_schedule[df_schedule['station_code'].str.upper() == station_code.upper()]
    return format_results(result)

@router.get("/api/schedule/junction")
def get_schedule_by_junction(junction: str = Query(..., min_length=1)):
    result = df_schedule[df_schedule['station_name'].str.contains(junction, case=False, na=False)]
    return format_results(result)