import { html, css } from 'lit';
import { customElement, state, property } from 'lit/decorators.js';
import { BaseComponent } from './base-component';
import { budgetStore } from '../store/budget-store';
import '../components/common/toast-notification';
import { ToastType } from '../components/common/toast-notification';
import { FileUploadSchema } from '../utils/validation';
import { logger } from '../services/logger';

@customElement('file-upload')
export class FileUpload extends BaseComponent {
  @property({ type: Boolean, reflect: true }) compact = false;

  @state() private isUploading = false;
  @state() private pendingConflict: { file: File, analysisData: any, size: string } | null = null;
  @state() private uploadResult: { count: number, warnings: string[], skipped: number } | null = null;
  @state() private isDragging = false;
  @state() private activeTab: 'local' | 'onedrive' | 'sharepoint' = 'local';
  @state() private toastState: { message: string, type: ToastType, visible: boolean } = {
    message: '', type: 'info', visible: false
  };

  static styles = [
    BaseComponent.styles,
    css`
      :host { display: block; }
      
      .upload-zone {
        border: 2px dashed var(--color-border);
        border-radius: var(--radius-lg);
        padding: 3rem 2rem;
        text-align: center;
        transition: all var(--transition-normal);
        background: rgba(255, 255, 255, 0.02);
        cursor: pointer;
        position: relative;
      }
      
      :host([compact]) .upload-zone {
        padding: 1.5rem 1rem;
        border-radius: var(--radius-md);
        border-width: 1px;
      }

      .upload-zone:hover, .upload-zone.drag-active {
        border-color: var(--color-primary);
        background: rgba(59, 130, 246, 0.05);
        transform: scale(1.01);
      }
      
      :host([compact]) .upload-zone:hover { transform: none; }

      .icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        color: var(--color-text-muted);
        transition: color var(--transition-normal);
      }
      
      :host([compact]) .icon { font-size: 1.5rem; margin-bottom: 0.5rem; }

      .upload-zone:hover .icon { color: var(--color-primary); }
      
      .text {
        color: var(--color-text);
        font-weight: 500;
        margin-bottom: 0.5rem;
      }
      
      :host([compact]) .text { font-size: 0.9rem; margin-bottom: 0.25rem; }

      .subtext {
        color: var(--color-text-muted);
        font-size: var(--font-size-sm);
      }
      
      :host([compact]) .subtext { display: none; }

      /* Tab Styles */
      .tabs {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        justify-content: center;
      }
      
      :host([compact]) .tabs { gap: 0.5rem; margin-bottom: 1rem; }

      .tab {
        padding: 0.5rem 1rem;
        background: transparent;
        border: 1px solid var(--color-border);
        color: var(--color-text-muted);
        border-radius: var(--radius-md);
        cursor: pointer;
        transition: all var(--transition-fast);
      }
      
      .tab.active {
        background: var(--color-primary);
        color: white;
        border-color: var(--color-primary);
      }
      
      .tab:hover:not(.active) {
        border-color: var(--color-text);
        color: var(--color-text);
      }

      /* Modal Overlay specialized for Upload */
      .modal-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex; justify-content: center; align-items: center;
        z-index: 1000;
      }
      
      .modal {
        background: var(--color-surface);
        padding: 2rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        text-align: center;
        max-width: 400px;
        width: 90%;
        color: var(--color-text);
        border: 1px solid var(--color-border);
      }
    `
  ];

