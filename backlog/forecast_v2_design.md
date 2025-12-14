# Forecast V2 Design Document

**Date:** 2025-12-14
**Status:** Partially Implemented (Components Ready, Integration Pending)
**Priority:** Enhancement
**Complexity:** Medium-High (2-3 weeks engineering effort)

---

## Executive Summary

The current forecasting implementation uses Holt's Linear Trend Method, which works well for short-term OpEx predictions but fails for project-based budgets with mixed CapEx/OpEx spending patterns. This document proposes a hybrid forecasting architecture that separates expense types and applies appropriate models to each.

**Implementation Status (Dec 14, 2025):** 
*   ✅ **Expense Classification:** Logic implemented in `analysis_services.py` but **NOT** integrated into the main analysis pipeline.
*   ✅ **Forecasting Algorithms:** Holt-Winters, Monte Carlo (CapEx), and S-Curve (Projects) logic exists in `analysis_services.py`.
*   ❌ **Integration:** `AnalyzeBudgetUseCase` still performs a monolithic forecast on aggregated data. It does **not** separate OpEx/CapEx, nor does it use the S-Curve for projects or Monte Carlo for CapEx. The advanced models are currently "dead code" or only partially used (Holt-Winters is used on the total).

---

## Problem Statement

### Current Limitations

| Issue | Impact |
|-------|--------|
| Single model for all expenses | CapEx spikes distort trend predictions |
| No project lifecycle awareness | Can't predict project ramp-up/wind-down |
| No seasonality handling | Misses Q4 budget cycles, fiscal year patterns |
| Time-series only approach | CapEx is event-driven, not time-driven |

### Data Characteristics

- **Projects:** Discrete spending entities with lifecycles
- **CapEx:** Lumpy, irregular (hardware, licenses, one-time purchases)
- **OpEx:** Recurring, predictable (subscriptions, cloud, salaries)

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FORECAST ENGINE V2                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   OpEx       │    │   CapEx      │    │  Project   │ │
│  │   Forecast   │    │   Forecast   │    │  Lifecycle │ │
│  │              │    │              │    │            │ │
│  │ ARIMA/Prophet│    │ Planned +    │    │  S-Curve   │ │
│  │ + seasonality│    │ Monte Carlo  │    │  by phase  │ │
│  └──────┬───────┘    └──────┬───────┘    └─────┬──────┘ │
│         │                   │                   │        │
│         └───────────────────┼───────────────────┘        │
│                             ▼                            │
│                    ┌────────────────┐                    │
│                    │   Aggregator   │                    │
│                    │  + Confidence  │                    │
│                    │   Intervals    │                    │
│                    └────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### Core Formula

```
Total_Forecast = OpEx_forecast + CapEx_planned + Project_lifecycle_adjustment
```

---

## Forecasting Methods by Expense Type

### 1. OpEx Forecasting (Recurring Costs)

**Recommended Methods:**

| Method | Best For | Data Required | Implementation Status |
|--------|----------|---------------|-----------------------|
| Holt-Winters | Seasonal patterns | 12+ months | ✅ Implemented (Used on Total) |
| ARIMA | Complex autocorrelation | 12+ months | ❌ Pending |
| Prophet | Business events, holidays | 6+ months | ❌ Pending |
| ARIMAX | External factors (headcount, projects) | 12+ months | ❌ Pending |

**Holt-Winters (Triple Exponential Smoothing):**

```python
def holt_winters_forecast(history, periods=6, alpha=0.6, beta=0.3, gamma=0.3, season_length=12):
    """
    Triple exponential smoothing with multiplicative seasonality.

    Parameters:
    - alpha: Level smoothing (0-1)
    - beta: Trend smoothing (0-1)
    - gamma: Seasonal smoothing (0-1)
    - season_length: Period of seasonality (12 for monthly)
    """
    n = len(history)

    # Fallback to Holt's method if insufficient data for seasonality
    if n < season_length * 2:
        return holt_linear_forecast(history, periods, alpha, beta)

    # Initialize seasonal indices from first full season
    first_season_avg = np.mean(history[:season_length])
    season = [history[i] / first_season_avg for i in range(season_length)]

    # Initialize level and trend
    level = first_season_avg
    trend = (np.mean(history[season_length:2*season_length]) -
             np.mean(history[:season_length])) / season_length

    # Smoothing loop
    for t in range(season_length, n):
        val = history[t]
        last_level, last_trend = level, trend

        # Update equations
        level = alpha * (val / season[t % season_length]) + (1 - alpha) * (last_level + last_trend)
        trend = beta * (level - last_level) + (1 - beta) * last_trend
        season[t % season_length] = gamma * (val / level) + (1 - gamma) * season[t % season_length]

    # Generate forecast with confidence intervals
    forecasts = []
    for k in range(1, periods + 1):
        point_forecast = (level + k * trend) * season[(n + k - 1) % season_length]
        forecasts.append({
            'period': k,
            'forecast': max(0, point_forecast),
            'seasonal_factor': season[(n + k - 1) % season_length]
        })

    return forecasts
```

