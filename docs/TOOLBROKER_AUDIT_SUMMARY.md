# ToolBroker Audit & PRD - Samenvatting

> **Agentic Trader Platform V18**
> **Volledige Scheiding van SanskritiSetu**
> **Datum**: 22 Februari 2026

---

## 1. Documentatie Deliverables

De volgende documenten zijn aangemaakt als onderdeel van deze audit:

### 1.1 Architecture Audit
**File**: `docs/TOOLBROKER_ARCHITECTURE_AUDIT.md`
**Omvang**: ~20,000 woorden
**Doel**: Volledige architecturale analyse en transformatieplan

**Inhoud**:
- Executive Summary met doelstellingen
- Huidige V17 architectuur analyse
- Doelarchitectuur (ToolBroker + MCP)
- Migratie strategie (V17 → ToolBroker)
- Data modellen en schemas
- API endpoint specificaties
- Implementatie roadmap (6 sprints)
- Technische specificaties
- Test strategie
- Risico's & mitigaties

### 1.2 Product Requirements Document (PRD)
**File**: `docs/PRD_TOOLBROKER_V18.md`
**Omvang**: ~23,000 woorden
**Doel**: Gedetailleerde functionele en non-functionele requirements

**Inhoud**:
- Document control & stakeholders
- Problem statement & solution
- 40+ Functionele Requirements (FR-001 t/m FR-040)
- 30+ Non-Functionele Requirements (NFR-001 t/m NFR-040)
- User Interface Requirements (API specs)
- Data Requirements (config & database)
- Implementation Plan (5 sprints)
- Test Plan met test cases
- Appendix met glossary & references

### 1.3 Implementation Guide
**File**: `docs/TOOLBROKER_IMPLEMENTATION_GUIDE.md`
**Omrang**: ~38,000 woorden
**Doel**: Stap-voor-stap technische implementatie

**Inhoud**:
- Quick start checklist
- Project structuur
- 9 implementatiestappen met complete code:
  1. Basis structuur
  2. Exceptions
  3. Schemas (Pydantic)
  4. Circuit Breaker
  5. Retry Engine
  6. Tool Registry
  7. Core ToolBroker
  8. API Endpoints
  9. Integratie in Main App
- Testing instructies
- Volgende stappen

---

## 2. Key Architectural Decisions

### 2.1 Volledige Scheiding van SanskritiSetu
| Aspect | Beslissing | Rationale |
|--------|-----------|-----------|
| Code overname | **VERBODEN** | Geen directe copy-paste uit SanskritiSetu |
| Concept gebruik | **TOEGESTAAN** | Begrijp de patronen, herbouw voor trading context |
| Inspiratie bron | SanskritiSetu ToolBroker | Bewijs dat architectuur werkt |
| Implementatie | Volledig custom | Eigen controle, eigen codebase |

### 2.2 MCP Protocol als Standaard
```
Voordelen:
✅ Industrie adoptie (Anthropic, OpenAI)
✅ LLM-gestuurde orkestratie mogelijk
✅ Externe tools eenvoudig te integreren
✅ JSON-RPC standaard
✅ Future-proof
```

### 2.3 Behoud V17 Financiële Logica
Alle financiële constraints blijven 100% behouden:
```python
# Behouden uit V17
MAX_POSITION_EUR = 2000.0          # €2k cap
MAX_HOLD_DAYS = 60                  # 60-day failsafe
TRAILING_STOP_THRESHOLD = 0.40      # +40% peak
TRAILING_STOP_DISTANCE = 0.15       # -15% drop = exit
COMMISSION_PCT = 0.0005             # 0.05% commission
SLIPPAGE_PCT = 0.001                # 0.1% slippage
```

---

## 3. Transformatie: V17 → V18

### 3.1 Huidige V17 Flow
```
BacktestEngine
  └── VedAstroElementalAgentV17
       ├── VedAstro (hardcoded call)
       ├── FireAgent (hardcoded call)
       ├── EarthAgent (hardcoded call)
       └── WaterAgent (hardcoded call)
```

### 3.2 Nieuwe V18 Flow
```
BacktestEngineV18
  └── ToolBroker
       ├── vedastro__generate_signal (MCP tool)
       ├── elemental__fire_position_size (MCP tool)
       ├── elemental__earth_entry_check (MCP tool)
       ├── elemental__water_regime_check (MCP tool)
       └── elemental__ether_consensus (MCP tool)
```

### 3.3 Tool Mapping
| V17 Component | V18 Tool | Prioriteit |
|--------------|----------|------------|
| `VedAstroElementalAgentV17.evaluate_entry()` | `vedastro__generate_signal` | P0 |
| `FireAgentV17.calculate_position_size()` | `elemental__fire_position_size` | P0 |
| `EarthAgentV17.should_enter()` | `elemental__earth_entry_check` | P0 |
| `EarthAgentV17.check_trailing_stop()` | `elemental__earth_exit_check` | P0 |
| `WaterAgentV12.get_macro_signal()` | `elemental__water_regime_check` | P0 |
| `Ether consensus logic` | `elemental__ether_consensus` | P0 |
| Data fetching | `data__get_historical_prices` | P0 |
| Portfolio status | `data__get_portfolio_status` | P0 |
| Paper trading | `execution__execute_paper_trade` | P0 |

---

## 4. Componenten Overzicht

