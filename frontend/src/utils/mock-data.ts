import { BudgetMetrics } from '../store/budget-store';

export const VENDOR_CATEGORIES = {
    'Cloud Infrastructure': [
        'Amazon Web Services', 'Azure Cloud', 'Google Cloud Platform',
        'Oracle Cloud Infrastructure', 'DigitalOcean', 'Cloudflare',
        'Akamai', 'Datadog', 'New Relic', 'PagerDuty'
    ],
    'Data Center': [
        'Equinix', 'Digital Realty', 'Iron Mountain', 'NextDC',
        'Schneider Electric', 'Vertiv', 'ComEd Power', 'Level 3 Communications'
    ],
    'Staffing & Contractors': [
        'Randstad Technologies', 'Robert Half', 'TekSystems', 'Hays Specialist Recruitment',
        'Toptal', 'Upwork Enterprise', 'Accenture', 'Deloitte'
    ],
    'Hardware & Networking': [
        'Dell Technologies', 'Hewlett Packard Enterprise', 'Lenovo', 'Cisco Systems',
        'Juniper Networks', 'Arista Networks', 'Palo Alto Networks', 'NetApp', 'Pure Storage'
    ]
};

export const PROJECT_VENDORS = {
    'Cloud Migration 2.0': [
        'Amazon Web Services', 'Azure Cloud', 'Accenture', 'Deloitte', 'Randstad Technologies',
        'Cloudflare', 'Toptal'
    ],
    'Legacy DC Maintenance': [
        'Equinix', 'Digital Realty', 'Dell Technologies', 'Hewlett Packard Enterprise',
        'Schneider Electric', 'Vertiv', 'Cisco Systems', 'ComEd Power'
    ],
    'AI/ML Platform Build': [
        'Google Cloud Platform', 'Oracle Cloud Infrastructure', 'Arista Networks',
        'Pure Storage', 'Datadog', 'Robert Half'
    ],
    'Security Hardening': [
        'Palo Alto Networks', 'Cloudflare', 'Akamai', 'New Relic',
        'PagerDuty', 'Juniper Networks', 'Iron Mountain'
    ]
};

// Deterministic Random Number Generator (Linear Congruential Generator)
class SeededRandom {
    private seed: number;
    constructor(seed: number) { this.seed = seed; }

    // Returns number between 0 and 1
    next() {
        this.seed = (this.seed * 9301 + 49297) % 233280;
        return this.seed / 233280;
    }
}

