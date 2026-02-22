# WebSocket 403 Fix

> Documentation of the WebSocket connection issues and their resolution

## Problem

WebSocket connections were returning **403 Forbidden** errors when attempting to connect from the frontend.

## Root Causes

1. **CORS Middleware**: FastAPI's CORS middleware doesn't handle WebSocket upgrade requests properly
2. **Auth Token Validation**: The WebSocket endpoint required a token query parameter that wasn't being passed correctly
3. **No Public Endpoint**: There was no unauthenticated endpoint for development/testing

## Solution

### 1. Added Public WebSocket Endpoint

Created `/ws/public` endpoint that doesn't require authentication:

```python
@router.websocket("/ws/public")
async def websocket_public_endpoint(websocket: WebSocket):
    """Public WebSocket endpoint (no auth required)."""
    await handle_websocket_connection(websocket, token=None)
```

### 2. Improved Error Handling

Refactored connection handling into a separate function for better error handling and logging:

```python
async def handle_websocket_connection(websocket: WebSocket, token: Optional[str] = None):
    """Handle WebSocket connection lifecycle."""
    # ... connection logic with proper error handling
```

### 3. Updated Frontend

Changed frontend to use the public endpoint for development:

```typescript
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/public';
```

### 4. Added Logging Middleware

Added middleware to log WebSocket upgrade requests:

```python
@app.middleware("http")
async def websocket_logging_middleware(request, call_next):
    if request.headers.get("upgrade") == "websocket":
        logger.info(f"WebSocket upgrade request from: {request.client}")
    # ...
```

## Configuration

### Environment Variables

```bash
# For development (no auth)
VITE_WS_URL=ws://localhost:8000/ws/public

# For production (with auth)
VITE_WS_URL=wss://api.yourdomain.com/ws
```

### Testing

```bash
# Install websockets
pip install websockets

# Test public endpoint
python scripts/websocket_test.py --public

# Test authenticated endpoint (if you have a token)
python scripts/websocket_test.py --url ws://localhost:8000/ws --token YOUR_TOKEN
```

## Available Endpoints

| Endpoint | Auth | Use Case |
|----------|------|----------|
| `/ws` | Required | Production with JWT |
| `/ws/public` | Not required | Development/testing |
| `/ws/stats` | Not required | Connection statistics |

## Frontend Usage

### Using the Context (Recommended)

```typescript
import { useChannel } from '@/context';

// Auto-subscribes and manages connection
const { isConnected } = useChannel('ticker.BTC-EUR', (message) => {
  console.log(message.data);
});
```

### Using WebSocket Directly

```typescript
const ws = new WebSocket('ws://localhost:8000/ws/public');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'ticker.BTC-EUR'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## Channels

Available WebSocket channels:

- `ticker.{symbol}` - Price updates (e.g., `ticker.BTC-EUR`)
- `orderbook.{symbol}` - Orderbook depth updates
- `orders.{account_id}` - User order updates
- `navagraha.updates` - Consciousness state updates
- `ooda.updates` - OODA cycle updates

## Troubleshooting

### 403 Forbidden

**Cause**: Auth token missing or invalid
**Fix**: Use `/ws/public` endpoint for development

### Connection Refused

**Cause**: Backend not running
**Fix**: Start backend: `uvicorn backend.api.main:app --reload`

### Timeout

**Cause**: No messages received within timeout period
**Fix**: This is normal if no data is being broadcast

## Production Deployment

For production:

1. Use authenticated endpoint `/ws`
2. Implement proper JWT validation
3. Use WSS (WebSocket Secure) over HTTPS
4. Configure CORS properly:

```python
allow_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com",
]
```

## References

- [FastAPI WebSocket Docs](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
