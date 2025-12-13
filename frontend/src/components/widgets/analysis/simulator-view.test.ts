import { describe, it, expect, beforeEach } from 'vitest';
import { SimulatorView } from './simulator-view';

describe('SimulatorView', () => {
    let element: SimulatorView;

    beforeEach(() => {
        element = new SimulatorView();
        document.body.appendChild(element);
    });

    it('should render simulator view', () => {
        const form = element.shadowRoot?.querySelector('.form-group');
        expect(form).toBeTruthy();
    });
});

