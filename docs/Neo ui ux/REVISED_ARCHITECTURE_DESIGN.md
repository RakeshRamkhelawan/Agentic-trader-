# Revised Architecture Design
## Samkhya Yoga Agentic Trader — State Management & Performance Architecture

**Generated:** 2026-02-15  
**Document Version:** 1.0  
**Focus Areas:** NavagrahaState Threading, Caching Strategy, Circuit Breaker Patterns

---

## 1. NavagrahaState Threading Architecture

### Overview

NavagrahaState is the central philosophical backbone that threads through all system layers, from consciousness (Tattva) to material execution (OODA Act). This design specifies exactly how state is calculated, cached, propagated, and consumed.

### Threading Diagram

```
```
┌─────────────────────────────────────────────────────────────────────┐
│                         REQUEST BOUNDARY                             │
│                  (HTTP/WebSocket/Scheduled Job)                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OODA COORDINATOR (Entry Point)                    │
│  - Receives trigger (market tick, time-based, manual)               │
│  - Initializes OODAContext with request metadata                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              NAVAGRAHA STATE CALCULATOR (Phase 1.2)                  │
│                                                                       │
│  1. Check Redis Cache (key: "navagraha:state:{timestamp_5min}")     │
│     └─ HIT? → Return cached NavagrahaState (latency <50ms)          │
│     └─ MISS? → Calculate fresh (steps below)                        │
│                                                                       │
│  2. Swiss Ephemeris Calculation (pyswisseph + Kerykeion)            │
│     - Input: datetime.now(UTC), location (lat/lon)                  │
│     - Output: 9 planetary positions (lon, lat, speed, retrograde)   │
│     - Latency Budget: <500ms (cold), enforce timeout                │
│                                                                       │
│  3. Invariant Validation (test_ephemeris.py patterns)               │
│     - Assert exactly 9 planets returned                             │
│     - Assert Rahu always retrograde                                 │
│     - Assert positions in valid ranges [0, 360]                     │
│                                                                       │
│  4. Guna Aggregation (Phase 1.5 logic)                              │
│     - Map planets to gunas: Sun→Sattva, Mars→Rajas, Saturn→Tamas   │
│     - Weighted sum based on planet strength (dignities)             │
│     - Normalize: sattva + rajas + tamas = 1.0                       │
│                                                                       │
│  5. Rahu Kala Calculation (Phase 1.2 logic)                         │
│     - Calculate for current day and location                        │
│     - Cache with daily TTL (key: "rahu_kala:{date}")                │
│     - Return: is_active (bool), start_time, end_time                │
│                                                                       │
│  6. Dasha Determination (Phase 1.2 logic)                           │
│     - Based on Moon's position (Vimshottari Dasha)                  │
│     - Return: current_dasha (planet name), remaining_period         │
│                                                                       │
│  7. Assemble NavagrahaState Object                                  │
│     - planets: List[PlanetState]                                    │
│     - guna_ratios: Dict[GunaType, float]                            │
│     - rahu_kala: RahuKalaState                                      │
│     - current_dasha: DashaState                                     │
│     - calculated_at: datetime                                       │
│                                                                       │
│  8. Cache Result (Redis, TTL: 5 minutes for positions)              │
└────────────────────────────┬────────────────────────────────────────┘
                             │ NavagrahaState object
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OODA CONTEXT (State Container)                    │
│                                                                       │
│  ooda_context = OODAContext(                                         │
│      navagraha_state=state,                                          │
│      market_data=None,  # Filled in Observe                          │
│      strategy=None,      # Selected in Orient                        │
│      risk_assessment=None,  # Computed in Decide                     │
│      execution_plan=None    # Generated in Decide                    │
│  )                                                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   OBSERVE    │   │    ORIENT    │   │    DECIDE    │   ┌──────────────┐
│              │   │              │   │              │   │     ACT      │
│ - Market data│   │ - Dasha →    │   │ - Guna →     │   │              │
│   collection │   │   Strategy   │   │   Risk mod   │   │ - Rahu Kala  │
│              │   │   selection  │   │              │   │   GATE CHECK │
│ - Attach to  │──▶│              │──▶│ - Position   │──▶│              │
│   context    │   │ - Pattern    │   │   sizing     │   │ - Execute if │
│              │   │   detection  │   │              │   │   not blocked│
└──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘
        │                    │                    │              │
        │                    │                    │              │
        └────────────────────┴────────────────────┴──────────────┘
                             │ State injected into agents
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ELEMENTAL AGENTS (5 Elements)                    │
│                                                                       │
│  Each agent receives navagraha_state in constructor/observe():       │
│                                                                       │
│  def __init__(self, navagraha_state: NavagrahaState):                │
│      self.navagraha_state = navagraha_state                          │
│      self.prana = 100.0  # Initial energy                            │
│                                                                       │
│  def _update_prana(self):                                            │
│      # Guna-based decay rate                                         │
│      gunas = self.navagraha_state.guna_ratios                        │
│      decay_rate = (                                                  │
│          gunas['sattva'] * 0.01 +  # Slow decay                      │
│          gunas['rajas'] * 0.03 +   # Medium decay                    │
│          gunas['tamas'] * 0.07     # Fast decay                      │
│      )                                                               │
│      self.prana -= decay_rate                                        │
│                                                                       │
│  def _modulate_behavior(self, signal: TradingSignal) -> Signal:      │
│      # Guna modulation of trading behavior                           │
│      gunas = self.navagraha_state.guna_ratios                        │
│                                                                       │
│      if gunas['sattva'] > 0.5:  # Sattvic dominance                  │
│          signal.confidence *= 0.8  # More cautious                   │
│          signal.position_size *= 0.7                                 │
│      elif gunas['rajas'] > 0.5:  # Rajasic dominance                 │
│          signal.confidence *= 1.2  # More aggressive                 │
│          signal.position_size *= 1.3                                 │
│      elif gunas['tamas'] > 0.5:  # Tamasic dominance                 │
│          signal.confidence *= 0.5  # Very cautious/inert             │
│          signal.position_size *= 0.3                                 │
│                                                                       │
│      return signal                                                   │
└─────────────────────────────────────────────────────────────────────┘
```
```

