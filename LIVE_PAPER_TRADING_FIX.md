# Live Paper Trading - Fix & Start Guide

## ✅ API Status

De API endpoints zijn nu werkend:

```bash
# Test via Docker (werkt!)
docker exec api-server python -c "
from fastapi.testclient import TestClient
from backend.api.main import app
client = TestClient(app)

# Status check
r = client.get('/api/v1/paper-trading/status')
print(f'Status: {r.json()}')

# Start session
r = client.post('/api/v1/paper-trading/start', json={'duration': 8, 'capital': 10000})
print(f'Start: {r.json()}')
"
```

### Beschikbare Endpoints:

| Endpoint | Methode | Status |
|----------|---------|--------|
| `/api/v1/paper-trading/status` | GET | ✅ Werkend |
| `/api/v1/paper-trading/ws-url` | GET | ✅ Werkend |
| `/api/v1/paper-trading/start` | POST | ✅ Werkend |
| `/api/v1/paper-trading/stop` | POST | ✅ Werkend |
| `/ws/paper-trading` | WebSocket | ✅ Werkend |

---

## 🚀 Start de Paper Trading Sessie

### Manier 1: Via Python Script (Aanbevolen)

```bash
# Terminal 1: Start live trading
python scripts/live_paper_trading_production.py --duration 8 --capital 10000

# Terminal 2: Monitor
docker logs -f api-server
```

### Manier 2: Via Frontend

```bash
# 1. Zorg dat API draait
docker-compose up -d api-server

# 2. Start frontend
cd frontend
npm run dev

# 3. Open http://localhost:5173/paper-trading
# 4. Klik "Start Session"
```

---

## 🌐 WebSocket Test

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/paper-trading');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({type: 'subscribe', channel: 'paper_trading.live'}));
};

ws.onmessage = (e) => {
  console.log('Message:', JSON.parse(e.data));
};
```

---

## 📊 Wat Je Ziet

### Console Output:
```
[00:15:40] [MomentumTrader    ] BUY  0.0010 BTC/EUR @ EUR 56,743.00
[00:15:42] [MeanReversion     ] SELL 0.0010 ETH/EUR @ EUR 3,245.00

STATUS | 0:01:00 | Trades: 15 | P&L: EUR +12.50 (+0.13%)
```

### Frontend:
- Real-time trade updates
- Portfolio value
- Agent decisions
- Live statistics

---

## 🔧 Troubleshooting

### API Error?
```bash
# Check of API draait
docker logs api-server --tail 20

# Restart indien nodig
docker restart api-server
```

### WebSocket Error?
```bash
# Check WebSocket stats
docker exec api-server python -c "
from backend.api.websocket_manager import ws_manager
print(ws_manager.get_stats())
"
```

### Frontend Error?
```bash
# Clear cache & restart
cd frontend
rm -rf node_modules/.vite
npm run dev
```

---

## 📁 Files

- `backend/api/paper_trading_api.py` - REST API
- `backend/api/paper_trading_ws.py` - WebSocket endpoint
- `backend/services/paper_trading_engine.py` - Trading engine
- `frontend/src/pages/LivePaperTrading.tsx` - Frontend pagina
- `frontend/src/components/dashboard/LivePaperTrading.tsx` - Dashboard component

---

## 🎉 Veel Plezier!

De paper trading is nu volledig functioneel met:
- ✅ Live WebSocket updates
- ✅ Multi-exchange support
- ✅ 5 AI trading agents
- ✅ Real-time dashboard
