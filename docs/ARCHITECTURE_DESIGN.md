# Revised Architecture Design - Samkhya Yoga Agentic Trader

**Generated:** 2026-02-14  
**Version:** 1.0  
**Focus:** State Management, Performance Optimization, Circuit Breakers

---

## 1. NavagrahaState Threading Architecture

### 1.1 Overview

NavagrahaState represents the current planetary positions and their influences. This state must thread through every layer of the system while maintaining:
- **Immutability:** State snapshots are read-only
- **Freshness:** Positions cached with TTL-based invalidation
- **Accessibility:** Available to OODA, Agents, Execution, and Audit layers

### 1.2 State Flow Diagram

```
```
┌─────────────────────────────────────────────────────────────────┐
│                    NAVAGRAHA STATE LIFECYCLE                     │
└─────────────────────────────────────────────────────────────────┘

[Swiss Ephemeris Engine]
          │
          │ Calculate positions every 5 minutes
          ▼
┌──────────────────────┐
│  NavagrahaState      │
│  - timestamp         │
│  - planet_positions  │   Cache: Redis
│  - aspects           │   TTL: 5min (positions)
│  - rahu_kala         │        15min (aspects)
│  - dasha_period      │        24h (rahu_kala, dasha)
└──────────────────────┘
          │
          │ Publish to Redis PubSub channel: "navagraha:updates"
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     STATE CONSUMERS (Parallel)                   │
├─────────────────┬─────────────────┬──────────────┬──────────────┤
│                 │                 │              │              │
▼                 ▼                 ▼              ▼              ▼
[OODA Loop]   [Guna Engine]   [WebSocket]   [Audit Log]   [Dashboard]
     │              │               │              │              │
     │              │               │              │              │
     ▼              ▼               │              │              │
[Elemental     [Prana          Broadcast      Store for     Real-time
 Agents]        Modulation]     to clients    compliance    visualization
     │              │                                            │
     └──────────────┴────────────────────────────────────────────┘
                                   │
                                   ▼
                         [Execution Layer]
                         Decision contains:
                         - navagraha_snapshot_id
                         - guna_ratios
                         - agent_votes
```
```

### 1.3 State Schema

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
from enum import Enum

@dataclass(frozen=True)
class PlanetPosition:
    longitude: float
    latitude: float
    speed: float
    is_retrograde: bool
    house: int
    sign: str

@dataclass(frozen=True)
class Aspect:
    planet1: str
    planet2: str
    angle: float
    aspect_type: str
    orb: float
    is_applying: bool

@dataclass(frozen=True)
class NavagrahaState:
    timestamp: datetime
    calculation_time_ms: float
    
    planets: Dict[str, PlanetPosition]
    
    aspects: List[Aspect]
    
    rahu_kala_start: datetime
    rahu_kala_end: datetime
    is_rahu_kala_active: bool
    
    dasha_lord: str
    dasha_start: datetime
    dasha_end: datetime
    
    cache_key: str
    version: str = "1.0"
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'planets': {k: v.__dict__ for k, v in self.planets.items()},
            'aspects': [a.__dict__ for a in self.aspects],
            'rahu_kala': {
                'active': self.is_rahu_kala_active,
                'start': self.rahu_kala_start.isoformat(),
                'end': self.rahu_kala_end.isoformat()
            },
            'dasha': {
                'lord': self.dasha_lord,
                'start': self.dasha_start.isoformat(),
                'end': self.dasha_end.isoformat()
            }
        }
```

### 1.4 State Access Patterns

**Pattern 1: OODA Loop Integration**
```python
class OODACoordinator:
    async def observe(self) -> Observations:
        navagraha_state = await self.navagraha_service.get_current_state()
        
        return Observations(
            market_data=await self.market_service.get_latest(),
            navagraha_state=navagraha_state,
            sentiment=await self.sentiment_service.analyze(),
            timestamp=datetime.utcnow()
        )
    
    async def orient(self, observations: Observations) -> Orientation:
        guna_ratios = self.guna_engine.calculate(observations.navagraha_state)
        
        return Orientation(
            guna_ratios=guna_ratios,
            navagraha_snapshot_id=observations.navagraha_state.cache_key,
            context=self._build_context(observations)
        )
```

**Pattern 2: Execution Layer Audit**
```python
class OrderExecutor:
    async def execute(self, decision: Decision) -> ExecutionResult:
        navagraha_state = await self.navagraha_service.get_by_cache_key(
            decision.navagraha_snapshot_id
        )
        
        audit_record = AuditRecord(
            decision_id=decision.id,
            navagraha_state=navagraha_state.to_dict(),
            guna_ratios=decision.guna_ratios,
            execution_timestamp=datetime.utcnow()
        )
        
        await self.audit_logger.log(audit_record)
        
        return await self._execute_order(decision, navagraha_state)
