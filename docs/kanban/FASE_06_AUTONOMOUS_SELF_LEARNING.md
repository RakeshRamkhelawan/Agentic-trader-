# Fase 6: Autonomous Self-Learning

> **Prioriteit**: 🔵 MEDIUM
> **Afhankelijkheden**: Fase 1 (NavagrahaEngine), Fase 4 (Backtesting)
> **Geschatte effort**: 5-7 dagen
> **Master document**: [SAMKHYA_MASTER_KANBAN_TDD.md](./SAMKHYA_MASTER_KANBAN_TDD.md)

---

## Overzicht

Zelf-lerend systeem: Karma feedback loop (trade outcome → parameter tuning), Dasha-aware OODA scheduling, en Viveka discriminerend vermogen.

```
Karma Loop (Feedback):
  Trade Outcome → KarmaAnalyzer → Parameter Adjustments
       ↓                                    ↓
  PunyaScore (merit)              GrahaGunaMapper weights
  PapaScore (demerit)             ElementalBase prana rates
                                  OODALoopCoordinator thresholds

Dasha Scheduler:
  Mahadasha Lord → Strategy Selection
  Antardasha Lord → Risk Appetite Adjustment

Viveka (Discriminating Wisdom):
  ReviewAgent → Analyze N past decisions → Learn patterns
  → Update ColdPathCoordinator weights
```

---

## Bestaande Code Referenties

| Bestand | Regels | Status |
|---------|--------|--------|
| [backend/orchestration/ooda_coordinator.py](../../backend/orchestration/ooda_coordinator.py) | 518 | run_cycle() L118, set_trading_mode() L455 |
| [backend/orchestration/cold_path_coordinator.py](../../backend/orchestration/cold_path_coordinator.py) | 544 | ColdPathCoordinator L122, write_config() L438 |
| [backend/strategies/base.py](../../backend/strategies/base.py) | 24 | BaseStrategy(ABC) L6 |
| [backend/strategies/mean_reversion.py](../../backend/strategies/mean_reversion.py) | 84 | MeanReversionStrategy |
| [backend/strategies/momentum.py](../../backend/strategies/momentum.py) | 117 | MomentumStrategy |
| [backend/governance/decision_audit.py](../../backend/governance/decision_audit.py) | 247 | AuditLogger L75, log_decision() L89 |
| [backend/services/intent_monitor.py](../../backend/services/intent_monitor.py) | 53 | IntentMonitor (Purusha) |

**TODO markers**:
- `ooda_coordinator.py:367` — "TODO: Track actual position"
- `ooda_coordinator.py:425` — "TODO: Connect to real Portfolio/Account service"

---

## Taken & Microtaken

---

### TAAK 6.1: Karma Feedback Loop

**Doel**: Trade outcomes analyseren en systeem parameters automatisch aanpassen.

**Bestanden te creëren**:
- `backend/core/karma/analyzer.py`
- `backend/core/karma/models.py`
- `backend/core/karma/__init__.py`
- `backend/tests/unit/test_karma_analyzer.py`

---

#### Microtaak 6.1.1: Karma Modellen

**Masterprompt**:
```
Karma = wet van oorzaak en gevolg — hier: trade-actie → uitkomst → aanpassing.
Punya (verdienste): winstgevende trades, correcte risico-inschatting.
Papa (schuld): verliesgevende trades, te laat gesloten posities.
KarmaScore: rolling 30-day som van punya (positief) en papa (negatief).
Elk trade outcome wordt gescored en beïnvloedt:
- GrahaGunaMapper weights (confident → hogere weights, onzeker → lagere)
- ElementalBase prana regeneration rate
- OODALoopCoordinator decision thresholds
```

