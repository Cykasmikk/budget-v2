import { Store } from '@tanstack/store';
import { budgetService } from '../services/budget.service';
import { generateMockData, generatePartialMockData } from '../utils/mock-data';
import { QueryResult, BreakdownDict, MerchantMap, HistoryData, HistoryItem, ForecastSummary, TimelineItem } from '../types/interfaces';
import { logger } from '../services/logger';
import { ForecastService } from '../utils/forecast';

export interface Transaction {
    date: string;
    category: string;
    amount: number;
    description: string;
}

export interface Subscription {
    description: string;
    amount: number;
    frequency: string;
    category?: string;
    start_date?: string;
    next_payment_date?: string;
    status?: string;
}

export interface BudgetMetrics {
    total_expenses: number;
    category_breakdown: Record<string, number>;
    project_breakdown: Record<string, number>;
    top_merchants: Record<string, number>;
    gaps: Array<{ start_date: string; end_date: string; days: number }>;
    flash_fill: Array<{ description: string; suggested_category: string; count: number }>;
    subscriptions: Array<Subscription>;
    anomalies: Array<{ description: string; date: string; amount: number; average: number }>;
    monthly_trend: HistoryItem[];
    category_history: Record<string, HistoryItem[]>;
    project_history: Record<string, HistoryItem[]>;
    
    // Timeline / Gantt
    timeline: Array<TimelineItem>;

    // Dynamic Vendor Maps (Drill-Down)
    category_vendors: Record<string, string[]>;
    project_vendors: Record<string, string[]>;

    // Detailed Merchant Breakdowns (Map<Category, Map<Merchant, Amount>>)
    category_merchants: Record<string, Record<string, number>>;
    project_merchants: Record<string, Record<string, number>>;
    
    // Forecast Summary
    forecast_summary?: ForecastSummary;
}

export interface UploadedFile {
    id: string;
    name: string;
    uploadDate: string;
    size: string;
    data: BudgetMetrics;
}

export type MergeStrategy = 'latest' | 'blended' | 'combined';


export interface AppSettings {
    currency: string;
    forecast_horizon: number;
    theme: string;
    budget_threshold: number;
}

export interface BudgetState {
    transactions: Transaction[];
    metrics: BudgetMetrics;
    isLoading: boolean;
    error: string | null;
    budgetLimit: number;
    viewMode: 'category' | 'project' | 'forecast' | 'chat' | 'lifecycle' | 'timeline';
    queryResult: QueryResult | null;
    rules: Array<{ id: number; pattern: string; category: string }>;
    uploadedFiles: UploadedFile[];
    mergeStrategy: MergeStrategy;
    settings: AppSettings; // Persisted settings
}

const initialState: BudgetState = {
    transactions: [],
    metrics: {
        total_expenses: 0,
        category_breakdown: {},
        project_breakdown: {},
        top_merchants: {},
        gaps: [],
        flash_fill: [],
        subscriptions: [],
        anomalies: [],
        monthly_trend: [],
        category_history: {},
        project_history: {},
        
        timeline: [],

        category_vendors: {},
        project_vendors: {},

        category_merchants: {},
        project_merchants: {}
    },
    isLoading: false,
    error: null,
    budgetLimit: 0,
    viewMode: 'category',
    queryResult: null,
    rules: [],
    uploadedFiles: [],
    mergeStrategy: 'latest',
    settings: {
        currency: 'USD',
        forecast_horizon: 6,
        theme: 'dark',
        budget_threshold: 5000
    }
};

export class BudgetStore {
    private store = new Store<BudgetState>(initialState);

    constructor() {
        this.loadFromStorage();
    }

    private saveTimeout: number | null = null;