  /* Logic Methods (Drastically simplified where possible or just moved) */
  private async processFiles(files: FileList) {
    // ... logic same as before, preserving functionality
    if (!files.length) return;
    this.isUploading = true;
    budgetStore.setLoading(true);

    const formatSize = (bytes: number) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Validate file
      const validationResult = FileUploadSchema.safeParse({
        name: file.name,
        size: file.size,
        type: file.type
      });

      if (!validationResult.success) {
        const errorMsg = validationResult.error.errors.map((e: any) => e.message).join(', ');
        this.showToast(errorMsg, 'error');
        continue;
      }
      const formData = new FormData();
      formData.append('files', file);

      try {
        const response = await fetch('/api/v1/upload', { method: 'POST', body: formData });
        if (!response.ok) throw new Error('Upload failed');

        const responseData = await response.json();
        const analysisData = responseData.data;

        if (!analysisData) {
          throw new Error('Invalid server response: No data received');
        }

        const skippedCount = analysisData.skipped_count || 0;
        const warnings = analysisData.warnings || [];
        const successCount = (analysisData.subscriptions?.length || 0) + (analysisData.total_expenses > 0 ? 50 : 0);

        if (skippedCount > 0) {
          this.uploadResult = { count: successCount, warnings: warnings, skipped: skippedCount };
        }

        const fileSize = formatSize(file.size);
        const existing = budgetStore.state.uploadedFiles.find(f => f.name === file.name);

        if (existing) {
          this.pendingConflict = { file: file, analysisData, size: fileSize };
          this.isUploading = false;
          budgetStore.setLoading(false);
          const input = this.shadowRoot?.getElementById('fileInput') as HTMLInputElement;
          if (input) input.value = '';
          return;
        }

        budgetStore.setData({ transactions: analysisData.transactions || [], metrics: analysisData }, file.name, fileSize);

        if (skippedCount === 0) this.showToast('Upload successful!', 'success');

      } catch (e: unknown) {
        const error = e instanceof Error ? e : new Error(String(e));
        logger.error('File upload failed', 'file-upload', error, { fileName: file.name });
        this.showToast(error.message || 'Upload failed', 'error');
      }
    }
    this.isUploading = false;
    budgetStore.setLoading(false);
    const input = this.shadowRoot?.getElementById('fileInput') as HTMLInputElement;
    if (input) input.value = '';
  }

  /* Boilerplate Handlers */
  private handleDragOver(e: DragEvent) { e.preventDefault(); e.stopPropagation(); this.isDragging = true; }
  private handleDragLeave(e: DragEvent) { e.preventDefault(); e.stopPropagation(); this.isDragging = false; }
  private handleDrop(e: DragEvent) {
    e.preventDefault(); e.stopPropagation(); this.isDragging = false;
    if (e.dataTransfer?.files) this.processFiles(e.dataTransfer.files);
  }
  private handleUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files) this.processFiles(input.files);
  }
  private showToast(message: string, type: ToastType) { this.toastState = { message, type, visible: true }; }
  private hideToast() { this.toastState = { ...this.toastState, visible: false }; }

  private resolveConflict(action: 'overwrite' | 'keep' | 'cancel') {
    if (!this.pendingConflict) return;
    const { file, analysisData, size } = this.pendingConflict;
    if (action === 'cancel') { this.pendingConflict = null; return; }
    if (action === 'overwrite') {
      const existing = budgetStore.state.uploadedFiles.find(f => f.name === file.name);
      if (existing) budgetStore.removeUploadedFile(existing.id);
    }
    budgetStore.setData({ transactions: analysisData.transactions || [], metrics: analysisData }, file.name, size);
    this.pendingConflict = null;
  }

  render() {
    return html`
      ${this.renderConflictModal()}
      ${this.renderResultModal()}

      <toast-notification 
        .message=${this.toastState.message} 
        .type=${this.toastState.type} 
        .visible=${this.toastState.visible}
        @close=${this.hideToast}
      ></toast-notification>

      <div class="tabs">
        <button class="tab ${this.activeTab === 'local' ? 'active' : ''}" @click=${() => this.activeTab = 'local'}>Local</button>
        <button class="tab ${this.activeTab === 'onedrive' ? 'active' : ''}" @click=${() => this.activeTab = 'onedrive'}>OneDrive</button>
        <button class="tab ${this.activeTab === 'sharepoint' ? 'active' : ''}" @click=${() => this.activeTab = 'sharepoint'}>SharePoint</button>
      </div>

      ${this.activeTab === 'local' ? html`
        <div 
          class="upload-zone ${this.isUploading ? 'uploading' : ''} ${this.isDragging ? 'drag-active' : ''}"
          @click=${() => this.shadowRoot?.getElementById('fileInput')?.click()}
          @dragover=${this.handleDragOver}
          @dragleave=${this.handleDragLeave}
          @drop=${this.handleDrop}
          role="button"
          tabindex="0"
          aria-label="Drop files here to upload"
          aria-describedby="upload-description"
        >
          <input type="file" accept=".xlsx, .xls" multiple style="display: none" id="fileInput" @change=${this.handleUpload} aria-label="Upload file" />
          <div class="icon" aria-hidden="true">${this.isUploading ? '⏳' : '📁'}</div>
          <div class="text">${this.isUploading ? 'Uploading...' : 'Drop your budget files here'}</div>
          <div class="subtext" id="upload-description">Supports multiple .xlsx and .xls files</div>
          ${!this.isUploading ? html`<button class="btn btn-primary" style="margin-top: 1rem;" aria-label="Select file to upload">Select File</button>` : ''}
        </div>
      ` : html`
        <div class="upload-zone">
          <div class="icon">🚧</div>
          <div class="text">Coming Soon</div>
          <div class="subtext">${this.activeTab === 'onedrive' ? 'OneDrive' : 'SharePoint'} integration is under development.</div>
        </div>
      `}
    `;
  }

  renderConflictModal() {
    if (!this.pendingConflict) return '';
    return html`
        <div class="modal-overlay">
          <div class="modal">
            <h3 style="color: var(--color-primary); margin-top:0;">File Conflict Detected</h3>
            <p>A file named <strong>"${this.pendingConflict.file.name}"</strong> already exists.</p>
            <div class="flex-row justify-between gap-md" style="margin-top: 1.5rem; justify-content: center;">
              <button class="btn btn-secondary" @click=${() => this.resolveConflict('cancel')}>Cancel</button>
              <button class="btn btn-secondary" @click=${() => this.resolveConflict('keep')}>Keep Both</button>
              <button class="btn btn-primary" @click=${() => this.resolveConflict('overwrite')}>Overwrite</button>
            </div>
          </div>
        </div>
     `;
  }

  renderResultModal() {
    if (!this.uploadResult) return '';
    return html`
        <div class="modal-overlay">
          <div class="modal" style="max-width: 600px;">
            <h3 style="color: var(--color-primary); margin-top:0;">Upload Status: ${this.uploadResult.skipped === 0 ? 'Success' : 'Partial Success'}</h3>
            <p>
                Successfully uploaded <strong>${this.uploadResult.count}</strong> rows.
                ${this.uploadResult.skipped > 0 ? html`<br/><span class="text-warning">Skipped <strong>${this.uploadResult.skipped}</strong> rows due to errors.</span>` : ''}
            </p>
            ${this.uploadResult.warnings.length > 0 ? html`
                <div style="background: rgba(0,0,0,0.1); padding: 1rem; border-radius: var(--radius-sm); text-align: left; max-height: 200px; overflow-y: auto; font-size: 0.85rem; font-family: monospace; margin-bottom: 1.5rem;">
                    ${this.uploadResult.warnings.map(w => html`<div class="text-error" style="margin-bottom: 0.25rem;">${w}</div>`)}
                </div>
            ` : ''}
            <div style="text-align: center;">
              <button class="btn btn-primary" @click=${() => this.uploadResult = null}>Close</button>
            </div>
          </div>
        </div>
     `;
  }
}
