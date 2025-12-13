import { describe, it, expect, beforeEach, vi } from 'vitest';
import { RulesCard } from './rules-card';
import { budgetStore } from '../../store/budget-store';

describe('RulesCard', () => {
    let element: RulesCard;

    beforeEach(() => {
        element = new RulesCard();
        element.rules = [];
        document.body.appendChild(element);
    });

    it('should render rules card', () => {
        const h2 = element.shadowRoot?.querySelector('h2');
        expect(h2).toBeTruthy();
        expect(h2?.textContent).toContain('Categorization Rules');
    });

    it('should render form inputs', () => {
        const inputs = element.shadowRoot?.querySelectorAll('.form-input');
        expect(inputs?.length).toBe(2);
    });

    it('should render add rule button', () => {
        const button = element.shadowRoot?.querySelector('.btn-submit');
        expect(button).toBeTruthy();
        expect(button?.textContent).toContain('Add Rule');
    });

    it('should update pattern value on input', () => {
        const patternInput = element.shadowRoot?.querySelectorAll('.form-input')[0] as HTMLInputElement;
        patternInput.value = '^AWS.*';
        patternInput.dispatchEvent(new Event('input'));
        
        expect(element.pattern).toBe('^AWS.*');
    });

    it('should update category value on input', () => {
        const categoryInput = element.shadowRoot?.querySelectorAll('.form-input')[1] as HTMLInputElement;
        categoryInput.value = 'Cloud Infrastructure';
        categoryInput.dispatchEvent(new Event('input'));
        
        expect(element.category).toBe('Cloud Infrastructure');
    });

    it('should display empty state when no rules', () => {
        element.rules = [];
        element.requestUpdate();
        
        const emptyState = element.shadowRoot?.querySelector('.scroll-content')?.textContent;
        expect(emptyState).toContain('No custom rules');
    });

    it('should display rules table when rules exist', () => {
        element.rules = [
            { id: 1, pattern: '^AWS.*', category: 'Cloud' },
            { id: 2, pattern: '^Azure.*', category: 'Cloud' }
        ];
        element.requestUpdate();
        
        const table = element.shadowRoot?.querySelector('table');
        expect(table).toBeTruthy();
        
        const rows = element.shadowRoot?.querySelectorAll('tbody tr');
        expect(rows?.length).toBe(2);
    });

    it('should call addRule when button is clicked', () => {
        vi.spyOn(budgetStore, 'addRule');
        
        element.pattern = '^AWS.*';
        element.category = 'Cloud';
        
        const button = element.shadowRoot?.querySelector('.btn-submit') as HTMLButtonElement;
        button.click();
        
        expect(budgetStore.addRule).toHaveBeenCalledWith('^AWS.*', 'Cloud');
    });
});

