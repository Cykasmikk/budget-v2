import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { authStore } from '../store/auth-store';
import { EmailSchema, PasswordSchema, getValidationError } from '../utils/validation';
import { logger } from '../services/logger';

@customElement('login-view')
export class LoginView extends LitElement {
  static styles = css`
    :host {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background-color: var(--color-background);
      color: var(--color-text);
      font-family: 'Inter', sans-serif;
      overflow: hidden;
      position: relative;
    }

    /* Background decorative elements (similar to dashboard subtle gradients if any, or just clean) */
    :host::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(circle at center, rgba(59,130,246,0.03) 0%, transparent 50%);
      z-index: 0;
      pointer-events: none;
    }

    .login-card {
      position: relative;
      z-index: 1;
      background: var(--color-surface);
      padding: 3rem;
      border-radius: var(--radius-lg, 16px);
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); /* Deep shadow for floating effect */
      width: 100%;
      max-width: 400px;
      text-align: center;
      border: 1px solid var(--color-border);
      backdrop-filter: blur(12px);
    }

    .brand {
      font-size: 2rem;
      font-weight: 800;
      margin-bottom: 2rem;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 0.5rem;
      color: var(--color-text);
    }

    .brand span {
      background: var(--gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    h1 {
      margin-bottom: 0.5rem;
      color: var(--color-text);
      font-weight: 600;
      font-size: 1.5rem;
      letter-spacing: -0.025em;
    }
    
    p.subtitle {
      color: var(--color-text-muted);
      margin-bottom: 2rem;
      font-size: 0.95rem;
    }

    .input-group {
      margin-bottom: 1.25rem;
      text-align: left;
    }
    
    label {
      display: block;
      margin-bottom: 0.5rem;
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--color-text-muted);
    }

    input {
      width: 100%;
      padding: 0.75rem 1rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md, 8px);
      font-size: 1rem;
      outline: none;
      transition: all 0.2s;
      box-sizing: border-box; 
      color: var(--color-text);
    }

    input:focus {
      border-color: var(--color-primary);
      background: rgba(59, 130, 246, 0.05); /* Subtle blue tint */
      box-shadow: 0 0 0 1px var(--color-primary);
    }

    input::placeholder {
      color: rgba(255, 255, 255, 0.2);
    }

    .btn {
      width: 100%;
      padding: 0.875rem;
      border-radius: var(--radius-md, 8px);
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      border: none;
      margin-bottom: 1rem;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 0.5rem;
    }

    .btn-primary {
      background: var(--color-primary);
      color: white;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .btn-primary:hover {
      background: #2563eb; /* Slightly lighter shade manually if var not avail, or filter brightness */
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
    
    .btn-secondary {
      background: transparent;
      color: var(--color-text);
      border: 1px solid var(--color-border);
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--color-text-muted);
    }

    .divider {
      display: flex;
      align-items: center;
      text-align: center;
      margin: 1.5rem 0;
      color: var(--color-text-muted);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .divider::before, .divider::after {
      content: '';
      flex: 1;
      border-bottom: 1px solid var(--color-border);
    }
    
    .divider:not(:empty)::before {
      margin-right: 1em;
    }

    .divider:not(:empty)::after {
      margin-left: 1em;
    }
    
    .error-msg {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: var(--color-error, #ef4444);
        padding: 0.75rem;
        border-radius: var(--radius-md, 8px);
        font-size: 0.875rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
  `;

  @state() email = '';
  @state() password = '';
  @state() error = '';
  @state() loading = false;
  @state() emailError = '';
  @state() passwordError = '';

  @state() private ssoEnabled = false;
  @state() private ssoProviderName = '';

  async connectedCallback() {
    super.connectedCallback();
    // Check if SSO is enabled for the default tenant
    try {
      const response = await fetch('/api/v1/settings');
      if (response.ok) {
        const data = await response.json();
        if (data.auth_config && data.auth_config.enabled) {
          this.ssoEnabled = true;
          this.ssoProviderName = data.auth_config.provider_name;
        }
      }
    } catch (e) {
      const error = e instanceof Error ? e : new Error(String(e));
      logger.error("Failed to check SSO status", 'LoginView', error);
    }
  }