    private saveToStorage(state: BudgetState) {
        if (this.saveTimeout) {
            window.clearTimeout(this.saveTimeout);
        }

        this.saveTimeout = window.setTimeout(() => {
            try {
                const data = {
                    uploadedFiles: state.uploadedFiles,
                    mergeStrategy: state.mergeStrategy,
                    budgetLimit: state.budgetLimit,
                    demoInitialized: true // Flag to indicate we've run before
                };
                localStorage.setItem('budget_demo_state', JSON.stringify(data));
                this.saveTimeout = null;
            } catch (e) {
                const error = e instanceof Error ? e : new Error(String(e));
                logger.error('Failed to save state', 'BudgetStore', error);
            }
        }, 1000); // 1s debounce
    }

    private loadFromStorage() {
        try {
            const stored = localStorage.getItem('budget_demo_state');
            if (stored) {
                const data = JSON.parse(stored);
                // We must recalculate metrics from stored files
                const metrics = data.uploadedFiles
                    ? this.calculateMetrics(data.uploadedFiles, data.mergeStrategy || 'latest')
                    : initialState.metrics;

                this.store.setState((state) => ({
                    ...state,
                    uploadedFiles: data.uploadedFiles || [],
                    mergeStrategy: data.mergeStrategy || 'latest',
                    budgetLimit: data.budgetLimit || 0,
                    metrics: metrics
                }));
            }
        } catch (e) {
            const error = e instanceof Error ? e : new Error(String(e));
            logger.error('Failed to load state', 'BudgetStore', error);
        }
    }

    get state() {
        return this.store.state;
    }

    getStore() {
        return this.store;
    }

    // Helper to merge history arrays by summing amounts for matching months
    private mergeHistoryArrays(
        base: HistoryItem[],
        incoming: HistoryItem[]
    ) {
        const mergedMap = new Map<string, HistoryItem>();

        // Index base
        base.forEach(item => mergedMap.set(item.month, { ...item }));

        // Merge incoming
        incoming.forEach(item => {
            if (mergedMap.has(item.month)) {
                const existing = mergedMap.get(item.month)!;
                existing.amount += item.amount;
                // If any source is actual data (false), the merged point is actual (false)
                existing.is_forecast = existing.is_forecast && item.is_forecast;
            } else {
                mergedMap.set(item.month, { ...item });
            }
        });

        // Convert back to array (could sort by date if needed, but assuming order is preserved or handled by chart)
        return Array.from(mergedMap.values());
    }


    // Helper functions for merging strategies
    private mergeCategoryBreakdown(source: BreakdownDict, target: BreakdownDict): void {
        Object.entries(source || {}).forEach(([key, val]) => {
            target[key] = (target[key] || 0) + Number(val);
        });
    }

    private mergeProjectBreakdown(source: BreakdownDict, target: BreakdownDict): void {
        Object.entries(source || {}).forEach(([key, val]) => {
            target[key] = (target[key] || 0) + Number(val);
        });
    }

    private mergeMerchantMaps(source: MerchantMap, target: MerchantMap): void {
        Object.entries(source || {}).forEach(([k1, v1]: [string, Record<string, number>]) => {
            if (!target[k1]) target[k1] = {};
            Object.entries(v1 || {}).forEach(([k2, v2]) => {
                target[k1][k2] = (target[k1][k2] || 0) + Number(v2);
            });
        });
    }

    private mergeVendorArrays(source: Record<string, string[]>, target: Record<string, string[]>): void {
        Object.entries(source || {}).forEach(([k, arr]) => {
            if (!target[k]) target[k] = [];
            target[k] = Array.from(new Set([...target[k], ...arr]));
        });
    }

    private recalculateMonthlyTrend(blended: BudgetMetrics): void {
        const trendMap = new Map<string, HistoryItem>();

        Object.values(blended.category_history).forEach((history: HistoryItem[]) => {
            history.forEach((item: HistoryItem) => {
                if (trendMap.has(item.month)) {
                    trendMap.get(item.month)!.amount += item.amount;
                } else {
                    trendMap.set(item.month, { ...item });
                }
            });
        });

        blended.monthly_trend = Array.from(trendMap.values())
            .sort((a, b) => new Date(a.month).getTime() - new Date(b.month).getTime());
    }

