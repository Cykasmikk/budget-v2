import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { authStore } from '../store/auth-store';

@customElement('callback-view')
export class CallbackView extends LitElement {
    static styles = css`
        :host {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: var(--color-background, #111827);
            color: var(--color-text, white);
            font-family: 'Inter', sans-serif;
        }
        .card {
             background: var(--color-surface, #1f2937);
             padding: 2rem;
             border-radius: 12px;
             text-align: center;
             border: 1px solid var(--color-border, #374151);
        }
    `;

    @state() private message = 'Completing sign in...';
    @state() private error = '';

    async connectedCallback() {
        super.connectedCallback();

        // Parse URL params
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');

        if (!code) {
            this.error = 'No authorization code found.';
            return;
        }

        try {
            const response = await fetch('/api/v1/auth/sso/callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    callback_url: window.location.origin + window.location.pathname // Should typically be just origin + path
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'SSO Exchange Failed');
            }

            const data = await response.json();

            // Clean URL
            window.history.replaceState({}, document.title, '/');

            // Update Store (User is logged in!)
            this.message = 'Success! Redirecting...';

            // Artificial delay for UX
            setTimeout(() => {
                authStore.loginSuccess({ email: data.user, role: 'viewer' }); // Role will be refreshed from backend /auth/me anyway if we did full session check, but this gets us into dashboard
            }, 800);

        } catch (e: any) {
            this.error = e.message;
        }
    }

    render() {
        if (this.error) {
            return html`
                <div class="card">
                    <h1 style="color: #ef4444;">Sign In Failed</h1>
                    <p>${this.error}</p>
                    <button 
                        style="margin-top: 1rem; padding: 0.5rem 1rem; cursor: pointer;"
                        @click=${() => window.location.href = '/'}
                    >
                        Return to Login
                    </button>
                </div>
            `;
        }

        return html`
            <div class="card">
                <h2>🔐 Authenticating</h2>
                <p>${this.message}</p>
            </div>
        `;
    }
}
