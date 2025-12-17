import { describe, it, expect, beforeEach, vi } from 'vitest';
import { RulesCard } from './rules-card';
import { budgetStore } from '../../store/budget-store';

describe('RulesCard Neuro-Symbolic Features', () => {
    let element: RulesCard;

    // Mock suggestions data
    const mockSuggestions = [
        { description: 'Netflix', suggested_category: 'Entertainment', count: 12 },
        { description: 'Uber', suggested_category: 'Transport', count: 5 }
    ];

    beforeEach(() => {
        element = new RulesCard();
        (element as any).rules = [];
        (element as any).suggestions = mockSuggestions;
        document.body.appendChild(element);
    });

    it('should render tabs for Active Rules and Suggested Rules', async () => {
        await element.updateComplete;
        const tabs = element.shadowRoot?.querySelectorAll('.tab-btn');
        expect(tabs?.length).toBe(2);
        expect(tabs?.[0].textContent).toContain('Active Rules');
        expect(tabs?.[1].textContent).toContain('Suggested Rules');
    });

    it('should show suggestions when Suggested Rules tab is clicked', async () => {
        await element.updateComplete;
        const suggestionsTab = element.shadowRoot?.querySelectorAll('.tab-btn')[1] as HTMLButtonElement;
        suggestionsTab.click();
        await element.updateComplete;

        const table = element.shadowRoot?.querySelector('table');
        expect(table).toBeTruthy();

        // Should show suggestion columns
        const headers = element.shadowRoot?.querySelectorAll('th');
        expect(headers?.[0].textContent).toContain('Pattern'); // Or Description
        expect(headers?.[1].textContent).toContain('Suggested Category');

        const rows = element.shadowRoot?.querySelectorAll('tbody tr');
        expect(rows?.length).toBe(2);
        expect(rows?.[0].textContent).toContain('Netflix');
    });

    it('should call addRule when approving a suggestion', async () => {
        // Switch to suggestions tab
        await element.updateComplete;
        const suggestionsTab = element.shadowRoot?.querySelectorAll('.tab-btn')[1] as HTMLButtonElement;
        suggestionsTab.click();
        await element.updateComplete;

        // Spy on budgetStore.addRule
        const addRuleSpy = vi.spyOn(budgetStore, 'addRule');

        // Click approve button on first row
        const approveBtn = element.shadowRoot?.querySelector('.btn-approve') as HTMLButtonElement;
        expect(approveBtn).toBeTruthy();
        approveBtn.click();

        expect(addRuleSpy).toHaveBeenCalledWith('Netflix', 'Entertainment');
    });
});
