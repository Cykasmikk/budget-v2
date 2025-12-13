/**
 * Structured logging service for frontend
 * Replaces console.log/error with proper JSON-structured logging
 */

export enum LogLevel {
    DEBUG = 'debug',
    INFO = 'info',
    WARN = 'warn',
    ERROR = 'error'
}

interface LogEntry {
    timestamp: string;
    level: LogLevel;
    component?: string;
    message: string;
    data?: unknown;
    error?: {
        message: string;
        stack?: string;
    };
}

class Logger {
    private isDevelopment: boolean;

    constructor() {
        // @ts-ignore - Vite provides import.meta.env
        this.isDevelopment = (typeof import.meta !== 'undefined' && import.meta.env?.DEV) || process.env.NODE_ENV === 'development';
    }

    private shouldLog(level: LogLevel): boolean {
        if (this.isDevelopment) {
            return true; // Log all levels in development
        }
        // In production, only log warnings and errors
        return level === LogLevel.WARN || level === LogLevel.ERROR;
    }

    private formatLog(level: LogLevel, message: string, component?: string, data?: unknown, error?: Error): LogEntry {
        const entry: LogEntry = {
            timestamp: new Date().toISOString(),
            level,
            message
        };
        if (component) {
            entry.component = component;
        }
        if (data) {
            entry.data = data;
        }
        if (error) {
            entry.error = {
                message: error.message,
                stack: error.stack
            };
        }
        return entry;
    }

    private log(level: LogLevel, message: string, component?: string, data?: unknown, error?: Error): void {
        if (!this.shouldLog(level)) {
            return;
        }

        const entry = this.formatLog(level, message, component, data, error);
        const jsonString = JSON.stringify(entry);

        // Use appropriate console method based on level
        switch (level) {
            case LogLevel.DEBUG:
                console.debug(jsonString);
                break;
            case LogLevel.INFO:
                console.info(jsonString);
                break;
            case LogLevel.WARN:
                console.warn(jsonString);
                break;
            case LogLevel.ERROR:
                console.error(jsonString);
                break;
        }
    }

    debug(message: string, component?: string, data?: unknown): void {
        this.log(LogLevel.DEBUG, message, component, data);
    }

    info(message: string, component?: string, data?: unknown): void {
        this.log(LogLevel.INFO, message, component, data);
    }

    warn(message: string, component?: string, data?: unknown): void {
        this.log(LogLevel.WARN, message, component, data);
    }

    error(message: string, component?: string, error?: Error, data?: unknown): void {
        this.log(LogLevel.ERROR, message, component, data, error);
    }
}

export const logger = new Logger();

