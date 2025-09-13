"""
schedule_simulator.py

Simulates train movements across stations using schedules_clean.json, trains.json, stations.json.

Inputs:
- schedules_clean.json: dict keyed by train_number with list of stops:
    {
      "47154": [
          {"station_code": "FM", "arrival": "07:55:00", "departure": "07:57:00"},
          {"station_code": "HYB", "arrival": "08:20:00", "departure": "08:22:00"}
      ],
      ...
    }
- trains.json: dict keyed by train_number with metadata
- stations.json: dict keyed by station_code with {"lat": float, "lon": float, "name": str}

Outputs:
- timeline.csv or timeline.json containing:
    train_number, stop_index, station_code, station_name, lat, lon,
    scheduled_arrival, scheduled_departure, dwell_seconds, segment_distance_km,
    segment_travel_seconds, theoretical_speed_kmph, status
"""

from __future__ import annotations
import json
import argparse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import math
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ---------------------- Utility Functions ----------------------

def load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance between two points in kilometers."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse various datetime formats into datetime objects."""
    if ts is None or ts in ("None", ""):
        return None
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        for fmt in ("%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y %H:%M:%S"):
            try:
                return datetime.strptime(ts, fmt)
            except Exception:
                continue
    logging.warning(f"Could not parse timestamp: {ts}")
    return None


# ---------------------- Core Simulation ----------------------

def simulate_schedule(schedule: Dict[str, List[Dict]], trains: Dict[str, Dict], stations: Dict[str, Dict],
                      default_speed_kmph: float = 60.0) -> pd.DataFrame:
    """
    Main entrypoint: simulate all trains and return concatenated timeline dataframe.
    """
    timelines = []

    # ✅ FIX: Iterate over train_number + stops since schedule is now a dict
    for train_number, stops in schedule.items():
        try:
            df = _simulate_single_train(train_number, stops, trains.get(str(train_number), {}),
                                       stations, default_speed_kmph)
            if df is not None and not df.empty:
                timelines.append(df)
        except Exception as e:
            logging.exception(f"Error simulating train {train_number}: {e}")

    if timelines:
        valid_timelines = [t for t in timelines if t is not None and not t.empty]
        if valid_timelines:
            full = pd.concat(valid_timelines, ignore_index=True)
        else:
            full = pd.DataFrame()

        full.sort_values(["train_number", "stop_index"], inplace=True)
        full.reset_index(drop=True, inplace=True)
    else:
        full = pd.DataFrame()

    return full