### State Lifetime & Scope

**Calculation Frequency:**
- **On-Demand (preferred):** Calculate at start of each OODA cycle
- **Scheduled:** Background job every 5 minutes (cache warmup)
- **Event-Driven:** On Dasha transition (daily check)

**Storage Locations:**
1. **Redis Cache (L1):** 5-minute TTL for positions, daily TTL for Rahu Kala
2. **Request Context (L2):** In-memory for duration of OODA cycle
3. **PostgreSQL (L3):** Historical archive for karma learning (navagraha_state_log table)

**Propagation Pattern:**
- **Injected:** Constructor injection into all agents
- **Immutable:** State object is read-only after creation
- **Versioned:** Each state has `calculated_at` timestamp for debugging

---

## 2. Multi-Level Caching Strategy

### Cache Architecture

```
```
┌─────────────────────────────────────────────────────────────────────┐
│                         CACHE HIERARCHY                              │
└─────────────────────────────────────────────────────────────────────┘

L1 CACHE: Redis (Distributed, Shared Across Instances)
┌─────────────────────────────────────────────────────────────────────┐
│  Key Pattern                │ TTL      │ Size    │ Hit Rate Target  │
│─────────────────────────────┼──────────┼─────────┼──────────────────│
│  navagraha:positions:{ts5m} │ 5 min    │ ~2 KB   │ >80%             │
│  navagraha:aspects:{ts15m}  │ 15 min   │ ~1 KB   │ >70%             │
│  navagraha:rahu_kala:{date} │ 24 hours │ ~500 B  │ >95%             │
│  navagraha:dasha:{date}     │ 24 hours │ ~300 B  │ >95%             │
│  navagraha:guna:{ts5m}      │ 5 min    │ ~200 B  │ >80%             │
│  market:ticker:{symbol}     │ 1 min    │ ~1 KB   │ >90%             │
│  llm:response:{hash}        │ 1 hour   │ ~5 KB   │ >60%             │
└─────────────────────────────────────────────────────────────────────┘

L2 CACHE: Application Memory (Per-Instance, LRU)
┌─────────────────────────────────────────────────────────────────────┐
│  - Strategy patterns (immutable, loaded at startup)                  │
│  - Indicator calculations (last 100 values per symbol)              │
│  - Agent state (prana, recent signals)                              │
│  - Max size: 256 MB per instance                                    │
└─────────────────────────────────────────────────────────────────────┘

L3 CACHE: PostgreSQL (Historical Archive)
┌─────────────────────────────────────────────────────────────────────┐
│  - Full NavagrahaState snapshots (1 per 5 minutes)                  │
│  - Trade decisions with state context                               │
│  - Karma learning dataset (all outcomes + state)                    │
│  - Retention: 2 years, partitioned by month                         │
└─────────────────────────────────────────────────────────────────────┘
```
```

