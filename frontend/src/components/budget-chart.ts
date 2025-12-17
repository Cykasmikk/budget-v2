import { LitElement, html, css, PropertyValues } from 'lit';
import { customElement, property, query } from 'lit/decorators.js';
import Chart, { ChartEvent, ActiveElement } from 'chart.js/auto';
import { ChartConfig, ChartContext, ChartData } from '../types/interfaces';

@customElement('budget-chart')
export class BudgetChart extends LitElement {
    static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
      min-height: 0;
      max-height: 100%;
    }
    .chart-wrapper {
      position: relative;
      width: 100%;
      height: 100%;
      max-width: 100%;
      max-height: 100%;
      overflow: hidden; /* Critical for stopping Chart.js loops */
      box-sizing: border-box;
      contain: layout size; /* Prevent layout thrashing */
      padding-bottom: 0.5rem; /* Small padding to prevent UI overhang at bottom */
    }
    canvas {
      display: block;
      max-width: 100%;
      max-height: 100%;
      /* Remove width/height 100% to prevent infinite loop with Chart.js attributes */
    }
  `;

    @property({ type: Object })
    data: Record<string, number> | Array<any> = {};

    @property({ type: String })
    viewMode: 'category' | 'project' | 'forecast' = 'category';

    @property({ type: Number })
    budgetLimit: number = 0;

    @query('canvas')
    private canvas!: HTMLCanvasElement;

    private chart: Chart | null = null;

    firstUpdated() {
        this.updateChart();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    updated(changedProperties: PropertyValues) {
        if (changedProperties.has('data') || changedProperties.has('viewMode') || changedProperties.has('budgetLimit')) {
            this.updateChart();
        }
    }

    private getChartColors(): string[] {
        return [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
            '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6'
        ];
    }

    private createForecastConfig(data: ChartData, isMultiLine: boolean, computedStyle: CSSStyleDeclaration): ChartConfig {
        const datasets: any[] = [];
        let labels: string[] = [];

        if (isMultiLine) {
            const allSeries = data as unknown as Record<string, Array<{ month: string; amount: number; is_forecast: boolean }>>;
            const seriesKeys = Object.keys(allSeries);
            if (seriesKeys.length > 0) {
                labels = allSeries[seriesKeys[0]].map((d: { month: string; amount: number; is_forecast: boolean }) => d.month);
            }

            const colors = this.getChartColors();
            seriesKeys.forEach((key, index) => {
                const seriesData = allSeries[key];
                const color = colors[index % colors.length];

                datasets.push({
                    label: key,
                    data: seriesData.map(d => d.amount),
                    borderColor: color,
                    backgroundColor: color,
                    borderWidth: 2,
                    tension: 0.4,
                    segment: {
                        borderDash: (ctx: ChartContext) => seriesData[ctx.p1DataIndex]?.is_forecast ? [5, 5] : undefined,
                        borderColor: (ctx: ChartContext) => seriesData[ctx.p1DataIndex]?.is_forecast ? color : undefined
                    },
                    pointRadius: 0,
                    pointHoverRadius: 4
                });
            });
        } else {
            const trendData = data as Array<{ month: string; amount: number; is_forecast: boolean; lower_bound?: number; upper_bound?: number }>;
            labels = trendData.map((d) => d.month);
            const values = trendData.map((d) => d.amount);
            const upperBounds = trendData.map((d) => d.upper_bound);
            const lowerBounds = trendData.map((d) => d.lower_bound);
            const hasBounds = upperBounds.some((v) => v !== undefined);

            if (hasBounds) {
                datasets.push({
                    label: 'Upper Bound',
                    data: upperBounds,
                    borderColor: 'transparent',
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    fill: false,
                    order: 1
                });
                datasets.push({
                    label: 'Confidence Interval',
                    data: lowerBounds,
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(59, 130, 246, 0.15)', // Light Blue with opacity
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    fill: '-1', // Fill to previous dataset (Upper Bound)
                    order: 1
                });
            }

            datasets.push({
                label: 'Monthly Spend',
                data: values,
                borderColor: computedStyle.getPropertyValue('--color-primary').trim(),
                backgroundColor: computedStyle.getPropertyValue('--color-primary').trim(),
                borderWidth: 2,
                tension: 0.4,
                segment: {
                    borderDash: (ctx: ChartContext) => trendData[ctx.p1DataIndex]?.is_forecast ? [5, 5] : undefined,
                    borderColor: (ctx: ChartContext) => trendData[ctx.p1DataIndex]?.is_forecast ? '#f59e0b' : computedStyle.getPropertyValue('--color-primary').trim()
                },
                pointRadius: (ctx: ChartContext) => trendData[ctx.dataIndex]?.is_forecast ? 2 : 4,
                pointBackgroundColor: (ctx: ChartContext) => trendData[ctx.dataIndex]?.is_forecast ? '#f59e0b' : computedStyle.getPropertyValue('--color-primary').trim(),
                order: 0 // Draw on top
            });
        }

        return {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: isMultiLine,
                        position: 'bottom',
                        labels: { usePointStyle: true, boxWidth: 8 }
                    },
                    title: {
                        display: true,
                        text: 'Monthly Spending Trend (Aus FY)',
                        color: computedStyle.getPropertyValue('--color-text').trim(),
                        font: { family: 'Inter', size: 16 }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context: any) => {
                                const val = context.parsed?.y;
                                const index = context.dataIndex;
                                // Access the original data to check is_forecast
                                // For multi-line, we might need a different approach, but for now single line trendData is in scope
                                let status = '';

                                if (!isMultiLine) {
                                    const trendData = data as Array<{ month: string; amount: number; is_forecast: boolean }>;
                                    if (trendData && trendData[index]) {
                                        status = trendData[index].is_forecast ? ' (Predicted)' : ' (Actual)';
                                    }
                                } else {
                                    // For multi-line, try to find the data point from the raw data object
                                    // context.dataset.label corresponds to the key in the data object
                                    const allSeries = data as unknown as Record<string, Array<{ month: string; amount: number; is_forecast: boolean }>>;
                                    const seriesKey = context.dataset.label;
                                    const seriesData = allSeries[seriesKey];
                                    if (seriesData && seriesData[index]) {
                                        status = seriesData[index].is_forecast ? ' (Predicted)' : ' (Actual)';
                                    }
                                }

                                return `${context.dataset?.label || 'Value'}${status}: $${val?.toLocaleString() ?? '0'}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: computedStyle.getPropertyValue('--color-border').trim() },
                        ticks: { color: computedStyle.getPropertyValue('--color-text-muted').trim() }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: computedStyle.getPropertyValue('--color-text-muted').trim(),
                            maxRotation: 0,
                            minRotation: 0
                        }
                    }
                },
                layout: { padding: { bottom: 30 } }
            }
        };
    }

    private createCategoryConfig(data: Record<string, number>, computedStyle: CSSStyleDeclaration): ChartConfig {
        const labels = Object.keys(data);
        const values = Object.values(data);

        return {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    label: 'Expenses',
                    data: values,
                    backgroundColor: [
                        computedStyle.getPropertyValue('--color-primary').trim(),
                        computedStyle.getPropertyValue('--color-success').trim(),
                        '#f59e0b',
                        computedStyle.getPropertyValue('--color-error').trim(),
                        '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6'
                    ],
                    borderColor: computedStyle.getPropertyValue('--color-surface').trim(),
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        display: true,
                        labels: {
                            color: computedStyle.getPropertyValue('--color-text').trim(),
                            font: { family: 'Inter' },
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    title: {
                        display: true,
                        text: 'Expenses by Category',
                        color: computedStyle.getPropertyValue('--color-text').trim(),
                        font: { family: 'Inter', size: 16, weight: 'bold' },
                        padding: { bottom: 20 }
                    }
                },
                layout: { padding: 20 },
                onClick: (_event: ChartEvent, elements: ActiveElement[]) => {
                    if (elements && elements.length > 0) {
                        const index = elements[0].index;
                        const label = labels[index];
                        const value = values[index];
                        this.dispatchEvent(new CustomEvent('segment-click', {
                            detail: { label, value },
                            bubbles: true,
                            composed: true
                        }));
                    }
                }
            }
        };
    }

    private createProjectConfig(data: Record<string, number>, computedStyle: CSSStyleDeclaration): ChartConfig {
        const labels = Object.keys(data);
        const values = Object.values(data);

        return {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Expenses by Project',
                    data: values,
                    backgroundColor: [
                        computedStyle.getPropertyValue('--color-primary').trim(),
                        computedStyle.getPropertyValue('--color-success').trim(),
                        '#f59e0b',
                        computedStyle.getPropertyValue('--color-error').trim(),
                        '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6'
                    ],
                    borderColor: computedStyle.getPropertyValue('--color-surface').trim(),
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        display: false,
                        labels: {
                            color: computedStyle.getPropertyValue('--color-text').trim(),
                            font: { family: 'Inter' },
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    title: {
                        display: true,
                        text: 'Expenses by Project',
                        color: computedStyle.getPropertyValue('--color-text').trim(),
                        font: { family: 'Inter', size: 16, weight: 'bold' },
                        padding: { bottom: 20 }
                    }
                },
                layout: { padding: 20 },
                onClick: (_event: ChartEvent, elements: ActiveElement[]) => {
                    if (elements && elements.length > 0) {
                        const index = elements[0].index;
                        const label = labels[index];
                        const value = values[index];
                        this.dispatchEvent(new CustomEvent('segment-click', {
                            detail: { label, value },
                            bubbles: true,
                            composed: true
                        }));
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: computedStyle.getPropertyValue('--color-border').trim() },
                        ticks: {
                            color: computedStyle.getPropertyValue('--color-text-muted').trim(),
                            font: { family: 'Inter' }
                        }
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: computedStyle.getPropertyValue('--color-text-muted').trim(),
                            font: { family: 'Inter' },
                            autoSkip: true
                        }
                    }
                }
            }
        };
    }

    private updateChart() {
        if (!this.canvas) return;

        if (this.chart) {
            this.chart.destroy();
        }

        // Get container dimensions AFTER layout to ensure accurate measurements
        const wrapper = this.shadowRoot?.querySelector('.chart-wrapper') as HTMLElement;
        let containerWidth = 0;
        let containerHeight = 0;

        if (wrapper) {
            const rect = wrapper.getBoundingClientRect();
            containerWidth = Math.max(1, Math.floor(rect.width));
            containerHeight = Math.max(1, Math.floor(rect.height));

            // Explicitly set canvas dimensions to prevent Chart.js from setting incorrect values
            // This breaks the infinite loop by constraining the canvas to container size
            if (containerWidth > 0 && containerHeight > 0) {
                // Use devicePixelRatio for crisp rendering, but constrain to container
                const dpr = window.devicePixelRatio || 1;
                this.canvas.width = containerWidth * dpr;
                this.canvas.height = containerHeight * dpr;
                this.canvas.style.width = `${containerWidth}px`;
                this.canvas.style.height = `${containerHeight}px`;
            }
        }

        const computedStyle = getComputedStyle(this);
        const isProject = this.viewMode === 'project';
        const isForecast = this.viewMode === 'forecast';

        let config: ChartConfig;

        if (isForecast) {
            const isMultiLine = !Array.isArray(this.data);
            config = this.createForecastConfig(this.data, isMultiLine, computedStyle);
        } else if (isProject) {
            config = this.createProjectConfig(this.data as Record<string, number>, computedStyle);
        } else {
            config = this.createCategoryConfig(this.data as Record<string, number>, computedStyle);
        }

        // @ts-ignore
        this.chart = new Chart(this.canvas, config);

        // After Chart.js initializes, enforce container bounds to prevent infinite expansion
        if (wrapper && containerWidth > 0 && containerHeight > 0) {
            const dpr = window.devicePixelRatio || 1;
            const maxWidth = containerWidth * dpr;
            const maxHeight = containerHeight * dpr;

            // Force canvas to respect container bounds (Chart.js may have changed them)
            if (this.canvas.width > maxWidth) {
                this.canvas.width = maxWidth;
                this.canvas.style.width = `${containerWidth}px`;
            }
            if (this.canvas.height > maxHeight) {
                this.canvas.height = maxHeight;
                this.canvas.style.height = `${containerHeight}px`;
            }
        }
    }

    render() {
        return html`
          <div class="chart-wrapper">
            <canvas></canvas>
          </div>
        `;
    }
}
