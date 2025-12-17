import { describe, it, expect, beforeEach } from 'vitest';
import { BudgetTable } from './budget-table';
import { Transaction } from '../store/budget.store';

describe('BudgetTable Neuro-Symbolic Features', () => {
    let element: BudgetTable;

    const mockTransactions: Transaction[] = [
        {
            date: '2024-01-01',
            category: 'Food',
            amount: 50,
            description: 'Groceries',
            confidence_score: 0.95,
            is_rule_match: false
        } as any,
        {
            date: '2024-01-02',
            category: 'Unknown',
            amount: 20,
            description: 'Mystery Charge',
            confidence_score: 0.4,
            is_rule_match: false
        } as any,
        {
            date: '2024-01-03',
            category: 'Rent',
            amount: 1000,
            description: 'Monthly Rent',
            confidence_score: 1.0,
            is_rule_match: true
        } as any
    ];

    beforeEach(() => {
        element = new BudgetTable();
        element.transactions = mockTransactions;
        document.body.appendChild(element);
    });

    it('should display warning for low confidence transactions', async () => {
        await element.updateComplete;
        // Looking for a warning icon or class on the low confidence row (index 1)
        const rows = element.shadowRoot?.querySelectorAll('tbody tr');
        expect(rows).toBeTruthy();
        // Row 2 is the low confidence one
        const lowConfRow = rows![1];
        const cell = lowConfRow.querySelector('.neuro-confidence');
        expect(cell).toBeTruthy();
        expect(cell?.textContent).toContain('⚠️'); // Or text "Review"
    });

    it('should display rule match icon for symbolic matches', async () => {
        await element.updateComplete;
        // Row 3 is the rule match one
        const rows = element.shadowRoot?.querySelectorAll('tbody tr');
        const ruleRow = rows![2];
        const cell = ruleRow.querySelector('.symbolic-match');
        expect(cell).toBeTruthy();
        expect(cell?.textContent).toContain('🔒'); // Or verified icon
    });
});
