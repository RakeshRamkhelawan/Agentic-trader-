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

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { useAuth0, User as Auth0User } from '@auth0/auth0-react';

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  tenantId?: string;
  accountId?: string;
  roles: string[];
}

interface AuthContextType {
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
              audience: import.meta.env.VITE_AUTH0_AUDIENCE,
              scope: 'openid profile email',
            },
          });
          setAccessToken(token);
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
        audience: import.meta.env.VITE_AUTH0_AUDIENCE,
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

/**
 * Hook to access authentication state and methods.
 * Must be used within an AuthProvider.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
