import { describe, it, expect, beforeEach, vi } from 'vitest';
import { LoginView } from './login-view';

describe('LoginView', () => {
    let element: LoginView;

    beforeEach(() => {
        element = new LoginView();
        document.body.appendChild(element);
    });

    it('should render login form', () => {
        const form = element.shadowRoot?.querySelector('form');
        expect(form).toBeTruthy();
    });

    it('should render email input', () => {
        const emailInput = element.shadowRoot?.querySelector('input[type="email"]');
        expect(emailInput).toBeTruthy();
    });

    it('should render password input', () => {
        const passwordInput = element.shadowRoot?.querySelector('input[type="password"]');
        expect(passwordInput).toBeTruthy();
    });

    it('should render sign in button', () => {
        const button = element.shadowRoot?.querySelector('button[type="submit"]');
        expect(button).toBeTruthy();
        expect(button?.textContent).toContain('Sign In');
    });

    it('should update email on input', () => {
        const emailInput = element.shadowRoot?.querySelector('input[type="email"]') as HTMLInputElement;
        emailInput.value = 'test@example.com';
        emailInput.dispatchEvent(new Event('input'));
        
        expect(element.email).toBe('test@example.com');
    });

    it('should update password on input', () => {
        const passwordInput = element.shadowRoot?.querySelector('input[type="password"]') as HTMLInputElement;
        passwordInput.value = 'password123';
        passwordInput.dispatchEvent(new Event('input'));
        
        expect(element.password).toBe('password123');
    });

    it('should show loading state during login', async () => {
        global.fetch = vi.fn(() => 
            new Promise(() => {}) // Never resolves
        ) as any;

        element.email = 'test@example.com';
        element.password = 'password123';
        
        const form = element.shadowRoot?.querySelector('form') as HTMLFormElement;
        form.dispatchEvent(new Event('submit'));
        
        await element.updateComplete;
        expect(element.loading).toBe(true);
    });

    it('should display error message on login failure', async () => {
        global.fetch = vi.fn(() => 
            Promise.resolve({
                ok: false,
                json: () => Promise.resolve({ detail: 'Invalid credentials' })
            } as Response)
        );

        element.email = 'test@example.com';
        element.password = 'password123';
        
        const form = element.shadowRoot?.querySelector('form') as HTMLFormElement;
        form.dispatchEvent(new Event('submit'));
        
        await new Promise(resolve => setTimeout(resolve, 0));
        await element.updateComplete;
        
        expect(element.error).toBeTruthy();
    });

    it('should render guest access button', () => {
        const guestButton = element.shadowRoot?.querySelector('.btn-secondary');
        expect(guestButton).toBeTruthy();
    });
});

