import { apiClient } from '../api-client';

// ============================================================================
// Types
// ============================================================================

export interface User {
    id: string;
    email: string;
    tenant_id: string;
    role: string;
    full_name?: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterData {
    email: string;
    password: string;
    full_name: string;
}

// ============================================================================
// Auth API
// ============================================================================

export const authApi = {
    /**
     * Register a new user
     */
    register: async (data: RegisterData): Promise<AuthResponse> => {
        const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data);
        return response.data;
    },

    /**
     * Login with email and password
     */
    login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
        const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', credentials);
        return response.data;
    },

    /**
     * Get current authenticated user info
     */
    me: async (): Promise<User> => {
        const response = await apiClient.get<User>('/api/v1/auth/me');
        return response.data;
    },

    /**
     * Logout (Local cleanup, can also notify backend if endpoint exists)
     */
    logout: async (): Promise<void> => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // If there's a logout endpoint: await apiClient.post('/api/v1/auth/logout');
    }
};