    private mergeCombinedStrategy(files: UploadedFile[]): BudgetMetrics {
        const combined = JSON.parse(JSON.stringify(initialState.metrics));

        files.forEach(file => {
            const data = file.data;
            combined.total_expenses += Number(data.total_expenses || 0);

            this.mergeCategoryBreakdown(data.category_breakdown || {}, combined.category_breakdown);
            this.mergeProjectBreakdown(data.project_breakdown || {}, combined.project_breakdown);

            Object.entries(data.top_merchants || {}).forEach(([key, val]) => {
                combined.top_merchants[key] = (combined.top_merchants[key] || 0) + Number(val);
            });

            // Deduplicate Arrays
            const mergeUnique = (base: any[], incoming: any[], keyFn: (item: any) => string) => {
                const map = new Map(base.map(i => [keyFn(i), i]));
                incoming.forEach(i => map.set(keyFn(i), i));
                return Array.from(map.values());
            };

            combined.gaps = mergeUnique(combined.gaps, data.gaps || [], (i) => `${i.start_date}_${i.end_date}`);
            combined.flash_fill = mergeUnique(combined.flash_fill, data.flash_fill || [], (i) => i.description);
            combined.subscriptions = mergeUnique(combined.subscriptions, data.subscriptions || [], (i) => `${i.description}_${i.amount}`);
            combined.timeline = mergeUnique(combined.timeline, data.timeline || [], (i) => i.id);
            combined.anomalies = mergeUnique(combined.anomalies, data.anomalies || [], (i) => `${i.description}_${i.date}`);

            // Check for date overlap before merging trends
            const combinedDates = combined.monthly_trend.map((x: any) => x.month);
            const incomingDates = (data.monthly_trend || []).map((x: any) => x.month);
            const overlap = combinedDates.filter((d: string) => incomingDates.includes(d));
            
            if (overlap.length > 0) {
                const msg = `Cannot combine files: Date overlap detected in ${overlap.join(', ')}. Use 'Blended' strategy or remove overlapping files.`;
                logger.error(msg, 'BudgetStore');
                throw new Error(msg);
            }

            combined.monthly_trend = this.mergeHistoryArrays(combined.monthly_trend, data.monthly_trend || []);

            Object.entries(data.category_history || {}).forEach(([cat, history]) => {
                if (!combined.category_history[cat]) {
                    combined.category_history[cat] = history;
                } else {
                    combined.category_history[cat] = this.mergeHistoryArrays(combined.category_history[cat], history);
                }
            });

            Object.entries(data.project_history || {}).forEach(([proj, history]) => {
                if (!combined.project_history[proj]) {
                    combined.project_history[proj] = history;
                } else {
                    combined.project_history[proj] = this.mergeHistoryArrays(combined.project_history[proj], history);
                }
            });

            this.mergeMerchantMaps(data.category_merchants || {}, combined.category_merchants);
            this.mergeMerchantMaps(data.project_merchants || {}, combined.project_merchants);
            this.mergeVendorArrays(data.category_vendors || {}, combined.category_vendors);
            this.mergeVendorArrays(data.project_vendors || {}, combined.project_vendors);
        });

        return combined;
    }

