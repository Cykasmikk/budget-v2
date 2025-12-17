import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { BudgetMetrics } from '../../../store/budget-store';
import './gantt-chart';

@customElement('timeline-view')
export class TimelineView extends LitElement {
    @property({ type: Object }) metrics: BudgetMetrics = {} as BudgetMetrics;

    static styles = css`
        :host {
            display: block;
            min-height: 0;
            max-height: 100%;
            width: 100%;
            box-sizing: border-box;
            overflow: hidden;
            padding: 1rem;
            box-sizing: border-box;
        }

        .header {
            margin-bottom: 1rem;
        }

        h3 {
            margin: 0;
            font-weight: 500;
            color: var(--color-text);
        }

        p {
            margin: 0.25rem 0 0;
            color: var(--color-text-secondary);
            font-size: 0.9rem;
        }
        
        .legend {
            display: flex;
            gap: 1rem;
            margin-top: 0.5rem;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--color-text-secondary);
        }
        
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
    `;

    render() {
        const timelineItems = this.metrics.timeline || [];

        return html`
            <div class="header">
                <h3>Contract & Lifecycle Timeline</h3>
                <p>Track software renewals, hardware end-of-life, and active subscriptions.</p>
                
                <div class="legend">
                    <div class="legend-item"><div class="dot" style="background: #3b82f6"></div> Subscription</div>
                    <div class="legend-item"><div class="dot" style="background: #10b981"></div> Contract</div>
                    <div class="legend-item"><div class="dot" style="background: #f59e0b"></div> Hardware</div>
                </div>
            </div>

            ${timelineItems.length > 0 ? html`
                <gantt-chart .items=${timelineItems}></gantt-chart>
            ` : html`
                <div style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
                    No timeline data available. Upload budget files with subscription or contract info.
                </div>
            `}
        `;
    }
}
