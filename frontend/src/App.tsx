import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';
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

// Auth0 Configuration
const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN || 'agentictrader.eu.auth0.com',
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || 'aO41wQ7VRzDoHavsdxamJpuSCa47wUJ8',
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE || 'https://api.agentic-trader.com',
  },
};

// Restore session on first load
function AppInitializer() {
  const { fetchCurrentUser, isAuthenticated } = useAuthStore();
  const { initializeData } = useAppStore();
  const { isAuthenticated: isAuth0Authenticated, getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    const init = async () => {
      // Check for Auth0 token
      if (isAuth0Authenticated) {
        try {
          const token = await getAccessTokenSilently();
          localStorage.setItem('access_token', token);
        } catch (e) {
          console.error('Failed to get Auth0 token:', e);
        }
      }
      
      const token = localStorage.getItem('access_token');
      if (token) {
        fetchCurrentUser().then((ok) => {
          if (ok) initializeData();
        });
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuth0Authenticated]);

  // When the user logs in after initial load, fetch all data
  useEffect(() => {
    if (isAuthenticated) {
      initializeData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  return null;
}

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const { isAuthenticated: isAuth0Authenticated, isLoading } = useAuth0();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-trade-blue" />
      </div>
    );
  }

  if (!isAuthenticated && !isAuth0Authenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Public Route Component (redirect if already authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const { isAuthenticated: isAuth0Authenticated } = useAuth0();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  if (isAuthenticated || isAuth0Authenticated) {
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
    </BrowserRouter>
  );
}

function App() {
  return (
    <Auth0Provider {...auth0Config}>
      <AppRoutes />
    </Auth0Provider>
  );
}

export default App;
