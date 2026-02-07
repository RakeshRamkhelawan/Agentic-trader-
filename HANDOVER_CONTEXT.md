# Handover Context

## 1. Primary Objective
Resolve API Authentication (401 errors) and WebSocket connectivity issues.

## 2. Completed Work
- **Authentication Unification**:
  - Replaced legacy `localStorage` token logic with a dynamic Auth0 token resolver in `OpenAPI`.
  - Integrated `wsClient.setToken()` into `AuthContext` to sync WebSocket authentication.
- **WebSocket Connectivity**:
  - Corrected `websocket-client.ts` to use `NEXT_PUBLIC_API_URL` (port 8000) instead of the hardcoded port 3000 origin.
  - Added support for passing JWT tokens via query parameters on WebSocket connections.
- **CORS & Backend**:
  - Updated `backend/api/main.py` to allow origins `http://localhost:3000` and `http://127.0.0.1:3000`.
  - Verified backend endpoints like `/portfolio` now respond correctly with the Bearer token.

## 3. Key Files
- `frontend/src/context/auth-context.tsx` (Auth & token coordination)
- `frontend/src/lib/api/websocket-client.ts` (WebSocket logic)
- `frontend/src/lib/api-client.ts` (API configuration)
- `backend/api/main.py` (CORS and middleware setup)

## 4. Current State
- **Build Status**: ✅ PASSING (`npm run build`)
- **API Status**: ✅ WORKING (authenticated requests to `/portfolio`)
- **WebSocket Status**: ✅ CONNECTED (connecting to `ws://localhost:8000/ws`)
- **Known Issues**:
  - WebSocket currently uses a "demo-tenant" fallback in the backend handler (Task for future tenant-aware WS logic).

## 5. Next Steps
1. **Verification**: Confirm real-time market data updates on the dashboard.
2. **Tenant Mapping**: Update WebSocket backend to extract `tenant_id` from the JWT token.
