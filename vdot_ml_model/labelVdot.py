import pandas as pd
import numpy as np


def calculate_vdot(distance_m: float, time_sec: float) -> float:
    t = time_sec / 60  # minutes
    v = distance_m / t  # meters per minute

    vo2 = -4.60 + 0.182258 * v + 0.000104 * (v ** 2)
    percent_vo2max = (0.8 + 0.1894393 * np.exp(-0.012778 * t) + 0.2989558 * np.exp(-0.1932605 * t))

    return vo2 / percent_vo2max


def find_race_like_efforts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["distance_miles"] = df["distance_km"] * 0.621371
    df["stoppage_ratio"] = df["moving_time"] / df["elapsed_time"]

    return df[
        (df["average_heartrate"] >= 160) &
        (df["distance_miles"] >= 3.0) &
        (df["stoppage_ratio"] >= 0.97) # Stopped no more than 3% of the time
    ]

def label_rolling_features(runs_df: pd.DataFrame, rolling_df: pd.DataFrame, output_csv: str) -> None:

    runs = runs_df.copy()
    rolling = rolling_df.copy()

    race_runs = find_race_like_efforts(runs)

    race_runs["vdot"] = race_runs.apply(
        lambda r: calculate_vdot(
            distance_m=r["distance_km"] * 1000,
            time_sec=r["moving_time"]
        ), axis=1
    )

    # Sort by date
    race_runs = race_runs.sort_values("start_date")

    # Keep only the BEST VDOT in a 21-day window
    filtered_races = []

    last_kept_date = None

    for _, row in race_runs.iterrows():
        if last_kept_date is None:
            filtered_races.append(row)
            last_kept_date = row["start_date"]
            continue

        if (row["start_date"] - last_kept_date).days >= 21:
            filtered_races.append(row)
            last_kept_date = row["start_date"]

    race_runs = pd.DataFrame(filtered_races)

    race_runs = race_runs[
        (race_runs["vdot"] > 30) &
        (race_runs["vdot"] < 80)
    ]

    labeled_rows = []

    for _, race in race_runs.iterrows():
        prior = rolling[rolling["start_date"] < race["start_date"]]
        if prior.empty:
            continue

        row = prior.iloc[-1].copy()
        row["vdot"] = race["vdot"]
        labeled_rows.append(row)

    labeled_df = pd.DataFrame(labeled_rows).reset_index(drop=True)
    labeled_df.to_csv(output_csv, index=False)

    print("Final VDOT Data Saved. Graph displayed.")

    return labeled_df