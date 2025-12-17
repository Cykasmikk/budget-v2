import { describe, it, expect, beforeEach } from 'vitest';
import { BudgetChart } from './budget-chart';

describe('BudgetChart', () => {
    let element: BudgetChart;

    beforeEach(() => {
        element = new BudgetChart();
        document.body.appendChild(element);
    });

    it('should render canvas', () => {
        const canvas = element.shadowRoot?.querySelector('canvas');
        expect(canvas).toBeTruthy();
    });
});
