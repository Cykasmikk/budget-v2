import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { Transaction } from '../store/budget.store';

@customElement('budget-table')
export class BudgetTable extends LitElement {
    @property({ type: Array }) transactions: Transaction[] = [];

    static styles = css`
    :host {
      display: block;
      overflow-x: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      color: var(--color-primary);
    }
    th, td {
      padding: 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }
    th {
      background: var(--color-surface);
      color: var(--color-accent);
      font-weight: 600;
    }
    tr:hover {
      background: var(--color-surface-hover);
    }
    .income { color: var(--color-success); }
    .expense { color: var(--color-danger); }
  `;

    render() {
        return html`
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Category</th>
            <th>Type</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          ${this.transactions.map(t => html`
            <tr>
              <td>${new Date(t.date).toLocaleDateString('en-CA')}</td>
              <td>${t.description}</td>
              <td>${t.category}</td>
              <td class="${t.type || ''}">${(t.type || 'unknown').toUpperCase()}</td>
              <td class="${t.type || ''}">$${t.amount?.toFixed(2) || '0.00'}</td>
            </tr>
          `)}
        </tbody>
      </table>
    `;
    }
}
