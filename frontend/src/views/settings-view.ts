import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { StoreController } from '../store/controller';
import { budgetStore } from '../store/budget-store';
import { authStore } from '../store/auth-store';
import { IssuerUrlSchema, ClientIdSchema, ClientSecretSchema, getValidationError } from '../utils/validation';
import { logger } from '../services/logger';

@customElement('settings-view')
export class SettingsView extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100%;
            padding: 2rem;
            color: var(--color-text);
            overflow-y: auto;
        }

        .settings-container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05); /* Glass card */
            border: 1px solid var(--color-border);
            border-radius: 12px;
            padding: 2rem;
        }

        h1 {
            font-size: 2rem;
            font-weight: 300;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--color-border);
            padding-bottom: 1rem;
        }

        section {
            margin-bottom: 3rem;
        }

        h2 {
            font-size: 1.2rem;
            color: var(--color-primary);
            margin-bottom: 1rem;
            font-weight: 500;
        }

        .control-group {
            display: grid;
            grid-template-columns: 1fr 200px;
            gap: 1rem;
            align-items: center;
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .control-group:last-child {
            border-bottom: none;
        }

        label {
            font-size: 1rem;
        }

        .description {
            font-size: 0.85rem;
            color: var(--color-text-secondary);
            margin-top: 0.25rem;
        }

        select, input[type="number"] {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--color-border);
            color: var(--color-text);
            padding: 0.5rem;
            border-radius: 6px;
            width: 100%;
            font-family: inherit;
        }

        button {
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }

        button.primary {
            background: var(--color-primary);
            color: white;
        }

        button.danger {
            background: rgba(255, 50, 50, 0.1);
            color: #ff6b6b;
            border: 1px solid #ff6b6b;
        }

        button.danger:hover {
            background: #ff6b6b;
            color: white;
        }
    `;

    // @ts-ignore
    private controller = new StoreController(this, budgetStore.getStore());

    @state()
    private authConfig = {
        enabled: false,
        provider_name: '',
        issuer_url: '',
        client_id: '',
        client_secret: ''
    };
    @state()
    private authErrors = {
        issuer_url: '',
        client_id: '',
        client_secret: ''
    };

    // Helper for role check (authStore is imported globally, but ideally we'd subscribe or pass prop)
    // Since this is a view inside AppRoot which subscribes, we can check store directly or use a controller.
    // We already have StoreController for budgetStore, let's just check the global store state for simplicity 
    // or add a subscription to authStore if needed for reactivity.
    // For now, assuming auth state is stable during settings view mount.

    @state() private currentUserRole = '';

    get isAdmin() {
        return this.currentUserRole === 'admin';
    }

    async connectedCallback() {
        super.connectedCallback();

        // Subscribe to user role to reactively hide/show sections
        this.currentUserRole = authStore.state.user?.role || '';

        // Ensure we have latest settings from backend
        // ... (rest of existing code)
        await budgetStore.fetchSettings();
        // We need to fetch auth config separately or extend fetchSettings?
        // For now detailed auth config is likely not in global public state, we fetch it here
        try {
            const response = await fetch('/api/v1/settings', { headers: { 'Content-Type': 'application/json' } });
            if (response.ok) {
                const data = await response.json();
                // Backend now returns {settings: {}, auth_config: {}} or just settings?
                // We updated backend to return both.
                if (data.auth_config) {
                    this.authConfig = {
                        enabled: data.auth_config.enabled || false,
                        provider_name: data.auth_config.provider_name || '',
                        issuer_url: data.auth_config.issuer || '',
                        client_id: data.auth_config.client_id || '',
                        client_secret: data.auth_config.client_secret || ''
                    };
                }
            }
        } catch (e) {
            const error = e instanceof Error ? e : new Error(String(e));
            logger.error("Failed to load auth config", 'SettingsView', error);
        }
    }

    private handleUpdate(key: string, value: any) {
        budgetStore.updateSettings({ [key]: value });
    }

    private updateAuthField(key: string, value: any) {
        this.authConfig = { ...this.authConfig, [key]: value };
    }

    private async saveAuthConfig() {
    // Validate all fields before saving
    const issuerResult = IssuerUrlSchema.safeParse(this.authConfig.issuer_url);
    const clientIdResult = ClientIdSchema.safeParse(this.authConfig.client_id);
    const clientSecretResult = ClientSecretSchema.safeParse(this.authConfig.client_secret);

    this.authErrors.issuer_url = issuerResult.success ? '' : getValidationError(issuerResult.error);
    this.authErrors.client_id = clientIdResult.success ? '' : getValidationError(clientIdResult.error);
    this.authErrors.client_secret = clientSecretResult.success ? '' : getValidationError(clientSecretResult.error);

    if (!issuerResult.success || !clientIdResult.success || !clientSecretResult.success) {
      return; // Don't save if validation fails
    }
        try {
            const response = await fetch('/api/v1/settings/auth', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.authConfig)
            });

            if (!response.ok) {
                const err = await response.json();
                alert('Error saving SSO config: ' + err.detail);
                return;
            }

            alert('SSO Configuration Saved Successfully');
        } catch (e) {
            alert('Failed to save configuration');
        }
    }

    private async handleReset() {
        if (confirm('Are you sure you want to delete all uploaded data? This action cannot be undone.')) {
            await budgetStore.resetData();
            alert('Application data has been reset.');
        }
    }

    render() {
        const { settings } = budgetStore.state;

        return html`
            <div class="settings-container">
                <h1>Settings</h1>

                <section>
                    <h2>Analysis Configuration</h2>
                    
                    <div class="control-group">
                        <div>
                            <label for="forecast-horizon">Forecast Horizon</label>
                            <div class="description" id="forecast-horizon-desc">Number of future months to project expenses.</div>
                        </div>
                        <select 
                            id="forecast-horizon"
                            aria-describedby="forecast-horizon-desc"
                            @change=${(e: any) => this.handleUpdate('forecast_horizon', parseInt(e.target.value))}
                            .value=${(settings.forecast_horizon ?? 6).toString()}
                        >
                            <option value="3">3 Months</option>
                            <option value="6">6 Months</option>
                            <option value="12">12 Months</option>
                            <option value="24">24 Months</option>
                            <option value="36">36 Months</option>
                            <option value="60">60 Months</option>
                        </select>
                    </div>

                    <div class="control-group">
                        <div>
                            <label>Currency Symbol</label>
                            <div class="description">Display currency for all financial values.</div>
                        </div>
                        <select 
                            @change=${(e: any) => this.handleUpdate('currency', e.target.value)}
                            .value=${settings.currency}
                        >
                            <option value="USD">USD ($)</option>
                            <option value="EUR">EUR (€)</option>
                            <option value="GBP">GBP (£)</option>
                            <option value="JPY">JPY (¥)</option>
                        </select>
                    </div>
                </section>

                <section>
                    <h2>Alerts & Thresholds</h2>
                    <div class="control-group">
                        <div>
                            <label>Budget Limit</label>
                            <div class="description">Global monthly spending limit triggering warnings.</div>
                        </div>
                        <input 
                                                        type="number"
                                                        .value=${(settings.budget_threshold ?? 0).toString()}
                                                        @change=${(e: any) => this.handleUpdate('budget_threshold', parseFloat(e.target.value))}                        />
                    </div>
                </section>

                ${this.isAdmin ? html`
                <section>
                    <h2>Authentication (SSO)</h2>
                    <div class="control-group">
                        <div>
                            <label>Enable SSO</label>
                            <div class="description">Allow users to sign in with OIDC Provider.</div>
                        </div>
                        <input 
                            type="checkbox" 
                            style="width: 20px; height: 20px;"
                            .checked=${this.authConfig.enabled}
                            @change=${(e: any) => this.updateAuthField('enabled', e.target.checked)}
                        />
                    </div>

                    <div class="control-group">
                         <div>
                            <label>Provider Name</label>
                            <div class="description">Display name on login button (e.g. "Google Workspace")</div>
                        </div>
                        <input type="text" 
                            .value=${this.authConfig.provider_name}
                            @change=${(e: any) => this.updateAuthField('provider_name', e.target.value)}
                        />
                    </div>

                    <div class="control-group">
                        <div>
                            <label>Issuer URL</label>
                            <div class="description">OIDC Issuer (e.g. https://accounts.google.com)</div>
                        </div>
                        <input type="text" 
                             placeholder="https://..."
                            .value=${this.authConfig.issuer_url}
                            @change=${(e: any) => this.updateAuthField('issuer_url', e.target.value)}
                        />
                    </div>

                    <div class="control-group">
                        <div>
                            <label>Client ID</label>
                        </div>
                        <input type="text" 
                            .value=${this.authConfig.client_id}
                            @change=${(e: any) => this.updateAuthField('client_id', e.target.value)}
                        />
                    </div>

                    <div class="control-group">
                        <div>
                            <label>Client Secret</label>
                        </div>
                         <input type="password" 
                            .value=${this.authConfig.client_secret}
                            @change=${(e: any) => this.updateAuthField('client_secret', e.target.value)}
                        />
                    </div>

                    <div style="text-align: right; margin-top: 1rem;">
                        <button class="primary" @click=${this.saveAuthConfig}>
                            Save SSO Configuration
                        </button>
                    </div>
                </section>
                ` : ''}

                <section>
                    <h2>Data Management</h2>
                    <div class="control-group">
                        <div>
                            <label>Factory Reset</label>
                            <div class="description">Clear all uploaded files and reset simulation data.</div>
                        </div>
                        <button class="danger" @click=${this.handleReset}>
                            Reset All Data
                        </button>
                    </div>
                </section>

                <section>
                    <h2>Application Info</h2>
                    <div class="control-group">
                        <div>
                            <label>Version</label>
                        </div>
                        <div style="text-align: right; opacity: 0.7;">v1.2.0 (Enterprise)</div>
                    </div>
                </section>
            </div>
        `;
    }
}
