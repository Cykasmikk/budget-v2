import pytest
from unittest.mock import AsyncMock
from src.domain.budget import BudgetEntry
from src.application.analyze_budget import AnalyzeBudgetUseCase
from datetime import date
from decimal import Decimal

@pytest.mark.asyncio
async def test_analyze_budget_use_case():
    # Mock dependencies
    mock_repo = AsyncMock()
    
    # Setup mock data
    mock_entries = [
        BudgetEntry(date=date(2025, 1, 1), category="Food", amount=Decimal("10.0"), description="Lunch"),
        BudgetEntry(date=date(2025, 1, 2), category="Food", amount=Decimal("20.0"), description="Dinner"),
        BudgetEntry(date=date(2025, 1, 2), category="Transport", amount=Decimal("5.0"), description="Bus")
    ]
    mock_repo.get_all.return_value = mock_entries
    
    # Mock Rule Repo
    mock_rule_repo = AsyncMock()
    mock_rule_repo.get_all.return_value = [] # No rules for simple test

    # Initialize Use Case
    use_case = AnalyzeBudgetUseCase(repo=mock_repo, rule_repo=mock_rule_repo)
    
    # Execute
    result = await use_case.execute()
    
    # Verify
    mock_repo.get_all.assert_called_once()
    assert result.total_expenses == Decimal("35.0")
    assert result.category_breakdown == {
        "Food": Decimal("30.0"),
        "Transport": Decimal("5.0")
    }
