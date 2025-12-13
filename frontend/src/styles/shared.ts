import { css } from 'lit';

// Common Interactive Elements
export const buttonStyles = css`
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    font-weight: 500;
    font-family: var(--font-family);
    cursor: pointer;
    transition: all var(--transition-fast);
    border: 1px solid transparent;
    font-size: 0.9rem;
    line-height: 1.5;
    text-decoration: none;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
    box-shadow: var(--shadow-glow);
  }

  .btn-primary:hover:not(:disabled) {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
  }

  .btn-secondary {
    background: transparent;
    border-color: var(--color-border);
    color: var(--color-text);
  }

  .btn-secondary:hover:not(:disabled) {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }

  .btn-ghost {
    background: transparent;
    color: var(--color-text-muted);
  }

  .btn-ghost:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.05);
    color: var(--color-text);
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
  }
`;

// Input Fields & Forms
export const formStyles = css`
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .form-label {
    font-size: 0.85rem;
    color: var(--color-text-muted);
    font-weight: 500;
  }

  .form-control {
    width: 100%;
    padding: 0.6rem 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text);
    font-family: var(--font-family);
    font-size: 0.9rem;
    transition: border-color var(--transition-fast);
  }

  .form-control:focus {
    outline: none;
    border-color: var(--color-primary);
    background: rgba(255, 255, 255, 0.08);
  }
  
  select.form-control {
    appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 0.75rem center;
    background-size: 1em;
    padding-right: 2.5rem;
  }
`;

// Card & Containers
export const cardStyles = css`
  .card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .card-title {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--color-text);
    margin: 0;
  }
`;

// Utility Classes
export const utilityStyles = css`
  .text-muted { color: var(--color-text-muted); }
  .text-success { color: var(--color-success); }
  .text-error { color: var(--color-error); }
  .text-primary { color: var(--color-primary); }
  
  .flex-row { display: flex; flex-direction: row; }
  .flex-col { display: flex; flex-direction: column; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .gap-sm { gap: 0.5rem; }
  .gap-md { gap: 1rem; }
  
  .w-full { width: 100%; }
  .h-full { height: 100%; }
`;

// Re-export specific groups
export const sharedStyles = [buttonStyles, formStyles, cardStyles, utilityStyles];
