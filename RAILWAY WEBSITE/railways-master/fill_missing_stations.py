import json
import pandas as pd
import requests
import time

# OpenStreetMap API endpoint
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def fetch_coordinates(station_name):
    """Fetch latitude and longitude using OpenStreetMap Nominatim API"""
    try:
        query = f"{station_name} railway station India"
        params = {"q": query, "format": "json", "limit": 1}
        headers = {"User-Agent": "railways-simulator"}

        response = requests.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except Exception as e:
        print(f"⚠ Error fetching {station_name}: {e}")
        return None, None

def fill_missing_coords(stations_json, missing_csv, output_json):
    # Load existing stations JSON
    with open(stations_json, "r", encoding="utf-8") as f:
        stations_data = json.load(f)

    # Load CSV of missing stations
    missing_df = pd.read_csv(missing_csv)

    for i, row in missing_df.iterrows():
        code = str(row["station_code"]).strip()
        name = str(row["station_name"]).strip()

        # Skip dummy stations like XX-BECE, YY-BPLC, etc.
        if code.startswith("XX-") or code.startswith("YY-"):
            print(f"⏩ Skipping dummy station: {name} ({code})")
            continue

        # Only fetch if lat/lon is missing or null
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            print(f"🔎 Fetching coordinates for: {name} ({code}) ...")
            lat, lon = fetch_coordinates(name)

            if lat and lon:
                if code in stations_data:
                    stations_data[code]["lat"] = lat
                    stations_data[code]["lon"] = lon
                    print(f"✅ Updated {code} → ({lat}, {lon})")
                else:
                    # If station not found, add it
                    stations_data[code] = {
                        "lat": lat,
                        "lon": lon,
                        "name": name
                    }
                    print(f"➕ Added missing station {code} → ({lat}, {lon})")
            else:
                print(f"❌ Could not find coordinates for {name}")

            # Sleep to respect API limits
            time.sleep(1)

    # Save updated stations JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(stations_data, f, indent=2, ensure_ascii=False)

    print(f"\n🎯 Updated stations saved to: {output_json}")

# Run the function
fill_missing_coords(
    stations_json="data/stations_clean.json",
    missing_csv="data/missing_stations.csv",
    output_json="data/stations_filled.json"
)
