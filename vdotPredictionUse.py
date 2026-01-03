from vdotPredictor import VDOTPredictor
from planParser import main as parse_plan
import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from data_pipeline.buildRollingFeatures import build_rolling_features


load_dotenv()

def get_prediction(user, parsed_plan):
    rolling_features_df = load_rolling_features(user)
    training_plan_df = parsed_plan

    predictor = VDOTPredictor()

    prediction = predictor.predict(
        current_vdot=59.2,
        recent_rolling_features=rolling_features_df.iloc[-1:],
        training_plan_df=training_plan_df,
        weeks=4
    )

    vdot_predicted, pct_increase = predictor.print_prediction(prediction)
    final_vdot_predicted = round(vdot_predicted, 2)
    final_pct_increase = round(pct_increase, 2)
    return final_vdot_predicted, final_pct_increase

def load_rolling_features(user):
    SUPABASE_URL = os.getenv('DB_URL')
    SUPABASE_KEY = os.getenv('DB_KEY')

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        supabase.table("RunData")
        .select("*")
        .eq("user", user).execute()
    )

    data = response.data

    clean_data = pd.DataFrame(data)
    clean_data = clean_data.drop('user', axis=1)
    clean_data = clean_data.drop('id', axis=1)
    clean_data["start_date"] = pd.to_datetime(clean_data["start_date"])

    rolling_features_data = build_rolling_features(df=clean_data)

    return rolling_features_data