import pandas as pd
import numpy as np
from typing import Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class VDOTPredictor:
    
    def __init__(self):
        """Initialize the predictor."""
        self.current_vdot = None
        self.recent_mileage = None
        self.recent_intensity = None
        
    def analyze_recent_training(self, rolling_features_df: pd.DataFrame) -> Dict:
        # Get most recent data
        recent = rolling_features_df.iloc[-1]
        
        # Volume metrics
        recent_14d_mileage = recent.get('mileage_miles_14d', 0)
        recent_30d_mileage = recent.get('mileage_miles_30d', 0)
        
        # Calculate weekly volume
        weekly_mileage_recent = recent_14d_mileage / 2
        
        # Intensity
        avg_pace_14d = recent.get('avg_pace_sec_per_km_14d', 600)
        fastest_pace_14d = recent.get('fastest_pace_sec_per_km_14d', 360)
        
        # Intensity factor (lower pace = higher intensity)
        intensity_factor = fastest_pace_14d / (avg_pace_14d + 1)
        
        # Run frequency
        run_count_14d = recent.get('run_count_14d', 6)
        runs_per_week = run_count_14d / 2
        
        # Long run
        longest_run = recent.get('longest_run_miles_14d', 0)
        
        return {
            'weekly_mileage': weekly_mileage_recent,
            'mileage_30d': recent_30d_mileage,
            'intensity_factor': intensity_factor,
            'runs_per_week': runs_per_week,
            'longest_run': longest_run,
            'avg_pace_sec_per_km': avg_pace_14d,
            'fastest_pace_sec_per_km': fastest_pace_14d,
        }
    
    def engineer_future_plan_features(self, 
                                      training_plan_df: pd.DataFrame) -> Dict:
        plan = training_plan_df.copy()
        
        # EXCLUDE cross-training and rest from running mileage
        running_plan = plan[~plan['type'].isin(['cross-training', 'rest'])].copy()
        
        # Calculate plan metrics (RUNNING ONLY)
        total_mileage = running_plan['miles'].sum()
        run_count = len(running_plan)
        avg_run_distance = running_plan[running_plan['miles'] > 0]['miles'].mean() if any(running_plan['miles'] > 0) else 0
        longest_run = running_plan['miles'].max()
        
        # Run type distribution (from running_plan only)
        easy_runs = len(running_plan[running_plan['type'] == 'easy'])
        tempo_runs = len(running_plan[running_plan['type'] == 'threshold'])
        interval_runs = len(running_plan[running_plan['type'] == 'interval'])
        long_runs = len(running_plan[running_plan['type'] == 'long'])
        
        weekly_mileage = total_mileage / 4
        weekly_runs = run_count / 4
        
        # Intensity score (weighted by run type)
        # Easy = 1.0x, Threshold = 2.5x, Interval = 3.5x, Long = 1.5x
        intensity_score = (
            easy_runs * 1.0 +
            tempo_runs * 2.5 +
            interval_runs * 3.5 +
            long_runs * 1.5
        )
        
        weekly_intensity = intensity_score / 4
        
        return {
            'total_mileage': total_mileage,
            'weekly_mileage': weekly_mileage,
            'run_count': run_count,
            'weekly_runs': weekly_runs,
            'avg_run_distance': avg_run_distance,
            'longest_run': longest_run,
            'easy_runs': easy_runs,
            'tempo_runs': tempo_runs,
            'interval_runs': interval_runs,
            'long_runs': long_runs,
            'intensity_score': intensity_score,
            'weekly_intensity': weekly_intensity,
        }
    
    def predict(self, current_vdot: float, recent_rolling_features: pd.DataFrame, training_plan_df: pd.DataFrame, weeks: int = 4) -> Dict:

        recent = self.analyze_recent_training(recent_rolling_features)
        

        plan = self.engineer_future_plan_features(training_plan_df)
        
        # BASE IMPROVEMENT from adequate training volume
        volume_change_pct = (plan['weekly_mileage'] - recent['weekly_mileage']) / (recent['weekly_mileage'] + 1)
        volume_improvement = current_vdot * (volume_change_pct * 0.03)
        
        # INTENSITY IMPROVEMENT
        intensity_improvement = (
            plan['tempo_runs'] * 0.12 +
            plan['interval_runs'] * 0.20
        )
        
        # CONSISTENCY BONUS
        run_frequency_bonus = 0
        if plan['weekly_runs'] >= 4:
            run_frequency_bonus = 0.10
        elif plan['weekly_runs'] >= 5:
            run_frequency_bonus = 0.15
        elif plan['weekly_runs'] >= 6:
            run_frequency_bonus = 0.20
        
        # LONG RUN BENEFIT
        if plan['longest_run'] > recent['longest_run']:
            long_run_improvement = (plan['longest_run'] - recent['longest_run']) * 0.01
        else:
            long_run_improvement = 0
        
        # DIMINISHING RETURNS (fitness ceiling)
        if current_vdot < 45:
            diminishing_factor = 1.0  # Beginner - good response
        elif current_vdot < 55:
            diminishing_factor = 0.85  # Intermediate
        elif current_vdot < 65:
            diminishing_factor = 0.70  # Advanced
        else:
            diminishing_factor = 0.55  # Elite - very hard to improve
        
        # ADEQUATE RECOVERY PENALTY
        training_stress = plan['weekly_intensity'] * plan['weekly_runs']
        
        if training_stress > 25:  # Very high stress
            recovery_penalty = -0.5
        elif training_stress > 20:  # High stress
            recovery_penalty = -0.2
        else:
            recovery_penalty = 0
        
        # TOTAL PREDICTION
        total_improvement = (
            volume_improvement +
            intensity_improvement +
            run_frequency_bonus +
            long_run_improvement +
            recovery_penalty
        ) * diminishing_factor
        
        if plan['weekly_mileage'] > 0 and total_improvement < 0.1:
            total_improvement = 0.1
        
        tempo_interval_count = plan['tempo_runs'] + plan['interval_runs']
        if tempo_interval_count >= 2:
            confidence_range = total_improvement * 0.15
        else:
            confidence_range = total_improvement * 0.25
        
        lower_bound = total_improvement - 1.96 * confidence_range
        upper_bound = total_improvement + 1.96 * confidence_range
        
        # Ensure bounds are reasonable
        lower_bound = max(lower_bound, total_improvement * 0.5)
        upper_bound = min(upper_bound, total_improvement * 1.5)
        
        result = {
            'predicted_vdot_improvement': total_improvement,
            'current_vdot': current_vdot,
            'projected_vdot': current_vdot + total_improvement,
            'confidence_interval_lower': lower_bound,
            'confidence_interval_upper': upper_bound,
            'plan_summary': {
                'total_mileage': plan['total_mileage'],
                'weekly_mileage': plan['weekly_mileage'],
                'weekly_runs': plan['weekly_runs'],
                'intensity_score': plan['weekly_intensity'],
                'volume_change_pct': volume_change_pct * 100,
            },
            'improvement_breakdown': {
                'volume_improvement': volume_improvement,
                'intensity_improvement': intensity_improvement,
                'run_frequency_bonus': run_frequency_bonus,
                'long_run_improvement': long_run_improvement,
                'recovery_penalty': recovery_penalty,
                'diminishing_factor': diminishing_factor,
            }
        }
        
        return result
    
    def print_prediction(self, prediction: Dict):
        current = prediction['current_vdot']
        improvement = prediction['predicted_vdot_improvement']
        projected = prediction['projected_vdot']
        
        if improvement > 0:
            pct_improvement = (improvement / current) * 100
        else:
            pct_improvement = 0.0

        return projected, pct_improvement