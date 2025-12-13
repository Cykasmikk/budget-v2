import { html, css, TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { BaseComponent } from '../../base-component';
import { Merchant } from '../../../types/interfaces';

@customElement('analysis-sidebar')
export class AnalysisSidebar extends BaseComponent {
  @property({ type: Object }) metrics: any = {};
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
    const trend = this.metrics.monthly_trend || [];
    const allForecasts = trend.filter((x: any) => x.is_forecast);
    const lastVisible = allForecasts[this.forecastMonths - 1] || trend[trend.length - 1];
    const first = trend[0]?.amount || 0;
    const isIncreasing = (lastVisible?.amount || 0) > first;

    const visibleForecasts = allForecasts.slice(0, this.forecastMonths);
    const forecastSum = visibleForecasts.reduce((a: number, b: any) => a + b.amount, 0);

    return html`
      <h3>Forecast Summary (Holt's Method)</h3>
      <div class="merchants-list">
         <div class="merchant-item">
           <span class="merchant-name">Trend</span>
           <span class="merchant-amount">
               ${isIncreasing ? 'Increasing ↗' : 'Decreasing ↘'}
           </span>
         </div>
         <div class="merchant-item">
            <span class="merchant-name">Next ${this.forecastMonths} Months</span>
            <span class="merchant-amount">
               ${this.showForecast ? `$${forecastSum.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 'Enable Forecast'}
            </span>
         </div>
      </div>
    `;
  }
}
