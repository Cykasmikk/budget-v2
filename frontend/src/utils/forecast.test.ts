import { describe, it, expect } from 'vitest';
import { ForecastService } from './forecast';
import { HistoryItem } from '../types/interfaces';

const createHistory = (amounts: number[], isForecast: boolean = false): HistoryItem[] => {
    return amounts.map((amount, i) => ({
        month: `Month ${i}`,
        amount,
        is_forecast: isForecast,
        sort_key: `2024-${(i+1).toString().padStart(2, '0')}`
    }));
};

describe('ForecastService', () => {
    it('should return undefined for insufficient data', () => {
        expect(ForecastService.generateSummary([])).toBeUndefined();
        expect(ForecastService.generateSummary(createHistory([100]))).toBeUndefined();
    });

    it('should ignore existing forecast items', () => {
        const history = [
            ...createHistory([100, 110]),
            ...createHistory([120], true)
        ];
        // Should only use the 2 actuals. 100 -> 110. Trend +10.
        // Next: 120 (Forecast 1).
        const summary = ForecastService.generateSummary(history, 1);
        expect(summary).toBeDefined();
        // Forecasted total for 1 period should be 120
        expect(summary?.forecasted_total).toBe(120);
    });

    it('should detect flat trend', () => {
        const history = createHistory([100, 100, 100]);
        const summary = ForecastService.generateSummary(history, 3);
        
        expect(summary).toBeDefined();
        expect(summary?.trend_direction).toContain('Stable');
        expect(summary?.growth_rate).toBe(0);
        expect(summary?.forecasted_total).toBe(300); // 100 * 3
    });

    it('should detect increasing trend', () => {
        const history = createHistory([100, 110, 120, 130]);
        // Trend is +10 per period.
        // Forecast 3 months: 140, 150, 160. Total 450.
        const summary = ForecastService.generateSummary(history, 3);
        
        expect(summary).toBeDefined();
        expect(summary?.trend_direction).toContain('Increasing');
        expect(summary?.trend_component).toBeGreaterThan(0);
        // Growth rate: (Last Forecast (160) - Last Actual (130)) / 130 = 30/130 = 23%
        expect(summary?.growth_rate).toBeGreaterThan(20);
        expect(summary?.forecasted_total).toBeCloseTo(450, 0);
    });

    it('should detect decreasing trend', () => {
        const history = createHistory([100, 90, 80]);
        const summary = ForecastService.generateSummary(history, 1);
        
        expect(summary).toBeDefined();
        expect(summary?.trend_direction).toContain('Decreasing');
        expect(summary?.trend_component).toBeLessThan(0);
    });
});
