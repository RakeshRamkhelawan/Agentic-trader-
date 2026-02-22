# Product Requirements Document (PRD)
# ToolBroker V18 - MCP-Enabled Trading Architecture

> **Project**: Agentic Trader Platform V18  
> **Feature**: ToolBroker Integration  
> **Status**: Draft → Ready for Development  
> **Priority**: P0 (Critical Path)

---

## 1. Document Control

### 1.1 Version History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-02-22 | Code Architect | Initial draft based on SanskritiSetu audit |
| 0.2 | 2026-02-22 | Code Architect | Added V17 migration specifics |
| 1.0 | 2026-02-22 | Code Architect | Final PRD ready for implementation |

### 1.2 Stakeholders
| Role | Name | Responsibility |
|------|------|----------------|
| Product Owner | System Architect | Feature acceptance |
| Tech Lead | Senior Developer | Implementation review |
| QA Lead | Test Engineer | Test strategy approval |
| DevOps | Infrastructure | Deployment & monitoring |

---

## 2. Overview

### 2.1 Problem Statement
De huidige V17 architectuur heeft strak gekoppelde agents die direct method calls uitvoeren. Dit resulteert in:
- **Cascading failures**: Als VedAstro crasht, crasht de hele backtest
- **Inflexibiliteit**: Nieuwe tools toevoegen vereist code wijzigingen
- **Moeilijke testing**: Agents zijn niet geïsoleerd testbaar
- **Geen LLM orkestratie**: Statische for-loops in plaats van intelligente routing

### 2.2 Solution
Implementeer een **ToolBroker** als centrale hub die:
1. Alle functionaliteit exposeert als **tools** (MCP protocol)
2. **Circuit breakers** gebruikt voor failure isolatie
3. **Retry logic** met exponential backoff toepast
4. **LLM's** tools laat orkestreren via JSON-RPC

### 2.3 Success Criteria
| Metric | Current (V17) | Target (V18) | Measurement |
|--------|---------------|--------------|-------------|
| Tool execution isolation | None | 100% | Chaos tests |
| New tool integration time | Days | Minutes | Time to register |
| Failure cascade prevention | No | Yes | Circuit breaker tests |
| Backtest completion rate | 95% | 99.5% | Production runs |
| Average tool latency | N/A | <100ms | Prometheus metrics |

---

## 3. Functional Requirements

### 3.1 Core ToolBroker (FR-001 t/m FR-010)

#### FR-001: Tool Registration
**Description**: Het systeem moet tools kunnen registreren met metadata

**Acceptance Criteria**:
```python
# Given een tool definitie
@tool_registry.register(
    name="vedastro__get_signal",
    description="Generate trading signal from astrological data",
    version="1.0.0",
    parameters={
        "symbol": {"type": "string", "required": True},
        "current_price": {"type": "number", "required": True}
    },
    returns={
        "signal": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
        "confidence": {"type": "number", "min": 0, "max": 100}
    }
)

# When de broker start
broker = ToolBroker()

# Then moet de tool beschikbaar zijn
assert "vedastro__get_signal" in broker.list_tools()
```

**Priority**: P0

---

#### FR-002: Tool Execution
**Description**: Het systeem moet tools kunnen uitvoeren met resilience

**Acceptance Criteria**:
```python
# Given een geregistreerde tool
broker = ToolBroker()

# When de tool wordt aangeroepen
result = await broker.execute_tool(
    tool_name="vedastro__get_signal",
    params={"symbol": "AAPL", "current_price": 185.50}
)

# Then moet het resultaat correct zijn
assert result.success is True
assert "signal" in result.data
assert result.execution_time_ms < 1000
```

**Priority**: P0

---

#### FR-003: Circuit Breaker Protection
**Description**: Tools moeten beschermd zijn door circuit breakers

