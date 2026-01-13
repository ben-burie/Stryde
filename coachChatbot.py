import os
from google import genai
from dotenv import load_dotenv
from google.genai import types
from supabase import create_client, Client
import json
from datetime import datetime
from pathlib import Path
import logging

load_dotenv()

client = genai.Client(api_key=os.getenv('API-KEY'))

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
api_logger = logging.getLogger("gemini_api")
api_logger.setLevel(logging.INFO)
json_handler = logging.FileHandler(log_dir / "gemini_api_calls.jsonl")
json_handler.setLevel(logging.INFO)
api_logger.addHandler(json_handler)

def get_authed_client(user_access_token: str) -> Client:
    SUPABASE_URL = os.getenv('DB_URL')
    SUPABASE_KEY = os.getenv('DB_KEY')
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase.postgrest.auth(user_access_token)
    return supabase

def load_runs(user, user_access_token):

    supabase = get_authed_client(user_access_token)
    response = (
        supabase.table("RunData")
        .select("id, distance_miles, moving_time, average_heartrate, total_elevation_gain, start_date")
        .eq("user", user).execute()
    )

    data = response.data

    run_records_text = "id, Distance (miles), Duration (seconds), Avg Heart Rate, Total Elevation Gain, Start Date\n" + "\n".join(
        [f"{r['id']}, {r['distance_miles']}, {r['moving_time']}, {r['average_heartrate']}, {r['total_elevation_gain']}, {r['start_date']}" for r in data]
    )

    return run_records_text

def load_recent_activity_summary(user, user_access_token):

    supabase = get_authed_client(user_access_token)
    response = (
        supabase.table("RecentActivity")
        .select("id, start_date, mileage_miles_30d, run_count_30d, avg_hr_30d, longest_run_miles_30d, avg_pace_sec_per_mile_30d, elevation_gain_m_30d")
        .eq("user", user).execute()
    )

    data = response.data

    recent_activity_text = "id, Start Date, Mileage (miles), Run Count, Avg Heart Rate, Longest Run (miles), Avg Pace (sec/mile), Elevation Gain (m)\n" + "\n".join(
        [f"{r['id']}, {r['start_date']}, {r['mileage_miles_30d']}, {r['run_count_30d']}, {r['avg_hr_30d']}, {r['longest_run_miles_30d']}, {r['avg_pace_sec_per_mile_30d']}, {r['elevation_gain_m_30d']}" for r in data]
    )

    return recent_activity_text

def load_vdot(user, user_access_token):

    supabase = get_authed_client(user_access_token)
    response = (
        supabase.table("CurrentFitness")
        .select("vdot")
        .eq("user", user).execute()
    )

    data = response.data

    if not data:
        return "No current fitness metrics found."

    metrics = data[0]
    vdot_text = (
        f"VDOT: {metrics['vdot']}\n"
    )

    return vdot_text

def ask_gemini(prompt, user, user_access_token):

    start_time = datetime.now()

    allRuns = load_runs(user, user_access_token)
    recentActivity = load_recent_activity_summary(user, user_access_token)
    vdot = load_vdot(user, user_access_token)
    
    # Combined context for the model
    context_data = f"HISTORICAL RUNS:\n{allRuns}\n\nRECENT SUMMARY:\n{recentActivity}\nJACK DANIELS CURRENT VDOT INDICATOR:\n{vdot}"

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="You are an expert running coach."
            ),
            contents=[
                {"role": "user", "parts": [{"text": context_data}]},
                {"role": "user", "parts": [{"text": prompt}]}
            ],
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        usage_metadata = response.usage_metadata
        
        input_tokens = usage_metadata.prompt_token_count
        output_tokens = usage_metadata.candidates_token_count
        total_tokens = usage_metadata.total_token_count
        
        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 2.5
        total_cost = input_cost + output_cost
        
        log_entry = {
            "timestamp": start_time.isoformat(),
            "user": user,
            "model": "gemini-2.5-flash",
            "prompt_length": len(prompt),
            "context_length": len(context_data),
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            "cost_usd": {
                "input": round(input_cost, 6),
                "output": round(output_cost, 6),
                "total": round(total_cost, 6)
            },
            "duration_seconds": round(duration, 3),
            "status": "success",
            "response_length": len(response.text)
        }
        
        api_logger.info(json.dumps(log_entry))

        return response.text
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_entry = {
            "timestamp": start_time.isoformat(),
            "user": user,
            "model": "gemini-2.5-flash",
            "prompt_length": len(prompt),
            "context_length": len(context_data),
            "duration_seconds": round(duration, 3),
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
        
        api_logger.error(json.dumps(error_entry))
        raise