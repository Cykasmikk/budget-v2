import { html, css, TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { BaseComponent } from '../../base-component';
import { Merchant } from '../../../types/interfaces';
import { BudgetMetrics } from '../../../store/budget-store';

@customElement('analysis-sidebar')
export class AnalysisSidebar extends BaseComponent {
  @property({ type: Object }) metrics: BudgetMetrics = {} as BudgetMetrics;
  @property({ type: String }) viewMode: string = 'category';
  @property({ type: String }) selectedCategory: string | null = null;
  @property({ type: Array }) merchants: Merchant[] = [];
  @property({ type: Number }) forecastMonths: number = 6;
  @property({ type: Boolean }) showForecast: boolean = false;

  static styles = [
    BaseComponent.styles,
    css`
      :host {
        display: flex;
        flex-direction: column;
        width: 280px;
        height: 100%;
        min-height: 0;
        border-left: 1px solid var(--color-border);
        padding-left: 1.25rem;
        overflow-y: auto;
      }

      /* Mobile */
      @media (max-width: 767px) {
        :host {
          width: 100%;
          height: auto;
          max-height: 300px; /* Limit height on mobile */
          border-left: none;
          border-top: 1px solid var(--color-border);
          padding-left: 0;
          padding-top: 1rem;
        }
      }

      /* 4K */
      @media (min-width: 3840px) {
        :host {
          width: 450px;
          padding-left: 2rem;
        }
        .merchant-name { font-size: 1.25rem; }
        .merchant-amount { font-size: 1.25rem; }
        h3 { font-size: 1.25rem; margin-bottom: 1.5rem; }
      }
      
      .merchants-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
      }

      .merchant-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: rgba(255,255,255,0.02);
        border-radius: var(--radius-md);
        min-width: 0;
      }

      .merchant-name { 
        font-weight: 500; 
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-right: 0.5rem;
      }
      
      .merchant-amount { 
        font-family: monospace; 
        color: var(--color-text-muted); 
        font-size: 0.9rem;
        flex: 0 0 auto;
      }

      h3 {
        font-size: 0.9rem; 
        margin: 0 0 1rem 0; 
        color: var(--color-text-muted); 
        text-transform: uppercase; 
        letter-spacing: 0.05em;
      }
    `
  ];

  render() {
    if (this.viewMode === 'forecast') {
      return this.renderForecastSummary();
    }

    const topCount = 8;
    const safeMerchants = Array.isArray(this.merchants) ? this.merchants : [];
    const topMerchants = safeMerchants.slice(0, topCount);
    const otherMerchants = safeMerchants.slice(topCount);
    
    const otherTotal = otherMerchants.reduce((sum, item) => {
        if (item && typeof item.amount === 'number') {
             return sum + item.amount;
        }
        return sum;
    }, 0);
    
    // We construct a Merchant object for 'Others' if needed for consistency in mapping
    const displayList: Merchant[] = [...topMerchants];
    if (otherTotal > 0) displayList.push({ name: 'Others', amount: otherTotal });

    return html`
      <h3>
         ${this.selectedCategory ? `Vendors in ${this.viewMode === 'project' ? 'Project' : 'Category'}` : 'Top Merchants'}
      </h3>
      <div class="merchants-list">
         ${displayList.map((item) => {
           if (!item || !item.name) return '';
           const { name, amount } = item;
           return html`
           <div class="merchant-item" style="${name === 'Others' ? 'font-style: italic; opacity: 0.7;' : ''}">
             <span class="merchant-name" title="${name}">${name}</span>
             <span class="merchant-amount">$${(amount as number).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
           </div>
         `;
         })}
         ${displayList.length === 0 ? html`
           <div style="color: var(--color-text-muted); font-style: italic;">No data available</div>
         ` : ''}
      </div>
    `;
  }

  private renderForecastSummary(): TemplateResult {
    const summary = this.metrics.forecast_summary;

    if (!summary) {
        const historyLen = this.metrics.monthly_trend?.length || 0;
        const message = historyLen < 2 
            ? "Need at least 2 months of data to generate a forecast." 
            : "No forecast data available.";

        return html`
            <h3>Forecast Summary</h3>
            <div class="merchants-list">
                <div class="merchant-item">
                    <span class="merchant-name">Status</span>
                    <span class="merchant-amount" style="font-size: 0.8rem; font-style: italic;">${message}</span>
                </div>
            </div>
        `;
    }

    return html`
      <h3>Forecast Summary</h3>
      <div class="merchants-list">
         <div class="merchant-item">
           <span class="merchant-name" title="Overall direction of the forecast over the horizon">Trend</span>
           <span class="merchant-amount" style="color: ${summary.trend_direction.includes('Increase') ? 'var(--color-warning)' : 'var(--color-success)'}">
               ${summary.trend_direction}
           </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name" title="Total forecasted expenses over the chosen horizon">Forecasted Expenses</span>
            <span class="merchant-amount">
               $${summary.forecasted_total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name" title="Percentage growth or decline in expenses over the forecast horizon, relative to the last actual period">Growth Rate</span>
            <span class="merchant-amount">
               ${summary.growth_rate}%
            </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name" title="Average width of the 95% confidence interval, indicating forecast uncertainty">Confidence Interval</span>
            <span class="merchant-amount">
               ±${summary.confidence_interval_width}%
            </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name" title="The underlying trend factor (change per period) in the forecasting model">Trend Component</span>
            <span class="merchant-amount">
               ${summary.trend_component}
            </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name" title="The smoothed base level of the data in the forecasting model">Level Component</span>
            <span class="merchant-amount">
               ${summary.level_component}
            </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name" title="Indicates if any historical data points were significantly outside the expected range">Outlier Detection</span>
            <span class="merchant-amount" style="color: ${summary.outlier_detected ? 'var(--color-error)' : 'var(--color-text-muted)'}">
               ${summary.outlier_detected ? 'Detected' : 'None'}
            </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name" title="Model accuracy based on Mean Absolute Percentage Error (MAPE), higher is better">Model Accuracy</span>
            <span class="merchant-amount">
               ${summary.model_accuracy}%
            </span>
         </div>
      </div>
    `;
  }
}