**Acceptance Criteria**:
- Na 5 failures in 60 seconden → circuit opent
- Bij open circuit → instant rejection met duidelijke error
- Na 60 seconden → half-open, test request toegestaan
- Na 2 successen in half-open → circuit sluit

**Test Scenario**:
```python
# Given een falende tool
for i in range(5):
    with pytest.raises(ToolExecutionException):
        await broker.execute_tool("failing_tool", {})

# When we nog een request doen
with pytest.raises(CircuitBreakerOpenException):
    await broker.execute_tool("failing_tool", {})

# Then moet de circuit breaker open zijn
assert broker.get_circuit_state("failing_tool") == CircuitState.OPEN
```

**Priority**: P0

---

#### FR-004: Retry with Exponential Backoff
**Description**: Gefaalde tools moeten automatisch retry'en

**Acceptance Criteria**:
- Max 3 retry attempts
- Delay: 100ms → 200ms → 400ms
- Jitter: ±10% random toevoeging
- Alleen retry bij transient errors

**Priority**: P0

---

#### FR-005: Tool Discovery
**Description**: Clients moeten beschikbare tools kunnen ontdekken

**Acceptance Criteria**:
```python
tools = await broker.list_tools()
# Returns:
[
    {
        "name": "vedastro__get_signal",
        "description": "Generate trading signal from astrological data",
        "parameters": {...},
        "returns": {...},
        "circuit_state": "closed"
    }
]
```

**Priority**: P1

---

#### FR-006: Health Monitoring
**Description**: De broker moet health status kunnen rapporteren

**Acceptance Criteria**:
```python
health = await broker.get_health()
# Returns:
{
    "status": "healthy",  # of "degraded", "unhealthy"
    "components": {
        "vedastro_mcp": "operational",
        "elemental_mcp": "operational",
        "circuit_breaker": "operational"
    },
    "metrics": {
        "total_calls": 15000,
        "success_rate": 0.987,
        "average_latency_ms": 45
    }
}
```

**Priority**: P1

---

### 3.2 MCP Protocol Support (FR-011 t/m FR-020)

#### FR-011: MCP Server Mode
**Description**: De ToolBroker moet als MCP server kunnen fungeren

**Acceptance Criteria**:
- Ondersteun `initialize` request
- Ondersteun `tools/list` request
- Ondersteun `tools/call` request
- JSON-RPC 2.0 compliant

**Priority**: P1

---

#### FR-012: MCP Client Mode
**Description**: De ToolBroker moet externe MCP servers kunnen benaderen

**Acceptance Criteria**:
```python
# Register external MCP server
broker.register_mcp_server(
    name="sentiment_analysis",
    command="npx",
    args=["-y", "@mcp/sentiment-server"]
)

# Call tool on external server
result = await broker.execute_tool(
    "sentiment_analysis__analyze",
    {"text": "Bitcoin is going to the moon!"}
)
```

**Priority**: P2

---

### 3.3 V17 Compatibility (FR-021 t/m FR-030)

#### FR-021: VedAstro Tool
**Description**: VedAstro analyse moet als tool beschikbaar zijn

**Tool Specification**:
```yaml
tool_name: vedastro__generate_signal
parameters:
  symbol: string (required)
  current_price: number (required)
  birth_date: string (optional, ISO format)
returns:
  signal: enum [STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL]
  confidence: number (0-100)
  strength_score: number (0-100)
  dasha_context: string
  primary_factors: array[string]
  risk_level: enum [low, medium, high]
  recommended_action: string
```

**Priority**: P0

---

#### FR-022: Fire Position Sizing Tool
**Description**: Fire agent positie sizing als tool

**Tool Specification**:
```yaml
tool_name: elemental__fire_position_size
parameters:
  symbol: string (required)
  portfolio_value: number (required)
  vedastro_score: number (required, 0-100)
  dominant_planet: string (required)
  price_history: array[number] (optional)
returns:
  position_size_eur: number
  max_position_eur: number (always 2000)
  position_pct: number
  sizing_factors:
    volatility: number
    harmony: number
    planet_multiplier: number
```

