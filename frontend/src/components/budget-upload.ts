import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { actions } from '../store/budget.store';

@customElement('budget-upload')
export class BudgetUpload extends LitElement {
    @state() private isUploading = false;
    @state() private message = '';

    static styles = css`
    :host {
      display: block;
      margin-bottom: 2rem;
    }
    .upload-zone {
      border: 2px dashed var(--border-color);
      border-radius: var(--border-radius);
      padding: 2rem;
      text-align: center;
      background: var(--color-surface);
      transition: border-color 0.2s;
    }
    .upload-zone:hover {
      border-color: var(--color-accent);
    }
    input[type="file"] {
      display: none;
    }
    label {
      cursor: pointer;
      color: var(--color-accent);
      font-weight: bold;
    }
    .message {
      margin-top: 1rem;
      font-size: 0.9rem;
    }
    .error { color: var(--color-danger); }
    .success { color: var(--color-success); }
  `;

    private async handleFile(e: Event) {
        const input = e.target as HTMLInputElement;
        console.log('BudgetUpload: handleFile called', { input, files: input.files, length: input.files?.length });
        if (!input.files?.length) {
            console.log('BudgetUpload: No files found');
            return;
        }

        this.isUploading = true;
        this.message = '';

        try {
            await actions.uploadFile(input.files[0]);
            this.message = 'Upload successful!';
            input.value = ''; // Reset
        } catch (err: any) {
            this.message = err.message;
        } finally {
            this.isUploading = false;
        }
    }

    render() {
        return html`
      <div class="upload-zone">
        <h3>Upload Budget Excel</h3>
        <p>Drag & drop or <label for="file-upload">browse</label></p>
        <input id="file-upload" type="file" accept=".xlsx, .xls" @change=${this.handleFile} />
        ${this.isUploading ? html`<p>Uploading...</p>` : ''}
        ${this.message ? html`<p class="message ${this.message.includes('success') ? 'success' : 'error'}">${this.message}</p>` : ''}
      </div>
    `;
    }
}
