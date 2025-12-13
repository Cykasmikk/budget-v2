import { LitElement, CSSResultGroup } from 'lit';
import { sharedStyles } from '../styles/shared';
import { logger } from '../services/logger';

/**
 * Abstract Base Class for all Enterprise Components.
 * 
 * enforces:
 * - Shared Design System styles (Buttons, Forms, Cards)
 * - Strict Typing expectations
 * - Common Lifecycle hooks (if needed in future)
 */
export abstract class BaseComponent extends LitElement {

    /**
     * Combine local component styles with the global shared system.
     * Components implementing `styles` should use `super.styles` if they want to extend,
     * but usually Lit merges array styles automatically if we return an array here.
     */
    static styles: CSSResultGroup = [
        ...sharedStyles
    ];

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        return super.createRenderRoot();
    }

    protected handleError(error: unknown) {
        const errorObj = error instanceof Error ? error : new Error(String(error));
        logger.error(`Component error`, this.tagName, errorObj);
        // Could dispatch a toast event here
        this.dispatchEvent(new CustomEvent('toast-message', {
            bubbles: true,
            composed: true,
            detail: {
                message: errorObj.message,
                type: 'error'
            }
        }));
    }
}
