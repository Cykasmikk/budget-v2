/**
 * Responsive design utilities
 * Provides breakpoint constants and reactive breakpoint detection
 */

export const BREAKPOINTS = {
    MOBILE: 320,
    TABLET: 768,
    DESKTOP: 1200,
    LARGE: 1920,
    FOUR_K: 3840
} as const;

export type Breakpoint = keyof typeof BREAKPOINTS;

/**
 * Reactive media query hook for Lit components
 * Returns true if the current viewport matches the breakpoint
 */
export function useMediaQuery(query: string): boolean {
    if (typeof window === 'undefined' || !window.matchMedia) {
        return false;
    }
    
    const mediaQuery = window.matchMedia(query);
    return mediaQuery.matches;
}

/**
 * Get current breakpoint name based on viewport width
 */
export function getCurrentBreakpoint(): Breakpoint {
    if (typeof window === 'undefined') {
        return 'DESKTOP';
    }
    
    const width = window.innerWidth;
    
    if (width >= BREAKPOINTS.FOUR_K) return 'FOUR_K';
    if (width >= BREAKPOINTS.LARGE) return 'LARGE';
    if (width >= BREAKPOINTS.DESKTOP) return 'DESKTOP';
    if (width >= BREAKPOINTS.TABLET) return 'TABLET';
    return 'MOBILE';
}

/**
 * Check if viewport is mobile
 */
export function isMobile(): boolean {
    return getCurrentBreakpoint() === 'MOBILE';
}

/**
 * Check if viewport is tablet
 */
export function isTablet(): boolean {
    return getCurrentBreakpoint() === 'TABLET';
}

/**
 * Check if viewport is desktop or larger
 */
export function isDesktop(): boolean {
    const bp = getCurrentBreakpoint();
    return bp === 'DESKTOP' || bp === 'LARGE' || bp === 'FOUR_K';
}

/**
 * CSS media query strings for use in styles
 */
export const MEDIA_QUERIES = {
    mobile: `(max-width: ${BREAKPOINTS.TABLET - 1}px)`,
    tablet: `(min-width: ${BREAKPOINTS.TABLET}px) and (max-width: ${BREAKPOINTS.DESKTOP - 1}px)`,
    desktop: `(min-width: ${BREAKPOINTS.DESKTOP}px)`,
    large: `(min-width: ${BREAKPOINTS.LARGE}px)`,
    fourK: `(min-width: ${BREAKPOINTS.FOUR_K}px)`
} as const;

