import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { BudgetUpload } from './budget-upload';
import { actions } from '../store/budget-store';

// Mock the actions
vi.mock('../store/budget-store', () => ({
    actions: {
        uploadFile: vi.fn()
    }
}));

describe('BudgetUpload', () => {
    let element: BudgetUpload;

    beforeEach(() => {
        element = new BudgetUpload();
        document.body.appendChild(element);
    });

    afterEach(() => {
        if (document.body.contains(element)) {
            document.body.removeChild(element);
        }
        vi.clearAllMocks();
    });

    it('should render budget upload component', () => {
        const uploadZone = element.shadowRoot?.querySelector('.upload-zone');
        expect(uploadZone).toBeTruthy();
    });

    it('should render file input', () => {
        const fileInput = element.shadowRoot?.querySelector('input[type="file"]');
        expect(fileInput).toBeTruthy();
        expect(fileInput?.getAttribute('accept')).toBe('.xlsx, .xls');
    });

    it('should display upload zone', () => {
        const uploadZone = element.shadowRoot?.querySelector('.upload-zone');
        expect(uploadZone?.textContent).toContain('Upload Budget Excel');
    });

    it('should handle file upload', async () => {
        const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const fileInput = element.shadowRoot?.querySelector('input[type="file"]') as HTMLInputElement;
        
        const mockFileList = {
            0: mockFile,
            length: 1,
            item: (index: number) => mockFile,
            [Symbol.iterator]: function* () { yield mockFile; }
        };

        Object.defineProperty(fileInput, 'files', {
            value: mockFileList,
            writable: false
        });

        const changeEvent = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(changeEvent);

        await element.updateComplete;

        expect(actions.uploadFile).toHaveBeenCalledWith(mockFile);
    });

    it('should show uploading state', async () => {
        const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const fileInput = element.shadowRoot?.querySelector('input[type="file"]') as HTMLInputElement;
        
        (actions.uploadFile as any).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

        Object.defineProperty(fileInput, 'files', {
            value: {
                0: mockFile,
                length: 1,
                item: (index: number) => mockFile,
                [Symbol.iterator]: function* () { yield mockFile; }
            },
            writable: false
        });

        const changeEvent = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(changeEvent);

        await element.updateComplete;

        expect(element.isUploading).toBe(true);
        const uploadingText = element.shadowRoot?.querySelector('p');
        expect(uploadingText?.textContent).toContain('Uploading');
    });

    it('should display success message on successful upload', async () => {
        const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const fileInput = element.shadowRoot?.querySelector('input[type="file"]') as HTMLInputElement;
        
        (actions.uploadFile as any).mockResolvedValueOnce(undefined);

        Object.defineProperty(fileInput, 'files', {
            value: {
                0: mockFile,
                length: 1,
                item: (index: number) => mockFile,
                [Symbol.iterator]: function* () { yield mockFile; }
            },
            writable: false
        });

        const changeEvent = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(changeEvent);

        await element.updateComplete;
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(element.message).toBe('Upload successful!');
    });

    it('should display error message on failed upload', async () => {
        const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const fileInput = element.shadowRoot?.querySelector('input[type="file"]') as HTMLInputElement;
        
        const error = new Error('Upload failed');
        (actions.uploadFile as any).mockRejectedValueOnce(error);

        Object.defineProperty(fileInput, 'files', {
            value: {
                0: mockFile,
                length: 1,
                item: (index: number) => mockFile,
                [Symbol.iterator]: function* () { yield mockFile; }
            },
            writable: false
        });

        const changeEvent = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(changeEvent);

        await element.updateComplete;
        await new Promise(resolve => setTimeout(resolve, 10));

        expect(element.message).toBe('Upload failed');
    });

    it('should not process if no file selected', async () => {
        const fileInput = element.shadowRoot?.querySelector('input[type="file"]') as HTMLInputElement;
        
        Object.defineProperty(fileInput, 'files', {
            value: null,
            writable: false
        });

        const changeEvent = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(changeEvent);

        await element.updateComplete;

        expect(actions.uploadFile).not.toHaveBeenCalled();
    });
});

