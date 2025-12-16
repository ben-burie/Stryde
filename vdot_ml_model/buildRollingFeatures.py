import pandas as pd
import numpy as np

# Change to pull from database instead of csv
def build_rolling_features(df: pd.DataFrame, windows=(14, 30)) -> pd.DataFrame:

    df = df.copy()
    df = df.sort_values("start_date").reset_index(drop=True)

    df["distance_km"] = df["distance_km"].astype(float)

    # Add a miles column for convenience (1 km = 0.621371 miles)
    df["distance_miles"] = df["distance_km"] * 0.621371
    # Avoid division by zero if distance is zero
    df["pace_sec_per_km"] = df["moving_time"] / df["distance_km"].replace({0: np.nan})
    # seconds per mile (useful for some features or display)
    df["pace_sec_per_mile"] = df["moving_time"] / df["distance_miles"].replace({0: np.nan})

    feature_frames = []

    for window in windows:
        rolling = (df.set_index("start_date").rolling(f"{window}D", closed="left"))

        features = pd.DataFrame({
            f"mileage_km_{window}d": rolling["distance_km"].sum(),
            f"mileage_miles_{window}d": rolling["distance_miles"].sum(),
            f"run_count_{window}d": rolling["distance_km"].count(),
            f"longest_run_km_{window}d": rolling["distance_km"].max(),
            f"longest_run_miles_{window}d": rolling["distance_miles"].max(),
            f"avg_pace_sec_per_km_{window}d": rolling["pace_sec_per_km"].mean(),
            f"fastest_pace_sec_per_km_{window}d": rolling["pace_sec_per_km"].min(),
            f"avg_pace_sec_per_mile_{window}d": rolling["pace_sec_per_mile"].mean(),
            f"fastest_pace_sec_per_mile_{window}d": rolling["pace_sec_per_mile"].min(),
            f"avg_hr_{window}d": rolling["average_heartrate"].mean(),
            f"max_hr_{window}d": rolling["max_heartrate"].max(),
            f"elevation_gain_m_{window}d": rolling["total_elevation_gain"].sum(),
        })

        feature_frames.append(features)

    # Combine all rolling features
    feature_df = pd.concat(feature_frames, axis=1)

    # Merge back with original dates
    final_df = pd.concat([df[["start_date"]].reset_index(drop=True), feature_df.reset_index(drop=True)], axis=1)

    # Drop rows without sufficient history
    final_df = final_df.dropna().reset_index(drop=True)

    print("Rolling features built.")
    return final_df