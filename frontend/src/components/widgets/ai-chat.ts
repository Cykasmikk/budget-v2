import { html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { BaseComponent } from '../base-component';
import { ChatMessage } from '../../types/interfaces';
import type { BudgetMetrics } from '../../store/budget-store';
import { ChatMessageSchema, getValidationError } from '../../utils/validation';
import { sanitizeHtml } from '../../utils/sanitize';
import { logger } from '../../services/logger';

@customElement('ai-chat')
export class AIChat extends BaseComponent {
  @property({ type: Object }) metrics: BudgetMetrics | null = null;

  @state() messages: ChatMessage[] = [];
  @state() inputValue: string = '';
  @state() isLoading: boolean = false;
  @state() private inputError: string = '';

  static styles = [
    BaseComponent.styles,
    css`
      :host {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-xl);
        overflow: hidden;
      }

      .chat-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--color-border);
        background: rgba(59, 130, 246, 0.05);
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }

      .chat-header h2 {
        margin: 0;
        font-size: var(--font-size-lg);
        font-weight: 600;
        color: var(--color-text);
      }

      .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        min-height: 0;
      }

      .message {
        display: flex;
        gap: 0.75rem;
        animation: fadeIn 0.3s ease-in;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .message.user {
        flex-direction: row-reverse;
      }

      .message-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
      }

      .message.user .message-avatar {
        background: var(--color-primary);
        color: white;
      }

      .message.assistant .message-avatar {
        background: rgba(59, 130, 246, 0.2);
        color: var(--color-primary);
      }

      .message-content {
        max-width: 70%;
        padding: 0.75rem 1rem;
        border-radius: var(--radius-md);
        word-wrap: break-word;
      }

      .message.user .message-content {
        background: var(--color-primary);
        color: white;
        border-bottom-right-radius: 4px;
      }

      .message.assistant .message-content {
        background: rgba(255, 255, 255, 0.05);
        color: var(--color-text);
        border: 1px solid var(--color-border);
        border-bottom-left-radius: 4px;
      }

      .chat-input-container {
        padding: 1rem 1.5rem;
        border-top: 1px solid var(--color-border);
        background: rgba(255, 255, 255, 0.02);
      }

      .chat-input-wrapper {
        display: flex;
        gap: 0.75rem;
        align-items: flex-end;
      }

      .chat-input {
        flex: 1;
        padding: 0.75rem 1rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        color: var(--color-text);
        font-family: var(--font-family);
        font-size: var(--font-size-base);
        resize: none;
        min-height: 44px;
        max-height: 120px;
        overflow-y: auto;
      }

      .chat-input:focus {
        outline: none;
        border-color: var(--color-primary);
        background: rgba(255, 255, 255, 0.08);
      }

      .send-button {
        padding: 0.75rem 1.5rem;
        background: var(--color-primary);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        font-weight: 600;
        cursor: pointer;
        transition: all var(--transition-fast);
        flex-shrink: 0;
      }

      .send-button:hover:not(:disabled) {
        background: var(--color-primary-hover);
        transform: translateY(-1px);
      }

      .send-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .empty-state {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: var(--color-text-muted);
        text-align: center;
        padding: 2rem;
      }

      .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
      }

      .typing-indicator {
        display: flex;
        gap: 0.25rem;
        padding: 0.5rem 0;
      }

      .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--color-text-muted);
        animation: typing 1.4s infinite;
      }

      .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
      }

      .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
      }

      @keyframes typing {
        0%, 60%, 100% {
          transform: translateY(0);
          opacity: 0.5;
        }
        30% {
          transform: translateY(-10px);
          opacity: 1;
        }
      }
    `
  ];

  connectedCallback() {
    super.connectedCallback();
    // Add welcome message
    if (this.messages.length === 0) {
      this.messages = [{
        role: 'assistant',
        content: 'Hello! I\'m your AI budget assistant. I can help you analyze your spending, answer questions about your budget data, and provide insights. What would you like to know?',
        timestamp: new Date()
      }];
    }
  }

  private async sendMessage() {
    if (!this.inputValue.trim() || this.isLoading) return;

    // Validate message
    const sanitized = sanitizeHtml(this.inputValue.trim());
    const validationResult = ChatMessageSchema.safeParse(sanitized);

    if (!validationResult.success) {
      this.inputError = getValidationError(validationResult.error);
      return;
    }

    this.inputError = '';

    const userMessage: ChatMessage = {
      role: 'user',
      content: sanitized,
      timestamp: new Date()
    };

    this.messages = [...this.messages, userMessage];
    this.inputValue = '';
    this.isLoading = true;

    try {
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_history: this.messages.slice(0, -1).map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }

      const data = await response.json();
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      };

      this.messages = [...this.messages, assistantMessage];
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      logger.error('Chat error', 'ai-chat', errorObj);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      this.messages = [...this.messages, errorMessage];
    } finally {
      this.isLoading = false;
    }
  }

  private handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  private scrollToBottom() {
    const messagesContainer = this.shadowRoot?.querySelector('.chat-messages');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  updated() {
    // Scroll to bottom when new messages arrive
    this.scrollToBottom();
  }

  render() {
    return html`
      <div class="chat-header">
        <div class="message-avatar" style="background: rgba(59, 130, 246, 0.2); color: var(--color-primary);" aria-hidden="true">
          🤖
        </div>
        <h2>AI Budget Assistant</h2>
      </div>

      <div class="chat-messages" role="log" aria-live="polite" aria-label="Chat conversation">
        ${this.messages.length === 0 ? html`
          <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            <p>Start a conversation with your AI budget assistant</p>
          </div>
        ` : this.messages.map((msg) => html`
          <div class="message ${msg.role}">
            <div class="message-avatar" aria-hidden="true">
              ${msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div class="message-content">
              ${msg.content}
            </div>
          </div>
        `)}
        
        ${this.isLoading ? html`
          <div class="message assistant">
            <div class="message-avatar" aria-hidden="true">🤖</div>
            <div class="message-content" aria-live="polite" aria-label="AI is typing">
              <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
              </div>
            </div>
          </div>
        ` : ''}
      </div>

      <div class="chat-input-container">
        <div class="chat-input-wrapper">
          <textarea
            class="chat-input ${this.inputError ? 'error' : ''}"
            .value=${this.inputValue}
            @input=${(e: Event) => { this.inputValue = (e.target as HTMLTextAreaElement).value; this.inputError = ''; }}
            @keydown=${this.handleKeyDown}
            placeholder="Ask me anything about your budget..."
            rows="1"
            ?disabled=${this.isLoading}
            aria-label="Chat message input"
            aria-invalid=${this.inputError ? 'true' : 'false'}
            aria-describedby=${this.inputError ? 'chat-input-error' : undefined}
          ></textarea>
          ${this.inputError ? html`<div id="chat-input-error" class="error-message" style="color: var(--color-error); font-size: 0.8rem; margin-top: 0.25rem; padding: 0 0.5rem;">${this.inputError}</div>` : ''}
          <button
            class="send-button"
            @click=${this.sendMessage}
            ?disabled=${!this.inputValue.trim() || this.isLoading}
            aria-label="Send message"
          >
            Send
          </button>
        </div>
      </div>
    `;
  }
}

