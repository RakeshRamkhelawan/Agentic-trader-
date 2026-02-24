# WebSocket Implementation Guide

> Real-time data streaming for Agentic Trader Platform

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Integration](#frontend-integration)
5. [Message Protocol](#message-protocol)
6. [Channels](#channels)
7. [Security](#security)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Agentic Trader Platform uses WebSockets for real-time data streaming:

| Feature | Channel | Frequency |
|---------|---------|-----------|
| Orderbook updates | `orderbook.{symbol}` | Real-time |
| Ticker prices | `ticker.{symbol}` | ~1 second |
| Order updates | `orders.{account_id}` | Event-driven |
| Navagraha state | `navagraha.updates` | ~1 minute |
| OODA cycles | `ooda.updates` | Event-driven |

### WebSocket URL

```javascript
// Development
ws://localhost:8000/ws

// Production (HTTPS)
wss://api.yourdomain.com/ws
```

---

## Architecture

```
┌─────────────────┐      WebSocket       ┌──────────────────┐
│  React Frontend │  ◄──────────────────► │  FastAPI Backend │
│  (useWebSocket) │      WSS/TLS 1.3     │  (WebSocketManager)│
└─────────────────┘                        └──────────────────┘
                                                     │
                       ┌─────────────────────────────┼─────────────────────────────┐
                       │                             │                             │
                       ▼                             ▼                             ▼
              ┌─────────────────┐         ┌──────────────────┐         ┌──────────────────┐
              │ Bitvavo/Revolut │         │   VedAstro       │         │  Order Manager   │
              │ Market Data     │         │   Calculations   │         │  Updates         │
              └─────────────────┘         └──────────────────┘         └──────────────────┘
```

---

## Backend Implementation

### File Structure

```
backend/
├── api/
│   ├── websocket_endpoints.py      # FastAPI routes
│   ├── websocket_manager.py        # Connection management
│   └── websocket_manager_v2.py     # Enhanced version (optional)
└── core/
    └── market_data/
        └── websocket_manager.py    # Market data specific
```

### WebSocket Manager (`websocket_manager.py`)

```python
"""
WebSocket Manager for real-time trading data.

Key features:
- Multi-tenant isolation (tenant_id + account_id)
- Channel-based subscriptions
- Automatic heartbeat/ping-pong
- Thread-safe connection handling
"""

from backend.api.websocket_manager import WebSocketManager

# Global singleton
ws_manager = WebSocketManager()

# Broadcast orderbook update
await ws_manager.broadcast_orderbook(
    symbol="BTC-EUR",
    bids=[["42000.50", "0.5"], ["41900.00", "1.2"]],
    asks=[["42100.00", "0.3"], ["42200.00", "0.8"]],
    is_snapshot=True
)

# Broadcast ticker
await ws_manager.broadcast_ticker(
    symbol="BTC-EUR",
    bid=42000.50,
    ask=42100.00,
    last=42050.00,
    volume_24h=1500.5,
    change_24h=500.00,
    change_percent_24h=1.2,
    high_24h=43000.00,
    low_24h=41000.00
)

# Broadcast order update to specific user
await ws_manager.broadcast_order_update(
    account_id="user-123",
    order_data={
        "order_id": "ord-456",
        "status": "filled",
        "filled_amount": "0.5",
        "price": "42000.50"
    }
)
```

### FastAPI Endpoints (`websocket_endpoints.py`)

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.api.websocket_manager import ws_manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None)  # JWT token from query param
):
    """
    Main WebSocket endpoint.

    Connection:
        ws://localhost:8000/ws?token=eyJhbG...

    Query Parameters:
        token: JWT access token (optional in dev mode)
    """
    connection_id = str(uuid.uuid4())

    # Validate token (production)
    if token:
        payload = jwt_manager.verify_token(token)
        tenant_id = payload["tenant_id"]
        account_id = payload["account_id"]
    else:
        # Demo mode
        tenant_id = "demo-tenant"
        account_id = "demo-account"

    try:
        await ws_manager.connect(websocket, connection_id, tenant_id, account_id)

        while True:
            data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=60.0
            )
            await ws_manager.handle_client_message(connection_id, data)

    except WebSocketDisconnect:
        logger.info(f"Disconnected: {connection_id}")
    except asyncio.TimeoutError:
        await ws_manager.send_message(connection_id, {"type": "ping"})
    finally:
        await ws_manager.disconnect(connection_id)
```

### Register in Main App

```python
# backend/api/main.py

from fastapi import FastAPI
from backend.api.websocket_endpoints import router as ws_router

app = FastAPI()

# Include WebSocket routes
app.include_router(ws_router)

# WebSocket available at: ws://localhost:8000/ws
```

---

## Frontend Integration

### React Hook (`useWebSocket.ts`)

```typescript
// frontend/src/hooks/useWebSocket.ts

import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: unknown;
  timestamp?: string;
}

interface UseWebSocketOptions {
  url: string;
  token?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    url,
    token,
    onMessage,
    onConnect,
    onDisconnect,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    // Build URL with token
    const wsUrl = token ? `${url}?token=${token}` : url;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      reconnectAttempts.current = 0;
      onConnect?.();
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        setLastMessage(message);
        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      onDisconnect?.();

