
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { Auth0Provider, useAuth0, AppState, User } from '@auth0/auth0-react';
import { OpenAPI } from '@/lib/api-client/generated/core/OpenAPI';
import { useRouter } from 'next/navigation';
import { wsClient } from '@/lib/api/websocket-client';

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    isApiReady: boolean;
    user: User | undefined;
    login: () => Promise<void>;
    logout: () => void;
    getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: React.ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
    const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN;
    const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID;
    const audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE;
    const router = useRouter();

    // Verify env vars
    useEffect(() => {
        if (!domain || !clientId) {
            console.error('Auth0 domain and client ID must be defined in environment variables');
        }
    }, [domain, clientId]);

    const onRedirectCallback = (appState?: AppState) => {
        router.push(appState?.returnTo || '/');
    };

    if (!domain || !clientId) {
        return <div>Auth0 Configuration Missing</div>;
    }

    return (
        <Auth0Provider
            domain={domain}
            clientId={clientId}
            authorizationParams={{
                redirect_uri: typeof window !== 'undefined' ? `${window.location.origin}/api/auth/callback` : '',
                audience: audience,
            }}
            onRedirectCallback={onRedirectCallback}
            cacheLocation="localstorage"
        >
            <AuthContextWrapper>{children}</AuthContextWrapper>
        </Auth0Provider>
    );
};

const AuthContextWrapper = ({ children }: { children: React.ReactNode }) => {
    const {
        isAuthenticated,
        isLoading,
        user,
        loginWithRedirect,
        logout: auth0Logout,
        getAccessTokenSilently,
    } = useAuth0();
    const audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE;
    const [isApiReady, setIsApiReady] = useState(false);

    const login = async () => {
        await loginWithRedirect();
    };

    const logout = () => {
        auth0Logout({
            logoutParams: {
                returnTo: typeof window !== 'undefined' ? window.location.origin : ''
            }
        });
    };

    const getAccessToken = async (): Promise<string | null> => {
        try {
            const token = await getAccessTokenSilently();
            return token;
        } catch (error) {
            console.error('[AuthContext] Error getting access token', error);
            return null;
        }
    };

    useEffect(() => {
        // Provide the implementation for the global resolver defined in api-client.ts
        if (typeof window !== 'undefined') {
            (window as any)._resolveToken = async () => {
                if (!isAuthenticated) return '';

                try {
                    return await getAccessTokenSilently({
                        authorizationParams: {
                            audience: audience,
                            scope: 'openid profile email'
                        }
                    });
                } catch (err) {
                    console.error('[AuthContext] Global resolver failed', err);
                    return '';
                }
            };
        }

        if (isAuthenticated) {
            console.log('[AuthContext] API Ready (Global resolver assigned)');
            setIsApiReady(true);
        } else {
            setIsApiReady(false);
            wsClient.setToken(null);
        }
    }, [isAuthenticated, getAccessTokenSilently, audience]);

    if (isLoading || (isAuthenticated && !isApiReady)) {
        return (
            <div className="flex h-screen w-full items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            </div>
        );
    }

    return (
        <AuthContext.Provider
            value={{
                isAuthenticated,
                isLoading,
                isApiReady,
                user,
                login,
                logout,
                getAccessToken,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};
