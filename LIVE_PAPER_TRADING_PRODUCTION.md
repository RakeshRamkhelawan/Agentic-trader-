# 🚀 Live Paper Trading - Production Mode

Volledig productie-achtige live ervaring met paper trading - **echte marktdata, nep geld, realtime visuals**.

---

## ✨ Features

### Realtime WebSocket Streaming
- **Live Trades** - Zie elke trade direct verschijnen
- **Price Updates** - Echte prijzen van Bitvavo & Revolut X
- **Portfolio Value** - Live P&L updates
- **Agent Decisions** - Zie welke agent wat beslist

### Multi-Exchange Support
- **Bitvavo** - 50+ EUR pairs
- **Revolut X** - Major crypto pairs
- **Live Orderbooks** - Real market depth

### Trading Agents (5 AI Agents)
1. **MomentumTrader** - Volgt prijs trends
2. **MeanReversion** - Tegen de trend in
3. **BreakoutHunter** - Zoekt breakouts
4. **ConservativeMR** - Veilige mean reversion
5. **AggressiveMomentum** - Snelle trades

---

## 🎬 Quick Start

### 1. Start de Backend

```bash
# Zorg dat alle services draaien
docker-compose up -d

# Check of API server draait
curl http://localhost:8000/health
```

### 2. Start Paper Trading Sessie

```bash
# Manier 1: Direct met Python
python scripts/live_paper_trading_production.py --duration 8 --capital 10000

# Manier 2: Via API (frontend kan dit ook)
curl -X POST http://localhost:8000/api/v1/paper-trading/start \
  -H "Content-Type: application/json" \
  -d '{"duration": 8, "capital": 10000}'
```

### 3. Open Frontend

```bash
# Start frontend
cd frontend
npm run dev

# Open http://localhost:5173/paper-trading
```

---

## 🖥️ Frontend Dashboard

### URL: `/paper-trading`

#### Componenten:

**1. Portfolio Overview (4 cards)**
- Total Value (EUR)
- P&L met percentage
- Total Trades count
- Buy/Sell ratio

**2. Live Trades (Realtime lijst)**
- Timestamp
- Symbol (BTC/EUR, etc.)
- Side (BUY/SELL badge)
- Quantity
- Price
- Agent naam

**3. Agent Decisions**
- Welke agent wat beslist
- Confidence score
- Reason (uptrend, below_avg, etc.)

**4. Agent Performance**
- Aantal trades per agent
- Grid weergave

**5. Connection Status**
- WebSocket connected/disconnected
- Session active/ended badges

---

## 🔌 WebSocket Protocol

### Connectie
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/paper-trading');
```

### Automatische Subscriptions
- `paper_trading.live` - Trades & portfolio
- `paper_trading.stats` - Statistics
- `paper_trading.agents` - Agent decisions

### Message Format

**Trade Event:**
```json
{
  "channel": "paper_trading.live",
  "type": "trade",
  "data": {
    "symbol": "BTC/EUR",
    "side": "BUY",
    "qty": 0.001,
    "price": 56743.00,
    "agent": "MomentumTrader",
    "timestamp": "2026-02-20T00:15:40Z"
  }
}
```

**Portfolio Update:**
```json
{
  "channel": "paper_trading.live",
  "type": "portfolio",
  "data": {
    "cash": 9850.00,
    "total_value": 10012.50,
    "pnl": 12.50,
    "pnl_pct": 0.13,
    "positions": {"BTC/EUR": 0.001}
  }
}
```

**Agent Decision:**
```json
{
  "channel": "paper_trading.agents",
  "type": "decision",
  "data": {
    "agent": "MomentumTrader",
    "decision": {
      "symbol": "BTC/EUR",
      "side": "BUY",
      "confidence": 0.7,
      "reason": "uptrend"
    }
  }
}
```

---

## 🛠️ API Endpoints

### Start Session
```http
POST /api/v1/paper-trading/start
Content-Type: application/json

{
  "duration": 8,    // hours
  "capital": 10000  // EUR
}
```

### Stop Session
```http
POST /api/v1/paper-trading/stop
```

### Get Status
```http
GET /api/v1/paper-trading/status

Response:
{
  "is_running": true,
  "trading_mode": "paper"
}
```

### Get WebSocket URL
```http
GET /api/v1/paper-trading/ws-url

Response:
{
  "websocket_url": "/ws/paper-trading",
  "channels": ["paper_trading.live", "paper_trading.stats", "paper_trading.agents"]
}
```

---

## 📊 Wat Je Ziet

### Realtime Updates (elke 5-30 seconden)

```
[00:15:40] [MomentumTrader    ] BUY  0.0010 BTC/EUR @ EUR 56,743.00
[00:15:42] [MeanReversion     ] SELL 0.0010 ETH/EUR @ EUR 3,245.00
[00:15:45] [BreakoutHunter    ] BUY  0.0010 SOL/EUR @ EUR 145.20

