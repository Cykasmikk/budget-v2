import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('insights-card')
export class InsightsCard extends LitElement {
  @property({ type: Object }) metrics: any = {};

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-xl);
      padding: 1.5rem;
      height: 100%;
      overflow: hidden;
      box-sizing: border-box;
    }

    * {
      box-sizing: border-box;
    }

    h2 {
      flex: 0 0 auto;
      font-size: var(--font-size-lg);
      font-weight: 600;
      margin: 0 0 1.5rem 0;
      color: var(--color-text);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .scroll-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      min-height: 0;
      padding-right: 0.25rem;
    }

    .section {
      margin-bottom: 2rem;
    }

    .section-title {
      font-size: 0.85rem;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 1rem;
      font-weight: 600;
    }

    .insight-card {
      padding: 1rem;
      border-radius: var(--radius-md);
      margin-bottom: 0.75rem;
    }

    .insight-title {
      font-weight: 600;
      margin-bottom: 0.25rem;
    }

    .insight-detail {
      font-size: 0.9rem;
      color: opacity(var(--color-text), 0.8);
    }
  `;

  render() {
    const hasFlashFill = this.metrics.flash_fill && this.metrics.flash_fill.length > 0;
    const hasSubscriptions = this.metrics.subscriptions && this.metrics.subscriptions.length > 0;
    const hasAnomalies = this.metrics.anomalies && this.metrics.anomalies.length > 0;

    return html`
      <h2>💡 Insights</h2>
      
      <div class="scroll-content">
        ${!hasFlashFill && !hasSubscriptions && !hasAnomalies ? html`
          <div style="text-align: center; color: var(--color-text-muted); font-style: italic; padding: 2rem;">
            No insights detected yet. Upload more data or wait for AI analysis.
          </div>
        ` : html`
          ${hasFlashFill ? html`
            <div class="section">
              <div class="section-title">⚡ Flash Fill Suggestions</div>
              ${this.metrics.flash_fill.map((item: any) => html`
                <div class="insight-card" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2);">
                  <div class="insight-title">${item.description}</div>
                  <div class="insight-detail">
                    Found ${item.count} items. Suggestion: <span style="color: var(--color-primary); font-weight: bold;">${item.suggested_category}</span>
                  </div>
                </div>
              `)}
            </div>
          ` : ''}

          ${hasSubscriptions ? html`
            <div class="section">
              <div class="section-title">🔄 Recurring Subscriptions</div>
              ${this.metrics.subscriptions.map((sub: any) => html`
                <div class="insight-card" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);">
                  <div class="insight-title">${sub.description}</div>
                  <div class="insight-detail">
                    ${sub.frequency} • <span style="color: var(--color-success); font-weight: bold;">$${sub.amount.toFixed(2)}</span>
                  </div>
                </div>
              `)}
            </div>
          ` : ''}

          ${hasAnomalies ? html`
            <div class="section">
              <div class="section-title">🚨 Spending Anomalies</div>
              ${this.metrics.anomalies.map((anomaly: any) => html`
                <div class="insight-card" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2);">
                  <div class="insight-title">${anomaly.description}</div>
                  <div class="insight-detail">
                    <span style="color: var(--color-error); font-weight: bold;">$${anomaly.amount.toFixed(2)}</span> 
                    (Avg: $${anomaly.average.toFixed(2)}) on ${anomaly.date}
                  </div>
                </div>
              `)}
            </div>
          ` : ''}
        `}
      </div>
    `;
  }
}