### Cache Invalidation Strategy

**Time-Based (TTL):**
- Positions: 5 minutes (ephemeris changes slowly)
- Aspects: 15 minutes (angular relationships)
- Rahu Kala: Daily (fixed time windows per day)
- Dasha: Daily (transitions at day boundaries)

**Event-Based Invalidation:**
```python
class CacheInvalidator:
    def on_dasha_transition(self, event: DashaTransitionEvent):
        redis.delete(f"navagraha:dasha:{event.date}")
        redis.delete(f"navagraha:state:*")  # Invalidate all states
        logger.info(f"Dasha transition: {event.old} → {event.new}")
    
    def on_midnight_utc(self):
        redis.delete("navagraha:rahu_kala:*")  # Clear all Rahu Kala cache
        logger.info("Daily Rahu Kala cache cleared")
    
    def on_system_restart(self):
        redis.flushdb()  # Nuclear option: clear all cache
        logger.warning("Full cache invalidation on system restart")
```

**Coherence Guarantees:**
- **Read-Your-Writes:** Use same Redis instance for write + read
- **Monotonic Reads:** Include timestamp in cache key to prevent stale reads
- **Eventual Consistency:** Accept 5-minute staleness for positions

### Performance Targets

| Operation | Target Latency (P95) | Current | Status |
|-----------|----------------------|---------|--------|
| Cache Hit (Redis) | <50ms | TBD | 🟡 To Implement |
| Cache Miss + Calc | <500ms | TBD | 🟡 To Implement |
| Full OODA Cycle | <2 seconds | TBD | 🟡 To Implement |
| Guna Calculation | <10ms | TBD | 🟡 To Implement |
| Rahu Kala Check | <5ms (cached) | TBD | 🟡 To Implement |

**Monitoring:**
```python
# Prometheus metrics
cache_hit_rate = Gauge('navagraha_cache_hit_rate', 'Cache hit rate by key pattern')
cache_latency = Histogram('navagraha_cache_latency_seconds', 'Cache operation latency')
ephemeris_calc_latency = Histogram('ephemeris_calculation_duration_seconds', 'Ephemeris calculation time')
```

---

## 3. Circuit Breaker Pattern for External APIs

### Architecture

```
```
┌─────────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER REGISTRY                          │
│                  (Shared State, Redis-Backed)                        │
└─────────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   CCXT API   │   │  Swiss Eph.  │   │  LLM APIs    │
│   Breaker    │   │   Breaker    │   │   Breaker    │
│              │   │              │   │              │
│ - Exchanges  │   │ - Kerykeion  │   │ - Ollama     │
│ - Rate limit │   │ - pyswisseph │   │ - Gemini     │
│ - Timeout    │   │ - File I/O   │   │ - DeepSeek   │
└──────────────┘   └──────────────┘   └──────────────┘
```
```

### Circuit Breaker State Machine

```
```
                    ┌─────────────────┐
                    │     CLOSED      │
                    │  (Normal Ops)   │
                    └────────┬────────┘
                             │
                    Failure threshold reached
                    (5 failures in 60s)
                             │
                             ▼
                    ┌─────────────────┐
              ┌────▶│      OPEN       │
              │     │  (Fail Fast)    │
              │     └────────┬────────┘
              │              │
              │     Timeout period elapsed
              │     (30 seconds)
              │              │
              │              ▼
              │     ┌─────────────────┐
              │     │   HALF-OPEN     │
              │     │ (Test Request)  │
              │     └────────┬────────┘
              │              │
              │    Success   │   Failure
              │      │       │      │
              └──────┘       └──────┘
                 (Close)     (Re-open)
```
```

### Implementation

