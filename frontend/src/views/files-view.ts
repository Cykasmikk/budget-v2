import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import { StoreController } from '../store/controller';
import { budgetStore, MergeStrategy } from '../store/budget-store';

@customElement('files-view')
export class FilesView extends LitElement {
  static styles = css`
    :host {
      display: block;
      padding: 2rem;
      color: var(--color-text);
      max-width: 1000px;
      margin: 0 auto;
    }

    h1 {
      font-size: 2rem;
      margin-bottom: 2rem;
      font-weight: 700;
      background: var(--gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .section {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: 1.5rem;
      margin-bottom: 2rem;
    }

    .section-header {
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .strategy-group {
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
    }

    .strategy-option {
      flex: 1;
      padding: 1rem;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all var(--transition-fast);
      background: rgba(255, 255, 255, 0.02);
    }

    .strategy-option:hover {
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--color-primary);
    }

    .strategy-option.active {
      background: rgba(59, 130, 246, 0.1);
      border-color: var(--color-primary);
      box-shadow: 0 0 0 1px var(--color-primary);
    }

    .strategy-option.disabled {
      opacity: 0.5;
      cursor: not-allowed;
      border-color: transparent;
    }
    
    .strategy-option.disabled:hover {
        background: rgba(255, 255, 255, 0.02);
        border-color: transparent;
    }

    .strategy-title {
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: var(--color-text);
    }

    .strategy-desc {
      font-size: 0.85rem;
      color: var(--color-text-muted);
      line-height: 1.4;
    }

    .file-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .file-item {
      display: flex;
      align-items: center;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
    }

    .file-icon {
      font-size: 1.5rem;
      margin-right: 1rem;
    }

    .file-info {
      flex: 1;
    }

    .file-name {
      font-weight: 500;
      color: var(--color-text);
      margin-bottom: 0.25rem;
    }

    .file-meta {
      font-size: 0.8rem;
      color: var(--color-text-muted);
    }

    .delete-btn {
      background: transparent;
      border: none;
      color: var(--color-text-muted);
      cursor: pointer;
      padding: 0.5rem;
      border-radius: var(--radius-sm);
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .delete-btn:hover {
      background: rgba(239, 68, 68, 0.1);
      color: var(--color-error);
    }

    .empty-state {
      text-align: center;
      padding: 3rem;
      color: var(--color-text-muted);
      border: 2px dashed var(--color-border);
      border-radius: var(--radius-lg);
    }
  `;

  // @ts-ignore
  private storeController = new StoreController(this, budgetStore.getStore());

  get isMultiFile(): boolean {
    return budgetStore.state.uploadedFiles.length > 1;
  }

  private setStrategy(strategy: MergeStrategy) {
    budgetStore.setMergeStrategy(strategy);
  }

  private handleStrategyClick(strategy: MergeStrategy, isEnabled: boolean) {
    if (!isEnabled) {
      alert("This strategy requires at least 2 uploaded files. Please upload another file.");
      return;
    }
    this.setStrategy(strategy);
  }

  private removeFile(e: Event, id: string) {
    e.stopPropagation();
    if (confirm('Are you sure you want to remove this file?')) {
      budgetStore.removeUploadedFile(id);
    }
  }

  render() {
    const { uploadedFiles, mergeStrategy } = budgetStore.state;

    return html`
      <h1>Files & Version Control</h1>

      <div class="section">
        <div class="section-header">
          Merge Strategy
        </div>
        <div style="font-size: 0.9rem; color: var(--color-text-muted); margin-bottom: 1rem;">
          Choose how multiple files are combined to generate dashboard insights.
        </div>

        <div class="strategy-group">
          <div 
            class="strategy-option ${mergeStrategy === 'latest' ? 'active' : ''}"
            @click=${() => this.handleStrategyClick('latest', true)}
          >
            <div class="strategy-title">Latest Version</div>
            <div class="strategy-desc">Only uses data from the most recently uploaded file. Previous files are stored but ignored.</div>
          </div>

          <div 
            class="strategy-option ${mergeStrategy === 'blended' ? 'active' : ''}"
            @click=${() => this.handleStrategyClick('blended', this.isMultiFile)}
          >
            <div class="strategy-title">Blended (Gap Fill)</div>
            <div class="strategy-desc">Prioritizes recent data, but fills in missing categories/projects from older files.</div>
          </div>

          <div 
            class="strategy-option ${mergeStrategy === 'combined' ? 'active' : ''}"
            @click=${() => this.handleStrategyClick('combined', this.isMultiFile)}
          >
            <div class="strategy-title">Full Combine</div>
            <div class="strategy-desc">Sums up values from all files. Useful for aggregating multi-department reports.</div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          Uploaded Files (${uploadedFiles.length})
        </div>

        ${uploadedFiles.length === 0 ? html`
          <div class="empty-state">
            No files uploaded yet. Use the sidebar to upload .xlsx files or load sample data.
          </div>
        ` : html`
          <div class="file-list">
            <!-- Reverse to show newest first -->
            ${[...uploadedFiles].reverse().map(file => html`
              <div class="file-item">
                <div class="file-icon">📄</div>
                <div class="file-info">
                  <div class="file-name">${file.name}</div>
                  <div class="file-meta">Uploaded: ${file.uploadDate} • Size: ${file.size}</div>
                </div>
                <button 
                  class="delete-btn" 
                  title="Remove File"
                  @click=${(e: Event) => this.removeFile(e, file.id)}
                >
                  🗑️
                </button>
              </div>
            `)}
          </div>
        `}
      </div>
    `;
  }
}
