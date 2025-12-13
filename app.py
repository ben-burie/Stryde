from vdot_ml_model.cleanInput import clean_strava_csv
from vdot_ml_model.buildRollingFeatures import build_rolling_features

clean_strava_csv(
    input_csv_path="vdot_ml_model/activities.csv",
    output_csv_path="vdot_ml_model/strava_runs_clean.csv"
)

build_rolling_features(
    input_csv_path="vdot_ml_model/strava_runs_clean.csv",
    output_csv_path="vdot_ml_model/strava_rolling_features.csv",
    windows=(14, 30)
)

"""
TO DO:
    -Verify data accuracy
    -Initialize database
    -Fix files reading/writing to csvs instead of database
    -Review cleaning and rolling reatures code and clean it up
"""
