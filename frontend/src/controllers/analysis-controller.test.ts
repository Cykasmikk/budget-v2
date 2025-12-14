import { describe, it, expect, beforeEach } from 'vitest';
import { AnalysisController } from './analysis-controller';
import { BudgetMetrics } from '../store/budget-store';
import { LitElement } from 'lit';

class MockHost extends LitElement {
    requestUpdate() {
        return super.requestUpdate();
    }
}
if (!customElements.get('mock-host-analysis')) {
    customElements.define('mock-host-analysis', MockHost);
}

describe('AnalysisController', () => {
    let controller: AnalysisController;
    let host: MockHost;
    const mockMetrics: BudgetMetrics = {
        total_expenses: 1000,
        category_breakdown: { 'Cloud': 500, 'Infrastructure': 300 },
        project_breakdown: { 'Project A': 400 },
        top_merchants: { 'AWS': 200 },
        gaps: [],
        flash_fill: [],
        subscriptions: [],
        anomalies: [],
        monthly_trend: [
            { month: 'Jan 2024', amount: 100, is_forecast: false, sort_key: '2024-01' }
        ],
        category_history: {
            'Cloud': [{ month: 'Jan 2024', amount: 50, is_forecast: false, sort_key: '2024-01' }]
        },
        project_history: {},
        timeline: [],
        category_vendors: {},
        project_vendors: {},
        category_merchants: {},
        project_merchants: {}
    };

    beforeEach(() => {
        host = new MockHost();
        controller = new AnalysisController(host);
    });

    it('should initialize with default values', () => {
        expect(controller.selectedCategory).toBeNull();
        expect(controller.showForecast).toBe(true);
        expect(controller.forecastMonths).toBe(6);
    });

    it('should get chart data for category view', () => {
        const result = controller.getChartData('category', mockMetrics);
        
        expect(result.data).toEqual(mockMetrics.category_breakdown);
        expect(result.isDrillDown).toBe(false);
    });

    it('should get chart data for project view', () => {
        const result = controller.getChartData('project', mockMetrics);
        
        expect(result.data).toEqual(mockMetrics.project_breakdown);
        expect(result.isDrillDown).toBe(false);
    });

    it('should get forecast data', () => {
        const result = controller.getChartData('forecast', mockMetrics);
        
        expect(result.data).toBeDefined();
        expect(result.isDrillDown).toBe(false);
    });

    it('should handle category selection', () => {
        controller.selectCategory('Cloud');
        
        expect(controller.selectedCategory).toBe('Cloud');
    });

    it('should clear category selection', () => {
        controller.selectCategory('Cloud');
        controller.selectCategory(null);
        
        expect(controller.selectedCategory).toBeNull();
    });

    it('should toggle forecast', () => {
        const initial = controller.showForecast;
        controller.toggleForecast(!initial);
        
        expect(controller.showForecast).toBe(!initial);
    });

    it('should set forecast months', () => {
        controller.setForecastMonths(6);
        
        expect(controller.forecastMonths).toBe(6);
    });

    it('should get title for different view modes', () => {
        expect(controller.getTitle('forecast')).toBe('Spending Forecast (Aus FY)');
        expect(controller.getTitle('chat')).toBe('AI Chat');
        expect(controller.getTitle('category')).toBe('Analysis');
        expect(controller.getTitle('project')).toBe('Analysis');
    });

    it('should handle drill down for category view', () => {
        const metricsWithMerchants: BudgetMetrics = {
            ...mockMetrics,
            category_merchants: {
                'Cloud': {
                    'AWS': 200,
                    'Azure': 100
                }
            }
        };

        controller.selectCategory('Cloud');
        const result = controller.getChartData('category', metricsWithMerchants);
        
        expect(result.isDrillDown).toBe(true);
        expect(result.data).toHaveProperty('AWS');
        expect(result.data).toHaveProperty('Azure');
    });

    it('should handle forecast data with showForecast false', () => {
        controller.showForecast = false;
        const result = controller.getChartData('forecast', mockMetrics);
        
        expect(result.data).toBeDefined();
        expect(Array.isArray(result.data)).toBe(true);
    });

    it('should handle forecast data with showForecast true', () => {
        controller.showForecast = true;
        controller.forecastMonths = 3;
        const result = controller.getChartData('forecast', mockMetrics);
        
        expect(result.data).toBeDefined();
    });

    it('should set forecast type', () => {
        controller.setForecastType('category');
        expect(controller.forecastType).toBe('category');
        
        controller.setForecastType('project');
        expect(controller.forecastType).toBe('project');
    });
});

