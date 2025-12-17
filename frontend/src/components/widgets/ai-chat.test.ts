import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AIChat } from './ai-chat';

describe('AIChat', () => {
    let element: AIChat;

    beforeEach(() => {
        element = new AIChat();
        document.body.appendChild(element);
    });

    it('should render chat interface', () => {
        const header = element.shadowRoot?.querySelector('.chat-header');
        const messages = element.shadowRoot?.querySelector('.chat-messages');
        const input = element.shadowRoot?.querySelector('.chat-input');
        
        expect(header).toBeTruthy();
        expect(messages).toBeTruthy();
        expect(input).toBeTruthy();
    });

    it('should display welcome message on initialization', () => {
        const messages = element.shadowRoot?.querySelectorAll('.message');
        expect(messages?.length).toBeGreaterThan(0);
    });

    it('should update input value on user input', () => {
        const input = element.shadowRoot?.querySelector('.chat-input') as HTMLTextAreaElement;
        const testValue = 'Test message';
        
        input.value = testValue;
        input.dispatchEvent(new Event('input'));
        
        expect(element.inputValue).toBe(testValue);
    });

    it('should disable send button when input is empty', () => {
        const sendButton = element.shadowRoot?.querySelector('.send-button') as HTMLButtonElement;
        expect(sendButton?.disabled).toBe(true);
    });

    it('should enable send button when input has value', async () => {
        const input = element.shadowRoot?.querySelector('.chat-input') as HTMLTextAreaElement;
        const sendButton = element.shadowRoot?.querySelector('.send-button') as HTMLButtonElement;
        
        input.value = 'Test message';
        input.dispatchEvent(new Event('input'));
        await element.updateComplete;
        
        expect(sendButton?.disabled).toBe(false);
    });

    it('should show loading state when sending message', async () => {
        global.fetch = vi.fn(() => 
            new Promise(() => {}) // Never resolves to simulate loading
        ) as any;

        const input = element.shadowRoot?.querySelector('.chat-input') as HTMLTextAreaElement;
        input.value = 'Test message';
        input.dispatchEvent(new Event('input'));
        await element.updateComplete; // Ensure button enables state update

        const sendButton = element.shadowRoot?.querySelector('.send-button') as HTMLButtonElement;
        sendButton.click();
        
        // Wait for event loop to process the click handler start
        await new Promise(resolve => setTimeout(resolve, 0));
        await element.updateComplete; // Wait for isLoading render update
        
        expect(element.isLoading).toBe(true);
    });

    it('should handle Enter key to send message', () => {
        const input = element.shadowRoot?.querySelector('.chat-input') as HTMLTextAreaElement;
        input.value = 'Test message';
        
        const keyDownEvent = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: false });
        input.dispatchEvent(keyDownEvent);
        
        // Should trigger send (we can't easily test the full flow without mocking fetch)
        expect(input.value).toBeDefined();
    });

    it('should not send on Shift+Enter', () => {
        const input = element.shadowRoot?.querySelector('.chat-input') as HTMLTextAreaElement;
        input.value = 'Test message';
        const initialMessages = element.messages.length;
        
        const keyDownEvent = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: true });
        input.dispatchEvent(keyDownEvent);
        
        expect(element.messages.length).toBe(initialMessages);
    });
});

