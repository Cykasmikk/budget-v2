import { describe, it, expect, beforeEach } from 'vitest';
import { SimulationCard } from './simulation-card';

describe('SimulationCard', () => {
    let element: SimulationCard;

    beforeEach(() => {
        element = new SimulationCard();
        document.body.appendChild(element);
    });

    it('should render simulation card', async () => {
        await element.updateComplete;
        const title = element.shadowRoot?.querySelector('h2');
        expect(title?.textContent).toContain('Sandbox Simulator');
    });
});

