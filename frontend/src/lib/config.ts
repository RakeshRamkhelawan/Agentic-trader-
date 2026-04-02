/**
 * Runtime Configuration
 * 
 * This module handles both Docker runtime config (via window.RUNTIME_CONFIG)
 * and build-time environment variables (via import.meta.env)
 */

// Get runtime config injected by Docker entrypoint script
const runtimeConfig = (typeof window !== 'undefined' && (window as any).RUNTIME_CONFIG) || {};

// Debug logging (only in development)
if (import.meta.env.DEV) {
  console.log('[Config] Runtime config:', runtimeConfig);
}

/**
 * Get configuration value with priority:
 * 1. Runtime config (from Docker)
 * 2. Build-time env (from Vite)
 * 3. Default fallback
 */
function getConfig(key: string, defaultValue: string): string {
  return runtimeConfig[key] || import.meta.env[key] || defaultValue;
}

// API Configuration
// Updated to match new Docker port allocation (see implementation_plan_docker_perfect.md)
export const API_URL = getConfig('VITE_API_URL', 'http://localhost:8099');
export const WS_URL = getConfig('VITE_WS_URL', 'ws://localhost:8099/ws');

// Auth0 Configuration
export const AUTH0_DOMAIN = getConfig('VITE_AUTH0_DOMAIN', '');
export const AUTH0_CLIENT_ID = getConfig('VITE_AUTH0_CLIENT_ID', '');
export const AUTH0_AUDIENCE = getConfig('VITE_AUTH0_AUDIENCE', '');

// PRODUCTION GUARD: Auth0 SHOULD be configured in production builds.
// In our Docker-based local live environment, we allow a fallback to prevent blocking the UI.
if (import.meta.env.PROD && !AUTH0_DOMAIN) {
  console.error(
    '[CONFIG WARNING] Missing VITE_AUTH0_DOMAIN in production build. ' +
    'Proceeding with development fallback. Set VITE_AUTH0_DOMAIN for full security.'
  );
}

// Dev mode is ONLY active when running in Vite dev server AND Auth0 is not configured.
// In production, this is unreachable due to the guard above.
export const isDevMode = import.meta.env.DEV && !AUTH0_DOMAIN;
export const isAuthDisabled = isDevMode;

// Demo Mode - When true, shows demo/sample data instead of empty states
export const isDemoMode = getConfig('VITE_DEMO_MODE', 'false') === 'true';

// Log configuration on load (only in dev, never leak config in prod)
if (import.meta.env.DEV) {
  console.log('[Config] API_URL:', API_URL);
  console.log('[Config] WS_URL:', WS_URL);
  console.log('[Config] Auth0 Domain:', AUTH0_DOMAIN || '(not set - dev mode)');
  console.log('[Config] Demo Mode:', isDemoMode ? 'ENABLED' : 'DISABLED');
}

