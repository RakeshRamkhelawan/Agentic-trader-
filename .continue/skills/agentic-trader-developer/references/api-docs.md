# API Documentation - Agentic Trader

API reference for the Agentic Trader platform.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.agentic-trader.com/api/v1
```

## Authentication

All endpoints (except health) require JWT authentication:

```http
Authorization: Bearer <token>
```

Get token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "my-tenant", "account_id": "my-account"}'
```

## Core Endpoints

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "18.0.0",
  "timestamp": "2026-02-26T14:00:00Z"
}
```

### Trading

#### Get Markets
```http
GET /trading/markets
Authorization: Bearer <token>
```

Response:
```json
{
  "markets": [
    {"symbol": "BTC-EUR", "price": 45000.00, "change_24h": 2.5},
    {"symbol": "ETH-EUR", "price": 3200.00, "change_24h": -1.2}
  ]
}
```

#### Place Order
```http
POST /trading/orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "symbol": "BTC-EUR",
  "side": "BUY",
  "type": "MARKET",
  "quantity": 0.1
}
```

Response:
```json
{
  "order_id": "uuid",
  "status": "submitted",
  "symbol": "BTC-EUR",
  "side": "BUY",
  "quantity": 0.1,
  "created_at": "2026-02-26T14:00:00Z"
}
```

#### Get Orders
```http
GET /trading/orders
Authorization: Bearer <token>
```

Query params:
- `status` - Filter by status (submitted, filled, cancelled)
- `symbol` - Filter by symbol
- `limit` - Max results (default: 50)

### Portfolio

#### Get Portfolio
```http
GET /trading/portfolio
Authorization: Bearer <token>
```

Response:
```json
{
  "positions": [
    {
      "symbol": "BTC-EUR",
      "quantity": 0.5,
      "avg_price": 44000.00,
      "current_price": 45000.00,
      "pnl": 500.00
    }
  ],
  "total_value": 22500.00,
  "total_pnl": 500.00
}
```

### Agents

#### Get Agent Status
```http
GET /agents/status
Authorization: Bearer <token>
```

Response:
```json
{
  "agents": [
    {
      "name": "sentiment_agent",
      "status": "active",
      "last_activity": "2026-02-26T14:00:00Z"
    }
  ]
}
```

#### Trigger Agent Analysis
```http
POST /agents/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "agent": "sentiment_agent",
  "symbol": "BTC-EUR"
}
```

### MCP Tools

#### List Tools
```http
GET /mcp/tools
Authorization: Bearer <token>
```

Response:
```json
{
  "tools": [
    {"name": "vedastro__generate_signal", "category": "vedastro"},
    {"name": "elemental__fire_position_size", "category": "elemental"},
    {"name": "execution__execute_paper_trade", "category": "execution"}
  ]
}
```

#### Call Tool
```http
POST /mcp/tools/call
Authorization: Bearer <token>
Content-Type: application/json

{
  "tool_name": "vedastro__generate_signal",
  "params": {
    "symbol": "BTC",
    "current_price": 45000
  }
}
```

Response:
```json
{
  "signal": "buy",
  "confidence": 0.75,
  "risk_level": "low"
}
```

### Backtesting

#### Run Backtest
```http
POST /backtest/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "strategy": "momentum",
  "symbol": "BTC-EUR",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "initial_capital": 10000
}
```

Response:
```json
{
  "backtest_id": "uuid",
  "status": "running",
  "estimated_completion": "2026-02-26T14:05:00Z"
}
```

#### Get Backtest Results
```http
GET /backtest/results/{backtest_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "status": "completed",
  "metrics": {
    "total_return": 25.5,
    "sharpe_ratio": 1.8,
    "max_drawdown": -8.2
  },
  "trades": [...]
}
```

## WebSocket API

### Real-time Market Data
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['BTC-EUR', 'ETH-EUR']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);  // { symbol, price, timestamp }
};
```

### Paper Trading Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/paper-trading');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Trade execution updates
};
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

Common codes:
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not found
- `422` - Validation error
- `500` - Internal server error

## Rate Limits

- Authenticated: 60 requests/minute
- Unauthenticated: 10 requests/minute

Headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1645891200
```

## SOC2 Audit Endpoints

### Get Audit Log
```http
GET /admin/audit-log
Authorization: Bearer <admin-token>
```

Query params:
- `start_date` - ISO 8601 format
- `end_date` - ISO 8601 format
- `user_id` - Filter by user
- `action` - Filter by action type

Response:
```json
{
  "logs": [
    {
      "timestamp": "2026-02-26T14:00:00Z",
      "user_id": "uuid",
      "action": "ORDER_PLACED",
      "details": {"symbol": "BTC-EUR", "quantity": 0.1},
      "ip_address": "10.0.0.1"
    }
  ]
}
```

Required for SOC2 compliance:
- All trade executions logged
- All authentication attempts logged
- All permission changes logged
- Logs retained for 7 years
