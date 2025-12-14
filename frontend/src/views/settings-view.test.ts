import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { SettingsView } from './settings-view';
import { budgetStore } from '../store/budget-store';

describe('SettingsView', () => {
    let element: SettingsView;

    beforeEach(() => {
        element = new SettingsView();
        document.body.appendChild(element);
    });

    afterEach(() => {
        document.body.removeChild(element);
    });

    it('should render settings view', () => {
        const h1 = element.shadowRoot?.querySelector('h1');
        expect(h1?.textContent).toContain('Settings');
    });

    it('should render forecast horizon control', () => {
        const select = element.shadowRoot?.querySelector('select');
        expect(select).toBeTruthy();
    });

    it('should handle missing settings gracefully', async () => {
        // @ts-ignore - Simulating corrupted state
        budgetStore.getStore().setState((state) => ({
            ...state,
            settings: {
                currency: 'USD',
                // budget_threshold and forecast_horizon missing
            }
        }));

        // Force re-render
        element.requestUpdate();
        await element.updateComplete;

        const inputs = element.shadowRoot?.querySelectorAll('input');
        expect(inputs).toBeTruthy();
    });
});

