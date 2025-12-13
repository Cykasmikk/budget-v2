from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Any, Optional
from decimal import Decimal

class QueryResultDTO(BaseModel):
    model_config = ConfigDict(strict=True)
    answer: str
    type: str
    data: Dict[str, Any] | List[Any] | None = None

class SimulationResultDTO(BaseModel):
    model_config = ConfigDict(strict=True)
    current_total: float
    simulated_total: float
    savings: float
    breakdown: Dict[str, float]

class DateRangeDTO(BaseModel):
    model_config = ConfigDict(strict=True)
    earliest: Optional[str] = None
    latest: Optional[str] = None

class BudgetContextDTO(BaseModel):
    model_config = ConfigDict(strict=True)
    total_expenses: float
    entry_count: int
    categories: Dict[str, float]
    projects: Dict[str, float]
    all_categories: List[str]
    all_projects: List[str]
    date_range: Optional[DateRangeDTO] = None
    average_expense: float
