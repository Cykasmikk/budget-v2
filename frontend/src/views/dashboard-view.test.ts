import { describe, it, expect, beforeEach } from 'vitest';
import { DashboardView } from './dashboard-view';

describe('DashboardView', () => {
    let element: DashboardView;

    beforeEach(() => {
        element = new DashboardView();
        document.body.appendChild(element);
    });

    it('should render file upload component', () => {
        const upload = element.shadowRoot?.querySelector('file-upload');
        expect(upload).toBeTruthy();
    });

    it('should render budget chart component', () => {
        const chart = element.shadowRoot?.querySelector('budget-chart');
        expect(chart).toBeTruthy();
    });
});
