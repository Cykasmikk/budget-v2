import { SimulatorAction, ScenarioPlan } from '../types/interfaces';

export interface BudgetRule {
    id: number;
    pattern: string;
    category: string;
}

export class BudgetService {
    private static instance: BudgetService;
    private baseUrl = '/api/v1';

    private constructor() { }

    static getInstance(): BudgetService {
        if (!BudgetService.instance) {
            BudgetService.instance = new BudgetService();
        }
        return BudgetService.instance;
    }

    async queryBudget(query: string): Promise<any> {
        const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        if (!response.ok) throw new Error('Query failed');
        return response.json();
    }

    async fetchRules(): Promise<BudgetRule[]> {
        const response = await fetch(`${this.baseUrl}/rules`);
        if (!response.ok) throw new Error('Failed to fetch rules');
        return response.json();
    }

    async addRule(pattern: string, category: string): Promise<void> {
        const response = await fetch(`${this.baseUrl}/rules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pattern, category })
        });
        if (!response.ok) throw new Error('Failed to add rule');
    }

    async deleteRule(id: number): Promise<void> {
        const response = await fetch(`${this.baseUrl}/rules/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete rule');
    }

    async parseScenario(scenario: string): Promise<SimulatorAction> {
        const response = await fetch(`${this.baseUrl}/ai/simulator/parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario })
        });
        if (!response.ok) throw new Error('Failed to parse scenario');
        const json = await response.json();
        return json.data;
    }

    async planSimulation(scenario: string): Promise<ScenarioPlan> {
        const response = await fetch(`${this.baseUrl}/ai/simulator/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario })
        });
        if (!response.ok) throw new Error('Failed to plan simulation');
        const json = await response.json();
        return json.data;
    }
}

export const budgetService = BudgetService.getInstance();
