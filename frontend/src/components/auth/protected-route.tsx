
'use client';

import { useAuth } from '@/context/auth-context';
import { Loader2 } from 'lucide-react';
import { useEffect } from 'react';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
    const { isAuthenticated, isLoading, isApiReady, login } = useAuth();

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            login();
        }
    }, [isLoading, isAuthenticated, login]);

    if (isLoading || (isAuthenticated && !isApiReady)) {
        return (
            <div
                className="flex h-screen w-full items-center justify-center"
                data-testid="loading-spinner"
            >
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return <>{children}</>;
};
