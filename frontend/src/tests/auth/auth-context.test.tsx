
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from '@/context/auth-context';
import { useAuth0 } from '@auth0/auth0-react';
import React from 'react';

// Mock the Auth0 hook
vi.mock('@auth0/auth0-react', () => ({
    Auth0Provider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    useAuth0: vi.fn(),
}));

// Test component to consume the context
const TestComponent = () => {
    const { isAuthenticated, user, login, logout } = useAuth();
    return (
        <div>
            <div data-testid="auth-status">{isAuthenticated ? 'Authenticated' : 'Not Authenticated'}</div>
            <div data-testid="user-name">{user?.name || 'No User'}</div>
            <button onClick={() => login()}>Login</button>
            <button onClick={() => logout()}>Logout</button>
        </div>
    );
};

describe('AuthContext', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.stubEnv('NEXT_PUBLIC_AUTH0_DOMAIN', 'test-domain.auth0.com');
        vi.stubEnv('NEXT_PUBLIC_AUTH0_CLIENT_ID', 'test-client-id');
        vi.stubEnv('NEXT_PUBLIC_AUTH0_AUDIENCE', 'test-audience');
    });

    it('provides authentication status from Auth0', async () => {
        // Mock Auth0 as not authenticated
        (useAuth0 as any).mockReturnValue({
            isAuthenticated: false,
            user: undefined,
            loginWithRedirect: vi.fn(),
            logout: vi.fn(),
            isLoading: false,
        });

        render(
            <AuthProvider>
                <TestComponent />
            </AuthProvider>
        );

        expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
        expect(screen.getByTestId('user-name')).toHaveTextContent('No User');
    });

    it('provides user details when authenticated', async () => {
        // Mock Auth0 as authenticated
        (useAuth0 as any).mockReturnValue({
            isAuthenticated: true,
            user: { name: 'Test User', email: 'test@example.com' },
            loginWithRedirect: vi.fn(),
            logout: vi.fn(),
            isLoading: false,
        });

        render(
            <AuthProvider>
                <TestComponent />
            </AuthProvider>
        );

        expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
        expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    });

    it('calls loginWithRedirect when login is called', async () => {
        const loginMock = vi.fn();
        (useAuth0 as any).mockReturnValue({
            isAuthenticated: false,
            loginWithRedirect: loginMock,
            logout: vi.fn(),
            isLoading: false,
        });

        render(
            <AuthProvider>
                <TestComponent />
            </AuthProvider>
        );

        screen.getByText('Login').click();
        expect(loginMock).toHaveBeenCalled();
    });

    it('sets OpenAPI token when authenticated', async () => {
        const { OpenAPI } = await import('@/lib/api-client');

        // Mock getAccessTokenSilently to return a token
        (useAuth0 as any).mockReturnValue({
            isAuthenticated: true,
            user: { name: 'Test User' },
            loginWithRedirect: vi.fn(),
            logout: vi.fn(),
            isLoading: false,
            getAccessTokenSilently: vi.fn().mockResolvedValue('mock-token'),
        });

        render(
            <AuthProvider>
                <TestComponent />
            </AuthProvider>
        );

        await waitFor(async () => {
            // OpenAPI.TOKEN can be a function or string
            // The generated client defines it as `string | (() => Promise<string>)`
            // Check if it resolves to 'mock-token'
            let tokenValue = OpenAPI.TOKEN;
            if (typeof tokenValue === 'function') {
                tokenValue = await (tokenValue as any)();
            }
            expect(tokenValue).toBe('mock-token');
        });
    });
});
