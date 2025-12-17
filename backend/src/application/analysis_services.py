from typing import List, Dict, Any, Literal
from decimal import Decimal
import math
from datetime import date, timedelta, datetime
import numpy as np
import structlog
from dataclasses import dataclass
from enum import Enum
import random

from src.infrastructure.models import BudgetModel
from src.domain.analysis_models import FlashFillSuggestion, SubscriptionEntry, AnomalyEntry

logger = structlog.get_logger()

# --- Constants ---

CAPEX_KEYWORDS = [
    'hardware', 'server', 'license', 'equipment', 'purchase',
    'infrastructure', 'asset', 'capital', 'one-time', 'setup',
    'installation', 'migration', 'implementation'
]

OPEX_KEYWORDS = [
    'subscription', 'monthly', 'recurring', 'saas', 'cloud',
    'hosting', 'support', 'maintenance', 'salary', 'contractor',
    'utility', 'rent', 'service'
]

# --- Enums & Dataclasses for V2 ---

class ProjectPhase(Enum):
    PLANNING = "planning"
    RAMP_UP = "ramp_up"
    EXECUTION = "execution"
    WIND_DOWN = "wind_down"
    COMPLETE = "complete"

@dataclass
class ProjectForecast:
    project_id: str
    total_budget: float
    duration_months: int
    current_month: int
    phase: ProjectPhase

# --- Helper Functions ---

def classify_expense(
    description: str,
    amount: float,
    category: str = None,
    is_recurring: bool = None
) -> Literal['capex', 'opex']:
    """
    Classify expense as CapEx or OpEx based on heuristics.
    """
    desc_lower = description.lower()

    # 1. Check explicit flag
    if is_recurring is not None:
        return 'opex' if is_recurring else 'capex'

    # 2. Keyword matching
    capex_score = sum(1 for kw in CAPEX_KEYWORDS if kw in desc_lower)
    opex_score = sum(1 for kw in OPEX_KEYWORDS if kw in desc_lower)

    if capex_score > opex_score:
        return 'capex'
    if opex_score > capex_score:
        return 'opex'

    # 3. Category-based rules (if provided)
    capex_categories = {'Hardware', 'Equipment', 'Infrastructure', 'Licenses'}
    opex_categories = {'Software', 'Hosting/Cloud', 'Contractors', 'Subscriptions'}

    if category in capex_categories:
        return 'capex'
    if category in opex_categories:
        return 'opex'

    # 4. Amount heuristic (large one-time = likely CapEx)
    if abs(amount) > 10000: 
        return 'capex'

    return 'opex'

def s_curve_spend(t: float, total_budget: float, midpoint: float, steepness: float = 1.0) -> float:
    """
    Logistic S-curve for cumulative project spending.
    """
    return total_budget / (1 + math.exp(-steepness * (t - midpoint)))

def determine_phase(current_month: int, total_months: int) -> ProjectPhase:
    """Determine project phase based on timeline position."""
    if total_months == 0:
        return ProjectPhase.COMPLETE
        
    progress = current_month / total_months

    if progress < 0.1:
        return ProjectPhase.PLANNING
    elif progress < 0.3:
        return ProjectPhase.RAMP_UP
    elif progress < 0.8:
        return ProjectPhase.EXECUTION
    elif progress < 1.0:
        return ProjectPhase.WIND_DOWN
    else:
        return ProjectPhase.COMPLETE

def project_monthly_spend(project: ProjectForecast) -> List[Dict]:
    """
    Generate monthly spend forecast for a project.
    """
    forecasts = []
    midpoint = project.duration_months / 2

    # Forecast for remaining months
    start_forecast_month = project.current_month + 1
    
    for month in range(start_forecast_month, project.duration_months + 1):
        cumulative_current = s_curve_spend(month, project.total_budget, midpoint)
        cumulative_prev = s_curve_spend(month - 1, project.total_budget, midpoint) if month > 0 else 0

        monthly_spend = cumulative_current - cumulative_prev

        forecasts.append({
            'project_id': project.project_id,
            'month': month - project.current_month,  # Months from now (1, 2, 3...)
            'forecast': monthly_spend,
            'cumulative': cumulative_current,
            'percent_complete': (cumulative_current / project.total_budget) * 100,
            'phase': determine_phase(month, project.duration_months)
        })

    return forecasts