      // Reconnect logic
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current += 1;
        console.log(`Reconnecting... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
        reconnectTimer.current = setTimeout(connect, reconnectInterval);
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [url, token, onMessage, onConnect, onDisconnect, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    ws.current?.close();
  }, []);

  const sendMessage = useCallback((message: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  const subscribe = useCallback((channel: string) => {
    sendMessage({ type: 'subscribe', channel });
  }, [sendMessage]);

  const unsubscribe = useCallback((channel: string) => {
    sendMessage({ type: 'unsubscribe', channel });
  }, [sendMessage]);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
    unsubscribe,
    connect,
    disconnect
  };
}
```

### Usage Example

```tsx
// frontend/src/components/TradingDashboard.tsx

import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuth } from '@/hooks/useAuth';
import { useState, useEffect } from 'react';

interface TickerData {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  change_percent_24h: number;
}

export function TradingDashboard() {
  const { accessToken } = useAuth();
  const [ticker, setTicker] = useState<TickerData | null>(null);
  const [orderbook, setOrderbook] = useState<{ bids: any[]; asks: any[] } | null>(null);

  const { isConnected, subscribe, unsubscribe } = useWebSocket({
    url: import.meta.env.VITE_WS_URL || 'wss://api.yourdomain.com/ws',
    token: accessToken,
    onConnect: () => {
      // Subscribe to channels on connect
      subscribe('ticker.BTC-EUR');
      subscribe('orderbook.BTC-EUR');
    },
    onMessage: (message) => {
      switch (message.channel) {
        case 'ticker.BTC-EUR':
          setTicker(message.data as TickerData);
          break;
        case 'orderbook.BTC-EUR':
          setOrderbook(message.data as { bids: any[]; asks: any[] });
          break;
      }
    }
  });

  return (
    <div>
      <div className="connection-status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      {ticker && (
        <div className="ticker">
          <h2>BTC/EUR</h2>
          <p>Price: €{ticker.last.toLocaleString()}</p>
          <p className={ticker.change_percent_24h >= 0 ? 'green' : 'red'}>
            {ticker.change_percent_24h >= 0 ? '▲' : '▼'}
            {Math.abs(ticker.change_percent_24h).toFixed(2)}%
          </p>
          <p>Bid: €{ticker.bid} | Ask: €{ticker.ask}</p>
        </div>
      )}

      {orderbook && (
        <div className="orderbook">
          <div className="asks">
            {orderbook.asks.slice(0, 5).map(([price, amount], i) => (
              <div key={i} className="ask">
                <span className="price">{price}</span>
                <span className="amount">{amount}</span>
              </div>
            ))}
          </div>
          <div className="bids">
            {orderbook.bids.slice(0, 5).map(([price, amount], i) => (
              <div key={i} className="bid">
                <span className="price">{price}</span>
                <span className="amount">{amount}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Message Protocol

### Client → Server

#### Subscribe to Channel
```json
{
  "type": "subscribe",
  "channel": "orderbook.BTC-EUR"
}
```

#### Unsubscribe from Channel
```json
{
  "type": "unsubscribe",
  "channel": "orderbook.BTC-EUR"
}
```

#### Ping (Keep-Alive)
```json
{
  "type": "ping"
}
```

### Server → Client

#### Connection Established
```json
{
  "type": "connected",
  "connection_id": "uuid-v4-string",
  "timestamp": "2026-02-22T20:30:00.000Z"
}
```

#### Pong (Ping Response)
```json
{
  "type": "pong"
}
```

#### Ticker Update
```json
{
  "channel": "ticker.BTC-EUR",
  "type": "update",
  "data": {
    "symbol": "BTC-EUR",
    "bid": 42000.50,
    "ask": 42100.00,
    "last": 42050.00,
    "volume_24h": 1500.5,
    "change_24h": 500.00,
    "change_percent_24h": 1.2,
    "high_24h": 43000.00,
    "low_24h": 41000.00,
    "timestamp": "2026-02-22T20:30:00.000Z"
  },
  "timestamp": "2026-02-22T20:30:00.000Z"
}
```

#### Orderbook Snapshot
```json
{
  "channel": "orderbook.BTC-EUR",
  "type": "snapshot",
  "data": {
    "bids": [
      ["42000.50", "0.5"],
      ["41900.00", "1.2"],
      ["41800.00", "2.0"]
    ],
    "asks": [
      ["42100.00", "0.3"],
      ["42200.00", "0.8"],
      ["42300.00", "1.5"]
    ],
    "timestamp": "2026-02-22T20:30:00.000Z"
  },
  "timestamp": "2026-02-22T20:30:00.000Z"
}
```

#### Orderbook Delta
```json
{
  "channel": "orderbook.BTC-EUR",
  "type": "delta",
  "data": {
    "bids": [["42000.50", "0.7"]],
    "asks": [],
    "timestamp": "2026-02-22T20:30:01.000Z"
  },
  "timestamp": "2026-02-22T20:30:01.000Z"
}
```

#### Order Update
```json
{
  "channel": "orders.user-123",
  "type": "update",
  "data": {
    "order_id": "ord-456",
    "status": "filled",
    "side": "buy",
    "symbol": "BTC-EUR",
    "amount": "0.5",
    "filled_amount": "0.5",
    "price": "42000.50",
    "filled_at": "2026-02-22T20:30:00.000Z"
  },
  "timestamp": "2026-02-22T20:30:00.000Z"
}
```

---

## Channels

### Available Channels

| Channel | Pattern | Description |
|---------|---------|-------------|
| Ticker | `ticker.{symbol}` | Price updates for symbol |
| Orderbook | `orderbook.{symbol}` | Order book depth updates |
| Orders | `orders.{account_id}` | User order status updates |
| Navagraha | `navagraha.updates` | Consciousness state updates |
| OODA | `ooda.updates` | Decision cycle updates |

### Channel Wildcards

```typescript
// Subscribe to all tickers (not implemented yet)
subscribe('ticker.*');

// Subscribe to multiple symbols
subscribe('ticker.BTC-EUR');
subscribe('ticker.ETH-EUR');
subscribe('ticker.ADA-EUR');
```

---

## Security

### Authentication

```typescript
// Option 1: Token in query parameter
const wsUrl = `wss://api.yourdomain.com/ws?token=${accessToken}`;

// Option 2: Token in subprotocol (advanced)
const ws = new WebSocket(url, ['access_token', token]);
```

### Backend Validation

```python
# backend/api/websocket_endpoints.py

from backend.core.auth.jwt import jwt_manager

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        payload = jwt_manager.verify_token(token)
        tenant_id = payload["tenant_id"]
        account_id = payload["account_id"]
    except JWTError:
        await websocket.close(code=4002, reason="Invalid token")
        return

    # Connection authorized
    await ws_manager.connect(websocket, connection_id, tenant_id, account_id)
```

### Rate Limiting

```python
# Limit connections per IP/account
connection_limits = {
    "per_ip": 5,
    "per_account": 3
}

async def check_connection_limit(ip: str, account_id: str) -> bool:
    ip_count = sum(1 for c in ws_manager.connections.values() if c.ip == ip)
    account_count = sum(1 for c in ws_manager.connections.values() if c.account_id == account_id)

    return ip_count < connection_limits["per_ip"] and account_count < connection_limits["per_account"]
```

---

## Monitoring

### WebSocket Stats Endpoint

```bash
# Get WebSocket statistics
curl https://api.yourdomain.com/ws/stats
```

```json
{
  "total_connections": 42,
  "total_channels": 15,
  "channels": {
    "ticker.BTC-EUR": 25,
    "ticker.ETH-EUR": 18,
    "orderbook.BTC-EUR": 12,
    "orders.user-123": 1
  }
}
```

### Prometheus Metrics

```python
# backend/core/telemetry/metrics.py

from prometheus_client import Counter, Gauge, Histogram

websocket_connections = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections'
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages sent',
    ['channel', 'type']
)

websocket_message_size = Histogram(
    'websocket_message_size_bytes',
    'Size of WebSocket messages',
    ['channel']
)
```

### Grafana Dashboard

See: `infrastructure/grafana/dashboards/websocket_reliability.json`

---

## Troubleshooting

### Connection Fails

```bash
# Test WebSocket connection
wscat -c wss://api.yourdomain.com/ws

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Check WebSocket stats
curl https://api.yourdomain.com/ws/stats
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Backend not running | Start API server |
| 403 Forbidden | CORS issue | Check CORS config |
| 401 Unauthorized | Invalid token | Refresh auth token |
| Slow messages | Network latency | Use CDN/edge locations |
| Disconnections | Idle timeout | Implement ping/pong |

### Browser Console Debug

```javascript
// Enable WebSocket debugging
const ws = new WebSocket('wss://api.yourdomain.com/ws');

ws.onopen = () => console.log('🔌 Connected');
ws.onclose = (e) => console.log('❌ Closed:', e.code, e.reason);
ws.onerror = (e) => console.error('💥 Error:', e);
ws.onmessage = (e) => console.log('📨 Message:', JSON.parse(e.data));
```

---

## Quick Reference

### cURL Testing

```bash
# Using websocat
websocat wss://api.yourdomain.com/ws

# Send subscribe message
{"type": "subscribe", "channel": "ticker.BTC-EUR"}
```

### Python Client

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "wss://api.yourdomain.com/ws"
    async with websockets.connect(uri) as ws:
        # Subscribe
        await ws.send(json.dumps({
            "type": "subscribe",
            "channel": "ticker.BTC-EUR"
        }))

        # Listen for messages
        while True:
            message = await ws.recv()
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(test_websocket())
```

---

## Summary

| Component | Implementation |
|-----------|----------------|
| Backend | FastAPI + `websocket_manager.py` |
| Frontend | React Hook `useWebSocket.ts` |
| Auth | JWT token in query param |
| Protocol | JSON over WebSocket |
| Transport | WSS (TLS 1.3) |
| Reconnection | Auto-reconnect with backoff |
