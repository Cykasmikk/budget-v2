from typing import List, Dict
from decimal import Decimal
from src.infrastructure.models import BudgetModel
import structlog
from src.domain.analysis_models import FlashFillSuggestion, SubscriptionEntry, AnomalyEntry

logger = structlog.get_logger()

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
    Acts as a lightweight 'AI' for missing data.
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
    def infer(description: str, current_category: str = None) -> str:
        """
        Infers category based on keywords in description.
        Prioritizes existing valid category if present.
        """
        # If we already have a specific category, strict keep it (unless it's generic)
        if current_category and current_category not in ["Uncategorized", "General", "Expense", "Misc"]:
            return current_category
            
        desc_lower = description.lower()
        
        for category, keywords in CategoryClassifier.KNOWLEDGE_BASE.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return category
                    
        return "Uncategorized"

class InsightGenerator:
    # ... previous code ...

    @staticmethod
    def generate_flash_fill(entries: List[BudgetModel]) -> List[FlashFillSuggestion]:
        """
        Identifies recurring uncategorized transactions and offers suggestions 
        based on the CategoryClassifier.
        """
        suggestions = []
        uncategorized_counts = {}
        
        # Count frequency of uncategorized descriptions
        for e in entries:
            if e.category in ["Uncategorized", "General", "Misc", "Expense", "Unknown"]:
                desc = e.description
                if desc not in uncategorized_counts:
                    uncategorized_counts[desc] = 0
                uncategorized_counts[desc] += 1
                
        # For frequent items, try to infer
        for desc, count in uncategorized_counts.items():
            if count >= 2: # Only suggest if it happens more than once
                inferred = CategoryClassifier.infer(desc)
                if inferred != "Uncategorized":
                    suggestions.append(FlashFillSuggestion(
                        description=desc,
                        suggested_category=inferred,
                        count=count
                    ))
        
        # Sort by impact (frequency)
        suggestions.sort(key=lambda x: x.count, reverse=True)
        return suggestions

    @staticmethod
    def detect_subscriptions(entries: List[BudgetModel]) -> List[SubscriptionEntry]:
        subscriptions = []
        desc_to_entries: Dict[str, List[BudgetModel]] = {}
        for e in entries:
            if e.description not in desc_to_entries:
                desc_to_entries[e.description] = []
            desc_to_entries[e.description].append(e)
            
        from datetime import timedelta
        
        for desc, entry_list in desc_to_entries.items():
            if len(entry_list) >= 2:
                # Sort by date
                entry_list.sort(key=lambda x: x.date)
                
                # Check for consistent amounts (heuristic)
                amounts = {e.amount for e in entry_list}
                
                # We allow slight variance or identical amounts
                if len(amounts) == 1: 
                    # It's a recurring exact amount
                    first_date = entry_list[0].date
                    last_date = entry_list[-1].date
                    
                    # Estimate frequency
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
                        
                    # Determine category (use inferrence)
                    raw_cat = entry_list[0].category
                    final_cat = CategoryClassifier.infer(desc, raw_cat)
                    
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
    def append_forecast(history: List[Dict], periods=36, alpha=0.6, beta=0.3):
        """
        Applies Holt's Linear Trend Method.
        Modifies list in-place.
        """
        if not history or len(history) < 2:
            logger.debug("Skipping forecast", history_len=len(history) if history else 0)
            return

        amounts = [float(x["amount"]) for x in history]
        
        level = amounts[0]
        trend = amounts[1] - amounts[0]
        
        for i in range(1, len(amounts)):
            val = amounts[i]
            last_level = level
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend
            
        last_date_str = history[-1].get("sort_key", "")
        try:
            year, month = map(int, last_date_str.split("-"))
        except ValueError:
            return 
            
        last_level = level
        last_trend = trend
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        for p in range(1, periods + 1):
            forecast_val = last_level + p * last_trend
            forecast_val = max(0, forecast_val)
            
            month += 1
            if month > 12:
                month = 1
                year += 1
                
            month_fmt = f"{month:02d}"
            sort_key = f"{year}-{month_fmt}"
            display_month = f"{months[month-1]} {year}"
            
            history.append({
                "month": display_month,
                "amount": Decimal(str(forecast_val)),
                "is_forecast": True,
                "sort_key": sort_key
            })
