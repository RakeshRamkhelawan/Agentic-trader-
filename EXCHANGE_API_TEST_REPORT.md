# Exchange API Test Report

**Datum:** 2026-03-06
**Getest:** Bitvavo & Revolut X APIs
**Doel:** Data beschikbaarheid voor Paper Trading

---

## Summary

| Exchange | Status | EUR Pairs | Real-time Data | Historisch | Orderbook | Account |
|----------|--------|-----------|----------------|------------|-----------|---------|
| **Bitvavo** | ✅ **WERKT PERFECT** | 435 | ✅ Ja | ✅ Ja | ✅ Ja | ✅ Ja |
| **Revolut X** | ⚠️ **Gedeeltelijk** | 50 | ❌ Nee | ❌ Nee | ❌ Nee | ⚠️ Beperkt |

**Aanbeveling:** Gebruik **Bitvavo** als primaire exchange voor paper trading. Revolut X heeft API endpoint issues.

---

## Bitvavo API ✅

### Verbindingsinfo
- **API Type:** REST (via CCXT library)
- **Base URL:** https://api.bitvavo.com/v2
- **Rate Limit:** 1000 weight points/minuut
- **Authenticatie:** API Key + Secret (HMAC SHA256)

### Beschikbare Data

#### 1. Trading Pairs
```
✅ 435 EUR pairs beschikbaar
Voorbeelden: BTC-EUR, ETH-EUR, SOL-EUR, XRP-EUR, ADA-EUR, AVAX-EUR, etc.
```

#### 2. Real-time Prices (Ticker)
```json
{
  "BTC-EUR": {
    "last": 59132.0,
    "bid": 59139.0,
    "ask": 59143.0,
    "high_24h": 61814.0,
    "low_24h": 58858.0,
    "change_24h_pct": -4.22,
    "timestamp": "2026-03-06T18:05:44"
  }
}
```
**Beschikbaar voor:** Alle 435 EUR pairs
**Update frequentie:** Real-time

#### 3. OHLCV/Candle Data
```json
{
  "timestamp": 1772816400000,
  "open": 59001.0,
  "high": 59071.0,
  "low": 58982.0,
  "close": 59047.0,
  "volume": 6.31433524
}
```
**Timeframes:** 1m, 5m, 15m, 1h, 4h, 1d
**Historie:** Tot 1000 candles
**Gebruik:** Technische analyse, backtesting

#### 4. Order Book (Market Depth)
```json
{
  "bids": [[59139.0, 0.01457591], [59138.0, 0.10000000], ...],
  "asks": [[59143.0, 0.01457591], [59144.0, 0.10000000], ...],
  "timestamp": 1772816749131
}
```
**Diepte:** Configurabel (10-100 levels)
**Spread:** Real-time (€4.00 voor BTC-EUR)

#### 5. Account Data
```json
{
  "EUR": {"free": 1000.0, "used": 0.0, "total": 1000.0},
  "BTC": {"free": 0.5, "used": 0.0, "total": 0.5}
}
```
**Beschikbaar:** Balances, orders, trades, deposit/withdraw history

### API Kosten (Bitvavo)
| Type | Fee |
|------|-----|
| Maker | 0.15% |
| Taker | 0.25% |
| Deposit (iDEAL) | Gratis |
| Withdrawal | Variabel per asset |

---

## Revolut X API ⚠️

### Verbindingsinfo
- **API Type:** REST (custom implementatie)
- **Base URL:** https://revx.revolut.com/api/1.0
- **Authenticatie:** Ed25519 signatures (moderner dan HMAC)
- **Status:** Gedeeltelijk functioneel

### Beschikbare Data

#### 1. Trading Pairs
```
✅ 50 USD pairs beschikbaar (hardcoded fallback)
Voorbeelden: BTC-USD, ETH-USD, SOL-USD, XRP-USD, ADA-USD, etc.
```
**Probleem:** `/api/1.0/symbols` endpoint geeft 404

#### 2. Real-time Prices ❌
```
Error: 404 Not Found
Endpoint: GET /api/1.0/ticker/{symbol}
```
**Status:** API endpoint bestaat niet of is gewijzigd

#### 3. Order Book ❌
```
Error: get_orderbook() got unexpected keyword argument 'limit'
```
**Status:** Methode aanwezig maar werkt niet correct

#### 4. Account Data ⚠️
```json
// Werkt gedeeltelijk
{
  "active_orders": 0
}
```
**Probleem:** `get_balance()` methode ontbreekt

### API Documentatie Issues
Volgens de websearch moet Revolut X API endpoints hebben zoals:
- `GET /api/1.0/ticker/{symbol}` ❌ (404)
- `GET /api/1.0/symbols` ❌ (404)
- `GET /api/1.0/orders/active` ✅ (werkt)

**Conclusie:** De API client implementatie is mogelijk verouderd ten opzichte van de huidige Revolut X API.

---

## Paper Trading Integratie

### Huidige Implementatie

De paper trading engine (`backend/services/real_paper_trading_v18_direct.py`) gebruikt:

```python
# Bitvavo (Primary)
self.bitvavo = BitvavoAdapter()
success = await self.bitvavo.initialize()
eur_pairs = self.bitvavo.get_eur_pairs()  # 435 pairs

# Revolut X (Fallback/Secondary)
self.revolut = RevolutXClient()
connected = await self.revolut.connect()
symbols = await self.revolut.get_symbols()  # 50 pairs (hardcoded)
```

