# Handover Context

## 1. Primary Objective
Resolve API Authentication (401 errors) and WebSocket connectivity issues.

## 2. Completed Work
- **High-Performance Caching & ETF Expansion**:
  - Implemented `AsyncCacheLayer` in `backend/core/cache_layer.py` using Redis.
  - Updated `TradingService.get_markets` with dynamic instrument discovery and 30s TTL caching.
  - Created `market_sync_task.py` for continuous background price updates.
  - Expanded ETF visibility by enabling dynamic discovery from Revolut X.
- **Authentication Unification & Race Condition Fix**:
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

## Fase 4: Performance & Instrumentatie [VOLTOOID]
De applicatie is nu geoptimaliseerd voor snelheid en bereik.
- **Extreme Performance**: Marktprijzen worden nu binnen enkele milliseconden geserveerd vanuit een Redis cache.
- **ETF Expansie**: De lijst met markten is niet langer beperkt tot crypto, maar haalt nu dynamisch alle beschikbare instrumenten (inclusief ETF's) op van de exchange adapters.
- **Achtergrond Sync**: Een dedicated script zorgt ervoor dat prijzen in de cache actueel blijven zonder dat de gebruiker hoeft te wachten op API-responses.

3. **Production Hardening**: Ensure all diagnostic logs are removed and the `isApiReady` pattern is used for all authenticated entry points.

## 6. Reflections
- **Race Conditions**: Deterministic API initialization is critical in SPA applications. The `isApiReady` guard successfully solved the 401 errors caused by requests being fired before Auth0 was fully bootstrapped.
- **Git Visibility**: Inconsistent `.gitignore` rules (like a generic `lib/` exclude) can hide critical source files. Always verify that source directories are correctly tracked after a major refactor.
- **Global Handlers**: For complex auth flows involving Auth0, delegating the token resolver to a global `window` object (with proper typescript-ignores) proved to be an effective bridge between the generated code and the React context.
