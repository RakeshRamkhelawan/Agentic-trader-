# Phase 2: Kanban/TDD Task Document
**Project:** Agentic Trading Platform - OODA Multi-Agent AGI
**Method:** Kanban + TDD (Red-Green-Refactor)
**Spec:** Based on `phase_intelligent_agent.md` and User Feedback

This document serves as the **definitive, step-by-step build instruction** for the LLM builder.

---

## Epic 0: Core Types & Contracts (Foundation)

### Task 0.1: Domain Models (Pydantic)

**Master Prompt:**
```text
Create backend/core/schemas/ooda_types.py.
Define strict Pydantic models for the OODA loop data flow.
Ensure all models have ConfigDict(frozen=True) for immutability.
```

**Context:**
- These types are the "language" spoken between agents.

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

class Orientation(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    regime: MarketRegime
    indicators: Dict[str, float]  # rsi, macd, bb_width
    core_sentiment: float  # From SystemIdentity (Ahamkara)
    rag_context: List[str]  # Summaries from VectorMemory
    confidence: float

class TradeProposal(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    side: str  # 'buy' or 'sell'
    size: float
    entry_price: Optional[float]
    stop_loss: float
    take_profit: float
    time_in_force: str = "GTC"
    rationale: str
    strategy_id: str

class RiskAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)
    approved: bool
    modified_size: Optional[float] = None
    risk_score: float  # 0.0-1.0
    reason: str
    checks_passed: List[str]
    checks_failed: List[str]

class ExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    side: str
    quantity: float
    order_type: str = "LIMIT"
    price: Optional[float]
    params: Dict[str, Any] = Field(default_factory=dict)

class ExecutionOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)
    success: bool
    order_id: Optional[str]
    filled_qty: float
    avg_price: float
    fee: float
    error: Optional[str]
```

### Task 0.2: Event Schemas

**Master Prompt:**
```text
Create backend/core/schemas/events.py.
Define payload schemas for the EventBus.
```

**Implementation Snippet:**
```python
# backend/core/schemas/events.py
class TradeProposalEvent(BaseModel):
    proposal: TradeProposal
    timestamp: float

class MarketTickEvent(BaseModel):
    symbol: str
    price: float
    timestamp: float
```

---

## Epic 1: Vector Memory & RAG Layer

### Task 1.1: TradingKnowledge Vector Store

**Master Prompt:**
```text
Implement backend/rag/vector_memory.py with a TradingKnowledge SQLAlchemy model using pgvector.
The model must store strategy playbooks, macro events, and historical scenarios with embeddings.
Implement insert, similarity search with cosine distance, and category filtering.
Use async SQLAlchemy.
Include "Logging/Audit": Log all searches to standard logger.
```

**Context:**
- Dependencies: `pgvector`, `sqlalchemy[async]`, `asyncpg`

**Unhappy Path Test (Systemic):**
```python
@pytest.mark.asyncio
async def test_search_database_down_resilience():
    """Systemic Unhappy Path: Database Down"""
    vm = VectorMemory(connection_string="postgresql+asyncpg://bad:port/db")
    # Should raise specific VectorStoreError, not crash application
    with pytest.raises(VectorStoreError):
        await vm.search_similar(...) 
```

---

## Epic 1.5: Cognitive Core Integration

### Task 1.5.1: SystemIdentity Adapter

**Master Prompt:**
```text
Implement backend/core/adapters/system_bridge.py.
Create a 'CognitiveBridge' class that wraps the existing SystemIdentity.
It must export a method `process_observation(obs: Observation) -> float`.
This method converts the Pydantic Observation into the numpy arrays required by SystemIdentity.process_market_cycle().
It returns the 'confidence' score from the Core (Ahamkara).
```

**Context:**
- Connects new OODA world (Pydantic) with valid Old World (Numpy/FFT).

**Happy Path Test:**
```python
@pytest.mark.asyncio
async def test_bridge_transform():
    identity = SystemIdentity()
    bridge = CognitiveBridge(identity)
    obs = Observation(symbol="BTC", price=50000, volume=100, orderbook=..., social_sentiment=0.5)
    
    core_confidence = await bridge.process_observation(obs)
    assert 0.0 <= core_confidence <= 1.0
    # Verify SystemIdentity state updated
    assert identity.system_state['total_experiences'] > 0
```

---

## Epic 2: Data Scout Agent (Observe)

### Task 2.1: DataScoutAgent Implementation

**Master Prompt:**
```text
Implement backend/agents/data_scout_agent.py.
Collects market data and returns a standardized Observation.
Must inject Audit logging: every observation is logged with a trace_id.
```

**Implementation Snippet:**
```python
class DataScoutAgent(BaseAgent):
    async def observe(self, symbol: str, trace_id: str) -> Observation:
        obs = ... # fetch data
        await self.audit_log.log(trace_id, "OBSERVE", obs.model_dump())
        return obs
```

---

## Epic 3: Analyst Agents (Orient)

### Task 3.1: TechnicalAnalyst Agent

**Master Prompt:**
```text
Implement backend/agents/analyst_agent.py.
Calculate indicators.
Consume the Observation.
Must include Audit logging.
```

### Task 3.2: Researcher Agents (Debate)

**Master Prompt:**
```text
Implement backend/agents/researcher_agent.py.
Bull/Bear agents.
Output layout:
class Argument(BaseModel):
    bias: str # 'bull'/'bear'
    key_points: List[str]
    rag_citations: List[str]
    sentiment_score: float
