import { ReactiveController, ReactiveControllerHost } from 'lit';
import { BudgetMetrics } from '../store/budget-store';
import { ChartData, HistoryData, HistoryItem, Merchant, BreakdownDict, ViewMode } from '../types/interfaces';

export class AnalysisController implements ReactiveController {
    host: ReactiveControllerHost;

    // State managed by this controller
    selectedCategory: string | null = null;
    forecastMonths: number = 6;
    showForecast: boolean = true;
    forecastType: 'total' | 'category' | 'project' = 'total';

    constructor(host: ReactiveControllerHost) {
        this.host = host;
        host.addController(this);
    }

    hostConnected() {
        // Subscribe to store improvements if needed
    }

    hostDisconnected() {
        // Cleanup
    }

    // --- Actions ---

    toggleForecast(visible: boolean) {
        this.showForecast = visible;
        this.host.requestUpdate();
    }

    setForecastMonths(months: number) {
        // Validation: Clamp between 1 and 12
        this.forecastMonths = Math.min(Math.max(months, 1), 12);
        this.host.requestUpdate();
    }

    setForecastType(type: 'total' | 'category' | 'project') {
        this.forecastType = type;
        this.host.requestUpdate();
    }

    getTitle(viewMode: ViewMode): string {
        switch (viewMode) {
            case 'forecast':
                return 'Spending Forecast (Aus FY)';
            case 'timeline':
                return 'Timeline';
            case 'chat':
                return 'AI Chat';
            case 'insights':
                return 'AI Insights';
            case 'simulator':
                return 'What-If Simulator';
            default:
                return 'Analysis';
        }
    }

    selectCategory(category: string | null) {
        this.selectedCategory = category;
        this.host.requestUpdate();
    }

    // --- Computed Data Helpers ---

    private getForecastData(metrics: BudgetMetrics): { data: ChartData; isDrillDown: boolean } {
        let history: HistoryItem[] | HistoryData = metrics.monthly_trend || [];
        if (this.forecastType === 'category') history = metrics.category_history || {};
        if (this.forecastType === 'project') history = metrics.project_history || {};

        const sliceForecast = (list: HistoryItem[]): HistoryItem[] => {
            const actuals = list.filter(x => !x.is_forecast);
            const forecasts = list.filter(x => x.is_forecast);
            return [...actuals, ...forecasts.slice(0, this.forecastMonths)];
        };

        if (!this.showForecast) {
            // Actuals Only
            if (Array.isArray(history)) {
                return { data: history.filter((x: HistoryItem) => !x.is_forecast), isDrillDown: false };
            } else {
                const data: HistoryData = {};
                Object.entries(history).forEach(([k, v]: [string, HistoryItem[]]) => {
                    data[k] = v.filter((x: HistoryItem) => !x.is_forecast);
                });
                return { data, isDrillDown: false };
            }
        } else {
            // Dynamic Extrapolation
            if (Array.isArray(history)) {
                return { data: sliceForecast(history), isDrillDown: false };
            } else {
                const data: HistoryData = {};
                Object.entries(history).forEach(([k, v]: [string, HistoryItem[]]) => {
                    data[k] = sliceForecast(v);
                });
                return { data, isDrillDown: false };
            }
        }
    }




    private getStandardViewData(viewMode: string, metrics: BudgetMetrics): { data: BreakdownDict; allMerchants: Merchant[]; isDrillDown: boolean } {
        // Convert top_merchants (Record<string, number>) to Merchant[]
        let allMerchants: Merchant[] = Object.entries(metrics.top_merchants || {}).map(([name, amount]) => ({ name, amount: Number(amount) })).sort((a, b) => b.amount - a.amount);
        let data: BreakdownDict = viewMode === 'project' ? metrics.project_breakdown : metrics.category_breakdown;
        let isDrillDown = false;

        // Drill Down Logic
        if (this.selectedCategory) {
            isDrillDown = true;
            if (viewMode === 'category' && metrics.category_merchants?.[this.selectedCategory]) {
                allMerchants = Object.entries(metrics.category_merchants[this.selectedCategory]).map(([name, amount]) => ({ name, amount: Number(amount) }));
            } else if (viewMode === 'project' && metrics.project_merchants?.[this.selectedCategory]) {
                allMerchants = Object.entries(metrics.project_merchants[this.selectedCategory]).map(([name, amount]) => ({ name, amount: Number(amount) }));
            }

            // Sort and Transform for Chart
            allMerchants.sort((a, b) => b.amount - a.amount);
            const drillDownData: BreakdownDict = {};
            allMerchants.forEach((merchant) => { drillDownData[merchant.name] = merchant.amount; });
            data = drillDownData;
        }

        return { data, allMerchants, isDrillDown };
    }

    getChartData(viewMode: string, metrics: BudgetMetrics): { data: ChartData; allMerchants: Merchant[]; isDrillDown: boolean } {
        // 1. Forecast View
        if (viewMode === 'forecast') {
            const result = this.getForecastData(metrics);
            return { ...result, allMerchants: [] };
        }

        // 2. Standard Views (Category/Project)
        return this.getStandardViewData(viewMode, metrics);
    }
}
