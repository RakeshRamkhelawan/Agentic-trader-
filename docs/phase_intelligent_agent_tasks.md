# Phase 2: Kanban/TDD Task Document
**Project:** Agentic Trading Platform - OODA Multi-Agent AGI
**Method:** Kanban + TDD (Red-Green-Refactor)
**Spec:** Based on `phase_intelligent_agent.md`

This document serves as the **step-by-step build instruction** for the LLM builder.

---

## Epic 1: Vector Memory & RAG Layer

### Task 1.1: TradingKnowledge Vector Store

**Master Prompt:**
```text
Implement backend/rag/vector_memory.py with a TradingKnowledge SQLAlchemy model using pgvector.
The model must store strategy playbooks, macro events, and historical scenarios with embeddings.
Implement insert, similarity search with cosine distance, and category filtering.
Use async SQLAlchemy. It must be testable standalone without LLM dependencies.
```

**Context:**
- Dependencies: `pgvector`, `sqlalchemy[async]`, `asyncpg`
- Interface: `VectorMemory.add_knowledge()`, `VectorMemory.search_similar()`

**Happy Path Test:**
```python
# backend/tests/test_rag_vector_memory.py
import pytest
from backend.rag.vector_memory import VectorMemory
import numpy as np

@pytest.mark.asyncio
async def test_add_and_search_knowledge():
    """Happy path: add knowledge and retrieve similar items"""
    vm = VectorMemory(connection_string="postgresql+asyncpg://user:pass@localhost/db")
    await vm.init_db()
    
    embedding = np.random.randn(1536).tolist()
    id = await vm.add_knowledge(
        content="When RSI > 80 and news is bad -> Short",
        embedding=embedding,
        category="strategy",
        asset="BTC"
    )
    assert id is not None
    
    results = await vm.search_similar(query_embedding=embedding, limit=3)
    assert len(results) == 1
    assert results[0].content == "When RSI > 80 and news is bad -> Short"
```

**Unhappy Path Test:**
```python
@pytest.mark.asyncio
async def test_invalid_embedding_dimension():
    """Unhappy path: wrong dimension raises ValueError"""
    vm = VectorMemory(...)
    with pytest.raises(ValueError):
        await vm.add_knowledge(content="Test", embedding=[0.1]*100, category="strategy")
```

**Implementation Snippet:**
```python
# backend/rag/vector_memory.py
class TradingKnowledge(Base):
    __tablename__ = "trading_knowledge"
    id = Column(Integer, primary_key=True)
    embedding = Column(Vector(1536))
    category = Column(String) # strategy, macro, scenario
```

---

## Epic 2: Data Scout Agent (Observe)

### Task 2.1: DataScoutAgent Implementation

**Master Prompt:**
```text
Implement backend/agents/data_scout_agent.py with DataScoutAgent class inheriting from BaseAgent.
This agent collects live market data (ticks, orderbook) and external data.
Normalize data into a standard Observation pydantic model for the SensoryProcessor.
Use dependency injection for market clients. Ensure robust error handling.
```

**Context:**
- Dependencies: `BaseAgent`, `ExchangeAdapter`
- Output: `Observation` model

**Happy Path Test:**
```python
# backend/tests/test_agents_specialized.py
@pytest.mark.asyncio
async def test_data_scout_observation():
    agent = DataScoutAgent(market_client=MockClient())
    obs = await agent.observe("BTC-EUR")
    assert obs.price > 0
    assert obs.symbol == "BTC-EUR"
    assert "bids" in obs.orderbook
```

**Implementation Snippet:**
```python
# backend/agents/data_scout_agent.py
class Observation(BaseModel):
    symbol: str
    price: float
    volume: float
    orderbook: Dict[str, Any]
    timestamp: datetime

class DataScoutAgent(BaseAgent):
    async def observe(self, symbol: str) -> Observation:
        # Fetch and normalize
        return Observation(...)
```

---

## Epic 3: Analyst Agents (Orient)

### Task 3.1: TechnicalAnalyst Agent

**Master Prompt:**
```text
Implement backend/agents/analyst_agent.py with TechnicalAnalyst class.
Calculate indicators (RSI, MACD, Bollinger) using numpy/pandas/talib from price history.
Output an Orientation object with indicators, regime detection, and confidence score.
```

