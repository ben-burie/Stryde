import pandas as pd

def clean_strava_csv(input_csv_path: str) -> None:
    df = pd.read_csv(input_csv_path)
    df.columns = df.columns.str.strip()

    # Column mapping
    column_map = {
        "Distance": "distance",
        "Moving Time": "moving_time",
        "Elapsed Time": "elapsed_time",
        "Average Speed": "average_speed",
        "Average Heart Rate": "average_heartrate",
        "Max Heart Rate": "max_heartrate",
        "Elevation Gain": "total_elevation_gain",
        "Activity Type": "type",
        "Activity Date": "start_date",
    }

    available_columns = {
        k: v for k, v in column_map.items() if k in df.columns
    }

    df = df[list(available_columns.keys())].rename(columns=available_columns)
    df = df[df["type"].str.lower() == "run"]
    df = df.dropna(subset=["average_heartrate", "max_heartrate"])

    df["start_date"] = pd.to_datetime(
        df["start_date"],
        format="%b %d, %Y, %I:%M:%S %p",
        errors="coerce"
    )

    df = df.dropna(subset=["distance", "moving_time"])
    df = df.reset_index(drop=True)

    df["distance"] = df["distance"].astype(float)
    df["distance_km"] = df["distance"].copy()
    df["distance_miles"] = df["distance_km"] * 0.621371

    df.to_csv("vdot_ml_model/clean_activities.csv", index=False)
    #print(f"✅ Cleaned Strava CSV saved to: {output_csv_path}")
    # Change to write to database instead of csv
    print("Input cleaned.")
    return df