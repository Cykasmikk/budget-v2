import { html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { BaseComponent } from '../base-component';
import { AnalysisController } from '../../controllers/analysis-controller';
import { BudgetMetrics } from '../../store/budget-store';
import { ViewMode } from '../../types/interfaces';

// Sub-components
import './analysis/analysis-sidebar';
import './analysis/analysis-controls';
import './timeline/timeline-view';
import '../budget-chart';
import '../reports/infographic-report';
import './ai-chat';

@customElement('analysis-card')
export class AnalysisCard extends BaseComponent {
  private controller = new AnalysisController(this);

  @property({ type: Object }) metrics: BudgetMetrics = {} as BudgetMetrics;
  @property({ type: String }) viewMode: ViewMode = 'category';
  @property({ type: Number }) budgetLimit: number = 0;
  @property({ type: Boolean }) isLoading: boolean = false;

  @state() showInfographic: boolean = false;

  static styles = [
    BaseComponent.styles,
    css`
      :host {
        display: block;
        height: 100%;
        overflow: hidden;
      }
      
      .content {
        flex: 1;
        display: flex;
        flex-direction: row; /* Horizontal layout */
        gap: 1.25rem;
        overflow: hidden;
        min-height: 0; /* CRITICAL: Prevents flex child from growing infinitely */
      }

      /* Mobile (320px - 767px) */
      @media (max-width: 767px) {
        .content {
          flex-direction: column;
          gap: 1rem;
        }
        
        .chart-container {
          min-height: 250px;
        }
      }

      /* 4K (3840px+) */
      @media (min-width: 3840px) {
        .content {
          gap: 3rem;
        }
        .chart-container {
            min-height: 600px; /* Larger chart for 4K */
        }
      }

      .chart-panel {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        overflow-y: auto;
      }

      .chart-container {
        flex: 1;
        position: relative;
        min-height: 200px;
        max-height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: hidden;
        padding-bottom: 0.75rem; /* Small padding to prevent UI overhang at bottom */
        box-sizing: border-box;
      }
      
      .header-row {
         display: flex;
         justify-content: space-between;
         align-items: center;
         margin-bottom: 0.75rem;
      }

      /* Insights Grid */
      .insights-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
      }
      
      .insight-card {
        padding: 1rem;
        border-radius: var(--radius-md);
        border-width: 1px;
        border-style: solid;
      }
      
      .insight-card.flash { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.2); }
      .insight-card.sub { background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.2); }
      .insight-card.anomaly { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); }
      
      .insight-title { font-weight: 600; margin-bottom: 0.25rem; }
      .insight-detail { font-size: 0.9rem; opacity: 0.8; }
    `
  ];

  render() {
    // 1. Prepare Data via Controller
    const { data: chartData, allMerchants, isDrillDown } = this.controller.getChartData(this.viewMode, this.metrics);

    // 2. Determine Title via Controller
    const title = this.controller.getTitle(this.viewMode);

    // Calculate max available forecast months from data
    const maxAvailableForecast = this.metrics.monthly_trend 
        ? this.metrics.monthly_trend.filter(x => x.is_forecast).length 
        : 12;

    return html`
      <div class="card h-full">
        <div class="header-row">
            <div class="flex-row items-center gap-sm">
                <h2 class="card-title">${title}</h2>
                ${isDrillDown ? html`
                    <span class="filter-badge" @click=${() => this.controller.selectCategory(null)} 
                          style="background: rgba(59, 130, 246, 0.1); color: var(--color-primary); padding: 0.25rem 0.5rem; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.75rem;"
                          role="button"
                          tabindex="0"
                          aria-label="Clear category filter">
                       ${this.controller.selectedCategory} <span aria-hidden="true">✕</span>
                    </span>
                ` : ''}
            </div>

            <analysis-controls
                .viewMode=${this.viewMode}
                .showForecast=${this.controller.showForecast}
                .forecastMonths=${this.controller.forecastMonths}
                .maxMonths=${maxAvailableForecast || 12}
                .forecastType=${this.controller.forecastType}
                @toggle-forecast=${(e: CustomEvent) => this.controller.toggleForecast(e.detail)}
                @update-months=${(e: CustomEvent) => this.controller.setForecastMonths(e.detail)}
                @update-type=${(e: CustomEvent) => this.controller.setForecastType(e.detail)}
            ></analysis-controls>
        </div>

        <div class="content">
            ${this.viewMode === 'chat' ? html`
                <ai-chat .metrics=${this.metrics}></ai-chat>
            ` : this.viewMode === 'timeline' ? html`
                <timeline-view .metrics=${this.metrics}></timeline-view>
            ` : html`
                
                <div class="chart-panel">
                    <div class="chart-container">
                        <budget-chart 
                            .data=${chartData}
                            .viewMode=${this.viewMode}
                            .budgetLimit=${this.budgetLimit}
                            @segment-click=${(e: CustomEvent) => { if (this.viewMode !== 'forecast') this.controller.selectCategory(e.detail.label); }}
                        ></budget-chart>
                    </div>
                </div>

                <analysis-sidebar
                    .metrics=${this.metrics}
                    .viewMode=${this.viewMode}
                    .selectedCategory=${this.controller.selectedCategory}
                    .merchants=${allMerchants}
                    .forecastMonths=${this.controller.forecastMonths}
                    .showForecast=${this.controller.showForecast}
                ></analysis-sidebar>
            `}
        </div>
        
        <!-- Hidden Infographic Report (Modals overlay generally) -->
        <infographic-report 
            .metrics=${this.metrics} 
            ?visible=${this.showInfographic}
            @close=${() => this.showInfographic = false}
        ></infographic-report>
      </div>
    `;
  }

}
