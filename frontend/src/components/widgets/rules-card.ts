import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { budgetStore } from '../../store/budget-store';
import { RulePatternSchema, CategorySchema, getValidationError } from '../../utils/validation';
import { Rule } from '../../types/interfaces';

@customElement('rules-card')
export class RulesCard extends LitElement {
  @property({ type: Array }) rules: Rule[] = [];

  private unsubscribe: (() => void) | null = null;

  connectedCallback() {
    super.connectedCallback();
    this.unsubscribe = budgetStore.getStore().subscribe(() => {
      this.requestUpdate();
    });
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.unsubscribe?.();
  }

  // Local state for inputs
  @state() pattern: string = '';
  @state() category: string = '';
  @state() private patternError: string = '';
  @state() private categoryError: string = '';

  // Derived state from store
  get suggestions() {
    return budgetStore.state.metrics.flash_fill || [];
  }

  @state() isOpen: boolean = false;
  @state() activeTab: 'active' | 'suggested' = 'active';

  static styles = css`
    :host {
      position: fixed;
      top: 80px; /* Below navbar roughly */
      right: 0;
      bottom: 20px;
      width: 450px;
      z-index: 50;
      display: flex;
      flex-direction: row;
      transform: translateX(100%);
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      pointer-events: none; /* Allow clicking through when collapsed */
    }

    :host([open]) {
      transform: translateX(0);
      pointer-events: auto;
    }

    /* Interactive area needs pointer events */
    .toggle-handle {
      position: absolute;
      left: -48px;
      top: 0;
      width: 48px;
      height: 48px;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-right: none;
      border-radius: var(--radius-xl) 0 0 var(--radius-xl);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--color-text);
      font-size: 1.5rem;
      box-shadow: -4px 0 15px rgba(0,0,0,0.2);
      pointer-events: auto; /* Always clickable */
    }
    
    .sidebar-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-right: none;
      border-radius: var(--radius-xl) 0 0 var(--radius-xl);
      padding: 1.5rem;
      height: 100%;
      overflow: hidden;
      box-sizing: border-box;
      box-shadow: -10px 0 30px rgba(0,0,0,0.5);
      pointer-events: auto;
    }

    /* ... Rest of existing styles adapter for scoped content ... */
    
    * { box-sizing: border-box; }

    h2 {
      flex: 0 0 auto;
      font-size: var(--font-size-lg);
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
      overflow-x: auto;
      min-height: 0;
      padding-right: 0.25rem;
    }

    .form-group {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
      flex: 0 0 auto;
    }

    .form-input {
      flex: 1;
      padding: 0.75rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--color-border);
      background: rgba(255,255,255,0.05);
      color: var(--color-text);
      font-family: var(--font-family);
    }

    .form-input:focus {
      outline: none;
      border-color: var(--color-primary);
    }

    .btn-submit {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      color: var(--color-text);
      padding: 0 1.5rem;
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
    }

    .btn-submit:hover {
      border-color: var(--color-primary);
      color: var(--color-primary);
      background: rgba(59, 130, 246, 0.1);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }

    th {
      text-align: left;
      padding: 0.75rem 1rem;
      color: var(--color-text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--color-border);
      background: rgba(255,255,255,0.02);
    }

    td {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      color: var(--color-text);
    }

    tr:last-child td {
      border-bottom: none;
    }

    .rule-pattern {
      font-family: monospace;
      background: rgba(0,0,0,0.3);
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-size: 0.85rem;
      color: var(--color-primary);
    }

    .btn-delete {
      background: transparent;
      border: none;
      color: var(--color-text-muted);
      cursor: pointer;
      padding: 0.4rem;
      border-radius: 4px;
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .btn-delete:hover {
      background: rgba(239, 68, 68, 0.1);
      color: var(--color-error);
    }
    .header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }

    .tabs {
      display: flex;
      gap: 0.5rem;
      background: rgba(0,0,0,0.2);
      padding: 0.25rem;
      border-radius: var(--radius-md);
    }

    .tab-btn {
      background: transparent;
      border: none;
      color: var(--color-text-muted);
      padding: 0.5rem 1rem;
      border-radius: var(--radius-sm);
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
      transition: all 0.2s;
    }

    .tab-btn.active {
      background: var(--color-primary);
      color: white;
    }

    .badge-count {
      font-size: 0.7rem;
      background: var(--color-surface-hover);
      padding: 0.1rem 0.3rem;
      border-radius: 4px;
      margin-left: 0.5rem;
      opacity: 0.8;
    }

    .btn-approve {
      background: transparent;
      border: none;
      color: var(--color-success);
      cursor: pointer;
      font-size: 1.1rem;
      padding: 0.4rem;
      transition: transform 0.2s;
    }

    .btn-approve:hover {
      transform: scale(1.2);
    }

    .empty-state {
        color: var(--color-text-muted); 
        font-style: italic; 
        text-align: center; 
        padding: 2rem;
    }
  `;

