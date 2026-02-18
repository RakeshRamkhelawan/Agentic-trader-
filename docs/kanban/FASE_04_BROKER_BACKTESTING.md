# Fase 4: Broker Expansion & Backtesting

> **Prioriteit**: 🟡 HIGH
> **Afhankelijkheden**: Fase 1 (NavagrahaEngine voor backtest replay), Fase 2 (API auth)
> **Geschatte effort**: 6-8 dagen
> **Master document**: [SAMKHYA_MASTER_KANBAN_TDD.md](./SAMKHYA_MASTER_KANBAN_TDD.md)

---

## Overzicht

Uitbreiden van broker connectiviteit (WebSocket real-time streams), Navagraha-aware backtesting engine, en social sentiment data feed.

```
Market Data Pipeline:
  CCXT Pro WebSocket → Redpanda → OODA _observe()
                                       ↓
  Backtesting Engine ← Historical Data + NavagrahaState replay
                                       ↓
  Social Sentiment → DataScout Agent → _orient() enrichment
```

---

## Bestaande Code Referenties

| Bestand | Regels | Status |
|---------|--------|--------|
| [backend/execution/ccxt_adapter.py](../../backend/execution/ccxt_adapter.py) | 435 | REST ✅, WebSocket stubs ✅ (L333-419) |
| [backend/execution/broker_interface.py](../../backend/execution/broker_interface.py) | — | ExecutionInterface ABC |
| [backend/execution/paper_exchange.py](../../backend/execution/paper_exchange.py) | — | Paper trading |
| [backend/execution/backtest_engine.py](../../backend/execution/backtest_engine.py) | — | Bestaand backtest |
| [backend/backtesting/engine.py](../../backend/backtesting/engine.py) | 71 | BacktestEngine (L13) |
| [backend/backtesting/data_feed.py](../../backend/backtesting/data_feed.py) | 74 | DataFeed |
| [backend/backtesting/exchange.py](../../backend/backtesting/exchange.py) | 86 | SimulatedExchange |
| [backend/backtesting/metrics.py](../../backend/backtesting/metrics.py) | 51 | MetricsCalculator |
| [backend/backtesting/models.py](../../backend/backtesting/models.py) | 50 | BacktestConfig/Result |
| [backend/agents/data_scout_agent.py](../../backend/agents/data_scout_agent.py) | — | DataScout met _fetch_* stubs |

**Opmerking**: `backend/market_data/providers/` en `backend/market_data/sinks/` zijn LEEG (alleen `__pycache__`).

---

## Taken & Microtaken

---

### TAAK 4.1: WebSocket Real-Time Market Data

**Doel**: CCXT Pro WebSocket streams → Redpanda → OODA pipeline.

**Bestanden te wijzigen**:
- `backend/execution/ccxt_adapter.py` (WebSocket stubs op L333-419)

**Bestanden te creëren**:
- `backend/market_data/providers/ccxt_ws_provider.py`
- `backend/market_data/sinks/redpanda_sink.py`
- `backend/tests/unit/test_ccxt_ws_provider.py`
- `backend/tests/unit/test_redpanda_sink.py`

---

#### Microtaak 4.1.1: CCXT Pro WebSocket Provider

**Masterprompt**:
```
Vervang mock fallbacks in ccxt_adapter.py subscribe_* methoden door echte CCXT Pro calls.
Bestaande code (ccxt_adapter.py:333-419):
  subscribe_ticker() — watch_ticker als _exchange_ws aanwezig, anders mock
  subscribe_orderbook() — watch_order_book als _exchange_ws aanwezig, anders mock
  subscribe_orders() — watch_orders als _exchange_ws aanwezig, anders mock

Splits WebSocket provider uit naar apart bestand.
Reconnect met exponential backoff. Max 5 retries.
Heartbeat: ping elke 30s, timeout na 60s.
Callback pattern: on_ticker(symbol, data), on_orderbook(symbol, data).
```

**Test FIRST**:
```python
class TestCCXTWSProvider:

    def test_subscribe_ticker_receives_data(self):
        """Happy: Ticker subscription ontvangt BTC/USDT updates."""
        pass

    def test_subscribe_orderbook_receives_data(self):
        """Happy: Orderbook subscription ontvangt depth updates."""
        pass

    def test_reconnect_on_disconnect(self):
        """Happy: Auto-reconnect na WebSocket disconnect."""
        pass

    def test_exponential_backoff(self):
        """Happy: Retry delays: 1s, 2s, 4s, 8s, 16s."""
        pass

    def test_max_retries_exceeded_raises(self):
        """Unhappy: Na 5 retries → geeft op met error."""
        pass

    def test_heartbeat_timeout_triggers_reconnect(self):
        """Unhappy: Geen heartbeat > 60s → reconnect."""
        pass

    def test_invalid_symbol_raises(self):
        """Unhappy: Niet-bestaand symbol → ValueError."""
        pass

    def test_multiple_subscriptions_same_connection(self):
        """Happy: Meerdere symbols op dezelfde WS connectie."""
        pass
```

#### Microtaak 4.1.2: Redpanda Sink

