import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

@customElement('toast-notification')
export class ToastNotification extends LitElement {
    @property({ type: String }) message = '';
    @property({ type: String }) type: ToastType = 'info';
    @property({ type: Boolean }) visible = false;
    @property({ type: Number }) duration = 3000;

    private _timer: number | undefined;

    static styles = css`
    :host {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 10000;
      pointer-events: none;
    }

    .toast {
      background: var(--color-background-card);
      color: var(--color-text);
      padding: 1rem 1.5rem;
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
      border-left: 4px solid var(--color-primary);
      display: flex;
      align-items: center;
      gap: 0.75rem;
      min-width: 300px;
      max-width: 450px;
      
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.3s ease, transform 0.3s ease;
      pointer-events: auto;
    }

    .toast.visible {
      opacity: 1;
      transform: translateY(0);
    }

    .toast.success { border-left-color: var(--color-success); }
    .toast.error { border-left-color: var(--color-error); }
    .toast.warning { border-left-color: var(--color-warning); }
    
    .icon {
      font-size: 1.25rem;
    }
  `;

    updated(changedProperties: Map<string, any>) {
        if (changedProperties.has('visible') && this.visible) {
            this.startTimer();
        }
    }

    private startTimer() {
        this.clearTimer();
        if (this.duration > 0) {
            this._timer = window.setTimeout(() => {
                this.dispatchEvent(new CustomEvent('close'));
            }, this.duration);
        }
    }

    private clearTimer() {
        if (this._timer) {
            clearTimeout(this._timer);
            this._timer = undefined;
        }
    }

    private getIcon() {
        switch (this.type) {
            case 'success': return '✓';
            case 'error': return '✕';
            case 'warning': return '⚠';
            default: return 'ℹ';
        }
    }

    render() {
        return html`
      <div class="toast ${this.type} ${this.visible ? 'visible' : ''}">
        <div class="icon">${this.getIcon()}</div>
        <div class="message">${this.message}</div>
      </div>
    `;
    }
}