    private mergeBlendedStrategy(files: UploadedFile[]): BudgetMetrics {
        const reversedFiles = [...files].reverse();
        const blended = JSON.parse(JSON.stringify(reversedFiles[0].data));

        // Ensure blended starts with numbers
        blended.total_expenses = Number(blended.total_expenses);
        Object.keys(blended.category_breakdown).forEach(k => blended.category_breakdown[k] = Number(blended.category_breakdown[k]));
        Object.keys(blended.project_breakdown).forEach(k => blended.project_breakdown[k] = Number(blended.project_breakdown[k]));

        for (let i = 1; i < reversedFiles.length; i++) {
            const data = reversedFiles[i].data;

            Object.entries(data.category_breakdown || {}).forEach(([key, val]) => {
                if (blended.category_breakdown[key] === undefined) {
                    blended.category_breakdown[key] = Number(val);
                }
            });

            Object.entries(data.project_breakdown || {}).forEach(([key, val]) => {
                if (blended.project_breakdown[key] === undefined) {
                    blended.project_breakdown[key] = Number(val);
                }
            });

            Object.entries(data.category_history || {}).forEach(([key, val]) => {
                if (!blended.category_history[key]) {
                    blended.category_history[key] = val;
                }
            });

            Object.entries(data.project_history || {}).forEach(([key, val]) => {
                if (!blended.project_history[key]) {
                    blended.project_history[key] = val;
                }
            });

            // Gap Fill: Merchant Maps
            Object.entries(data.category_merchants || {}).forEach(([cat, merchants]) => {
                if (!blended.category_merchants) blended.category_merchants = {};
                if (!blended.category_merchants[cat]) {
                    blended.category_merchants[cat] = merchants;
                }
            });

            Object.entries(data.project_merchants || {}).forEach(([proj, merchants]) => {
                if (!blended.project_merchants) blended.project_merchants = {};
                if (!blended.project_merchants[proj]) {
                    blended.project_merchants[proj] = merchants;
                }
            });
        }

        // Recalculate total expenses from category breakdown (Source of Truth)
        blended.total_expenses = Object.values(blended.category_breakdown || {})
            .reduce((sum: number, val: any) => sum + Number(val), 0);

        this.recalculateMonthlyTrend(blended);
        return blended;
    }

    // Helper to calculate merged metrics based on strategy
    private calculateMetrics(files: UploadedFile[], strategy: MergeStrategy, overrideHorizon?: number): BudgetMetrics {
        let result = initialState.metrics;

        try {
            if (files.length === 0) {
                result = initialState.metrics;
            } else if (strategy === 'latest' || files.length === 1) {
                result = files[files.length - 1].data;
            } else if (strategy === 'combined') {
                result = this.mergeCombinedStrategy(files);
            } else if (strategy === 'blended') {
                // For blended strategy, ensure files are processed chronologically (oldest first)
                const sortedFiles = [...files].sort((a, b) => {
                    const monthA = a.data.monthly_trend?.[0]?.sort_key || '';
                    const monthB = b.data.monthly_trend?.[0]?.sort_key || '';
                    return monthA.localeCompare(monthB);
                });
                result = this.mergeBlendedStrategy(sortedFiles);
            }
        } catch (e) {
            const error = e instanceof Error ? e : new Error(String(e));
            logger.error('Error calculating metrics', 'BudgetStore', error);
            // Fallback to latest if available
            if (files.length > 0) {
                result = files[files.length - 1].data;
            }
        }

        // Recalculate Forecast Summary based on merged trend
        if (result.monthly_trend && result.monthly_trend.length > 0) {
            const horizon = overrideHorizon ?? (this.store.state.settings?.forecast_horizon || 6);
            result.forecast_summary = ForecastService.generateSummary(result.monthly_trend, horizon);
        }

        this.validateMetrics(result);
        return result;
    }

    private validateMetrics(metrics: BudgetMetrics) {
        const categorySum = Object.values(metrics.category_breakdown || {})
            .reduce((sum, val) => sum + Number(val), 0);

        const tolerance = 0.1; // Allow small float error
        if (Math.abs(categorySum - metrics.total_expenses) > tolerance) {
            logger.warn('Metrics validation failed: Total Expenses does not match Category Breakdown sum', 'BudgetStore', {
                categorySum,
                total_expenses: metrics.total_expenses,
                diff: categorySum - metrics.total_expenses
            });
        }
    }

