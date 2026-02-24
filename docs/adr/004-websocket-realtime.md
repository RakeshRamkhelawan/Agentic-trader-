# ADR 004: WebSocket for Real-Time Data

## Status
Accepted

## Context

Trading platforms require real-time updates for:
- Price changes (ticker data)
- Order book depth updates
- Order status changes
- Portfolio value updates

HTTP polling introduces latency and unnecessary load.

## Decision

We will use **WebSocket connections** for all real-time data streaming.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      BROWSER CLIENT                          │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Price      │  │  Orderbook  │  │  Order Status       │  │
│  │  Display    │  │  Visualizer │  │  Notifications      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │                                   │
│  ┌───────────────────────┴───────────────────────────────┐   │
│  │         useWebSocket Hook (React)                     │   │
│  │  - Auto-reconnect                                     │   │
│  │  - Channel subscription                               │   │
│  │  - Message routing                                    │   │
│  └───────────────────────┬───────────────────────────────┘   │
└──────────────────────────┼───────────────────────────────────┘
                           │ WSS (WebSocket Secure)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                      API GATEWAY                             │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐   │
│  │         WebSocketManager                              │   │
│  │  - Connection management                              │   │
│  │  - Channel subscriptions                              │   │
│  │  - Message broadcasting                               │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Bitvavo    │  │  Order      │  │  Market Data        │  │
│  │  WebSocket  │  │  Service    │  │  Service            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Channel Design

```typescript
// Available channels
interface Channels {
  // Price updates
  'ticker.{symbol}': {
    symbol: string;
    bid: number;
    ask: number;
    last: number;
    change_24h: number;
  };

  // Order book depth
  'orderbook.{symbol}': {
    bids: [string, string][];  // [price, amount]
    asks: [string, string][];
  };

  // User-specific orders
  'orders.{account_id}': {
    order_id: string;
    status: 'pending' | 'filled' | 'cancelled';
    filled_amount: string;
  };
}

// Subscribe to channel
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'ticker.BTC-EUR'
}));
```

### Implementation

```python
# backend/api/websocket_manager.py
class WebSocketManager:
    async def connect(self, ws: WebSocket, tenant_id: str, account_id: str):
        await ws.accept()
        # Store connection with tenant context

    async def subscribe(self, connection_id: str, channel: str):
        # Enforce tenant isolation
        if channel == "orders":
            channel = f"orders.{self.connections[connection_id].account_id}"
        # Add to channel subscribers

    async def broadcast_to_channel(self, channel: str, message: dict):
        # Send to all subscribers
        for conn_id in self.channels[channel]:
            await self.connections[conn_id].send_json(message)
```

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| **WebSocket (Chosen)** | True real-time, bidirectional, low latency | Connection management complexity |
| Server-Sent Events (SSE) | Simple, HTTP-based | Unidirectional only |
| HTTP Polling | Simple, works everywhere | High latency, wasted resources |
| MQTT | IoT optimized, pub/sub | Additional protocol, broker needed |

## Consequences

### Positive
- **True real-time**: Sub-second updates
- **Efficient**: Single connection for many updates
- **Bidirectional**: Client can send and receive
- **Standard**: Native browser support

### Negative
- **Complexity**: Connection state management
- **Scaling**: Sticky sessions or shared state needed
- **Debugging**: Harder to inspect than HTTP
- **Proxies**: Some corporate proxies block WebSocket

### Scaling Strategy

For horizontal scaling:
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Load Balancer │──▶│   Server    │
│             │     │  (Sticky Session) │   │   (WS)      │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────┴──────┐
                                        │    Redis    │
                                        │  Pub/Sub    │
                                        └──────┬──────┘
                                               │
                                        ┌──────┴──────┐
                                        │   Server    │
                                        │   (WS)      │
                                        └─────────────┘
```

## Security

- WSS (WebSocket Secure) in production
- JWT token validation on connect
- Channel-level access control (tenant isolation)
- Rate limiting per connection

## Related Decisions
- ADR 003: Python Asyncio
- ADR 006: Redis for Pub/Sub

## References
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
