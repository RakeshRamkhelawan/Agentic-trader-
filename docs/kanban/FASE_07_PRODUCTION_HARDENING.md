# Fase 7: Production Hardening

> **Prioriteit**: 🔵 MEDIUM
> **Afhankelijkheden**: Fase 1-6 (alle features moeten bestaan)
> **Geschatte effort**: 5-7 dagen
> **Master document**: [SAMKHYA_MASTER_KANBAN_TDD.md](./SAMKHYA_MASTER_KANBAN_TDD.md)

---

## Overzicht

Productie-hardening: MiFID II compliance, LLM cost management, model fallback chain, en alle stubs vervangen door productie-code.

```
Production Stack:
├── MiFID II Compliance Layer
│   ├── Pre-trade checks (ESMA position limits)
│   ├── Best execution proof
│   ├── NavagrahaState audit logging
│   └── Trade reporting (T+1)
├── LLM Cost Management
│   ├── Token budget per agent per cycle
│   ├── Usage tracking (ClickHouse)
│   ├── Alert on budget exceeded
│   └── Fallback: Ollama local → DeepSeek → Gemini
├── Model Fallback Chain
│   └── Primary → Secondary → Tertiary → Offline fallback
└── Stub Expansion
    ├── DataScout _fetch_* methods → real APIs
    ├── portfolio mock $10k → real portfolio service
    ├── ElementalMacro._query_memory() → real RAG
    └── win_probability=0.5 → real model
```

---

## Bestaande Code Referenties

| Bestand | Regels | Status |
|---------|--------|--------|
| [backend/governance/circuit_breaker.py](../../backend/governance/circuit_breaker.py) | 311 | CircuitBreaker L72, check_and_trip() L151 |
| [backend/governance/decision_audit.py](../../backend/governance/decision_audit.py) | 247 | AuditLogger L75, log_decision() L89 |
| [backend/governance/agent_gatekeeper.py](../../backend/governance/agent_gatekeeper.py) | 91 | Agent permissies |
| [backend/governance/permission_service.py](../../backend/governance/permission_service.py) | 221 | Permissie checks |
| [backend/governance/trading_permissions.py](../../backend/governance/trading_permissions.py) | 72 | Trading permissies |
| [backend/llm/factory.py](../../backend/llm/factory.py) | 202 | LLMFactory L19, providers: Gemini, Ollama, DeepSeek |
| [backend/llm/service.py](../../backend/llm/service.py) | 164 | LLMService L22, UsageTracker |
| [backend/llm/resilience.py](../../backend/llm/resilience.py) | 59 | CircuitBreaker voor LLM |
| [backend/llm/usage_tracker.py](../../backend/llm/usage_tracker.py) | 167 | Token tracking (ClickHouse) |
| [backend/observability/metrics.py](../../backend/observability/metrics.py) | 75 | Prometheus metrics |
| [backend/agents/data_scout_agent.py](../../backend/agents/data_scout_agent.py) | — | _fetch_* stubs |

**Bekende stubs/mocks**:
- DataScout `_fetch_*` methods → mock data
- Portfolio/Account → mock $10,000
- `ElementalMacro._query_memory()` → stub
- `win_probability = 0.5` default in meerdere agents
- `ooda_coordinator.py:425` TODO: Connect to real Portfolio/Account

---

## Taken & Microtaken

---

### TAAK 7.1: MiFID II Compliance

**Doel**: Europese regelgeving compliance voor algoritmische handel.

**Bestanden te wijzigen**:
- `backend/governance/decision_audit.py` (extra velden)
- `backend/governance/circuit_breaker.py` (ESMA limits)

**Bestanden te creëren**:
- `backend/governance/mifid2/compliance_checker.py`
- `backend/governance/mifid2/position_limits.py`
- `backend/governance/mifid2/best_execution.py`
- `backend/governance/mifid2/trade_reporter.py`
- `backend/governance/mifid2/__init__.py`
- `backend/tests/unit/test_mifid2_compliance.py`

---

#### Microtaak 7.1.1: Pre-Trade Compliance Checker

**Masterprompt**:
```
MiFID II vereisten voor algoritmische handel:
1. Pre-trade risk controls (article 17)
2. Position limits (ESMA regulatory technical standards)
3. Best execution obligation (article 27)
4. Transaction reporting (article 26, T+1)
5. Algorithm identification (unique algo ID per strategie)
6. Kill switch (circuit breaker → bestaand circuit_breaker.py)

ComplianceChecker.check(trade_proposal: TradeProposal) → ComplianceResult.
Blokkeert trade als een compliance check faalt.
NavagrahaState moet gelogd worden als onderdeel van decision audit trail.
```