    setMergeStrategy(strategy: MergeStrategy) {
        this.store.setState((state) => {
            const newState = {
                ...state,
                mergeStrategy: strategy,
                metrics: this.calculateMetrics(state.uploadedFiles, strategy)
            };
            this.saveToStorage(newState);
            // Persist to backend
            this.updateSettings({ merge_strategy: strategy } as Partial<AppSettings>);
            return newState;
        });
    }

    addUploadedFile(file: UploadedFile) {
        this.store.setState((state) => {
            const newFiles = [...state.uploadedFiles, file];
            const newState = {
                ...state,
                uploadedFiles: newFiles,
                metrics: this.calculateMetrics(newFiles, state.mergeStrategy)
            };
            this.saveToStorage(newState);
            return newState;
        });
    }

    removeUploadedFile(id: string) {
        this.store.setState((state) => {
            const newFiles = state.uploadedFiles.filter(f => f.id !== id);
            const newState = {
                ...state,
                uploadedFiles: newFiles,
                metrics: this.calculateMetrics(newFiles, state.mergeStrategy)
            };
            this.saveToStorage(newState);
            return newState;
        });
    }

    setData(data: { transactions: Transaction[], metrics: BudgetMetrics }, fileName?: string, fileSize?: string) {
        // Sanitize incoming data (backend might return strings for Decimals)
        // We must rigorously convert EVERY field to Number to prevent chart crashes.
        const raw = data.metrics;
        logger.debug('Raw metrics received', 'BudgetStore', {
            trendLength: raw.monthly_trend?.length,
            hasForecast: raw.monthly_trend?.some(x => x.is_forecast),
            sample: raw.monthly_trend?.slice(-3)
        });

        const sanitizedMetrics: BudgetMetrics = {
            total_expenses: Number(raw.total_expenses || 0),

            // Simple Dictionaries
            category_breakdown: {},
            project_breakdown: {},
            top_merchants: {},

            // Nested Arrays/Objects
            monthly_trend: (raw.monthly_trend || []).map(item => ({
                ...item,
                amount: Number(item.amount || 0),
                is_forecast: !!item.is_forecast,
                sort_key: item.sort_key || ""
            })),

            category_history: {},
            project_history: {},

            category_vendors: raw.category_vendors || {},
            project_vendors: raw.project_vendors || {},

            category_merchants: {},
            project_merchants: {},

            gaps: raw.gaps || [],
            flash_fill: raw.flash_fill || [],

            subscriptions: (raw.subscriptions || []).map(s => ({
                ...s,
                amount: Number(s.amount || 0)
            })),

            timeline: (raw.timeline || []).map(t => ({
                ...t,
                amount: Number(t.amount || 0)
            })),

            anomalies: (raw.anomalies || []).map(a => ({
                ...a,
                amount: Number(a.amount || 0),
                average: Number(a.average || 0)
            })),
            
            // Pass through Forecast Summary if present
            forecast_summary: raw.forecast_summary
        };

        // Populate Dictionaries
        const sanitizeDict = (source: BreakdownDict | undefined, target: BreakdownDict) => {
            if (!source) return;
            Object.entries(source).forEach(([k, v]) => {
                target[k] = Number(v);
            });
        };

        sanitizeDict(raw.category_breakdown, sanitizedMetrics.category_breakdown);
        sanitizeDict(raw.project_breakdown, sanitizedMetrics.project_breakdown);
        sanitizeDict(raw.top_merchants, sanitizedMetrics.top_merchants);

        // Populate Histories
        const sanitizeHistory = (source: HistoryData | undefined, target: HistoryData) => {
            if (!source) return;
            Object.entries(source).forEach(([k, list]: [string, HistoryItem[] | unknown]) => {
                if (Array.isArray(list)) {
                    target[k] = list.map((item: HistoryItem) => ({
                        ...item,
                        amount: Number(item.amount || 0),
                        is_forecast: !!item.is_forecast, // Force boolean
                        sort_key: item.sort_key || ""
                    }));
                }
            });
        };

        sanitizeHistory(raw.category_history, sanitizedMetrics.category_history);
        sanitizeHistory(raw.project_history, sanitizedMetrics.project_history);

        // Sanitize Monthly Trend too (Redundant but safe if raw format changes, handled above in initialization)
        // sanitizedMetrics.monthly_trend = ... (Already done)

        // Populate Granular Merchant Maps
        const sanitizeDoubleDict = (source: MerchantMap | undefined, target: MerchantMap) => {
            if (!source) return;
            Object.entries(source).forEach(([k1, v1]: [string, Record<string, number>]) => {
                target[k1] = {};
                Object.entries(v1).forEach(([k2, v2]) => {
                    target[k1][k2] = Number(v2);
                });
            });
        };

        sanitizeDoubleDict(raw.category_merchants, sanitizedMetrics.category_merchants);
        sanitizeDoubleDict(raw.project_merchants, sanitizedMetrics.project_merchants);

        // When setting data directly (e.g. from upload), we add it as a file
        const newFile: UploadedFile = {
            id: Date.now().toString(),
            name: fileName || `Upload ${new Date().toLocaleTimeString()}`,
            uploadDate: new Date().toLocaleDateString(),
            size: fileSize || 'Unknown',
            data: sanitizedMetrics
        };
        this.addUploadedFile(newFile);
    }

