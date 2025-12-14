import { LitElement, html, css, svg } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { TimelineItem } from '../../../types/interfaces';

@customElement('gantt-chart')
export class GanttChart extends LitElement {
    @property({ type: Array }) items: TimelineItem[] = [];
    
    @state() private scrollOffset = 0;
    @state() private isDragging = false;
    @state() private startX = 0;
    @state() private initialScroll = 0;

    // Configuration
    private rowHeight = 40;
    private headerHeight = 50;
    private dayWidth = 20; // Pixels per day
    private sidebarWidth = 200;

    static styles = css`
        :host {
            display: block;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            position: relative;
            cursor: grab;
            user-select: none;
        }
        
        :host(:active) {
            cursor: grabbing;
        }

        .chart-container {
            width: 100%;
            height: 100%;
            overflow: hidden;
            position: relative;
        }

        svg {
            display: block;
        }

        text {
            fill: var(--color-text);
            font-family: var(--font-family);
            font-size: 0.85rem;
        }

        .grid-line {
            stroke: var(--color-border);
            stroke-width: 1;
            opacity: 0.3;
        }

        .today-line {
            stroke: var(--color-primary);
            stroke-width: 2;
            stroke-dasharray: 4 2;
        }

        .sidebar-bg {
            fill: var(--color-surface);
            opacity: 0.95;
        }
        
        .item-rect {
            rx: 4;
            ry: 4;
            filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));
            transition: opacity 0.2s;
        }
        
        .item-rect:hover {
            opacity: 0.8;
        }
    `;

