import os
from google import genai
from dotenv import load_dotenv
from google.genai import types
from supabase import create_client, Client
import json
import datetime

load_dotenv()

client = genai.Client(api_key=os.getenv('API-KEY'))

def load_runs():
    user = 'cb6541ac-4f5f-48ce-9f59-87260d595a27'

    SUPABASE_URL = os.getenv('DB_URL')
    SUPABASE_KEY = os.getenv('DB_KEY')

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
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

def load_recent_activity_summary():
    user = 'cb6541ac-4f5f-48ce-9f59-87260d595a27'

    SUPABASE_URL = os.getenv('DB_URL')
    SUPABASE_KEY = os.getenv('DB_KEY')

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
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

def ask_gemini(prompt):
    allRuns = load_runs()
    recentActivity = load_recent_activity_summary()
    
    # Combined context for the model
    context_data = f"HISTORICAL RUNS:\n{allRuns}\n\nRECENT SUMMARY:\n{recentActivity}"

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
    return response.text

print(ask_gemini("Create me a 30 day training plan."))