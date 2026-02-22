# WebSocket Documentation

> Real-time data streaming for Agentic Trader Platform

---

## Documentation Files

| File | Description |
|------|-------------|
| [WEBSOCKET_IMPLEMENTATION.md](./WEBSOCKET_IMPLEMENTATION.md) | Complete WebSocket implementation guide |
| [QUICK_START.md](./QUICK_START.md) | Get started in 5 minutes |

---

## Quick Links

- **Frontend Hook** → [WEBSOCKET_IMPLEMENTATION.md#frontend-integration](./WEBSOCKET_IMPLEMENTATION.md#frontend-integration)
- **Message Protocol** → [WEBSOCKET_IMPLEMENTATION.md#message-protocol](./WEBSOCKET_IMPLEMENTATION.md#message-protocol)
- **Available Channels** → [WEBSOCKET_IMPLEMENTATION.md#channels](./WEBSOCKET_IMPLEMENTATION.md#channels)
- **Security** → [WEBSOCKET_IMPLEMENTATION.md#security](./WEBSOCKET_IMPLEMENTATION.md#security)

---

## Code Examples

### React Component

```tsx
import { useWebSocket } from '@/hooks/useWebSocket';

function PriceDisplay() {
  const [price, setPrice] = useState(null);

  const { isConnected } = useWebSocket({
    url: import.meta.env.VITE_WS_URL,
    token: accessToken,
    onConnect: () => subscribe('ticker.BTC-EUR'),
    onMessage: (msg) => {
      if (msg.channel === 'ticker.BTC-EUR') {
        setPrice(msg.data.last);
      }
    }
  });

  return (
    <div>
      {isConnected ? '🟢' : '🔴'}
      €{price || '---'}
    </div>
  );
}
```

### Backend Broadcast

```python
from backend.api.websocket_manager import ws_manager

# Broadcast ticker update
await ws_manager.broadcast_ticker(
    symbol="BTC-EUR",
    bid=42000.50,
    ask=42100.00,
    last=42050.00,
    # ... other fields
)
```

---

## WebSocket URL

| Environment | URL |
|-------------|-----|
| Development | `ws://localhost:8000/ws` |
| Production | `wss://api.yourdomain.com/ws` |

---

## Available Channels

| Channel | Description | Message Type |
|---------|-------------|--------------|
| `ticker.{symbol}` | Price updates | `update` |
| `orderbook.{symbol}` | Order book depth | `snapshot`, `delta` |
| `orders.{account_id}` | User order updates | `update` |
| `navagraha.updates` | Consciousness state | `update` |
| `ooda.updates` | Decision cycles | `update` |

---

## File Structure

```
frontend/src/
├── hooks/
│   └── useWebSocket.ts           # React hook
├── components/websocket/
│   ├── LivePriceTicker.tsx       # Example component
│   └── index.ts

backend/
├── api/
│   ├── websocket_endpoints.py    # FastAPI routes
│   ├── websocket_manager.py      # Connection manager
│   └── websocket_manager_v2.py   # Enhanced version

infrastructure/
├── docker/
│   └── nginx.conf                # WebSocket proxy config
└── grafana/
    └── dashboards/
        └── websocket_reliability.json
```

---

## Testing

```bash
# Command line
websocat ws://localhost:8000/ws

# Browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({type: 'subscribe', channel: 'ticker.BTC-EUR'}));
```

---

## Related Documentation

- [SSL/HTTPS Setup](../infrastructure/HTTPS_SSL_SETUP.md)
- [Docker Deployment](../DOCKER_DEPLOYMENT.md)
