import json
import pandas as pd

def find_missing_stations(stations_path: str, output_csv: str):
    with open(stations_path, "r", encoding="utf-8") as f:
        stations = json.load(f)

    missing = []
    for code, info in stations.items():
        lat = info.get("lat")
        lon = info.get("lon")
        if lat is None or lon is None:
            missing.append({
                "station_code": code,
                "station_name": info.get("name", "Unknown"),
                "lat": lat,
                "lon": lon
            })

    if missing:
        df = pd.DataFrame(missing)
        df.to_csv(output_csv, index=False)
        print(f"⚠ Missing stations saved to: {output_csv} ({len(missing)} stations)")
    else:
        print("✅ All stations have coordinates!")

# Run it
find_missing_stations("data/stations_clean.json", "data/missing_stations.csv")
