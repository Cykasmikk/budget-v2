import { html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { BaseComponent } from '../../base-component';

@customElement('simulator-view')
export class SimulatorView extends BaseComponent {
  @property({ type: Object }) metrics: any = {};
  @property({ type: Object }) simulation: any = null;

  // Internal state for the form
  @state() private selectedCategory: string = '';
  @state() private percentage: string = '';

  static styles = [
    BaseComponent.styles,
    css`
      :host {
        display: flex;
        flex-direction: column;
        flex: 1;
        height: 100%; /* Fill parent */
        min-height: 0; /* Allow shrinking */
        overflow-y: auto;
      }

      .result-grid {
        display: grid; 
        grid-template-columns: repeat(3, 1fr); 
        gap: 1rem; 
        max-width: 800px; 
        margin-bottom: 2rem;
      }
      
      .result-card {
        padding: 1rem; 
        border-radius: var(--radius-md); 
        text-align: center;
      }
      
      .result-label {
        font-size: 0.75rem; 
        color: var(--color-text-muted); 
        margin-bottom: 0.25rem; 
        text-transform: uppercase; 
        letter-spacing: 0.05em;
      }
      
      .result-value {
        font-size: 1.25rem; 
        font-weight: 700; 
        white-space: nowrap;
      }
    `
  ];

  private handleRun() {
    this.dispatchEvent(new CustomEvent('run-simulation', {
      detail: { category: this.selectedCategory, percentage: this.percentage }
    }));
  }

  render() {
    return html`
         <div class="form-group flex-row items-center gap-md" style="max-width: 600px;">
              <select class="form-control" .value=${this.selectedCategory} @change=${(e: Event) => this.selectedCategory = (e.target as HTMLSelectElement).value}>
                <option value="">Select Category</option>
                ${Object.keys(this.metrics.category_breakdown || {}).map(cat => html`<option value="${cat}">${cat}</option>`)}
              </select>
              
              <input class="form-control" type="number" placeholder="Adj % (e.g. -10)" .value=${this.percentage} @input=${(e: Event) => this.percentage = (e.target as HTMLInputElement).value} />
              
              <button class="btn btn-primary" @click=${this.handleRun}>Run Simulation</button>
         </div>

         ${this.simulation ? html`
           <div class="result-grid">
             <div class="result-card" style="background: rgba(255,255,255,0.02);">
               <div class="result-label">Current</div>
               <div class="result-value">$${this.simulation.current_total.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
             </div>
             <div class="result-card" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2);">
               <div class="result-label">Simulated</div>
               <div class="result-value text-primary">$${this.simulation.simulated_total.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
             </div>
             <div class="result-card" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);">
               <div class="result-label">Savings</div>
               <div class="result-value text-success">$${this.simulation.savings.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
             </div>
           </div>
         ` : html`
           <div class="text-muted" style="text-align: center; font-style: italic; padding: 2rem;">
              Select a category and adjustment percentage to verify budget impact.
           </div>
         `}
    `;
  }
}