    setLoading(isLoading: boolean) {
        this.store.setState((state) => ({
            ...state,
            isLoading
        }));
    }

    setError(error: string) {
        this.store.setState((state) => ({
            ...state,
            isLoading: false,
            error
        }));
    }

    setBudgetLimit(limit: number) {
        this.store.setState((state) => {
            const newState = { ...state, budgetLimit: limit };
            this.saveToStorage(newState);
            return newState;
        });
    }

    setViewMode(mode: 'category' | 'project' | 'forecast' | 'chat' | 'lifecycle' | 'timeline') {
        this.store.setState((state) => ({
            ...state,
            viewMode: mode
        }));
    }
    // ... (queryBudget, fetchRules, addRule, deleteRule, simulateBudget implementations remain similar)
    async queryBudget(query: string) {
        this.store.setState((state) => ({ ...state, isLoading: true, error: null }));
        try {
            const result = await budgetService.queryBudget(query);
            this.store.setState((state) => ({ ...state, queryResult: result, isLoading: false }));
        } catch (error) {
            this.store.setState((state) => ({ ...state, error: (error as Error).message, isLoading: false }));
        }
    }

    async fetchRules() {
        try {
            const rules = await budgetService.fetchRules();
            this.store.setState((state) => ({ ...state, rules }));
        } catch (error) {
            const errorObj = error instanceof Error ? error : new Error(String(error));
            logger.error('Failed to fetch rules', 'BudgetStore', errorObj);
        }
    }

    async addRule(pattern: string, category: string) {
        try {
            await budgetService.addRule(pattern, category);
            await this.fetchRules();
        } catch (error) {
            const errorObj = error instanceof Error ? error : new Error(String(error));
            logger.error('Failed to add rule', 'BudgetStore', errorObj);
        }
    }

    async deleteRule(id: number) {
        try {
            await budgetService.deleteRule(id);
            await this.fetchRules();
        } catch (error) {
            const errorObj = error instanceof Error ? error : new Error(String(error));
            logger.error('Failed to delete rule', 'BudgetStore', errorObj);
        }
    }

    loadSampleData(variant?: string) {
        this.store.setState((state) => ({ ...state, isLoading: true }));
        if (variant) logger.debug('Loading variant', 'BudgetStore', { variant });
        try {
            const data = generateMockData();
            const sampleFile: UploadedFile = {
                id: 'sample-data',
                name: 'Sample Cloud Budget',
                uploadDate: new Date().toLocaleDateString(),
                size: '1.2 MB',
                data: data
            };

            const annualLimit = 66000000;
            const currentState = this.store.state;

            // Filter out existing sample data (deduplication)
            const existingFiles = currentState.uploadedFiles.filter(f => f.id !== 'sample-data');
            const newFiles = [...existingFiles, sampleFile];

            const newState = {
                ...currentState,
                uploadedFiles: newFiles,
                metrics: this.calculateMetrics(newFiles, currentState.mergeStrategy),
                budgetLimit: annualLimit,
                isLoading: false,
                error: null
            };

            this.store.setState(() => newState);
            this.saveToStorage(newState);

        } catch (error) {
            this.store.setState((state) => ({ ...state, error: 'Failed to load sample data', isLoading: false }));
        }
    }

