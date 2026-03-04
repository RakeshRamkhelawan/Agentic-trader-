# Unified Consciousness Integration

## Overview

De **Unified Consciousness Integration** consolideert alle 71 kern-modules van de Agentic Trader Platform in één coherent systeem. Het vervangt de 4 parallelle orchestrators (OODALoopCoordinator, CognitiveOrchestrator, ColdPathCoordinator, Phase12RealAgentCoordinator) met één unified "brein" waarbij OODA het primaire orchestratiepatroon is.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED CONSCIOUSNESS                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    OODALoopCoordinator (Primary Brain)           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │ OBSERVE │→│ ORIENT  │→│ DECIDE  │→│  ACT    │            │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │   │
│  │       ↑                                              ↓          │   │
│  │       └──────────────────────────────────────────────┘          │   │
│  │                           ↓                                     │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │              Unified Consciousness Components             │  │   │
│  │  ├──────────────────────────────────────────────────────────┤  │   │
│  │  │  • CognitiveOrchestrator (Message Bus & Guna Balance)    │  │   │
│  │  │  • NavagrahaService (Cosmic Time & Trading Gates)        │  │   │
│  │  │  • SystemIdentity (36-Tattva Consciousness)              │  │   │
│  │  │  • RiskOrchestrator (Kanchuka Risk Layer)                │  │   │
│  │  │  • KarmaRegister (Learning Feedback Loop)                │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Fases

### Fase A: Unify Orchestration ✅

**Doel:** Één "brein" dat alle agents aanstuurt.

**Wijzigingen:**
- `OODALoopCoordinator` is het primaire brein
- `CognitiveOrchestrator` is nu een dependency (message bus & guna balance)
- `ColdPathCoordinator` gemarkeerd als deprecated
- `Phase12RealAgentCoordinator` gemarkeerd als deprecated

**Key Files:**
- `backend/orchestration/ooda_coordinator.py` - Aangepast met unified consciousness dependencies

### Fase B: Connect Consciousness ✅

**Doel:** SystemIdentity (36-Tattva) en NavagrahaService beïnvloeden trade decisions.

**Features:**
- **Navagraha Pre-Check:** Trading gate controleert Rahu Kala en tamas niveau
- **Tattva Risk Gate:** Kanchuka layers (6-12) beïnvloeden position confidence
- **Guna Modulation:** Sattva/rajas/tamas verhouding beïnvloedt trade parameters

**Key Files:**
- `backend/core/navagraha/service.py` - Cosmic time service
- `backend/core/system_identity.py` - 36-Tattva consciousness

### Fase C: Wire Risk Pipeline ✅

**Doel:** 7 risk modules als Kanchuka-laag in OODA.

**Features:**
- `RiskOrchestrator.pre_trade_check()` toegevoegd aan `_decide()`
- VaR, Kelly Criterion, Drawdown Monitoring geïntegreerd
- Risk gates worden geëvalueerd vóór FundManager capital allocation

**Key Files:**
- `backend/risk/risk_orchestrator.py` - Central pre-trade validation
- `backend/orchestration/ooda_coordinator.py` - Risk integration in decide phase

### Fase D: Strategy Integration ✅

**Doel:** 6 strategy classes als plugins in OODA.

**Features:**
- `UnifiedStrategyRegistry` verbindt DashaStrategyMap met NavagrahaService
- TraderAgent accepteert strategy_registry parameter
- Dynamische strategy selectie gebaseerd op planetaire periodes

**Key Files:**
- `backend/core/strategy/unified_strategy_registry.py` - Strategy registry
- `backend/agents/trader_agent.py` - Strategy integration

### Fase E: Learning Loop ✅

**Doel:** Feedback van trades naar consciousness.

**Features:**
- Karma feedback loop na elke trade execution
- SystemIdentity.update_outcome() voor experience learning
- Reinforcement learning integratie

**Key Files:**
- `backend/core/karma/karma_register.py` - Karma tracking
- `backend/core/karma/reinforcement.py` - RL integration

### Fase F: Frontend Completeness ✅

**Doel:** Dashboard toont het unified systeem.

**Components:**
- `UnifiedConsciousnessDashboard` - Hoofd dashboard component
- `NavagrahaWheel` - Real-time planeetposities
- `RahuKalaGate` - Trading gate indicator
- `TattvaMonitor` - 36-Tattva traversal status
- `GunaDistribution` - Sattva/rajas/tamas donut chart
- `OODATransparency` - Live OODA cycle voortgang

**Key Files:**
- `frontend/src/components/dashboard/UnifiedConsciousnessDashboard.tsx`
- `frontend/src/components/dashboard/TattvaMonitor.tsx`
- `frontend/src/components/dashboard/GunaDistribution.tsx`
- `frontend/src/lib/stores/unifiedConsciousnessStore.ts`

## API Reference

### OODALoopCoordinator

```python
coordinator = OODALoopCoordinator(
    # Core agents
    data_scout=...,
    analyst=...,
    trader=...,
    risk_manager=...,
    # ...
    # Unified Consciousness Components (nieuw)
    cognitive_orchestrator=CognitiveOrchestrator(...),
    navagraha_service=NavagrahaService(...),
    system_identity=SystemIdentity(...),
    risk_orchestrator=RiskOrchestrator(...),
    karma_register=KarmaRegister(...),
)

# Run cycle met unified consciousness
result = await coordinator.run_cycle("BTC/USD", 50000.0)

# Get unified state
state = coordinator.get_unified_consciousness_state()
```

### Unified Strategy Registry

