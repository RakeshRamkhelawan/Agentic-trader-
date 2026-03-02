# Frontend-Backend Integration TDD Plan

## Overview
Full integration of the frontend with real backend APIs - no mocks or placeholders.

## Modules to Implement

### 1. Authentication Module
**Endpoints:**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Get current user

**Tests:**
- Happy path: Successful registration/login
- Unhappy path: Invalid credentials, duplicate email
- Integration: Token persistence, logout cleanup

### 2. KYC Module (Implemented but disabled)
**Endpoints:**
- `POST /api/v1/kyc/submit` - Submit KYC data
- `GET /api/v1/kyc/status` - Get KYC status
- `POST /api/v1/kyc/documents` - Upload documents

**Tests:**
- Happy path: KYC submission
- Unhappy path: Invalid documents
- Integration: Status flow verification

### 3. Trading Module
**Endpoints:**
- `GET /api/v1/markets/assets` - List available assets
- `GET /api/v1/markets/ticker/{symbol}` - Get price
- `GET /api/v1/markets/ohlcv/{symbol}` - Get historical data
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders` - List orders
- `DELETE /api/v1/orders/{id}` - Cancel order

**Tests:**
- Happy path: Order creation, cancellation
- Unhappy path: Insufficient funds, invalid symbol
- Integration: Order lifecycle

### 4. Portfolio Module
**Endpoints:**
- `GET /api/v1/portfolio` - Get holdings
- `GET /api/v1/portfolio/history` - Get trade history
- `GET /api/v1/portfolio/performance` - Get performance metrics

**Tests:**
- Happy path: Portfolio retrieval
- Unhappy path: Unauthorized access
- Integration: Real-time updates

### 5. WebSocket Module
**Endpoints:**
- `ws://api/v1/ws/market` - Market data stream
- `ws://api/v1/ws/orders` - Order updates stream

**Tests:**
- Happy path: Connection, data streaming
- Unhappy path: Reconnection, errors

## Implementation Order
1. API Client (Axios wrapper)
2. Auth API + Tests
3. KYC API + Tests (disabled)
4. Trading API + Tests
5. Portfolio API + Tests
6. WebSocket integration
7. Frontend store updates
8. End-to-end integration tests
