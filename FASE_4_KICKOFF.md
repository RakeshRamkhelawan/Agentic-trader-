# Fase 4: Broker & Backtesting — Kickoff Plan

> **Status**: INITIATED — 14 Feb 2026  
> **Previous Phases**: ✅ 3A (Exceptions), ✅ 3B (K8s), ✅ 3C (Logging ~75%)  
> **Scope**: WebSocket streams, Navagraha backtesting, sentiment feeds  
> **Estimated Duration**: 5-7 days

---

## Quick Reference

| Task | Component | Files | Priority | Est. Hours |
|------|-----------|-------|----------|-----------|
| **4.1** | CCXT WebSocket | `ccxt_ws_provider.py`, `redpanda_sink.py` | HIGH | 8-10 |
| **4.2** | Navagraha Replay | `navagraha_replay.py`, enhanced `engine.py` | HIGH | 6-8 |
| **4.3** | Sentiment Feed | `crypto_fear_greed.py`, `reddit_sentiment.py` | MEDIUM | 4-6 |

---

## Implementation Sequence

### Phase 4.1: WebSocket Real-Time Market Data ⇒ NOW

**Objective**: Stream live ticker data via CCXT Pro WebSocket to Redpanda

**Files to Create**:
1. `backend/market_data/providers/__init__.py`
2. `backend/market_data/providers/ccxt_ws_provider.py` — CCXT Pro WebSocket wrapper
3. `backend/market_data/sinks/__init__.py`
4. `backend/market_data/sinks/redpanda_sink.py` — Kafka producer
5. `backend/tests/unit/test_ccxt_ws_provider.py` — TDD tests
6. `backend/tests/unit/test_redpanda_sink.py` — TDD tests

**Files to Modify**:
- `backend/execution/ccxt_adapter.py` — Replace mock stubs with real WebSocket calls

**Approach**:
- Write tests FIRST (Red phase)
- Implement WebSocket with exponential backoff (3 retries, 1s-8s delays)
- Heartbeat: ping every 30s, timeout after 60s
- Redpanda topics: `market.ticker.{symbol}`, `market.orderbook.{symbol}`, `market.orders.{account_id}`

---

### Phase 4.2: Navagraha-Aware Backtesting Engine

**Objective**: Replay historical data with NavagrahaState calculations

**Files to Create**:
1. `backend/backtesting/navagraha_replay.py` — NavagrahaState replay iterator
2. `backend/tests/unit/test_navagraha_replay.py` — TDD tests
3. `backend/tests/integration/test_backtest_navagraha_full.py` — E2E integration

**Files to Modify**:
- `backend/backtesting/engine.py` — Enhanced with NavagrahaState parameter
- `backend/backtesting/models.py` — Add NavagrahaState to BacktestResult

**Approach**:
- Load NavagrahaEngine from Fase 1 (dependency)
- Calculate states per bar (hourly/daily granularity)
- Cache planetary positions within day (ephemeris slow)
- Apply Rahu Kala gate: block trades during inauspicious times
- Track navagraha metrics in backtest results

---

### Phase 4.3: Social Sentiment Data Feed

**Objective**: Enrich market data with real-time sentiment indicators

**Files to Create**:
1. `backend/data/sentiment_providers/__init__.py`
2. `backend/data/sentiment_providers/crypto_fear_greed.py` — Free public API
3. `backend/data/sentiment_providers/reddit_sentiment.py` — PRAW + Redis caching
4. `backend/tests/unit/test_sentiment_providers.py` — TDD tests

**Files to Modify**:
- `backend/agents/data_scout_agent.py` — Replace _fetch_* stubs

**Approach**:
- Crypto Fear & Greed: map 0-100 → sentiment -1.0 to +1.0
- Cache 1 hour (API publishes daily)
- Fallback: neutral 0.0 on errors
- Reddit sentiment: optional PRAW integration (requires API key)

---

## Dependencies Verification ✓

- ✅ **Fase 1**: NavagrahaEngine.assess() available (for replay)
- ✅ **Fase 2**: JWT auth framework ready (for WebSocket)
- ✅ **Fase 3**: docker-compose with Redpanda on port 9094
- ✅ **ccxt**: Pro version installed (ws support)
- ⚠️ **Redpanda**: Verify connectivity on 9094

---

## Testing Strategy (TDD)

**For each task**:
1. **RED**: Write failing tests (all edge cases)
2. **GREEN**: Implement to pass tests
3. **REFACTOR**: Extract, optimize, document

**Test Levels**:
- **Unit**: Individual providers/sinks in isolation
- **Integration**: Full pipeline (WebSocket → Redpanda → OODA)
- **E2E**: Production simulation (Binance testnet if available)

---

## Go/No-Go Checklist

- [x] Fase 3C priority files converted (~310 f-strings)
- [x] Dependencies documented
- [x] File structure planned
- [x] Test cases outlined in task docs
- [ ] **NEXT**: Start Task 4.1 WebSocket provider

---

## Success Criteria (Phase 4 Complete)

1. **WebSocket**: Live ticker from 1+ exchange, 0 missed ticks over 1 hour
2. **Backtesting**: Run 1-year backtest with NavagrahaState, output includes auspicious/inauspicious trade %, R² > 0.8
3. **Sentiment**: Correlate Fear & Greed with OODA decisions, 5+ sentiment feeds integrated
4. **Integration**: E2E test passes, data flows: WebSocket → Redpanda → OODA → Backtest

---

## Next Step

**→ BEGIN TASK 4.1: WebSocket Provider**

1. Create test file: `backend/tests/unit/test_ccxt_ws_provider.py`
2. Write all test cases (RED phase)
3. Create `backend/market_data/providers/ccxt_ws_provider.py`
4. Implement until tests pass (GREEN phase)
5. Create Redpanda sink tests
6. Implement Redpanda sink

---

## Timeline (Estimated)

| Task | Days | Status |
|------|------|--------|
| 4.1: WebSocket | 2-3 | ⏳ Ready |
| 4.2: Backtesting | 2 | ⏳ Blocked (after 4.1) |
| 4.3: Sentiment | 1-2 | ⏳ Blocked (after 4.1) |
| **Total** | **5-7** | **INITIATED** |
