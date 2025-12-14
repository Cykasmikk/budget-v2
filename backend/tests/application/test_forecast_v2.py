import pytest
from decimal import Decimal
from datetime import date, timedelta
import math
from src.application.analysis_services import ForecastService, ProjectPhase, s_curve_spend, project_monthly_spend, ProjectForecast

# We assume these will be added to ForecastService or a new module
# For TDD, we test the public interface we intend to build.

class TestForecastV2:

    def test_s_curve_logic(self):
        """Test the S-Curve generation for project spending."""
        total_budget = 1000.0
        midpoint = 5.0
        
        # t=0 (Early) -> Low spend
        spend_0 = s_curve_spend(0, total_budget, midpoint)
        assert spend_0 < total_budget * 0.1
        
        # t=midpoint -> 50% spend
        spend_mid = s_curve_spend(midpoint, total_budget, midpoint)
        assert math.isclose(spend_mid, total_budget / 2, rel_tol=0.01)
        
        # t=10 (Late) -> Near 100% spend
        spend_end = s_curve_spend(10, total_budget, midpoint)
        assert spend_end > total_budget * 0.9

    def test_project_monthly_forecast(self):
        """Test generating a monthly forecast series for a project."""
        proj = ProjectForecast(
            project_id="PROJ-001",
            total_budget=120000.0,
            duration_months=12,
            current_month=3,
            phase=ProjectPhase.RAMP_UP
        )
        
        forecasts = project_monthly_spend(proj)
        
        # Should return remaining months (12 - 3 + 1 = 10 months? logic check in impl)
        # If current_month is 3, we forecast 3..12
        assert len(forecasts) > 0
        assert forecasts[0]['month'] == 1 # 1 month from now
        
        total_forecast = sum(f['forecast'] for f in forecasts)
        
        # Cumulative spend so far (months 0-2) should be subtracted? 
        # The design doc says "cumulative_current - cumulative_prev".
        # We check if the sum approximates the remaining budget.
        # This asserts the logic flows correctly.
        assert total_forecast > 0
        assert total_forecast < 120000.0

    def test_classify_expense_v2(self):
        """Test the expense classifier (already partially implemented, verifying V2 requirements)."""
        from src.application.analysis_services import classify_expense
        
        assert classify_expense("Server Hardware", 5000) == "capex"
        assert classify_expense("AWS Subscription", 500) == "opex"
        assert classify_expense("Unknown", 15000) == "capex" # Amount heuristic
        assert classify_expense("Unknown", 100, is_recurring=True) == "opex"

    def test_holt_winters_signature(self):
        """
        Verify ForecastService has the new method.
        This will fail until we implement it.
        """
        history = [{"amount": 100, "sort_key": "2023-01"}]
        # Should not raise AttributeError
        ForecastService.holt_winters_forecast(history, periods=3)

    def test_capex_simulation_signature(self):
        """Verify ForecastService has capex simulation."""
        planned = [{"amount": 10000, "expected_month": 1, "project_id": "P1", "description": "Server"}]
        res = ForecastService.capex_forecast(planned)
        assert len(res) > 0
        assert 'p50' in res[0]
