import { Store } from '@tanstack/store';

export interface Transaction {
    id: number;
    date: string;
    description: string;
    amount: number;
    category: string;
    type: 'income' | 'expense';
}

export interface Metrics {
    total_income: number;
    total_expense: number;
    balance: number;
}

interface BudgetState {
    transactions: Transaction[];
    metrics: Metrics;
    isLoading: boolean;
    error: string | null;
}

export const budgetStore = new Store<BudgetState>({
    transactions: [],
    metrics: { total_income: 0, total_expense: 0, balance: 0 },
    isLoading: false,
    error: null,
});

export const actions = {
    async fetchDashboard() {
        budgetStore.setState((state) => ({ ...state, isLoading: true, error: null }));
        try {
            const response = await fetch('http://localhost:8000/api/v1/dashboard');
            if (!response.ok) throw new Error('Failed to fetch dashboard');
            const data = await response.json();
            budgetStore.setState((state) => ({
                ...state,
                transactions: data.transactions,
                metrics: data.metrics,
                isLoading: false,
            }));
        } catch (err: any) {
            budgetStore.setState((state) => ({ ...state, isLoading: false, error: err.message }));
        }
    },

    async uploadFile(file: File) {
        budgetStore.setState((state) => ({ ...state, isLoading: true, error: null }));
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/api/v1/upload', {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Upload failed');
            }
            await this.fetchDashboard();
        } catch (err: any) {
            budgetStore.setState((state) => ({ ...state, isLoading: false, error: err.message }));
            throw err;
        }
    },
};
