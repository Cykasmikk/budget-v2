import { describe, it, expect, beforeEach } from 'vitest';
import { DashboardView } from './dashboard-view';

describe('DashboardView', () => {
    let element: DashboardView;

    beforeEach(() => {
        element = new DashboardView();
        document.body.appendChild(element);
    });

    it('should render analysis card component', () => {
        const card = element.shadowRoot?.querySelector('analysis-card');
        expect(card).toBeTruthy();
    });


});
