import { Store } from "@tanstack/store";
import { logger } from '../services/logger';

export interface User {
    email: string;
    role: string;
}

export interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

export class AuthStore extends Store<AuthState> {
    constructor() {
        super({
            user: null,
            isAuthenticated: false,
            isLoading: true,
        });
        this.checkSession();
    }

    async checkSession() {
        this.setState((state) => ({ ...state, isLoading: true }));
        try {
            const response = await fetch('/api/v1/auth/me');
            if (response.ok) {
                const data = await response.json();
                this.setState((state) => ({
                    ...state,
                    user: { email: data.user, role: data.role },
                    isAuthenticated: true,
                    isLoading: false
                }));
            } else {
                this.setState((state) => ({ ...state, isLoading: false, isAuthenticated: false }));
            }
        } catch (e) {
            this.setState((state) => ({ ...state, isLoading: false, isAuthenticated: false }));
        }
    }

    loginSuccess(user: User) {
        this.setState((state) => {
            logger.debug('Login success', 'AuthStore', { email: user.email, role: user.role });
            return {
                ...state,
                user,
                isAuthenticated: true,
                isLoading: false
            };
        });
    }

    logout() {
        this.setState((state) => ({
            ...state,
            user: null,
            isAuthenticated: false
        }));
    }
}

export const authStore = new AuthStore();
