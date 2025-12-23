import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import warnings
import json
warnings.filterwarnings('ignore')


def predict_vdot_v2(vdot_csv_path, runs_csv_path, months_ahead=1, verbose=True):
    """
    Predict VDOT score multiple months from today using blended ARIMA + Linear Regression model.
    
    Parameters:
    -----------
    vdot_csv_path : str
        Path to CSV file with VDOT race data
        Required columns: start_date, vdot
    
    runs_csv_path : str
        Path to CSV file with training runs data
        Required columns: start_date, distance_km, average_speed, average_heartrate
    
    months_ahead : int
        Number of months to predict ahead (default: 1)
    
    verbose : bool
        If True, print detailed output. If False, only return JSON.
    
    Returns:
    --------
    dict : Forecast output containing predicted VDOT and confidence intervals
    """
    
    try:
        # Load data
        vdot_df = pd.read_csv(vdot_csv_path)
        vdot_df['start_date'] = pd.to_datetime(vdot_df['start_date'])
        vdot_df = vdot_df.sort_values('start_date').reset_index(drop=True)
        
        runs_df = pd.read_csv(runs_csv_path)
        runs_df['start_date'] = pd.to_datetime(runs_df['start_date'])
        runs_df = runs_df.sort_values('start_date').reset_index(drop=True)
        
        if verbose:
            print(f"Loaded {len(vdot_df)} VDOT data points and {len(runs_df)} training runs")
        
        def aggregate_training_metrics(runs, start_date, window_days=30):
            """Aggregate training metrics for a rolling window before a date"""
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
        
        # Prepare training data
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
            print(f"VDOT range: {y.min():.2f} - {y.max():.2f}")
        
        # Create time series dataframe
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
            print("MODEL FITTING")
            print("="*70)
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        exog_df = pd.DataFrame(
            X_scaled,
            columns=['distance_km_scaled', 'run_count_scaled', 'avg_speed_scaled', 'avg_hr_scaled'],
            index=ts_df.index
        )
        
        # Fit ARIMA model
        if verbose:
            print("\nFitting ARIMA(1,1,1) with exogenous variables...")
        
        try:
            model = ARIMA(ts_df['vdot'], exog=exog_df, order=(1, 1, 1))
            results = model.fit()
            if verbose:
                print("✓ ARIMA model fitted successfully")
        except Exception as e:
            if verbose:
                print(f"Falling back to basic ARIMA: {e}")
            model = ARIMA(ts_df['vdot'], order=(1, 1, 1))
            results = model.fit()
            exog_df = None
        
        # Fit Linear Regression for training-based prediction
        if verbose:
            print("Fitting Linear Regression model...")
        lr_model = LinearRegression()
        lr_model.fit(X, y)
        if verbose:
            print(f"✓ Linear Regression R² score: {lr_model.score(X, y):.4f}")
        
        # Make prediction
        if verbose:
            print("\n" + "="*70)
            print(f"{months_ahead}-MONTH AHEAD PREDICTION")
            print("="*70)
        
        last_date = ts_df.index[-1]
        last_vdot = ts_df['vdot'].iloc[-1]
        today = datetime.now()
        days_ahead = int(months_ahead * 30.44)
        future_date = today + timedelta(days=days_ahead)
        
        if verbose:
            print(f"\nLast VDOT recorded: {last_vdot:.2f} on {last_date.strftime('%Y-%m-%d')}")
            print(f"Prediction date:   {future_date.strftime('%Y-%m-%d')} ({months_ahead} month(s) from today)")
        
        # Get recent training metrics
        recent_metrics = aggregate_training_metrics(runs_df, last_date, window_days=30)
        
        forecast_value = None
        lower_bound = None
        upper_bound = None
        change = None
        
        if recent_metrics is not None:
            steps_ahead = max(1, int(months_ahead))
            
            # ARIMA forecast
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
            
            arima_forecast = forecast_result.predicted_mean.iloc[-1]
            conf_int = forecast_result.conf_int(alpha=0.2)
            lower_bound = conf_int.iloc[-1, 0]
            upper_bound = conf_int.iloc[-1, 1]
            
            # Linear Regression forecast
            lr_forecast = lr_model.predict(recent_X)[0]
            
            # Blend predictions: 60% ARIMA (trend), 40% Linear Regression (training)
            forecast_value = (0.5 * arima_forecast) + (0.5 * lr_forecast)
            
            change = forecast_value - last_vdot
            change_str = f"+{change:.2f}" if change >= 0 else f"{change:.2f}"
            
            if verbose:
                print(f"\nARIMA Forecast:          {arima_forecast:.2f}")
                print(f"Training-Based Forecast: {lr_forecast:.2f}")
                print(f"Blended Prediction:      {forecast_value:.2f}")
                print(f"Change from current:     {change_str}")
                print(f"80% Confidence Interval: {lower_bound:.2f} - {upper_bound:.2f}")
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
            print("FORECAST OUTPUT")
            print("="*70)
            print(json.dumps(forecast_output, indent=2))
        
        return forecast_output
    
    except Exception as e:
        error_output = {
            'error': str(e),
            'message': 'Failed to generate VDOT forecast'
        }
        if verbose:
            print(f"\n❌ Error: {e}")
        return error_output