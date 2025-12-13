from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class BudgetEntry(BaseModel):
    """
    Domain entity representing a single budget entry (expense or income).
    """
    model_config = ConfigDict(strict=True)
    
    date: date
    category: str
    amount: Decimal
    description: str
    project: str = "General"