**Constraints (V17 behoud)**:
- MAX_POSITION_EUR = 2000.0
- Max 2% van portfolio per positie

**Priority**: P0

---

#### FR-023: Earth Entry Check Tool
**Description**: Earth agent entry blocking als tool

**Tool Specification**:
```yaml
tool_name: elemental__earth_entry_check
parameters:
  symbol: string (required)
  trade_history: array[object] (required)
    - pnl: number
    - win: boolean
    - timestamp: string
returns:
  can_enter: boolean
  blocking_reason: string (nullable)
  recent_loss_count: integer
  consecutive_losses: integer
```

**Constraints (V17 behoud)**:
- 3 consecutive losses = block entry

**Priority**: P0

---

#### FR-024: Water Regime Check Tool
**Description**: Water agent macro regime als tool

**Tool Specification**:
```yaml
tool_name: elemental__water_regime_check
parameters:
  symbol: string (required)
  prices: array[number] (required, min 20 items)
returns:
  regime: enum [expansion, contraction, recovery, neutral]
  risk_on_score: number (0-1)
  hedge_signal:
    symbol: string (nullable)
    confidence: number (0-1)
```

**Priority**: P0

---

#### FR-025: Earth Exit Check Tool
**Description**: Earth agent exit criteria als tool

**Tool Specification**:
```yaml
tool_name: elemental__earth_exit_check
parameters:
  symbol: string (required)
  entry_date: string (required, ISO format)
  current_date: string (required, ISO format)
  entry_price: number (required)
  current_price: number (required)
  peak_price: number (required)
returns:
  should_exit: boolean
  exit_reason: string (nullable)
  days_held: integer
  pnl_pct: number
  trailing_stop_active: boolean
```

**Constraints (V17 behoud)**:
- MAX_HOLD_DAYS = 60
- Trailing stop: +40% peak → -15% drop = exit

**Priority**: P0

---

#### FR-026: Ether Consensus Tool
**Description**: Ether agent voor consensus synthesizing

**Tool Specification**:
```yaml
tool_name: elemental__ether_consensus
parameters:
  fire_vote: number (required, 0-1)
  earth_vote: number (required, 0-1)
  water_vote: number (required, 0-1)
  air_vote: number (required, 0-1)
returns:
  harmony_score: number (0-1)
  approved: boolean (harmony > 0.45)
  elemental_breakdown:
    fire: number
    earth: number
    water: number
    air: number
  dominant_element: string
```

**Priority**: P0

---

### 3.4 Data & Execution Tools (FR-031 t/m FR-040)

#### FR-031: Historical Data Tool
**Description**: Ophalen van historische prijsdata

**Tool Specification**:
```yaml
tool_name: data__get_historical_prices
parameters:
  symbol: string (required)
  start_date: string (required, ISO format)
  end_date: string (required, ISO format)
  timeframe: enum [1m, 5m, 1h, 1d] (default: 1d)
returns:
  data: array[object]
    - timestamp: string
    - open: number
    - high: number
    - low: number
    - close: number
    - volume: number
```

**Priority**: P0

---

#### FR-032: Portfolio Status Tool
**Description**: Huidige portfolio status ophalen

**Tool Specification**:
```yaml
tool_name: data__get_portfolio_status
parameters:
  account_id: string (required)
returns:
  cash_eur: number
  total_value_eur: number
  open_positions: array[object]
    - symbol: string
    - quantity: number
    - entry_price: number
    - current_price: number
    - unrealized_pnl: number
  daily_pnl: number
  total_pnl: number
```

**Priority**: P0

---

#### FR-033: Execute Paper Trade Tool
**Description**: Paper trade executie

