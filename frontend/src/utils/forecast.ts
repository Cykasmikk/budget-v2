import { HistoryItem, ForecastSummary } from '../types/interfaces';

// Default smoothing parameters for Holt's Linear Trend Method
// Alpha (level smoothing): Generally between 0.1 and 0.9, higher values for more recent data influence.
const HOLT_ALPHA_DEFAULT = 0.6; 
// Beta (trend smoothing): Generally between 0.1 and 0.9, higher values for more recent trend influence.
const HOLT_BETA_DEFAULT = 0.3;

export class ForecastService {
    /**
     * Applies Holt's Linear Trend Method to generate a forecast summary.
     * @param history The historical data (monthly trend).
     * @param periods Number of months to forecast.
     * @param alpha Level smoothing factor (0-1).
     * @param beta Trend smoothing factor (0-1).
     */
    static generateSummary(history: HistoryItem[], periods: number = 6, alpha: number = HOLT_ALPHA_DEFAULT, beta: number = HOLT_BETA_DEFAULT): ForecastSummary | undefined {
        // Filter for actuals only (is_forecast = false) just in case, though usually history is actuals.
        // Actually, merged history might contain previous forecasts? We should filter.
        const actuals = history.filter(h => !h.is_forecast);

        if (actuals.length < 2) return undefined;

        // Sort by date (assuming ISO YYYY-MM string in month or we rely on array order)
        // BudgetStore sorts monthly_trend by date already.

        const amounts = actuals.map(h => h.amount);

        // Initialization
        let level = amounts[0];
        let trend = amounts[1] - amounts[0];
        const fitted_values = [level];

        // Smoothing Loop
        for (let i = 1; i < amounts.length; i++) {
            const val = amounts[i];
            const last_level = level;
            const last_trend = trend;

            fitted_values.push(last_level + last_trend);

            level = alpha * val + (1 - alpha) * (last_level + last_trend);
            trend = beta * (level - last_level) + (1 - beta) * last_trend;
        }

        // Statistics
        const residuals = amounts.map((val, i) => val - fitted_values[i]);
        const sum_sq_error = residuals.reduce((sum, r) => sum + r * r, 0);
        const sigma = amounts.length > 0 ? Math.sqrt(sum_sq_error / amounts.length) : 0;

        // MAPE
        let mape = 0;
        let valid_points = 0;
        amounts.forEach((actual, i) => {
            if (actual !== 0) {
                mape += Math.abs(residuals[i] / actual);
                valid_points++;
            }
        });
        mape = valid_points > 0 ? (mape / valid_points) * 100 : 0;
        const accuracy = Math.max(0, 100 - mape);

        // Outlier Detection
        const outlier_detected = residuals.some(r => Math.abs(r) > 3 * sigma);

        // Projection for Summary
        let forecast_sum = 0;
        const ci_widths: number[] = [];

        let last_level = level;
        let last_trend = trend;

        for (let p = 1; p <= periods; p++) {
            let forecast_val = last_level + p * last_trend;
            const margin = 1.96 * sigma * Math.sqrt(p);
            
            const upper = forecast_val + margin;
            const lower = Math.max(0, forecast_val - margin);
            forecast_val = Math.max(0, forecast_val);

            forecast_sum += forecast_val;
            if (forecast_val > 0) {
                ci_widths.push((upper - lower) / forecast_val);
            }
        }

        let trend_direction = "Stable ➡";
        if (trend > 0.05 * Math.abs(level)) trend_direction = "Increasing ↗";
        else if (trend < -0.05 * Math.abs(level)) trend_direction = "Decreasing ↘";
        else if (trend > 0) trend_direction = "Slight Increase ↗";
        else if (trend < 0) trend_direction = "Slight Decrease ↘";

        const last_actual = amounts[amounts.length - 1] || 0;
        // Growth Rate: (Last Forecast - Last Actual) / Last Actual
        // Consistent with backend logic
        const last_forecast = last_level + periods * last_trend;
        let growth_rate = 0;
        if (last_actual !== 0) {
            growth_rate = ((last_forecast - last_actual) / last_actual) * 100;
        }

        const avg_ci_width = ci_widths.length > 0 ? (ci_widths.reduce((a, b) => a + b, 0) / ci_widths.length) * 100 : 0;

        return {
            trend_direction,
            forecasted_total: Number(forecast_sum.toFixed(2)),
            growth_rate: Number(growth_rate.toFixed(2)),
            confidence_interval_width: Number(avg_ci_width.toFixed(2)),
            seasonality_index: 0,
            trend_component: Number(trend.toFixed(2)),
            level_component: Number(level.toFixed(2)),
            outlier_detected,
            model_accuracy: Number(accuracy.toFixed(2))
        };
    }
}
