import { describe, it, expect, beforeEach } from 'vitest';
import { BudgetChart } from './budget-chart';

describe('BudgetChart Neuro-Symbolic Features', () => {
    let element: BudgetChart;

    beforeEach(() => {
        element = new BudgetChart();
        document.body.appendChild(element);
    });

    it('should distinguish Actuals vs Predicted in tooltip labels', async () => {
        // Setup mock data with forecast
        element.viewMode = 'forecast';
        element.data = [
            { month: '2024-01', amount: 100, is_forecast: false },
            { month: '2024-02', amount: 120, is_forecast: true }
        ];

        await element.updateComplete;

        // We need to access the chart instance to check config
        const chart = (element as any).chart;
        expect(chart).toBeTruthy();

        // Get the tooltip callback
        const tooltipCallback = chart.config.options.plugins.tooltip.callbacks.label;

        // Mock context for Actuals (Index 0)
        const contextActual = {
            parsed: { y: 100 },
            dataset: { label: 'Monthly Spend', data: [100, 120] },
            dataIndex: 0
        };

        // Mock context for Forecast (Index 1)
        const contextForecast = {
            parsed: { y: 120 },
            dataset: { label: 'Monthly Spend', data: [100, 120] },
            dataIndex: 1
        };

        const labelActual = tooltipCallback(contextActual);
        const labelForecast = tooltipCallback(contextForecast);

        // Expect implicit or explicit distinction
        // Current implementation probably just shows "Monthly Spend: $100"
        // We want "Monthly Spend (Actual): $100" or similar
        expect(labelActual).toContain('(Actual)');
        expect(labelForecast).toContain('(Predicted)');
    });

    it('should render confidence intervals when bounds are present', async () => {
        element.viewMode = 'forecast';
        element.data = [
            { month: '2024-01', amount: 100, is_forecast: true, lower_bound: 90, upper_bound: 110 }
        ];

        await element.updateComplete;
        const chart = (element as any).chart;

        // Should have 3 datasets: Upper, Lower, Main
        expect(chart.data.datasets.length).toBe(3);
        expect(chart.data.datasets[0].label).toBe('Upper Bound');
        expect(chart.data.datasets[1].label).toBe('Confidence Interval');
        expect(chart.data.datasets[2].label).toBe('Monthly Spend');
    });
});
