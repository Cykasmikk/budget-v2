import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { budgetStore } from '../../store/budget-store';
import { User } from '../../store/auth-store';
import '../file-upload';

@customElement('app-shell')
export class AppShell extends LitElement {
  @property({ type: Object }) metrics: any = {};
  @property({ type: Number }) budgetLimit: number = 0;
  @property({ type: Object }) user: User | null = null;
  @property({ type: String }) activeTab: string = 'dashboard';

  private handleNavClick(tab: string) {
    this.dispatchEvent(new CustomEvent('nav-change', {
      detail: { tab },
      bubbles: true,
      composed: true
    }));
  }

  static styles = css`
    :host {
      display: flex;
      height: 100vh;
      overflow: hidden;
      background-color: var(--color-background);
      color: var(--color-text);
    }

    aside {
      width: var(--sidebar-width);
      background-color: var(--color-surface);
      border-right: 1px solid var(--color-border);
      display: flex;
      flex-direction: column;
      padding: 1rem;
      gap: 1rem;
      overflow-y: auto;
    }

    .brand {
      font-size: var(--font-size-lg);
      font-weight: 700;
      color: var(--color-text);
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex: 0 0 auto;
      min-height: 2rem;
    }

    .brand span {
      background: var(--gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .budget-status {
      padding: 0.75rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      flex: 0 0 auto;
    }

    .budget-label {
      font-size: 0.7rem;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.125rem;
    }

    .budget-value {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--color-text);
      font-feature-settings: "tnum";
    }

    .budget-remaining {
      font-size: 0.75rem;
      margin-top: 0.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    nav {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      /* flex: 1; Removed to allow subsequent items (Data Controls) to sit just below */
      margin-bottom: 2rem; /* Add some spacing before data controls */
    }

    .nav-item {
      padding: 0.5rem 0.75rem;
      border-radius: var(--radius-md);
      color: var(--color-text-muted);
      cursor: pointer;
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-weight: 500;
      border: 1px solid transparent;
      font-size: 0.9rem;
    }

    .nav-item:hover {
      background-color: rgba(255, 255, 255, 0.03);
      color: var(--color-text);
    }

    .nav-item.active {
      background-color: rgba(59, 130, 246, 0.1);
      color: var(--color-primary);
      border-color: rgba(59, 130, 246, 0.2);
    }

    .upload-section {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding-top: 1rem;
      border-top: 1px solid var(--color-border);
      flex: 0 0 auto;
    }

    .action-button {
      width: 100%;
      padding: 0.625rem;
      background: rgba(59, 130, 246, 0.1);
      border: 1px solid var(--color-primary);
      color: var(--color-primary);
      border-radius: var(--radius-md);
      cursor: pointer;
      font-weight: 600;
      font-size: 0.8rem;
      transition: all var(--transition-fast);
      text-align: center;
    }

    .action-button:hover {
      background: rgba(59, 130, 246, 0.2);
      transform: translateY(-1px);
    }

    main {
      flex: 1;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    header {
      height: var(--header-height);
      border-bottom: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1.5rem;
      background-color: rgba(15, 17, 21, 0.8);
      backdrop-filter: blur(8px);
    }

    .content-area {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 0;
      height: 100%;
      position: relative;
    }

    /* Mobile (max 767px) - Bottom Navigation Layout */
    @media (max-width: 767px) {
      :host {
        flex-direction: column-reverse; /* Nav at bottom */
      }

      aside {
        width: 100%;
        height: auto;
        flex-direction: row;
        justify-content: space-around;
        padding: 0.5rem;
        border-right: none;
        border-top: 1px solid var(--color-border);
        flex: 0 0 auto;
      }

      /* Hide non-nav items in sidebar on mobile for simplicity, or adapt them */
      .brand, .budget-status, .upload-section {
        display: none;
      }

      nav {
        flex-direction: row;
        width: 100%;
        justify-content: space-around;
        margin-bottom: 0;
      }

      .nav-item {
        flex-direction: column;
        gap: 0.25rem;
        font-size: 0.7rem;
        padding: 0.5rem;
      }
    }

    /* 4K (min 3840px) - Scaled Sidebar */
    @media (min-width: 3840px) {
      aside {
        width: 400px;
        padding: 2rem;
      }
      
      .brand { font-size: 2.5rem; }
      .nav-item { font-size: 1.5rem; padding: 1rem; }
      .budget-value { font-size: 2rem; }
    }
  `;

  render() {
    const total = this.metrics.total_expenses || 0;
    return html`
      <aside>
        <div class="brand">
          <span>AI</span> Budget
        </div>
        
        <div class="budget-status">
          <div class="budget-label">Total Spent</div>
          <div class="budget-value">$${Number(total).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
        </div>


        <nav>
          <div 
            class="nav-item ${this.activeTab === 'dashboard' ? 'active' : ''}"
            @click=${() => this.handleNavClick('dashboard')}
          >
            <span>📊</span> Dashboard
          </div>
          <div 
            class="nav-item ${this.activeTab === 'files' ? 'active' : ''}"
            @click=${() => this.handleNavClick('files')}
          >
            <span>📁</span> Files
          </div>
          <div 
            class="nav-item ${this.activeTab === 'transactions' ? 'active' : ''}"
            @click=${() => this.handleNavClick('transactions')}
          >
            <span>💳</span> Transactions
          </div>
          <div 
            class="nav-item ${this.activeTab === 'settings' ? 'active' : ''}"
            @click=${() => this.handleNavClick('settings')}
          >
            <span>⚙️</span> Settings
          </div>
        </nav>

        <div class="upload-section">
          <div class="budget-label">Data Controls</div>
          
          <div style="display: flex; gap: 0.5rem;">
            <button 
              class="action-button"
              @click=${() => budgetStore.loadSampleData('A')}
            >
              Load Sample A
            </button>
            <button 
              class="action-button"
              @click=${() => budgetStore.loadSampleData('B')}
            >
              Load Sample B
            </button>
          </div>
          
          <button 
            class="action-button"
            style="margin-top: 0.5rem; width: 100%;"
            @click=${() => budgetStore.loadPartialData()}
          >
            Load Partial Update
          </button>

          <file-upload compact></file-upload>
        </div>
      </aside>
      <main>
        <header>
          <div style="font-weight: 600;">Dashboard Overview</div>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="font-size: 0.875rem; color: var(--color-text-muted);">
              ${this.user ? this.user.email : 'Guest Mode'}
            </div>
            ${this.user && this.user.role === 'admin' ? html`
              <span style="font-size: 0.65rem; padding: 2px 6px; background: var(--color-primary); color: white; border-radius: 4px; text-transform: uppercase;">Admin</span>
            ` : ''}
          </div>
        </header>
        <div class="content-area">
          <slot></slot>
        </div>
      </main>
    `;
  }
}
