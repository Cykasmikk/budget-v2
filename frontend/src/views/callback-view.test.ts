import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { CallbackView } from './callback-view';
import { authStore } from '../store/auth-store';

describe('CallbackView', () => {
    let element: CallbackView;

    beforeEach(() => {
        element = new CallbackView();
        document.body.appendChild(element);
        global.fetch = vi.fn();
    });

    afterEach(() => {
        if (document.body.contains(element)) {
            document.body.removeChild(element);
        }
        vi.restoreAllMocks();
    });

    it('should render callback view', () => {
        const container = element.shadowRoot?.querySelector('.card');
        expect(container).toBeTruthy();
    });

    it('should display loading message initially', () => {
        const message = element.shadowRoot?.querySelector('p');
        expect(message?.textContent).toContain('Completing sign in');
    });

    it('should handle SSO callback with code', async () => {
        const mockResponse = {
            ok: true,
            json: () => Promise.resolve({ user: 'test@example.com', role: 'viewer' })
        };
        
        (global.fetch as any).mockResolvedValueOnce(mockResponse);
        
        // Simulate URL with code parameter
        Object.defineProperty(window, 'location', {
            value: {
                search: '?code=test-code',
                origin: 'http://localhost',
                pathname: '/callback'
            },
            writable: true
        });

        await element.connectedCallback();
        await element.updateComplete;

        expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/sso/callback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: 'test-code',
                callback_url: 'http://localhost/callback'
            })
        });
    });

    it('should display error when no code is present', async () => {
        Object.defineProperty(window, 'location', {
            value: { search: '' },
            writable: true
        });

        await element.connectedCallback();
        await element.updateComplete;

        expect(element.error).toBe('No authorization code found.');
    });

    it('should display error message on failed callback', async () => {
        const mockResponse = {
            ok: false,
            json: () => Promise.resolve({ detail: 'SSO Exchange Failed' })
        };
        
        (global.fetch as any).mockResolvedValueOnce(mockResponse);
        
        Object.defineProperty(window, 'location', {
            value: { search: '?code=test-code', origin: 'http://localhost', pathname: '/callback' },
            writable: true
        });

        await element.connectedCallback();
        await element.updateComplete;

        expect(element.error).toBe('SSO Exchange Failed');
    });
});

