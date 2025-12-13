import { describe, it, expect, beforeEach } from 'vitest';
import { AnalysisControls } from './analysis-controls';

describe('AnalysisControls', () => {
    let element: AnalysisControls;

    beforeEach(() => {
        element = new AnalysisControls();
        element.viewMode = 'category';
        document.body.appendChild(element);
    });

    it('should render analysis controls', () => {
        const buttons = element.shadowRoot?.querySelectorAll('.toggle-btn');
        expect(buttons?.length).toBeGreaterThan(0);
    });

    it('should highlight active view mode', () => {
        element.viewMode = 'category';
        element.requestUpdate();
        
        const activeButton = element.shadowRoot?.querySelector('.toggle-btn.active');
        expect(activeButton).toBeTruthy();
    });
});