### 4.1 Core ToolBroker (`backend/core/tool_broker/`)
| Component | Bestand | Omschrijving |
|-----------|---------|--------------|
| Broker | `broker.py` | Centrale router en orchestrator |
| Circuit Breaker | `circuit_breaker.py` | Failure isolatie state machine |
| Retry Engine | `retry.py` | Exponential backoff met jitter |
| Registry | `registry.py` | Tool registratie en discovery |
| Schemas | `schemas.py` | Pydantic models |
| Exceptions | `exceptions.py` | Custom exception hierarchy |
| Metrics | `metrics.py` | Prometheus metrics verzameling |
| MCP Adapter | `mcp_adapter.py` | JSON-RPC protocol handling |

### 4.2 Tools (`backend/tools/`)
| Server | Tools | V17 Equivalent |
|--------|-------|----------------|
| VedAstro | `generate_signal`, `get_dasha`, `get_transits` | VedAstroElementalAgentV17 |
| Elemental | `fire_position_size`, `earth_entry_check`, `water_regime_check`, `earth_exit_check`, `ether_consensus` | Fire/Earth/Water Agents |
| Data | `get_historical_prices`, `get_portfolio_status` | Directe data calls |
| Execution | `execute_paper_trade`, `get_open_positions` | Paper exchange adapter |

---

## 5. Resilience Configuratie

### 5.1 Circuit Breaker
```yaml
failure_threshold: 5           # Open na 5 failures
failure_window_seconds: 60     # In 60 seconden window
timeout_seconds: 30            # 30s timeout per call
reset_timeout_seconds: 60      # Na 60s proberen te herstellen
half_open_requests: 3          # Max 3 requests in half-open
```

### 5.2 Retry
```yaml
max_attempts: 3                # Max 3 pogingen
initial_delay_ms: 100          # Start met 100ms
max_delay_ms: 10000            # Max 10 seconden
backoff_factor: 2.0            # 100ms → 200ms → 400ms
jitter_enabled: true           # +10% random voor thundering herd preventie
```

---

## 6. API Endpoints

### 6.1 Core Endpoints
```http
POST   /api/v1/tools/execute        # Tool executie
GET    /api/v1/tools/list           # Tool discovery
GET    /api/v1/tools/health         # Health check
GET    /api/v1/tools/metrics        # Resilience metrics
GET    /api/v1/tools/circuit-breakers  # Circuit states
```

### 6.2 MCP Protocol Endpoints
```http
POST   /api/v1/mcp/initialize       # MCP initialize
POST   /api/v1/mcp/tools/list       # MCP tools/list
POST   /api/v1/mcp/tools/call       # MCP tools/call
```

---

## 7. Implementatie Roadmap

### Fase 1: Fundament (Week 1)
- [ ] ToolBroker module structuur
- [ ] Base classes implementeren
- [ ] Circuit breaker & retry
- [ ] Unit tests (100% coverage)

### Fase 2: MCP Protocol (Week 2)
- [ ] MCP server mode
- [ ] MCP client mode
- [ ] Protocol compliance tests

### Fase 3: V17 Migration (Week 3)
- [ ] VedAstro tools
- [ ] Elemental tools
- [ ] Data & Execution tools

### Fase 4: BacktestEngine Refactor (Week 4)
- [ ] BacktestEngineV18
- [ ] ToolBroker integratie
- [ ] Performance benchmarks

### Fase 5: Monitoring & Release (Week 5)
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Chaos tests
- [ ] Documentatie

---

## 8. Success Metrics

| Metric | V17 (Current) | V18 (Target) |
|--------|---------------|--------------|
| Tool isolation | 0% | 100% |
| Failure cascade prevention | No | Yes |
| New tool integration | Days | Minutes |
| Backtest completion | 95% | 99.5% |
| Circuit breaker coverage | 0% | 100% |
| Retry capability | 0% | 100% |

---

## 9. Risico's & Mitigatie

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| Performance regressie | Hoog | Medium | Benchmarks, local mode voor hot path |
| VedAstro integratie | Medium | Hoog | Stapsgewijze migratie, fallback behouden |
| MCP overhead | Medium | Medium | Local mode, protocol optimalisatie |
| Scope creep | Hoog | Medium | Strict P0/P1/P2, 5-sprint limiet |
| Test coverage | Medium | Medium | 100% unit test requirement |

---

## 10. Conclusie

De ToolBroker-architectuur transformeert de Agentic Trader Platform van een statisch, hardcoded systeem naar een dynamisch, modulair, en schaalbaar ecosysteem.

### Voordelen
1. **LLM Orkestratie**: Tools kunnen door LLM's worden gecombineerd
2. **Failure Isolatie**: Circuit breakers voorkaan cascading failures
3. **Uitbreidbaarheid**: Nieuwe tools zonder code changes
4. **Standaardisatie**: MCP protocol = industrie compatibel
5. **Robuustheid**: Retry, timeouts, graceful degradation

### Volgende Actie
Start **Fase 1: Fundament** implementatie volgens `TOOLBROKER_IMPLEMENTATION_GUIDE.md`.

---

**Documentatie Set**:
1. `TOOLBROKER_ARCHITECTURE_AUDIT.md` - Architectuur analyse
2. `PRD_TOOLBROKER_V18.md` - Requirements document
3. `TOOLBROKER_IMPLEMENTATION_GUIDE.md` - Implementatie guide
4. `TOOLBROKER_AUDIT_SUMMARY.md` - Deze samenvatting

**Totale Documentatie**: ~81,000 woorden
**Status**: ✅ READY FOR IMPLEMENTATION

---

*Audit Completed*: 2026-02-22
*Auditor*: Code Architect
*Review Status*: Final
