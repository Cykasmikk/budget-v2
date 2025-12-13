import { describe, it, expect, beforeEach } from 'vitest';
import { BudgetStore, UploadedFile, BudgetMetrics } from './budget-store';

// Helper to create mock metrics
const createMetrics = (total: number, categoryVal: number): BudgetMetrics => ({
    total_expenses: total,
    category_breakdown: { 'Test': categoryVal },
    project_breakdown: {},
    top_merchants: {},
    gaps: [],
    flash_fill: [],
    subscriptions: [],
    anomalies: [],
    monthly_trend: [],
    category_history: {},
    project_history: {},
    category_vendors: {},
    project_vendors: {},
    category_merchants: {},
    project_merchants: {}
});

describe('BudgetStore Merge Logic', () => {
    let store: BudgetStore;

    beforeEach(() => {
        localStorage.clear();
        store = new BudgetStore();
        // Reset strategy to default to avoid state leakage
        store.setMergeStrategy('latest');
    });

    it('should default to latest strategy', () => {
        expect(store.state.mergeStrategy).toBe('latest');
    });

    it('LATEST strategy should return data from the newest file', () => {
        const file1: UploadedFile = {
            id: '1', name: 'Old', uploadDate: '2023-01-01', size: '1KB',
            data: createMetrics(100, 10)
        };
        const file2: UploadedFile = {
            id: '2', name: 'New', uploadDate: '2023-01-02', size: '1KB',
            data: createMetrics(200, 20)
        };

        store.addUploadedFile(file1);
        store.addUploadedFile(file2);

        // Default is latest
        expect(store.state.metrics.total_expenses).toBe(200);
        expect(store.state.metrics.category_breakdown['Test']).toBe(20);
    });

    it('COMBINED strategy should sum values', () => {
        const file1: UploadedFile = {
            id: '1', name: 'A', uploadDate: '2023', size: '1KB',
            data: createMetrics(100, 10)
        };
        const file2: UploadedFile = {
            id: '2', name: 'B', uploadDate: '2023', size: '1KB',
            data: createMetrics(200, 20)
        };

        store.addUploadedFile(file1);
        store.addUploadedFile(file2);
        store.setMergeStrategy('combined');

        expect(store.state.metrics.total_expenses).toBe(300);
        expect(store.state.metrics.category_breakdown['Test']).toBe(30);
    });

    it('BLENDED strategy should fill gaps from older files', () => {
        const file1: UploadedFile = { // Older
            id: '1', name: 'Old', uploadDate: '2023', size: '1KB',
            data: {
                ...createMetrics(100, 10), // Base
                category_breakdown: { 'Common': 10, 'OldOnly': 50 }
            }
        };
        const file2: UploadedFile = { // Newer
            id: '2', name: 'New', uploadDate: '2024', size: '1KB',
            data: {
                ...createMetrics(200, 20),
                category_breakdown: { 'Common': 20, 'NewOnly': 60 }
            }
        };

        store.addUploadedFile(file1);
        store.addUploadedFile(file2);
        store.setMergeStrategy('blended');

        // Should have NewOnly (60) and Common (20 from New)
        // Should have filled OldOnly (50) and added it to total?
        // Logic says: if missing, add val and add to total.
        // Base total (New) = 200 (includes Common:20 + NewOnly:60 + maybe others = 120 gap? no createMetrics sets total explicitly)
        // Wait, createMetrics(200, 20) sets total=200, but breakdown only has 'Test':20.
        // My manual overrides above didn't update total.
        // Let's rely on the logic:
        // Blended starts with File2 metrics (Total 200).
        // It sees 'OldOnly' in File1. Adds it to breakdown. Adds 50 to total.
        // Final Total should be 200 + 50 = 250.
        // Breakdown: Common=20 (from New), NewOnly=60, OldOnly=50.

        expect(store.state.metrics.category_breakdown['Common']).toBe(20);
        expect(store.state.metrics.category_breakdown['NewOnly']).toBe(60);
        expect(store.state.metrics.category_breakdown['OldOnly']).toBe(50);
        expect(store.state.metrics.total_expenses).toBe(250);
    });

    it('COMBINED strategy should merge trend history by summing matching months', () => {
        const history1 = [
            { month: 'Jan 2024', amount: 100, is_forecast: false },
            { month: 'Feb 2024', amount: 150, is_forecast: false }
        ];
        const history2 = [
            { month: 'Jan 2024', amount: 50, is_forecast: false }, // Should sum to 150
            { month: 'Mar 2024', amount: 200, is_forecast: false }  // Should be added
        ];

        const file1: UploadedFile = {
            id: '1', name: 'A', uploadDate: '2023', size: '1KB',
            data: { ...createMetrics(100, 10), monthly_trend: history1 }
        };
        const file2: UploadedFile = {
            id: '2', name: 'B', uploadDate: '2023', size: '1KB',
            data: { ...createMetrics(200, 20), monthly_trend: history2 }
        };

        store.addUploadedFile(file1);
        store.addUploadedFile(file2);
        store.setMergeStrategy('combined');

        const trends = store.state.metrics.monthly_trend;
        // Map by month for easy check
        const trendMap = new Map(trends.map(t => [t.month, t.amount]));

        expect(trendMap.get('Jan 2024')).toBe(150);
        expect(trendMap.get('Feb 2024')).toBe(150);
        expect(trendMap.get('Mar 2024')).toBe(200);
        expect(trendMap.get('Mar 2024')).toBe(200);
        expect(trends.length).toBe(3);
    });

    it('should remove file and recalculate metrics', () => {
        const file1: UploadedFile = {
            id: '1', name: 'A', uploadDate: '2023', size: '1KB',
            data: createMetrics(100, 10)
        };
        const file2: UploadedFile = {
            id: '2', name: 'B', uploadDate: '2023', size: '1KB',
            data: createMetrics(200, 20)
        };

        store.addUploadedFile(file1);
        store.addUploadedFile(file2);

        // Initial state: Latest = 200
        expect(store.state.metrics.total_expenses).toBe(200);

        store.removeUploadedFile('2');

        // New state: Should revert to last available file (file1)
        expect(store.state.uploadedFiles.length).toBe(1);
        expect(store.state.metrics.total_expenses).toBe(100);

        store.removeUploadedFile('1');

        // Empty state
        expect(store.state.uploadedFiles.length).toBe(0);
        expect(store.state.metrics.total_expenses).toBe(0);
    });
});

