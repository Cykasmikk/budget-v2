from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import date, timedelta
import pandas as pd
from src.domain.repository import BudgetRepository
from src.domain.budget import BudgetEntry
from src.domain.analysis_models import (
    BudgetAnalysisResult, 
    TrendEntry, 
    GapEntry, 
    FlashFillSuggestion, 
    SubscriptionEntry, 
    AnomalyEntry,
    ForecastSummary,
    TimelineItem
)
import structlog
from src.application.analysis_services import GapDetector, InsightGenerator, ForecastService
from datetime import timedelta
import uuid

logger = structlog.get_logger()

class AnalyzeBudgetUseCase:
    """
    Use case for analyzing budget data to generate insights, trends, and statistics.
    Orchestrates various specialized services (GapDetector, InsightGenerator, ForecastService)
    to produce a comprehensive `BudgetAnalysisResult`.
    """
    
    def __init__(self, repo: BudgetRepository):
        self.repo = repo
        
    def _compute_analysis(self, entries: list, settings: Dict[str, Any] = None) -> BudgetAnalysisResult:
        """
        Performs the heavy CPU-bound analysis logic synchronously.
        This method is intended to be run in a separate thread to avoid blocking the event loop.

        Args:
            entries (list): A list of budget entries (models) to analyze.
            settings (dict): Tenant settings containing 'forecast_horizon'.

        Returns:
            BudgetAnalysisResult: The populated analysis result object containing all insights.
        """
        settings = settings or {}
        forecast_horizon = settings.get("forecast_horizon", 6)

        # 0. Pre-processing: Filter for Expenses vs Income
        # We assume the user wants to track "Spending".
        # We exclude typically non-expense categories from the "Total" and "Trend" to avoid 
        # payments (positive) cancelling out expenses (negative).
        exclude_categories = {"Payment", "Transfer", "Income", "Credit Card Payment", "Opening Balance"}
        
        expense_entries = [e for e in entries if e.category not in exclude_categories]

        # 1. Basic Stats (Total Expenses is magnitude of spending)
        total_expenses = sum((abs(e.amount) for e in expense_entries), Decimal("0"))
        
        category_breakdown: Dict[str, Decimal] = {}
        project_breakdown: Dict[str, Decimal] = {}
        merchant_breakdown: Dict[str, Decimal] = {}
        
        # For breakdowns, we use ALL entries but take absolute value to show magnitude of activity
        # (Or should we filter? Usually filtering is safer for "Budget" view)
        for e in expense_entries:
            amt = abs(e.amount)
            category_breakdown[e.category] = category_breakdown.get(e.category, Decimal("0")) + amt
            project_breakdown[e.project] = project_breakdown.get(e.project, Decimal("0")) + amt
            merchant_breakdown[e.description] = merchant_breakdown.get(e.description, Decimal("0")) + amt
            
        top_merchants = dict(sorted(merchant_breakdown.items(), key=lambda item: item[1], reverse=True)[:5])

        # 2. Insights using Services (Use full list for context, or filtered? Full is better for gaps/subscriptions)
        gaps = GapDetector.detect_gaps(entries)
        flash_fill_suggestions = InsightGenerator.generate_flash_fill(entries)
        subscriptions = InsightGenerator.detect_subscriptions(entries)
        anomalies = InsightGenerator.detect_anomalies(entries)

        # 3. Trend Analysis & Forecasting (Use Expense Entries only)
        monthly_trend_map: Dict[str, Dict] = {}
        category_history_map: Dict[str, Dict[str, Dict]] = {}
        project_history_map: Dict[str, Dict[str, Dict]] = {}

        for e in expense_entries:
            month_key = e.date.strftime("%Y-%m")
            month_display = e.date.strftime("%b %Y")
            amt = abs(e.amount)
            
            # Overall Trend
            if month_key not in monthly_trend_map:
                monthly_trend_map[month_key] = {"month": month_display, "amount": Decimal("0"), "sort_key": month_key}
            monthly_trend_map[month_key]["amount"] += amt
            
            # Category History
            if e.category not in category_history_map:
                category_history_map[e.category] = {}
            if month_key not in category_history_map[e.category]:
                category_history_map[e.category][month_key] = {"month": month_display, "amount": Decimal("0"), "sort_key": month_key}
            category_history_map[e.category][month_key]["amount"] += amt

            # Project History
            if e.project not in project_history_map:
                project_history_map[e.project] = {}
            if month_key not in project_history_map[e.project]:
                project_history_map[e.project][month_key] = {"month": month_display, "amount": Decimal("0"), "sort_key": month_key}
            project_history_map[e.project][month_key]["amount"] += amt

        # Convert to lists and sort
        monthly_trend_raw = sorted(monthly_trend_map.values(), key=lambda x: x["sort_key"])
        
        logger.debug("forecast_input_data_debug", 
                     count=len(monthly_trend_raw), 
                     sample_amounts=[float(x["amount"]) for x in monthly_trend_raw[:5]],
                     all_amounts=[float(x["amount"]) for x in monthly_trend_raw])
        
        category_history_raw: Dict[str, List[Dict]] = {}
        for cat, month_map in category_history_map.items():
            category_history_raw[cat] = sorted(month_map.values(), key=lambda x: x["sort_key"])

        project_history_raw: Dict[str, List[Dict]] = {}
        for proj, month_map in project_history_map.items():
            project_history_raw[proj] = sorted(month_map.values(), key=lambda x: x["sort_key"])

        # 4. Filter Granular Merchants (Use Expense Entries)
        category_merchants_map: Dict[str, Dict[str, Decimal]] = {}
        project_merchants_map: Dict[str, Dict[str, Decimal]] = {}

        for e in expense_entries:
            amt = abs(e.amount)
            if e.category not in category_merchants_map:
                category_merchants_map[e.category] = {}
            category_merchants_map[e.category][e.description] = category_merchants_map[e.category].get(e.description, Decimal("0")) + amt

            if e.project not in project_merchants_map:
                project_merchants_map[e.project] = {}
            project_merchants_map[e.project][e.description] = project_merchants_map[e.project].get(e.description, Decimal("0")) + amt

        category_merchants = {
            cat: dict(sorted(merch_map.items(), key=lambda item: item[1], reverse=True)[:10])
            for cat, merch_map in category_merchants_map.items()
        }
        
        project_merchants = {
            proj: dict(sorted(merch_map.items(), key=lambda item: item[1], reverse=True)[:10])
            for proj, merch_map in project_merchants_map.items()
        }

        # 5. Apply Forecast
        forecast_metrics_dict = ForecastService.append_forecast(monthly_trend_raw, periods=forecast_horizon)
        forecast_summary = ForecastSummary(**forecast_metrics_dict)
        
        for history in category_history_raw.values():
            ForecastService.append_forecast(history, periods=forecast_horizon)
            
        for history in project_history_raw.values():
            ForecastService.append_forecast(history, periods=forecast_horizon)

        # 6. Convert to Pydantic Models for Response
        monthly_trend_models = [
            TrendEntry(
                month=x["month"],
                amount=x["amount"],
                is_forecast=x.get("is_forecast", False),
                sort_key=x["sort_key"],
                lower_bound=x.get("lower_bound"),
                upper_bound=x.get("upper_bound")
            ) for x in monthly_trend_raw
        ]

        category_history_models: Dict[str, List[TrendEntry]] = {}
        for cat, raw_list in category_history_raw.items():
            category_history_models[cat] = [
                TrendEntry(
                    month=x["month"],
                    amount=x["amount"],
                    is_forecast=x.get("is_forecast", False),
                    sort_key=x["sort_key"],
                    lower_bound=x.get("lower_bound"),
                    upper_bound=x.get("upper_bound")
                ) for x in raw_list
            ]
            
        project_history_models: Dict[str, List[TrendEntry]] = {}
        for proj, raw_list in project_history_raw.items():
            project_history_models[proj] = [
                TrendEntry(
                    month=x["month"],
                    amount=x["amount"],
                    is_forecast=x.get("is_forecast", False),
                    sort_key=x["sort_key"],
                    lower_bound=x.get("lower_bound"),
                    upper_bound=x.get("upper_bound")
                ) for x in raw_list
            ]

        # 7. Generate Timeline Items
        timeline_items: List[TimelineItem] = []
        
        # A. Map Subscriptions to Timeline
        for sub in subscriptions:
            # Estimate end date based on frequency (default to 1 year for visualization if ongoing)
            start = sub.start_date
            # Visual duration: if monthly, show 1 month block repeating? 
            # For Gantt, usually we want "Contract Duration". 
            # If it's a subscription, let's show a 12-month projected block from start or current date.
            
            # Use next_payment_date as a "renewal" marker
            
            item = TimelineItem(
                id=str(uuid.uuid4()),
                label=f"{sub.description} ({sub.frequency})",
                start_date=sub.start_date,
                end_date=sub.next_payment_date if sub.next_payment_date > sub.start_date else sub.start_date + timedelta(days=30),
                type="subscription",
                amount=sub.amount,
                color="#3b82f6" # Blue
            )
            timeline_items.append(item)

        # B. Detect Implicit Contracts (e.g. "Annual", "Renewal")
        for e in expense_entries:
            desc_lower = e.description.lower()
            if any(k in desc_lower for k in ["annual", "renewal", "yearly", "lease", "contract", "license"]):
                # Assume 1 year duration
                start = e.date
                end = start + timedelta(days=365)
                
                # Check duplication with subscriptions (simple check)
                if not any(t.label.startswith(e.description) for t in timeline_items):
                    item = TimelineItem(
                        id=str(uuid.uuid4()),
                        label=e.description,
                        start_date=start,
                        end_date=end,
                        type="contract",
                        amount=float(e.amount),
                        color="#10b981" # Green
                    )
                    timeline_items.append(item)
            
            # C. Detect Hardware EOL (Mock logic for demo: "MacBook", "Laptop", "Server")
            if any(k in desc_lower for k in ["macbook", "laptop", "server", "dell", "lenovo", "hp ", "apple"]):
                 # Assume 3 year lifecycle
                start = e.date
                end = start + timedelta(days=365 * 3)
                
                # Avoid duplicates if we already caught it as a contract (e.g. "Dell Lease")
                if not any(t.label == f"{e.description} (Lifecycle)" for t in timeline_items):
                     item = TimelineItem(
                        id=str(uuid.uuid4()),
                        label=f"{e.description} (Lifecycle)",
                        start_date=start,
                        end_date=end,
                        type="hardware",
                        amount=float(e.amount),
                        color="#f59e0b" # Amber
                    )
                     timeline_items.append(item)


        # Legacy redundant fields
        category_vendors = {k: list(v.keys()) for k, v in category_merchants.items()}
        project_vendors = {k: list(v.keys()) for k, v in project_merchants.items()}

        return BudgetAnalysisResult(
            total_expenses=total_expenses,
            category_breakdown=category_breakdown,
            project_breakdown=project_breakdown,
            top_merchants=top_merchants,
            monthly_trend=monthly_trend_models,
            category_history=category_history_models,
            project_history=project_history_models,
            category_merchants=category_merchants,
            project_merchants=project_merchants,
            gaps=gaps, # Validated as compatible by Pydantic
            flash_fill=flash_fill_suggestions,
            subscriptions=subscriptions,
            anomalies=anomalies,
            timeline=timeline_items,
            category_vendors=category_vendors,
            project_vendors=project_vendors,
            forecast_summary=forecast_summary
        )

    async def execute(self, entries: list = None, settings: Dict[str, Any] = None) -> BudgetAnalysisResult:
        """
        Executes the analysis workflow.
        
        Fetches data from the repository (if not provided) and runs the computation
        in a thread pool to ensure non-blocking execution.

        Args:
            entries (list, optional): Pre-fetched entries to analyze. Defaults to None (fetches all).
            settings (dict, optional): Tenant settings.

        Returns:
            BudgetAnalysisResult: The complete analysis result.
        """
        if entries is None:
            entries = await self.repo.get_all() # type: ignore
        
        import asyncio
        loop = asyncio.get_running_loop()
        
        # Run synchronous analysis in executor
        return await loop.run_in_executor(None, self._compute_analysis, entries, settings)
