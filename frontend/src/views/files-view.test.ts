import { describe, it, expect, beforeEach } from 'vitest';
import { FilesView } from './files-view';

describe('FilesView', () => {
    let element: FilesView;

    beforeEach(() => {
        element = new FilesView();
        document.body.appendChild(element);
    });

    it('should render files view', () => {
        const h1 = element.shadowRoot?.querySelector('h1');
        expect(h1?.textContent).toContain('Files');
    });

    it('should render merge strategy options', () => {
        const strategies = element.shadowRoot?.querySelectorAll('.strategy-option');
        expect(strategies?.length).toBe(3);
    });

    it('should display empty state when no files', () => {
        const emptyState = element.shadowRoot?.querySelector('.empty-state');
        expect(emptyState).toBeTruthy();
    });
});

