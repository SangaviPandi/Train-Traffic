import json

def merge_stations(original_file, filled_file, output_file):
    # Load the original stations
    with open(original_file, "r", encoding="utf-8") as f:
        original_stations = json.load(f)

    # Load the filled stations
    with open(filled_file, "r", encoding="utf-8") as f:
        filled_stations = json.load(f)

    updated_count = 0

    # Merge missing coordinates
    for code, station in original_stations.items():
        if station.get("lat") is None or station.get("lon") is None:
            if code in filled_stations:
                filled = filled_stations[code]
                if filled.get("lat") and filled.get("lon"):
                    station["lat"] = filled["lat"]
                    station["lon"] = filled["lon"]
                    updated_count += 1

    # Save the merged result
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(original_stations, f, indent=4)

    print(f"✅ Merging complete!")
    print(f"🔹 Updated {updated_count} stations with missing coordinates.")
    print(f"📌 Final file saved to: {output_file}")


if __name__ == "__main__":
    merge_stations(
        "data/stations_clean.json",      # Original stations file
        "data/stations_filled.json",      # Filled stations file
        "data/stations_final.json"       # Output merged file
    )
