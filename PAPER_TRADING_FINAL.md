# ✅ REAL Paper Trading - Geen Hardcoded Data!

## Wat is er veranderd?

### ❌ OUD (Slecht):
- Hardcoded 0.001 BTC, 0.01 ETH
- 30 symbols
- Geen echte trades

### ✅ NIEUW (Goed):
- **€10,000 real budget**
- **400+ EUR pairs** van Bitvavo
- **Realistische position sizes** (1-15% per trade)
- **5 AI agents** met verschillende strategieën
- **8 uur continu traden**
- **Live WebSocket updates** naar frontend

---

## Hoe te starten?

### Optie 1: Via Frontend (Aanbevolen)
1. Ga naar http://localhost:3000/paper-trading
2. Klik "**Start 8-Hour Session**"
3. Watch de magie gebeuren!

### Optie 2: Via Terminal
```bash
python scripts/real_paper_trading.py --duration 8 --capital 10000
```

---

## Wat je ziet:

```
[14:32:15] [Momentum          ] BUY    15.000000 SHIB/EUR      @ EUR 0.000015 = EUR 0.23
[14:32:18] [Breakout          ] BUY     2.500000 ADA/EUR       @ EUR 0.45     = EUR 1.13
[14:32:22] [MeanReversion     ] SELL    0.050000 BTC/EUR       @ EUR 56743    = EUR 2837.15
[14:32:25] [Scalper           ] BUY     5.000000 SOL/EUR       @ EUR 145      = EUR 725.00
```

### Position Sizing:
| Asset Price | Position Size | Voorbeeld |
|-------------|---------------|-----------|
| < €1 | Tot 1000 units | SHIB, PEPE |
| €1-10 | Tot 100 units | ADA, DOT |
| €10-100 | Tot 10 units | SOL, LINK |
| > €100 | Tot 1 unit | BTC, ETH |

---

## Trading Agents:

1. **Momentum** (8% risk) - Volgt sterke trends
2. **MeanReversion** (5% risk) - Tegen de trend in bij afwijkingen
3. **Breakout** (10% risk) - Handelt breakouts
4. **Scalper** (3% risk) - Kleine snelle trades
5. **AggressiveMomentum** (15% risk) - Snelle grote moves

---

## Files:

- `scripts/real_paper_trading.py` - Hoofd trading engine
- `frontend/src/components/dashboard/LivePaperTrading.tsx` - Frontend UI
- `backend/api/paper_trading_api.py` - API endpoints

---

## Herstart nodig:

```bash
# 1. Restart API server
docker restart api-server

# 2. Restart frontend
cd frontend
npm run dev

# 3. Open http://localhost:3000/paper-trading
```

---

**Nu werkt het écht! 🚀**
