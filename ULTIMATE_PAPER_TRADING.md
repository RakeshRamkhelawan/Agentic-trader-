# 🚀 Ultimate Multi-Exchange Paper Trading

Complete 8-hour paper trading systeem met alle symbolen van Bitvavo en Revolut X.

---

## 📊 Systeem Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ULTIMATE PAPER TRADING SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Capital: EUR 10,000                                                        │
│  Duration: 8 hours                                                          │
│  Exchanges: Bitvavo + Revolut X                                             │
│  Symbols: 50+ EUR pairs                                                     │
│  Agents: 4 trading strategies                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Trading Agents:
1. **MomentumAgent** - Volgt trends (10% risico)
2. **MeanRevAgent** - Tegen de trend in (8% risico)
3. **RandomAgent** - Willekeurige trades (5% risico)
4. **AggressiveMomentum** - Snelle momentum (15% risico)

---

## 🚀 Quick Start

### Optie 1: Windows PowerShell

```powershell
# Start 8-uurs sessie
.\scripts\start_8h_paper_trading.ps1
```

### Optie 2: Linux/Mac/Windows Git Bash

```bash
# Start 8-uurs sessie
chmod +x scripts/start_8h_paper_trading.sh
./scripts/start_8h_paper_trading.sh
```

### Optie 3: Direct Python

```bash
# Start 8-uurs sessie met logging
python scripts/ultimate_paper_trading.py --duration 8 --capital 10000 2>&1 | tee paper_trading_8h.log
```

---

## 📈 Live Monitoring

Open een **tweede terminal** om live mee te kijken:

```bash
python scripts/monitor_paper_trading.py
```

Dit toont:
- Totaal aantal trades
- Unieke symbols
- Recentste trades
- Top 10 symbols

---

## 🎯 Wat het Systeem Doet

### 1. Exchange Connecties
```
[INIT] Connecting to exchanges...
[OK] Bitvavo: 50 EUR pairs
[OK] Revolut X: 30 major pairs
[INFO] Total symbols to trade: 80
```

### 2. Prijs Updates
Elke 10 seconden:
- Fetch prijzen van alle exchanges
- Update portfolio waardes
- Sla prijs history op

### 3. Trading Cycles
Elke cyclus:
- Selecteer 5 willekeurige symbols
- Laat agents beslissen
- Execute paper trades
- Log resultaten

### 4. Status Reports
Elke minuut:
- Portfolio value
- P&L berekening
- Trade statistics
- Agent performance

---

## 📋 Output

### Console Output:
```
[00:15:40] [MomentumAgent       ] BUY  0.001000 BTC/EUR      @ EUR 56,743.00
[00:15:42] [MeanRevAgent        ] SELL 0.001000 ETH/EUR      @ EUR 3,245.00
...
--------------------------------------------------------------------------------
STATUS REPORT | Elapsed: 0:01:00 | Trades: 15
--------------------------------------------------------------------------------
  Cash: EUR 9,850.00
  Portfolio Value: EUR 10,012.50
  P&L: EUR +12.50 (+0.13%)
  Symbols Traded: 8
  Buy/Sell: 8/7
```

### Database:
Alle trades worden opgeslagen in:
- **Table:** `orders`
- **Tenant:** `paper_trading`
- **Status:** `FILLED`

### Log Files:
- `paper_trading_8h_YYYYMMDD_HHMMSS.log` - Complete log
- `ultimate_paper_session_YYYYMMDD_HHMMSS.json` - Trade data

---

## 🔍 Resultaten Bekijken

### Na de sessie:

```bash
# Check database
python scripts/check_paper_trades_db.py

# Importeer trades (automatisch gebeurd)
python scripts/import_ultimate_trades.py <session_file.json>
```

### API Endpoints:

```bash
# Alle trades
curl http://localhost:8003/api/v1/trading/history

# Portfolio
curl http://localhost:8003/api/v1/trading/portfolio
```

---

## ⚙️ Configuratie

### Environment Variables (.env):

```env
# Trading Mode (vereist)
TRADING_MODE=paper

# Bitvavo (voor alle EUR pairs)
BITVAVO_API_KEY=your_key
BITVAVO_API_SECRET=your_secret
BITVAVO_SANDBOX=false

# Revolut X (optioneel)
REVOLUT_API_KEY=your_key
REVOLUT_PRIVATE_KEY_PATH=./revolut_private.pem
```

### Aanpassen:

```bash
# Meer capital
python scripts/ultimate_paper_trading.py --duration 8 --capital 50000

# Kortere test (1 uur)
python scripts/ultimate_paper_trading.py --duration 1 --capital 10000

# Alleen Bitvavo (als Revolut X niet werkt)
# Wijzig in ultimate_paper_trading.py:
# - Commentarieer Revolut X sectie
```

---

## 🐛 Troubleshooting

### Revolut X 401 Error

```
[ERROR] Revolut X: 401 Unauthorized
```

**Oplossing:** Revolut X is optioneel. Het systeem werkt prima met alleen Bitvavo. Om Revolut X te fixen:
1. Check API key in .env
2. Genereer nieuwe keys via https://exchange.revolut.com/

### Database Errors

```bash
# Fix schema
python scripts/fix_orders_schema.py
python scripts/fix_orders_id.py
```

### Geen Trades

```bash
# Test connectie
python scripts/test_bitvavo_connection.py

# Test ultimate system (korte run)
python scripts/test_ultimate_trading.py
```

---

## 📊 Voorbeeld Workflow

```bash
# Terminal 1: Start trading sessie
python scripts/ultimate_paper_trading.py --duration 8 --capital 10000

# Terminal 2: Monitor (optioneel)
python scripts/monitor_paper_trading.py

# Wacht 8 uur...

# Na afloop: check resultaten
python scripts/check_paper_trades_db.py
```

---

## 🎓 Hoe de Agents Werken

### Momentum Strategy
```python
if price > previous > before_previous:
    BUY  # Trend is omhoog
elif price < previous < before_previous:
    SELL  # Trend is omlaag
```

### Mean Reversion Strategy
```python
average = mean(last_10_prices)
if price < average * 0.99:
    BUY  # Prijs is onder gemiddelde
elif price > average * 1.01:
    SELL  # Prijs is boven gemiddelde
```

### Random Strategy
```python
if random() > 0.7:
    BUY or SELL  # 30% kans om te traden
```

---

## 📈 Verwachte Resultaten

Na 8 uur:
- **100-500+ trades** (afhankelijk van market activity)
- **20-50+ symbols** getraded
- **Agents** met verschillende performance
- **Portfolio value** met P&L tracking

---

## 🔒 Veiligheid

- **100% Paper Trading** - Geen echt geld
- **Read-only API keys** - Alleen market data
- **Shadow Portfolio** - Simulatie in geheugen
- **Database logging** - Alle trades gelogd

---

**Start je 8-uurs sessie nu! 🚀**

```bash
python scripts/ultimate_paper_trading.py --duration 8 --capital 10000
```
