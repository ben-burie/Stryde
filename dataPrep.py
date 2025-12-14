from vdot_ml_model.cleanInput import clean_strava_csv
from vdot_ml_model.buildRollingFeatures import build_rolling_features
from vdot_ml_model.labelVdot import label_rolling_features

import pandas as pd
import matplotlib.pyplot as plt

clean_strava_csv(
    input_csv_path="vdot_ml_model/activities_most_recent.csv",
    output_csv_path="vdot_ml_model/strava_runs_clean.csv"
)

build_rolling_features(
    input_csv_path="vdot_ml_model/strava_runs_clean.csv",
    output_csv_path="vdot_ml_model/strava_rolling_features.csv",
    windows=(14, 30)
)

label_rolling_features(
    runs_csv="vdot_ml_model/strava_runs_clean.csv",
    rolling_csv="vdot_ml_model/strava_rolling_features.csv",
    output_csv="vdot_ml_model/vdot_ml_dataset.csv"
)

# Plot VDOT over time
df = pd.read_csv('vdot_ml_model/vdot_ml_dataset.csv')
df = df.sort_values("start_date")
plt.plot(df["start_date"], df["vdot"])
plt.xticks(rotation=45)
plt.xlabel('Index')
plt.ylabel('Value')
plt.title('Column Data')
plt.show()