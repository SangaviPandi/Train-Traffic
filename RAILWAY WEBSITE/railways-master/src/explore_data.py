from clean_data import load_stations, load_trains, load_schedules, clean_schedules, clean_trains

def print_summary():
    stations = load_stations()
    trains = clean_trains(load_trains())
    schedules = clean_schedules(load_schedules())

    print("🔸 Stations")
    print(stations.info())
    print(stations.head())

    print("\n🔸 Trains")
    print(trains.info())
    print(trains[['number', 'name', 'type', 'from_station_code', 'to_station_code']].head())

    print("\n🔸 Schedules")
    print(schedules.info())
    print(schedules.head())

    # Count missing values
    print("\nMissing values in schedules:\n", schedules.isnull().sum())

if __name__ == "__main__":
    print_summary()