    loadPartialData() {
        this.store.setState((state) => ({ ...state, isLoading: true }));
        try {
            const data = generatePartialMockData();
            const partialFile: UploadedFile = {
                id: 'partial-update',
                name: 'Partial Cloud Update (Apr)',
                uploadDate: new Date().toLocaleDateString(),
                size: '150 KB',
                data: data
            };

            const currentState = this.store.state;
            const existingFiles = currentState.uploadedFiles.filter(f => f.id !== 'partial-update');
            const newFiles = [...existingFiles, partialFile];

            const newState = {
                ...currentState,
                uploadedFiles: newFiles,
                metrics: this.calculateMetrics(newFiles, currentState.mergeStrategy),
                isLoading: false,
                error: null
            };

            this.store.setState(() => newState);
            this.saveToStorage(newState);
        } catch (error) {
            this.store.setState((state) => ({ ...state, error: 'Failed to load partial data', isLoading: false }));
        }
    }

    // Settings Logic
    async fetchSettings() {
        try {
            const response = await fetch('/api/v1/settings');
            if (response.ok) {
                const data = await response.json();
                // Backend now returns { settings: {...}, auth_config: {...} }
                const incomingSettings = data.settings || data;

                this.store.setState((state) => ({
                    ...state,
                    settings: {
                        ...state.settings,
                        ...incomingSettings
                    }
                }));

                // Sync properties
                if (incomingSettings.merge_strategy) {
                    this.store.setState((state) => ({
                        ...state,
                        mergeStrategy: incomingSettings.merge_strategy,
                        // Re-calc metrics if strategy changed? Yes.
                        metrics: this.calculateMetrics(state.uploadedFiles, incomingSettings.merge_strategy)
                    }));
                }

                // Sync budget limit with persisted setting if 0
                if (this.store.state.budgetLimit === 0) {
                    this.store.setState((state) => ({ ...state, budgetLimit: incomingSettings.budget_threshold }));
                }
            }
        } catch (e) {
            const error = e instanceof Error ? e : new Error(String(e));
            logger.error('Failed to fetch settings', 'BudgetStore', error);
        }
    }

    async updateSettings(update: Partial<AppSettings>) {
        try {
            const response = await fetch('/api/v1/settings', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(update)
            });

            if (response.ok) {
                const newSettings = await response.json();
                this.store.setState((state) => {
                    const updatedState = { ...state, settings: newSettings };
                    
                    // Side Effects
                    if (update.budget_threshold) {
                        updatedState.budgetLimit = update.budget_threshold;
                    }

                    // Recalculate metrics if forecast horizon changed
                    if (update.forecast_horizon) {
                        updatedState.metrics = this.calculateMetrics(state.uploadedFiles, state.mergeStrategy, update.forecast_horizon);
                    }
                    
                    return updatedState;
                });
            }
        } catch (e) {
            const error = e instanceof Error ? e : new Error(String(e));
            logger.error('Failed to update settings', 'BudgetStore', error);
        }
    }

    // Data Reset
    async resetData() {
        this.store.setState(s => ({
            ...s,
            uploadedFiles: [],
            metrics: initialState.metrics,
            budgetLimit: 0
        }));
        this.saveToStorage(this.store.state);
        // Also clear local storage completely if requested
        localStorage.removeItem('budget_demo_state');
    }
}

export const budgetStore = new BudgetStore();