    private get dateRange() {
        if (this.items.length === 0) {
            const now = new Date();
            return { start: now, end: new Date(now.getFullYear() + 1, 0, 1), totalDays: 365 };
        }

        const dates = this.items.flatMap(i => [new Date(i.start_date), new Date(i.end_date)]);
        const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
        const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));

        // Add padding
        minDate.setDate(minDate.getDate() - 7);
        maxDate.setDate(maxDate.getDate() + 30);

        const totalDays = Math.ceil((maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24));
        return { start: minDate, end: maxDate, totalDays };
    }

    private handleMouseDown(e: MouseEvent) {
        this.isDragging = true;
        this.startX = e.clientX;
        this.initialScroll = this.scrollOffset;
    }

    private handleMouseMove(e: MouseEvent) {
        if (!this.isDragging) return;
        const delta = e.clientX - this.startX;
        
        // Limit scrolling
        const { totalDays } = this.dateRange;
        const maxScroll = (totalDays * this.dayWidth) - (this.clientWidth - this.sidebarWidth);
        
        // Inverted delta for "drag to move canvas" feel
        let newScroll = this.initialScroll + delta;
        
        // Bounds checking
        if (newScroll > 0) newScroll = 0; // Can't scroll past start
        if (newScroll < -maxScroll) newScroll = -maxScroll; // Can't scroll past end

        this.scrollOffset = newScroll;
    }

    private handleMouseUp() {
        this.isDragging = false;
    }

    connectedCallback() {
        super.connectedCallback();
        this.addEventListener('mousedown', this.handleMouseDown);
        window.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        window.addEventListener('mouseup', () => this.handleMouseUp());
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener('mousedown', this.handleMouseDown);
        // Note: window listeners might need stricter cleanup if multiple instances exist,
        // but binding to 'this' usually requires a bound reference.
        // For prototype, this is acceptable, but ideally use bound methods.
    }

    render() {
        const { start, totalDays } = this.dateRange;
        const width = Math.max(this.clientWidth, 800); // Default min width
        const height = Math.max(this.items.length * this.rowHeight + this.headerHeight, this.clientHeight);
        
        return html`
            <div class="chart-container">
                <svg width="${width}" height="${height}">
                    <defs>
                        <clipPath id="chart-area">
                            <rect x="${this.sidebarWidth}" y="0" width="${width - this.sidebarWidth}" height="${height}" />
                        </clipPath>
                    </defs>

                    <!-- Background Grid -->
                    <g transform="translate(${this.sidebarWidth + this.scrollOffset}, 0)" clip-path="url(#chart-area)">
                        ${this.renderGrid(start, totalDays, height)}
                        ${this.renderItems(start)}
                    </g>

                    <!-- Sidebar (Fixed on Left) -->
                    <rect x="0" y="0" width="${this.sidebarWidth}" height="${height}" class="sidebar-bg" />
                    <line x1="${this.sidebarWidth}" y1="0" x2="${this.sidebarWidth}" y2="${height}" stroke="var(--color-border)" />
                    ${this.renderSidebar()}
                    
                    <!-- Header Background (Fixed Top) -->
                     <rect x="0" y="0" width="${width}" height="${this.headerHeight}" fill="var(--color-surface)" opacity="0.9" />
                     <line x1="0" y1="${this.headerHeight}" x2="${width}" y2="${this.headerHeight}" stroke="var(--color-border)" />
                     
                     <!-- Header Sidebar Label -->
                     <text x="10" y="30" font-weight="bold" fill="var(--color-primary)">Item Name</text>

                     <!-- Header Dates (Scrolls with grid) -->
                     <g transform="translate(${this.sidebarWidth + this.scrollOffset}, 0)" clip-path="url(#chart-area)">
                        ${this.renderHeaderDates(start, totalDays)}
                     </g>
                </svg>
            </div>
        `;
    }

    private renderGrid(startDate: Date, days: number, height: number) {
        const elements = [];
        const today = new Date();
        const diffToday = Math.ceil((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

        for (let i = 0; i <= days; i++) {
            const x = i * this.dayWidth;
            
            // Month separators
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            
            if (currentDate.getDate() === 1) {
                elements.push(svg`
                    <line x1="${x}" y1="0" x2="${x}" y2="${height}" stroke="var(--color-border)" stroke-width="2" opacity="0.5" />
                `);
            } else {
                elements.push(svg`
                    <line x1="${x}" y1="0" x2="${x}" y2="${height}" class="grid-line" />
                `);
            }
        }

        // Today Line
        if (diffToday >= 0 && diffToday <= days) {
            const todayX = diffToday * this.dayWidth;
            elements.push(svg`
                <line x1="${todayX}" y1="0" x2="${todayX}" y2="${height}" class="today-line" />
            `);
        }

        return elements;
    }

    private renderHeaderDates(startDate: Date, days: number) {
        const elements = [];
        for (let i = 0; i <= days; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            
            // Render Month Label
            if (currentDate.getDate() === 1) {
                const x = i * this.dayWidth;
                const label = currentDate.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
                elements.push(svg`
                    <text x="${x + 5}" y="30" font-weight="bold">${label}</text>
                `);
            }
        }
        return elements;
    }

    private renderSidebar() {
        return this.items.map((item, index) => {
            const y = this.headerHeight + (index * this.rowHeight) + (this.rowHeight / 2) + 5;
            return svg`
                <text x="10" y="${y}" style="font-size: 0.8rem;">${item.label}</text>
                <line x1="0" y1="${this.headerHeight + (index + 1) * this.rowHeight}" x2="${this.sidebarWidth}" y2="${this.headerHeight + (index + 1) * this.rowHeight}" stroke="var(--color-border)" opacity="0.3" />
            `;
        });
    }

    private renderItems(startDate: Date) {
        return this.items.map((item, index) => {
            const start = new Date(item.start_date);
            const end = new Date(item.end_date);
            
            const startDiff = Math.ceil((start.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
            const duration = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
            
            const x = startDiff * this.dayWidth;
            const width = Math.max(duration * this.dayWidth, 5); // Min width for visibility
            const y = this.headerHeight + (index * this.rowHeight) + 10;
            const height = this.rowHeight - 20;
            
            // Generate color based on type if not provided
            let color = item.color || 'var(--color-primary)';
            if (!item.color) {
                switch(item.type) {
                    case 'contract': color = '#10b981'; break;
                    case 'hardware': color = '#f59e0b'; break;
                    case 'subscription': color = '#3b82f6'; break;
                    case 'renewal': color = '#ef4444'; break;
                }
            }

            return svg`
                <rect 
                    x="${x}" 
                    y="${y}" 
                    width="${width}" 
                    height="${height}" 
                    fill="${color}" 
                    class="item-rect"
                >
                    <title>${item.label}: ${start.toLocaleDateString()} - ${end.toLocaleDateString()}</title>
                </rect>
                <text x="${x + width + 5}" y="${y + height / 2 + 4}" fill="${color}" style="font-size: 0.75rem;">${item.amount ? '$' + item.amount.toLocaleString() : ''}</text>
            `;
        });
    }
}
