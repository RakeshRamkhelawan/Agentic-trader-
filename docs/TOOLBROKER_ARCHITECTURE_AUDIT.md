# ToolBroker Architectuur Audit & Integratie Plan

> **Volledige Scheiding van SanskritiSetu** | **Agentic Trader Platform V18**

---

## 1. Executive Summary

### 1.1 Doelstelling
Transformeer de huidige V17 "statische" Elemental Engine naar een dynamische, modulaire **ToolBroker-architectuur** gebaseerd op het **Model Context Protocol (MCP)**. Dit maakt:

- **LLM-gestuurde orkestratie** in plaats van hardcoded flows
- **Plug-and-play uitbreiding** met externe tools (sentiment, macro, etc.)
- **Isolatie van failures** via circuit breakers
- **Standaardisatie** volgens industrie-norm (Anthropic/OpenAI compatible)

### 1.2 Scope
| In Scope | Out of Scope |
|----------|-------------|
| ToolBroker core implementatie | SanskritiSetu-specifieke business logic |
| MCP protocol adapter | Serena/Sequential Thinking integratie |
| V17 Elemental Agents als tools | UI/Frontend wijzigingen (apart traject) |
| VedAstro als MCP-server | Andere projecten (SanskritiSetu) |
| Paper Trading als MCP-client | |

### 1.3 Belangrijkste Principes
1. **Zero-Copy Philosophy**: Geen directe code overname uit SanskritiSetu
2. **Concept Inspiratie**: Begrijp de patronen, herbouw voor trading context
3. **V17 Behoud**: Alle financiële logica (€2k cap, 60-day failsafe, etc.) blijft intact
4. **MCP Standaard**: JSON-RPC berichten voor alle tool communicatie

---

## 2. Huidige V17 Architectuur Analyse

### 2.1 Flow Diagram (Huidig)
```
┌─────────────────────────────────────────────────────────────┐
│                    BacktestEngine                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FOR day IN backtest_period:                       │   │
│  │    1. Call VedAstro.analyze_asset()                │   │
│  │    2. IF signal == BUY:                            │   │
│  │         Call FireAgent.calculate_position_size()   │   │
│  │         Call EarthAgent.should_enter()             │   │
│  │         Call WaterAgent.get_macro_signal()         │   │
│  │    3. IF all_pass: Execute Trade                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Problemen met Huidige Architectuur
| Probleem | Impact | Oplossing via ToolBroker |
|----------|--------|-------------------------|
| Strakke koppeling | V17 crasht als één agent faalt | Circuit breaker isolatie |
| Statische flow | Kan alleen hardcoded sequenties uitvoeren | LLM-gestuurde orkestratie |
| Geen externe tools | Sentiment/macro toevoegen = code wijzigen | MCP server registratie |
| Moeilijk te testen | Alles is interne methods | Tools zijn aparte units |
| Geen resilience | Timeout = crash | Retry + circuit breaker |

### 2.3 Te Behouden V17 Logica
```python
# FINANCIELE CONSTRAINTS (100% behouden)
MAX_POSITION_EUR = 2000.0          # €2k cap per positie
MAX_HOLD_DAYS = 60                  # 60-day failsafe
TRAILING_STOP_THRESHOLD = 0.40      # +40% → trailing stop active
TRAILING_STOP_DISTANCE = 0.15       # -15% van peak = exit

# VEDASTRO INTEGRATIE (behouden)
MIN_VEDASTRO_CONFIDENCE = 50.0
MIN_VEDASTRO_SCORE = 45.0

# ELEMENTAL AGENTS (als tools herstructureerd)
- FireAgentV17.calculate_position_size() → tool_fire_position_size
- EarthAgentV17.should_enter() → tool_earth_entry_check
- WaterAgentV12.get_macro_signal() → tool_water_regime_check
- EarthAgentV17.check_trailing_stop() → tool_earth_exit_check
```

---

## 3. Doelarchitectuur: ToolBroker + MCP

### 3.1 Conceptuele Flow (Nieuw)
```
┌─────────────────────────────────────────────────────────────────────┐
│                     LLM Orchestrator (DeepSeek/Claude)              │
│  "Analyseer AAPL voor vandaag, check VedAstro dasha,               │
│   vraag Elemental consensus, bepaal of we moeten hedgen"           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ JSON-RPC (MCP)
┌─────────────────────────────────────────────────────────────────────┐
│                         ToolBroker (Central Hub)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Router    │  │   Circuit   │  │    Retry    │  │  Metrics   │ │
│  │             │  │  Breaker    │  │   Engine    │  │   & Logs   │ │
│  └──────┬──────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────┼───────────────────────────────────────────────────────────┘
          │
    ┌─────┴─────┬─────────────┬─────────────┬─────────────┐
    ▼           ▼             ▼             ▼             ▼
