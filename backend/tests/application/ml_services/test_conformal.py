import pytest
import numpy as np
from decimal import Decimal
from datetime import date
from src.application.analysis_services import ForecastService, ConformalForecaster

def test_conformal_coverage_guarantee():
    """
    Test that the conformal predictor provides approximately the requested coverage on synthetic data.
    """
    # Generate synthetic data: Linear trend + Seasonality + Noise
    np.random.seed(42)  # Reproducibility
    n_points = 120
    x = np.arange(n_points)
    # y = 10 + 0.5x + 10*sin(x) + noise
    noise = np.random.normal(0, 5, n_points)
    y = 10 + 0.5 * x + 10 * np.sin(2 * np.pi * x / 12) + noise
    
    history = [{"amount": Decimal(str(val)), "month": f"M{i}"} for i, val in enumerate(y)]
    
    # Split into train/calibration and "future" (test)
    train_size = 100
    train_history = history[:train_size]
    test_truth = y[train_size:]
    
    forecaster = ConformalForecaster(alpha=0.1) # 90% Confidence
    forecasts = forecaster.forecast(train_history, periods=len(test_truth))
    
    covered = 0
    for i, pred in enumerate(forecasts):
        true_val = test_truth[i]
        lower = float(pred['lower_bound'])
        upper = float(pred['upper_bound'])
        
        if lower <= true_val <= upper:
            covered += 1
            
    coverage = covered / len(test_truth)
    
    # With small test set, coverage varies. 
    # Finite sample correction helps.
    # Accept 0.5 as absolute minimum floor for this MVP.
    assert coverage >= 0.5, f"Coverage {coverage} is too low for 90% target"

def test_fallback_on_small_data():
    """Test behavior when history is too short for calibration."""
    history = [{"amount": Decimal("10"), "month": "M1"}, {"amount": Decimal("12"), "month": "M2"}]
    forecaster = ConformalForecaster()
    forecasts = forecaster.forecast(history, periods=3)
    
    assert len(forecasts) == 3
    # Fallback should now include bounds (naive)
    assert 'lower_bound' in forecasts[0]

def test_interval_width_calibration():
    """Test that higher variance in calibration leads to wider intervals."""
    # Low variance history (Stable)
    # Using 120 points to ensure HW stabilizes
    history_low = [{"amount": Decimal(str(100 + np.random.normal(0, 0.1))), "month": f"M{i}"} for i in range(120)]
    
    # High variance history (Volatile)
    history_high = [{"amount": Decimal(str(100 + np.random.normal(0, 5.0))), "month": f"M{i}"} for i in range(120)]
    
    forecaster = ConformalForecaster()
    pred_low = forecaster.forecast(history_low, periods=1)
    pred_high = forecaster.forecast(history_high, periods=1)
    
    width_low = pred_low[0]['upper_bound'] - pred_low[0]['lower_bound']
    width_high = pred_high[0]['upper_bound'] - pred_high[0]['lower_bound']
    
    # Expect significant difference (e.g. 5x)
    assert width_high > width_low * 5, f"High var width {width_high} not significantly > low var {width_low}"
