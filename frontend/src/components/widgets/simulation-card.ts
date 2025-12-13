import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { budgetStore } from '../../store/budget-store';

@customElement('simulation-card')
export class SimulationCard extends LitElement {
  @property({ type: Object }) metrics: any = {};
  @property({ type: Object }) simulation: any = null;

  @state() private selectedCategory: string = '';
  @state() private percentage: string = '';

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-xl);
      padding: 1rem;
      height: 100%;
      overflow: hidden;
      box-sizing: border-box;
    }

    * { box-sizing: border-box; }

    h2 {
      flex: 0 0 auto;
      font-size: var(--font-size-base);
      font-weight: 600;
      margin: 0 0 1rem 0;
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

    .form-group {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1rem;
      flex: 0 0 auto;
    }

    .form-input, .form-select {
      flex: 1;
      padding: 0.5rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--color-border);
      background: rgba(255,255,255,0.05);
      color: var(--color-text);
      font-family: var(--font-family);
      font-size: 0.9rem;
    }
    
    .form-input:focus, .form-select:focus {
      outline: none;
      border-color: var(--color-primary);
    }

    .btn-submit {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      color: var(--color-text);
      padding: 0 1rem;
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.9rem;
    }

    .btn-submit:hover {
      border-color: var(--color-primary);
      color: var(--color-primary);
    }
    
    .result-grid {
      display: grid; 
      grid-template-columns: repeat(3, 1fr); 
      gap: 0.75rem;
    }

    .result-card {
      padding: 0.75rem;
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
      font-size: 1.125rem;
      font-weight: 700;
      white-space: nowrap;
    }
  `;

  render() {
    return html`
      <h2>🧪 Sandbox Simulator</h2>
      
      <div class="scroll-content">
        <div class="form-group">
          <select 
            class="form-select"
            .value=${this.selectedCategory}
            @change=${(e: Event) => this.selectedCategory = (e.target as HTMLSelectElement).value}
          >
            <option value="">Select Category</option>
            ${Object.keys(this.metrics.category_breakdown || {}).map(cat => html`<option value="${cat}">${cat}</option>`)}
          </select>
          
          <input 
            class="form-input"
            type="number" 
            placeholder="Adj %" 
            .value=${this.percentage}
            @input=${(e: Event) => this.percentage = (e.target as HTMLInputElement).value}
          />
          
          <button class="btn-submit" @click=${this.runSimulation}>Run</button>
        </div>
        
        ${this.simulation ? html`
          <div class="result-grid">
            <div class="result-card" style="background: rgba(255,255,255,0.02);">
              <div class="result-label">Current</div>
              <div class="result-value">$${this.simulation.current_total.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
            </div>
            
            <div class="result-card" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2);">
              <div class="result-label">Simulated</div>
              <div class="result-value" style="color: var(--color-primary);">$${this.simulation.simulated_total.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
            </div>
            
            <div class="result-card" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);">
              <div class="result-label">Savings</div>
              <div class="result-value" style="color: var(--color-success);">$${this.simulation.savings.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
            </div>
          </div>
        ` : html`
          <div style="text-align: center; color: var(--color-text-muted); font-style: italic; padding: 1rem; font-size: 0.9rem;">
            Select a category and adjustment to simulate.
          </div>
        `}
      </div>
    `;
  }

  private runSimulation() {
    if (this.selectedCategory && this.percentage) {
      budgetStore.simulateBudget([{ category: this.selectedCategory, percentage: Number(this.percentage) }]);
    }
  }
}