**Tool Specification**:
```yaml
tool_name: execution__execute_paper_trade
parameters:
  symbol: string (required)
  action: enum [BUY, SELL] (required)
  quantity: number (required)
  order_type: enum [MARKET, LIMIT] (default: MARKET)
  limit_price: number (optional)
returns:
  order_id: string
  status: enum [FILLED, PARTIAL, REJECTED]
  filled_quantity: number
  filled_price: number
  commission: number
  timestamp: string
```

**Constraints**:
- Max position size: €2,000
- Commission: 0.05%
- Slippage: 0.1%

**Priority**: P0

---

## 4. Non-Functional Requirements

### 4.1 Performance (NFR-001 t/m NFR-010)

#### NFR-001: Tool Execution Latency
**Requirement**: 95th percentile < 100ms voor lokale tools
**Measurement**: Prometheus histogram `tool_execution_duration_seconds`
**Target**: bucket_100ms > 0.95

#### NFR-002: Throughput
**Requirement**: Minimaal 1000 tool calls per seconde
**Measurement**: Load test met Locust
**Target**: 1000 RPS met < 100ms latency

#### NFR-003: Circuit Breaker Response Time
**Requirement**: Circuit breaker decision < 1ms
**Measurement**: Interne timing
**Target**: < 1ms overhead

### 4.2 Reliability (NFR-011 t/m NFR-020)

#### NFR-011: Availability
**Requirement**: 99.9% uptime voor ToolBroker
**Measurement**: Health check probes
**Target**: < 0.1% error rate

#### NFR-012: Failure Isolation
**Requirement**: Eén failed tool mag andere tools niet beïnvloeden
**Measurement**: Chaos tests
**Target**: 100% isolation

#### NFR-013: Data Consistency
**Requirement**: Tool executions moeten idempotent zijn
**Measurement**: Retry tests
**Target**: Same result bij retry met zelfde parameters

### 4.3 Security (NFR-021 t/m NFR-030)

#### NFR-021: Authentication
**Requirement**: Alle tool calls vereisen JWT token
**Implementation**: FastAPI dependency injection

#### NFR-022: Authorization
**Requirement**: Scope-based toegang (`tool:execute`, `tool:read`)
**Implementation**: RBAC middleware

#### NFR-023: Input Validation
**Requirement**: Alle inputs gevalideerd via Pydantic
**Implementation**: Strict schema validation

### 4.4 Observability (NFR-031 t/m NFR-040)

#### NFR-031: Metrics
**Required Metrics**:
- `tool_calls_total` (counter, labels: tool_name, status)
- `tool_execution_duration_seconds` (histogram)
- `circuit_breaker_state` (gauge, labels: tool_name, state)
- `retry_attempts_total` (counter, labels: tool_name)

#### NFR-032: Logging
**Requirement**: Structured logging voor alle tool calls
**Format**: JSON met correlation_id, tool_name, duration, status

#### NFR-033: Tracing
**Requirement**: OpenTelemetry tracing voor end-to-end visibility
**Implementation**: Auto-instrumentatie van FastAPI

---

## 5. User Interface Requirements

### 5.1 API Endpoints

#### 5.1.1 Tool Execution
```http
POST /api/v1/tools/execute
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "tool_name": "vedastro__generate_signal",
  "params": {
    "symbol": "AAPL",
    "current_price": 185.50
  },
  "timeout_seconds": 30,
  "request_id": "req_12345"
}
```

Response:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "result": {
    "signal": "BUY",
    "confidence": 75.5,
    "strength_score": 68.0
  },
  "execution_time_ms": 45.2,
  "circuit_breaker_state": "closed",
  "retry_count": 0,
  "request_id": "req_12345"
}
```

#### 5.1.2 Tool List
```http
GET /api/v1/tools/list
Authorization: Bearer {jwt_token}
```

Response:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "tools": [
    {
      "name": "vedastro__generate_signal",
      "description": "Generate trading signal from astrological data",
      "parameters": {...},
      "returns": {...},
      "circuit_state": "closed"
    }
  ]
}
```