**ARIMAX (with external variables):**

```python
from statsmodels.tsa.arima.model import ARIMA

def arimax_forecast(opex_series, project_count, headcount, periods=6):
    """
    ARIMA with exogenous variables for OpEx forecasting.

    External variables:
    - project_count: Number of active projects
    - headcount: Team size (drives OpEx)
    """
    exog = np.column_stack([project_count, headcount])

    model = ARIMA(opex_series, order=(2, 1, 2), exog=exog)
    fitted = model.fit()

    # Forecast requires future exog values (use last known or planned)
    future_exog = np.column_stack([
        [project_count[-1]] * periods,
        [headcount[-1]] * periods
    ])

    forecast = fitted.forecast(steps=periods, exog=future_exog)
    conf_int = fitted.get_forecast(steps=periods, exog=future_exog).conf_int()

    return {
        'forecast': forecast.tolist(),
        'lower_bound': conf_int.iloc[:, 0].tolist(),
        'upper_bound': conf_int.iloc[:, 1].tolist()
    }
```

---

### 2. CapEx Forecasting (Lumpy Purchases)

**Approach:** Don't use statistical forecasting. Use planned budgets with timing uncertainty.

**Status:** ✅ Logic Implemented (Monte Carlo) but ❌ Not Integrated.

```python
import random
from typing import List, Dict
from datetime import datetime, timedelta

def capex_forecast(planned_purchases: List[Dict], timing_uncertainty: float = 0.2) -> List[Dict]:
    """
    Monte Carlo simulation for CapEx timing uncertainty.

    Parameters:
    - planned_purchases: List of planned CapEx items
      [{amount, expected_month, project_id, description}, ...]
    - timing_uncertainty: Standard deviation of timing slip (0.2 = 20% of timeline)

    Returns:
    - Probabilistic forecast with confidence levels
    """
    simulations = 1000
    monthly_forecasts = {}

    for _ in range(simulations):
        for purchase in planned_purchases:
            # Simulate timing slip (purchases often delayed, rarely early)
            slip_months = max(-1, random.gauss(0.5, timing_uncertainty * 3))  # Slight delay bias
            actual_month = int(purchase['expected_month'] + slip_months)

            if actual_month not in monthly_forecasts:
                monthly_forecasts[actual_month] = []
            monthly_forecasts[actual_month].append(purchase['amount'])

    # Aggregate results
    results = []
    for month, amounts in sorted(monthly_forecasts.items()):
        results.append({
            'month': month,
            'expected': sum(amounts) / simulations,
            'p10': np.percentile(amounts, 10),
            'p50': np.percentile(amounts, 50),
            'p90': np.percentile(amounts, 90),
            'type': 'capex',
            'confidence': 0.7  # CapEx timing is inherently uncertain
        })

    return results


def get_planned_capex(project_budgets: List[Dict]) -> List[Dict]:
    """
    Extract planned CapEx from project budgets.

    project_budgets: [{project_id, capex_items: [{description, amount, planned_date}]}]
    """
    planned = []
    current_month = datetime.now().month
    current_year = datetime.now().year

    for project in project_budgets:
        for item in project.get('capex_items', []):
            planned_date = item.get('planned_date')
            if planned_date:
                # Convert to months from now
                months_from_now = (planned_date.year - current_year) * 12 + (planned_date.month - current_month)
                if months_from_now > 0:
                    planned.append({
                        'amount': item['amount'],
                        'expected_month': months_from_now,
                        'project_id': project['project_id'],
                        'description': item['description']
                    })

    return planned
```

---

### 3. Project Lifecycle Model (S-Curve)

**Pattern:** Projects follow predictable spending curves.

**Status:** ✅ Logic Implemented (S-Curve) but ❌ Not Integrated.

```
Spend
  │         ╭────────╮
  │        ╱          ╲
  │       ╱            ╲
  │      ╱              ╲
  │─────╱                ╲─────
  └──────────────────────────── Time
       Ramp    Peak    Wind-down
```

