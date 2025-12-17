import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SimulatorWidget } from './simulator-widget';
import { budgetService } from '../../services/budget.service';

// Mock the API service
vi.mock('../../services/budget.service', () => ({
    budgetService: {
        parseScenario: vi.fn()
    }
}));

describe('SimulatorWidget Neuro-Symbolic Features', () => {
    let element: SimulatorWidget;

    beforeEach(() => {
        vi.resetAllMocks();
        element = new SimulatorWidget();
        document.body.appendChild(element);
    });

    it('should calculate deterministic savings for simple scenario', async () => {
        // Setup API mock
        (budgetService.parseScenario as any).mockResolvedValue({
            action: 'reduce',
            target: 'Dining',
            amount: 20.0,
            unit: 'percent'
        });

        // Mock BudgetStore state
        const { budgetStore } = await import('../../store/budget-store');

        // Setup mock metrics with a known category
        // @ts-ignore - manipulating private/readonly state for test
        budgetStore.store.setState({
            ...budgetStore.state,
            metrics: {
                ...budgetStore.state.metrics,
                total_expenses: 1000,
                category_breakdown: {
                    'Dining': 500,
                    'Software': 200
                }
            }
        });

        // Set input
        element.scenarioInput = 'Cut Dining by 20%';
        await element.updateComplete;

        // Run simulation directly (since it's async now)
        await element.runSimulation();
        await element.updateComplete;

        // Check symbolic result
        // 20% of 500 = 100
        const savings = element.shadowRoot?.querySelector('.savings');
        expect(savings?.textContent).toContain('$100.00');
    });
});
