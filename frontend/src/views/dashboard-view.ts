import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import { StoreController } from '../store/controller';
import { budgetStore } from '../store/budget-store';
import { authStore } from '../store/auth-store';
import { uiStore } from '../store/ui-store';

import '../components/layout/app-shell';
import '../components/widgets/analysis-card';
import '../views/files-view';
import '../views/settings-view';

@customElement('dashboard-view')
export class DashboardView extends LitElement {
  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
      background-color: var(--color-background);
      overflow: hidden;
    }

    .grid-dashboard {
      display: grid; 
      grid-template-columns: repeat(12, 1fr);
      grid-template-rows: 1fr; /* Single row for Analysis */
      gap: 1rem;
      padding: 1rem;
      box-sizing: border-box;
      max-width: 1600px;
      margin: 0 auto;
      height: 100%;
      max-height: 100%;
      overflow: hidden; /* Prevent scrolling */
      min-height: 0; /* Critical for grid children to respect container bounds */
    }

    /* Grid Spans */
    .span-2 { grid-column: span 2; }
    .span-3 { grid-column: span 3; }
    .span-4 { grid-column: span 4; }
    .span-6 { grid-column: span 6; }
    .span-8 { grid-column: span 8; }
    .span-12 { 
      grid-column: span 12;
      min-height: 0; /* Critical: prevents grid items from overflowing */
      overflow: hidden;
    }
    
    .row-span-2 { grid-row: span 1; } /* Adjusted to match template-rows logic or remove if unnecessary */

    /* Widget Heights - Removed fixed min-heights in favor of grid sizing */

    /* Responsive Breakpoints */
    /* Mobile (320px - 767px) */
    @media (max-width: 767px) {
      .grid-dashboard {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding: 0.75rem;
        height: auto;
        overflow-y: auto;
      }
      
      .span-2, .span-3, .span-4, .span-6, .span-8, .span-12 {
        grid-column: auto;
        width: 100%;
      }
    }

    /* Tablet (768px - 1199px) */
    @media (min-width: 768px) and (max-width: 1199px) {
      .grid-dashboard {
        grid-template-columns: repeat(6, 1fr);
        padding: 1rem;
      }
      
      .span-2 { grid-column: span 3; }
      .span-3 { grid-column: span 3; }
      .span-4 { grid-column: span 6; }
      .span-6 { grid-column: span 6; }
      .span-8 { grid-column: span 6; }
    }

    /* Desktop (1200px - 1919px) - default */
    @media (min-width: 1200px) and (max-width: 1919px) {
      .span-2 { grid-column: span 2; }
      .span-3 { grid-column: span 3; }
      .span-4 { grid-column: span 4; }
      .span-6 { grid-column: span 6; }
      .span-8 { grid-column: span 8; }
    }

    /* Large Desktop (1920px - 3839px) */
    @media (min-width: 1920px) and (max-width: 3839px) {
      .grid-dashboard {
        max-width: 2000px;
        gap: 1.5rem;
        padding: 1.5rem;
      }
    }

    /* 4K (3840px+) */
    @media (min-width: 3840px) {
      .grid-dashboard {
        max-width: 4000px;
        gap: 3rem;
        padding: 3rem;
        font-size: 1.25rem; /* Scale text for 4K */
      }
    }
  `;

  // @ts-ignore: Controller is used for reactivity even if not accessed directly
  private storeController = new StoreController(this, budgetStore.getStore());

  // Also subscribe to auth store
  // @ts-ignore
  private authController = new StoreController(this, authStore);

  // Subscribe to UI store for navigation state
  // @ts-ignore
  private uiController = new StoreController(this, uiStore);

  connectedCallback() {
    super.connectedCallback();
    budgetStore.fetchRules();

    // Note: Sample data loading removed - users should upload their own data
    // Sample data can still be loaded manually via the app shell menu if needed for demos
  }

  private handleNavChange(e: CustomEvent) {
    uiStore.setActiveTab(e.detail.tab);
  }

  render() {
    const state = budgetStore.state;
    const authState = authStore.state;
    const activeTab = uiStore.state.activeTab;

    return html`
      <app-shell
        .metrics=${state.metrics}
        .budgetLimit=${state.budgetLimit}
        .user=${authState.user}
        .activeTab=${activeTab}
        @nav-change=${this.handleNavChange}
      >
        ${activeTab === 'dashboard' ? html`
          <div class="grid-dashboard">
            <!-- Main Analysis Console (Span 12) -->
            <div class="span-12">
              <analysis-card 
                .metrics=${state.metrics}
                .viewMode=${state.viewMode}
                .budgetLimit=${state.budgetLimit}
                .isLoading=${state.isLoading}
              ></analysis-card>
            </div>
          </div>
        ` : ''}

        ${activeTab === 'files' ? html`<files-view></files-view>` : ''}
        ${activeTab === 'settings' ? html`<settings-view></settings-view>` : ''}
      </app-shell>
    `;
  }
}