**Context:**
- Input: `Observation` + Price History
- Output: `Orientation` model

**Happy Path Test:**
```python
async def test_ta_indicators():
    agent = TechnicalAnalyst()
    prices = [100, 102, 105, ...] # 20+ points
    orientation = await agent.analyze(features={"prices": prices}, context={"symbol":"BTC"})
    assert "rsi" in orientation.indicators
    assert orientation.confidence > 0.0
```

**Implementation Snippet:**
```python
# backend/agents/analyst_agent.py
class TechnicalAnalyst(BaseAgent):
    async def analyze(self, features, context):
        prices = features['prices']
        rsi = self._calculate_rsi(prices)
        regime = self._classify_regime(rsi)
        return Orientation(indicators={'rsi': rsi}, regime=regime)
```

### Task 3.2: Researcher Agents (Debate)

**Master Prompt:**
```text
Implement backend/agents/researcher_agent.py with BullResearcher and BearResearcher classes.
These agents perform RAG searches on VectorMemory to find supporting evidence for their bias.
Bull focuses on positive signals/news; Bear focuses on risks/resistance.
Output a structured Argument object.
```

**Context:**
- Dependencies: `VectorMemory`, `BaseAgent`

**Happy Path Test:**
```python
async def test_bull_bear_debate():
    bull = BullResearcher(vector_memory=mock_vm)
    bear = BearResearcher(vector_memory=mock_vm)
    
    bull_arg = await bull.research("BTC")
    bear_arg = await bear.research("BTC")
    
    assert bull_arg.sentiment == "positive"
    assert bear_arg.sentiment == "negative"
    assert len(bull_arg.rag_references) > 0
```

---

## Epic 4: Risk Manager (Decide - Constraint)

### Task 4.1: RiskManagerAgent

**Master Prompt:**
```text
Implement backend/agents/risk_manager_agent.py.
This agent acts as a gatekeeper. It accepts a TradeProposal and validates it against hard policies:
1. Max Drawdown check
2. Position Sizing limit (e.g., max 5% of portfolio)
3. Asset Blacklist
Returns a RiskAssessment with approved=True/False and modified sizing if needed.
```

**Context:**
- Input: `TradeProposal`, `PortfolioState`
- Output: `RiskAssessment`

**Happy Path Test:**
```python
async def test_risk_checks():
    risk_agent = RiskManagerAgent(config={"max_position_size": 0.05})
    
    # Proposal too large (10%)
    proposal = TradeProposal(symbol="BTC", size=0.10) 
    assessment = await risk_agent.evaluate(proposal, portfolio_value=1000)
    
    assert assessment.approved == False
    assert "size_limit_exceeded" in assessment.reason
```

**Implementation Snippet:**
```python
# backend/agents/risk_manager_agent.py
class RiskManagerAgent(BaseAgent):
    async def evaluate(self, proposal: TradeProposal, portfolio: PortfolioState) -> RiskAssessment:
        if proposal.size * proposal.price > portfolio.total_value * self.max_pos_limit:
             return RiskAssessment(approved=False, reason="Exposure limit")
        return RiskAssessment(approved=True)
```

---

## Epic 5: Trader Agent (Decide - Plan)

### Task 5.1: TraderAgent Implementation

**Master Prompt:**
```text
Implement backend/agents/trader_agent.py.
The TraderAgent synthesizes inputs from Analysts (Orientation) and Researchers (Arguments).
It formulates a TradeProposal (Entry, StopLoss, TakeProfit, Size).
It MUST consult the LLM to generate the strategy rationale based on the inputs.
```

**Context:**
- Input: `Orientation`, `List[Argument]`
- Output: `TradeProposal`

**Happy Path Test:**
```python
async def test_trader_synthesis():
    trader = TraderAgent()
    orientation = Orientation(regime="trending_up", indicators={"rsi": 30})
    proposal = await trader.plan_trade(orientation)
    
    assert proposal.side == "buy"
    assert proposal.stop_loss < proposal.entry_price
    assert len(proposal.rationale) > 0
```

---

## Epic 6: Fund Manager (Decide - Allocate)

### Task 6.1: FundManagerAgent

