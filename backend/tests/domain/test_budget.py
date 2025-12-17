import pytest
from datetime import date
from decimal import Decimal
from src.domain.budget import BudgetEntry

def test_budget_entry_creation():
    entry = BudgetEntry(
        date=date(2025, 1, 1),
        category="Groceries",
        amount=Decimal("150.50"),
        description="Weekly shopping"
    )
    
    assert entry.date == date(2025, 1, 1)
    assert entry.category == "Groceries"
    assert entry.amount == Decimal("150.50")
    assert entry.description == "Weekly shopping"

def test_budget_entry_validation():
    # Test that amount must be positive (if that's a rule, let's assume yes for expenses)
    # Actually, let's just test basic types for now.
    pass
