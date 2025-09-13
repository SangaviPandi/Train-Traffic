import json

def clean_stations(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        stations_raw = json.load(f)

    # ✅ If it's a GeoJSON FeatureCollection, get the features list
    if isinstance(stations_raw, dict) and "features" in stations_raw:
        features = stations_raw["features"]
    elif isinstance(stations_raw, list):
        features = stations_raw
    else:
        raise ValueError("Invalid stations.json format! Expected GeoJSON or list.")

    stations_clean = {}

    for feature in features:
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        code = props.get("code")
        name = props.get("name")

        # Default lat/lon values
        lat = lon = None
        if geometry and geometry.get("coordinates"):
            lon, lat = geometry["coordinates"]  # GeoJSON = [lon, lat]

        if code:
            stations_clean[code] = {
                "lat": lat,
                "lon": lon,
                "name": name or code
            }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stations_clean, f, indent=4)

    print(f"Original station entries: {len(features)}")
    print(f"Stations with coordinates: {sum(1 for s in stations_clean.values() if s['lat'] is not None)}")
    print(f"Stations without coordinates: {sum(1 for s in stations_clean.values() if s['lat'] is None)}")
    print(f"Cleaned stations saved to: {output_path}")


if __name__ == "__main__":
    clean_stations("data/stations_clean.json")
