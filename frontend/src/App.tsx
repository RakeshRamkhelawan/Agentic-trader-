import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Auth0Provider } from '@auth0/auth0-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import { AuthProvider, useAuth, WebSocketProvider } from '@/context';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/Header';
import { Dashboard } from '@/pages/Dashboard';
import { Markets } from '@/pages/Markets';
import { Portfolio } from '@/pages/Portfolio';
import { Terminal } from '@/pages/Terminal';
import { History } from '@/pages/History';
import { Settings } from '@/pages/Settings';
import PaperTradingPage from '@/pages/paper-trading';
import { Login } from '@/pages/auth/Login';
import { Register } from '@/pages/auth/Register';
import { KYC } from '@/pages/auth/KYC';
import { Toaster } from '@/components/ui/sonner';
import { API_URL, AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_AUDIENCE, isDevMode } from '@/lib/config';



// Validate required configuration
if (!API_URL) {
  console.error(
    '[CRITICAL] Missing required configuration: API_URL\n' +
    'Please set VITE_API_URL environment variable.'
  );
}

if (isDevMode) {
  console.warn(
    '[DEVELOPMENT MODE] Running in Vite dev server without Auth0.\n' +
    'Authentication is bypassed for local development.\n' +
    'This mode is impossible in production builds (guard in config.ts).'
  );
}

// Auth0 Configuration - only if all vars present
const auth0Config = isDevMode
  ? null
  : {
    domain: AUTH0_DOMAIN,
    clientId: AUTH0_CLIENT_ID,
    authorizationParams: {
      redirect_uri: window.location.origin,
      audience: AUTH0_AUDIENCE,
    },
  };

// Initialize app data when user authenticates
function AppInitializer() {
  const { isAuthenticated, user } = useAuth();
  const { initializeData } = useAppStore();

  useEffect(() => {
    if (isAuthenticated && user) {
      initializeData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user]);

  return null;
}

// Protected Route Component - uses unified auth context
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-trade-blue" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Public Route Component (redirect if already authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  interface LocationState {
    from?: {
      pathname?: string;
    };
  }
  const from = (location.state as LocationState)?.from?.pathname || '/dashboard';

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}

// Main Layout Component
function MainLayout() {
  const { sidebarExpanded } = useAppStore();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      <div
        className={cn(
          'transition-all duration-300',
          sidebarExpanded ? 'ml-60' : 'ml-[72px]'
        )}
      >
        <Header />

        <main className="pt-16 min-h-screen">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/markets" element={<Markets />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/terminal" element={<Terminal />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/paper-trading" element={<PaperTradingPage />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>

      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#111111',
            border: '1px solid #262626',
            color: '#FFFFFF',
          },
        }}
      />
    </div>
  );
}

function AppRoutes() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WebSocketProvider>
          <AppInitializer />
          <Routes>
            {/* Public Routes */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/register"
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              }
            />

            {/* KYC Route */}
            <Route
              path="/kyc"
              element={
                <ProtectedRoute>
                  <KYC />
                </ProtectedRoute>
              }
            />

            {/* Protected Routes with Layout */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            />
          </Routes>
        </WebSocketProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}



function App() {
  // Show error if API URL is missing
  if (!API_URL) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black text-white p-8">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-bold text-red-500 mb-4">Configuration Error</h1>
          <p className="mb-4">
            Missing required configuration. Please set <code>VITE_API_URL</code> environment variable.
          </p>
        </div>
      </div>
    );
  }

  // Development mode without Auth0
  if (isDevMode) {
    return (
      <div className="min-h-screen bg-black">
        <div className="fixed top-0 left-0 right-0 bg-yellow-500/20 border-b border-yellow-500/50 text-yellow-400 text-xs px-4 py-1 text-center z-50">
          Development Mode - Authentication Disabled
        </div>
        <div className="pt-6">
          <BrowserRouter>
            <AppRoutesInternal />
          </BrowserRouter>
        </div>
      </div>
    );
  }

  // Production mode with Auth0
  return (
    <Auth0Provider {...auth0Config!}>
      <AppRoutes />
    </Auth0Provider>
  );
}

// Internal routes for dev mode (no AuthProvider needed, useAuth handles it)
function AppRoutesInternal() {
  return (
    <WebSocketProvider>
      <Routes>
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/*"
          element={
            <div className="min-h-screen bg-background">
              <Sidebar />
              <div className="transition-all duration-300 ml-60">
                <div className="flex items-center justify-end px-4 py-2 border-b border-border bg-card/50">
                  <span className="text-sm text-muted-foreground mr-4">
                    Dev User
                  </span>
                </div>
                <main className="pt-4 min-h-screen">
                  <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/markets" element={<Markets />} />
                    <Route path="/portfolio" element={<Portfolio />} />
                    <Route path="/terminal" element={<Terminal />} />
                    <Route path="/history" element={<History />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/paper-trading" element={<PaperTradingPage />} />
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </main>
              </div>
              <Toaster
                position="bottom-right"
                toastOptions={{
                  style: {
                    background: '#111111',
                    border: '1px solid #262626',
                    color: '#FFFFFF',
                  },
                }}
              />
            </div>
          }
        />
      </Routes>
    </WebSocketProvider>
  );
}

export default App;
