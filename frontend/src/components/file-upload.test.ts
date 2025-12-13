import { describe, it, expect, beforeEach } from 'vitest';
import { FileUpload } from './file-upload';

describe('FileUpload', () => {
    let element: FileUpload;

    beforeEach(() => {
        element = new FileUpload();
        document.body.appendChild(element);
    });

    it('should render upload button', () => {
        const button = element.shadowRoot?.querySelector('.upload-zone button');
        expect(button).toBeTruthy();
        expect(button?.textContent).toContain('Select File');
    });
});
