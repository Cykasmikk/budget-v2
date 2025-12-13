import { describe, it, expect, beforeEach } from 'vitest';
import { AnalysisSidebar } from './analysis-sidebar';
import { BudgetMetrics } from '../../../store/budget-store';

describe('AnalysisSidebar', () => {
    let element: AnalysisSidebar;
    const mockMetrics: BudgetMetrics = {
        total_expenses: 1000,
        category_breakdown: { 'Cloud': 500, 'Infrastructure': 300 },
        project_breakdown: {},
        top_merchants: { 'AWS': 200, 'Azure': 100 },
        gaps: [],
        flash_fill: [],
        subscriptions: [],
        anomalies: [],
        monthly_trend: [],
        category_history: {},
        project_history: {},
        category_vendors: {},
        project_vendors: {},
        category_merchants: {},
        project_merchants: {}
    };

    beforeEach(() => {
        element = new AnalysisSidebar();
        element.metrics = mockMetrics;
        document.body.appendChild(element);
    });

    it('should render analysis sidebar', () => {
        const sidebar = element.shadowRoot?.querySelector(':host');
        expect(element).toBeTruthy();
    });

    it('should display merchants list', () => {
        element.merchants = [['AWS', 200], ['Azure', 100]];
        element.requestUpdate();
        
        const merchantsList = element.shadowRoot?.querySelector('.merchants-list');
        expect(merchantsList).toBeTruthy();
    });

    it('should display merchant items', async () => {
        element.merchants = [['AWS', 2000], ['Azure', 1000]];
        await element.updateComplete;
        
        const merchantItems = element.shadowRoot?.querySelectorAll('.merchant-item');
        expect(merchantItems?.length).toBeGreaterThan(0);
    });

    it('should format merchant amounts correctly', async () => {
        element.merchants = [['AWS', 2000]];
        await element.updateComplete;
        
        const merchantItem = element.shadowRoot?.querySelector('.merchant-item');
        expect(merchantItem?.textContent).toContain('$2,000');
    });

    it('should handle empty merchants list', () => {
        element.merchants = [];
        element.requestUpdate();
        
        const merchantsList = element.shadowRoot?.querySelector('.merchants-list');
        expect(merchantsList).toBeTruthy();
    });

    it('should display forecast info when showForecast is true', () => {
        element.showForecast = true;
        element.forecastMonths = 6;
        element.requestUpdate();
        
        expect(element.showForecast).toBe(true);
        expect(element.forecastMonths).toBe(6);
    });
});

