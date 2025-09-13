import pandas as pd
from tabulate import tabulate  # For beautiful table formatting

# Path to optimized AI schedule
TIMELINE_AI = r"data\timeline_ai.csv"

def load_schedule():
    print("📂 Loading AI-optimized schedule...")
    df = pd.read_csv(TIMELINE_AI, low_memory=False)
    print(f"✅ Loaded {len(df)} records from AI schedule")
    return df

def format_time(dt):
    """Convert datetime to HH:MM format"""
    try:
        return pd.to_datetime(dt).strftime("%H:%M")
    except:
        return "NA"

def search_by_train(df, train_number):
    return df[df['train_number'].astype(str) == str(train_number)]

def search_by_station(df, station_code):
    return df[df['station_code'].str.upper() == station_code.upper()]

def search_by_junction(df, junction):
    return df[df['station_name'].str.contains(junction, case=False, na=False)]

def display_results(result):
    if result.empty:
        print("\n⚠️ No matching schedule found!")
        return

    # Format times to HH:MM only
    result['scheduled_arrival'] = result['scheduled_arrival'].apply(format_time)
    result['scheduled_departure'] = result['scheduled_departure'].apply(format_time)

    # Select relevant columns
    columns_to_show = ['train_number', 'station_code', 'station_name', 'scheduled_arrival', 'scheduled_departure']
    if 'train_name' in result.columns:
        columns_to_show.insert(1, 'train_name')

    # Limit results to top 15 for readability
    limited_result = result[columns_to_show].head(15)

    # Pretty display using tabulate
    print("\n📌 Schedule Results:")
    print(tabulate(limited_result, headers="keys", tablefmt="fancy_grid", showindex=False))

def main():
    df = load_schedule()
    print("\n🚉 AI Train Scheduler — Query Mode")
    print("1️⃣ Search by Train Number")
    print("2️⃣ Search by Station Code")
    print("3️⃣ Search by Junction / Station Name")
    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1":
        train_no = input("Enter Train Number: ").strip()
        result = search_by_train(df, train_no)
    elif choice == "2":
        station = input("Enter Station Code: ").strip()
        result = search_by_station(df, station)
    elif choice == "3":
        junction = input("Enter Junction / Station Name: ").strip()
        result = search_by_junction(df, junction)
    else:
        print("❌ Invalid choice!")
        return

    display_results(result)

if __name__ == "__main__":
    main()