--------------------------------------------------------------------------------
STATS | 0:01:00 | Trades: 15 | P&L: EUR +12.50 (+0.13%)
--------------------------------------------------------------------------------
```

### Frontend View

```
┌─────────────────────────────────────────────────────────────────┐
│ Live Paper Trading          [Connected] [Session Active]        │
├─────────────────────────────────────────────────────────────────┤
│ Total Value    │ P&L           │ Total Trades │ Buy/Sell Ratio │
│ €10,012.50     │ €+12.50 (+0.13%)│ 15          │ 8/7            │
├─────────────────────────────────────────────────────────────────┤
│ Live Trades                │ Agent Decisions                    │
│ ────────────────────────── │ ────────────────────────────────── │
│ [BUY] 0.0010 BTC/EUR       │ MomentumTrader: BUY BTC/EUR        │
│       @ €56,743            │ Confidence: 70%                    │
│       MomentumTrader       │ Reason: uptrend                    │
│ ────────────────────────── │ ────────────────────────────────── │
│ [SELL] 0.0010 ETH/EUR      │ MeanReversion: SELL ETH/EUR        │
│        @ €3,245            │ Confidence: 65%                    │
│        MeanReversion       │ Reason: above_avg                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Productie-Mode vs Paper-Mode

| Aspect | Productie | Paper (Nu) |
|--------|-----------|------------|
| **Echt geld** | ✅ Ja | ❌ Nee |
| **Echte prijzen** | ✅ Ja | ✅ Ja |
| **Live execution** | ✅ Ja | ✅ Simulated |
| **WebSocket updates** | ✅ Ja | ✅ Ja |
| **Agent beslissingen** | ✅ Ja | ✅ Ja |
| **Frontend dashboard** | ✅ Ja | ✅ Ja |

**Conclusie:** Alles werkt hetzelfde als productie, alleen het geld is nep!

---

## 🔧 Configuratie

### Environment (.env)

```env
# VEREIST
TRADING_MODE=paper

# Bitvavo (voor prijzen)
BITVAVO_API_KEY=your_key
BITVAVO_API_SECRET=your_secret

# Revolut X (optioneel)
REVOLUT_API_KEY=your_key
REVOLUT_PRIVATE_KEY_PATH=./revolut_private.pem

# Frontend
VITE_WS_URL=ws://localhost:8000
VITE_API_URL=http://localhost:8000
```

---

## 🚀 Starten

### Manier 1: Volledige 8-uurs Sessie

```bash
# Terminal 1: Backend paper trading
python scripts/live_paper_trading_production.py --duration 8 --capital 10000

# Terminal 2: Monitor
python scripts/monitor_paper_trading.py

# Browser: http://localhost:5173/paper-trading
```

### Manier 2: Via Frontend

```bash
# Start backend
docker-compose up -d api-server

# Start frontend
cd frontend && npm run dev

# Ga naar http://localhost:5173/paper-trading
# Klik "Start Session"
```

---

## 📈 Resultaten

Na 8 uur:
- **100-500+ trades** (afhankelijk van market volatility)
- **20-50+ symbols** getraded
- **5 agents** met verschillende performance
- **Complete trade history** in database
- **Session log** in JSON file

---

## 🐛 Troubleshooting

### WebSocket Niet Verbonden
```bash
# Check of backend draait
curl http://localhost:8000/health

# Check WebSocket stats
curl http://localhost:8000/ws/stats
```

### Geen Trades
```bash
# Check Bitvavo connectie
python scripts/test_bitvavo_connection.py

# Test paper trading
python scripts/test_ultimate_trading.py
```

### Frontend Errors
```bash
# Check environment
cat frontend/.env

# Rebuild
npm install
npm run dev
```

---

## 📁 Files

### Backend
- `backend/services/paper_trading_live.py` - WebSocket broadcaster
- `backend/api/paper_trading_ws.py` - WebSocket endpoint
- `backend/api/paper_trading_api.py` - REST API
- `scripts/live_paper_trading_production.py` - Trading engine

### Frontend
- `frontend/src/pages/LivePaperTrading.tsx` - Pagina
- `frontend/src/components/dashboard/LivePaperTrading.tsx` - Component
- `frontend/src/App.tsx` - Router
- `frontend/src/components/layout/sidebar.tsx` - Navigatie

---

## 🎉 Veel Plezier!

Je hebt nu een **volledig productie-achtig** trading systeem dat:
- ✅ Realtime marktdata gebruikt
- ✅ AI agents laat traden
- ✅ Live updates naar frontend stuurt
- ✅ 8 uur lang kan draaien
- ✅ Geen echt geld riskeert

**Start je sessie en zie de magie gebeuren! 🚀**
