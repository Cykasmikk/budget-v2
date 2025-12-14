import { describe, it, expect, beforeEach } from 'vitest';
import { UIStore } from './ui-store';

describe('UIStore', () => {
    let store: UIStore;

    beforeEach(() => {
        store = new UIStore();
    });

    it('should initialize with default dashboard tab', () => {
        expect(store.state.activeTab).toBe('dashboard');
    });

    it('should update active tab', () => {
        store.setActiveTab('settings');
        expect(store.state.activeTab).toBe('settings');
    });

    it('should reset to default state', () => {
        store.setActiveTab('files');
        store.reset();
        expect(store.state.activeTab).toBe('dashboard');
    });
});