**Test FIRST**:
```python
class TestKarmaModels:

    def test_punya_increases_on_profitable_trade(self):
        """Happy: Winstgevende trade → punya +."""
        pass

    def test_papa_increases_on_losing_trade(self):
        """Happy: Verliesgevende trade → papa +."""
        pass

    def test_karma_score_bounded(self):
        """Happy: Score is bounded [-100, +100]."""
        pass

    def test_karma_decay_over_time(self):
        """Happy: Oude trades wegen minder mee (time decay)."""
        pass

    def test_zero_pnl_trade_neutral(self):
        """Happy: Break-even trade → geen karma effect."""
        pass
```

#### Microtaak 6.1.2: KarmaAnalyzer

**Masterprompt**:
```
KarmaAnalyzer.analyze(trade_result: TradeResult) → KarmaAdjustment.
KarmaAdjustment bevat:
- parameter_deltas: Dict[str, float] (welke parameters aanpassen)
- confidence: float (0-1, hoe zeker de aanpassing)
- reasoning: str (uitleg in Samkhya termen)

Connectie met bestaande code:
- TradeResult van order_executor.py ExecutionResult
- AuditLogger.log_decision() voor trail
- IntentMonitor.monitor_balance() voor Guna tracking
```

**Test FIRST**:
```python
class TestKarmaAnalyzer:

    def test_analyze_profitable_trade_adjusts_positively(self):
        """Happy: Profit → positieve parameter shifts."""
        pass

    def test_analyze_losing_trade_adjusts_negatively(self):
        """Happy: Loss → conservatievere thresholds."""
        pass

    def test_consecutive_losses_increase_tamas(self):
        """Happy: 3+ opeenvolgende losses → tamas boost."""
        pass

    def test_adjustment_confidence_based_on_sample_size(self):
        """Happy: Meer trades → hogere confidence."""
        pass

    def test_adjustments_respect_bounds(self):
        """Unhappy: Parameters gaan niet buiten veilige grenzen."""
        pass

    def test_analyze_with_no_history_returns_neutral(self):
        """Unhappy: Geen trade history → geen aanpassing."""
        pass
```

**Taak-afronding integratie test**:
```python
async def test_integration_6_1_karma_loop_e2e():
    """
    Integratie: Executeer trade → analyze outcome → adjust parameters → verify.
    1. OODA cycle produces trade
    2. Execute trade (paper)
    3. KarmaAnalyzer scores outcome
    4. Parameters adjusted
    5. Next OODA cycle uses adjusted parameters
    """
    pass
```

---

### TAAK 6.2: Dasha-Aware OODA Scheduling

**Doel**: Mahadasha/Antardasha beïnvloedt strategie selectie en risk appetite.

**Bestanden te wijzigen**:
- `backend/orchestration/ooda_coordinator.py` (set_trading_mode() L455)

**Bestanden te creëren**:
- `backend/core/navagraha/dasha_scheduler.py`
- `backend/tests/unit/test_dasha_scheduler.py`

---

#### Microtaak 6.2.1: DashaScheduler

**Masterprompt**:
```
DashaScheduler vertaalt Mahadasha/Antardasha naar trading parameters:
| Mahadasha Lord | Strategie voorkeur    | Risk multiplier |
|----------------|-----------------------|-----------------|
| Jupiter        | Trend-following       | 1.2x            |
| Saturn         | Mean reversion        | 0.7x            |
| Mars           | Momentum/breakout     | 1.0x            |
| Venus          | Range-trading         | 0.9x            |
| Mercury        | Scalping              | 0.8x            |
| Rahu           | Contrarian            | 0.6x (cautious) |
| Ketu           | No new positions      | 0.3x            |
| Sun            | Blue-chip/large-cap   | 1.1x            |
| Moon           | Sentiment-following   | 0.9x            |

Antardasha modifieert: sub-period lord overrides timing.
"""
```

