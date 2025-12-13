from typing import List, Dict, Optional
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field, ConfigDict

class TrendEntry(BaseModel):
    """
    Represents a single data point in a monthly trend analysis.

    Attributes:
        month (str): The month label (e.g., "Jan 2024").
        amount (Decimal): The total aggregated amount for the month.
        is_forecast (bool): True if this data point is a predicted value, False if actual.
        sort_key (str): A sortable string representation of the month (e.g., "2024-01").
    """
    model_config = ConfigDict(strict=True)
    month: str
    amount: Decimal
    is_forecast: bool
    sort_key: str

class GapEntry(BaseModel):
    """
    Represents a detected gap in financial data availability.

    Attributes:
        start_date (date): The start date of the gap.
        end_date (date): The end date of the gap.
        days (int): The duration of the gap in days.
    """
    model_config = ConfigDict(strict=True)
    start_date: date
    end_date: date
    days: int

class FlashFillSuggestion(BaseModel):
    """
    Represents an AI-suggested category rule based on historical data.

    Attributes:
        description (str): The transaction description pattern.
        suggested_category (str): The category suggested by the analysis.
        count (int): The number of transactions supporting this suggestion.
    """
    model_config = ConfigDict(strict=True)
    description: str
    suggested_category: str
    count: int

class SubscriptionEntry(BaseModel):
    """
    Represents a detected recurring subscription payment.

    Attributes:
        description (str): The subscription name or merchant.
        amount (float): The recurring payment amount.
        frequency (str): The detected frequency (e.g., "Monthly").
        category (str): The category of the subscription.
        start_date (date): The date of the first detected payment.
        next_payment_date (date): The predicted next payment date.
        status (str): The status of the subscription (e.g., "Active").
    """
    model_config = ConfigDict(strict=True)
    description: str
    amount: float
    frequency: str
    category: str = "Uncategorized"
    start_date: date
    next_payment_date: date
    status: str = "Active" # Active, Cancelled, Expiring

class AnomalyEntry(BaseModel):
    """
    Represents a spending anomaly (outlier) detected in the data.

    Attributes:
        description (str): The transaction description.
        date (date): The date of the anomalous transaction.
        amount (float): The amount of the transaction.
        average (float): The historical average for similar transactions.
    """
    model_config = ConfigDict(strict=True)
    description: str
    date: date
    amount: float
    average: float

class BudgetAnalysisResult(BaseModel):
    """
    Comprehensive result of a budget analysis operation.
    Aggregates statistics, trends, insights, and anomalies.
    """
    model_config = ConfigDict(strict=True)
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
    
    # Upload feedback
    warnings: List[str] = []
    skipped_count: int = 0

    # Legacy/Redundant fields kept for compatibility if needed, else optional
    category_vendors: Optional[Dict[str, List[str]]] = None
    project_vendors: Optional[Dict[str, List[str]]] = None
