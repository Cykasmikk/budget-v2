import pytest
from src.application.symbolic.budget_solver import BudgetSolver
from decimal import Decimal

def test_budget_solver_initialization():
    """Test solver initialization."""
    solver = BudgetSolver()
    assert solver.solver is not None

def test_verify_invariants_valid():
    """Test verification of a valid budget state."""
    solver = BudgetSolver()
    
    # Simple budget: Total = 100, Expenses = [40, 60] -> Valid
    is_valid, proof = solver.verify_budget_sum(
        total=Decimal("100.00"),
        components=[Decimal("40.00"), Decimal("60.00")]
    )
    assert is_valid is True
    assert "verified" in proof.lower()

def test_verify_invariants_invalid():
    """Test verification of an invalid budget state."""
    solver = BudgetSolver()
    
    # Invalid budget: Total = 100, Expenses = [40, 50] -> Invalid (Balance = 10)
    is_valid, proof = solver.verify_budget_sum(
        total=Decimal("100.00"),
        components=[Decimal("40.00"), Decimal("50.00")]
    )
    assert is_valid is False
    assert "violation" in proof.lower() or "counterexample" in proof.lower()

def test_rule_conflict_detection():
    """Test detection of conflicting rules."""
    solver = BudgetSolver()
    
    # Conflict: Pattern "Netflix" maps to "Entertainment" AND "Software"
    conflicts = solver.detect_rule_conflicts([
        {"pattern": "Netflix", "category": "Entertainment"},
        {"pattern": "Netflix", "category": "Software"}
    ])
    assert len(conflicts) > 0
    
    # No conflict
    conflicts = solver.detect_rule_conflicts([
        {"pattern": "Netflix", "category": "Entertainment"},
        {"pattern": "Spotify", "category": "Entertainment"}
    ])
    assert len(conflicts) == 0
