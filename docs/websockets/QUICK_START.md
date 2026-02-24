# WebSocket Quick Start

> Get real-time data streaming in 5 minutes

---

## 1. Backend Setup (Already Done ✓)

The WebSocket endpoints are already configured in `backend/api/websocket_endpoints.py`.

### Verify it's working:

```bash
# Start the backend
uvicorn backend.api.main:app --reload --port 8000

# Test WebSocket connection
websocat ws://localhost:8000/ws

# Send test message
{"type": "subscribe", "channel": "ticker.BTC-EUR"}
```

---

## 2. Frontend Integration

### Step 1: Create the Hook

```bash
# File already exists
frontend/src/hooks/useWebSocket.ts
```

### Step 2: Use in Your Component

```tsx
// frontend/src/components/LivePrice.tsx
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuth } from '@/hooks/useAuth';

export function LivePrice() {
  const { accessToken } = useAuth();
  const [price, setPrice] = useState(null);

  const { isConnected } = useWebSocket({
    url: import.meta.env.VITE_WS_URL,
    token: accessToken,
    onConnect: () => console.log('Connected!'),
    onMessage: (msg) => {
      if (msg.channel === 'ticker.BTC-EUR') {
        setPrice(msg.data.last);
      }
    }
  });

  return (
    <div>
      <span>{isConnected ? '🟢' : '🔴'}</span>
      <span>€{price || '---'}</span>
    </div>
  );
}
```

### Step 3: Environment Variables

```bash
# frontend/.env
VITE_WS_URL=wss://api.yourdomain.com/ws

# For local development
VITE_WS_URL=ws://localhost:8000/ws
```

---

## 3. Available Channels

Subscribe to channels after connection:

```typescript
const { subscribe } = useWebSocket({
  url: VITE_WS_URL,
  onConnect: () => {
    subscribe('ticker.BTC-EUR');      // Price updates
    subscribe('orderbook.BTC-EUR');   // Orderbook depth
    subscribe('orders.{account_id}'); // Your orders
  }
});
```

---

## 4. Testing

### Browser Console

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws');

// Listen
ws.onmessage = (e) => console.log(JSON.parse(e.data));

// Subscribe
ws.send(JSON.stringify({type: 'subscribe', channel: 'ticker.BTC-EUR'}));
```

### Command Line

```bash
# Install websocat
cargo install websocat

# Connect
websocat ws://localhost:8000/ws

# Send messages (type and press Enter)
{"type": "subscribe", "channel": "ticker.BTC-EUR"}
```

---

## 5. Production Checklist

- [ ] Use `wss://` (secure WebSocket) in production
- [ ] Implement JWT token authentication
- [ ] Add reconnection logic (handled by hook)
- [ ] Configure nginx proxy for WebSocket
- [ ] Monitor connection stats at `/ws/stats`

---

## Common Patterns

### Pattern 1: Live Price Ticker

```tsx
function PriceTicker({ symbol }) {
  const [price, setPrice] = useState(null);

  const { subscribe, unsubscribe } = useWebSocket({
    url: WS_URL,
    onConnect: () => subscribe(`ticker.${symbol}`),
    onMessage: (msg) => {
      if (msg.channel === `ticker.${symbol}`) {
        setPrice(msg.data.last);
      }
    }
  });

  return <span>€{price?.toLocaleString()}</span>;
}
```

### Pattern 2: Order Updates

```tsx
function OrderMonitor() {
  const [orders, setOrders] = useState([]);
  const { accountId } = useAuth();

  useWebSocket({
    url: WS_URL,
    token: accessToken,
    onConnect: () => subscribe(`orders.${accountId}`),
    onMessage: (msg) => {
      if (msg.channel === `orders.${accountId}`) {
        // Update order in list
        setOrders(prev => prev.map(o =>
          o.id === msg.data.order_id ? { ...o, ...msg.data } : o
        ));
      }
    }
  });

  return <OrderList orders={orders} />;
}
```

### Pattern 3: Multiple Symbols

```tsx
function MultiSymbolMonitor({ symbols }) {
  const [prices, setPrices] = useState({});

  const { subscribe } = useWebSocket({
    url: WS_URL,
    onConnect: () => {
      symbols.forEach(s => subscribe(`ticker.${s}`));
    },
    onMessage: (msg) => {
      if (msg.channel?.startsWith('ticker.')) {
        const symbol = msg.channel.replace('ticker.', '');
        setPrices(prev => ({ ...prev, [symbol]: msg.data }));
      }
    }
  });

  return (
    <div>
      {symbols.map(s => (
        <div key={s}>{s}: €{prices[s]?.last}</div>
      ))}
    </div>
  );
}
```

---

## Troubleshooting

### "WebSocket connection failed"
- Check if backend is running: `curl http://localhost:8000/health`
- Verify URL: `ws://` for HTTP, `wss://` for HTTPS

### "Disconnected immediately"
- Check JWT token is valid
- Verify token is passed correctly

### "No messages received"
- Subscribe to a channel after connecting
- Check channel name is correct (case-sensitive)

---

That's it! You now have real-time data streaming. 🚀