### Data Flow voor Paper Trading

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PAPER TRADING DATA FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

[Bitvavo API]              [Paper Trading Engine]         [Frontend]
     │                              │                         │
     │ 1. 435 EUR pairs             │                         │
     ├─────────────────────────────>│                         │
     │                              │ 2. Select top symbols   │
     │                              │    (majors + alts)      │
     │ 3. Real-time prices          │                         │
     ├─────────────────────────────>│                         │
     │                              │ 4. Agent decisions      │
     │                              │    (5 strategies)       │
     │ 5. OHLCV data                │                         │
     ├─────────────────────────────>│                         │
     │                              │ 6. Execute trades       │
     │                              │    (shadow portfolio)   │
     │                              │                         │
     │                              ├────────────────────────>│
     │                              │    7. WebSocket         │
     │                              │       broadcast         │
```

### Data Requirements vs Availability

| Requirement | Bitvavo | Revolut X | Status |
|-------------|---------|-----------|--------|
| Real-time prices | ✅ 435 pairs | ❌ Broken | ✅ Voldaan |
| Historical OHLCV | ✅ 1000 candles | ❌ N/A | ✅ Voldaan |
| Order book | ✅ 100 levels | ❌ Broken | ✅ Voldaan |
| Account balance | ✅ Full | ⚠️ Partial | ✅ Voldaan |
| Order placement | ✅ Yes | ⚠️ Unknown | ⚠️ Paper only |
| EUR pairs | ✅ 435 | ❌ 0 | ✅ Voldaan |

---

## API Documentatie (Websearch Resultaten)

### Bitvavo API
- **Docs:** https://docs.bitvavo.com/
- **Python SDK:** `python-bitvavo-api` of `bitvavo-api-upgraded`
- **Features:**
  - 1000 weight points/min rate limit
  - WebSocket support
  - MiCA compliance
  - iDEAL/Bancontact deposits

### Revolut X API
- **Docs:** https://developer.revolut.com/docs/x-api/revolut-x-crypto-exchange-rest-api
- **Authenticatie:** Ed25519 (moderner dan HMAC)
- **Features:**
  - Ed25519 signature-based auth
  - Custom headers: `X-Revx-API-Key`, `X-Revx-Timestamp`, `X-Revx-Signature`
  - Limit orders, market orders
  - Order book access

**Probleem:** De implementatie in `backend/exchange/integrations/revolut_x_client.py` lijkt niet overeen te komen met de huidige API documentatie.

---

## Recommendations

### Voor Paper Trading (Directe actie)

1. **Gebruik Bitvavo als primaire exchange**
   - 435 EUR pairs (meer dan genoeg)
   - Alle data endpoints werken
   - Nederlandse exchange (EUR focus)

2. **Revolut X uitschakelen of fixen**
   - Huidige implementatie is non-functioneel
   - Vereist update van API client
   - Of verwijderen uit paper trading engine

3. **Bitvavo uitbreiden**
   ```python
   # Meer pairs selecteren
   majors = ["BTC-EUR", "ETH-EUR", "SOL-EUR", "XRP-EUR", ...]  # Top 20
   alts = random.sample(eur_pairs, 100)  # 100 random alts
   self.symbols["bitvavo"] = majors + alts  # 120 total
   ```

### Voor Productie

1. **Revolut X client updaten**
   - Nieuwe API endpoints implementeren
   - Ed25519 authenticatie behouden (is modern)
   - Test tegen live API

2. **Bitvavo multi-key support**
   - Rate limiting opheffen
   - Meerdere API keys roteren
   - Zie `bitvavo-api-upgraded` package

3. **Fallback mechanisme**
   ```python
   if bitvavo.available:
       use_bitvavo()
   else:
       logger.error("No exchange available")
       # Don't use Revolut X until fixed
   ```

---

## Test Output Files

De volgende JSON files zijn gegenereerd tijdens test:

| File | Exchange | Data |
|------|----------|------|
| `bitvavo_all_eur_pairs.json` | Bitvavo | Alle 435 EUR pairs |
| `bitvavo_prices_snapshot.json` | Bitvavo | Real-time prijzen (19 pairs) |
| `bitvavo_btc_eur_ohlcv_1h.json` | Bitvavo | 24h candle data |
| `bitvavo_btc_eur_orderbook.json` | Bitvavo | Order book depth |
| `bitvavo_balance.json` | Bitvavo | Account balance |
| `revolut_x_all_symbols.json` | Revolut X | 50 USD pairs (hardcoded) |
| `revolut_x_active_orders.json` | Revolut X | 0 actieve orders |

---

## Conclusie

**Bitvavo is productie-ready** voor paper trading met:
- ✅ 435 EUR trading pairs
- ✅ Real-time prijs data
- ✅ Historische OHLCV data
- ✅ Order book depth
- ✅ Account management
- ✅ Nederlandse regulatory compliance

**Revolut X is niet productie-ready** vanwege API endpoint issues. Vereist significante updates aan de client implementatie.

**Advies:** Focus paper trading development op Bitvavo integratie. Revolut X kan later worden toegevoegd wanneer de API client is gefixt.

---

**Einde Report**
