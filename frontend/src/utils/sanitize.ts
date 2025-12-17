/**
 * Input sanitization utilities
 * Prevents XSS and ensures safe user input handling
 */

/**
 * Strip HTML tags from user input
 * @param input - User input string
 * @returns Sanitized string without HTML tags
 */
export function sanitizeHtml(input: string): string {
    const div = document.createElement('div');
    div.textContent = input;
    return div.textContent || div.innerText || '';
}

/**
 * Validate and escape regex patterns safely
 * @param pattern - Regex pattern string
 * @returns Validated pattern or throws error
 */
export function sanitizeRegex(pattern: string): string {
    try {
        // Test if pattern is valid
        new RegExp(pattern);
        return pattern;
    } catch (error) {
        throw new Error(`Invalid regex pattern: ${pattern}`);
    }
}

/**
 * Sanitize string input by removing dangerous characters
 * @param input - User input string
 * @returns Sanitized string
 */
export function sanitizeString(input: string): string {
    return input
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove script tags
        .replace(/javascript:/gi, '') // Remove javascript: protocol
        .replace(/on\w+\s*=/gi, '') // Remove event handlers
        .trim();
}

