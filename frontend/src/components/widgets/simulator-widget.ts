import { html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { BaseComponent } from '../base-component';
import { budgetStore } from '../../store/budget-store';
import { budgetService } from '../../services/budget.service';


interface PlanAction {
  action: 'reduce' | 'increase' | 'set';
  target: string;
  amount: number;
  unit: 'percent' | 'absolute';
  explanation?: string;
  calculatedDelta?: number; // The actual $ impact (Change in Spend)
  cumulativeTotal?: number; // Cat 4.4: Running total after this step
  isEditing?: boolean; // UI State
}

@customElement('simulator-widget')
export class SimulatorWidget extends BaseComponent {
  @state() scenarioInput: string = '';
  @state() simulatedActions: PlanAction[] = [];
  @state() projectedSavings: number | null = null;
  @state() simulatedTotal: number | null = null;
  @state() errorMessage: string = '';
  @state() planExplanation: string = '';
  @state() isLoading: boolean = false;

  @state() savedScenarios: any[] = [];
  @state() undoStack: any[] = []; // Stores previous metrics
  @state() showComparison: boolean = false;
  @state() successMessage: string = '';

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
        padding: 1.5rem;
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        background: var(--color-surface);
        gap: 1rem;
      }
      .scroll-container {
          flex: 1;
          overflow-y: auto;
          min-height: 0;
          padding-right: 0.5rem;
      }
      .input-group {
        display: flex;
        gap: 0.5rem;
      }
      input {
        flex: 1;
        padding: 0.75rem;
        border-radius: var(--radius-md);
        border: 1px solid var(--color-border);
        background: rgba(255, 255, 255, 0.05);
        color: var(--color-text);
        font-family: inherit;
      }
      button {
        padding: 0.75rem 1.25rem;
        background: var(--color-primary);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        cursor: pointer;
        font-weight: 500;
        transition: opacity 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
      }
      button:hover { opacity: 0.9; }
      button:disabled { opacity: 0.5; cursor: not-allowed; }
      
      button.secondary { background: var(--color-surface-hover); color: var(--color-text); border: 1px solid var(--color-border); }
      button.success { background: var(--color-success); }
      button.danger { background: var(--color-error); }
      button.icon-only { padding: 0.4rem; font-size: 1rem; }

      .action-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        margin-top: 1rem;
      }

      .action-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        transition: background-color 0.2s;
      }
      .action-item:hover { background: rgba(255, 255, 255, 0.06); }

      .action-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
      }
      
      .action-details { flex: 1; }
      .action-title { font-weight: 600; font-size: 0.95rem; display: block; margin-bottom: 0.25rem; }
      .action-desc { font-size: 0.85rem; color: var(--color-text-secondary); }
      
      .action-stats { display: flex; flex-direction: column; align-items: flex-end; }
      .action-impact { font-weight: 700; font-size: 1rem; text-align: right; }
      .action-cumulative { font-size: 0.75rem; color: var(--color-text-secondary); margin-top: 0.25rem; }
      
      .impact-positive { color: var(--color-success); }
      .impact-negative { color: var(--color-error); }
      
      .action-controls {
          display: flex;
          gap: 0.25rem;
          opacity: 0.4;
          transition: opacity 0.2s;
          margin-left: 0.5rem;
      }
      .action-item:hover .action-controls { opacity: 1; }

      .edit-form {
          display: flex;
          gap: 0.5rem;
          width: 100%;
          align-items: center;
      }
      .edit-form input { padding: 0.4rem; font-size: 0.9rem; }
      .edit-form select { 
          padding: 0.4rem; 
          background: rgba(0,0,0,0.3); 
          color: white; 
          border: 1px solid var(--color-border); 
          border-radius: var(--radius-sm); 
      }

      .results-summary {
        margin-top: 1rem;
        padding: 1.25rem;
        background: rgba(var(--color-primary-rgb), 0.1);
        border: 1px solid rgba(var(--color-primary-rgb), 0.2);
        border-radius: var(--radius-md);
      }
      .summary-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
      }
      .summary-row:last-child { margin-bottom: 0; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.1); font-weight: 700; font-size: 1.1rem; }
      
      .toolbar { display: flex; gap: 0.5rem; margin-top: 1rem; flex-wrap: wrap; }
      
      .toast {
          padding: 0.75rem 1rem;
          background: var(--color-success);
          color: white;
          border-radius: var(--radius-md);
          margin-bottom: 1rem;
          animation: fadeIn 0.3s ease;
          display: flex;
          align-items: center;
          gap: 0.5rem;
      }
      @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

      .loading-spinner { animation: spin 1s linear infinite; }
      @keyframes spin { 100% { transform: rotate(360deg); } }
      
      .comparison-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 1rem;
          font-size: 0.9rem;
      }
      .comparison-table th { text-align: left; padding: 0.5rem; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); }
      .comparison-table td { padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
      .comparison-table tr:hover { background: rgba(255,255,255,0.02); }
      
      .saved-scenarios { margin-top: 1rem; border-top: 1px solid var(--color-border); padding-top: 1rem; }
      .saved-chip { display: inline-block; padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.1); border-radius: 1rem; font-size: 0.8rem; margin-right: 0.5rem; cursor: pointer; }
    `
  ];

  firstUpdated() {
    this.loadSavedScenarios();
  }

  loadSavedScenarios() {
    try {
      const stored = localStorage.getItem('budget_scenarios');
      if (stored) {
        this.savedScenarios = JSON.parse(stored); // Store full objects now
      }
    } catch (e) { }
  }

  render() {
    return html`
      <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3 style="margin:0;">AI Planner</h3>
          <div style="display:flex; gap:0.5rem; align-items:center;">
             ${this.isLoading ? html`<span class="loading-spinner">⚙️</span>` : ''}
              ${this.savedScenarios.length > 0 ? html`
                  <button class="icon-only secondary" title="Toggle Comparison" @click=${() => this.showComparison = !this.showComparison}>
                      📊
                  </button>
              ` : ''}
          </div>
      </div>

      <div class="input-group">
          <input 
          type="text"
          placeholder="e.g. Cut dining by 20% and reduce AWS by $500"
          .value=${this.scenarioInput}
          @input=${(e: Event) => this.scenarioInput = (e.target as HTMLInputElement).value}
          @keypress=${(e: KeyboardEvent) => e.key === 'Enter' && this.runSimulation()}
          />
          <button ?disabled=${this.isLoading} @click=${this.runSimulation}>
            ${this.isLoading ? 'Planning...' : 'Plan'}
          </button>
      </div>
      
      ${this.successMessage ? html`
          <div class="toast">
              <span>✅</span> ${this.successMessage}
          </div>
      ` : ''}
      
      ${this.errorMessage ? html`<div style="color: var(--color-error); font-size: 0.9rem;">${this.errorMessage}</div>` : ''}

      <div class="scroll-container">
          
          ${this.showComparison ? this.renderComparisonTable() : html`
            
              ${this.planExplanation ? html`
                <div style="color: var(--color-text-secondary); margin: 0.5rem 0; font-style: italic; font-size: 0.9rem;">
                    AI Goal: "${this.planExplanation}"
                </div>
              ` : ''}
    
              ${this.simulatedActions.length > 0 ? html`
                <div class="action-list">
                    ${this.simulatedActions.map((action, i) => this.renderActionItem(action, i))}
                </div>
    
                <div class="results-summary">
                    <div class="summary-row">
                        <span>Current Budget</span>
                        <span>$${budgetStore.state.metrics.total_expenses.toFixed(2)}</span>
                    </div>
                    <div class="summary-row">
                        <span>Projected Savings</span>
                        <span class="impact-positive">-$${Math.abs(this.projectedSavings || 0).toFixed(2)}</span>
                    </div>
                    <div class="summary-row">
                        <span>New Total</span>
                        <span>$${(this.simulatedTotal || 0).toFixed(2)}</span>
                    </div>
                </div>
                
                <div class="toolbar" style="justify-content: space-between; align-items: center;">
                    <button class="secondary" @click=${this.addAction} style="border-style: dashed;">+ Add Step</button>
                    <div style="display:flex; gap:0.5rem;">
                        <button class="success" @click=${this.applyPlan}>Apply</button>
                        ${this.undoStack.length > 0 ? html`
                            <button class="secondary" @click=${this.undoLast}>Undo</button>
                        ` : ''}
                        <button class="secondary" @click=${this.saveScenario}>Save</button>
                        <button class="secondary" @click=${this.exportPlan}>Export</button>
                    </div>
                </div>
              ` : ''}
              
              ${this.savedScenarios.length > 0 && !this.showComparison ? html`
                <div class="saved-scenarios">
                    <small style="color: var(--color-text-secondary); display:block; margin-bottom:0.5rem;">Saved Scenarios:</small>
                    ${this.savedScenarios.map(s => html`
                        <span class="saved-chip" @click=${() => this.loadScenario(s.name)}>${s.name}</span>
                    `)}
                </div>
              ` : ''}

          `}
      </div>
    `;
  }

  renderComparisonTable() {
    const current = budgetStore.state.metrics.total_expenses;
    return html`
        <div style="margin-bottom:1rem;">
            <h4>Scenario Comparison</h4>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Savings</th>
                        <th>New Total</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.savedScenarios.map(s => html`
                        <tr style="cursor:pointer;" @click=${() => { this.loadScenario(s.name); this.showComparison = false; }}>
                            <td>${s.name}</td>
                            <td class="impact-positive">-$${(s.savings || 0).toFixed(0)}</td>
                            <td>$${(current - (s.savings || 0)).toFixed(0)}</td>
                            <td>${s.actions.length}</td>
                        </tr>
                    `)}
                </tbody>
            </table>
            <button class="secondary" style="margin-top:1rem; width:100%" @click=${() => this.showComparison = false}>Back to Planner</button>
        </div>
      `;
  }

  renderActionItem(action: PlanAction, index: number) {
    const isPositive = (action.calculatedDelta || 0) > 0;
    const isSavings = (action.calculatedDelta || 0) < 0; // Savings = negative delta (cost reduction)

    if (action.isEditing) {
      return html`
            <div class="action-item">
                <div class="edit-form">
                    <select .value=${action.action} @change=${(e: any) => this.updateAction(index, 'action', e.target.value)}>
                        <option value="reduce">Reduce</option>
                        <option value="increase">Increase</option>
                        <option value="set">Set</option>
                    </select>
                    <input type="text" placeholder="Target (e.g. Dining)" .value=${action.target} @change=${(e: any) => this.updateAction(index, 'target', e.target.value)} />
                    <input type="number" placeholder="Amount" .value=${action.amount} @change=${(e: any) => this.updateAction(index, 'amount', parseFloat(e.target.value))} />
                    <select .value=${action.unit} @change=${(e: any) => this.updateAction(index, 'unit', e.target.value)}>
                        <option value="absolute">$</option>
                        <option value="percent">%</option>
                    </select>
                    <button class="success icon-only" @click=${() => this.toggleEdit(index)}>✓</button>
                </div>
            </div>
         `;
    } else {
      return html`
            <div class="action-item">
                <div class="action-icon">
                    ${action.action === 'reduce' ? '↓' : (action.action === 'increase' ? '↑' : '=')}
                </div>
                <div class="action-details">
                    <span class="action-title">
                        ${index + 1}. ${this.capitalize(action.action)} ${this.capitalize(action.target)}
                    </span>
                    <span class="action-desc">
                        By ${action.amount}${action.unit === 'percent' ? '%' : ''} 
                    </span>
                </div>
                <div class="action-stats">
                    <div class="action-impact ${isSavings ? 'impact-positive' : (isPositive ? 'impact-negative' : '')}">
                        ${(action.calculatedDelta || 0) < 0 ? '-' : '+'}$${Math.abs(action.calculatedDelta || 0).toFixed(0)}
                    </div>
                    ${action.cumulativeTotal !== undefined ? html`
                        <div class="action-cumulative">Running: $${action.cumulativeTotal.toFixed(0)}</div>
                    ` : ''}
                </div>
                <div class="action-controls">
                    <button class="icon-only secondary" @click=${() => this.moveAction(index, -1)} ?disabled=${index === 0}>↑</button>
                    <button class="icon-only secondary" @click=${() => this.moveAction(index, 1)} ?disabled=${index === this.simulatedActions.length - 1}>↓</button>
                    <button class="icon-only secondary" @click=${() => this.toggleEdit(index)}>✎</button>
                    <button class="icon-only danger" @click=${() => this.removeAction(index)}>🗑</button>
                </div>
            </div>
         `;
    }
  }

  // --- Actions ---

  addAction() {
    const newAction: PlanAction = {
      action: 'reduce',
      target: 'Dining',
      amount: 0,
      unit: 'absolute',
      isEditing: true, // Start in edit mode
      calculatedDelta: 0
    };
    this.simulatedActions = [...this.simulatedActions, newAction];
    this.recalculatePlan(this.simulatedActions);
  }

  toggleEdit(index: number) {
    const actions = [...this.simulatedActions];
    actions[index].isEditing = !actions[index].isEditing;
    if (!actions[index].isEditing) {
      // Recalculate if saving
      this.recalculatePlan(actions);
    } else {
      this.simulatedActions = actions;
    }
  }

  updateAction(index: number, field: keyof PlanAction, value: any) {
    const actions = [...this.simulatedActions];
    (actions[index] as any)[field] = value;
    this.simulatedActions = actions;
  }

  moveAction(index: number, direction: number) {
    const newIndex = index + direction;
    // Bounds check
    if (newIndex < 0 || newIndex >= this.simulatedActions.length) {
      return;
    }

    const actions = [...this.simulatedActions];
    const temp = actions[index];
    actions[index] = actions[newIndex];
    actions[newIndex] = temp;

    // Recalculate (this sets simulatedActions internally)
    this.recalculatePlan(actions);

    // Explicitly trigger UI update to ensure disabled states on buttons refresh
    this.requestUpdate();
  }

  removeAction(index: number) {
    const actions = [...this.simulatedActions];
    actions.splice(index, 1);
    this.recalculatePlan(actions);
  }

  // Recalculates totals locally without re-querying AI
  recalculatePlan(actions: PlanAction[]) {
    const metrics = budgetStore.state.metrics;
    const breakdown = metrics.category_breakdown || {};
    let totalDelta = 0;

    // We compute Running Total starting from Base
    let runningTotal = metrics.total_expenses;

    actions.forEach(action => {
      const target = action.target.toLowerCase();
      const keys = Object.keys(breakdown);
      const key = keys.find(k => k.toLowerCase() === target || k.toLowerCase().includes(target));
      const base = key ? breakdown[key] : 0;

      let delta = 0;
      if (base > 0) {
        if (action.unit === 'percent') delta = base * (action.amount / 100);
        else delta = action.amount;

        if (action.action === 'increase') delta = -delta;
        else if (action.action === 'set') delta = base - action.amount;
      }

      // calculatedDelta = Change in Spend.
      // If action is 'reduce' by $100, delta is $100. Change in spend is -$100.
      // If action is 'increase' by $100, delta is -$100. Change in spend is +$100.
      // If action is 'set' to $50 (from $100), delta is $50. Change in spend is -$50.
      const changeInSpend = (action.action === 'increase') ? Math.abs(delta) : -Math.abs(delta);
      action.calculatedDelta = changeInSpend;

      totalDelta += delta; // totalDelta accumulates the 'savings' amount (positive for savings)

      runningTotal += changeInSpend;
      action.cumulativeTotal = runningTotal;
    });

    this.simulatedActions = actions;
    this.projectedSavings = totalDelta;
    this.simulatedTotal = metrics.total_expenses - totalDelta;
  }

  capitalize(s: string) { return s.charAt(0).toUpperCase() + s.slice(1); }

  async runSimulation() {
    this.errorMessage = '';
    this.projectedSavings = null;
    this.simulatedTotal = null;
    this.simulatedActions = [];
    this.isLoading = true;

    if (!this.scenarioInput.trim()) {
      this.isLoading = false;
      return;
    }

    try {
      const plan = await budgetService.planSimulation(this.scenarioInput);
      if (!plan || !plan.actions || plan.actions.length === 0) {
        this.errorMessage = "Could not understand scenario.";
        this.isLoading = false;
        return;
      }
      this.planExplanation = plan.explanation || "";
      const metrics = budgetStore.state.metrics;
      const breakdown = metrics.category_breakdown || {};
      const projectBreakdown = metrics.project_breakdown || {};
      const topMerchants = metrics.top_merchants || {};
      let totalDelta = 0;
      const processedActions: PlanAction[] = [];

      let runningTotal = metrics.total_expenses;

      for (const action of plan.actions) {
        const target = action.target; // Trusted canonical name from backend
        let matchedAmount = 0;
        let matchedSource = '';
        let found: number | undefined = undefined; // Initialize found to handle its scope

        // 1. Direct Canonical Lookup (Primary)
        // We trust the backend has already resolved 'target' to the exact canonical name found in the database.
        if (breakdown[target] !== undefined) {
          matchedAmount = breakdown[target];
          matchedSource = 'Category';
          found = matchedAmount;
        } else if (projectBreakdown[target] !== undefined) {
          matchedAmount = projectBreakdown[target];
          matchedSource = 'Project';
          found = matchedAmount;
        } else if (topMerchants[target] !== undefined) {
          matchedAmount = topMerchants[target];
          matchedSource = 'Merchant';
          found = matchedAmount;
        } else {
          // Extended Search: Look in detailed merchant lists (Cat 4.7 Fix)
          // Fix: Aggregate across ALL categories instead of breaking on first match
          let totalMerchantSpend = 0;
          let merchantFound = false;

          const categoryMerchants = metrics.category_merchants || {};
          for (const cat of Object.keys(categoryMerchants)) {
            if (categoryMerchants[cat] && categoryMerchants[cat][target] !== undefined) {
              totalMerchantSpend += categoryMerchants[cat][target];
              merchantFound = true;
            }
          }

          if (merchantFound) {
            matchedAmount = totalMerchantSpend;
            matchedSource = 'Merchant';
            found = matchedAmount;
          } else {
            // If not found in categories (unlikely for expense), try projects
            let totalProjectSpend = 0;
            let projectFound = false;

            const projectMerchants = metrics.project_merchants || {};
            for (const proj of Object.keys(projectMerchants)) {
              if (projectMerchants[proj] && projectMerchants[proj][target] !== undefined) {
                totalProjectSpend += projectMerchants[proj][target];
                projectFound = true;
              }
            }

            if (projectFound) {
              matchedAmount = totalProjectSpend;
              matchedSource = 'Merchant';
              found = matchedAmount;
            }
          }

          if (found === undefined) {
            console.warn(`[Simulator] Target entity '${target}' not found in extended metrics. Resolution failed or entity has no spend.`);
          }
        }
        let delta = 0;
        if (matchedSource && found !== undefined) { // Use `undefined` for strict check
          matchedAmount = found;
          if (action.unit === 'percent') delta = matchedAmount * (action.amount / 100);
          else delta = action.amount;
          if (action.action === 'increase') delta = -delta;
          else if (action.action === 'set') delta = matchedAmount - action.amount;
        }
        totalDelta += delta;

        const changeInSpend = (action.action === 'increase') ? Math.abs(delta) : -Math.abs(delta);
        runningTotal += changeInSpend;

        processedActions.push({
          ...action,
          calculatedDelta: changeInSpend,
          cumulativeTotal: runningTotal
        });
      }
      this.simulatedActions = processedActions;
      this.projectedSavings = totalDelta;
      this.simulatedTotal = metrics.total_expenses - totalDelta;
    } catch (e) {
      this.errorMessage = 'Simulation failed. Please try again.';
      console.error(e);
    } finally {
      this.isLoading = false;
    }
  }

  applyPlan() {
    // Push to Undo Stack
    const currentSnapshot = JSON.parse(JSON.stringify(budgetStore.state.metrics));
    this.undoStack.push(currentSnapshot);
    if (this.undoStack.length > 5) this.undoStack.shift();

    const newMetrics = JSON.parse(JSON.stringify(currentSnapshot));
    newMetrics.total_expenses = this.simulatedTotal;

    budgetStore.setData({
      transactions: budgetStore.state.transactions,
      metrics: newMetrics
    }, "AI Simulation");

    this.successMessage = "Scenario Applied! Charts updated.";
    setTimeout(() => this.successMessage = '', 3000);
  }

  undoLast() {
    const prev = this.undoStack.pop();
    if (prev) {
      budgetStore.setData({
        transactions: budgetStore.state.transactions,
        metrics: prev
      }, "Undo Simulation");
      this.successMessage = "Undo Successful.";
      setTimeout(() => this.successMessage = '', 3000);
      this.requestUpdate();
    }
  }

  saveScenario() {
    const name = prompt("Name this scenario:", this.scenarioInput);
    if (!name) return;
    const scenario = {
      name,
      input: this.scenarioInput,
      actions: this.simulatedActions,
      savings: this.projectedSavings,
      date: new Date().toISOString()
    };

    const stored = localStorage.getItem('budget_scenarios');
    const list = stored ? JSON.parse(stored) : [];
    list.push(scenario);
    localStorage.setItem('budget_scenarios', JSON.stringify(list));
    this.loadSavedScenarios();
    this.successMessage = "Scenario Saved.";
    setTimeout(() => this.successMessage = '', 3000);
  }

  loadScenario(name: string) {
    const stored = localStorage.getItem('budget_scenarios');
    if (stored) {
      const list = JSON.parse(stored);
      const s = list.find((x: any) => x.name === name);
      if (s) {
        this.scenarioInput = s.input;
        this.simulatedActions = s.actions || [];
        this.projectedSavings = s.savings;
        this.simulatedTotal = budgetStore.state.metrics.total_expenses - (s.savings || 0);
        this.planExplanation = "Loaded from history";
      }
    }
  }

  exportPlan() {
    const data = {
      goal: this.scenarioInput,
      explanation: this.planExplanation,
      actions: this.simulatedActions,
      impact: {
        savings: this.projectedSavings,
        new_total: this.simulatedTotal
      }
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `budget-scenario-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    this.successMessage = "Plan Exported.";
    setTimeout(() => this.successMessage = '', 3000);
  }
}
