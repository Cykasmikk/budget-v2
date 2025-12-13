from typing import List, Dict, Optional
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field

class TrendEntry(BaseModel):
    month: str
    amount: Decimal
    is_forecast: bool
    sort_key: str

class GapEntry(BaseModel):
    start_date: date
    end_date: date
    days: int

class FlashFillSuggestion(BaseModel):
    description: str
    suggested_category: str
    count: int

class SubscriptionEntry(BaseModel):
    description: str
    amount: float
    frequency: str
    category: str = "Uncategorized"
    start_date: date
    next_payment_date: date
    status: str = "Active" # Active, Cancelled, Expiring

class AnomalyEntry(BaseModel):
    description: str
    date: date
    amount: float
    average: float

class BudgetAnalysisResult(BaseModel):
    total_expenses: Decimal
    category_breakdown: Dict[str, Decimal]
    project_breakdown: Dict[str, Decimal]
    top_merchants: Dict[str, Decimal]
    
    monthly_trend: List[TrendEntry]
    category_history: Dict[str, List[TrendEntry]]
    project_history: Dict[str, List[TrendEntry]]
    
    category_merchants: Dict[str, Dict[str, Decimal]]
    project_merchants: Dict[str, Dict[str, Decimal]]
    
    gaps: List[GapEntry]
    flash_fill: List[FlashFillSuggestion]
    subscriptions: List[SubscriptionEntry]
    anomalies: List[AnomalyEntry]

    # Legacy/Redundant fields kept for compatibility if needed, else optional
    category_vendors: Optional[Dict[str, List[str]]] = None
    project_vendors: Optional[Dict[str, List[str]]] = None
