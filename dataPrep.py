from vdot_ml_model.cleanInput import clean_strava_csv
from vdot_ml_model.buildRollingFeatures import build_rolling_features
from vdot_ml_model.labelVdot import label_rolling_features
from vdot_ml_model.variableVdotPredictor import predict_vdot

import pandas as pd
import matplotlib.pyplot as plt

clean_data = clean_strava_csv(input_csv_path="vdot_ml_model/activities_most_recent.csv")

rolling_features_data = build_rolling_features(df=clean_data)

label_rolling_features(runs_df=clean_data, rolling_df=rolling_features_data, output_csv="vdot_ml_model/vdot_ml_dataset.csv")

# Plot VDOT over time
df = pd.read_csv('vdot_ml_model/vdot_ml_dataset.csv')
df = df.sort_values("start_date")
plt.plot(df["start_date"], df["vdot"], marker='o', linestyle='-')
plt.xticks(rotation=45)
plt.xlabel('Index')
plt.ylabel('Value')
plt.title('Column Data')
plt.show()

predict_vdot_current = predict_vdot(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities.csv", months_ahead=0, verbose=False)
print("Current_Prediction:", predict_vdot_current['predicted_vdot'])

predict_vdot_3m = predict_vdot(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities.csv", months_ahead=3, verbose=False)
print("3m_Prediction:", predict_vdot_3m['predicted_vdot'])

predict_vdot_6m = predict_vdot(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities.csv", months_ahead=6, verbose=False)
print("6m_Prediction:", predict_vdot_6m['predicted_vdot'])