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
from supabase import create_client, Client
import os

def clean_and_build_dataset(file_stream):
    try: 
        csv_string = file_stream.read().decode('utf-8')
        csv_io = StringIO(csv_string)

        clean_data = clean_strava_csv(input_csv_path=csv_io)
        write_rundata_to_db(clean_data)
        clean_data["start_date"] = pd.to_datetime(clean_data["start_date"])

        rolling_features_data = build_rolling_features(df=clean_data)
        last_30_days = rolling_features_data.iloc[-1].copy() # last 30 days of activity

        vdot_data = label_rolling_features(runs_df=clean_data, rolling_df=rolling_features_data, output_csv="vdot_ml_model/vdot_ml_dataset.csv")

        last_30_days_for_db = last_30_days.copy()
        last_30_days_for_db["start_date"] = pd.Timestamp(last_30_days_for_db["start_date"]).strftime('%Y-%m-%d %H:%M:%S')
        write_recent_activity_to_db(pd.DataFrame([last_30_days_for_db]))

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

def write_rundata_to_db(df: pd.DataFrame):

    user = 'cb6541ac-4f5f-48ce-9f59-87260d595a27'

    SUPABASE_URL = os.getenv('DB_URL')
    SUPABASE_KEY = os.getenv('DB_KEY')

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Delete current user's data
    supabase.table("RunData").delete().eq("user", user).execute()
    print("Existing user data deleted.")

    data = df.to_dict(orient='records')
    print(data)

    count = 0
    for record in data:
        data_to_insert = {
            "distance": float(record['distance']),
            "moving_time": float(record['moving_time']),
            "elapsed_time": float(record['elapsed_time']),
            "average_speed": float(record['average_speed']),
            "average_heartrate": float(record['average_heartrate']),
            "max_heartrate": float(record['max_heartrate']),
            "total_elevation_gain": float(record['total_elevation_gain']),
            "type": record['type'],
            "start_date": record['start_date'],
            "distance_km": float(record['distance_km']),
            "distance_miles": float(record['distance_miles']),
            "user": user
        }
    
        try:
            supabase.table("RunData").insert(data_to_insert).execute()
            count += 1
            print(f"✅ Data successfully written to the database. Count: {count}")
        except Exception as e:
            print(f"❌ Failed to write data to the database. Error: {e}")

def write_recent_activity_to_db(df: pd.DataFrame):

    user = 'cb6541ac-4f5f-48ce-9f59-87260d595a27'

    SUPABASE_URL = os.getenv('DB_URL')
    SUPABASE_KEY = os.getenv('DB_KEY')

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    supabase.table("RecentActivity").delete().eq("user", user).execute()
    print("Existing user data deleted.")

    data = df.to_dict(orient='records')
    print(data)

    count = 0
    for record in data:
        data_to_insert = {
            "start_date": record['start_date'],
            "mileage_km_30d": float(record['mileage_km_30d']),
            "mileage_miles_30d": float(record['mileage_miles_30d']),
            "run_count_30d": float(record['run_count_30d']),
            "longest_run_km_30d": float(record['longest_run_km_30d']),
            "longest_run_miles_30d": float(record['longest_run_miles_30d']),
            "avg_pace_sec_per_km_30d": float(record['avg_pace_sec_per_km_30d']),
            "fastest_pace_sec_per_km_30d": float(record['fastest_pace_sec_per_km_30d']),
            "avg_pace_sec_per_mile_30d": float(record['avg_pace_sec_per_mile_30d']),
            "fastest_pace_sec_per_mile_30d": float(record['fastest_pace_sec_per_mile_30d']),
            "avg_hr_30d": float(record['avg_hr_30d']),
            "max_hr_30d": float(record['max_hr_30d']),
            "elevation_gain_m_30d": float(record['elevation_gain_m_30d']),
            "user": user
        }
    
        try:
            supabase.table("RecentActivity").insert(data_to_insert).execute()
            count += 1
            print(f"✅ Recent activity successfully written to the database. Count: {count}")
        except Exception as e:
            print(f"❌ Failed to write recent activity to the database. Error: {e}")
