# Phase 2: Kanban/TDD Task Document
**Project:** Agentic Trading Platform - OODA Multi-Agent AGI
**Method:** Kanban + TDD (Red-Green-Refactor)
**Spec:** Based on `phase_intelligent_agent.md` (1:1 Match)

This document serves as the **definitive, step-by-step build instruction** for the LLM builder.

---

## Epic 12: Documentatie & Schema's (Foundational Layer)
*(Implement First for Type Safety)*

### Task 12.1: Type Definities (Pydantic)
**Section:** 12.1

**Master Prompt:**
```text
Create backend/core/schemas/ooda_types.py.
Define strict Pydantic models for the OODA loop data flow.
Ensure all models have ConfigDict(frozen=True) for immutability.
Include: MarketRegime, Observation, Orientation, TradeProposal, RiskAssessment, ExecutionPlan, ExecutionOutcome.
```

**Implementation Snippet:**
```python
# backend/core/schemas/ooda_types.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class MarketRegime(str, Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"

class Observation(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    price: float
    volume: float
    orderbook: Dict[str, Any]  # {bids: [], asks: []}
    funding_rate: Optional[float] = None
    social_sentiment: float = 0.0
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    raw_ticker: Dict[str, Any] = Field(default_factory=dict)

# ... (Include Orientation, TradeProposal, RiskAssessment, ExecutionPlan, ExecutionOutcome as per spec)
```

### Task 12.2: Event Schema's
**Section:** 12.2

**Master Prompt:**
```text
Create backend/core/schemas/events.py.
Define payload schemas for the EventBus:
- market_tick
- news_event
- trade_proposal
- trade_executed
- risk_alert
- system_health
```

---

## Epic 3: OODA Loop Orchestratie

### Task 3.1: OODA Orchestrator
**Section:** 3.1
**Dependencies:** Epic 12, Epic 4, Epic 5

**Master Prompt:**
```text
Implement backend/orchestration/ooda_coordinator.py.
Class: OODALoopCoordinator.
Dependencies: SystemIdentity, SensoryProcessor, MemorySystem, Agents (DataScout, Analyst, RiskManager, Trader, FundManager).
Modes:
1. `run_loop_interval(interval_ms)`
2. `run_loop_event_driven()` (subscribes to market_tick)
Config: `TRADING_MODE` ("notify_only" vs "auto").
Logic:
- Observe -> Orient -> Decide -> Act.
- If "notify_only": Stop after Decide. Emit `trade_proposal` event. Do NOT call Execution.
- If "auto": Call Execution.
```

**Happy Path Test (Notify Mode):**
```python
async def test_notify_only_mode():
    coord = OODALoopCoordinator(trading_mode="notify_only")
    # ... setup mocks ...
    await coord.run_cycle("BTC")

    assert execution_engine.execute.call_count == 0
    assert event_bus.emit.call_args[0][0] == "trade_proposal"
```

### Task 3.2: Cognitive System Bridge (Adapter)
**Section:** 3.1 (Dependency)

**Master Prompt:**
```text
Implement backend/core/adapters/system_bridge.py.
Create a 'CognitiveBridge' class that wraps the existing SystemIdentity.
Export method `process_observation(obs: Observation) -> float`.
Converts Pydantic Observation to Numpy inputs for SystemIdentity.process_market_cycle().
Returns 'confidence' score from Core (Ahamkara).
```

---

## Epic 4: RAG / Vector Memory Layer

### Task 4.1: Vector Memory
**Section:** 4.1

**Master Prompt:**
```text
Implement backend/rag/vector_memory.py.
Model: TradingKnowledge (SQLAlchemy) with pgvector.
Columns: id, content, embedding, category, asset, timestamp.
Functionality:
- Upsert Playbooks/Events.
- Similarity Search (cosine distance).
- Async SQLAlchemy implementation.
```

**Unhappy Path Test (DB Down):**
```python
@pytest.mark.asyncio
async def test_search_database_down_resilience():
    """Systemic Unhappy Path: Database Down"""
    vm = VectorMemory(connection_string="postgresql+asyncpg://bad:port/db")
    with pytest.raises(VectorStoreError):
        await vm.search_similar(...)
```

---

## Epic 5: Multi-Agent “Trading Firm” Laag

### Task 5.1: DataScoutAgent
**Section:** 5.1

**Master Prompt:**
```text
Implement backend/agents/data_scout_agent.py.
Rol: Observe.
Collects live data (ticks, orderbook) and normalizes to Observation schema.
Inject Audit logging: log(trace_id, "OBSERVE", obs).
```

### Task 5.2: AnalystAgent (Technical & Sentiment)
**Section:** 5.2

**Master Prompt:**
```text
Implement backend/agents/analyst_agent.py.
Rol: Orient.
- TechnicalAnalyst: Calc RSI, MACD, Bollinger.
- SentimentAnalyst: Aggregates news/tweets.
Output: Orientation (with confidence score).
```

### Task 5.3: RiskManagerAgent
**Section:** 5.3

**Master Prompt:**
```text
Implement backend/agents/risk_manager_agent.py.
Rol: Decide (Constraints).
Validates TradeProposal against policies (max drawdown, exposure).
Returns: RiskAssessment (GO/NO-GO).
Systemic Failure: If logic fails/crashes, default to REJECT.
```

