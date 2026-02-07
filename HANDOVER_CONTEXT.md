# Handover Context

## 1. Primary Objective
Resolve API Authentication (401 errors) and WebSocket connectivity issues.

## 2. Completed Work
- **Authentication Unification & Race Condition Fix**:
  - Implemented `isApiReady` in `AuthContext` to prevent early API calls.
  - Added the `isApiReady` guard to `ProtectedRoute.tsx`.
  - Created a robust global token delegator (`window._resolveToken`) in `api-client.ts` and `trading-api.ts`.
  - Unified `OpenAPI` imports to ensure singleton consistency.
  - **Kritieke Fix**: Corrigeerde de root `.gitignore` (verwijderde `lib/`) die verhinderde dat de API-client bestanden werden gecommit.
- **WebSocket Connectivity**:
  - Corrected `websocket-client.ts` port and proxy handling.
  - Synchronized WebSocket tokens with the Auth0 state changes.
- **Infrastructure**:
  - Fixed Next.js proxy port (8000) and relative base URL for headers.
  - Cleaned up diagnostic logs in both frontend and backend.

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

3. **Production Hardening**: Ensure all diagnostic logs are removed and the `isApiReady` pattern is used for all authenticated entry points.

## 6. Reflections
- **Race Conditions**: Deterministic API initialization is critical in SPA applications. The `isApiReady` guard successfully solved the 401 errors caused by requests being fired before Auth0 was fully bootstrapped.
- **Git Visibility**: Inconsistent `.gitignore` rules (like a generic `lib/` exclude) can hide critical source files. Always verify that source directories are correctly tracked after a major refactor.
- **Global Handlers**: For complex auth flows involving Auth0, delegating the token resolver to a global `window` object (with proper typescript-ignores) proved to be an effective bridge between the generated code and the React context.