**Test FIRST**:
```python
class TestMiFID2Compliance:

    def test_pre_trade_check_passes_valid_trade(self):
        """Happy: Geldige trade passeert compliance checks."""
        pass

    def test_position_limit_exceeded_blocks_trade(self):
        """Unhappy: Te grote positie → trade geblokkeerd."""
        pass

    def test_esma_leverage_limit_enforced(self):
        """Unhappy: Crypto leverage > 2:1 voor retail → geblokkeerd."""
        pass

    def test_best_execution_proof_generated(self):
        """Happy: Best execution bewijs opgeslagen per trade."""
        pass

    def test_algo_id_assigned_per_strategy(self):
        """Happy: Elke strategie heeft uniek algorithm identifier."""
        pass

    def test_navagraha_state_in_audit_trail(self):
        """Happy: NavagrahaState gelogd bij elke trade decision."""
        pass

    def test_trade_report_generated_within_t1(self):
        """Happy: Trade report binnen T+1 gegenereerd."""
        pass

    def test_kill_switch_circuit_breaker_compliant(self):
        """Happy: Circuit breaker voldoet aan MiFID II kill switch."""
        pass

    def test_compliance_failure_logs_reason(self):
        """Unhappy: Compliance fout → gedetailleerde logging."""
        pass
```

---

### TAAK 7.2: LLM Cost Management

**Doel**: Token budgetten per agent, cost tracking, budget alerts.

**Bestanden te wijzigen**:
- `backend/llm/usage_tracker.py` (167 regels — budget limits toevoegen)
- `backend/llm/factory.py` (202 regels — budget-aware provider creation)

**Bestanden te creëren**:
- `backend/llm/budget_manager.py`
- `backend/tests/unit/test_llm_budget.py`

---

#### Microtaak 7.2.1: BudgetManager

**Masterprompt**:
```
BudgetManager tracked token budget per agent per OODA cycle:
- AnalystAgent: max 4000 tokens/cycle
- DataScout: max 2000 tokens/cycle
- TraderAgent: max 3000 tokens/cycle
- RiskManager: max 2000 tokens/cycle
- Daily total budget: max 500k tokens/dag

Alerts:
- 80% budget gebruikt → WARNING log
- 100% budget → agent degraded mode (kort prompt)
- 120% budget → agent SKIP (niet meer aanloggen bij LLM)

Tracking: ClickHouse (bestaand usage_tracker.py L167).
Dashboard: Prometheus gauge llm_budget_remaining_tokens.
```

**Test FIRST**:
```python
class TestLLMBudgetManager:

    def test_budget_decreases_on_usage(self):
        """Happy: Token gebruik vermindert budget."""
        pass

    def test_warning_at_80_percent(self):
        """Happy: 80% budget → WARNING log."""
        pass

    def test_degraded_mode_at_100_percent(self):
        """Happy: 100% → degraded mode (kort prompt)."""
        pass

    def test_skip_mode_at_120_percent(self):
        """Unhappy: 120% → agent skip."""
        pass

    def test_budget_resets_daily(self):
        """Happy: Budget reset elke dag middernacht UTC."""
        pass

    def test_budget_per_agent_independent(self):
        """Happy: Agent A budget raakt niet agent B."""
        pass

    def test_budget_tracks_to_clickhouse(self):
        """Happy: Elk gebruik gelogd in ClickHouse."""
        pass
```

---

### TAAK 7.3: Model Fallback Chain

**Doel**: Graceful degradation als primary LLM provider faalt.

**Bestanden te wijzigen**:
- `backend/llm/factory.py` (LLMFactory L19)
- `backend/llm/resilience.py` (59 regels — uitbreiden)

**Bestanden te creëren**:
- `backend/llm/fallback_chain.py`
- `backend/tests/unit/test_fallback_chain.py`

---

#### Microtaak 7.3.1: FallbackChain

**Masterprompt**:
```
Fallback volgorde:
1. Primary: DeepSeek (goedkoop, snel)
2. Secondary: Gemini (als DeepSeek down)
3. Tertiary: Ollama local (als cloud down)
4. Offline: Geen LLM (rule-based fallback)

CircuitBreaker per provider (bestaand: llm/resilience.py).
Na 3 failures → switch naar volgende in chain.
Health check: elke 60s probe primary.
Recovery: als primary weer healthy → switch terug.
"""
```

**Test FIRST**:
```python
class TestFallbackChain:

    def test_primary_provider_used_by_default(self):
        """Happy: DeepSeek is primary."""
        pass

    def test_fallback_to_secondary_on_failure(self):
        """Happy: DeepSeek down → Gemini gebruikt."""
        pass

    def test_fallback_to_tertiary(self):
        """Happy: DeepSeek + Gemini down → Ollama."""
        pass

    def test_offline_mode_no_llm(self):
        """Unhappy: Alle providers down → rule-based fallback."""
        pass

    def test_recovery_switches_back_to_primary(self):
        """Happy: Primary recovered → switch terug."""
        pass

    def test_circuit_breaker_trips_after_3_failures(self):
        """Happy: 3 failures → circuit breaker open."""
        pass

    def test_health_check_frequency(self):
        """Happy: Health check elke 60s."""
        pass
```