```

---

## 2. Caching Strategy for Swiss Ephemeris

### 2.1 Cache Hierarchy

```
```
┌──────────────────────────────────────────────────────────────┐
│                    CACHING LAYERS                             │
└──────────────────────────────────────────────────────────────┘

L1: In-Memory Cache (Python LRU)
    - Size: 100 most recent states
    - Eviction: LRU
    - Hit rate target: 60%
    - Latency: <1ms
    
    ▼ (on miss)

L2: Redis Cache (Distributed)
    - TTL by data type:
      * Planet positions: 5 minutes
      * Aspects: 15 minutes
      * Rahu Kala: 24 hours
      * Dasha periods: 24 hours
    - Hit rate target: 95%
    - Latency: <5ms
    
    ▼ (on miss)

L3: Swiss Ephemeris Calculation
    - Fallback: Last known good state (max age: 1 hour)
    - Circuit breaker: After 3 consecutive failures
    - Latency: 50-100ms
```
```

### 2.2 Redis Key Schema

```python
class NavagrahaCache:
    KEY_PATTERNS = {
        'position': 'navagraha:pos:{date}:{time_bucket}:{planet}',
        'aspects': 'navagraha:asp:{date}:{time_bucket}',
        'rahu_kala': 'navagraha:rk:{date}',
        'dasha': 'navagraha:dasha:{date}',
        'full_state': 'navagraha:state:{cache_key}'
    }
    
    TTL = {
        'position': 300,
        'aspects': 900,
        'rahu_kala': 86400,
        'dasha': 86400,
        'full_state': 3600
    }
    
    async def get_planet_position(
        self,
        planet: str,
        timestamp: datetime
    ) -> Optional[PlanetPosition]:
        time_bucket = self._get_time_bucket(timestamp, bucket_size_min=5)
        key = self.KEY_PATTERNS['position'].format(
            date=timestamp.date(),
            time_bucket=time_bucket,
            planet=planet
        )
        
        cached = await self.redis.get(key)
        if cached:
            self.metrics.increment('cache_hit', tags={'type': 'position'})
            return PlanetPosition.from_json(cached)
        
        self.metrics.increment('cache_miss', tags={'type': 'position'})
        return None
```

### 2.3 Cache Invalidation Strategy

**Trigger Conditions:**
1. Ephemeris file update (manual admin action)
2. Manual invalidation via API endpoint
3. TTL expiration (automatic)
4. Circuit breaker activation (safety)

**Invalidation Process:**
```python
class CacheInvalidator:
    async def invalidate_all(self, reason: str):
        await self.redis.delete_pattern('navagraha:*')
        
        await self.event_bus.publish('cache.invalidated', {
            'timestamp': datetime.utcnow(),
            'reason': reason
        })
        
        await self.recalculate_all()
    
    async def invalidate_time_range(
        self,
        start: datetime,
        end: datetime
    ):
        keys_to_delete = []
        async for key in self.redis.scan_iter('navagraha:*'):
            if self._is_in_range(key, start, end):
                keys_to_delete.append(key)
        
        if keys_to_delete:
            await self.redis.delete(*keys_to_delete)
```

### 2.4 Cache Warming Strategy

**On Startup:**
```python
async def warm_cache_on_startup():
    now = datetime.utcnow()
    
    for hours_ahead in range(24):
        future_time = now + timedelta(hours=hours_ahead)
        await navagraha_service.calculate_and_cache(future_time)
    
    logger.info("Cache warmed with 24 hours of ephemeris data")
```

**Scheduled Pre-calculation:**
```python
@scheduler.scheduled_job('cron', hour='*/6')
async def refresh_cache():
    now = datetime.utcnow()
    for hours_ahead in range(6):
        future_time = now + timedelta(hours=hours_ahead)
        await navagraha_service.calculate_and_cache(future_time)
