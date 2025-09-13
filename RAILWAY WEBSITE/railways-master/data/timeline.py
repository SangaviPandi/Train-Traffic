import pandas as pd
import json
import os

# Load timeline data
timeline_df = pd.read_csv("data/timeline.csv", low_memory=False)  # Fixes DtypeWarning

# Load station data (with district info)
with open("data/stations_final.json", "r", encoding="utf-8") as f:
    stations_data = json.load(f)

# Convert station data to DataFrame
stations_df = pd.DataFrame([
    {
        "station_code": code,
        "station_name": info.get("name", ""),
        "lat": info.get("lat"),
        "lon": info.get("lon"),
        "district": info.get("district", "Unknown")
    }
    for code, info in stations_data.items()
])

# Merge district info into timeline
merged_df = timeline_df.merge(stations_df, on="station_code", how="left")

# Save merged file
merged_df.to_csv("data/timeline_with_districts.csv", index=False)
print("✅ Merged timeline saved to data/timeline_with_districts.csv")

# Ensure output folder exists
output_folder = "data/districts"
os.makedirs(output_folder, exist_ok=True)

# Group by district
district_groups = merged_df.groupby("district")

# Save separate CSVs for each district
for district, group in district_groups:
    safe_name = district.replace(" ", "_").replace("/", "_")
    group.to_csv(f"{output_folder}/{safe_name}.csv", index=False)

print("✅ District-wise CSVs saved in:", output_folder)
