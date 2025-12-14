import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { InfographicReport } from './infographic-report';
import { BudgetMetrics } from '../../store/budget-store';

describe('InfographicReport', () => {
    let element: InfographicReport;
    const mockMetrics: BudgetMetrics = {
        total_expenses: 1000,
        category_breakdown: { 'Cloud': 500, 'Infrastructure': 300 },
        project_breakdown: {},
        top_merchants: { 'AWS': 200 },
        gaps: [],
        flash_fill: [],
        subscriptions: [],
        anomalies: [],
        monthly_trend: [],
        category_history: {},
        project_history: {},
        timeline: [],
        category_vendors: {},
        project_vendors: {},
        category_merchants: {},
        project_merchants: {}
    };

    beforeEach(() => {
        element = new InfographicReport();
        element.metrics = mockMetrics;
        document.body.appendChild(element);
    });

    afterEach(() => {
        if (document.body.contains(element)) {
            document.body.removeChild(element);
        }
    });

    it('should render infographic report', () => {
        expect(element).toBeTruthy();
    });

    it('should be hidden by default', () => {
        expect(element.visible).toBe(false);
    });

    it('should show when visible is true', () => {
        element.visible = true;
        element.requestUpdate();
        
        expect(element.visible).toBe(true);
    });

    it('should render A4 page when visible', () => {
        element.visible = true;
        element.requestUpdate();
        
        const a4Page = element.shadowRoot?.querySelector('.a4-page');
        expect(a4Page).toBeTruthy();
    });

    it('should display metrics when provided', () => {
        element.visible = true;
        element.metrics = mockMetrics;
        element.requestUpdate();
        
        expect(element.metrics).toEqual(mockMetrics);
    });

    it('should handle null metrics', () => {
        element.visible = true;
        element.metrics = null;
        element.requestUpdate();
        
        expect(element.metrics).toBeNull();
    });
});