┌───────┐  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│VedAstro│  │Elemental│  │  Data    │  │Execution │  │  Risk    │
│  MCP   │  │  MCP    │  │   MCP    │  │   MCP    │  │   MCP    │
│Server  │  │ Server  │  │  Server  │  │  Server  │  │  Server  │
└───────┘  └────────┘  └──────────┘  └──────────┘  └──────────┘
```

### 3.2 Componenten Breakdown

#### 3.2.1 ToolBroker Core (`backend/core/tool_broker/`)
| Component | Verantwoordelijkheid | SanskritiSetu Inspiratie |
|-----------|---------------------|-------------------------|
| `broker.py` | Centrale router, tool registratie | service.py concept |
| `circuit_breaker.py` | Failure isolatie, state machine | resilience.py pattern |
| `retry.py` | Exponential backoff, jitter | RetryConfig concept |
| `mcp_adapter.py` | JSON-RPC protocol handling | mcp_client.py protocol |
| `registry.py` | Tool discovery & metadata | local_registry.py concept |
| `schemas.py` | Pydantic models voor requests/responses | schemas.py pattern |

#### 3.2.2 MCP Servers (Lokaal of Extern)
| Server | Tools | V17 Equivalent |
|--------|-------|----------------|
| **VedAstro MCP** | `get_dasha`, `get_transits`, `generate_signal` | VedAstroElementalAgentV17 |
| **Elemental MCP** | `fire_position_size`, `earth_entry_check`, `water_regime`, `ether_consensus` | Fire/Earth/Water Agents |
| **Data MCP** | `get_historical_prices`, `get_portfolio_status`, `get_market_regime` | Directe data calls |
| **Execution MCP** | `execute_paper_trade`, `get_open_positions`, `close_position` | Paper exchange adapter |
| **Risk MCP** | `calculate_var`, `stress_test`, `kelly_optimize` | Risk engine |

#### 3.2.3 Resilience Layer
```python
# Circuit Breaker States
CLOSED   → Normal operation, requests pass through
OPEN     → Service failing, requests rejected immediately  
HALF_OPEN → Testing recovery, limited requests allowed

# Retry Config
max_attempts: int = 3
initial_delay_ms: int = 100
max_delay_ms: int = 10000
backoff_factor: float = 2.0
jitter_enabled: bool = True
```

---

## 4. Migratie Strategie: V17 → ToolBroker

### 4.1 Fase 1: Tool Identificatie
Elke huidige V17 methode wordt een tool:

```python
# HUIDIG (V17)
class VedAstroElementalAgentV17:
    async def evaluate_entry(self, symbol, price, date, portfolio) -> Optional[Dict]:
        # ... complexe logica
        return entry_dict

# NIEUW (ToolBroker)
# Tool: vedastro__evaluate_entry
@tool_registry.register(
    name="vedastro__evaluate_entry",
    description="Evaluate entry opportunity using VedAstro analysis",
    parameters={
        "symbol": {"type": "string", "required": True},
        "current_price": {"type": "number", "required": True},
        "portfolio_value": {"type": "number", "required": True}
    }
)
async def tool_vedastro_evaluate_entry(params: Dict) -> Dict:
    # Zelfde logica, andere interface
    pass
```

### 4.2 Fase 2: Tool Implementaties

#### Tool 1: VedAstro Signal Generator
```python
# backend/tools/vedastro/signal_generator.py
class VedAstroSignalTool:
    """Generates BUY/SELL/HOLD signals from astrological data"""
    
    async def execute(self, symbol: str, current_price: float) -> Dict:
        # 1. Get cached or fresh VedAstro analysis
        # 2. Apply TradingSignalGenerator
        # 3. Return structured signal
        return {
            "signal": "BUY",  # of SELL/HOLD
            "confidence": 75.5,
            "strength_score": 68.0,
            "dasha_context": "Jupiter Mahadasha...",
            "primary_factors": ["Strong Gaja Kesari Yoga"],
            "risk_level": "medium"
        }
```

#### Tool 2: Fire Position Sizing
```python
# backend/tools/elemental/fire_agent.py
class FirePositionSizeTool:
    """Calculates position size based on volatility and VedAstro score"""
    
    MAX_POSITION_EUR = 2000.0  # Behouden uit V17
    
    async def execute(self, symbol: str, portfolio_value: float, 
                      vedastro_score: float, dominant_planet: str) -> Dict:
        # V17 logica exact behouden
        position_size = self._calculate_v17_logic(...)
        return {
            "position_size_eur": position_size,
            "max_allowed": self.MAX_POSITION_EUR,
            "harmony_factor": 0.85,
            "planet_multiplier": 1.2
        }
