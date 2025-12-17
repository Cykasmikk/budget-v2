import pytest
from unittest.mock import MagicMock, AsyncMock
from decimal import Decimal
from datetime import date
from src.domain.budget import BudgetEntry
from src.application.analyze_budget import AnalyzeBudgetUseCase

@pytest.mark.asyncio
async def test_analyze_budget_returns_forecast_summary():
    # 1. Setup
    mock_repo = AsyncMock()
    # Steady growth data to ensure a valid forecast
    mock_entries = [
        BudgetEntry(date=date(2024, 1, 1), category="Test", amount=Decimal("100"), description="A"),
        BudgetEntry(date=date(2024, 2, 1), category="Test", amount=Decimal("110"), description="B"),
        BudgetEntry(date=date(2024, 3, 1), category="Test", amount=Decimal("120"), description="C")
    ]
    mock_repo.get_all.return_value = mock_entries
    
    use_case = AnalyzeBudgetUseCase(repo=mock_repo)
    
    # 2. Execute
    result = await use_case.execute(entries=mock_entries, settings={"forecast_horizon": 3})
    
    # 3. Verify
    assert result.forecast_summary is not None
    summary = result.forecast_summary
    
    assert summary.trend_direction == "Increasing ↗"
    # Trend is +10. Forecast: 130, 140, 150 -> Sum = 420 (approx)
    # Actually, fitted level at period 3 (Mar) is approx 120.
    # Projections:
    # 1. 120 + 10 = 130
    # 2. 120 + 20 = 140
    # 3. 120 + 30 = 150
    # Total = 420.
    assert summary.forecasted_total > 400
    
    # Growth Rate: (150 - 120)/120 = 25% (approx)
    assert summary.growth_rate > 20.0
    
    assert summary.model_accuracy > 90.0 # Perfect linear fit
    assert summary.outlier_detected is False
