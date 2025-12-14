import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from decimal import Decimal
from datetime import date
from src.domain.budget import BudgetEntry
from src.application.analyze_budget import AnalyzeBudgetUseCase
from src.infrastructure.models import TenantModel

@pytest.mark.asyncio
async def test_analyze_budget_uses_forecast_horizon_setting():
    # 1. Setup Mock Repo & Data
    mock_repo = AsyncMock()
    
    # Create 3 months of historical data
    mock_entries = [
        BudgetEntry(date=date(2024, 1, 1), category="Test", amount=Decimal("100"), description="A"),
        BudgetEntry(date=date(2024, 2, 1), category="Test", amount=Decimal("110"), description="B"),
        BudgetEntry(date=date(2024, 3, 1), category="Test", amount=Decimal("120"), description="C")
    ]
    mock_repo.get_all.return_value = mock_entries
    
    # 2. Setup Mock Settings
    # We expect AnalyzeBudgetUseCase to accept settings or a horizon value
    # Let's assume we will pass it into execute() or constructor.
    # Passing to execute() is cleaner for stateless use cases.
    custom_horizon = 12
    
    use_case = AnalyzeBudgetUseCase(repo=mock_repo)
    
    # 3. Execute
    # Passing settings to execute. This signature doesn't exist yet, so this will fail or we'll need to update the call.
    result = await use_case.execute(entries=mock_entries, settings={"forecast_horizon": custom_horizon})
    
    # 4. Verify
    # Total items = 3 history + 12 forecast = 15
    # The monthly_trend should have 15 items
    assert len(result.monthly_trend) == 15
    
    # Check that the last 12 are forecasts
    forecast_items = [x for x in result.monthly_trend if x.is_forecast]
    assert len(forecast_items) == custom_horizon