  async handleSSOLogin() {
    try {
      const response = await fetch('/api/v1/auth/sso/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          callback_url: window.location.origin + '/auth/callback', // We need to handle this route!
          email: this.email // Optional hint
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        }
      } else {
        const err = await response.json();
        this.error = "SSO Init Failed: " + err.detail;
      }
    } catch (e) {
      this.error = "Failed to start SSO flow.";
    }
  }

  async handleLogin(e: Event) {
    e.preventDefault();
    
    // Validate inputs
    const emailResult = EmailSchema.safeParse(this.email);
    const passwordResult = PasswordSchema.safeParse(this.password);

    if (!emailResult.success) {
      this.emailError = getValidationError(emailResult.error);
      return;
    } else {
      this.emailError = '';
    }

    if (!passwordResult.success) {
      this.passwordError = getValidationError(passwordResult.error);
      return;
    } else {
      this.passwordError = '';
    }

    this.loading = true;
    this.error = '';

    try {
      const response = await fetch(`/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: this.email, password: this.password })
      });

      if (!response.ok) throw new Error('Invalid credentials');

      const data = await response.json();
      authStore.loginSuccess({ email: data.user, role: data.role });

      // Redirect handled by Router observing store
    } catch (err) {
      this.error = "Invalid email or password.";
    } finally {
      this.loading = false;
    }
  }

  async handleGuestAccess() {
    this.loading = true;
    this.error = '';

    try {
      const response = await fetch(`/api/v1/auth/guest`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Guest creation failed' }));
        
        // Handle rate limiting specifically
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait before trying again, or clear your browser cache/cookies.');
        }
        
        throw new Error(errorData.detail || `HTTP ${response.status}: Guest creation failed`);
      }

      await response.json();
      
      // Guest user is fake/viewer
      authStore.loginSuccess({ email: 'guest@demo.local', role: 'viewer' });
      // Router will handle redirection based on store state change
    } catch (err: any) {
      console.error('Guest login failed:', err);
      this.error = err.message || "Failed to start demo mode.";
    } finally {
      this.loading = false;
    }
  }

  render() {
    return html`
      <div class="login-card">
        <div class="brand">
          <span>AI</span> Budget
        </div>
        
        <h1>Welcome Back</h1>
        <p class="subtitle">Enter your credentials to access the dashboard.</p>
        
        ${this.error ? html`<div class="error-msg">${this.error}</div>` : ''}

        <form @submit=${this.handleLogin}>
          <div class="input-group">
            <label>Email Address</label>
            <input 
                type="email" 
                .value=${this.email} 
                @input=${(e: Event) => { this.email = (e.target as HTMLInputElement).value; }}
                placeholder="name@company.com"
                required
            >
            ${this.emailError ? html`<div class="error-msg">${this.emailError}</div>` : ''}
          </div>
          
          <div class="input-group">
            <label>Password</label>
            <input 
                type="password"
                .value=${this.password}
                @input=${(e: Event) => { this.password = (e.target as HTMLInputElement).value; }} 
                placeholder="••••••••"
                required
            >
            ${this.passwordError ? html`<div class="error-msg">${this.passwordError}</div>` : ''}
          </div>

          <button type="submit" class="btn btn-primary" ?disabled=${this.loading}>
            ${this.loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div class="divider">OR CONTINUE WITH</div>

        ${this.ssoEnabled ? html`
            <button class="btn btn-secondary" @click=${this.handleSSOLogin} style="margin-bottom: 0.5rem;" aria-label="Sign in with SSO">
                <span style="font-size: 1.2em; margin-right: 0.5rem;" aria-hidden="true">🔐</span>
                Sign in with ${this.ssoProviderName || 'SSO'}
            </button>
        ` : ''}

        <button class="btn btn-secondary" @click=${this.handleGuestAccess} ?disabled=${this.loading} aria-label="Try demo with guest access">
            <span aria-hidden="true">🚀</span> Try Demo (Guest Access)
        </button>
      </div>
    `;
  }
}
