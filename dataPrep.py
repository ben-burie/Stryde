from vdot_ml_model.cleanInput import clean_strava_csv
from vdot_ml_model.buildRollingFeatures import build_rolling_features
from vdot_ml_model.labelVdot import label_rolling_features

import pandas as pd
import matplotlib.pyplot as plt

clean_data = clean_strava_csv(
    input_csv_path="vdot_ml_model/activities_most_recent.csv"
)

rolling_features_data = build_rolling_features(
    df=clean_data
)

label_rolling_features(
    runs_df=clean_data,
    rolling_df=rolling_features_data,
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