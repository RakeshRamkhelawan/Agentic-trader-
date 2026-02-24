/**
 * Auth Context
 *
 * Unified authentication using Auth0 as the single source of truth.
 * Replaces the dual-auth pattern (Auth0 + custom store) with a single,
 * consistent authentication flow.
 *
 * Features:
 * - Auth0 as primary authentication provider
 * - JWT token management (memory-only, no localStorage)
 * - User profile caching
 * - Authentication state synchronization
 */

/* eslint-disable react-refresh/only-export-components, react-hooks/set-state-in-effect */

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { setApiToken } from '@/lib/api';
import { AUTH0_DOMAIN, AUTH0_AUDIENCE } from '@/lib/config';

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  tenantId?: string;
  accountId?: string;
  roles: string[];
}

export interface AuthContextType {
  /** Whether user is authenticated */
  isAuthenticated: boolean;
  /** Whether auth is still loading */
  isLoading: boolean;
  /** Current user or null */
  user: User | null;
  /** JWT access token */
  accessToken: string | null;
  /** Login redirect */
  login: () => void;
  /** Logout */
  logout: () => void;
  /** Get fresh token */
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const {
    isAuthenticated: auth0IsAuthenticated,
    isLoading: auth0IsLoading,
    user: auth0User,
    getAccessTokenSilently,
    loginWithRedirect,
    logout: auth0Logout,
  } = useAuth0();

  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  // Transform Auth0 user to our User format
  useEffect(() => {
    if (auth0User && auth0IsAuthenticated) {
      const transformedUser: User = {
        id: auth0User.sub || '',
        email: auth0User.email || '',
        name: auth0User.name || auth0User.email || '',
        picture: auth0User.picture,
        tenantId: auth0User['https://agentic-trader.com/tenant_id'] as string,
        accountId: auth0User['https://agentic-trader.com/account_id'] as string,
        roles: (auth0User['https://agentic-trader.com/roles'] as string[]) || [],
      };
      setUser(transformedUser);
    } else {
      setUser(null);
    }
  }, [auth0User, auth0IsAuthenticated]);

  // Get access token when authenticated
  useEffect(() => {
    const getToken = async () => {
      if (auth0IsAuthenticated) {
        try {
          const token = await getAccessTokenSilently({
            authorizationParams: {
              audience: AUTH0_AUDIENCE,
              scope: 'openid profile email',
            },
          });
          setAccessToken(token);
          setApiToken(token); // Sync with API client
        } catch (error) {
          console.error('Failed to get access token:', error);
          setAccessToken(null);
        }
      } else {
        setAccessToken(null);
      }
    };

    getToken();
  }, [auth0IsAuthenticated, getAccessTokenSilently]);

  const login = useCallback(() => {
    loginWithRedirect({
      authorizationParams: {
        audience: AUTH0_AUDIENCE,
        scope: 'openid profile email',
      },
    });
  }, [loginWithRedirect]);

  const logout = useCallback(() => {
    auth0Logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  }, [auth0Logout]);

  const getAccessToken = useCallback(async () => {
    if (!auth0IsAuthenticated) return null;
    try {
      return await getAccessTokenSilently({
        authorizationParams: {
          audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        },
      });
    } catch (error) {
      console.error('Failed to get access token:', error);
      return null;
    }
  }, [auth0IsAuthenticated, getAccessTokenSilently]);

  const value: AuthContextType = {
    isAuthenticated: auth0IsAuthenticated,
    isLoading: auth0IsLoading,
    user,
    accessToken,
    login,
    logout,
    getAccessToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Check if we're in development mode without Auth0
const isDevMode = !AUTH0_DOMAIN;

// Dev mode fallback value
const devAuthValue: AuthContextType = {
  isAuthenticated: true,
  isLoading: false,
  user: {
    id: 'dev-user-001',
    email: 'dev@localhost',
    name: 'Developer',
    roles: ['admin'],
  },
  accessToken: 'dev-token',
  login: () => {},
  logout: () => window.location.reload(),
  getAccessToken: async () => 'dev-token',
};

/**
 * Hook to access authentication state and methods.
 * Must be used within an AuthProvider.
 * In development mode without Auth0, returns mock auth data.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    if (isDevMode) {
      return devAuthValue;
    }
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
