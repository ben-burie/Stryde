import matplotlib
matplotlib.use('Agg')

from vdot_ml_model.cleanInput import clean_strava_csv
from vdot_ml_model.buildRollingFeatures import build_rolling_features
from vdot_ml_model.labelVdot import label_rolling_features
from vdot_ml_model.variableVdotPredictor import predict_vdot
from vdot_ml_model.variableVdotPredictor_v2 import predict_vdot_v2

import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

def clean_and_build_dataset(file_stream):
    try: 
        csv_string = file_stream.read().decode('utf-8')
        csv_io = StringIO(csv_string)

        clean_data = clean_strava_csv(input_csv_path=csv_io)
        rolling_features_data = build_rolling_features(df=clean_data)
        vdot_data = label_rolling_features(runs_df=clean_data, rolling_df=rolling_features_data, output_csv="vdot_ml_model/vdot_ml_dataset.csv")

        if vdot_data.empty:
            print("Warning: No race-like efforts found in data")
            return 0.0, int(round(clean_data["average_heartrate"].mean()))

        latest_vdot = vdot_data.sort_values("start_date").iloc[-1]
        
        vdot_value = float(latest_vdot['vdot']) 
        avg_hr = int(round(clean_data["average_heartrate"].mean()))
        
        print(f"VDOT (type: {type(vdot_value).__name__}): {vdot_value}")
        print(f"Avg HR (type: {type(avg_hr).__name__}): {avg_hr}")
        
        return vdot_value, avg_hr
        
    except Exception as e:
        print(f"Error in clean_and_build_dataset: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise
    



"""
predict_vdot_current = predict_vdot(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities copy.csv", months_ahead=0, verbose=False)
print("Current_Prediction:", predict_vdot_current['predicted_vdot'])

predict_vdot_3m = predict_vdot(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities copy.csv", months_ahead=3, verbose=False)
print("3m_Prediction:", predict_vdot_3m['predicted_vdot'])

predict_vdot_6m = predict_vdot(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities copy.csv", months_ahead=6, verbose=False)
print("6m_Prediction:", predict_vdot_6m['predicted_vdot'])

print("\n\n\n\nV2 model:")

predict_vdot_current = predict_vdot_v2(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities.csv", months_ahead=0, verbose=False)
print("Current_Prediction:", predict_vdot_current['predicted_vdot'])

predict_vdot_3m = predict_vdot_v2(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities.csv", months_ahead=3, verbose=False)
print("3m_Prediction:", predict_vdot_3m['predicted_vdot'])

predict_vdot_6m = predict_vdot_v2(vdot_csv_path="vdot_ml_model/vdot_ml_dataset.csv", runs_csv_path="vdot_ml_model/clean_activities.csv", months_ahead=6, verbose=False)
print("6m_Prediction:", predict_vdot_6m['predicted_vdot'])
"""