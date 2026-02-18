
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { useAuth } from '@/context/auth-context';
import React from 'react';

// Mock the AuthContext
vi.mock('@/context/auth-context', () => ({
    useAuth: vi.fn(),
}));

describe('ProtectedRoute', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders loading spinner when authenticating', () => {
        (useAuth as any).mockReturnValue({
            isAuthenticated: false,
            isLoading: true,
            login: vi.fn(),
        });

        render(
            <ProtectedRoute>
                <div>Protected Content</div>
            </ProtectedRoute>
        );

        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
        expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('renders children when authenticated', () => {
        (useAuth as any).mockReturnValue({
            isAuthenticated: true,
            isLoading: false,
            login: vi.fn(),
        });

        render(
            <ProtectedRoute>
                <div>Protected Content</div>
            </ProtectedRoute>
        );

        expect(screen.getByText('Protected Content')).toBeInTheDocument();
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });

    it('redirects to login when not authenticated', async () => {
        const loginMock = vi.fn();
        (useAuth as any).mockReturnValue({
            isAuthenticated: false,
            isLoading: false,
            login: loginMock,
        });

        render(
            <ProtectedRoute>
                <div>Protected Content</div>
            </ProtectedRoute>
        );

        expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
        // Since useEffect is async, we might need waitFor, but typically it runs after render.
        // We'll verify login is called.
        await waitFor(() => {
            expect(loginMock).toHaveBeenCalled();
        });
    });
});
