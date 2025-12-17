import { html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { BaseComponent } from '../base-component';
import { budgetStore } from '../../store/budget-store';
import { budgetService } from '../../services/budget.service';

@customElement('simulator-widget')
export class SimulatorWidget extends BaseComponent {
  @state() scenarioInput: string = '';
  @state() projectedSavings: number | null = null;
  @state() simulatedTotal: number | null = null;
  @state() errorMessage: string = '';
  @state() planExplanation: string = '';

  static styles = [
    BaseComponent.styles,
    css`
      :host {
        display: flex;
        flex-direction: column;
        min-height: 0;
        max-height: 100%;
        box-sizing: border-box;
        overflow: hidden;
        padding: 1rem;
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        background: var(--color-surface);
      }
      .scroll-container {
          flex: 1;
          overflow-y: auto;
          min-height: 0;
      }
      .input-group {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
      }
      input {
        flex: 1;
        padding: 0.5rem;
        border-radius: var(--radius-sm);
        border: 1px solid var(--color-border);
        background: rgba(255, 255, 255, 0.05);
        color: var(--color-text);
      }
      button {
        padding: 0.5rem 1rem;
        background: var(--color-primary);
        color: white;
        border: none;
        border-radius: var(--radius-sm);
        cursor: pointer;
      }
      .results {
        margin-top: 1rem;
        padding: 1rem;
        background: rgba(0, 0, 0, 0.2);
        border-radius: var(--radius-md);
      }
      .comparison {
        display: flex;
        justify-content: space-between;
        margin-top: 0.5rem;
      }
    `
  ];

  render() {
    return html`
      <h3>What-If Simulator</h3>
      <div class="scroll-container">
        <div class="input-group">
            <input 
            type="text"
            placeholder="e.g. Cut dining by 20%"
            .value=${this.scenarioInput}
            @input=${(e: Event) => this.scenarioInput = (e.target as HTMLInputElement).value}
            />
            <button @click=${this.runSimulation}>Simulate</button>
        </div>
        
        ${this.errorMessage ? html`<div style="color: var(--color-error); margin-bottom: 0.5rem; font-size: 0.9rem;">${this.errorMessage}</div>` : ''}
        ${this.planExplanation ? html`<div style="color: var(--color-text-secondary); margin-bottom: 0.5rem; font-size: 0.9rem; font-style: italic;">${this.planExplanation}</div>` : ''}

        ${this.projectedSavings !== null ? html`
            <div class="results">
            <div class="comparison">
                <span>Projected Savings:</span>
                <span class="savings">$${this.projectedSavings.toFixed(2)}</span>
            </div>
            ${this.simulatedTotal !== null ? html`
                <div class="comparison">
                <span>New Total:</span>
                <span class="total">$${this.simulatedTotal.toFixed(2)}</span>
                </div>
            ` : ''}
            </div>
        ` : ''
      }
      </div>
    `;
  }

  async runSimulation() {
    this.errorMessage = '';
    this.projectedSavings = null;
    this.simulatedTotal = null;

    if (!this.scenarioInput.trim()) return;

    try {
      // Call backend AI Planner
      const plan = await budgetService.planSimulation(this.scenarioInput);

      if (!plan || !plan.actions || plan.actions.length === 0) {
        this.errorMessage = "Could not understand scenario.";
        return;
      }

      this.planExplanation = plan.explanation || "";

      const metrics = budgetStore.state.metrics;
      const breakdown = metrics.category_breakdown || {};

      let totalDelta = 0;

      // Process all actions
      const projectBreakdown = metrics.project_breakdown || {};
      const topMerchants = metrics.top_merchants || {};

      for (const action of plan.actions) {
        const target = action.target.toLowerCase();
        let matchedAmount = 0;
        let matchedSource = '';

        // Helper to find match in a record
        const findMatch = (record: Record<string, number>) => {
          const keys = Object.keys(record);
          // 1. Exact match
          let key = keys.find(k => k.toLowerCase() === target);
          if (key) return record[key];

          // 2. Fuzzy match (target contains key or key contains target)
          // e.g. target="AWS Services", key="AWS" -> mismatch if strict, but let's be generous
          key = keys.find(k => k.toLowerCase().includes(target) || target.includes(k.toLowerCase()));
          if (key) return record[key];

          return null;
        };

        // 1. Try Category
        let found = findMatch(breakdown);
        if (found !== null) {
          matchedAmount = found;
          matchedSource = 'Category';
        } else {
          // 2. Try Project
          found = findMatch(projectBreakdown);
          if (found !== null) {
            matchedAmount = found;
            matchedSource = 'Project';
          } else {
            // 3. Try Merchant
            found = findMatch(topMerchants);
            if (found !== null) {
              matchedAmount = found;
              matchedSource = 'Merchant';
            }
          }
        }

        if (matchedSource) {
          const currentAmount = matchedAmount;
          let delta = 0;

          if (action.unit === 'percent') {
            delta = currentAmount * (action.amount / 100);
          } else {
            delta = action.amount;
          }

          // Handle direction
          if (action.action === 'increase') {
            delta = -delta; // Negative savings (cost increases)
          } else if (action.action === 'set') {
            delta = currentAmount - action.amount;
          }

          totalDelta += delta;
        } else {
          this.planExplanation += ` (Warning: Could not find '${action.target}' in budget data)`;
        }
      }

      // Final values
      const currentTotal = metrics.total_expenses;
      this.projectedSavings = totalDelta;
      this.simulatedTotal = currentTotal - totalDelta;

    } catch (e) {
      this.errorMessage = 'Simulation failed. Please try again.';
      console.error(e);
    }
  }
}
