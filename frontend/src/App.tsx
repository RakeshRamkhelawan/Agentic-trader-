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
import LivePaperTradingPage from '@/pages/LivePaperTrading';
import { Login } from '@/pages/auth/Login';
import { Register } from '@/pages/auth/Register';
import { KYC } from '@/pages/auth/KYC';
import { Toaster } from '@/components/ui/sonner';

// Validate required environment variables
const requiredEnvVars = [
  'VITE_AUTH0_DOMAIN',
  'VITE_AUTH0_CLIENT_ID',
  'VITE_AUTH0_AUDIENCE',
  'VITE_API_URL',
];

const missingEnvVars = requiredEnvVars.filter(
  (key) => !import.meta.env[key]
);

if (missingEnvVars.length > 0) {
  console.error(
    '[CRITICAL] Missing required environment variables:\n' +
      missingEnvVars.map((v) => `  - ${v}`).join('\n') +
      '\n\nPlease copy .env.example to .env and fill in your values.'
  );
}

// Auth0 Configuration - NO fallback values for security
const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN || '',
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || '',
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE || '',
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
  const from = (location.state as any)?.from?.pathname || '/dashboard';

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
            <Route path="/paper-trading" element={<LivePaperTradingPage />} />
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
  // Show error if env vars are missing
  if (missingEnvVars.length > 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black text-white p-8">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-bold text-red-500 mb-4">Configuration Error</h1>
          <p className="mb-4">
            Missing required environment variables. Please copy <code>.env.example</code> to{' '}
            <code>.env</code> and fill in your values.
          </p>
          <ul className="list-disc list-inside bg-red-950/30 p-4 rounded border border-red-500/30">
            {missingEnvVars.map((v) => (
              <li key={v} className="font-mono text-red-300">
                {v}
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  return (
    <Auth0Provider {...auth0Config}>
      <AppRoutes />
    </Auth0Provider>
  );
}

export default App;