# --- Services ---

class GapDetector:
    @staticmethod
    def detect_gaps(entries: List[BudgetModel]) -> List[Dict]:
        """
        Detects gaps of more than 7 days between transactions.
        """
        if not entries:
            return []
            
        sorted_entries = sorted(entries, key=lambda x: x.date)
        gaps = []
        
        if len(sorted_entries) > 1:
            for i in range(len(sorted_entries) - 1):
                current_date = sorted_entries[i].date
                next_date = sorted_entries[i+1].date
                delta = (next_date - current_date).days
                
                if delta > 7:
                    gaps.append({
                        "start_date": current_date,
                        "end_date": next_date,
                        "days": delta
                    })
        return gaps

class CategoryClassifier:
    """
    Heuristic-based classifier to infer categories from transaction descriptions.
    """
    
    KNOWLEDGE_BASE = {
        "Software": ["github", "atlassian", "jira", "confluence", "slack", "zoom", "adobe", "figma", "notion", "linear", "microsoft", "jetbrains", "docker"],
        "Hosting/Cloud": ["aws", "amazon web services", "google cloud", "gcp", "azure", "digitalocean", "vercel", "netlify", "heroku", "cloudflare"],
        "Observability": ["datadog", "pagerduty", "new relic", "sentry", "grafana", "prometheus", "splunk"],
        "Security": ["okta", "auth0", "1password", "lastpass", "crowdstrike", "palo alto", "vpn"],
        "Contractors": ["upwork", "fiverr", "toptal", "consulting", "contractor", "freelance"],
        "Hardware": ["dell", "apple", "lenovo", "hp", "cdw", "equipment", "monitor", "laptop"],
        "Facilities": ["rent", "lease", "utility", "water", "electricity", "cleaning", "security", "office"],
        "Data": ["snowflake", "tableau", "looker", "fivetran", "dbt"],
        "Marketing": ["hubspot", "facebook ads", "google ads", "mailchimp", "linkedin"],
        "Sales": ["salesforce", "pipedrive", "gong"],
    }

    @staticmethod
    async def infer(description: str, current_category: str = None, predictor: Any = None, reasoner: Any = None) -> tuple[str, float]:
        """
        Infers category and confidence using Neuro-Symbolic Hybrid Reasoner if available.
        Returns: (Category, Confidence)
        """
        if current_category and current_category not in ["Uncategorized", "General", "Expense", "Misc"]:
            return current_category, 1.0
            
        desc_lower = description.lower()
        
        # 0. Hybrid Reasoner (Neuro-Symbolic) - Priority 1
        if reasoner:
            # We assume rules are handled within reasoner or passed to it. 
            # For this static method, we might pass an empty rule list or pre-baked rules if available.
            # Ideally reasoner has access to rules, but here we keep it simple.
            result = await reasoner.refine_prediction(description, rules=[]) 
            if result.confidence > 0.6: # Configurable threshold
                return result.category, result.confidence

        # 1. Deterministic Rule Matching (Legacy Symbolic)
        for category, keywords in CategoryClassifier.KNOWLEDGE_BASE.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return category, 1.0
        
        # 2. Neural Predictor (Legacy / Fallback)
        if predictor:
            try:
                pred_category, confidence = predictor.predict(description)
                if confidence > 0.5: 
                    return pred_category, confidence
            except Exception as e:
                logger.warning("predictor_inference_failed", error=str(e))
                    
        return "Uncategorized", 0.0

