
export interface BudgetRule {
    id: number;
    pattern: string;
    category: string;
}

export interface SimulationResult {
    current_total: number;
    simulated_total: number;
    savings: number;
    breakdown: Record<string, number>;
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

    async simulateBudget(adjustments: Array<{ category: string; percentage: number }>): Promise<SimulationResult> {
        const response = await fetch(`${this.baseUrl}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(adjustments)
        });
        if (!response.ok) throw new Error('Simulation failed');
        return response.json();
    }
}

export const budgetService = BudgetService.getInstance();