export const generateMockData = (): BudgetMetrics => {
    // Fixed seed for determinism
    const rng = new SeededRandom(123456);

    // Target: ~$65M Annual
    // Monthly: ~$5.4M

    const vendors = {
        cloud: VENDOR_CATEGORIES['Cloud Infrastructure'],
        datacenter: VENDOR_CATEGORIES['Data Center'],
        staffing: VENDOR_CATEGORIES['Staffing & Contractors'],
        hardware: VENDOR_CATEGORIES['Hardware & Networking']
    };

    // Base monthly allocations (approximate)
    const allocations = {
        cloud: 2160000,     // 40%
        datacenter: 1080000, // 20%
        staffing: 1350000,   // 25%
        hardware: 810000     // 15%
    };

    // Generate Category Breakdown
    const category_breakdown: Record<string, number> = {
        'Cloud Infrastructure': allocations.cloud * 12,
        'Data Center': allocations.datacenter * 12,
        'Staffing & Contractors': allocations.staffing * 12,
        'Hardware & Networking': allocations.hardware * 12,
        'Software Licenses': 500000, // Extra buffer
        'Training & Travel': 250000
    };

    // Generate Top Merchants (Distribute category totals across vendors with some variance)
    const top_merchants: Record<string, number> = {};

    // Helper to distribute amount across vendors
    const distribute = (total: number, vendorList: string[]) => {
        let remaining = total;
        vendorList.forEach((vendor, index) => {
            if (index === vendorList.length - 1) {
                top_merchants[vendor] = remaining;
            } else {
                // Random share for this vendor (pareto principle-ish)
                const share = remaining * (rng.next() * 0.4 + 0.1);
                top_merchants[vendor] = Math.round(share);
                remaining -= top_merchants[vendor];
            }
        });
    };

    distribute(category_breakdown['Cloud Infrastructure'], vendors.cloud);
    distribute(category_breakdown['Data Center'], vendors.datacenter);
    distribute(category_breakdown['Staffing & Contractors'], vendors.staffing);
    distribute(category_breakdown['Hardware & Networking'], vendors.hardware);

    // Generate Monthly Trend (Aust FY: July - June)
    const months = [
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'
    ];

    // Base monthly is ~5.4M. Add some seasonality/growth.
    const monthly_trend = months.map((month, index) => {
        // Simple trend: Start slightly lower, grow over time, spike in June (EOSY)
        const base = 5200000;
        const growth = index * 50000; // Linear growth
        const seasonal = month === 'Jun' ? 800000 : (month === 'Dec' ? -200000 : 0); // June spike, Dec dip
        const random = (rng.next() - 0.5) * 200000; // Random noise

        return {
            month: `${month} 2024`, // Assuming current FY
            amount: Math.round(base + growth + seasonal + random),
            is_forecast: false
        };
    });

    // --- MOCK FORECAST GENERATION (36 Months) ---
    // Mimic Holt's Method (Linear Trend) roughly
    const lastAmount = monthly_trend[monthly_trend.length - 1].amount;
    const avgGrowth = (lastAmount - monthly_trend[0].amount) / 12; // Crude slope

    for (let i = 1; i <= 36; i++) {
        const nextDate = new Date(2025, 6 + i - 1, 1); // Start Jul 2025 (post June 2025)
        const monthName = nextDate.toLocaleString('default', { month: 'short' });
        const year = nextDate.getFullYear();
        const displayMonth = `${monthName} ${year}`;

        const projected = lastAmount + (avgGrowth * i);
        const random = (rng.next() - 0.5) * 100000; // Less noise in forecast

        monthly_trend.push({
            month: displayMonth,
            amount: Math.round(projected + random),
            is_forecast: true
        });
    }


    // Adjust total expenses to match the sum of monthly trend for consistency (Actuals only)
    const total_expenses = monthly_trend.filter(x => !x.is_forecast).reduce((sum, item) => sum + item.amount, 0);

    // Generate History Breakdown Helper
    const generateHistory = (breakdown: Record<string, number>) => {
        const history: Record<string, Array<{ month: string; amount: number; is_forecast: boolean }>> = {};

        Object.entries(breakdown).forEach(([key, totalAnnual]) => {
            const monthlyBase = totalAnnual / 12;
            const trendLine: any[] = months.map((month, index) => {
                const growth = index * (monthlyBase * 0.02); // 2% growth
                const random = (rng.next() - 0.5) * (monthlyBase * 0.1); // +/- 5% variance
                return {
                    month: `${month} 2024`,
                    amount: Math.round(monthlyBase + growth + random),
                    is_forecast: false
                };
            });

            // Add Forecast to Category/Project History
            const lastCatAmount = trendLine[trendLine.length - 1].amount;
            const catGrowth = (lastCatAmount - trendLine[0].amount) / 12;

            for (let i = 1; i <= 36; i++) {
                const nextDate = new Date(2025, 6 + i - 1, 1);
                const monthName = nextDate.toLocaleString('default', { month: 'short' });
                const year = nextDate.getFullYear();

                const projected = lastCatAmount + (catGrowth * i);
                trendLine.push({
                    month: `${monthName} ${year}`,
                    amount: Math.round(projected),
                    is_forecast: true
                });
            }
            history[key] = trendLine;
        });
        return history;
    };

    const category_history = generateHistory(category_breakdown);
    const project_history = generateHistory({
        'Cloud Migration 2.0': total_expenses * 0.45,
        'Legacy DC Maintenance': total_expenses * 0.25,
        'AI/ML Platform Build': total_expenses * 0.20,
        'Security Hardening': total_expenses * 0.10
    });

    return {
        total_expenses,
        category_breakdown,
        project_breakdown: {
            'Cloud Migration 2.0': total_expenses * 0.45,
            'Legacy DC Maintenance': total_expenses * 0.25,
            'AI/ML Platform Build': total_expenses * 0.20,
            'Security Hardening': total_expenses * 0.10
        },
        top_merchants,
        gaps: [],
        flash_fill: [],
        subscriptions: [
            { description: 'AWS Support Enterprise', amount: 15000, frequency: 'Monthly' },
            { description: 'GitHub Enterprise', amount: 5000, frequency: 'Monthly' },
            { description: 'Jira/Confluence', amount: 3000, frequency: 'Monthly' }
        ],
        anomalies: [
            { description: 'Unexpected Egress Spike (AWS)', date: '2024-05-12', amount: 45000, average: 12000 },
            { description: 'Urgent Hardware Replacement', date: '2024-08-01', amount: 85000, average: 0 }
        ],
        monthly_trend,
        category_history,
        project_history,
        category_vendors: {}, // Fallback empty
        project_vendors: {}, // Fallback empty
        category_merchants: {}, // Fallback empty
        project_merchants: {} // Fallback empty
    };
};

export const generatePartialMockData = (): BudgetMetrics => {
    // Partial Update: Only Cloud Infrastructure
    // Total approx $1M

    // Only one category
    const category_breakdown = {
        'Cloud Infrastructure': 985000
    };

    const project_breakdown = {
        'Cloud Migration 2.0': 600000,
        'AI/ML Platform Build': 385000
        // Missing Legacy DC, Security Hardening
    };

    const top_merchants = {
        'Amazon Web Services': 500000,
        'Azure Cloud': 300000,
        'Google Cloud Platform': 185000
    };

    // Simplified Trend
    const months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const monthly_trend = months.map(m => ({
        month: `${m} 2024`,
        amount: Math.round(985000 / 12),
        is_forecast: false
    }));

    return {
        total_expenses: 985000,
        category_breakdown,
        project_breakdown,
        top_merchants,
        gaps: [],
        flash_fill: [],
        subscriptions: [],
        anomalies: [],
        monthly_trend,
        category_history: { 'Cloud Infrastructure': monthly_trend },
        project_history: {
            'Cloud Migration 2.0': monthly_trend.map(x => ({ ...x, amount: x.amount * 0.6 })),
            'AI/ML Platform Build': monthly_trend.map(x => ({ ...x, amount: x.amount * 0.4 }))
        },
        category_vendors: {},
        project_vendors: {},
        category_merchants: {},
        project_merchants: {}
    };
};
