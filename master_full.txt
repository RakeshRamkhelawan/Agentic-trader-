# Samkhya Yoga Agentic Trader — Master Kanban TDD Planning

> **Versie**: 2.0 — 14 februari 2026
> **Status**: Actief — 7 fasen, 29 taken, ~180 microtaken
> **Methodologie**: TDD (Red-Green-Refactor) + Integration Tests op productie-code
> **Bronnen**: [Blueprint](../../HANDOVER_CONTEXT.md) | [Audit Report](../reports/EPIC_01_CODE_REVIEW.md)

---

## Inhoudsopgave

1. [Architectuur Overzicht](#architectuur-overzicht)
2. [Fase-documenten Index](#fase-documenten-index)
3. [Prioriteitsmatrix](#prioriteitsmatrix)
4. [Kanban Board — Alle Fasen](#kanban-board)
5. [Dependencies Graph](#dependencies-graph)
6. [Test Strategie](#test-strategie)
7. [Codebase Referenties](#codebase-referenties)
8. [Beslissingen Log](#beslissingen-log)

---

## Architectuur Overzicht

```
Market Data (Exchange/CCXT)
│
▼
[1] CognitiveBridge (backend/core/adapters/system_bridge.py:18)
│   ★ FASE 1: + NavagrahaEngine.assess()
│
▼
[2] SystemIdentity (backend/core/system_identity.py:25)
│   36-Tattva Traversal: Ascend→Filter→Interface→Sense→Decide→Act→Materialize→Descend
│   ★ FASE 1: + navagraha_state.guna_modulation pre-Ascend
│
▼
[3] OODALoopCoordinator (backend/orchestration/ooda_coordinator.py:47)
│   OBSERVE → ORIENT → DECIDE → HARMONIZE → ACT
│   ★ FASE 1: + ElementalSynthesis in ORIENT
│   ★ FASE 1: + Rahu Kala gate in DECIDE
│   ★ FASE 1: + Planetary harmony in HARMONIZE
│
├── Elemental Agents (backend/agents/elemental_*.py)
│   ★ FASE 1: + Graha-Prana binding
│
├── ★ NIEUW: Navagraha Layer (backend/core/navagraha/)
│   EphemerisCalculator | NakshatraCalculator | VimshottariDasha
│   AspectAnalyzer | RahuKalaCalculator | HoraCalculator
│
▼
[4] Execution (backend/execution/)
    CCXTAdapter | OrderExecutor | SmartOrderRouter
    ★ FASE 4: + WebSocket streams, backtesting
```

---

## Fase-documenten Index

| Fase | Document | Prioriteit | Taken | Status |
|------|----------|-----------|-------|--------|
| **Fase 1** | [FASE_01_CONSCIOUSNESS_OODA_NAVAGRAHA_BRIDGE.md](./FASE_01_CONSCIOUSNESS_OODA_NAVAGRAHA_BRIDGE.md) | 🔴 CRITICAL | 9 taken, ~65 microtaken | ⬜ Not Started |
| **Fase 2** | [FASE_02_SECURITY_IAM.md](./FASE_02_SECURITY_IAM.md) | 🔴 P0 | 3 taken, ~24 microtaken | ⬜ Not Started |
| **Fase 3** | [FASE_03_INFRASTRUCTURE.md](./FASE_03_INFRASTRUCTURE.md) | 🔴 P0 | 3 taken, ~22 microtaken | ⬜ Not Started |
| **Fase 4** | [FASE_04_BROKER_BACKTESTING.md](./FASE_04_BROKER_BACKTESTING.md) | 🟡 P1 | 3 taken, ~20 microtaken | ⬜ Not Started |
| **Fase 5** | [FASE_05_FRONTEND_MVP.md](./FASE_05_FRONTEND_MVP.md) | 🟡 P1 | 4 taken, ~18 microtaken | ⬜ Not Started |
| **Fase 6** | [FASE_06_AUTONOMOUS_SELF_LEARNING.md](./FASE_06_AUTONOMOUS_SELF_LEARNING.md) | 🟢 P2 | 3 taken, ~16 microtaken | ⬜ Not Started |
| **Fase 7** | [FASE_07_PRODUCTION_HARDENING.md](./FASE_07_PRODUCTION_HARDENING.md) | 🟢 P2 | 4 taken, ~15 microtaken | ⬜ Not Started |

---

## Prioriteitsmatrix

```
Impact ▲
       │
  HIGH │  FASE 1 (Bridge)     FASE 4 (Brokers)
       │  FASE 2 (Security)   FASE 5 (Frontend)
       │  FASE 3 (Infra)
       │
  MED  │                      FASE 6 (Autonomy)
       │                      FASE 7 (Hardening)
       │
  LOW  │
       └──────────────────────────────────────► Effort
           LOW        MEDIUM         HIGH
```

**Kritiek pad**: Fase 1 → Fase 3 → Fase 4 → Fase 7
**Parallel pad**: Fase 2 (kan parallel met Fase 1), Fase 5 (kan parallel met Fase 4)

---

## Kanban Board

### 🔴 Fase 1: Consciousness-OODA-Navagraha Bridge

| ID | Taak | Afhankelijk van | Status |
|----|------|-----------------|--------|
| 1.1 | Navagraha Pydantic Modellen + Engine Scaffold | — | ⬜ |
| 1.2 | EphemerisCalculator (Kerykeion/pyswisseph) | 1.1 | ⬜ |
| 1.3 | NakshatraCalculator + VimshottariDasha | 1.2 | ⬜ |
| 1.4 | AspectAnalyzer + RahuKala + Hora | 1.2 | ⬜ |
| 1.5 | GrahaGunaMapper | 1.2, 1.3, 1.4 | ⬜ |
| 1.6 | NavagrahaEngine Orchestrator | 1.5 | ⬜ |
| 1.7 | Wire into CognitiveBridge + SystemIdentity | 1.6 | ⬜ |
| 1.8 | Wire into OODALoopCoordinator | 1.6, 1.7 | ⬜ |
| 1.9 | Wire ElementalAgents Graha-Prana + Prana Lifecycle | 1.6 | ⬜ |

### 🔴 Fase 2: Security & IAM

| ID | Taak | Afhankelijk van | Status |
|----|------|-----------------|--------|
| 2.1 | OAuth2/OIDC Middleware + JWT Validation | — | ⬜ |
| 2.2 | Multi-Tenant Isolation (ClickHouse + ChromaDB) | 2.1 | ⬜ |
| 2.3 | Vault Secret Provider + Key Rotation | 2.1 | ⬜ |

### 🔴 Fase 3: Infrastructure

| ID | Taak | Afhankelijk van | Status |
|----|------|-----------------|--------|
| 3.1 | Kubernetes Manifests + Helm Charts | — | ⬜ |
| 3.2 | Multi-Stage Dockerfiles + Ephemeris Bundling | 1.6 | ⬜ |
| 3.3 | Prometheus Navagraha Metrics + Grafana Dashboards | 1.6 | ⬜ |

### 🟡 Fase 4: Broker Expansion & Backtesting

| ID | Taak | Afhankelijk van | Status |
|----|------|-----------------|--------|
| 4.1 | CCXT WebSocket + Multi-Exchange | 1.8 | ⬜ |
| 4.2 | BacktestExchangeAdapter + Navagraha Replay | 1.6, 4.1 | ⬜ |
| 4.3 | SocialSentimentHarvester (5e Tanmatra) | 1.8 | ⬜ |

### 🟡 Fase 5: Frontend MVP

| ID | Taak | Afhankelijk van | Status |
|----|------|-----------------|--------|
| 5.1 | Mahabhutas Coherence Visualisatie | 1.9 | ⬜ |
| 5.2 | Navagraha Dashboard Component | 1.6, 3.3 | ⬜ |
| 5.3 | Trading Console + Circuit Breaker UI | 1.8 | ⬜ |
| 5.4 | Decision Explainability Panel | 1.8, 5.2 | ⬜ |

### 🟢 Fase 6: Autonomous Self-Learning

| ID | Taak | Afhankelijk van | Status |
|----|------|-----------------|--------|
| 6.1 | Feedback Loop (Karma) — MemorySystem | 1.7 | ⬜ |
| 6.2 | OODA Scheduler + Dasha-Aware Cycling | 1.6, 6.1 | ⬜ |
| 6.3 | Viveka Learning — Buddhi Self-Correction | 6.1, 6.2 | ⬜ |

### 🟢 Fase 7: Production Hardening

| ID | Taak | Afhankelijk van | Status |
|----|------|-----------------|--------|
| 7.1 | MiFID II Audit Logging + NavagrahaState | 1.6 | ⬜ |
| 7.2 | LLM Token Tracking + Billing | 2.1 | ⬜ |
| 7.3 | Model Fallback Logic (DeepSeek→Gemini→Ollama) | — | ⬜ |
| 7.4 | Stub Services Expansion (risk_engine, market_data) | 1.8 | ⬜ |

---

## Dependencies Graph

```
Fase 1.1 ──► 1.2 ──► 1.3
                 ├──► 1.4
                 └──► 1.5 ──► 1.6 ──┬──► 1.7 ──► 1.8
                                     │              │
                                     ├──► 1.9       │
                                     │              │
                                     ├──► 3.2       │
                                     ├──► 3.3       │
                                     ├──► 7.1       │
                                     │              │
                                     │         ┌────┘
                                     │         ▼
Fase 2.1 ──► 2.2                     │    4.1 ──► 4.2
         └──► 2.3                    │         └──► 4.3
         └──► 7.2                    │
                                     │    5.1 ◄── 1.9
Fase 3.1 (standalone)                │    5.2 ◄── 1.6 + 3.3
                                     │    5.3 ◄── 1.8
                                     │    5.4 ◄── 1.8 + 5.2
                                     │
                                     └──► 6.1 ──► 6.2 ──► 6.3
                                               7.3 (standalone)
                                               7.4 ◄── 1.8
```

---

## Test Strategie

### TDD Workflow per Microtaak

```
1. RED   — Schrijf failing test (happy + unhappy path)
2. GREEN — Implementeer minimale code om test te laten slagen
3. REFACTOR — Clean up, DRY, docstrings
4. VERIFY — Run alle tests in de module
```

### Test Niveaus per Taak

| Niveau | Wat | Waar | Wanneer |
|--------|-----|------|---------|
| **Unit Test** | Individuele functie/methode | `backend/tests/unit/` | Elke microtaak |
| **Happy Path** | Correcte input → verwacht resultaat | Per microtaak | Verplicht |
| **Unhappy Path** | Foute input, edge cases, exceptions | Per microtaak | Verplicht |
| **Integratie Test** | Meerdere componenten samen | `backend/tests/integration/` | Na elke taak-afronding |
| **Productie Test** | Tegen echte services (exchange, DB) | `backend/tests/e2e/` | Na elke fase-afronding |

### Test Naming Convention

```python
# Unit tests
def test_{functie}_{scenario}_returns_{verwacht}():      # Happy
def test_{functie}_{fout_scenario}_raises_{exception}():  # Unhappy

# Integratie tests
async def test_integration_{taak_id}_{flow}_end_to_end():

# Productie tests
async def test_production_{fase}_{component}_live():
```

### Cruciale Test Invarianten

1. **Rahu is ALTIJD retrograde** — elke test die `GrahaPosition` voor Rahu maakt moet `retrograde=True` asserteren
2. **Guna vector som ≠ 1.0** — Gunas zijn onafhankelijke dimensies, NIET percentages
3. **NavagrahaState.positions bevat exact 9 entries** — altijd alle 9 grahas
4. **Rahu Kala duurt ~1.5 uur** — nooit langer dan 2 uur, nooit korter dan 1 uur
5. **Nakshatra index altijd 0-26** — 27 nakshatras
6. **Pada altijd 1-4** — exact 4 padas per nakshatra
7. **Planetary positions 0°-360°** — siderische absolute longitude
8. **Prana altijd 0-100** — nooit negatief, nooit boven max
9. **Circuit breaker = fail-safe** — als Fire agent prana=0, blokkeer executie

---

## Codebase Referenties

### Bestaande Bestanden (Exact paths + line counts)

| Bestand | Pad | Regels | Hoofdklasse |
|---------|-----|--------|-------------|
| OODA Coordinator | `backend/orchestration/ooda_coordinator.py` | 530 | `OODALoopCoordinator` |
| Cognitive Orchestrator | `backend/services/cognitive_orchestrator.py` | 511 | `CognitiveOrchestrator` |
| Orchestrator Agent | `backend/agents/orchestrator_agent.py` | 119 | `OrchestratorAgent` |
| Base Agent | `backend/agents/base_agent.py` | 188 | `BaseAgent(ABC)` |
| DataScout Agent | `backend/agents/data_scout_agent.py` | 288 | `DataScoutAgent` |
| Risk Manager Agent | `backend/agents/risk_manager_agent.py` | 221 | `RiskManagerAgent` |
| System Bridge | `backend/core/adapters/system_bridge.py` | 184 | `CognitiveBridge` |
| System Identity | `backend/core/system_identity.py` | 595 | `SystemIdentity` |
| Sensory Processor | `backend/core/sensory_processor.py` | 144 | `SensoryProcessor` |
| Decision Discriminator | `backend/core/decision_discriminator.py` | 236 | `DecisionDiscriminator` |
| Memory System | `backend/core/memory_system.py` | 246 | `MemorySystem` |
| Intent Monitor | `backend/services/intent_monitor.py` | 53 | `IntentMonitor` |
| Elemental Base | `backend/agents/elemental_base.py` | 192 | `ElementalBase(ABC)` |
| Elemental Router | `backend/agents/elemental_router.py` | 73 | `ElementalRouter` |
| Elemental Ether | `backend/agents/elemental_orchestrator.py` | 175 | `ElementalOrchestrator` |
| Elemental Air | `backend/agents/elemental_research.py` | 131 | `ElementalResearch` |
| Elemental Fire | `backend/agents/elemental_risk_guardian.py` | 131 | `ElementalRiskGuardian` |
| Elemental Water | `backend/agents/elemental_macro.py` | 116 | `ElementalMacro` |
| Elemental Earth | `backend/agents/elemental_valuation.py` | 133 | `ElementalValuation` |
| CCXT Adapter | `backend/execution/ccxt_adapter.py` | 425 | `CCXTAdapter` |
| Order Executor | `backend/execution/order_executor.py` | 400 | `OrderExecutor` |
| Smart Order Router | `backend/execution/smart_order_router.py` | 268 | `SmartOrderRouter` |
| Stress Tester | `backend/risk/stress_tester.py` | 173 | `StressTestSuite` |
| Kelly Criterion | `backend/risk/kelly_criterion.py` | 178 | `KellyCriterion` |
| VaR Calculator | `backend/risk/var_calculator.py` | 51 | `VaRCalculator` |
| OODA Types | `backend/core/schemas/ooda_types.py` | 358 | Pydantic models |
| Settings | `backend/core/config/settings.py` | 135 | `Settings` |
| Auth Middleware | `backend/core/auth/middleware.py` | 131 | `AuthMiddleware` |
| API Main | `backend/api/main.py` | 191 | FastAPI app |
| API Gateway | `backend/api/gateway.py` | 372 | `APIGateway` |
| Auth API | `backend/api/auth_api.py` | 313 | Auth routes |

### Nieuw Te Creëren Bestanden

| Pad | Fase | Beschrijving |
|-----|------|--------------|
| `backend/core/navagraha/__init__.py` | 1.1 | Package init |
| `backend/core/navagraha/models.py` | 1.1 | Pydantic modellen |
| `backend/core/navagraha/engine.py` | 1.6 | NavagrahaEngine orchestrator |
| `backend/core/navagraha/ephemeris.py` | 1.2 | EphemerisCalculator |
| `backend/core/navagraha/nakshatra.py` | 1.3 | NakshatraCalculator |
| `backend/core/navagraha/dasha.py` | 1.3 | VimshottariDasha |
| `backend/core/navagraha/aspects.py` | 1.4 | AspectAnalyzer |
| `backend/core/navagraha/rahu_kala.py` | 1.4 | RahuKalaCalculator |
| `backend/core/navagraha/hora.py` | 1.4 | HoraCalculator |
| `backend/core/navagraha/graha_guna_mapper.py` | 1.5 | GrahaGunaMapper |
| `backend/tests/unit/test_navagraha_models.py` | 1.1 | Model tests |
| `backend/tests/unit/test_ephemeris.py` | 1.2 | Ephemeris tests |
| `backend/tests/unit/test_nakshatra.py` | 1.3 | Nakshatra tests |
| `backend/tests/unit/test_dasha.py` | 1.3 | Dasha tests |
| `backend/tests/unit/test_aspects.py` | 1.4 | Aspect tests |
| `backend/tests/unit/test_rahu_kala.py` | 1.4 | Rahu Kala tests |
| `backend/tests/unit/test_hora.py` | 1.4 | Hora tests |
| `backend/tests/unit/test_graha_guna_mapper.py` | 1.5 | Guna mapping tests |
| `backend/tests/unit/test_navagraha_engine.py` | 1.6 | Engine tests |
| `backend/tests/integration/test_ooda_navagraha.py` | 1.8 | OODA+Navagraha integratie |
| `backend/tests/integration/test_elemental_graha.py` | 1.9 | Elemental+Graha integratie |

---

## Beslissingen Log

| # | Beslissing | Rationale | Fase |
|---|-----------|-----------|------|
| D1 | Kashmir Shaivism 36-Tattva (niet Samkhya 25) | Codebase implementeert al 36 lagen | Architectuur |
| D2 | OODA + Elemental + Navagraha triple-track | Elk systeem voegt unieke informatie toe | 1 |
| D3 | Prana als circuit breaker signal | Fire agent fail-safe patroon als template | 1 |
| D4 | Tamas-aware scheduling | Reduceer frequentie bij lage volatiliteit | 6 |
| D5 | Memory-first over model-first | Buddhi's Vasana detectie vóór LLM consultatie | 6 |
| D6 | Real ephemeris (Kerykeion+pyswisseph) | NASA JPL DE431, geen mocks | 1 |
| D7 | Grahas moduleren Gunas, niet buy/sell | Samkhya: bewustzijn verlicht, Prakrti handelt | 1 |
| D8 | System "birth" = deployment time | Vimshottari Dasha op eerste deployment Moon | 1 |

---

> **Volgende stap**: Begin met [Fase 1](./FASE_01_CONSCIOUSNESS_OODA_NAVAGRAHA_BRIDGE.md) — het fundament waar alle andere fasen op bouwen.