#### 5.1.3 Health Check
```http
GET /api/v1/tools/health
```

Response:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2026-02-22T10:30:00Z",
  "components": {
    "vedastro_mcp": "operational",
    "elemental_mcp": "operational",
    "circuit_breaker": "operational"
  }
}
```

---

## 6. Data Requirements

### 6.1 Configuration
```yaml
# config/toolbroker.yaml
tool_broker:
  # Resilience settings
  circuit_breaker:
    failure_threshold: 5
    failure_window_seconds: 60
    timeout_seconds: 30
    reset_timeout_seconds: 60
    half_open_requests: 3
  
  retry:
    max_attempts: 3
    initial_delay_ms: 100
    max_delay_ms: 10000
    backoff_factor: 2.0
    jitter_enabled: true
  
  # MCP server configurations
  mcp_servers:
    vedastro:
      type: local
      module: backend.tools.vedastro
      enabled: true
    
    elemental:
      type: local
      module: backend.tools.elemental
      enabled: true
    
    data:
      type: local
      module: backend.tools.data
      enabled: true
    
    execution:
      type: local
      module: backend.tools.execution
      enabled: true
```

### 6.2 Database Schema (voor tool execution logs)
```sql
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(200) NOT NULL,
    params JSONB,
    result JSONB,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    execution_time_ms FLOAT,
    circuit_breaker_state VARCHAR(20),
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    account_id UUID REFERENCES accounts(id)
);

CREATE INDEX idx_tool_executions_tool_name ON tool_executions(tool_name);
CREATE INDEX idx_tool_executions_created_at ON tool_executions(created_at);
CREATE INDEX idx_tool_executions_request_id ON tool_executions(request_id);
```

---

## 7. Implementation Plan

### 7.1 Sprint Breakdown

#### Sprint 1: Core Infrastructure (Week 1)
**Stories**:
- [TB-001] Set up `backend/core/tool_broker/` module structure
- [TB-002] Implement base ToolBroker class with registration
- [TB-003] Implement Circuit Breaker state machine
- [TB-004] Implement Retry engine with exponential backoff
- [TB-005] Define Pydantic schemas for requests/responses

**Definition of Done**:
- Unit tests for circuit breaker (100% coverage)
- Unit tests for retry logic (100% coverage)
- All code reviewed and merged

#### Sprint 2: MCP Protocol (Week 2)
**Stories**:
- [TB-006] Implement MCP server mode (JSON-RPC)
- [TB-007] Implement MCP client for external servers
- [TB-008] Tool discovery mechanism
- [TB-009] Health check endpoints

**Definition of Done**:
- MCP protocol compliance tests passing
- Integration tests with mock MCP servers

#### Sprint 3: V17 Tools Migration (Week 3)
**Stories**:
- [TB-010] Migrate VedAstro as MCP server
- [TB-011] Migrate Fire Agent as tool
- [TB-012] Migrate Earth Agent as tool
- [TB-013] Migrate Water Agent as tool
- [TB-014] Migrate Ether consensus as tool

**Definition of Done**:
- All V17 tools available via ToolBroker
- Backward compatibility tests passing

#### Sprint 4: BacktestEngine Integration (Week 4)
**Stories**:
- [TB-015] Refactor BacktestEngine to use ToolBroker
- [TB-016] Implement Data tools (historical prices, portfolio status)
- [TB-017] Implement Execution tools (paper trade)
- [TB-018] Update BacktestEngine tests

**Definition of Done**:
- Full backtest runs successfully with ToolBroker
- Performance benchmarks V17 vs V18

#### Sprint 5: Monitoring & Hardening (Week 5)
**Stories**:
- [TB-019] Prometheus metrics integration
- [TB-020] Structured logging
- [TB-021] OpenTelemetry tracing
- [TB-022] Chaos tests implementation
- [TB-023] Circuit breaker monitoring dashboard

**Definition of Done**:
- All metrics visible in Grafana
- Chaos tests passing
- Documentation complete

### 7.2 Dependencies
```
Sprint 1: None (greenfield)
Sprint 2: Depends on Sprint 1
Sprint 3: Depends on Sprint 2
Sprint 4: Depends on Sprint 3
Sprint 5: Depends on Sprint 4
```

### 7.3 Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Performance regressie | Benchmark V17 vs V18 voor elke sprint |
| VedAstro integratie complex | Fallback naar V17 implementatie behouden |
| MCP protocol overhead | Local mode voor kritieke tools |
| Scope creep | Strict P0/P1/P2 prioritering |

---

## 8. Test Plan

### 8.1 Test Levels

#### Unit Tests
- Circuit breaker state transitions
- Retry logic met verschillende scenarios
- Tool registratie en discovery
- Schema validatie

#### Integration Tests
- End-to-end tool execution flow
- MCP protocol compliance
- Database persistence
- Error handling en recovery

#### Chaos Tests
- Circuit breaker onder failure load
- Retry exhaustion scenarios
- Partial system failures
- Network latency simulation

### 8.2 Test Cases (voorbeelden)

#### TC-001: Circuit Breaker Opens After Threshold
```python
def test_circuit_opens_after_5_failures():
    broker = ToolBroker()
    
    # 5 failures triggeren
    for i in range(5):
        with pytest.raises(ToolExecutionException):
            await broker.execute_tool("failing_tool", {})
    
    # Circuit moet open zijn
    assert broker.get_circuit_state("failing_tool") == CircuitState.OPEN
    
    # Direct rejection
    with pytest.raises(CircuitBreakerOpenException):
        await broker.execute_tool("failing_tool", {})
