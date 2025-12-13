import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { BudgetMetrics } from '../../store/budget-store';
import '../budget-chart';

@customElement('infographic-report')
export class InfographicReport extends LitElement {
  @property({ type: Object }) metrics: BudgetMetrics | null = null;
  @property({ type: Boolean }) visible: boolean = false;

  static styles = css`
    :host {
      display: block;
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.8);
      z-index: 9999;
      overflow-y: auto;
      backdrop-filter: blur(5px);
      display: none; /* Hidden by default */
    }

    :host([visible]) {
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 2rem;
    }

    .a4-page {
      width: 296mm;
      min-height: 210mm;
      background: white; /* Print background usually white */
      color: #1f2937; /* Dark gray text for print legibility */
      padding: 10mm; /* REFACTOR: Reduced padding */
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      font-family: 'Inter', sans-serif;
      display: flex;
      flex-direction: column;
      gap: 10px; /* REFACTOR: Reduced gap */
      position: relative;
      
      /* Chart Color Overrides for White Paper */
      --color-text: #111827;
      --color-text-muted: #6b7280;
      /* ... other vars ... */
      --color-border: #d1d5db; 
      --color-surface: #ffffff;
      --color-primary: #2563eb; 
      --color-success: #059669;
      --color-error: #dc2626;
    }

    /* Print Overrides */
    @media print {
      /* ... default overrides ... */
      .a4-page {
        width: 296mm !important; 
        height: 209mm !important;
        box-shadow: none !important;
        margin: 0 !important;
        padding: 10mm !important; /* REFACTOR: Reduced print padding */
        page-break-after: avoid !important;
        transform: scale(1); 
        overflow: hidden !important; 
      }
      /* ... */
    }

    h1, h2, h3 { margin: 0; }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #3b82f6;
      padding-bottom: 10px; /* REFACTOR: Reduced padding */
    }
    
    /* ... header styles ... */

    .grid-stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 10px; /* REFACTOR: Reduced margin */
    }

    .stat-card {
      background: #f3f4f6;
      padding: 10px; /* REFACTOR: Reduced padding */
      border-radius: 8px;
    }

    /* ... stat styles ... */

    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr; /* REFACTOR: 50/50 Split */
      grid-template-rows: 1fr 1fr;
      gap: 15px;
      height: 115mm; /* REFACTOR: Increased height significantly */
      margin-bottom: 10px; /* REFACTOR: Reduced margin */
    }

    .chart-box:first-child {
      grid-column: 1;
      grid-row: 1 / -1; /* Trend chart spans full height on left */
    }
    
    .chart-box:nth-child(2) {
      grid-column: 2;
      grid-row: 1;
    }

    .chart-box:nth-child(3) {
      grid-column: 2;
      grid-row: 2;
    }

    .chart-box {
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 10px; /* Reduce padding */
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .chart-title {
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 5px;
        color: #374151;
    }

    .chart-container {
        flex: 1;
        position: relative;
        min-height: 0; /* Important for flex/grid child scrolling/sizing */
    }

    .analysis-text {
      background: #eff6ff;
      border-left: 4px solid #3b82f6;
      padding: 20px;
      border-radius: 4px;
      font-size: 14px;
      line-height: 1.6;
      color: #374151;
    }
    
    .analysis-text h3 {
        font-size: 16px;
        color: #1d4ed8;
        margin-bottom: 10px;
    }

    .footer {
      margin-top: auto;
      border-top: 1px solid #e5e7eb;
      padding-top: 10px;
      text-align: center;
      font-size: 10px;
      color: #9ca3af;
    }

    .close-btn {
      position: absolute;
      top: 20px;
      right: 20px;
      background: white;
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      font-size: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .print-btn {
        position: absolute;
        top: 20px;
        right: 70px;
        background: #3b82f6;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
    }
    .chart-content {
        display: flex;
        flex: 1;
        gap: 15px;
        min-height: 0;
        overflow: hidden;
    }
    
    .chart-wrapper {
        flex: 1; /* Chart takes available space */
        min-width: 0;
        position: relative;
    }
    
    .data-list {
        flex: 0 0 45%; /* Fixed width for data list */
        font-size: 9px;
        overflow-y: hidden;
    }
    
    .data-row {
        display: flex;
        justify-content: space-between;
        padding: 2px 0;
        border-bottom: 1px solid #f3f4f6;
    }
    
    .data-name {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 80px;
    }
    
    .data-val {
        font-family: monospace;
        color: #6b7280;
    }
  `;

  renderDataList(data: Record<string, number>, total: number) {
    const sorted = Object.entries(data)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5); // Top 5

