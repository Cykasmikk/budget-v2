import { describe, it, expect, beforeEach } from 'vitest';
import { TimelineView } from './timeline-view';
import { BudgetMetrics } from '../../../store/budget-store';
import { TimelineItem } from '../../../types/interfaces';

describe('TimelineView', () => {
    let element: TimelineView;
    const mockTimeline: TimelineItem[] = [
        {
            id: '1',
            label: 'AWS Support',
            start_date: '2024-01-01',
            end_date: '2024-12-31',
            type: 'subscription',
            amount: 1000
        },
        {
            id: '2',
            label: 'Server Refresh',
            start_date: '2024-06-01',
            end_date: '2027-06-01',
            type: 'hardware',
            amount: 50000
        }
    ];

    const mockMetrics = {
        total_expenses: 0,
        category_breakdown: {},
        project_breakdown: {},
        top_merchants: {},
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
        project_merchants: {},
        timeline: mockTimeline
    } as BudgetMetrics;

    beforeEach(() => {
        element = new TimelineView();
        element.metrics = mockMetrics;
        document.body.appendChild(element);
    });

    it('should render header', () => {
        const header = element.shadowRoot?.querySelector('h3');
        expect(header?.textContent).toContain('Contract & Lifecycle Timeline');
    });

    it('should render gantt chart when data exists', async () => {
        await element.updateComplete;
        const gantt = element.shadowRoot?.querySelector('gantt-chart');
        expect(gantt).toBeTruthy();
        expect(gantt?.items).toEqual(mockTimeline);
    });

    it('should render empty state when no data', async () => {
        element.metrics = { ...mockMetrics, timeline: [] };
        await element.requestUpdate();
        await element.updateComplete;
        
        const gantt = element.shadowRoot?.querySelector('gantt-chart');
        expect(gantt).toBeNull();
        
        const emptyMsg = element.shadowRoot?.textContent;
        expect(emptyMsg).toContain('No timeline data available');
    });
});