class InsightGenerator:
    @staticmethod
    async def generate_flash_fill(entries: List[BudgetModel], predictor: Any = None) -> List[FlashFillSuggestion]:
        suggestions = []
        uncategorized_counts = {}
        
        for e in entries:
            if e.category in ["Uncategorized", "General", "Misc", "Expense", "Unknown"]:
                desc = e.description
                if desc not in uncategorized_counts:
                    uncategorized_counts[desc] = 0
                uncategorized_counts[desc] += 1
                
        for desc, count in uncategorized_counts.items():
            if count >= 2: 
                inferred, conf = await CategoryClassifier.infer(desc, predictor=predictor)
                if inferred != "Uncategorized":
                    suggestions.append(FlashFillSuggestion(
                        description=desc,
                        suggested_category=inferred,
                        count=count
                    ))
        
        suggestions.sort(key=lambda x: x.count, reverse=True)
        return suggestions

    @staticmethod
    async def detect_subscriptions(entries: List[BudgetModel], predictor: Any = None) -> List[SubscriptionEntry]:
        subscriptions = []
        desc_to_entries: Dict[str, List[BudgetModel]] = {}
        for e in entries:
            if e.description not in desc_to_entries:
                desc_to_entries[e.description] = []
            desc_to_entries[e.description].append(e)
            
        for desc, entry_list in desc_to_entries.items():
            if len(entry_list) >= 2:
                entry_list.sort(key=lambda x: x.date)
                amounts = {e.amount for e in entry_list}
                
                if len(amounts) == 1: 
                    first_date = entry_list[0].date
                    last_date = entry_list[-1].date
                    
                    days_diff = (entry_list[1].date - entry_list[0].date).days
                    freq = "Monthly"
                    next_date = last_date + timedelta(days=30)
                    
                    if 25 <= days_diff <= 35:
                        freq = "Monthly"
                        next_date = last_date + timedelta(days=30)
                    elif 360 <= days_diff <= 370:
                        freq = "Annual"
                        next_date = last_date + timedelta(days=365)
                    elif days_diff < 10:
                        freq = "Weekly"
                        next_date = last_date + timedelta(days=7)
                        
                    raw_cat = entry_list[0].category
                    final_cat, _ = await CategoryClassifier.infer(desc, raw_cat, predictor=predictor)
                    
                    subscriptions.append(SubscriptionEntry(
                        description=desc,
                        amount=float(list(amounts)[0]),
                        frequency=freq,
                        category=final_cat,
                        start_date=first_date,
                        next_payment_date=next_date,
                        status="Active"
                    ))
        return subscriptions

    @staticmethod
    def detect_anomalies(entries: List[BudgetModel]) -> List[AnomalyEntry]:
        anomalies = []
        desc_to_entries: Dict[str, List[BudgetModel]] = {}
        for e in entries:
            if e.description not in desc_to_entries:
                desc_to_entries[e.description] = []
            desc_to_entries[e.description].append(e)
            
        for desc, entry_list in desc_to_entries.items():
            if len(entry_list) >= 3:
                amounts = [float(e.amount) for e in entry_list]
                avg_amount = sum(amounts) / len(amounts)
                for e in entry_list:
                    if float(e.amount) > avg_amount * 2:
                        anomalies.append(AnomalyEntry(
                            description=desc,
                            date=e.date,
                            amount=float(e.amount),
                            average=avg_amount
                        ))
        return anomalies



