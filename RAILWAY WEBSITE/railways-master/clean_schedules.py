import json
from collections import defaultdict

# Load the schedules.json file
with open("data/schedules.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Original station records: {len(data)}")

# Dictionary to group trains
grouped_trains = defaultdict(list)

# Group stops by train_number
for record in data:
    train_number = str(record.get("train_number")).strip()
    if train_number and record.get("departure") not in [None, "", "None"]:
        grouped_trains[train_number].append({
            "station_name": record.get("station_name"),
            "station_code": record.get("station_code"),
            "arrival": record.get("arrival"),
            "departure": record.get("departure"),
            "day": record.get("day")
        })

# Remove trains with zero stops
cleaned_schedules = {
    train_number: stops
    for train_number, stops in grouped_trains.items()
    if len(stops) > 0
}

print(f"Unique trains after grouping: {len(grouped_trains)}")
print(f"Trains kept after cleaning: {len(cleaned_schedules)}")
print(f"Trains removed: {len(grouped_trains) - len(cleaned_schedules)}")

# Save the cleaned schedules
with open("data/schedules_clean.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_schedules, f, indent=2)

print("Cleaned schedules saved to: data/schedules_clean.json")
