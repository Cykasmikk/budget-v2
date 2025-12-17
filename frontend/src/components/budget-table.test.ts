import { describe, it, expect, beforeEach } from 'vitest';
import { BudgetTable } from './budget-table';
import type { Transaction } from '../store/budget.store';

describe('BudgetTable', () => {
    let element: BudgetTable;
    const mockTransactions: Transaction[] = [
        {
            id: 1,
            date: '2024-01-15',
            category: 'Cloud',
            amount: 100,
            description: 'AWS Service',
            type: 'expense'
        },
        {
            id: 2,
            date: '2024-01-16',
            category: 'Infrastructure',
            amount: 200,
            description: 'Server Hosting',
            type: 'expense'
        }
    ];

    beforeEach(() => {
        element = new BudgetTable();
        element.transactions = mockTransactions;
        document.body.appendChild(element);
    });

    it('should render budget table', () => {
        const table = element.shadowRoot?.querySelector('table');
        expect(table).toBeTruthy();
    });

    it('should render table headers', () => {
        const headers = element.shadowRoot?.querySelectorAll('th');
        expect(headers?.length).toBeGreaterThan(0);
    });

    it('should render transaction rows', () => {
        const rows = element.shadowRoot?.querySelectorAll('tbody tr');
        expect(rows?.length).toBe(mockTransactions.length);
    });

    it('should display transaction data', () => {
        const firstRow = element.shadowRoot?.querySelector('tbody tr');
        expect(firstRow?.textContent).toContain('AWS Service');
        expect(firstRow?.textContent).toContain('Cloud');
    });

    it('should format amounts correctly', () => {
        const firstRow = element.shadowRoot?.querySelector('tbody tr');
        expect(firstRow?.textContent).toContain('$100');
    });

    it('should handle empty transactions', async () => {
        element.transactions = [];
        await element.updateComplete;
        
        const rows = element.shadowRoot?.querySelectorAll('tbody tr');
        expect(rows?.length).toBe(0);
    });

    it('should display date in correct format', () => {
        const firstRow = element.shadowRoot?.querySelector('tbody tr');
        expect(firstRow?.textContent).toContain('2024-01-15');
    });
});

