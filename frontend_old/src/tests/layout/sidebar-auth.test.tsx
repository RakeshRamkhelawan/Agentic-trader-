
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Sidebar } from '@/components/layout/sidebar';
import { useAuth } from '@/context/auth-context';
import React from 'react';

// Mock the AuthContext
vi.mock('@/context/auth-context', () => ({
    useAuth: vi.fn(),
}));

// Mock Next.js hooks
vi.mock('next/navigation', () => ({
    usePathname: () => '/',
}));

describe('Sidebar Auth', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('shows login button when not authenticated', () => {
        (useAuth as any).mockReturnValue({
            isAuthenticated: false,
            login: vi.fn(),
            logout: vi.fn(),
        });

        render(<Sidebar />);

        const loginBtn = screen.getByRole('button', { name: /login/i });
        expect(loginBtn).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /logout/i })).not.toBeInTheDocument();
    });

    it('shows logout button when authenticated', () => {
        (useAuth as any).mockReturnValue({
            isAuthenticated: true,
            user: { name: 'Test User' },
            login: vi.fn(),
            logout: vi.fn(),
        });

        render(<Sidebar />);

        const logoutBtn = screen.getByRole('button', { name: /logout/i });
        expect(logoutBtn).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /login/i })).not.toBeInTheDocument();
    });

    it('calls login when login button is clicked', () => {
        const loginMock = vi.fn();
        (useAuth as any).mockReturnValue({
            isAuthenticated: false,
            login: loginMock,
            logout: vi.fn(),
        });

        render(<Sidebar />);

        fireEvent.click(screen.getByRole('button', { name: /login/i }));
        expect(loginMock).toHaveBeenCalled();
    });

    it('calls logout when logout button is clicked', () => {
        const logoutMock = vi.fn();
        (useAuth as any).mockReturnValue({
            isAuthenticated: true,
            logout: logoutMock,
            login: vi.fn(),
        });

        render(<Sidebar />);

        fireEvent.click(screen.getByRole('button', { name: /logout/i }));
        expect(logoutMock).toHaveBeenCalled();
    });
});
