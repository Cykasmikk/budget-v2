import { ChartConfiguration } from 'chart.js';

/**
 * View mode types for analysis views
 */
export type ViewMode = 'category' | 'project' | 'forecast' | 'simulator' | 'chat' | 'lifecycle';

/**
 * Chat message interface
 */
export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

/**
 * Chart.js configuration type
 */
export type ChartConfig = ChartConfiguration;

/**
 * Chart.js context type for callbacks
 */
export interface ChartContext {
    p1DataIndex: number;
    dataIndex: number;
    datasetIndex: number;
    chart: any; // Chart.js Chart instance - using any here as Chart.js types are complex
}

/**
 * Rule input interface for validation
 */
export interface RuleInput {
    pattern: string;
    category: string;
}

/**
 * SSO authentication configuration
 */
export interface AuthConfig {
    enabled: boolean;
    issuer_url: string;
    client_id: string;
    client_secret: string;
}

/**
 * Merchant data structure
 */
export interface Merchant {
    name: string;
    amount: number;
}

/**
 * Chart data structure for different view modes
 */
export type ChartData = 
    | Record<string, number>  // Category/Project breakdown
    | Array<{ month: string; amount: number; is_forecast: boolean }>  // Single trend line
    | Record<string, Array<{ month: string; amount: number; is_forecast: boolean }>>;  // Multi-line forecast

/**
 * Query result interface
 */
export interface QueryResult {
    answer: string;
    type: string;
    data: Record<string, unknown> | Array<unknown>;
}

/**
 * Simulation result interface
 */
export interface SimulationResult {
    current_total: number;
    simulated_total: number;
    savings: number;
    breakdown: Record<string, number>;
}

/**
 * History item structure
 */
export interface HistoryItem {
    month: string;
    amount: number;
    is_forecast: boolean;
}

/**
 * History data structure (category or project history)
 */
export type HistoryData = Record<string, HistoryItem[]>;

/**
 * Dictionary type for breakdowns
 */
export type BreakdownDict = Record<string, number>;

/**
 * Double dictionary type for merchant maps
 */
export type MerchantMap = Record<string, Record<string, number>>;

