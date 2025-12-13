import { html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { BaseComponent } from '../../base-component';
import { budgetStore } from '../../../store/budget-store';

@customElement('analysis-controls')
export class AnalysisControls extends BaseComponent {
  @property({ type: String }) viewMode = 'category';
  @property({ type: Boolean }) showForecast = false;
  @property({ type: Number }) forecastMonths = 6;
  @property({ type: String }) forecastType = 'total';

  static styles = [
    BaseComponent.styles,
    css`
      :host {
        display: flex;
        gap: 1rem;
        align-items: center;
      }

      .toggle-group {
        display: flex;
        background: rgba(255, 255, 255, 0.05);
        border-radius: var(--radius-md);
        padding: 2px;
        align-items: center;
      }

      .toggle-btn {
        padding: 0.5rem 1rem;
        border: none;
        background: transparent;
        color: var(--color-text-muted);
        cursor: pointer;
        border-radius: var(--radius-sm);
        transition: all var(--transition-fast);
        font-family: var(--font-family);
        font-size: 0.9rem;
      }

      .toggle-btn.active {
        background: var(--color-surface);
        color: var(--color-text);
        box-shadow: var(--shadow-sm);
      }
      
      .separator {
        width: 1px;
        height: 16px;
        background: var(--color-border);
        margin: 0 0.5rem;
      }
    `
  ];

  /* Events */
  private _toggleForecast(e: Event) {
    const checked = (e.target as HTMLInputElement).checked;
    this.dispatchEvent(new CustomEvent('toggle-forecast', { detail: checked }));
  }

  private _changeForecastMonths(e: Event) {
    const val = Number((e.target as HTMLInputElement).value);
    this.dispatchEvent(new CustomEvent('update-months', { detail: val }));
  }

  private _setForecastType(type: string) {
    this.dispatchEvent(new CustomEvent('update-type', { detail: type }));
  }

  render() {
    return html`
      ${this.viewMode === 'forecast' ? html`
          <div class="toggle-group" style="padding: 0.25rem 0.75rem; gap: 0.5rem;">
            <label class="text-muted" style="font-size: 0.8rem; display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
               <input type="checkbox" .checked=${this.showForecast} @change=${this._toggleForecast} aria-label="Show forecast">
               Show Forecast
            </label>
            
            ${this.showForecast ? html`
                <div class="separator"></div>
                <label class="text-muted" style="font-size: 0.8rem; white-space: nowrap;">Horizon: ${this.forecastMonths} Months</label>
                <input type="range" min="1" max="36" step="1" .value=${this.forecastMonths} 
                       @input=${this._changeForecastMonths}
                       style="width: 100px; accent-color: var(--color-primary);"
                       aria-label="Forecast horizon in months"
                >
            ` : ''}
          </div>
          
          <div class="toggle-group">
            <button class="toggle-btn ${this.forecastType === 'total' ? 'active' : ''}" @click=${() => this._setForecastType('total')} aria-label="Show total forecast" aria-pressed=${this.forecastType === 'total'}>Total</button>
            <button class="toggle-btn ${this.forecastType === 'category' ? 'active' : ''}" @click=${() => this._setForecastType('category')} aria-label="Show category forecast" aria-pressed=${this.forecastType === 'category'}>Category</button>
            <button class="toggle-btn ${this.forecastType === 'project' ? 'active' : ''}" @click=${() => this._setForecastType('project')} aria-label="Show project forecast" aria-pressed=${this.forecastType === 'project'}>Project</button>
          </div>
      ` : ''}
      
      <div class="toggle-group">
        <button class="toggle-btn ${this.viewMode === 'category' ? 'active' : ''}"
          @click=${() => budgetStore.setViewMode('category')} aria-label="View by category" aria-pressed=${this.viewMode === 'category'}>Category</button>
        <button class="toggle-btn ${this.viewMode === 'project' ? 'active' : ''}"
          @click=${() => budgetStore.setViewMode('project')} aria-label="View by project" aria-pressed=${this.viewMode === 'project'}>Project</button>
        <button class="toggle-btn ${this.viewMode === 'forecast' ? 'active' : ''}"
          @click=${() => budgetStore.setViewMode('forecast')} aria-label="View forecast" aria-pressed=${this.viewMode === 'forecast'}>Forecast</button>
        <button class="toggle-btn ${this.viewMode === 'simulator' ? 'active' : ''}"
          @click=${() => budgetStore.setViewMode('simulator')} aria-label="View simulator" aria-pressed=${this.viewMode === 'simulator'}>Simulator</button>
        <button class="toggle-btn ${this.viewMode === 'chat' ? 'active' : ''}"
          @click=${() => budgetStore.setViewMode('chat')} aria-label="Open AI chat" aria-pressed=${this.viewMode === 'chat'}>AI Chat</button>
      </div>

      <button class="btn btn-secondary" @click=${() => window.open('/api/v1/export', '_blank')} aria-label="Export data as CSV">
        Export CSV
      </button>
    `;
  }
}