def _simulate_single_train(train_number: str, stops: List[Dict], train_meta: Dict,
                           stations: Dict[str, Dict], default_speed_kmph: float) -> pd.DataFrame:
    """Simulate a single train's stops and compute derived fields."""

    # ✅ Skip trains with no stops
    if not stops or len(stops) == 0:
        logging.warning(f"Skipping train {train_number} — no stops found")
        return pd.DataFrame()

    # Sort stops properly based on day + arrival/departure time
    stops = sorted(stops, key=lambda x: (x.get("day", 1), x.get("arrival") or x.get("departure") or "00:00:00"))

    # Normalize stops
    normalized = []
    for i, s in enumerate(stops):
        code = s.get("station_code") or s.get("station")
        arr = parse_iso(s.get("arrival"))
        dep = parse_iso(s.get("departure"))
        day_offset = int(s.get("day", 1) or 1)
        normalized.append({
            "stop_index": i,
            "station_code": code,
            "arrival": arr,
            "departure": dep,
            "day_offset": day_offset
        })

    # Fill station metadata
    for s in normalized:
        meta = stations.get(s["station_code"], {})
        s["lat"] = meta.get("lat")
        s["lon"] = meta.get("lon")
        s["station_name"] = meta.get("name") or meta.get("station_name") or s["station_code"]

    # Fix missing times
    for s in normalized:
        if s["arrival"] is None and s["departure"] is not None:
            s["arrival"] = s["departure"]
        if s["departure"] is None and s["arrival"] is not None:
            s["departure"] = s["arrival"]

    # Build DataFrame rows
    rows = []
    prev = None
    for s in normalized:
        row = {
            "train_number": train_number,
            "stop_index": s["stop_index"],
            "station_code": s["station_code"],
            "station_name": s["station_name"],
            "lat": s.get("lat"),
            "lon": s.get("lon"),
            "scheduled_arrival": s.get("arrival"),
            "scheduled_departure": s.get("departure"),
            "day_offset": s.get("day_offset", 0),
        }
        # Distance from previous station
        if prev is None or s.get("lat") is None or prev.get("lat") is None:
            row["segment_distance_km"] = None
        else:
            row["segment_distance_km"] = haversine_km(prev.get("lat"), prev.get("lon"),
                                                     s.get("lat"), s.get("lon"))
        rows.append(row)
        prev = s

    df = pd.DataFrame(rows)

    # Default speed
    max_speed = float(train_meta.get("max_speed_kmph") or train_meta.get("max_speed") or default_speed_kmph)

    # Forward pass: infer missing times
    for idx in range(len(df)):
        if pd.isna(df.at[idx, "scheduled_arrival"]) and pd.isna(df.at[idx, "scheduled_departure"]):
            if idx > 0 and not pd.isna(df.at[idx-1, "scheduled_departure"]) and df.at[idx, "segment_distance_km"] is not None:
                travel_hours = df.at[idx, "segment_distance_km"] / max_speed
                travel_seconds = int(travel_hours * 3600)
                inferred_arrival = df.at[idx-1, "scheduled_departure"] + timedelta(seconds=travel_seconds)
                df.at[idx, "scheduled_arrival"] = inferred_arrival
                df.at[idx, "scheduled_departure"] = inferred_arrival + timedelta(minutes=2)
        else:
            if not pd.isna(df.at[idx, "scheduled_arrival"]) and pd.isna(df.at[idx, "scheduled_departure"]):
                df.at[idx, "scheduled_departure"] = df.at[idx, "scheduled_arrival"] + timedelta(minutes=2)
            if pd.isna(df.at[idx, "scheduled_arrival"]) and not pd.isna(df.at[idx, "scheduled_departure"]):
                df.at[idx, "scheduled_arrival"] = df.at[idx, "scheduled_departure"] - timedelta(minutes=2)

    # Backward pass: infer earlier missing times
    for idx in range(len(df)-1, -1, -1):
        if pd.isna(df.at[idx, "scheduled_arrival"]) and idx < len(df)-1 and not pd.isna(df.at[idx+1, "scheduled_arrival"]) and df.at[idx+1, "segment_distance_km"] is not None:
            travel_hours = df.at[idx+1, "segment_distance_km"] / max_speed
            travel_seconds = int(travel_hours * 3600)
            inferred_departure = df.at[idx+1, "scheduled_arrival"] - timedelta(seconds=travel_seconds)
            df.at[idx, "scheduled_departure"] = inferred_departure
            df.at[idx, "scheduled_arrival"] = inferred_departure - timedelta(minutes=2)

    # Compute derived fields
    dwell_secs = []
    travel_secs = [None] * len(df)
    theo_speed = [None] * len(df)

    for idx in range(len(df)):
        arr = df.at[idx, "scheduled_arrival"]
        dep = df.at[idx, "scheduled_departure"]
        dwell = int((dep - arr).total_seconds()) if pd.notna(arr) and pd.notna(dep) else None
        dwell_secs.append(dwell)
        if idx > 0 and df.at[idx, "segment_distance_km"] is not None and not pd.isna(df.at[idx-1, "scheduled_departure"]) and not pd.isna(arr):
            seg_seconds = int((arr - df.at[idx-1, "scheduled_departure"]).total_seconds())
            travel_secs[idx] = seg_seconds
            if seg_seconds > 0:
                hours = seg_seconds / 3600.0
                theo_speed[idx] = df.at[idx, "segment_distance_km"] / hours
        else:
            travel_secs[idx] = None
            theo_speed[idx] = None

    df["dwell_seconds"] = dwell_secs
    df["segment_travel_seconds"] = travel_secs
    df["theoretical_speed_kmph"] = theo_speed
    df["status"] = "SCHEDULED"
    df["train_type"] = train_meta.get("type")
    df["max_speed_kmph"] = max_speed

    return df


# ---------------------- Save Timeline ----------------------

def save_timeline(df: pd.DataFrame, path: str) -> None:
    if path.lower().endswith(".csv"):
        df.to_csv(path, index=False)
    else:
        df.to_json(path, orient="records", date_format="iso", force_ascii=False)
    logging.info(f"Saved timeline to {path}")


# ---------------------- CLI ----------------------

def main():
    parser = argparse.ArgumentParser(description="Simulate train schedules into a timeline DataFrame")
    parser.add_argument("--schedule", required=True, help="Path to schedules_clean.json")
    parser.add_argument("--trains", required=True, help="Path to trains.json")
    parser.add_argument("--stations", required=True, help="Path to stations.json")
    parser.add_argument("--out", required=False, default="timeline.csv", help="Output file path (csv or json)")
    parser.add_argument("--default-speed", required=False, type=float, default=60.0, help="Fallback speed km/h")
    args = parser.parse_args()

    schedule = load_json_file(args.schedule)
    trains = load_json_file(args.trains)
    stations = load_json_file(args.stations)

    df = simulate_schedule(schedule, trains, stations, default_speed_kmph=args.default_speed)
    save_timeline(df, args.out)

    if not df.empty:
        logging.info(f"Simulated {df['train_number'].nunique()} trains and {len(df)} stops")
        print(df.head(20).to_string(index=False))
    else:
        logging.warning("No valid train timeline produced.")


if __name__ == "__main__":
    main()