```

#### Tool 3: Earth Entry Check
```python
# backend/tools/elemental/earth_agent.py
class EarthEntryCheckTool:
    """Checks if entry is allowed (3-loss rule)"""
    
    async def execute(self, symbol: str, trade_history: List[Dict]) -> Dict:
        # V17: 3 consecutive losses = block entry
        recent_losses = self._count_recent_losses(symbol, trade_history)
        return {
            "can_enter": recent_losses < 3,
            "reason": "3 consecutive losses" if recent_losses >= 3 else None,
            "recent_loss_count": recent_losses
        }
```

### 4.3 Fase 3: BacktestEngine Refactor
```python
# HUIDIG
class BacktestEngine:
    def __init__(self):
        self.elemental_agent = VedAstroElementalAgentV17()
    
    async def run(self):
        for day in dates:
            entry = await self.elemental_agent.evaluate_entry(...)

# NIEUW
class BacktestEngineV18:
    def __init__(self, tool_broker: ToolBroker):
        self.broker = tool_broker
    
    async def run(self):
        for day in dates:
            # Via ToolBroker - volledige decoupling
            entry = await self.broker.execute_tool(
                "vedastro__evaluate_entry",
                {"symbol": "AAPL", "current_price": price, ...}
            )
```

---

## 5. Data Modellen (Schemas)

### 5.1 Core Schemas
```python
# backend/core/tool_broker/schemas.py

class ToolExecutionRequest(BaseModel):
    tool_name: str  # format: "server__tool_name"
    params: Dict[str, Any]
    timeout_seconds: Optional[int] = 30
    request_id: Optional[str] = None

class ToolExecutionResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: float
    circuit_breaker_state: Optional[str]  # closed/open/half_open
    retry_count: int = 0

class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class ResilienceMetrics(BaseModel):
    total_calls: int
    successful_calls: int
    failed_calls: int
    circuit_breaker_opens: int
    average_latency_ms: float
```

### 5.2 Trading-Specifieke Schemas
```python
# backend/tools/schemas/trading.py

class VedAstroSignalResult(BaseModel):
    signal: Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
    confidence: float  # 0-100
    strength_score: float  # 0-100
    dasha_context: str
    primary_factors: List[str]
    risk_level: Literal["low", "medium", "high"]
    recommended_timeframe: str

class ElementalConsensusResult(BaseModel):
    harmony_score: float  # 0-1
    fire_vote: float
    earth_vote: float  
    water_vote: float
    approved: bool  # harmony > 0.45
    blocking_reasons: List[str]

class PositionSizingResult(BaseModel):
    position_size_eur: float
    max_position_eur: float = 2000.0
    position_pct_of_portfolio: float
    sizing_factors: Dict[str, float]
```

---

## 6. API Endpoints

### 6.1 ToolBroker Endpoints
```python
# backend/api/toolbroker_api.py

router = APIRouter(prefix="/v1/tools", tags=["ToolBroker"])

@router.post("/execute")
async def execute_tool(request: ToolExecutionRequest) -> ToolExecutionResponse:
    """Execute any registered tool with resilience"""
    pass

@router.get("/list")
async def list_tools() -> List[ToolInfo]:
    """List all available tools with schemas"""
    pass

@router.get("/resilience/status")
async def get_resilience_status() -> ResilienceStatus:
    """Get circuit breaker states and metrics"""
    pass

@router.get("/health")
async def health_check() -> HealthCheckResponse:
    """Check ToolBroker and all registered servers"""
    pass
```

### 6.2 MCP Server Endpoints (voor externe communicatie)
```python
# MCP protocol endpoints voor externe LLM clients

@router.post("/mcp/initialize")
async def mcp_initialize() -> MCPInitializeResponse:
    """MCP protocol initialization"""
    pass

@router.post("/mcp/tools/list")
async def mcp_list_tools() -> MCPToolsListResponse:
    """MCP protocol tools/list method"""
    pass

@router.post("/mcp/tools/call")
async def mcp_call_tool(request: MCPToolCallRequest) -> MCPToolCallResponse:
    """MCP protocol tools/call method"""
    pass