class ForecastService:
    @staticmethod
    def append_forecast(history: List[Dict], periods=6, alpha=0.6, beta=0.3) -> Dict[str, Any]:
        """
        Applies Forecasting. Tries Holt-Winters first, falls back to Holt Linear.
        Modifies list in-place.
        Returns a summary dictionary of the forecast model.
        """
        # Clamp forecast horizon to reasonable limit (60 months)
        periods = min(max(periods, 1), 60)

        empty_summary = {
            "trend_direction": "Insufficient Data",
            "forecasted_total": Decimal("0.00"),
            "growth_rate": Decimal("0.00"),
            "confidence_interval_width": Decimal("0.00"),
            "seasonality_index": Decimal("0.00"),
            "trend_component": Decimal("0.00"),
            "level_component": Decimal("0.00"),
            "outlier_detected": False,
            "model_accuracy": Decimal("0.00")
        }

        if not history or len(history) < 2:
            return empty_summary

        # Try Conformal Holt-Winters First
        # Note: ConformalForecaster is defined below, but available at runtime.
        try:
            forecaster = ConformalForecaster(alpha=0.1) # 90% Confidence
            hw_forecasts = forecaster.forecast(history, periods=periods)
        except NameError:
            # Fallback if ConformalForecaster is not yet bound (rare/cyclic)
            hw_forecasts = ForecastService.holt_winters_forecast(history, periods=periods)
        
        if hw_forecasts:
            # Integrate HW Results
            last_date_str = history[-1].get("sort_key", "")
            try:
                year, month = map(int, last_date_str.split("-"))
            except ValueError:
                return empty_summary

            months_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            forecast_sum = 0
            
            for item in hw_forecasts:
                forecast_val = item['forecast']
                forecast_sum += forecast_val
                
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                
                month_fmt = f"{month:02d}"
                sort_key = f"{year}-{month_fmt}"
                display_month = f"{months_names[month-1]} {year}"
                
                history.append({
                    "month": display_month,
                    "amount": Decimal(f"{forecast_val:.2f}"),
                    "lower_bound": Decimal(f"{item.get('lower_bound', forecast_val * 0.9):.2f}"),
                    "upper_bound": Decimal(f"{item.get('upper_bound', forecast_val * 1.1):.2f}"),
                    "is_forecast": True,
                    "sort_key": sort_key
                })
            
            # Calculate avg confidence width for summary
            avg_width = Decimal("0.00")
            if hw_forecasts:
                total_width = sum((item.get('upper_bound', 0) - item.get('lower_bound', 0)) for item in hw_forecasts)
                avg_width = Decimal(f"{total_width / len(hw_forecasts):.2f}")

            # Simple Summary for HW
            return {
                "trend_direction": "Seasonal/Complex",
                "forecasted_total": Decimal(f"{forecast_sum:.2f}"),
                "growth_rate": Decimal("0.00"), # Todo: calc
                "model_accuracy": Decimal("85.00"), # Placeholder/Estimated
                "confidence_interval_width": avg_width, 
                "seasonality_index": Decimal("1.00"), # Avg seasonality
                "trend_component": Decimal("0.00"),
                "level_component": Decimal("0.00"),
                "outlier_detected": False
            }

        # Fallback to Holt Linear (Legacy)
        amounts = [float(x["amount"]) for x in history]
        
        # Initialization
        level = amounts[0]
        trend = amounts[1] - amounts[0]
        
        fitted_values = [level]
        
        # Smoothing Loop
        for i in range(1, len(amounts)):
            val = amounts[i]
            last_level = level
            last_trend = trend
            
            fitted_values.append(last_level + last_trend)
            
            level = alpha * val + (1 - alpha) * (last_level + last_trend)
            trend = beta * (level - last_level) + (1 - beta) * last_trend
            
        residuals = [amounts[i] - fitted_values[i] for i in range(len(amounts))]
        sum_sq_error = sum(r**2 for r in residuals)
        sigma = math.sqrt(sum_sq_error / len(amounts)) if len(amounts) > 0 else 0
        
        last_date_str = history[-1].get("sort_key", "")
        try:
            year, month = map(int, last_date_str.split("-"))
        except ValueError:
            return empty_summary
            
        last_level = level
        last_trend = trend
        
        months_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        forecast_sum = 0
        
        for p in range(1, periods + 1):
            forecast_val = last_level + p * last_trend
            margin = 1.96 * sigma * math.sqrt(p)
            
            upper = forecast_val + margin
            lower = max(0, forecast_val - margin)
            forecast_val = max(0, forecast_val)
            
            forecast_sum += forecast_val
            
            month += 1
            if month > 12:
                month = 1
                year += 1
                
            month_fmt = f"{month:02d}"
            sort_key = f"{year}-{month_fmt}"
            display_month = f"{months_names[month-1]} {year}"
            
            history.append({
                "month": display_month,
                "amount": Decimal(f"{forecast_val:.2f}"),
                "lower_bound": Decimal(f"{lower:.2f}"),
                "upper_bound": Decimal(f"{upper:.2f}"),
                "is_forecast": True,
                "sort_key": sort_key
            })

        return {
            "trend_direction": "Stable",
            "forecasted_total": Decimal(f"{forecast_sum:.2f}"),
            "growth_rate": Decimal("0.00"),
            "model_accuracy": Decimal("0.00"),
            "confidence_interval_width": Decimal("0.00"),
            "seasonality_index": Decimal("0.00"),
            "trend_component": Decimal(f"{last_trend:.2f}"),
            "level_component": Decimal(f"{last_level:.2f}"),
            "outlier_detected": False
        }

    @staticmethod
    def holt_winters_forecast(
        history: List[Dict], 
        periods=6, 
        alpha=0.6, 
        beta=0.3, 
        gamma=0.3, 
        season_length=12
    ) -> List[Dict]:
        """
        Triple exponential smoothing with multiplicative seasonality.
        Returns ONLY the forecast points (doesn't modify history in-place).
        """
        if not history:
            return []
            
        values = [float(x.get("amount", 0)) for x in history]
        n = len(values)
        
        # Fallback if insufficient data
        if n < season_length + 1:
            # Use basic Holt logic from append_forecast, or just simple projection
            # For this simplified implementation, we'll return an empty list or call legacy?
            # Let's return a simple linear forecast
            if n < 2: return []
            level = values[-1]
            trend = (values[-1] - values[0]) / n
            forecasts = []
            for k in range(1, periods + 1):
                 val = max(0, level + k * trend)
                 # Naive bounds for fallback
                 forecasts.append({
                     'period': k, 
                     'forecast': val, 
                     'seasonal_factor': 1.0,
                     'lower_bound': max(0, val * 0.9),
                     'upper_bound': val * 1.1
                 })
            return forecasts

        # Initialize seasonal indices
        first_season_avg = np.mean(values[:season_length])
        season = [values[i] / first_season_avg if first_season_avg > 0 else 1.0 for i in range(season_length)]

        # Initialize level and trend
        level = first_season_avg
        trend = (np.mean(values[season_length:2*season_length]) - 
                 np.mean(values[:season_length])) / season_length

        # Smoothing
        residuals = []
        for t in range(season_length, n):
            val = values[t]
            last_level, last_trend = level, trend
            
            season_idx = t % season_length
            s_factor = season[season_idx] if season[season_idx] > 0 else 1.0
            
            # Prediction for current step (one-step ahead)
            # Note: Seasonality for prediction uses the value from the previous cycle
            pred = (last_level + last_trend) * s_factor
            residuals.append(val - pred)
            
            level = alpha * (val / s_factor) + (1 - alpha) * (last_level + last_trend)
            trend = beta * (level - last_level) + (1 - beta) * last_trend
            season[season_idx] = gamma * (val / level) + (1 - gamma) * season[season_idx]

        # Calculate Sigma (Standard Deviation of Residuals)
        sigma = 0.0
        if residuals:
            sigma = math.sqrt(sum(r**2 for r in residuals) / len(residuals))
        
        # Avoid zero sigma for flat lines to prevent collapse
        if sigma < 0.01: 
            sigma = max(0.1, np.mean(values) * 0.05) if values else 1.0

        forecasts = []
        for k in range(1, periods + 1):
            season_idx = (n + k - 1) % season_length
            point_forecast = (level + k * trend) * season[season_idx]
            
            # Prediction Interval (approximate for HW)
            # standard error increases with horizon
            # PI = y_hat +/- 1.96 * sigma * sqrt(k) (Simplified for state space)
            margin = 1.96 * sigma * math.sqrt(k)
            
            forecasts.append({
                'period': k,
                'forecast': max(0, point_forecast),
                'seasonal_factor': season[season_idx],
                'lower_bound': max(0, point_forecast - margin),
                'upper_bound': point_forecast + margin
            })
            
        return forecasts

    @staticmethod
    def capex_forecast(planned_purchases: List[Dict], timing_uncertainty: float = 0.2) -> List[Dict]:
        """
        Monte Carlo simulation for CapEx.
        """
        simulations = 1000
        monthly_forecasts = {}

        for _ in range(simulations):
            for purchase in planned_purchases:
                # expected_month is relative (1 = next month)
                expected_month = purchase.get('expected_month', 1)
                amount = float(purchase.get('amount', 0))
                
                # Simulate timing slip
                slip_months = max(-1, random.gauss(0.5, timing_uncertainty * 3))
                actual_month = int(expected_month + slip_months)
                
                if actual_month < 1: actual_month = 1 # Can't happen in past relative to now

                if actual_month not in monthly_forecasts:
                    monthly_forecasts[actual_month] = []
                monthly_forecasts[actual_month].append(amount)

        results = []
        for month, amounts in sorted(monthly_forecasts.items()):
            amounts_np = np.array(amounts)
            results.append({
                'month': month,
                'expected': float(np.mean(amounts_np)),
                'p10': float(np.percentile(amounts_np, 10)),
                'p50': float(np.percentile(amounts_np, 50)),
                'p90': float(np.percentile(amounts_np, 90)),
                'type': 'capex',
                'confidence': 0.7
            })

        return results

