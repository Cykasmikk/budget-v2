import { describe, it, expect, beforeEach } from 'vitest';
import { SimulationCard } from './simulation-card';

describe('SimulationCard', () => {
    let element: SimulationCard;

    beforeEach(() => {
        element = new SimulationCard();
        document.body.appendChild(element);
    });

    it('should render simulation card', () => {
        const card = element.shadowRoot?.querySelector('.card');
        expect(card).toBeTruthy();
    });
});