```

#### TC-002: VedAstro Tool Returns Correct Schema
```python
async def test_vedastro_tool_returns_valid_signal():
    broker = ToolBroker()
    
    result = await broker.execute_tool(
        "vedastro__generate_signal",
        {"symbol": "AAPL", "current_price": 185.50}
    )
    
    assert result.success
    assert result.data["signal"] in ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
    assert 0 <= result.data["confidence"] <= 100
    assert 0 <= result.data["strength_score"] <= 100
```

#### TC-003: Fire Position Size Respects Constraints
```python
async def test_fire_position_size_respects_max():
    broker = ToolBroker()
    
    result = await broker.execute_tool(
        "elemental__fire_position_size",
        {
            "symbol": "AAPL",
            "portfolio_value": 100000,
            "vedastro_score": 80,
            "dominant_planet": "JUPITER"
        }
    )
    
    assert result.data["position_size_eur"] <= 2000.0
    assert result.data["max_position_eur"] == 2000.0
```

---

## 9. Appendix

### 9.1 Glossary
| Term | Definition |
|------|------------|
| MCP | Model Context Protocol - standaard voor LLM tool communicatie |
| Tool | Een geïsoleerde, herbruikbare functie met gedefinieerde input/output |
| Circuit Breaker | Pattern om failures te isoleren en cascading errors te voorkomen |
| Resilience | Vermogen van het systeem om te herstellen van failures |
| Orkestratie | Het coördineren van meerdere tools door een LLM |

### 9.2 References
- [SanskritiSetu ToolBroker Audit](./TOOLBROKER_ARCHITECTURE_AUDIT.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/specification)
- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
- [V17 Elemental Agents](../backend/agents/elemental_agent_manager_v17.py)

### 9.3 Decision Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-22 | Gebruik custom implementatie ipv SanskritiSetu copy | Volledige scheiding, eigen controle |
| 2026-02-22 | MCP protocol als standaard | Industrie adoptie, LLM compatibiliteit |
| 2026-02-22 | Local + Remote MCP servers | Flexibiliteit voor interne en externe tools |
| 2026-02-22 | Exponential backoff met jitter | Thundering herd preventie |

---

## 10. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Tech Lead | | | |
| QA Lead | | | |

---

*Document End*
