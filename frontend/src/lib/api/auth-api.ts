import { z } from "zod";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// ============================================================================
// Types
// ============================================================================

export interface User {
    id: string;
    email: string;
    full_name?: string;
    role: string;
    tenant_id: string;
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
// API Functions
// ============================================================================

/**
 * Helper for making auth requests
 */
async function authRequest<T>(endpoint: string, data: any): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    const responseData = await response.json();

    if (!response.ok) {
        throw new Error(responseData.detail || "Authentication failed");
    }

    return responseData;
}

export const authApi = {
    login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
        return authRequest<AuthResponse>("/api/v1/auth/login", credentials);
    },

    register: async (data: RegisterData): Promise<AuthResponse> => {
        return authRequest<AuthResponse>("/api/v1/auth/register", data);
    }
};
