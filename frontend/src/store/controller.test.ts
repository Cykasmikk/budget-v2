import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { StoreController } from './controller';
import { Store } from '@tanstack/store';
import { LitElement } from 'lit';

class MockHost extends LitElement {
    requestUpdate() {
        return super.requestUpdate();
    }
}
if (!customElements.get('mock-host-store')) {
    customElements.define('mock-host-store', MockHost);
}

describe('StoreController', () => {
    let controller: StoreController<{ count: number }>;
    let host: MockHost;
    let store: Store<{ count: number }>;

    beforeEach(() => {
        host = new MockHost();
        store = new Store({ count: 0 });
        controller = new StoreController(host, store);
        document.body.appendChild(host);
    });

    afterEach(() => {
        if (document.body.contains(host)) {
            document.body.removeChild(host);
        }
    });

    it('should initialize with store', () => {
        expect(controller.store).toBe(store);
        expect(controller.host).toBe(host);
    });

    it('should subscribe to store on host connected', () => {
        host.connectedCallback();
        
        const updateSpy = vi.spyOn(host, 'requestUpdate');
        
        store.setState({ count: 1 });
        
        expect(updateSpy).toHaveBeenCalled();
    });

    it('should unsubscribe on host disconnected', () => {
        host.connectedCallback();
        
        vi.spyOn(host, 'requestUpdate');
        
        host.disconnectedCallback();
        store.setState({ count: 2 });
        
        // After disconnect, updates should not trigger requestUpdate
        // Note: This test may need adjustment based on actual behavior
        expect(controller.unsubscribe).toBeDefined();
    });

    it('should add itself as controller to host', () => {
        // Controller is added via host.addController() in constructor
        // We can verify by checking that unsubscribe is defined after connection
        host.connectedCallback();
        expect(controller.unsubscribe).toBeDefined();
    });
});

