import { describe, it, expect, beforeEach } from 'vitest';
import { AuthStore } from './auth-store';

describe('AuthStore', () => {
    let store: AuthStore;

    beforeEach(() => {
        store = new AuthStore();
    });

    it('should initialize with logged out state', () => {
        const state = store.state;
        expect(state.isAuthenticated).toBe(false);
        expect(state.user).toBeNull();
    });

    it('should set authenticated state on login', () => {
        const user = { email: 'test@example.com', role: 'admin' };
        store.loginSuccess(user);
        
        expect(store.state.isAuthenticated).toBe(true);
        expect(store.state.user).toEqual(user);
    });

    it('should clear state on logout', () => {
        store.loginSuccess({ email: 'test@example.com', role: 'admin' });
        store.logout();
        
        expect(store.state.isAuthenticated).toBe(false);
        expect(store.state.user).toBeNull();
    });

    it('should set loading state', () => {
        store.setState((state) => ({ ...state, isLoading: true }));
        expect(store.state.isLoading).toBe(true);
        
        store.setState((state) => ({ ...state, isLoading: false }));
        expect(store.state.isLoading).toBe(false);
    });
});

