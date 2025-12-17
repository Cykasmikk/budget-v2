import pytest
from decimal import Decimal
from src.application.analysis_services import ForecastService

class TestForecasting:
    
    def test_ramp_up_trend(self):
        """
        Sequence: 100, 110, 120, 130, 140, 150.
        Trend is +10/period.
        Forecast should be roughly 160, 170...
        """
        # Mocking history dict structure used by service
        # Service expects: [{"amount": Decimal(...), "sort_key": "YYYY-MM"}]
        
        data = [100, 110, 120, 130, 140, 150]
        history = []
        for i, val in enumerate(data):
            history.append({
                "amount": Decimal(str(val)),
                "sort_key": f"2024-{i+1:02d}",
                "month": "Month"
            })

        ForecastService.append_forecast(history, periods=2)
        
        # Original: 6 items. Forecast: 2 items. Total: 8
        assert len(history) == 8
        
        f1 = float(history[6]["amount"])
        f2 = float(history[7]["amount"])
        
        print(f"Ramp Forecast: {f1}, {f2}")
        
        assert history[6]["is_forecast"] == True
        assert f1 > 150
        assert f1 < 170 
        assert f2 > f1

    def test_accelerating_growth(self):
        """
        Sequence: 100, 100, 100, 120, 150.
        """
        data = [100, 100, 100, 120, 150]
        history = []
        for i, val in enumerate(data):
            history.append({
                "amount": Decimal(str(val)),
                "sort_key": f"2024-{i+1:02d}",
                "month": "Month"
            })
            
        ForecastService.append_forecast(history, periods=1, alpha=0.8, beta=0.5)
        
        f1 = float(history[-1]["amount"])
        print(f"Accel Forecast: {f1}")
        assert f1 > 150
        
    def test_flat_trend(self):
        data = [100, 100, 100, 100, 100]
        history = []
        for i, val in enumerate(data):
            history.append({
                "amount": Decimal(str(val)),
                "sort_key": f"2024-{i+1:02d}",
                "month": "Month"
            })

        ForecastService.append_forecast(history, periods=1)
        f1 = float(history[-1]["amount"])
        
        assert abs(f1 - 100) < 1.0

    def test_forecast_confidence_intervals(self):
        """
        Verify that forecast entries include confidence intervals (upper/lower bounds).
        """
        data = [100, 110, 105, 115, 120] # Slight noise
        history = []
        for i, val in enumerate(data):
            history.append({
                "amount": Decimal(str(val)),
                "sort_key": f"2024-{i+1:02d}",
                "month": "Month"
            })
            
        ForecastService.append_forecast(history, periods=3)
        
        # Check only the forecast items (indexes 5, 6, 7)
        for i in range(5, 8):
            item = history[i]
            assert item["is_forecast"] is True
            assert "lower_bound" in item
            assert "upper_bound" in item
            
            amount = float(item["amount"])
            lower = float(item["lower_bound"])
            upper = float(item["upper_bound"])
            
            # Basic sanity check: Lower <= Amount <= Upper
            assert lower <= amount <= upper
            # Bounds should not be identical for noisy data
            assert upper > lower

    def test_forecast_summary_metrics(self):
        """
        Verify that append_forecast returns a comprehensive summary of the model.
        """
        # Steady growth: 100, 110, 120, 130, 140
        data = [100, 110, 120, 130, 140]
        history = []
        for i, val in enumerate(data):
            history.append({
                "amount": Decimal(str(val)),
                "sort_key": f"2024-{i+1:02d}",
                "month": "Month"
            })
            
        summary = ForecastService.append_forecast(history, periods=3)
        
        assert summary is not None
        assert summary["trend_direction"] == "Increasing ↗"
        assert float(summary["trend_component"]) > 0
        assert summary["model_accuracy"] > 90.0 # Should be high for perfect linear data
        
        # Check forecasted total (next 3 months: 150+160+170 = 480)
        # Using fuzzy match
        assert abs(float(summary["forecasted_total"]) - 480.0) < 5.0
        
        # Growth rate (approx 21.4%)
        assert 15.0 < float(summary["growth_rate"]) < 25.0
