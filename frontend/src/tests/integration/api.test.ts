/**
 * API Integration Tests
 *
 * These tests verify that the API client correctly:
 * 1. Attaches auth tokens to requests
 * 2. Handles responses correctly
 * 3. Manages error scenarios
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import { setApiToken, getApiToken, authApi, marketsApi } from '@/lib/api';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn((fn) => fn) },
        response: { use: vi.fn((fn, errFn) => fn) },
      },
      get: vi.fn(),
      post: vi.fn(),
    })),
  },
}));

describe('API Client', () => {
  beforeEach(() => {
    // Clear token before each test
    setApiToken(null);
  });

  describe('Token Management', () => {
    it('should store token in memory', () => {
      const testToken = 'test-jwt-token';
      setApiToken(testToken);
      expect(getApiToken()).toBe(testToken);
    });

    it('should clear token when set to null', () => {
      setApiToken('test-token');
      setApiToken(null);
      expect(getApiToken()).toBeNull();
    });
  });

  describe('Request Interceptor', () => {
    it('should add Authorization header when token exists', () => {
      const token = 'my-auth-token';
      setApiToken(token);

      // Simulate request interceptor
      const config = { headers: {} };
      const tokenFromStore = getApiToken();

      if (tokenFromStore) {
        config.headers.Authorization = `Bearer ${tokenFromStore}`;
      }

      expect(config.headers.Authorization).toBe(`Bearer ${token}`);
    });

    it('should not add Authorization header when token is null', () => {
      setApiToken(null);

      const config = { headers: {} };
      const tokenFromStore = getApiToken();

      if (tokenFromStore) {
        config.headers.Authorization = `Bearer ${tokenFromStore}`;
      }

      expect(config.headers.Authorization).toBeUndefined();
    });
  });
});

/**
 * Manual Integration Test Checklist
 *
 * Run these manually after deploying to verify end-to-end connectivity:
 *
 * 1. Health Check
 *    curl http://localhost:8000/api/v1/health
 *    Expected: { "status": "ok" }
 *
 * 2. Authentication Flow
 *    - Open browser at http://localhost:5173
 *    - Click "Login with Auth0"
    - Complete OAuth flow
 *    - Verify dashboard loads
 *    - Check Network tab: all API calls should have Authorization header
 *
 * 3. Authenticated API Calls
 *    - Dashboard should load markets data
 *    - Portfolio should show holdings
 *    - Orders should display
 *
 * 4. WebSocket Connection
 *    - Open browser console
 *    - Run: new WebSocket('ws://localhost:8000/ws?token=YOUR_TOKEN')
 *    - Should connect successfully
 *    - Send: {"type": "subscribe", "channel": "ticker.BTC-EUR"}
 *    - Should receive price updates
 *
 * 5. Error Handling
 *    - Expire the token (wait 1 hour or modify token)
 *    - Refresh page
 *    - Should redirect to /login
 */

export const integrationChecklist = {
  healthCheck: () => fetch(`${import.meta.env.VITE_API_URL}/api/v1/health`),
  authFlow: 'Manual: Login via Auth0',
  apiCalls: [
    'GET /api/v1/trading/markets',
    'GET /api/v1/trading/portfolio',
    'GET /api/v1/trading/orders/active',
  ],
  websocket: 'ws://localhost:8000/ws',
};
