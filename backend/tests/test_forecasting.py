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