**Test FIRST**:
```python
class TestDashaScheduler:

    def test_jupiter_mahadasha_prefers_trend(self):
        """Happy: Jupiter → trend-following strategie."""
        pass

    def test_saturn_mahadasha_prefers_mean_reversion(self):
        """Happy: Saturn → mean-reversion strategie."""
        pass

    def test_ketu_mahadasha_blocks_new_positions(self):
        """Happy: Ketu → risk 0.3x, geen nieuwe posities."""
        pass

    def test_risk_multiplier_bounded(self):
        """Happy: Multiplier altijd 0.1-2.0."""
        pass

    def test_antardasha_modifies_timing(self):
        """Happy: Antardasha lord overrides sub-timing."""
        pass

    def test_unknown_lord_returns_default(self):
        """Unhappy: Onbekende lord → default parameters."""
        pass
```

---

### TAAK 6.3: Viveka (Discriminating Wisdom) Learning

**Doel**: Periodieke review van beslissingen → leereffect.

**Bestanden te creëren**:
- `backend/core/viveka/review_agent.py`
- `backend/core/viveka/__init__.py`
- `backend/tests/unit/test_viveka_review.py`

---

#### Microtaak 6.3.1: VivekaReviewAgent

**Masterprompt**:
```
Viveka = discriminerend vermogen (Buddhi's hoogste functie).
VivekaReviewAgent analyseert de laatste N beslissingen:
- Welke Navagraha condities leidden tot winst?
- Welke condities leidden tot verlies?
- Pattern matching via simple statistical analysis (geen ML)
- Output: VivekaInsight met aanbevelingen
Connectie: ColdPathCoordinator.write_config() (L438) voor parameter updates.
Draait als CronJob: elke 24 uur.
"""
```

**Test FIRST**:
```python
class TestVivekaReviewAgent:

    def test_review_identifies_profitable_patterns(self):
        """Happy: Winstgevende Navagraha patronen gedetecteerd."""
        pass

    def test_review_identifies_losing_patterns(self):
        """Happy: Verliesgevende patronen gedetecteerd."""
        pass

    def test_minimum_sample_size_required(self):
        """Unhappy: < 10 trades → "insufficient data"."""
        pass

    def test_insights_written_to_cold_path(self):
        """Happy: Inzichten geschreven naar ColdPathCoordinator."""
        pass

    def test_no_overfit_guard(self):
        """Happy: Kleine veranderingen per review (max 5% per param)."""
        pass

    def test_review_logs_to_audit(self):
        """Happy: Elke review gelogd in AuditLogger."""
        pass
```

**Taak-afronding integratie test**:
```python
async def test_integration_6_full_self_learning_loop():
    """
    Integratie: Trade → Karma → DashaScheduler → Viveka → Parameter Update.
    1. Execute 20 paper trades
    2. KarmaAnalyzer scores alle outcomes
    3. DashaScheduler selecteert strategie op basis van huidige Dasha
    4. VivekaReviewAgent analyseert patronen
    5. Parameters updaten
    6. Volgende batch trades gebruikt nieuwe parameters
    7. Verify resultaat is minstens niet slechter (geen regression)
    """
    pass
```

---

## Fase 6 Productie Test

```python
@pytest.mark.e2e
async def test_production_phase6_self_learning():
    """
    PRODUCTIE TEST:
    1. Karma analyzer werkt op echte paper trade history
    2. DashaScheduler selecteert juiste strategie voor huidige Dasha
    3. Viveka review produceert inzichten
    4. Parameter updates zijn bounded en safe
    5. System performance degradeert niet (regression guard)
    """
    pass
```

---

## Kruisverwijzingen

- **← Fase 1**: NavagrahaEngine voor Dasha state (Taak 1.3, 1.6)
- **← Fase 4**: Backtest resultaten als training data (Taak 4.2)
- **← Fase 4**: Trade outcomes van order executor (Taak 4.1)
- **→ Fase 5**: Karma score weergave in dashboard (Taak 5.4)
- **→ Fase 7**: Viveka insights in MiFID II audit trail (Taak 7.1)
- **→ Fase 7**: Learning rate bounded door governance (Taak 7.4)