**Implementation:**

```python
import math
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

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

def s_curve_spend(t: float, total_budget: float, midpoint: float, steepness: float = 1.0) -> float:
    """
    Logistic S-curve for cumulative project spending.

    Parameters:
    - t: Current month in project lifecycle
    - total_budget: Total project budget
    - midpoint: Month when 50% is spent
    - steepness: How sharp the ramp (0.5 = gradual, 2.0 = steep)

    Returns:
    - Cumulative spend at month t
    """
    return total_budget / (1 + math.exp(-steepness * (t - midpoint)))


def project_monthly_spend(project: ProjectForecast) -> List[Dict]:
    """
    Generate monthly spend forecast for a project.
    """
    forecasts = []
    midpoint = project.duration_months / 2

    for month in range(project.current_month, project.duration_months + 1):
        cumulative_current = s_curve_spend(month, project.total_budget, midpoint)
        cumulative_prev = s_curve_spend(month - 1, project.total_budget, midpoint) if month > 0 else 0

        monthly_spend = cumulative_current - cumulative_prev

        forecasts.append({
            'project_id': project.project_id,
            'month': month - project.current_month + 1,  # Months from now
            'forecast': monthly_spend,
            'cumulative': cumulative_current,
            'percent_complete': (cumulative_current / project.total_budget) * 100,
            'phase': determine_phase(month, project.duration_months)
        })

    return forecasts


def determine_phase(current_month: int, total_months: int) -> ProjectPhase:
    """Determine project phase based on timeline position."""
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
```

---

### 4. Expense Classifier

**Status:** ✅ **IMPLEMENTED** (See `backend/src/application/analysis_services.py`) but ❌ Not Integrated.

```python
from typing import Literal

# Keywords for classification
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

def classify_expense(
    description: str,
    amount: float,
    category: str = None,
    is_recurring: bool = None
) -> Literal['capex', 'opex']:
    """
    Classify expense as CapEx or OpEx.

    Heuristics:
    1. Explicit recurring flag
    2. Keyword matching
    3. Amount threshold (large one-time = likely CapEx)
    4. Category-based rules
    """
    desc_lower = description.lower()

    # Check explicit flag
    if is_recurring is not None:
        return 'opex' if is_recurring else 'capex'

    # Keyword matching
    capex_score = sum(1 for kw in CAPEX_KEYWORDS if kw in desc_lower)
    opex_score = sum(1 for kw in OPEX_KEYWORDS if kw in desc_lower)

    if capex_score > opex_score:
        return 'capex'
    if opex_score > capex_score:
        return 'opex'

    # Category-based rules
    capex_categories = {'Hardware', 'Equipment', 'Infrastructure', 'Licenses'}
    opex_categories = {'Software', 'Hosting/Cloud', 'Contractors', 'Subscriptions'}

    if category in capex_categories:
        return 'capex'
    if category in opex_categories:
        return 'opex'

    # Amount heuristic (large one-time purchases are often CapEx)
    # This threshold should be configurable
    if amount > 10000:
        return 'capex'

    return 'opex'  # Default to OpEx
```

---

### 5. Forecast Aggregator

**Status:** ❌ Pending

```python
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ForecastResult:
    month: int
    total: float
    opex: float
    capex: float
    lower_bound: float
    upper_bound: float
    confidence: float
    breakdown: Dict[str, float]

def aggregate_forecasts(
    opex_forecast: List[Dict],
    capex_forecast: List[Dict],
    project_forecasts: List[Dict],
    periods: int = 6
) -> List[ForecastResult]:
    """
    Combine all forecast sources into unified prediction.

    Handles:
    - Different confidence levels per source
    - Overlapping project contributions
    - Uncertainty propagation
    """
    results = []

    for month in range(1, periods + 1):
        # Get forecasts for this month
        opex = next((f for f in opex_forecast if f.get('period') == month), {'forecast': 0})
        capex = next((f for f in capex_forecast if f.get('month') == month), {'expected': 0})

        # Sum project contributions
        project_total = sum(
            f['forecast'] for f in project_forecasts
            if f.get('month') == month
        )

        # Calculate totals
        opex_val = opex.get('forecast', 0)
        capex_val = capex.get('expected', 0)
        total = opex_val + capex_val + project_total

        # Propagate uncertainty (simplified - assumes independence)
        opex_var = (opex.get('upper', opex_val) - opex.get('lower', opex_val)) ** 2 / 4
        capex_var = (capex.get('p90', capex_val) - capex.get('p10', capex_val)) ** 2 / 4
        total_std = math.sqrt(opex_var + capex_var)

        # Weighted confidence
        opex_weight = opex_val / total if total > 0 else 0
        capex_weight = capex_val / total if total > 0 else 0
        confidence = opex_weight * 0.85 + capex_weight * 0.70  # OpEx more predictable

        results.append(ForecastResult(
            month=month,
            total=total,
            opex=opex_val,
            capex=capex_val,
            lower_bound=max(0, total - 1.96 * total_std),
            upper_bound=total + 1.96 * total_std,
            confidence=confidence,
            breakdown={
                'opex': opex_val,
                'capex': capex_val,
                'project_adjustments': project_total
            }
        ))

    return results
```