  updated(changedProperties: Map<string, any>) {
    if (changedProperties.has('isOpen')) {
      if (this.isOpen) {
        this.setAttribute('open', '');
      } else {
        this.removeAttribute('open');
      }
    }
  }

  render() {
    return html`
      <button class="toggle-handle" @click=${() => this.isOpen = !this.isOpen} aria-label="Toggle Rules Sidebar">
            ${this.isOpen ? '→' : '📏'}
      </button>

      <div class="sidebar-content">
        <div class="header-row">
            <h2>📏 Rules Engine</h2>
            <div class="tabs">
            <button class="tab-btn ${this.activeTab === 'active' ? 'active' : ''}" @click=${() => this.activeTab = 'active'}>Active Rules</button>
            <button class="tab-btn ${this.activeTab === 'suggested' ? 'active' : ''}" @click=${() => this.activeTab = 'suggested'}>Suggested Rules</button>
            </div>
        </div>
        
        ${this.activeTab === 'active' ? this.renderActiveRules() : this.renderSuggestedRules()}
      </div>
    `;
  }

  renderActiveRules() {
    return html`
      <div class="form-group">
        <label for="pattern-input" class="sr-only">Match Pattern</label>
        <input 
          id="pattern-input"
          class="form-input ${this.patternError ? 'error' : ''}"
          type="text" 
          placeholder="Match Pattern (Regex)" 
          .value=${this.pattern}
          @input=${(e: Event) => { this.pattern = (e.target as HTMLInputElement).value; this.patternError = ''; }}
        />
        <input 
          id="category-input"
          class="form-input ${this.categoryError ? 'error' : ''}"
          type="text" 
          placeholder="Assign Category" 
          .value=${this.category}
          @input=${(e: Event) => { this.category = (e.target as HTMLInputElement).value; this.categoryError = ''; }}
          @keydown=${(e: KeyboardEvent) => e.key === 'Enter' && this.addRule()}
        />
        <button class="btn-submit" @click=${this.addRule}>Add Rule</button>
      </div>
      
      <div class="scroll-content">
        ${this.rules.length > 0 ? html`
          <table>
            <thead>
              <tr>
                <th style="width: 45%;">Pattern</th>
                <th style="width: 45%;">Category</th>
                <th style="width: 10%;">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${this.rules.map(rule => html`
                <tr>
                  <td><span class="rule-pattern">${rule.pattern}</span></td>
                  <td>${rule.category}</td>
                  <td>
                    <button class="btn-delete" @click=${() => budgetStore.deleteRule(rule.id)} title="Delete Rule">
                      🗑️
                    </button>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
          <div class="empty-state">No active rules defined.</div>
        `}
      </div>
    `;
  }

  renderSuggestedRules() {
    return html`
      <div class="scroll-content">
        ${this.suggestions.length > 0 ? html`
          <table>
            <thead>
              <tr>
                <th style="width: 45%;">Pattern (Description)</th>
                <th style="width: 45%;">Suggested Category</th>
                <th style="width: 10%;">Action</th>
              </tr>
            </thead>
            <tbody>
              ${this.suggestions.map(suggestion => html`
                <tr>
                  <td><span class="rule-pattern">${suggestion.description}</span> <span class="badge-count">x${suggestion.count}</span></td>
                  <td>${suggestion.suggested_category}</td>
                  <td>
                    <button class="btn-approve" 
                      @click=${() => this.approveSuggestion(suggestion)} 
                      title="Promote to Rule">
                      ✅
                    </button>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
           <div class="empty-state">No AI suggestions available.</div>
        `}
      </div>
    `;
  }

  private approveSuggestion(suggestion: { description: string; suggested_category: string }) {
    budgetStore.addRule(suggestion.description, suggestion.suggested_category);
  }

  private addRule() {
    // Validate inputs
    const patternResult = RulePatternSchema.safeParse(this.pattern);
    const categoryResult = CategorySchema.safeParse(this.category);

    if (!patternResult.success) {
      this.patternError = getValidationError(patternResult.error);
      return;
    } else {
      this.patternError = '';
    }

    if (!categoryResult.success) {
      this.categoryError = getValidationError(categoryResult.error);
      return;
    } else {
      this.categoryError = '';
    }

    if (this.pattern && this.category) {
      budgetStore.addRule(this.pattern, this.category);
      this.pattern = '';
      this.category = '';
    }
  }
}