```

---

## 3. Circuit Breaker Architecture

### 3.1 Circuit Breaker States

```
```
                    ┌──────────┐
                    │  CLOSED  │ (Normal operation)
                    │          │
                    └────┬─────┘
                         │
                         │ Failure threshold exceeded
                         │ (3 failures in 30s)
                         ▼
                    ┌──────────┐
              ┌────▶│   OPEN   │ (Blocking calls)
              │     │          │
              │     └────┬─────┘
              │          │
              │          │ Timeout expires (60s)
              │          ▼
              │     ┌──────────┐
              │     │ HALF-OPEN│ (Testing recovery)
              │     │          │
              │     └────┬─────┘
              │          │
              │          ├──▶ Success → CLOSED
              │          │
              └──────────┘ Failure → OPEN
```
```

### 3.2 Circuit Breaker Implementation

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Callable
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 1
    ):
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        self.half_open_call_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.metrics = PrometheusMetrics()
    
    async def call(self, func: Callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_call_count = 0
                self.metrics.set_gauge(
                    f'circuit_breaker_state',
                    1,
                    {'name': self.name, 'state': 'half_open'}
                )
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name} is OPEN"
                )
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_call_count >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name} max half-open calls exceeded"
                )
            self.half_open_call_count += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.metrics.set_gauge(
                f'circuit_breaker_state',
                0,
                {'name': self.name, 'state': 'closed'}
            )
        
        self.failure_count = 0
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.metrics.increment(
            'circuit_breaker_failures',
            tags={'name': self.name}
        )
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.metrics.set_gauge(
                f'circuit_breaker_state',
                2,
                {'name': self.name, 'state': 'open'}
            )
    
    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        
        elapsed = datetime.utcnow() - self.last_failure_time
        return elapsed.total_seconds() >= self.timeout_seconds
```

### 3.3 Circuit Breaker Cascade Strategy

```python
class CircuitBreakerManager:
    def __init__(self):
        self.breakers = {
            'swiss_ephemeris': CircuitBreaker('swiss_ephemeris', failure_threshold=3, timeout_seconds=60),
            'exchange_api': CircuitBreaker('exchange_api', failure_threshold=5, timeout_seconds=30),
            'llm_provider': CircuitBreaker('llm_provider', failure_threshold=3, timeout_seconds=120),
            'sentiment_api': CircuitBreaker('sentiment_api', failure_threshold=5, timeout_seconds=60),
            'database': CircuitBreaker('database', failure_threshold=2, timeout_seconds=10),
        }
    
    async def call_with_fallback(
        self,
        primary_service: str,
        fallback_service: Optional[str],
        func: Callable,
        *args,
        **kwargs
    ):
        try:
            breaker = self.breakers[primary_service]
            return await breaker.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            if fallback_service:
                logger.warning(
                    f"{primary_service} circuit open, using fallback: {fallback_service}"
                )
                fallback_breaker = self.breakers[fallback_service]
                return await fallback_breaker.call(func, *args, **kwargs)
            raise
```

### 3.4 Service-Specific Circuit Breaker Policies

**Swiss Ephemeris Service:**
```python
class NavagrahaService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            'swiss_ephemeris',
            failure_threshold=3,
            timeout_seconds=60
        )
        self.cache = NavagrahaCache()
    
    async def get_current_state(self) -> NavagrahaState:
        try:
            return await self.circuit_breaker.call(
                self._calculate_ephemeris
            )
        except CircuitBreakerOpenError:
            cached_state = await self.cache.get_last_known_good(
                max_age_minutes=60
            )
            
            if cached_state:
                logger.warning("Using cached ephemeris data due to circuit breaker")
                return cached_state
            else:
                raise EphemerisServiceDegradedError(
                    "Circuit breaker open and no cached data available"
                )
```

**Exchange API Service:**
```python
class ExchangeService:
    def __init__(self):
        self.primary_breaker = CircuitBreaker('exchange_api_primary', failure_threshold=5)
        self.backup_breaker = CircuitBreaker('exchange_api_backup', failure_threshold=3)
    
    async def place_order(self, order: Order) -> ExecutionResult:
        try:
            return await self.primary_breaker.call(
                self._place_order_primary,
                order
            )
        except CircuitBreakerOpenError:
            logger.warning("Primary exchange circuit open, using backup")
            return await self.backup_breaker.call(
                self._place_order_backup,
                order
            )
```

**LLM Provider Chain:**
```python
class LLMService:
    async def call_with_fallback(self, prompt: str) -> str:
        providers = ['ollama', 'gemini', 'deepseek']
        
        for provider in providers:
            breaker = self.breakers[provider]
            try:
                return await breaker.call(
                    self._call_provider,
                    provider,
                    prompt
                )
            except (CircuitBreakerOpenError, LLMProviderError):
                logger.warning(f"{provider} unavailable, trying next")
                continue
        
        raise LLMExhaustedError("All LLM providers failed or circuit open")
```

---

## 4. Performance Optimization Architecture

### 4.1 Latency Budgets (SLAs)

