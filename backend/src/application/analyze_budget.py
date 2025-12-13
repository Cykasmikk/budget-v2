from typing import Dict, Any, List
from decimal import Decimal
import structlog
from src.domain.repository import BudgetRepository
from src.domain.analysis_models import (
    BudgetAnalysisResult, TrendEntry
)
from src.application.analysis_services import (
    GapDetector, InsightGenerator, ForecastService
)

logger = structlog.get_logger()

class AnalyzeBudgetUseCase:
    """
    Use case for analyzing budget data.
    Refactored to orchestrate specialized services.
    """
    
    def __init__(self, repo: BudgetRepository):
        self.repo = repo
        
    def _compute_analysis(self, entries: list) -> BudgetAnalysisResult:
        """
        Synchronous CPU-bound logic.
        """
        # 1. Basic Stats
        total_expenses = sum((e.amount for e in entries), Decimal("0"))
        
        category_breakdown: Dict[str, Decimal] = {}
        project_breakdown: Dict[str, Decimal] = {}
        merchant_breakdown: Dict[str, Decimal] = {}
        
        for e in entries:
            category_breakdown[e.category] = category_breakdown.get(e.category, Decimal("0")) + e.amount
            project_breakdown[e.project] = project_breakdown.get(e.project, Decimal("0")) + e.amount
            merchant_breakdown[e.description] = merchant_breakdown.get(e.description, Decimal("0")) + e.amount
            
        top_merchants = dict(sorted(merchant_breakdown.items(), key=lambda item: item[1], reverse=True)[:5])

        # 2. Insights using Services
        gaps = GapDetector.detect_gaps(entries)
        flash_fill_suggestions = InsightGenerator.generate_flash_fill(entries)
        subscriptions = InsightGenerator.detect_subscriptions(entries)
        anomalies = InsightGenerator.detect_anomalies(entries)

        # 3. Trend Analysis & Forecasting
        monthly_trend_map: Dict[str, Dict] = {}
        category_history_map: Dict[str, Dict[str, Dict]] = {}
        project_history_map: Dict[str, Dict[str, Dict]] = {}

        for e in entries:
            month_key = e.date.strftime("%Y-%m")
            month_display = e.date.strftime("%b %Y")
            
            # Overall Trend
            if month_key not in monthly_trend_map:
                monthly_trend_map[month_key] = {"month": month_display, "amount": Decimal("0"), "sort_key": month_key}
            monthly_trend_map[month_key]["amount"] += e.amount
            
            # Category History
            if e.category not in category_history_map:
                category_history_map[e.category] = {}
            if month_key not in category_history_map[e.category]:
                category_history_map[e.category][month_key] = {"month": month_display, "amount": Decimal("0"), "sort_key": month_key}
            category_history_map[e.category][month_key]["amount"] += e.amount

            # Project History
            if e.project not in project_history_map:
                project_history_map[e.project] = {}
            if month_key not in project_history_map[e.project]:
                project_history_map[e.project][month_key] = {"month": month_display, "amount": Decimal("0"), "sort_key": month_key}
            project_history_map[e.project][month_key]["amount"] += e.amount

        # Convert to lists and sort
        monthly_trend_raw = sorted(monthly_trend_map.values(), key=lambda x: x["sort_key"])
        
        category_history_raw: Dict[str, List[Dict]] = {}
        for cat, month_map in category_history_map.items():
            category_history_raw[cat] = sorted(month_map.values(), key=lambda x: x["sort_key"])

        project_history_raw: Dict[str, List[Dict]] = {}
        for proj, month_map in project_history_map.items():
            project_history_raw[proj] = sorted(month_map.values(), key=lambda x: x["sort_key"])

        # 4. Filter Granular Merchants
        category_merchants_map: Dict[str, Dict[str, Decimal]] = {}
        project_merchants_map: Dict[str, Dict[str, Decimal]] = {}

        for e in entries:
            if e.category not in category_merchants_map:
                category_merchants_map[e.category] = {}
            category_merchants_map[e.category][e.description] = category_merchants_map[e.category].get(e.description, Decimal("0")) + e.amount

            if e.project not in project_merchants_map:
                project_merchants_map[e.project] = {}
            project_merchants_map[e.project][e.description] = project_merchants_map[e.project].get(e.description, Decimal("0")) + e.amount

        category_merchants = {
            cat: dict(sorted(merch_map.items(), key=lambda item: item[1], reverse=True)[:10])
            for cat, merch_map in category_merchants_map.items()
        }
        
        project_merchants = {
            proj: dict(sorted(merch_map.items(), key=lambda item: item[1], reverse=True)[:10])
            for proj, merch_map in project_merchants_map.items()
        }

        # 5. Apply Forecast
        ForecastService.append_forecast(monthly_trend_raw, periods=36)
        
        for history in category_history_raw.values():
            ForecastService.append_forecast(history, periods=36)
            
        for history in project_history_raw.values():
            ForecastService.append_forecast(history, periods=36)

        # 6. Convert to Pydantic Models for Response
        monthly_trend_models = [
            TrendEntry(
                month=x["month"],
                amount=x["amount"],
                is_forecast=x.get("is_forecast", False),
                sort_key=x["sort_key"]
            ) for x in monthly_trend_raw
        ]

        category_history_models: Dict[str, List[TrendEntry]] = {}
        for cat, raw_list in category_history_raw.items():
            category_history_models[cat] = [
                TrendEntry(
                    month=x["month"],
                    amount=x["amount"],
                    is_forecast=x.get("is_forecast", False),
                    sort_key=x["sort_key"]
                ) for x in raw_list
            ]
            
        project_history_models: Dict[str, List[TrendEntry]] = {}
        for proj, raw_list in project_history_raw.items():
            project_history_models[proj] = [
                TrendEntry(
                    month=x["month"],
                    amount=x["amount"],
                    is_forecast=x.get("is_forecast", False),
                    sort_key=x["sort_key"]
                ) for x in raw_list
            ]

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
            category_vendors=category_vendors,
            project_vendors=project_vendors
        )

    async def execute(self, entries: list = None) -> BudgetAnalysisResult:
        """
        Calculates total expenses and category breakdown.
        Executes CPU-bound logic in a thread pool to avoid blocking the event loop.
        """
        if entries is None:
            entries = await self.repo.get_all() # type: ignore
        
        import asyncio
        loop = asyncio.get_running_loop()
        
        # Run synchronous analysis in executor
        return await loop.run_in_executor(None, self._compute_analysis, entries)
