import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { authStore, AuthState } from './store/auth-store';
import './views/dashboard-view';
import './views/login-view';
import './views/callback-view';

@customElement('app-root')
export class AppRoot extends LitElement {
  static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background-color: var(--color-background, #f4f4f9);
      font-family: 'Inter', sans-serif;
    }
  `;

  @state() private auth: AuthState = authStore.state;

  private cleanup: (() => void) | undefined;

  connectedCallback() {
    super.connectedCallback();
    this.cleanup = authStore.subscribe(() => {
      this.auth = authStore.state;
    });
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.cleanup?.();
  }

  render() {
    // Check for Callback Route
    if (window.location.pathname.includes('/auth/callback')) {
      return html`<callback-view></callback-view>`;
    }

    if (this.auth.isLoading) {
      return html`<div>Loading...</div>`;
    }

    if (!this.auth.isAuthenticated) {
      return html`<login-view></login-view>`;
    }

    return html`<dashboard-view></dashboard-view>`;
  }
}