**Masterprompt**:
```
Produceer ticks naar Redpanda topics:
  market.ticker.{symbol} → TickerUpdate
  market.orderbook.{symbol} → OrderBook  
  market.orders.{account_id} → OrderUpdate
Gebruik confluent-kafka of aiokafka (Redpanda is Kafka-compatible).
docker-compose.yml heeft Redpanda al op port 9094.
Schema: Avro of JSON schema.
```

---

### TAAK 4.2: Navagraha-Aware Backtesting

**Doel**: Backtest engine die NavagrahaState op historische data replayed.

**Bestanden te wijzigen**:
- `backend/backtesting/engine.py` (71 regels — uitbreiden)
- `backend/backtesting/models.py` (50 regels — NavagrahaState toevoegen)

**Bestanden te creëren**:
- `backend/backtesting/navagraha_replay.py`
- `backend/tests/unit/test_navagraha_replay.py`

---

#### Microtaak 4.2.1: NavagrahaReplay klasse

**Masterprompt**:
```
NavagrahaReplay berekent NavagrahaState voor elke bar in backtest.
Input: datetime range + interval.
Output: Iterator[NavagrahaState].
Optimalisatie: cache posities per dag (planeten bewegen langzaam).
Rahu Kala: herbereken per dag op basis van sunrise/sunset.
Hora: herbereken per uur.
Dasha: herbereken per dag (verandert langzaam).
Koppeling: BacktestEngine geeft NavagrahaState mee aan OODA cycle.
```

**Test FIRST**:
```python
class TestNavagrahaReplay:

    def test_replay_generates_states_per_bar(self):
        """Happy: Elke bar krijgt een NavagrahaState."""
        pass

    def test_replay_forward_only(self):
        """Happy: States zijn chronologisch geordend."""
        pass

    def test_rahu_kala_varies_per_day(self):
        """Happy: Rahu Kala verschilt per weekdag."""
        pass

    def test_replay_caches_positions_within_day(self):
        """Happy: Positions hergebruikt binnen zelfde dag."""
        pass

    def test_replay_over_dasha_transition(self):
        """Happy: Mahadasha wisselt binnen backtest range."""
        pass

    def test_backtest_with_navagraha_gate_blocks_some_trades(self):
        """Happy: Rahu Kala blokkeert trades in backtest."""
        pass

    def test_backtest_result_includes_navagraha_stats(self):
        """Happy: BacktestResult bevat navagraha statistieken."""
        pass
```

---

### TAAK 4.3: Social Sentiment Data Feed

**Doel**: DataScout agent's _fetch_* stubs vervangen door echte implementaties.

**Bestanden te wijzigen**:
- `backend/agents/data_scout_agent.py` (bevat _fetch_* stubs)

**Bestanden te creëren**:
- `backend/data/sentiment_providers/crypto_fear_greed.py`
- `backend/data/sentiment_providers/reddit_sentiment.py`
- `backend/tests/unit/test_sentiment_providers.py`

---

#### Microtaak 4.3.1: Crypto Fear & Greed Index

**Masterprompt**:
```
Free API: https://api.alternative.me/fng/
Retourneert 0-100 score. Map naar sentiment float (-1 tot +1).
Caching: 1 uur (publiceert 1x per dag).
Fallback: default 0.0 (neutraal) bij API-fout.
DataScout agent._fetch_social_sentiment() vervangen.
```

**Test FIRST**:
```python
class TestCryptoFearGreedProvider:

    def test_fetch_returns_valid_score(self):
        """Happy: API retourneert score 0-100."""
        pass

    def test_maps_to_sentiment_range(self):
        """Happy: Score 0-100 → sentiment -1.0 tot +1.0."""
        pass

    def test_api_timeout_returns_neutral(self):
        """Unhappy: Timeout → default 0.0."""
        pass

    def test_api_error_returns_neutral(self):
        """Unhappy: HTTP 5xx → default 0.0."""
        pass

    def test_caching_within_hour(self):
        """Happy: Tweede call binnen 1 uur retourneert cache."""
        pass
```

**Taak-afronding integratie test**:
```python
async def test_integration_4_full_market_pipeline():
    """
    Integratie: WebSocket ticker → Redpanda → OODA observe → NavagrahaState.
    Backtest engine replay met NavagrahaState.
    """
    pass
```

---

## Fase 4 Productie Test

```python
@pytest.mark.e2e
async def test_production_phase4_broker_backtesting():
    """
    PRODUCTIE TEST:
    1. CCXT WebSocket connect naar Binance testnet
    2. Receive ticker data
    3. Produce naar Redpanda
    4. Backtest met NavagrahaState replay
    5. Fear & Greed API live call
    """
    pass
```

---

## Kruisverwijzingen

- **← Fase 1**: NavagrahaEngine.assess() voor replay (Taak 1.6)
- **← Fase 2**: WebSocket auth vereist JWT (Taak 2.1)
- **← Fase 3**: Redpanda in docker-compose (Taak 3.2)
- **→ Fase 5**: Real-time ticker data naar frontend (Taak 5.3)
- **→ Fase 6**: Backtest resultaten als feedback voor Karma loop (Taak 6.1)
- **→ Fase 7**: Broker latency monitoring (Taak 7.4)
