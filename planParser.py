import re
import pandas as pd
from typing import List, Tuple

def parse_mileage(mileage_str: str) -> float:
    match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', mileage_str)
    if match:
        return float(match.group(2))
    match = re.search(r'(\d+(?:\.\d+)?)', mileage_str)
    if match:
        return float(match.group(1))
    return 0.0

def estimate_time(miles: float, pace_type: str) -> str:
    pace_minutes_per_mile = {
        'easy': 10.0,
        'threshold': 7.5,
        'tempo': 7.5,
        'interval': 6.5,
        'strides': 2.0,
        'cross-training': 37.5,
        'rest': 0.0
    }
    
    minutes_per_mile = pace_minutes_per_mile.get(pace_type, 10.0)
    if miles == 0 or pace_type == 'rest':
        return '0m'
    
    total_minutes = round(miles * minutes_per_mile)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def get_run_type(day_text: str) -> str:
    day_lower = day_text.lower()
    
    if 'cross-training' in day_lower or 'cycling' in day_lower or 'swimming' in day_lower or 'elliptical' in day_lower:
        return 'cross-training'
    elif 'rest' in day_lower:
        return 'rest'
    elif 'interval' in day_lower:
        return 'interval'
    elif 'tempo' in day_lower:
        return 'threshold'
    elif 'long run' in day_lower:
        return 'long'
    elif 'easy run' in day_lower or 'easy' in day_lower:
        return 'easy'
    else:
        return 'easy'

def parse_running_schedule(text: str) -> List[Tuple[int, float, str, str]]:
    runs = []
    run_number = 1
    
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Match Day 1, Day 2, etc. OR Monday, Tuesday, etc. OR * **Day 1:**
        day_pattern = r'^[\*\-]?\s*\*{0,2}(Day\s+\d+|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\*{0,2}:?'
        day_match = re.match(day_pattern, line, re.IGNORECASE)
        
        if day_match:
            # Extract the description after the day indicator
            if ':' in line:
                rest_of_line = line.split(':', 1)[1].strip()
            else:
                rest_of_line = line.split(day_match.group(1), 1)[-1].strip()
            
            # Remove markdown formatting
            rest_of_line = rest_of_line.replace('**', '').replace('*', '')
            
            full_description = rest_of_line
            
            # Collect multi-line descriptions
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Stop if empty line or new day/section
                if not next_line:
                    j += 1
                    continue
                
                # Check if we've hit a new day or section header
                if re.match(day_pattern, next_line, re.IGNORECASE):
                    break
                if any(keyword in next_line.lower() for keyword in ['week', 'approx', 'pace guide', 'fitness']):
                    if ':' in next_line or next_line.isupper():
                        break
                
                # Add to description if it looks like part of the workout
                if (next_line.startswith(('*', '-', '1', '2', '3', '4', '5', '6', '7', '8', '9')) 
                    or any(keyword in next_line.lower() for keyword in ['mile', 'min', 'warm', 'cool', 'pace', 'recovery', 'repeat', 'effort'])):
                    full_description += ' ' + next_line.replace('*', '').replace('**', '')
                    j += 1
                else:
                    break
            
            run_type = get_run_type(full_description)
            
            # Handle rest and cross-training
            if run_type == 'rest':
                runs.append((run_number, 0, '0m', 'rest'))
                run_number += 1
            elif run_type == 'cross-training':
                # Extract time if available
                time_match = re.search(r'(\d+)\s*-\s*(\d+)\s*min', full_description)
                if time_match:
                    time_str = f"{time_match.group(2)}m"
                else:
                    time_str = "0m"
                runs.append((run_number, 0, time_str, 'cross-training'))
                run_number += 1
            else:
                # Extract mileage for actual runs
                mileage = parse_mileage(full_description)
                if mileage > 0:
                    time_str = estimate_time(mileage, run_type)
                    runs.append((run_number, mileage, time_str, run_type))
                    run_number += 1
            
            i = j
        else:
            i += 1
    
    return runs

def create_dataframe(runs: List[Tuple[int, float, str, str]]) -> pd.DataFrame:
    df = pd.DataFrame(runs, columns=['run #', 'miles', 'expected time', 'type'])
    return df

def main(plan):
    schedule_text = plan
    runs = parse_running_schedule(schedule_text)
    df = create_dataframe(runs)
    
    return df