| Component | P50 | P95 | P99 | Timeout |
|-----------|-----|-----|-----|---------|
| Ephemeris Calculation | 50ms | 100ms | 150ms | 500ms |
| Redis Cache Lookup | 1ms | 5ms | 10ms | 50ms |
| OODA Observe Phase | 100ms | 200ms | 300ms | 1000ms |
| OODA Orient Phase | 50ms | 100ms | 150ms | 500ms |
| OODA Decide Phase | 150ms | 300ms | 500ms | 2000ms |
| OODA Act Phase | 200ms | 400ms | 800ms | 3000ms |
| Full OODA Cycle | 500ms | 1000ms | 1500ms | 5000ms |
| Order Execution | 100ms | 300ms | 500ms | 2000ms |
| WebSocket Broadcast | 10ms | 50ms | 100ms | 500ms |

### 4.2 Parallelization Strategy

```python
class OptimizedOODACoordinator:
    async def run_cycle(self) -> CycleResult:
        async with self.metrics.timer('ooda_cycle_duration'):
            observations = await self._observe()
            
            orientation, guna_update = await asyncio.gather(
                self._orient(observations),
                self._update_guna(observations.navagraha_state)
            )
            
            agent_tasks = [
                self.ether_agent.decide(observations, orientation),
                self.air_agent.decide(observations, orientation),
                self.fire_agent.decide(observations, orientation),
                self.water_agent.decide(observations, orientation),
                self.earth_agent.decide(observations, orientation),
            ]
            
            agent_decisions = await asyncio.gather(*agent_tasks)
            
            decision = self._aggregate_decisions(
                agent_decisions,
                guna_ratios=orientation.guna_ratios
            )
            
            execution_result = await self._act(decision)
            
            return CycleResult(
                decision=decision,
                execution=execution_result,
                cycle_duration_ms=self.metrics.get_timer_value('ooda_cycle_duration')
            )
```

### 4.3 Database Query Optimization

```python
class OptimizedMarketDataRepository:
    async def get_latest_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[OHLCV]:
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = $1 AND timeframe = $2
            ORDER BY timestamp DESC
            LIMIT $3
        """
        
        cache_key = f"ohlcv:{symbol}:{timeframe}:{limit}"
        
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        result = await self.db.fetch(query, symbol, timeframe, limit)
        
        await self.redis.setex(
            cache_key,
            60,
            json.dumps([dict(r) for r in result])
        )
        
        return result
```

---

## 5. Monitoring & Observability Integration

### 5.1 Key Metrics

```python
class SystemMetrics:
    NAVAGRAHA_METRICS = [
        'navagraha_calculation_duration_seconds',
        'navagraha_cache_hit_rate',
        'navagraha_state_age_seconds',
        'rahu_kala_gate_blocks_total',
    ]
    
    OODA_METRICS = [
        'ooda_cycle_duration_seconds{phase="observe|orient|decide|act"}',
        'ooda_cycles_total{status="success|failure"}',
        'agent_decision_latency_seconds{agent="ether|air|fire|water|earth"}',
    ]
    
    EXECUTION_METRICS = [
        'orders_placed_total{exchange="binance|bybit"}',
        'order_fill_latency_seconds',
        'circuit_breaker_state{service="..."}',
    ]
```

### 5.2 Health Check Endpoints

```python
@app.get("/health")
async def health_check():
    checks = await asyncio.gather(
        check_redis(),
        check_postgres(),
        check_ephemeris(),
        check_exchanges(),
        return_exceptions=True
    )
    
    all_healthy = all(c.status == "healthy" for c in checks if not isinstance(c, Exception))
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 6. Deployment Architecture

### 6.1 Service Topology

```
```
┌────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Backend API │  │ NavagrahaCalc│  │   WebSocket  │    │
│  │  (FastAPI)   │  │   Service    │  │   Gateway    │    │
│  │  Replicas: 3 │  │  Replicas: 2 │  │  Replicas: 2 │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                  │                  │            │
│         └──────────────────┴──────────────────┘            │
│                            │                                │
│                    ┌───────▼────────┐                      │
│                    │  Redis Cluster │                      │
│                    │   (Cache + PS) │                      │
│                    └────────────────┘                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  PostgreSQL  │  │  ClickHouse  │  │  Prometheus  │    │
│  │  (Primary)   │  │  (Analytics) │  │  (Metrics)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└────────────────────────────────────────────────────────────┘
```
```

---

## Conclusion

This architecture provides:
✅ **Immutable NavagrahaState** threading through all layers  
✅ **3-tier caching** with 95%+ hit rate target  
✅ **Circuit breakers** with fallback chains  
✅ **Sub-second OODA cycles** via parallelization  
✅ **Production-grade observability** with Prometheus/Grafana  
✅ **Horizontal scalability** via Kubernetes deployment