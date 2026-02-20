# 📈 Realtime Paper Trading Guide

Deze guide beschrijft hoe je paper trading kunt uitvoeren met **echte marktdata** van Bitvavo en Revolut X.

---

## ✅ Wat is Paper Trading?

Paper trading is het simuleren van trades met "nep" geld, maar tegen **echte marktprijzen**. Dit is ideaal voor:
- Testen van strategieën zonder risico
- Data genereren voor de applicatie
- Valideren van de trading flow

---

## 🚀 Quick Start

### 1. Infrastructuur Starten

```bash
# Start alle services
docker-compose up -d

# Controleer of alles draait
docker ps
```

### 2. Environment Configuratie

Controleer `.env`:

```env
# Trading Mode (belangrijk!)
TRADING_MODE=paper

# Bitvavo API (voor realtime data)
BITVAVO_API_KEY=your_key
BITVAVO_API_SECRET=your_secret
BITVAVO_SANDBOX=false

# Revolut X API (optioneel)
REVOLUT_API_KEY=your_key
REVOLUT_PRIVATE_KEY_PATH=./revolut_private.pem
```

### 3. Realtime Paper Trading Starten

```bash
# Automatische trading (10 trades)
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 10

# Interactieve trading
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR
```

---

## 📊 Beschikbare Scripts

| Script | Doel |
|--------|------|
| `realtime_paper_trading.py` | Realtime paper trading met echte data |
| `run_paper_trading.py` | Simulatie met gegenereerde prijzen |
| `import_paper_trades.py` | Importeer trades naar database |
| `check_paper_trades_db.py` | Check trades in database |
| `test_bitvavo_connection.py` | Test Bitvavo connectie |

---

## 💻 Interactieve Trading Commands

Wanneer je het interactieve script start:

```
> buy 0.001        # Koop 0.001 BTC
> sell 0.001       # Verkoop 0.001 BTC
> balance          # Toon huidige balans
> status           # Toon prijs en positie
> auto 20          # Auto-trade 20 trades
> quit             # Afsluiten
```

---

## 📈 Data Generatie

### Methode 1: Realtime met Bitvavo (Aanbevolen)

```bash
# Genereer 50 trades met echte marktdata
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 50
```

**Voordelen:**
- Echte marktprijzen van Bitvavo
- Real-time orderbook data
- 437+ EUR trading pairs beschikbaar

### Methode 2: Simulatie

```bash
# Genereer 100 trades met gesimuleerde prijzen
python scripts/run_paper_trading.py 100

# Importeer naar database
python scripts/import_paper_trades.py
```

---

## 🔌 Exchanges

### Bitvavo (Nederlands)

```bash
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR
```

- **Voordelen:** EUR pairs, iDEAL, Nederlandse exchange
- **Symbol format:** `BTC/EUR`, `ETH/EUR`
- **API Docs:** https://docs.bitvavo.com/

### Revolut X

```bash
python scripts/realtime_paper_trading.py --exchange revolut --symbol BTC-USD
```

- **Voordelen:** Lage fees, goede API
- **Symbol format:** `BTC-USD`, `ETH-USD`
- **API Docs:** https://developer.revolut.com/

---

## 🗄️ Database

Trades worden opgeslagen in PostgreSQL onder:
- **Table:** `orders`
- **Tenant:** `paper_trading`
- **Status:** `FILLED`

### Check Data

```bash
python scripts/check_paper_trades_db.py
```

### API Endpoints

```bash
# Get all trades
curl http://localhost:8003/api/v1/trading/history

# Get portfolio
curl http://localhost:8003/api/v1/trading/portfolio
```

---

## ⚙️ Configuratie

### Trading Mode

Zorg dat `TRADING_MODE=paper` staat in `.env`:

```bash
# Controleer
grep TRADING_MODE .env

# Instellen
sed -i 's/TRADING_MODE=.*/TRADING_MODE=paper/' .env
```

### Meer Data Genereren

```bash
# 500 trades genereren
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 500

# Meerdere symbolen
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol ETH/EUR --auto 50
```

---

## 📊 Resultaten

Na een sessie worden automatisch:
1. Trades uitgevoerd tegen echte marktprijzen
2. Session data opgeslagen naar JSON
3. Trades geïmporteerd in database
4. Balans getoond

**Voorbeeld output:**
```
[23:09:10] BTC/EUR @ EUR 56,755.00
  [OK] BUY 0.001 @ EUR 56,755.00
  [OK] SELL 0.001 @ EUR 56,755.00

Final Balance:
  Cash: EUR 10,000.01
  BTC/EUR: 0.000000
  Total Value: EUR 10,000.01
```

---

## 🔒 Veiligheid

- **Paper Trading = Geen echt geld**
- API keys alleen voor lezen (market data)
- Geen live orders mogelijk in paper mode
- ShadowPortfolio houdt simulatie bij

---

## 🐛 Troubleshooting

### Bitvavo Connection Failed

```bash
# Test connectie
python scripts/test_bitvavo_connection.py

# Check API keys
grep BITVAVO .env
```

### Database Error

```bash
# Fix schema
python scripts/fix_orders_schema.py
python scripts/fix_orders_id.py
```

### Import Failed

```bash
# Handmatig importeren
python scripts/import_realtime_paper_trades.py realtime_paper_session_YYYYMMDD_HHMMSS.json
```

---

## 📝 Voorbeeld Workflow

```bash
# 1. Start infrastructuur
docker-compose up -d

# 2. Test connectie
python scripts/test_bitvavo_connection.py

# 3. Genereer 100 trades met echte data
python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR --auto 100

# 4. Check database
python scripts/check_paper_trades_db.py

# 5. Start frontend
# Open http://localhost:3000 om trades te zien
```

---

## 🎯 Volgende Stappen

1. **Strategy Backtesting:** Test strategieën op historische data
2. **Live Signals:** Genereer signals zonder execution
3. **Multi-Asset:** Trade meerdere pairs tegelijk
4. **Performance Analysis:** Analyseer resultaten in Grafana

---

**Veel succes met paper trading! 🚀**