---

### TAAK 7.4: Stub Expansion (Productie Code)

**Doel**: Alle mocks en stubs vervangen door echte implementaties.

**Bestanden te wijzigen** (alle stubs):
- `backend/agents/data_scout_agent.py` (`_fetch_*` stubs)
- `backend/orchestration/ooda_coordinator.py:425` (portfolio mock)
- `backend/agents/elemental_macro.py` (`_query_memory()` stub)
- Diverse agents: `win_probability=0.5` default

---

#### Microtaak 7.4.1: Portfolio Service Connectie

**Masterprompt**:
```
Fix TODO ooda_coordinator.py:425: "TODO: Connect to real Portfolio/Account service"
Huidige code: _get_portfolio_state() retourneert mock $10,000.
Vervang door: echte portfolio query via ccxt_adapter.get_balance().
Fallback: als exchange onbereikbaar → gebruik laatste bekende state.
"""
```

**Test FIRST**:
```python
class TestPortfolioConnection:

    def test_real_balance_from_exchange(self):
        """Happy: Echte balans van exchange via ccxt."""
        pass

    def test_fallback_to_cached_on_error(self):
        """Unhappy: Exchange down → cached balans."""
        pass

    def test_portfolio_includes_all_assets(self):
        """Happy: Alle assets in portfolio."""
        pass

    def test_empty_portfolio_returns_zero(self):
        """Happy: Geen balans → $0 (niet $10,000 mock)."""
        pass
```

#### Microtaak 7.4.2: DataScout Real Data Sources

**Masterprompt**:
```
Vervang DataScout stubs:
- _fetch_market_data() → echte OHLCV via ccxt_adapter
- _fetch_social_sentiment() → CryptoFearGreed (van Fase 4.3)
- _fetch_orderbook() → echte orderbook via ccxt_adapter
Elke methode moet error handling + fallback naar cached data.
"""
```

#### Microtaak 7.4.3: Win Probability Model

**Masterprompt**:
```
Vervang win_probability=0.5 default door simpel statistisch model:
- Rolling 30-day win rate als baseline
- Gecorrigeerd voor marktregime (trending/ranging)
- Gecorrigeerd voor Navagraha state (confidence factor)
Geen ML nodig — simple Bayesian estimate.
"""
```

**Test FIRST**:
```python
class TestWinProbabilityModel:

    def test_probability_based_on_history(self):
        """Happy: History 70% wins → P(win) ≈ 0.7."""
        pass

    def test_no_history_returns_prior(self):
        """Unhappy: Geen history → Bayesian prior 0.5."""
        pass

    def test_probability_bounded_0_1(self):
        """Happy: Output altijd 0-1."""
        pass

    def test_navagraha_modulates_probability(self):
        """Happy: Jupiter Mahadasha → slight upward bias."""
        pass

    def test_market_regime_adjustment(self):
        """Happy: Trending markt + momentum strat → higher P."""
        pass
```

**Taak-afronding integratie test**:
```python
async def test_integration_7_4_no_stubs_remaining():
    """
    Integratie: VOLLEDIGE OODA loop zonder enige stub/mock.
    1. Echte marktdata (exchange of replay)
    2. Echte portfolio balans
    3. Echte Navagraha berekeningen
    4. Echte LLM calls (of rule-based fallback)
    5. Echte risk management
    6. Geen $10,000 mock
    7. Geen win_probability=0.5 hardcode
    """
    pass
```

---

## Fase 7 Productie Test

```python
@pytest.mark.e2e
async def test_production_phase7_full_system():
    """
    PRODUCTIE TEST: Complete end-to-end system verification.
    
    1. MiFID II compliance checks passeren
    2. Pre-trade risk controls werken
    3. LLM budget management actief
    4. Fallback chain functioneel
    5. Alle stubs vervangen door productie code
    6. NavagrahaState in alle audit trails
    7. Circuit breaker trip → graceful degradation
    8. Portfolio = echte exchange balans
    9. Win probability = model-based
    10. Trade reporting T+1
    """
    pass
```

---

## Kruisverwijzingen

- **← Fase 1**: NavagrahaState voor audit trail (alle taken)
- **← Fase 2**: JWT auth voor alle endpoints (Taak 2.1)
- **← Fase 3**: Prometheus alerting (circuit breaker, budget) (Taak 3.3)
- **← Fase 4**: CCXT adapter voor echte exchange data (Taak 4.1)
- **← Fase 4**: Sentiment providers voor DataScout (Taak 4.3)
- **← Fase 5**: Compliance indicators in UI (Taak 5.4)
- **← Fase 6**: Karma/Viveka voor win probability model (Taak 6.1, 6.3)