```

---

## 7. Implementatie Roadmap

### Fase 1: Fundament (Week 1)
- [ ] `backend/core/tool_broker/` structuur aanmaken
- [ ] Base ToolBroker class implementeren
- [ ] Circuit breaker implementatie
- [ ] Retry engine met exponential backoff
- [ ] Pydantic schemas definiëren

### Fase 2: MCP Protocol (Week 1-2)
- [ ] MCP adapter implementeren
- [ ] JSON-RPC request/response handling
- [ ] Tool discovery mechanism
- [ ] Server registratie systeem

### Fase 3: V17 Tools Migratie (Week 2-3)
- [ ] VedAstro tools packageren als MCP server
- [ ] Elemental agents converteren naar tools
- [ ] Data/Execution tools implementeren
- [ ] Risk tools integreren

### Fase 4: BacktestEngine Refactor (Week 3)
- [ ] BacktestEngine omzetten naar ToolBroker client
- [ ] Alle directe calls vervangen door broker.execute_tool()
- [ ] Test suite uitbreiden voor nieuwe architectuur

### Fase 5: Resilience & Monitoring (Week 4)
- [ ] Circuit breaker monitoring dashboard
- [ ] Metrics verzameling (Prometheus)
- [ ] Health checks implementeren
- [ ] Chaos tests (failure injectie)

### Fase 6: Documentatie & Release (Week 4)
- [ ] API documentatie
- [ ] Architecture Decision Records (ADRs)
- [ ] Migration guide voor ontwikkelaars
- [ ] V18 release

---

## 8. Technische Specificaties

### 8.1 Dependencies
```txt
# requirements/toolbroker.txt
# Core
pydantic>=2.0.0
fastapi>=0.104.0

# MCP Protocol
mcp>=1.0.0  # Model Context Protocol SDK

# Resilience
tenacity>=8.0.0  # Retry logic (optioneel, kan ook custom)

# Async
anyio>=4.0.0

# Observability
prometheus-client>=0.19.0
opentelemetry-api>=1.21.0
```

### 8.2 Configuratie
```yaml
# config/toolbroker.yaml
tool_broker:
  # Resilience
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
  
  # MCP Servers
  servers:
    vedastro:
      type: local
      module: backend.tools.vedastro
      enabled: true
    
    elemental:
      type: local
      module: backend.tools.elemental
      enabled: true
    
    # Externe MCP servers (voorbeeld)
    sentiment:
      type: mcp
      command: npx
      args: ["-y", "@modelcontextprotocol/server-sentiment"]
      enabled: false  # Future expansion
```

### 8.3 Error Handling Strategy
```python
class ToolBrokerException(Exception):
    """Base exception"""
    pass

class CircuitBreakerOpenException(ToolBrokerException):
    """Circuit breaker is open"""
    pass

class ToolExecutionException(ToolBrokerException):
    """Tool execution failed"""
    def __init__(self, tool_name: str, error_detail: str, original_error: Exception = None):
        self.tool_name = tool_name
        self.error_detail = error_detail
        self.original_error = original_error

class ToolNotFoundException(ToolBrokerException):
    """Tool not in registry"""
    pass

class MCPConnectionError(ToolBrokerException):
    """MCP server connection failed"""
    pass
```

---

## 9. Test Strategie

### 9.1 Unit Tests
```python
# Test circuit breaker state transitions
def test_circuit_opens_after_threshold_failures():
    pass

def test_circuit_half_open_recovery():
    pass

# Test retry logic
def test_retry_exhaustion():
    pass

def test_retry_success_on_second_attempt():
    pass
```

### 9.2 Integration Tests
```python
# Test complete tool execution flow
async def test_vedastro_tool_execution():
    broker = ToolBroker()
    result = await broker.execute_tool("vedastro__get_signal", {"symbol": "AAPL"})
    assert result.success

# Test failure isolation
async def test_elemental_failure_doesnt_affect_vedastro():
    pass
```

### 9.3 Chaos Tests
```python
# Test resilience under failure
async def test_graceful_degradation_when_vedastro_down():
    pass

async def test_circuit_breaker_prevents_cascading_failure():
    pass
```

---

## 10. Risico's & Mitigaties

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| Performance regressie | Hoog | Medium | Benchmark V17 vs V18, optimize hot path |
| VedAstro integratie complexiteit | Medium | Hoog | Stapsgewijze migratie, behoud oude als fallback |
| MCP protocol overhead | Medium | Medium | Local mode voor kritieke tools, MCP voor externe |
| Circuit breaker te agressief | Hoog | Low | Tune thresholds, monitoring alerts |
| Data inconsistency | Hoog | Medium | Transactie wrapper, idempotency keys |

---

## 11. Conclusie

De ToolBroker-architectuur transformeert de Agentic Trader Platform van een statisch, hardcoded systeem naar een dynamisch, modulair ecosysteem. Belangrijkste voordelen:

1. **Flexibiliteit**: LLM's kunnen zelfstandig tools orkestreren
2. **Robuustheid**: Circuit breakers en retry logic isoleren failures
3. **Uitbreidbaarheid**: Nieuwe tools via MCP registreren, geen code changes
4. **Testbaarheid**: Elke tool is een geïsoleerde unit
5. **Standaardisatie**: MCP protocol = compatibel met industrie tools

**Volgende Stap**: Fase 1 implementatie starten met `backend/core/tool_broker/` structuur.

---

*Document Versie: 1.0*  
*Laatste Update: 2026-02-22*  
*Status: READY FOR IMPLEMENTATION*