class ConformalForecaster:
    """
    Implements Split Conformal Prediction for Time Series Forecasting.
    Uses a hold-out calibration set to compute empirical non-conformity scores (residuals)
    and produces rigorously calibrated prediction intervals.
    """
    
    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha

    def forecast(self, history: List[Dict[str, Any]], periods: int = 6) -> List[Dict[str, Any]]:
        if not history or len(history) < 12:
            return ForecastService.holt_winters_forecast(history, periods=periods)

        # 1. Split Data (Training vs Calibration)
        n = len(history)
        cal_size = max(4, int(n * 0.2))
        
        if n - cal_size < 4:
             return ForecastService.holt_winters_forecast(history, periods=periods)

        train_history = history[:-cal_size]
        calibration_truth = history[-cal_size:]
        
        # 2. Predict on Calibration Set
        cal_predictions = ForecastService.holt_winters_forecast(train_history, periods=cal_size)
        
        # 3. Compute Non-Conformity Scores (Absolute Residuals)
        scores = []
        for i, truth_entry in enumerate(calibration_truth):
            truth_val = float(truth_entry.get("amount", 0))
            if i < len(cal_predictions):
                pred_val = cal_predictions[i]['forecast']
                scores.append(abs(truth_val - pred_val))
        
        if not scores:
             return ForecastService.holt_winters_forecast(history, periods=periods)

        # 4. Compute Q-hat (Empirical Quantile with Finite Sample Correction)
        n_cal = len(scores)
        q_level = min(1.0, (1 - self.alpha) * (1 + 1.0 / n_cal))
        # fallback if numpy complains about q > 1 (though min(1.0) handles it)
        try:
            q_hat = np.quantile(scores, q_level)
        except:
             q_hat = np.quantile(scores, 0.95)

        # 5. Predict Future (Refit on full history)
        final_forecasts = ForecastService.holt_winters_forecast(history, periods=periods)
        
        # 6. Apply Calibrated Intervals
        for item in final_forecasts:
            y_hat = item['forecast']
            item['lower_bound'] = max(0, y_hat - q_hat)
            item['upper_bound'] = y_hat + q_hat
            item['conformal_q'] = float(q_hat)
            
        return final_forecasts