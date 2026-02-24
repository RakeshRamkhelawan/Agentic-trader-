# Data Flow Timing Audit

## Huidige Timing Analyse

### 1. Data Inkomend (Bitvavo WebSocket)
```
WebSocket berichten: ~5-10ms tussen updates per symbool
Totaal 113 symbolen: ~100-200ms voor volledige refresh
```

### 2. Data Verwerking
```
WebSocket message parsing: ~1-2ms per bericht
Cache update: ~0.5ms per symbool
```

### 3. Trading Cycle
```
Interval: 3 seconden
- Get fresh prices: ~1-5ms
- Analyze 30 symbols: ~50-100ms
- Execute trades: ~10-50ms
- Totaal per cycle: ~100-200ms
```

### 4. Bottlenecks Identified
```
Probleem: Data staleness check faalt omdat:
1. WebSocket data komt binnen maar wordt niet correct verwerkt (geen "last" field)
2. REST fallback duurt ~1-2 seconden voor 100 symbolen
3. Trading agents checken elke 3s, maar data kan 60s oud zijn
```

## Voorgestelde Oplossing: Data Pre-fetch Agent

### Architectuur
```
┌─────────────────────────────────────────────────────────────┐
│                    DATA PRE-FETCH AGENT                      │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Warm-up    │───▶│   Cache      │───▶│   Serving    │  │
│  │   (2 min)    │    │   (99 symb)  │    │   (agents)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   ▲                   ▲           │
│         │                   │                   │           │
│  ┌──────▼───────────────────┴───────────────────┘           │
│  │              Multi-Source Fetcher                        │
│  │  • WebSocket (real-time) - 10ms latency                  │
│  │  • REST batch (backup) - 1s latency                      │
│  │  • Historical warm-up - 30s latency (eenmalig)           │
│  └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   TRADING AGENTS                             │
│                                                              │
│  Momentum ──────┐                                           │
│  MeanReversion ─┼──▶ ┌─────────────┐  ───▶ Orders          │
│  Breakout ──────┤    │   Cache     │                        │
│  Scalper ───────┼──▶ │   Read      │  ───▶ Orders          │
│  Position ──────┘    └─────────────┘                        │
│                                                              │
│  Refresh interval: elke 3s (async van data fetch)           │
└─────────────────────────────────────────────────────────────┘
```

### Timing Guarantees
```
Data Pre-fetch Agent:
- Start: T-2min (warm-up historical data)
- Real-time: WebSocket streaming (T-0)
- Cache refresh: elke 1s (WebSocket) + elke 5s (REST backup)
- Data age max: 5s (stale threshold)

Trading Agents:
- Data request: T+0
- Cache hit: <1ms (100% hit rate)
- Data age: <5s (garantie)
```

### Voordelen
1. **Gegarandeerde data availability**: Agents krijgen ALTIJD data
2. **Decoupling**: Data fetch en trading zijn onafhankelijk
3. **Multi-source**: WebSocket + REST + Historical warm-up
4. **Predictable latency**: <1ms voor agents
5. **Fault tolerance**: Als WebSocket faalt, heeft cache nog 60s data

### Implementatie Plan
1. Creëer `DataPreFetchAgent` class
2. Voeg warm-up mode toe (historische data vooraf laden)
3. Implementeer multi-source fetching (WS + REST parallel)
4. Update trading agents om van DataAgent te lezen
5. Voeg health checks en monitoring toe
