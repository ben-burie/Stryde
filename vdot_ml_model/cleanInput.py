import pandas as pd

def clean_strava_csv(input_csv_path: str, output_csv_path: str) -> None:
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

    df["start_date"] = pd.to_datetime(
        df["start_date"],
        format="%b %d, %Y, %I:%M:%S %p",
        errors="coerce"
    )

    df = df.dropna(subset=["distance", "moving_time"])
    df = df.reset_index(drop=True)

    df["distance"] = df["distance"].astype(float)
    sample_max = df["distance"].abs().max() if not df.empty else 0
    if sample_max > 1000:
        df["distance_km"] = df["distance"] / 1000.0
        detected_unit = "meters"
    else:
        # assume input was already in kilometers
        df["distance_km"] = df["distance"].copy()
        detected_unit = "kilometers"

    df["distance_miles"] = df["distance_km"] * 0.621371
    print(f"Detected distance unit: {detected_unit}. Converted to distance_km and distance_miles.")

    df.to_csv(output_csv_path, index=False)
    print(f"✅ Cleaned Strava CSV saved to: {output_csv_path}")
    # Change to write to database instead of csv