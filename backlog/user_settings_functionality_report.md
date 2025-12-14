# User Settings Functionality Report

## Analysis Date
**December 13, 2025**

## Executive Summary
The "user settings" within the application, managed at the tenant level and exposed via `SettingsView` (frontend) and `settings_router.py` (backend), are **partially functional and actively used**. While some settings directly impact user experience and data processing, others are currently stored but await full integration with corresponding features.

---

## Detailed Breakdown of Settings

The `TenantModel` in `backend/src/infrastructure/models.py` stores a `settings` JSON object with the following fields:

### 1. `currency` (e.g., "USD")
*   **Purpose:** To display financial values with the correct currency symbol.
*   **Functionality:** ✅ **Active.** The `frontend/src/store/budget-store.ts` fetches and updates this setting. Display components (e.g., `BudgetTable`, metrics displays) are intended to use this for formatting, making it directly impact the user's visual experience of financial figures.
*   **Backend Impact:** Stored only; no backend calculations or conversions are performed based on this setting.

### 2. `forecast_horizon` (e.g., 3, 6, 12 months)
*   **Purpose:** To define the period for future expense projections.
*   **Functionality:** ⚠️ **Partially Active.** The `SettingsView` allows users to select this value, and it's correctly stored and synced. It is intended to be consumed by the forecasting engine (e.g., in `AnalyzeBudgetUseCase` or `SimulateBudgetUseCase` on the backend). However, as per `implementation_status_report.md`, the forecasting feature is currently marked as "Mock" or "Placeholder", meaning the full impact of this setting is not yet realized.

### 3. `theme` (e.g., "dark")
*   **Purpose:** To switch the application's visual theme (e.g., dark mode, light mode).
*   **Functionality:** ❌ **Passive (Stored only).** The `SettingsView` allows users to change this value, and it's correctly stored and synced. However, there is no active CSS or JavaScript logic in the frontend (e.g., in `app-shell.ts` or global styles) that consumes this setting to actually switch the theme. The UI theme remains static regardless of this setting.

### 4. `budget_threshold` (e.g., 5000)
*   **Purpose:** To set a global spending limit, potentially triggering warnings or alerts.
*   **Functionality:** ✅ **Active.** The `SettingsView` allows users to set this. The `budgetStore.state.settings.budget_threshold` is synced and directly influences `budgetStore.state.budgetLimit`. This `budgetLimit` is then used by frontend components (e.g., `AppShell`, `AnalysisCard`) to display "Budget Remaining" and likely provides a basis for visual warning indicators when spending approaches or exceeds the limit.
*   **Backend Impact:** Stored only; no backend enforcement or calculation based on this.

### 5. `merge_strategy` (e.g., 'latest', 'blended', 'combined')
*   **Purpose:** To define how data from multiple uploaded budget files should be aggregated.
*   **Functionality:** ✅ **Active and Critical.** This setting is actively used by the `BudgetStore`'s `calculateMetrics` function. It directly dictates the core logic for combining financial data from different sources (`mergeCombinedStrategy`, `mergeBlendedStrategy`). This has a significant impact on how the user's overall budget data is presented and analyzed.
*   **Backend Impact:** Stored only; the logic for applying this strategy resides on the frontend, which fetches and applies it after data upload.

---

## Conclusion
User settings are more than just placeholders. `currency`, `budget_threshold`, and especially `merge_strategy` play active roles in the application's current functionality. The `forecast_horizon` setting is in place for future feature development, and the `theme` setting is currently passive, awaiting frontend implementation to apply its effect.

Further development will likely enhance the impact of `forecast_horizon` and integrate `theme` into the UI.
