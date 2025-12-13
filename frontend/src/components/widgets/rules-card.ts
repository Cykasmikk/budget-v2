import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { budgetStore } from '../../store/budget-store';
import { RulePatternSchema, CategorySchema, getValidationError } from '../../utils/validation';

@customElement('rules-card')
export class RulesCard extends LitElement {
  @property({ type: Array }) rules: any[] = [];

  // Local state for inputs
  @state() pattern: string = '';
  @state() category: string = '';
  @state() private patternError: string = '';
  @state() private categoryError: string = '';

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
      overflow-x: auto; /* Allow horizontal scroll for table */
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
  `;

  render() {
    return html`
      <h2>📏 Categorization Rules</h2>
      
      <div class="form-group">
        <label for="pattern-input" class="sr-only">Match Pattern</label>
        <input 
          id="pattern-input"
          class="form-input ${this.patternError ? 'error' : ''}"
          type="text" 
          placeholder="Match Pattern (Regex, e.g., ^(AWS|Azure).*)" 
          .value=${this.pattern}
          @input=${(e: Event) => { this.pattern = (e.target as HTMLInputElement).value; this.patternError = ''; }}
          aria-label="Match Pattern (Regex)"
          aria-invalid=${this.patternError ? 'true' : 'false'}
          aria-describedby=${this.patternError ? 'pattern-error' : undefined}
        />
        ${this.patternError ? html`<div id="pattern-error" class="error-message" style="color: var(--color-error); font-size: 0.8rem; margin-top: 0.25rem;">${this.patternError}</div>` : ''}
        <label for="category-input" class="sr-only">Assign Category</label>
        <input 
          id="category-input"
          class="form-input ${this.categoryError ? 'error' : ''}"
          type="text" 
          placeholder="Assign Category" 
          .value=${this.category}
          @input=${(e: Event) => { this.category = (e.target as HTMLInputElement).value; this.categoryError = ''; }}
          @keydown=${(e: KeyboardEvent) => e.key === 'Enter' && this.addRule()}
          aria-label="Assign Category"
          aria-invalid=${this.categoryError ? 'true' : 'false'}
          aria-describedby=${this.categoryError ? 'category-error' : undefined}
        />
        ${this.categoryError ? html`<div id="category-error" class="error-message" style="color: var(--color-error); font-size: 0.8rem; margin-top: 0.25rem;">${this.categoryError}</div>` : ''}
        <button class="btn-submit" @click=${this.addRule} aria-label="Add categorization rule">Add Rule</button>
      </div>
      
      <div class="scroll-content">
        ${this.rules.length > 0 ? html`
          <table aria-label="Categorization rules table">
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
                    <button class="btn-delete" @click=${() => budgetStore.deleteRule(rule.id)} title="Delete Rule" aria-label="Delete rule for ${rule.pattern}">
                      <span aria-hidden="true">🗑️</span>
                    </button>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        ` : html`
          <div style="color: var(--color-text-muted); font-style: italic; text-align: center; padding: 2rem;">
            No custom rules defined yet. Add a rule above to automatically categorize transactions.
          </div>
        `}
      </div>
    `;
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