```python
from backend.core.strategy.unified_strategy_registry import UnifiedStrategyRegistry

registry = UnifiedStrategyRegistry(
    navagraha_service=navagraha_service,
)

# Get strategy based on current Dasha
strategy_id, strategy = await registry.get_strategy_for_current_dasha(
    lat=52.3676, lon=4.9041  # Amsterdam
)

# Analyze with Dasha-based strategy
intent = await registry.analyze_with_dasha_strategy(
    market_data={"price": 50000, "symbol": "BTC/USD"},
    soul_context={"confidence": 0.8},
)
```

## Frontend Usage

### UnifiedConsciousnessDashboard

```tsx
import { UnifiedConsciousnessDashboard } from '@/components/dashboard/UnifiedConsciousnessDashboard';
import { useUnifiedConsciousness } from '@/lib/stores/unifiedConsciousnessStore';

function Dashboard() {
    const { state, refresh } = useUnifiedConsciousness();

    return (
        <UnifiedConsciousnessDashboard state={state} />
    );
}
```

### Individual Widgets

```tsx
import { NavagrahaWheel } from '@/components/dashboard/NavagrahaWheel';
import { GunaDistribution } from '@/components/dashboard/GunaDistribution';
import { TattvaMonitor } from '@/components/dashboard/TattvaMonitor';

// Navagraha Wheel
<NavagrahaWheel planets={navagrahaState.planets} />

// Guna Distribution
<GunaDistribution
    guna={gunaVector}
    consciousness_level="Pure Awareness"
    balance_score={0.85}
/>

// Tattva Monitor
<TattvaMonitor state={tattvaState} />
```

## Testing

### Integration Tests

```bash
# Run unified consciousness integration tests
pytest backend/tests/integration/test_unified_consciousness.py -v
```

### Test Coverage

- ✅ Navagraha gate blocks trade during Rahu Kala
- ✅ Full OODA cycle with unified consciousness
- ✅ CognitiveOrchestrator guna integration
- ✅ Tattva risk gate evaluation
- ✅ RiskOrchestrator integration
- ✅ Strategy selection by Dasha

## Configuration

### Environment Variables

```bash
# Navagraha settings
LATITUDE=52.3676
LONGITUDE=4.9041

# Enable unified consciousness
ENABLE_UNIFIED_CONSCIOUSNESS=true

# Risk orchestrator settings
MAX_DAILY_VAR_PCT=0.05
MAX_POSITIONS=10
```

### Settings

```python
# backend/core/config/settings.py
class Settings:
    LATITUDE: float = 52.3676  # Amsterdam
    LONGITUDE: float = 4.9041

    # Unified Consciousness
    ENABLE_UNIFIED_CONSCIOUSNESS: bool = True

    # Risk
    MAX_DAILY_VAR_PCT: float = 0.05
    MAX_POSITIONS: int = 10
```

## Metrics & Observability

### Prometheus Metrics

```python
# Guna metrics
cognitive_orchestrator_guna_sattva
cognitive_orchestrator_guna_rajas
cognitive_orchestrator_guna_tamas
cognitive_orchestrator_guna_deviation

# OODA cycle metrics
ooda_cycles_completed_total
ooda_cycle_duration_seconds
ooda_phase_duration_seconds{phase="observe|orient|decide|act"}

# Consciousness gate metrics
consciousness_gate_blocked_total{reason="rahu_kala|high_tamas|kanchuka"}
```

### Logs

```
[OODA] Unified Consciousness Mode
  cognitive_orchestrator=enabled
  navagraha_service=enabled
  system_identity=enabled
  risk_orchestrator=enabled
  karma_register=enabled

[NAVAGRAHA] Trading gate OPEN - consciousness: Pure Awareness
[TATTVA] Kanchuka gate OPEN - avg_coherence: 0.85
[RISK] RiskOrchestrator approved: recommended_quantity=1.2345
[KARMA] Feedback recorded for trace_id=xxx
```

## Migration Guide

### From Legacy Orchestrators

1. **ColdPathCoordinator** → Gebruik `OODALoopCoordinator` met `cognitive_orchestrator`
2. **Phase12RealAgentCoordinator** → Gebruik `OODALoopCoordinator` met `strategy_registry`
3. **CognitiveOrchestrator standalone** → Inject als dependency in OODA

### Code Changes

```python
# Before (Legacy)
cold_path = ColdPathCoordinator(config_path="...")
decision = cold_path.make_decision()

# After (Unified)
coordinator = OODALoopCoordinator(
    # ... agents ...
    cognitive_orchestrator=CognitiveOrchestrator(...),
    navagraha_service=NavagrahaService(...),
    # ...
)
result = await coordinator.run_cycle("BTC/USD", 50000.0)
```

## Troubleshooting

### Trading Gate Blocked

```
[NAVAGRAHA] Rahu Kala active or high tamas - trading gate CLOSED
```

**Oplossing:** Check `rahu_kala_active` en `guna_distribution.tamas` in logs.

### Low Tattva Coherence

```
[TATTVA] Kanchuka risk gate blocked - avg_coherence: 0.45
```

**Oplossing:** SystemIdentity heeft tijd nodig om te stabiliseren na startup.

### Risk Orchestrator Blocking

```
[RISK] RiskOrchestrator blocked: Max drawdown exceeded
```

**Oplossing:** Check `DrawdownMonitor` status en portfolio value.

## References

- [OODA Loop Documentation](docs/architecture/ooda_loop.md)
- [36-Tattva Architecture](docs/consciousness/36_tattva.md)
- [Navagraha Service](docs/astrology/navagraha.md)
- [Risk Orchestrator](docs/risk/risk_orchestrator.md)

---

*Last Updated: 2026-02-17*
*Version: 1.0.0*
*Status: Production Ready*