**Master Prompt:**
```text
Implement backend/agents/fund_manager_agent.py.
This meta-agent oversees multiple TraderAgents.
It receives TradeProposals and decides on final allocation based on global portfolio correlation and cash availability.
It resolves conflicts if multiple traders want to buy the same asset or exceed leverage.
```

**Context:**
- Input: `List[TradeProposal]`, `PortfolioState`
- Output: `List[ExecutionPlan]`

**Happy Path Test:**
```python
async def test_fund_allocation():
    manager = FundManagerAgent()
    prop1 = TradeProposal(symbol="BTC", size=1000) # Valid
    prop2 = TradeProposal(symbol="ETH", size=5000) # Exceeds cash
    
    decisions = await manager.allocate([prop1, prop2], cash_balance=2000)
    
    assert len(decisions) == 1
    assert decisions[0].symbol == "BTC"
    # ETH rejected or resized
```

---

## Epic 7: OODA Orchestrator

### Task 7.1: OODALoopCoordinator

**Master Prompt:**
```text
Implement backend/orchestration/ooda_coordinator.py.
Create the OODALoopCoordinator class that binds all agents together.
Implement the `run_cycle()` method that executes:
1. Observe (DataScout)
2. Orient (Analyst, Researcher -> VectorMemory)
3. Decide (Trader -> FundManager -> RiskManager)
4. Act (Execution)
Ensure steps are async and data flows correctly between stages.
```

**Context:**
- Dependencies: All Agents, `SystemIdentity`

**Happy Path Test:**
```python
# backend/tests/test_ooda_coordinator.py
async def test_ooda_cycle():
    coord = OODALoopCoordinator(agents=...)
    result = await coord.run_cycle(symbol="BTC-EUR")
    
    assert "observation" in result
    assert "decision" in result
    assert result["status"] == "cycle_complete"
```

**Implementation Snippet:**
```python
# backend/orchestration/ooda_coordinator.py
class OODALoopCoordinator:
    async def run_cycle(self, symbol):
        obs = await self.data_scout.observe(symbol)
        orient = await self.analyst.analyze(obs)
        # RAG enrichment
        proposal = await self.trader.plan_trade(orient)
        audit = await self.risk_manager.evaluate(proposal)
        
        if audit.approved:
             res = await self.executor.execute(proposal)
             return res
```

---

## Epic 8: Execution & Hot Path

### Task 8.1: FastConfig & HotPathEngine

**Master Prompt:**
```text
Implement backend/execution/hot_path_engine.py and fast_config.py.
FastConfig should use a shared structure (or simple in-memory dict for now) to pass approved strategies to the hot path.
HotPathEngine executes orders immediately when price triggers match, bypassing LLM layers.
Implement `check_triggers()` which runs on every tick.
```

**Context:**
- Performance is key. No API calls in the trigger loop.

**Happy Path Test:**
```python
async def test_hot_path_trigger():
    engine = HotPathEngine()
    # Strategy: Buy if price < 49000
    engine.load_strategy(symbol="BTC", trigger_price=49000, side="buy")
    
    # Tick 50000 -> No act
    await engine.process_tick(price=50000)
    assert engine.orders_sent == 0
    
    # Tick 48900 -> Act
    await engine.process_tick(price=48900)
    assert engine.orders_sent == 1
```

---

## Epic 9: Governance & Integration

### Task 9.1: DecisionAuditLog & Watchdog

**Master Prompt:**
```text
Implement backend/core/compliance/audit_logger.py and watchdog_agent.py.
DecisionAuditLog must record the UUID trace of every OODA cycle, including all inputs and reasoning.
WatchdogAgent must run in parallel, checking heartbeats of the Coordinator. If the loop stalls > 60s, trigger a circuit breaker (cancel all open orders).
```

**Context:**
- Critical for safety.

**Happy Path Test:**
```python
async def test_audit_logging():
    logger = DecisionAuditLog()
    await logger.log_cycle(trace_id="abc", inputs={...}, decision="BUY")
    # Verify DB insertion
    
async def test_watchdog_circuit_breaker():
    dog = WatchdogAgent(timeout=1)
    # Simulate stall
    await asyncio.sleep(1.1)
    await dog.monitor()
    assert dog.circuit_broken == True
```
