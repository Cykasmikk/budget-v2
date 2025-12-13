from typing import List, Dict, Any
from decimal import Decimal
from src.domain.repository import BudgetRepository
from pydantic import BaseModel

class SimulationAdjustment(BaseModel):
    category: str
    percentage: float # e.g., -20.0 for 20% reduction, 10.0 for 10% increase

class SimulateBudgetUseCase:
    def __init__(self, repo: BudgetRepository):
        self.repo = repo

    async def execute(self, adjustments: List[SimulationAdjustment]) -> Dict[str, Any]:
        entries = await self.repo.get_all()
        
        # Calculate current baseline
        current_total = sum((e.amount for e in entries), Decimal("0"))
        current_category_totals = {}
        for e in entries:
            current_category_totals[e.category] = current_category_totals.get(e.category, Decimal("0")) + e.amount
            
        # Apply adjustments
        simulated_total = Decimal("0")
        simulated_category_totals = current_category_totals.copy()
        
        for adj in adjustments:
            if adj.category in simulated_category_totals:
                original_amount = simulated_category_totals[adj.category]
                # Calculate change: original * (percentage / 100)
                # If percentage is -20, change is negative.
                change = original_amount * (Decimal(str(adj.percentage)) / Decimal("100"))
                simulated_category_totals[adj.category] = original_amount + change
        
        simulated_total = sum(simulated_category_totals.values())
        
        return {
            "current_total": current_total,
            "simulated_total": simulated_total,
            "savings": current_total - simulated_total,
            "breakdown": simulated_category_totals
        }
