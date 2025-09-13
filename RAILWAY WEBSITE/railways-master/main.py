from src.clean_data import load_stations, load_trains, load_schedules, clean_schedules, clean_trains

def main():
    stations_df = load_stations()
    trains_df = clean_trains(load_trains())
    schedules_df = clean_schedules(load_schedules())

    print(f"✅ Loaded {len(stations_df)} stations, {len(trains_df)} trains, {len(schedules_df)} schedule entries.")
    
    # Example: Trains with most stops
    stop_counts = schedules_df['train_number'].value_counts().head(10)
    print("\n📊 Top trains by number of stops:")
    print(stop_counts)

    # Join data if needed
    merged = schedules_df.merge(trains_df, left_on='train_number', right_on='number', how='left', suffixes=('_schedule', '_train'))
    print("\n🚆 Sample merged data:")
    print(merged[['train_number', 'train_name', 'station_name', 'departure_schedule']].head())
    print("📋 Merged columns:", merged.columns.tolist())


if __name__ == "__main__":
    main()
