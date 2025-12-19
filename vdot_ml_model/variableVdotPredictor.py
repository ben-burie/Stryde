import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import StandardScaler
import warnings
import json
warnings.filterwarnings('ignore')


def predict_vdot(vdot_csv_path, runs_csv_path, months_ahead=1, verbose=True):
    
    try:
        # Load VDOT race data
        vdot_df = pd.read_csv(vdot_csv_path)
        vdot_df['start_date'] = pd.to_datetime(vdot_df['start_date'])
        vdot_df = vdot_df.sort_values('start_date').reset_index(drop=True)
        
        # Load training runs data
        runs_df = pd.read_csv(runs_csv_path)
        runs_df['start_date'] = pd.to_datetime(runs_df['start_date'])
        runs_df = runs_df.sort_values('start_date').reset_index(drop=True)
        
        if verbose:
            print(f"Loaded {len(vdot_df)} VDOT data points and {len(runs_df)} training runs")
        
        def aggregate_training_metrics(runs, start_date, window_days=30):
            """
            Aggregate training metrics for a rolling window before a date
            """
            window_start = start_date - timedelta(days=window_days)
            window_runs = runs[(runs['start_date'] >= window_start) & (runs['start_date'] < start_date)]
            
            if len(window_runs) == 0:
                return None
            
            metrics = {
                'total_distance_km': window_runs['distance_km'].sum(),
                'run_count': len(window_runs),
                'avg_speed_kmh': window_runs['average_speed'].mean(),
                'avg_hr': window_runs['average_heartrate'].mean(),
            }
            return metrics
        
        X_data = []
        y_data = []
        dates = []
        
        for idx, row in vdot_df.iterrows():
            vdot_date = row['start_date']
            vdot_score = row['vdot']
            
            agg_metrics = aggregate_training_metrics(runs_df, vdot_date, window_days=30)
            
            if agg_metrics is not None:
                X_data.append([
                    agg_metrics['total_distance_km'],
                    agg_metrics['run_count'],
                    agg_metrics['avg_speed_kmh'],
                    agg_metrics['avg_hr'],
                ])
                y_data.append(vdot_score)
                dates.append(vdot_date)
        
        X = np.array(X_data)
        y = np.array(y_data)
        dates = np.array(dates)
        
        if verbose:
            print(f"\nCreated {len(y)} VDOT observations with preceding 30-day training context")
            print(f"Features: distance_km, run_count, avg_speed, avg_hr")
            print(f"VDOT range: {y.min():.2f} - {y.max():.2f}")
        
        ts_df = pd.DataFrame({
            'date': dates,
            'vdot': y,
            'distance_km': X[:, 0],
            'run_count': X[:, 1],
            'avg_speed_kmh': X[:, 2],
            'avg_hr': X[:, 3],
        })
        ts_df = ts_df.set_index('date')
        
        if verbose:
            print("\n" + "="*70)
            print("TIME SERIES ANALYSIS")
            print("="*70)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        exog_df = pd.DataFrame(
            X_scaled,
            columns=['distance_km_scaled', 'run_count_scaled', 'avg_speed_scaled', 'avg_hr_scaled'],
            index=ts_df.index
        )

        if verbose:
            print("\nFitting ARIMA model with training metrics as exogenous variables...")
        
        try:
            model = ARIMA(ts_df['vdot'], exog=exog_df, order=(2, 0, 1))
            results = model.fit(disp=False)
            if verbose:
                print("✓ ARIMA(1,1,1) model with exogenous variables fitted successfully")
                print(f"AIC: {results.aic:.2f}")
                print(f"BIC: {results.bic:.2f}")
        except Exception as e:
            if verbose:
                print(f"Note: ARIMA with exogenous variables had issues, falling back to basic ARIMA")
                print(f"Error: {e}")
            model = ARIMA(ts_df['vdot'], order=(2, 0, 1))
            results = model.fit()
            exog_df = None
            if verbose:
                print("✓ ARIMA(1,1,1) model fitted successfully")
        
        # Make prediction
        if verbose:
            print("\n" + "="*70)
            print(f"{months_ahead}-MONTH AHEAD PREDICTION")
            print("="*70)
        
        last_date = ts_df.index[-1]
        last_vdot = ts_df['vdot'].iloc[-1]
        today = datetime.now()
        
        # Calculate future date based on months_ahead
        days_ahead = int(months_ahead * 30.44)  # Average days per month
        future_date = today + timedelta(days=days_ahead)
        
        if verbose:
            print(f"\nLast VDOT recorded: {last_vdot:.2f} on {last_date.strftime('%Y-%m-%d')}")
            print(f"Today's date:      {today.strftime('%Y-%m-%d')}")
            print(f"Prediction date:   {future_date.strftime('%Y-%m-%d')} ({months_ahead} month(s) from today)\n")
        
        recent_metrics = aggregate_training_metrics(runs_df, last_date, window_days=30)
        
        forecast_value = None
        lower_bound = None
        upper_bound = None
        change = None
        
        if recent_metrics is not None:
            steps_ahead = max(1, int(months_ahead))
            
            recent_X = np.array([[
                recent_metrics['total_distance_km'],
                recent_metrics['run_count'],
                recent_metrics['avg_speed_kmh'],
                recent_metrics['avg_hr'],
            ]])
            recent_X_scaled = scaler.transform(recent_X)
            
            future_exog = pd.DataFrame(
                np.tile(recent_X_scaled, (steps_ahead, 1)),
                columns=['distance_km_scaled', 'run_count_scaled', 'avg_speed_scaled', 'avg_hr_scaled']
            )
            
            if exog_df is not None:
                forecast_result = results.get_forecast(steps=steps_ahead, exog=future_exog)
            else:
                forecast_result = results.get_forecast(steps=steps_ahead)
            
            forecast_value = forecast_result.predicted_mean.iloc[-1]
            conf_int = forecast_result.conf_int(alpha=0.2)
            lower_bound = conf_int.iloc[-1, 0]
            upper_bound = conf_int.iloc[-1, 1]
            
            change = forecast_value - last_vdot
            change_str = f"+{change:.2f}" if change >= 0 else f"{change:.2f}"
            
            if verbose:
                print(f"Predicted VDOT ({months_ahead} month(s)):     {forecast_value:.2f}")
                print(f"Change from current:       {change_str}")
                print(f"80% Confidence Interval:   {lower_bound:.2f} - {upper_bound:.2f}")
                print(f"\nRecent Training Context (last 30 days):")
                print(f"  Total distance:          {recent_metrics['total_distance_km']:.1f} km")
                print(f"  Number of runs:          {recent_metrics['run_count']:.0f}")
                print(f"  Average pace:            {60000/recent_metrics['avg_speed_kmh']:.1f} min/km")
                print(f"  Average heart rate:      {recent_metrics['avg_hr']:.1f} bpm")
        
        # Create forecast output
        forecast_output = {
            'last_vdot': round(last_vdot, 2),
            'last_date': last_date.strftime('%Y-%m-%d'),
            'predicted_vdot': round(forecast_value, 2) if forecast_value else None,
            'prediction_date': future_date.strftime('%Y-%m-%d'),
            'lower_bound_80pct': round(lower_bound, 2) if lower_bound else None,
            'upper_bound_80pct': round(upper_bound, 2) if upper_bound else None,
            'change': round(change, 2) if change else None,
            'months_ahead': months_ahead
        }
        
        if verbose:
            print("\n" + "="*70)
            print("FORECAST OUTPUT (JSON)")
            print("="*70)
            print(json.dumps(forecast_output, indent=2))
        
        return forecast_output
    
    except Exception as e:
        error_output = {
            'error': str(e),
            'message': 'Failed to generate VDOT forecast'
        }
        if verbose:
            print(f"\nError: {e}")
        return error_output