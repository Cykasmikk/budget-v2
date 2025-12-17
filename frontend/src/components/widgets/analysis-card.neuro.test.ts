import { describe, it, expect, beforeEach } from 'vitest';
import { AnalysisCard } from './analysis-card';
import { BudgetMetrics } from '../../store/budget-store';

describe('AnalysisCard Neuro-Symbolic Features', () => {
    let element: AnalysisCard;
    const mockMetrics: BudgetMetrics = {
        total_expenses: 1000,
        category_breakdown: { 'Test': 1000 }, // Matches total
        project_breakdown: {},
        top_merchants: {},
        gaps: [],
        flash_fill: [{ count: 1, description: 'Test', suggested_category: 'Test' }],
        subscriptions: [],
        anomalies: [],
        monthly_trend: [],
        category_history: {},
        project_history: {},
        timeline: [],
        category_vendors: {},
        project_vendors: {},
        category_merchants: {},
        project_merchants: {},
        is_verified: true // Hypothetical backend flag, or we verify locally
    } as any; // Using any to partial match for now as we might extend the type

    beforeEach(() => {
        element = new AnalysisCard();
        element.metrics = mockMetrics;
        document.body.appendChild(element);
    });

    it('should render insights-card when viewMode is insights', async () => {
        element.viewMode = 'insights' as any; // Cast as we haven't updated the type yet
        await element.updateComplete;
        const insights = element.shadowRoot?.querySelector('insights-card');
        expect(insights).toBeTruthy();
    });

    it('should display a Verified Badge when numbers match (Symbolic Check)', async () => {
        // In this case, total_expenses (1000) == sum(category_breakdown) (1000)
        await element.updateComplete;
        const badge = element.shadowRoot?.querySelector('.verified-badge');
        expect(badge).toBeTruthy();
        expect(badge?.textContent).toContain('Verified');
    });

    it('should NOT display Verified Badge when numbers do not match', async () => {
        element.metrics = {
            ...mockMetrics,
            total_expenses: 2000, // Mismatch with breakdown (1000)
            category_breakdown: { 'Test': 1000 }
        };
        await element.updateComplete;
        const badge = element.shadowRoot?.querySelector('.verified-badge');
        expect(badge).toBeFalsy();
    });
});
