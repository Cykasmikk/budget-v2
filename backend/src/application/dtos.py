from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Any, Optional
from decimal import Decimal

class QueryResultDTO(BaseModel):
    model_config = ConfigDict(strict=True)
    answer: str
    type: str
    data: Dict[str, Any] | List[Any] | None = None

class DateRangeDTO(BaseModel):
    model_config = ConfigDict(strict=True)
    earliest: Optional[str] = None
    latest: Optional[str] = None

class TransactionDTO(BaseModel):
    """Individual transaction for context"""
    model_config = ConfigDict(strict=True)
    date: str
    amount: float
    description: str
    category: str
    project: Optional[str] = None
    confidence_score: float = 1.0
    is_rule_match: bool = False
    type: str = "unknown"

class BudgetContextDTO(BaseModel):
    model_config = ConfigDict(strict=True)
    total_expenses: float
    entry_count: int
    categories: Dict[str, float]
    projects: Dict[str, float]
    all_categories: List[str]
    all_projects: List[str]
    all_merchants: List[str] = []
    monthly_summary: Dict[str, float] = {}
    date_range: Optional[DateRangeDTO] = None
    average_expense: float
    # Enhanced context - limited to manage token usage
    recent_transactions: List[TransactionDTO] = []  # Last 10 transactions
    large_transactions: List[TransactionDTO] = []  # Transactions > $500 (max 10)
    top_merchants: Dict[str, float] = {}  # Top 10 merchants by total spending
