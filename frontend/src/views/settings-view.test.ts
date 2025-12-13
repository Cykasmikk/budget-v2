import { describe, it, expect, beforeEach } from 'vitest';
import { SettingsView } from './settings-view';

describe('SettingsView', () => {
    let element: SettingsView;

    beforeEach(() => {
        element = new SettingsView();
        document.body.appendChild(element);
    });

    it('should render settings view', () => {
        const h1 = element.shadowRoot?.querySelector('h1');
        expect(h1?.textContent).toContain('Settings');
    });

    it('should render forecast horizon control', () => {
        const select = element.shadowRoot?.querySelector('select');
        expect(select).toBeTruthy();
    });
});