---

## Data Model Changes

### New Fields Required

```python
# In BudgetModel or transaction table
class ExpenseEntry:
    # Existing fields...

    # New fields for V2
    expense_type: Literal['capex', 'opex', 'unknown']  # Classification
    is_recurring: bool                                  # Explicit flag
    project_phase: str                                  # Project lifecycle phase
    planned_date: datetime                              # For CapEx planning
```

### API Changes

```python
# New endpoint for forecast configuration
@router.post("/api/v1/forecast/configure")
async def configure_forecast(
    capex_threshold: float = 10000,
    seasonality_period: int = 12,
    forecast_method: Literal['holt', 'holt_winters', 'arima', 'prophet'] = 'holt_winters'
):
    """Configure forecast engine parameters."""
    pass

# Enhanced forecast response
@router.get("/api/v1/forecast")
async def get_forecast(periods: int = 6, include_breakdown: bool = True):
    """
    Returns:
    {
        "forecast": [...],
        "opex_forecast": [...],
        "capex_forecast": [...],
        "project_forecasts": [...],
        "methodology": "hybrid_v2",
        "confidence_summary": {...}
    }
    """
    pass
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [x] Add expense_type field to data model (See `models.py`)
- [x] Implement expense classifier (See `analysis_services.py`)
- [ ] Create CapEx/OpEx separation in analyze_budget.py (Pending)
- [x] Add unit tests for classifier

### Phase 2: Forecast Models (Week 2)
- [x] Implement Holt-Winters in backend
- [x] Add CapEx Monte Carlo simulation
- [x] Create project S-curve model
- [ ] Implement forecast aggregator (Pending Integration)

### Phase 3: Integration (Week 3)
- [ ] Update API endpoints
- [ ] Modify frontend to display breakdown
- [ ] Add configuration UI for forecast parameters
- [ ] End-to-end testing

---

## Method Selection Guide

| Data Situation | Recommended Method |
|----------------|-------------------|
| < 6 months data | Holt's Linear (current) |
| 6-12 months, no seasonality | Holt's Linear |
| 12+ months, seasonal patterns | Holt-Winters |
| Complex dependencies | ARIMAX with external vars |
| Business events matter | Prophet |
| Mostly CapEx | Planned budget + Monte Carlo |
| Mixed CapEx/OpEx | **Hybrid model (this design)** |

---

## Dependencies

### Python Libraries

```
statsmodels>=0.14.0    # ARIMA, Holt-Winters
prophet>=1.1.0         # Facebook Prophet (optional)
numpy>=1.24.0          # Numerical operations
scipy>=1.11.0          # Statistical functions
```

### Optional (for advanced features)

```
tensorflow>=2.13.0     # LSTM forecasting
pytorch>=2.0.0         # Alternative deep learning
```

---

## Success Metrics

| Metric | Current (V1) | Target (V2) |
|--------|--------------|-------------|
| MAPE (OpEx) | ~15% | < 10% |
| MAPE (Total) | ~25% | < 15% |
| CapEx timing accuracy | N/A | ±1 month |
| User confidence score | Unknown | > 4/5 |

---

## References

1. Holt, C. C. (1957). "Forecasting Trends and Seasonals by Exponentially Weighted Averages"
2. Winters, P. R. (1960). "Forecasting Sales by Exponentially Weighted Moving Averages"
3. Box, G. E. P., & Jenkins, G. M. (1970). "Time Series Analysis: Forecasting and Control"
4. Taylor, S. J., & Letham, B. (2018). "Forecasting at Scale" (Prophet)

---

**Document Status:** Partially Implemented (Core Algorithms Ready, Full Integration Pending)
**Next Steps:** Refactor `AnalyzeBudgetUseCase` to separate OpEx/CapEx flows and utilize the new models.