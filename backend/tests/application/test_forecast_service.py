import pytest
from decimal import Decimal
import numpy as np
from src.application.analysis_services import ForecastService

def test_append_forecast_confidence_intervals():
    """Test that confidence intervals are generated and are not fixed 10% widths."""
    # Create a history with clear variance
    # A sine wave + noise should theoretically produce a decent HW fit with non-zero variance
    history = []
    for i in range(24):
        val = 100 + 10 * np.sin(i * np.pi / 6) + np.random.normal(0, 5)
        history.append({
            "month": f"M{i}", 
            "amount": Decimal(f"{val:.2f}"),
            "sort_key": f"2024-{i+1:02d}"
        })
    
    result = ForecastService.append_forecast(history, periods=3)
    
    # Check that we have forecast entries
    forecast_entries = [x for x in history if x.get("is_forecast")]
    assert len(forecast_entries) == 3
    
    # Check bounds existence
    for entry in forecast_entries:
        assert entry["lower_bound"] is not None
        assert entry["upper_bound"] is not None
        assert entry["upper_bound"] >= entry["amount"]
        assert entry["lower_bound"] <= entry["amount"]

    # Check that it's NOT just +/- 10% (Legacy check)
    # prediction = entry["amount"]
    # If it was fixed 10%, upper would be pred * 1.1
    # We expect it to be different
    first_forecast = forecast_entries[0]
    val = float(first_forecast["amount"])
    upper = float(first_forecast["upper_bound"])
    
    # Assert it's not exactly 10% (allowing for floating point comparison)
    fixed_margin = val * 0.1
    actual_margin = upper - val
    
    # If simple 10% logic, margin == fixed_margin. We want it to be statistical.
    # It might coincidentally be close, but unlikely to be *exactly* 1.1x if using sigma.
    assert abs(actual_margin - fixed_margin) > 0.01 or actual_margin == 0.0, "Confidence interval appears to be fixed 10% heuristc"

def test_holt_winters_seasonality():
    """Test that seasonality is captured."""
    # Perfect seasonal data
    history = []
    season = [10, 20, 30, 10, 20, 30, 10, 20, 30, 10, 20, 30] # 4 cycles of length 3? No, period is usually 12.
    # Let's make 2 years of monthly data with clear seasonality
    values = [100, 120, 140, 110, 100, 90, 80, 90, 100, 110, 130, 150] # Year 1
    values += values # Year 2
    
    for i, v in enumerate(values):
        history.append({
            "month": f"M{i}", 
            "amount": Decimal(str(v)),
            "sort_key": f"2024-{i+1:02d}"
        })
        
    result = ForecastService.append_forecast(history, periods=3)
    
    # The next 3 months should roughly follow the start of the pattern (100, 120, 140)
    forecasts = [float(x["amount"]) for x in history if x.get("is_forecast")]
    
    # HW might dampen or trend, but should be roughly similar
    assert forecasts[0] == pytest.approx(100, rel=0.2)
    assert forecasts[1] == pytest.approx(120, rel=0.2)
