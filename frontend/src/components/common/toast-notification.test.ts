import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ToastNotification } from './toast-notification';

describe('ToastNotification', () => {
    let element: ToastNotification;

    beforeEach(() => {
        element = new ToastNotification();
        document.body.appendChild(element);
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        if (document.body.contains(element)) {
            document.body.removeChild(element);
        }
    });

    it('should render toast notification', () => {
        const toast = element.shadowRoot?.querySelector('.toast');
        expect(toast).toBeTruthy();
    });

    it('should display message', async () => {
        element.message = 'Test message';
        element.visible = true;
        await element.updateComplete;
        
        const messageEl = element.shadowRoot?.querySelector('.message');
        expect(messageEl?.textContent).toBe('Test message');
    });

    it('should show success icon for success type', async () => {
        element.type = 'success';
        element.visible = true;
        await element.updateComplete;
        
        const toast = element.shadowRoot?.querySelector('.toast.success');
        expect(toast).toBeTruthy();
    });

    it('should show error icon for error type', async () => {
        element.type = 'error';
        element.visible = true;
        await element.updateComplete;
        
        const toast = element.shadowRoot?.querySelector('.toast.error');
        expect(toast).toBeTruthy();
    });

    it('should show warning icon for warning type', async () => {
        element.type = 'warning';
        element.visible = true;
        await element.updateComplete;
        
        const toast = element.shadowRoot?.querySelector('.toast.warning');
        expect(toast).toBeTruthy();
    });

    it('should auto-close after duration', async () => {
        const closeSpy = vi.fn();
        element.addEventListener('close', closeSpy);
        
        element.visible = true;
        element.duration = 1000;
        await element.updateComplete;
        
        vi.advanceTimersByTime(1000);
        
        expect(closeSpy).toHaveBeenCalled();
    });

    it('should not auto-close if duration is 0', async () => {
        const closeSpy = vi.fn();
        element.addEventListener('close', closeSpy);
        
        element.visible = true;
        element.duration = 0;
        await element.updateComplete;
        
        vi.advanceTimersByTime(10000);
        
        expect(closeSpy).not.toHaveBeenCalled();
    });

    it('should clear timer when visibility changes', async () => {
        element.visible = true;
        element.duration = 1000;
        await element.updateComplete;
        
        element.visible = false;
        await element.updateComplete;
        
        vi.advanceTimersByTime(1000);
        
        // Timer should be cleared, so close event shouldn't fire
        const closeSpy = vi.fn();
        element.addEventListener('close', closeSpy);
        expect(closeSpy).not.toHaveBeenCalled();
    });
});