```python
from enum import Enum
from datetime import datetime, timedelta
import redis
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 30
    window_seconds: int = 60

class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig, redis_client: redis.Redis):
        self.name = name
        self.config = config
        self.redis = redis_client
        self._state_key = f"circuit:{name}:state"
        self._failure_key = f"circuit:{name}:failures"
        self._last_failure_key = f"circuit:{name}:last_failure"
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        state = self._get_state()
        
        if state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _get_state(self) -> CircuitState:
        state_str = self.redis.get(self._state_key)
        if state_str:
            return CircuitState(state_str.decode())
        return CircuitState.CLOSED
    
    def _record_failure(self):
        self.redis.incr(self._failure_key)
        self.redis.expire(self._failure_key, self.config.window_seconds)
        self.redis.set(self._last_failure_key, datetime.utcnow().isoformat())
        
        failures = int(self.redis.get(self._failure_key) or 0)
        if failures >= self.config.failure_threshold:
            self._transition_to_open()
    
    def _record_success(self):
        state = self._get_state()
        if state == CircuitState.HALF_OPEN:
            self._transition_to_closed()
        self.redis.delete(self._failure_key)
    
    def _transition_to_open(self):
        self.redis.set(self._state_key, CircuitState.OPEN.value)
        logger.warning(f"Circuit {self.name} transitioned to OPEN")
        prometheus_gauge.labels(circuit=self.name).set(2)  # 2 = OPEN
    
    def _transition_to_half_open(self):
        self.redis.set(self._state_key, CircuitState.HALF_OPEN.value)
        logger.info(f"Circuit {self.name} transitioned to HALF-OPEN")
        prometheus_gauge.labels(circuit=self.name).set(1)  # 1 = HALF-OPEN
    
    def _transition_to_closed(self):
        self.redis.set(self._state_key, CircuitState.CLOSED.value)
        self.redis.delete(self._failure_key)
        logger.info(f"Circuit {self.name} transitioned to CLOSED")
        prometheus_gauge.labels(circuit=self.name).set(0)  # 0 = CLOSED
    
    def _should_attempt_reset(self) -> bool:
        last_failure_str = self.redis.get(self._last_failure_key)
        if not last_failure_str:
            return True
        
        last_failure = datetime.fromisoformat(last_failure_str.decode())
        return datetime.utcnow() - last_failure > timedelta(seconds=self.config.timeout_seconds)

class CircuitBreakerRegistry:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.breakers = {}
    
    def get_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        if name not in self.breakers:
            config = config or CircuitBreakerConfig()
            self.breakers[name] = CircuitBreaker(name, config, self.redis)
        return self.breakers[name]
```

### Usage Examples

```python
breaker_registry = CircuitBreakerRegistry(redis_client)

ccxt_breaker = breaker_registry.get_breaker("ccxt_binance", CircuitBreakerConfig(
    failure_threshold=5,
    timeout_seconds=60
))

try:
    ticker = ccxt_breaker.call(exchange.fetch_ticker, "BTC/USDT")
except CircuitBreakerOpenError:
    logger.warning("CCXT circuit open, using fallback exchange")
    ticker = fallback_exchange.fetch_ticker("BTC/USDT")
except Exception as e:
    logger.error(f"CCXT call failed: {e}")
    raise
```

### Cascade Prevention

```python
class CascadeBreaker:
    def __init__(self, breakers: List[CircuitBreaker]):
        self.breakers = breakers
    
    def check_cascade(self) -> bool:
        open_count = sum(1 for b in self.breakers if b._get_state() == CircuitState.OPEN)
        if open_count >= len(self.breakers) * 0.5:
            logger.critical("Cascade detected: 50% of circuits OPEN")
            self._trigger_emergency_mode()
            return True
        return False
    
    def _trigger_emergency_mode(self):
        redis.set("system:emergency_mode", "true")
        alert_pagerduty("Circuit breaker cascade detected")
```

---

## 4. Error Handling & Graceful Degradation

### Ephemeris Calculation Failure

```python
class NavagrahaStateCalculator:
    def calculate_with_fallback(self, dt: datetime, location: Location) -> NavagrahaState:
        try:
            return self._calculate_real(dt, location)
        except EphemerisCalculationError as e:
            logger.error(f"Ephemeris calculation failed: {e}")
            
            last_known = self._get_last_known_state(dt)
            if last_known and (dt - last_known.calculated_at) < timedelta(minutes=15):
                logger.warning("Using last known state (age: <15min)")
                return last_known
            
            logger.critical("No recent state available, using safe defaults")
            return self._create_safe_default_state(dt)
    
    def _create_safe_default_state(self, dt: datetime) -> NavagrahaState:
        return NavagrahaState(
            planets=[],  # Empty positions
            guna_ratios={"sattva": 0.7, "rajas": 0.2, "tamas": 0.1},  # Safe (cautious) ratios
            rahu_kala=RahuKalaState(is_active=False),  # Assume not active
            current_dasha=DashaState(planet="Saturn", remaining_days=365),  # Conservative
            calculated_at=dt,
            is_fallback=True  # Flag for monitoring
        )
```

### Monitoring Dashboard Requirements

See "Observability & Monitoring Plan" document for full specifications.

---

*End of Revised Architecture Design Document*