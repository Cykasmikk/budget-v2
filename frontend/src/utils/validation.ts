import { z } from 'zod';

/**
 * Validation schemas for user inputs
 * All schemas use strict validation to prevent XSS and invalid data
 */

/**
 * Regex pattern validation for categorization rules
 * Max length 200 chars, must be valid regex
 */
export const RulePatternSchema = z.string()
    .min(1, 'Pattern cannot be empty')
    .max(200, 'Pattern must be less than 200 characters')
    .refine((val: string) => {
        try {
            new RegExp(val);
            return true;
        } catch {
            return false;
        }
    }, 'Pattern must be a valid regular expression');

/**
 * Category name validation
 * Alphanumeric, spaces, hyphens, underscores allowed
 * Max 100 characters
 */
export const CategorySchema = z.string()
    .min(1, 'Category cannot be empty')
    .max(100, 'Category must be less than 100 characters')
    .regex(/^[a-zA-Z0-9\s\-_]+$/, 'Category can only contain letters, numbers, spaces, hyphens, and underscores');

/**
 * Chat message validation
 * Max 2000 characters, no HTML/script tags
 */
export const ChatMessageSchema = z.string()
    .min(1, 'Message cannot be empty')
    .max(2000, 'Message must be less than 2000 characters')
    .refine((val: string) => {
        // Check for potential XSS patterns
        const dangerousPatterns = /<script|javascript:|onerror=|onclick=/i;
        return !dangerousPatterns.test(val);
    }, 'Message contains invalid content');

/**
 * Email validation
 * Standard email format
 */
export const EmailSchema = z.string()
    .min(1, 'Email is required')
    .email('Invalid email format')
    .max(255, 'Email must be less than 255 characters');

/**
 * Password validation
 * Min 8 characters, must contain at least one letter and one number
 */
export const PasswordSchema = z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password must be less than 128 characters')
    .regex(/[a-zA-Z]/, 'Password must contain at least one letter')
    .regex(/[0-9]/, 'Password must contain at least one number');

/**
 * SSO Issuer URL validation
 * Must be a valid HTTPS URL
 */
export const IssuerUrlSchema = z.string()
    .min(1, 'Issuer URL is required')
    .max(500, 'URL must be less than 500 characters')
    .url('Invalid URL format')
    .refine((val: string) => val.startsWith('https://'), 'Issuer URL must use HTTPS');

/**
 * SSO Client ID validation
 * Alphanumeric, hyphens, underscores allowed
 */
export const ClientIdSchema = z.string()
    .min(1, 'Client ID is required')
    .max(200, 'Client ID must be less than 200 characters')
    .regex(/^[a-zA-Z0-9\-_]+$/, 'Client ID can only contain letters, numbers, hyphens, and underscores');

/**
 * SSO Client Secret validation
 * Non-empty, min 10 characters
 */
export const ClientSecretSchema = z.string()
    .min(10, 'Client Secret must be at least 10 characters')
    .max(500, 'Client Secret must be less than 500 characters');

/**
 * SSO Configuration schema
 */
export const SSOConfigSchema = z.object({
    enabled: z.boolean(),
    issuer_url: IssuerUrlSchema,
    client_id: ClientIdSchema,
    client_secret: ClientSecretSchema,
    provider_name: z.string().max(100).optional()
});

/**
 * File upload validation
 * Validates file type and size
 */
export const FileUploadSchema = z.object({
    name: z.string(),
    size: z.number().max(10 * 1024 * 1024, 'File size must be less than 10MB'), // 10MB max
    type: z.string().refine((val: string) => {
        const validTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
            'application/vnd.ms-excel', // .xls
            'application/octet-stream' // Sometimes Excel files are detected as this
        ];
        return validTypes.includes(val) || val.endsWith('sheet') || val.endsWith('excel');
    }, 'File must be an Excel file (.xlsx or .xls)')
});

/**
 * Rule input validation (pattern + category)
 */
export const RuleInputSchema = z.object({
    pattern: RulePatternSchema,
    category: CategorySchema
});

/**
 * Validation error helper
 */
export function getValidationError(error: z.ZodError): string {
    return error.errors.map((e: z.ZodIssue) => e.message).join(', ');
}

