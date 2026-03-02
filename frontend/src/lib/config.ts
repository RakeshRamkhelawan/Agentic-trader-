/**
 * Runtime Configuration
 * 
 * This module handles both Docker runtime config (via window.RUNTIME_CONFIG)
 * and build-time environment variables (via import.meta.env)
 */

// Get runtime config injected by Docker entrypoint script
const runtimeConfig = (typeof window !== 'undefined' && (window as any).RUNTIME_CONFIG) || {};

// Debug logging (only in development)
if (import.meta.env.DEV || runtimeConfig.VITE_API_URL) {
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
export const API_URL = getConfig('VITE_API_URL', 'http://localhost:8001');
export const WS_URL = getConfig('VITE_WS_URL', 'ws://localhost:8001/ws/public');

// Auth0 Configuration
export const AUTH0_DOMAIN = getConfig('VITE_AUTH0_DOMAIN', '');
export const AUTH0_CLIENT_ID = getConfig('VITE_AUTH0_CLIENT_ID', '');
export const AUTH0_AUDIENCE = getConfig('VITE_AUTH0_AUDIENCE', '');

// Feature flags
export const isDevMode = !AUTH0_DOMAIN;
export const isAuthDisabled = isDevMode;

// Demo Mode - When true, shows demo/sample data instead of empty states
export const isDemoMode = getConfig('VITE_DEMO_MODE', 'false') === 'true';

// Log configuration on load
console.log('[Config] API_URL:', API_URL);
console.log('[Config] WS_URL:', WS_URL);
console.log('[Config] Auth0 Domain:', AUTH0_DOMAIN || '(not set - dev mode)');
console.log('[Config] Demo Mode:', isDemoMode ? 'ENABLED' : 'DISABLED');