    return html`
        <div class="data-list">
            ${sorted.map(([name, value]) => html`
                <div class="data-row">
                    <span class="data-name" title="${name}">${name}</span>
                    <div style="display: flex; gap: 5px;">
                        <span class="data-val" style="font-weight: 600">$${(value / 1000).toFixed(0)}k</span>
                        <span class="data-val">${((value / total) * 100).toFixed(0)}%</span>
                    </div>
                </div>
            `)}
        </div>
      `;
  }

  render() {
    if (!this.metrics) return html``;

    const { total_expenses, category_breakdown, project_breakdown, monthly_trend } = this.metrics;

    // Auto-Analysis Generation
    const topCategory = Object.entries(category_breakdown).sort(([, a], [, b]) => b - a)[0];
    const topProject = Object.entries(project_breakdown).sort(([, a], [, b]) => b - a)[0];
    const trendDirection = (monthly_trend[monthly_trend.length - 1]?.amount || 0) > (monthly_trend[0]?.amount || 0) ? "increasing" : "decreasing";

    return html`
      <button class="no-print close-btn" @click=${() => this.dispatchEvent(new CustomEvent('close'))}>✕</button>
      <button class="no-print print-btn" @click=${() => window.print()}>🖨️ Print / Save PDF</button>

      <div class="a4-page">
        <!-- Header -->
        <div class="header">
          <h1>Budget Executive Report</h1>
          <div class="subtitle">
            Generated: ${new Date().toLocaleDateString()}<br>
            Budget FY 2024-2025
          </div>
        </div>

        <!-- KPI Row -->
        <div class="grid-stats">
          <div class="stat-card">
            <div class="stat-label">Total Annual Spend</div>
            <div class="stat-value">$${(total_expenses / 1000000).toFixed(2)}M</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Avg Monthly Spend</div>
            <div class="stat-value">$${(total_expenses / 12 / 1000).toFixed(0)}k</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Top Category</div>
            <div class="stat-value" style="font-size: 14px">${topCategory?.[0]}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Largest Project</div>
            <div class="stat-value" style="font-size: 14px">${topProject?.[0]}</div>
          </div>
        </div>

        <!-- Charts (High Res for Print) -->
        <div class="charts-row">
           <div class="chart-box">
             <div class="chart-title">Monthly Spending Trend</div>
             <div class="chart-container">
               <!-- Forced high-contrast forecast chart -->
               <budget-chart 
                 .data=${monthly_trend} 
                 viewMode="forecast" 
                 budgetLimit=${0}
               ></budget-chart>
             </div>
           </div>
           
           <div class="chart-box">
             <div class="chart-title">Category Split</div>
             <div class="chart-content">
               <div class="chart-wrapper">
                 <budget-chart 
                   .data=${category_breakdown} 
                   viewMode="category" 
                   budgetLimit=${0}
                 ></budget-chart>
               </div>
               ${this.renderDataList(category_breakdown, total_expenses)}
             </div>
           </div>

           <div class="chart-box">
             <div class="chart-title">Project Breakdown</div>
             <div class="chart-content">
               <div class="chart-wrapper">
                 <budget-chart 
                   .data=${project_breakdown} 
                   viewMode="project" 
                   budgetLimit=${0}
                 ></budget-chart>
               </div>
               ${this.renderDataList(project_breakdown, total_expenses)}
             </div>
           </div>
        </div>

        <!-- Automated Analysis -->
        <div class="analysis-text">
            <h3>🤖 AI Executive Summary</h3>
            <p>
                Total expenditure for the fiscal year is projected at <strong>$${(total_expenses / 1000000).toFixed(2)} million</strong>. 
                Spending patterns indicate a <strong>${trendDirection}</strong> trend over the 12-month period.
            </p>
            <p style="margin-top: 10px;">
                The largest cost driver remains <strong>${topCategory?.[0]}</strong>, accounting for approximately 
                <strong>${((topCategory?.[1] / total_expenses) * 100).toFixed(0)}%</strong> of the total budget.
                Project-based allocation is heavily weighted towards <strong>${topProject?.[0]}</strong>.
            </p>
            <p style="margin-top: 10px;">
                Recommendation: Review vendor agreements for ${topCategory?.[0]} and monitor the ${trendDirection} monthly trend to align with Q4 targets.
            </p>
        </div>

        <!-- Footer -->
        <div class="footer">
            CONFIDENTIAL - INTERNAL USE ONLY • Generated by BudgetAI System
        </div>
      </div>
    `;
  }
}