```

---

## Epic 4: Risk Manager (Decide - Constraint)

### Task 4.1: RiskManager Implementation

**Master Prompt:**
```text
Implement backend/agents/risk_manager_agent.py.
Validates TradeProposal.
Addresses Systemic Failure: If RiskManager service/logic fails (exception), default to REJECT.
```

**Unhappy Path Test (Systemic):**
```python
async def test_risk_agent_exception_defaults_to_reject():
    """If internal logic fails, return approved=False"""
    agent = RiskManagerAgent()
    # Mock internal method to raise Exception
    agent._check_drawdown = Mock(side_effect=Exception("DB fail"))
    
    assessment = await agent.evaluate(proposal, ...)
    assert assessment.approved == False
    assert "SystemError" in assessment.reason
```

---

## Epic 5: Trader Agent (Decide - Plan)

### Task 5.1: TraderAgent Implementation

**Master Prompt:**
```text
Implement backend/agents/trader_agent.py.
Input: Orientation (with Core intuition) + List[Argument] (Bull/Bear).
Use LLM to synthesize.
Constraint: Even if LLM says "BUY", if Core Intuition (from Orientation) is < 0.2, force "HOLD" or reduce size (Core Override).
```

**Context:**
- Validates that the "Gut Feeling" of the existing system is respected.

---

## Epic 6: Fund Manager (Decide - Allocate)

### Task 6.1: FundManagerAgent

**Master Prompt:**
```text
Implement backend/agents/fund_manager_agent.py.
Allocate capital across proposals.
Audit: Log final allocation decision.
```

---

## Epic 7: OODA Orchestrator

### Task 7.1: OODALoopCoordinator

**Master Prompt:**
```text
Implement backend/orchestration/ooda_coordinator.py.
Modes:
1. `run_loop_interval(interval_ms)`
2. `run_loop_event_driven()` (subscribes to market_tick)

Config: `TRADING_MODE` ("notify_only" vs "auto")
Logic:
- If "notify_only": Stop after Decide. Emit `trade_proposal` event. Do NOT call Execution.
- If "auto": Call Execution.
```

**Happy Path Test (Run Mode):**
```python
async def test_notify_only_mode():
    coord = OODALoopCoordinator(trading_mode="notify_only")
    # ... setup mocks ...
    await coord.run_cycle("BTC")
    
    assert execution_engine.execute.call_count == 0
    assert event_bus.emit.call_args[0][0] == "trade_proposal"
```

**Unhappy Path Test (LLM Timeout):**
```python
async def test_ooda_llm_timeout_robustness():
    """If Analyst LLM times out, OODA should skip trading this cycle but NOT crash"""
    coord = OODALoopCoordinator()
    coord.analyst.analyze = Mock(side_effect=TimeoutError("LLM Slow"))
    
    result = await coord.run_cycle("BTC")
    assert result["status"] == "skipped"
    assert result["reason"] == "OrientationFailed"
    # Ensure loop stays alive
```

---

## Epic 8: Execution & Hot Path

### Task 8.1: FastConfig Structure & Tests

**Master Prompt:**
```text
Implement backend/execution/fast_config.py.
Define the Shared Memory Structure (using `struct` or `multiprocessing.SharedMemory` pattern, or a highly optimized dictionary for MVP).
Strict Structure:
- symbol (str 10)
- direction (int: 1=buy, -1=sell)
- size (float)
- trigger_price (float)
- max_slippage (float)
- valid_until (timestamp)
- strategy_id (uuid)
```

**Round-Trip Test:**
```python
def test_fast_config_round_trip():
    fc = FastConfig()
    fc.write("BTC", side=1, price=50000, size=0.1)
    
    # Read back from "Hotkey" perspective
    read_val = fc.read("BTC")
    assert read_val['side'] == 1
    assert read_val['trigger_price'] == 50000
```

### Task 8.2: HotPathEngine & Exchange Errors

**Master Prompt:**
```text
Implement HotPathEngine.
Handle Exchange Errors:
- If order rejected (Insufficient Funds): Log Audit, Disable Strategy, Alert User.
- If network timeout: Retry (max 3 times) then Abort.
```

---

## Epic 9: Governance

### Task 9.1: DecisionAuditLog

**Master Prompt:**
```text
Implement backend/core/compliance/audit_logger.py.
Must support structured logging of every step in OODA.
Schema:
{
  trace_id: str,
  timestamp: float,
  stage: str (OBSERVE|ORIENT|DECIDE|ACT),
  component: str,
  input_summary: dict,
  output_summary: dict,
  latency_ms: float
}
```

---

## Epic 10: End-to-End Integration

### Task 10.1: Full Dataflow Test

**Master Prompt:**
```text
Create backend/tests/test_end_to_end_flow.py.
Simulate a full market tick -> trade execution flow.
Verify:
1. DataScout -> Observation
2. Bridge -> SystemIdentity sets 'confidence'
3. Analyst -> Orientation (includes Core confidence)
4. Trader -> Proposal
5. Risk -> Approval
6. FundManager -> Allocation
7. Execution -> Order
8. AuditLog -> Contains full trace
```
