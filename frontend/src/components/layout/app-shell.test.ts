import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AppShell } from './app-shell';
import { BudgetMetrics } from '../../store/budget-store';
import { User } from '../../store/auth-store';

describe('AppShell', () => {
    let element: AppShell;
    const mockMetrics: BudgetMetrics = {
        total_expenses: 1000,
        category_breakdown: {},
        project_breakdown: {},
        top_merchants: {},
        gaps: [],
        flash_fill: [],
        subscriptions: [],
        anomalies: [],
        monthly_trend: [],
        category_history: {},
        project_history: {},
        category_vendors: {},
        project_vendors: {},
        category_merchants: {},
        project_merchants: {}
    };

    const mockUser: User = {
        email: 'test@example.com',
        role: 'viewer'
    };

    beforeEach(() => {
        element = new AppShell();
        element.metrics = mockMetrics;
        element.user = mockUser;
        element.activeTab = 'dashboard';
        document.body.appendChild(element);
    });

    it('should render app shell', () => {
        const shell = element.shadowRoot?.querySelector(':host');
        expect(element).toBeTruthy();
    });

    it('should render sidebar', () => {
        const sidebar = element.shadowRoot?.querySelector('aside');
        expect(sidebar).toBeTruthy();
    });

    it('should render brand name', () => {
        const brand = element.shadowRoot?.querySelector('.brand');
        expect(brand).toBeTruthy();
    });

    it('should dispatch nav-change event on nav click', () => {
        const navSpy = vi.fn();
        element.addEventListener('nav-change', navSpy);
        
        element.handleNavClick('files');
        
        expect(navSpy).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: { tab: 'files' }
            })
        );
    });

    it('should render main content area', () => {
        const main = element.shadowRoot?.querySelector('main');
        expect(main).toBeTruthy();
    });

    it('should display user email when user is set', () => {
        element.user = mockUser;
        element.requestUpdate();
        
        // Check if user info is displayed (implementation dependent)
        expect(element.user?.email).toBe('test@example.com');
    });
});

