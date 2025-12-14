import { describe, it, expect, beforeEach } from 'vitest';
import { AnalysisCard } from './analysis-card';
import { BudgetMetrics } from '../../store/budget-store';

describe('AnalysisCard', () => {
    let element: AnalysisCard;
    const mockMetrics: BudgetMetrics = {
        total_expenses: 1000,
        category_breakdown: { 'Test': 500 },
        project_breakdown: {},
        top_merchants: {},
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
        element = new AnalysisCard();
        element.metrics = mockMetrics;
        element.viewMode = 'category';
        document.body.appendChild(element);
    });

    it('should render analysis card', () => {
        const card = element.shadowRoot?.querySelector('.card');
        expect(card).toBeTruthy();
    });

    it('should display correct title for category view', async () => {
        element.viewMode = 'category';
        await element.updateComplete;
        const title = element.shadowRoot?.querySelector('.card-title');
        expect(title?.textContent).toContain('Analysis');
    });

    it('should display correct title for forecast view', async () => {
        element.viewMode = 'forecast';
        await element.updateComplete;
        const title = element.shadowRoot?.querySelector('.card-title');
        expect(title?.textContent).toContain('Forecast');
    });

    it('should display correct title for chat view', async () => {
        element.viewMode = 'chat';
        await element.updateComplete;
        const title = element.shadowRoot?.querySelector('.card-title');
        expect(title?.textContent).toContain('AI Chat');
    });

    it('should render analysis controls', () => {
        const controls = element.shadowRoot?.querySelector('analysis-controls');
        expect(controls).toBeTruthy();
    });

    it('should render chart for category view', async () => {
        element.viewMode = 'category';
        await element.updateComplete;
        const chart = element.shadowRoot?.querySelector('budget-chart');
        expect(chart).toBeTruthy();
    });

    it('should render ai-chat for chat view', async () => {
        element.viewMode = 'chat';
        await element.updateComplete;
        const chat = element.shadowRoot?.querySelector('ai-chat');
        expect(chat).toBeTruthy();
    });
});