**Unhappy Path Test:**
```python
async def test_risk_agent_exception_defaults_to_reject():
    agent = RiskManagerAgent()
    agent._check_drawdown = Mock(side_effect=Exception("DB fail"))
    assessment = await agent.evaluate(...)
    assert assessment.approved == False
```

### Task 5.4: TraderAgent
**Section:** 5.4

**Master Prompt:**
```text
Implement backend/agents/trader_agent.py.
Rol: Decide (Execution Plan).
Input: Orientation + Researcher Arguments.
Synthesizes signals into TradeProposal.
Constraint: Verify Core Intuition < 0.2 override (Force HOLD).
```

### Task 5.5: FundManagerAgent
**Section:** 5.5

**Master Prompt:**
```text
Implement backend/agents/fund_manager_agent.py.
Rol: Decide (Portfolio Allocation).
Aggregates multiple TradeProposals.
Allocates capital based on risk/reward.
```

### Task 5.6: ResearcherAgents (Bull/Bear)
**Section:** 5.6

**Master Prompt:**
```text
Implement backend/agents/researcher_bull_agent.py & researcher_bear_agent.py.
Rol: Orient (Debate).
Generate opposing theses (Bull vs Bear arguments).
Output: List[Argument] for TraderAgent.
```

---

## Epic 6: Execution Layer: Hot Path

### Task 6.1: FastConfig Bridge
**Section:** 6.1

**Master Prompt:**
```text
Implement backend/execution/fast_config.py.
Zero-copy bridge (Shared Memory / Optimized Dict).
Structure: symbol, direction, size, trigger_price, max_slippage, valid_until, strategy_id.
```

### Task 6.2: HotPathEngine
**Section:** 6.2

**Master Prompt:**
```text
Implement backend/execution/hot_path_engine.py.
Low-latency execution.
Reads FastConfig.
 executes orders via Exchange API.
Handles Exchange Errors (Timeout/Rejection) -> Log & Disable Strategy.
```

---

## Epic 7: Governance, Monitoring & Failure Modes

### Task 7.1: Observability & Logging
**Section:** 7.1

**Master Prompt:**
```text
Implement backend/core/compliance/audit_logger.py (DecisionAuditLog).
Log every OODA cycle with `trace_id`.
Fields: Snapshot, RAG Sources, Agent Outputs, Decision, ExecutionOutcome.
```

### Task 7.2: Agent Failure Modes & Watchdogs
**Section:** 7.2

**Master Prompt:**
```text
Implement backend/orchestration/watchdog.py.
Monitor OODALoopCoordinator heartbeat.
Implement Circuit Breaker for frequent timeouts/errors.
Hard limit on MAX_ITERATIONS in loops.
```

### Task 7.3: Governance / RBAC
**Section:** 7.3

**Master Prompt:**
```text
Enforce strict changes to TRADING_MODE.
Ensure TRADING_MODE cannot be changed by Agents, only by Admin/Config.
```

### Task 7.4: Evaluation Datasets
**Section:** 7.4

**Master Prompt:**
```text
Create evaluation datasets (backtest scenarios):
- Crash (Market drop > 10%)
- Gap-up
- Flash-illiquidity
Ensure new agent versions pass these gates.
```

---

## Epic 8: Human-in-the-Loop & Config

### Task 8.1: Notify-Only Mode
**Section:** 8.1

**Master Prompt:**
```text
Verify Notify-Only logic in OODA Coordinator.
Ensure events `trade_proposal` are emitted.
Implement UI handler (Mock or Real) for Manual Approval injection.
```

---

## Epic 9: Validatie & Tests

### Task 9.1: Nieuwe Test Suites
**Section:** 9.1

**Master Prompt:**
```text
Create dedicated test files:
- backend/tests/test_ooda_coordinator.py
- backend/tests/test_agents_specialized.py
- backend/tests/test_execution_hotpath.py
- backend/tests/test_rag_vector_memory.py
```

### Task 9.2: Integratie (End-to-End)
**Section:** 9.2

**Master Prompt:**
```text
Create backend/tests/test_end_to_end_flow.py.
Simulate Full Flow: Market Tick -> OODA -> Order -> Execution.
Verify Audit Log completeness.
```

---

## Epic 10: Data- en Configlaag

### Task 10.1: Standardized Data Layer
**Section:** 10.1

**Master Prompt:**
```text
Verify schema implementation for:
- market_tick (Postgres)
- orderbook_snapshot (Redis)
- portfolio_state (Redis)
Ensure Agents use these standardized sources only.
```

### Task 10.2: Config & Policy Store
**Section:** 10.2

**Master Prompt:**
```text
Implement Central Config Store (backend/config/trading_config.py).
Store Risk Limits, OODA Interval, Active Agents.
Remove hardcoded values from Agents.
```

---

## Epic 11: Security & Tool Governance

### Task 11.1: Tool Toegang
**Section:** 11.1

**Master Prompt:**
```text
Audit Tool Access.
Ensure 'Execute Trade' is ONLY available to TraderAgent and HotPathEngine.
Implement Code-level Guardrails (Allowlist).
```

### Task 11.2: Prompt Injection Mitigatie
**Section:** 11.2

**Master Prompt:**
```text
Implement Citation Validation in Research Agents.
Ensure RAG sources are explicitly cited.
Flag conflicting sources.
```
