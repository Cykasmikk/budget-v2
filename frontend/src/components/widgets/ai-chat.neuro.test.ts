import { describe, it, expect, beforeEach } from 'vitest';
import { AIChat } from './ai-chat';
import { ChatMessage } from '../../types/interfaces';

describe('AIChat Neuro-Symbolic Features', () => {
    let element: AIChat;

    beforeEach(() => {
        element = new AIChat();
        document.body.appendChild(element);
    });

    it('should render explanation panel when message has explanation', async () => {
        // Manually push a message with an explanation
        const msg: ChatMessage = {
            role: 'assistant',
            content: 'The total is $500.',
            explanation: 'SELECT SUM(amount) FROM transactions',
            timestamp: new Date()
        };

        // We need to bypass the private property or just set it if we can access the state
        // Since messages is @state(), we can set it via property access if public, or use a method
        // But AIChat initializes messages in connectedCallback. 
        // We can force update.

        // accessing private state for test
        (element as any).messages = [msg];
        await element.updateComplete;

        const explanation = element.shadowRoot?.querySelector('.explanation-panel');
        expect(explanation).toBeTruthy();
        expect(explanation?.textContent).toContain('SELECT SUM(amount)');
    });

    it('should NOT render explanation panel when message has no explanation', async () => {
        const msg: ChatMessage = {
            role: 'assistant',
            content: 'Just text.',
            timestamp: new Date()
        };
        (element as any).messages = [msg];
        await element.updateComplete;

        const explanation = element.shadowRoot?.querySelector('.explanation-panel');
        expect(explanation).toBeFalsy();
    });
});
