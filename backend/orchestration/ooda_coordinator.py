"""
OODA Loop Coordinator - Central Orchestration.

Coordineert de volledige Observe -> Orient -> Decide -> Act cyclus.
Unified Consciousness Architecture - Geïntegreerd met:
- CognitiveOrchestrator (message bus & agent registry)
- NavagrahaService (cosmic time & trading gates)
- SystemIdentity (36-Tattva consciousness)
- RiskOrchestrator (pre-trade risk validation)
- KarmaRegister (learning feedback loop)
"""

import logging
import time
import uuid
from collections.abc import Callable
from enum import Enum
from typing import Any, AsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.karma.karma_register import KarmaRegister, TradeOutcome
from backend.core.schemas.ooda_types import (
    CapitalAllocation,
    ExecutionPlan,
    Observation,
    Orientation,
    PortfolioState,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)
from backend.core.system_identity import SystemIdentity
from backend.execution.fast_config import FastConfig
from backend.execution.order_executor import OrderExecutor
from backend.governance.circuit_breaker import CircuitBreaker, CircuitBreakerTrippedError
from backend.governance.decision_audit import AuditLogger
from backend.risk.risk_orchestrator import RiskOrchestrator

logger = logging.getLogger(__name__)


class TradingMode(str, Enum):
    """Trading execution mode."""

    NOTIFY_ONLY = "notify_only"  # Stop na RiskAssessment, human approval required
    AUTO = "auto"  # Volledig geautomatiseerd


class OODALoopCoordinator:
    """
    OODA Loop Coordinator.

    Orkestreert multi-agent trading pipeline:
    1. OBSERVE: DataScout -> Observation
    2. ORIENT: CognitiveBridge + Analyst -> Orientation
    3. DECIDE: Trader + RiskManager -> TradeProposal + RiskAssessment
    4. HARMONIZE: Orchestrator -> Harmony check
    5. ACT: [Execution] -> ExecutionOutcome
    """

    def __init__(
        self,
        data_scout: DataScoutAgent,
        analyst: AnalystAgent,
        trader: TraderAgent,
        risk_manager: RiskManagerAgent,
        fund_manager: Any,  # Avoid circular import, type is FundManagerAgent
        bull_researcher: Any,  # Avoid circular import, type is BullResearcher
        bear_researcher: Any,  # Avoid circular import, type is BearResearcher
        cognitive_bridge: CognitiveBridge,
        orchestrator: OrchestratorAgent | None = None,
        order_executor: OrderExecutor | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        trading_mode: TradingMode = TradingMode.NOTIFY_ONLY,
        rag_retriever: Any | None = None,
        audit_session_factory: Callable[[], AsyncContextManager[AsyncSession]] | None = None,
        # === UNIFIED CONSCIOUSNESS INTEGRATION (Phase A-E) ===
        cognitive_orchestrator: Any | None = None,  # CognitiveOrchestrator
        navagraha_service: Any | None = None,  # NavagrahaService
        system_identity: SystemIdentity | None = None,  # SystemIdentity (36-Tattva)
        risk_orchestrator: RiskOrchestrator | None = None,  # RiskOrchestrator
        karma_register: KarmaRegister | None = None,  # KarmaRegister
        vedastro_agent: Any | None = None,  # VedastroSignalAgent (Exo-System)
        elemental_orchestrator: Any | None = None,  # ElementalOrchestrator
        clickhouse_client: Any | None = None,  # ClickHouseClient
    ):
        """
        Initialiseer OODA Coordinator.

        Args:
            data_scout: DataScoutAgent instance
            analyst: AnalystAgent instance
            trader: TraderAgent instance
            risk_manager: RiskManagerAgent instance
            fund_manager: FundManagerAgent instance
            bull_researcher: BullResearcher instance
            bear_researcher: BearResearcher instance
            cognitive_bridge: CognitiveBridge instance
            orchestrator: OrchestratorAgent (Cognitive Core) voor harmony checks
            order_executor: Order execution engine
            circuit_breaker: Optional CircuitBreaker voor safety
            trading_mode: Execution mode (notify_only / auto)
            rag_retriever: Optional RAG retriever voor historical context
            audit_session_factory: Optional session factory voor audit logging
            # Unified Consciousness
            cognitive_orchestrator: CognitiveOrchestrator voor message bus & guna balance
            navagraha_service: NavagrahaService voor cosmic time & trading gates
            system_identity: SystemIdentity voor 36-Tattva consciousness
            risk_orchestrator: RiskOrchestrator voor pre-trade risk validation
            karma_register: KarmaRegister voor learning feedback loop
        """
        # Core OODA agents
        self.data_scout = data_scout
        self.analyst = analyst
        self.trader = trader
        self.risk_manager = risk_manager
        self.fund_manager = fund_manager
        self.bull_researcher = bull_researcher
        self.bear_researcher = bear_researcher
        self.cognitive_bridge = cognitive_bridge
        self.orchestrator = orchestrator
        self.order_executor = order_executor
        self.circuit_breaker = circuit_breaker
        self.trading_mode = trading_mode
        self.rag_retriever = rag_retriever
        self.audit_session_factory = audit_session_factory

        # === UNIFIED CONSCIOUSNESS INTEGRATION ===
        self.cognitive_orchestrator = cognitive_orchestrator
        self.navagraha_service = navagraha_service
        self.system_identity = system_identity
        self.risk_orchestrator = risk_orchestrator
        self.karma_register = karma_register
        self.vedastro_agent = vedastro_agent
        self.elemental_orchestrator = elemental_orchestrator
        self.clickhouse_client = clickhouse_client

        # Inject ClickHouse client into agents
        self._inject_database_into_agents()

        # Runtime state
        self.cycles_completed = 0
        self._current_guna = None  # GunaDistribution from Navagraha
        self._current_tattva_state = None  # Tattva state from SystemIdentity

        # Log unified consciousness status
        logger.info(
            f"OODA Coordinator initialized (UNIFIED CONSCIOUSNESS MODE)\n"
            f"  mode={trading_mode.value}, "
            f"circuit_breaker={'enabled' if circuit_breaker else 'disabled'}, "
            f"orchestrator={'enabled' if orchestrator else 'disabled'}, "
            f"audit_logger={'enabled' if audit_session_factory else 'disabled'}\n"
            f"  cognitive_orchestrator={'enabled' if cognitive_orchestrator else 'disabled'}, "
            f"navagraha_service={'enabled' if navagraha_service else 'disabled'}, "
            f"system_identity={'enabled' if system_identity else 'disabled'}\n"
            f"  risk_orchestrator={'enabled' if risk_orchestrator else 'disabled'}, "
            f"karma_register={'enabled' if karma_register else 'disabled'}\n"
            f"  clickhouse_persistence={'enabled' if clickhouse_client else 'disabled'}"
        )

    def _inject_database_into_agents(self) -> None:
        """Inject ClickHouse client into all participating agents for persistence."""
        if not self.clickhouse_client:
            return

        agents = [
            self.data_scout,
            self.analyst,
            self.trader,
            self.risk_manager,
            self.fund_manager,
            self.bull_researcher,
            self.bear_researcher,
            self.orchestrator,
            self.vedastro_agent,
            self.elemental_orchestrator,
        ]

        for agent in agents:
            if agent and hasattr(agent, "clickhouse_client"):
                agent.clickhouse_client = self.clickhouse_client
                logger.debug(f"Injected ClickHouse client into {agent.agent_name}")

    async def run_cycle(
        self, symbol: str, current_price: float, strategy_id: str = "momentum_v1"
    ) -> dict[str, Any]:
        """
        Voer één complete OODA cyclus uit.

        Args:
            symbol: Trading pair
            current_price: Current market price (voor entry calculation)
            strategy_id: Strategy identifier

        Returns:
            Dict met cyclus resultaat
        """
        trace_id = str(uuid.uuid4())

        # Check FastConfig overrides
        try:
            config = FastConfig.read()
            action_override = config.get("action", 0)
            if action_override != 0:
                logger.warning(f"Manual override active: action={action_override}")
        except Exception:
            pass

        # === NAVAGRAHA PRE-CHECK (Phase B) ===
        if self.navagraha_service:
            try:
                from backend.core.config.settings import settings

                nava_state = await self.navagraha_service.get_current_state(
                    lat=settings.LATITUDE, lon=settings.LONGITUDE
                )
                self._current_guna = nava_state.guna_distribution

                if not nava_state.trading_gate_open:
                    logger.warning(
                        f"[{trace_id}] Rahu Kala active or high tamas - trading gate CLOSED"
                    )
                    return {
                        "trace_id": trace_id,
                        "symbol": symbol,
                        "decision": "BLOCKED_BY_CONSCIOUSNESS_GATE",
                        "gate_open": False,
                        "rahu_kala_active": nava_state.rahu_kala_active,
                        "guna_distribution": nava_state.guna_distribution.model_dump(),
                        "consciousness_level": nava_state.consciousness_level,
                    }

                logger.debug(
                    f"[{trace_id}] Trading gate OPEN - consciousness: {nava_state.consciousness_level}"
                )
            except Exception as e:
                logger.warning(f"Navagraha check failed (proceeding): {e}")

        # === SYSTEM IDENTITY PRE-CHECK (Phase B) ===
        if self.system_identity:
            try:
                # Check Kanchuka risk gate (layers 6-12)
                tattva_risk = self._get_tattva_risk_gate_state()
                if tattva_risk.get("risk_gate_blocked"):
                    logger.warning(
                        f"[{trace_id}] Tattva risk gate blocked - Kanchuka restrictions active"
                    )
                    # Don't block, but log and reduce confidence
                    self._current_tattva_state = tattva_risk
            except Exception as e:
                logger.warning(f"SystemIdentity check failed (proceeding): {e}")

        # === COGNITIVE ORCHESTRATOR MARKET TICK (Phase A) ===
        if self.cognitive_orchestrator:
            try:
                # Delegate market data processing to CognitiveOrchestrator
                await self.cognitive_orchestrator.handle_market_tick(
                    {
                        "symbol": symbol,
                        "price": current_price,
                        "event_type": "ticker",
                        "venue": "unified_ooda",
                        "ts_exchange": time.time(),
                    }
                )
            except Exception as e:
                logger.warning(f"CognitiveOrchestrator market tick failed: {e}")

        return await self._execute_ooda_loop(symbol, current_price, strategy_id, trace_id)

    async def _execute_ooda_loop(
        self,
        symbol: str,
        current_price: float,
        strategy_id: str,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Internal execution of the loop.

        Returns:
            Dict met cycle results en decision
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        logger.info(f"Starting OODA cycle for {symbol} (trace_id={trace_id})")

        try:
            # ========== SAFETY CHECK ==========
            if self.circuit_breaker:
                if await self.circuit_breaker.is_tripped():
                    reason = await self.circuit_breaker.get_trip_reason()
                    logger.error(f"Circuit breaker TRIPPED ({reason}) - halting cycle")
                    raise CircuitBreakerTrippedError(
                        f"Trading halted: circuit breaker tripped ({reason})"
                    )

            # ========== OBSERVE ==========
            observation = await self._observe(symbol, trace_id)

            # ========== ORIENT ==========
            orientation, bull_hypothesis, bear_hypothesis = await self._orient(observation)

            # ========== DECIDE ==========
            proposal, risk_assessment, capital_allocation = await self._decide(
                orientation, current_price, strategy_id
            )

            # ========== HARMONIZE (Orchestrator) ==========
            harmony_result = None
            if self.orchestrator:
                proposals = [proposal] if proposal else []
                assessments = [risk_assessment] if risk_assessment else []
                harmony_result = await self.orchestrator.harmonize(
                    observation=observation,
                    orientation=orientation,
                    bull_hypothesis=bull_hypothesis,
                    bear_hypothesis=bear_hypothesis,
                    proposals=proposals,
                    risk_assessments=assessments,
                )
                logger.info(
                    f"[HARMONIZE] status={harmony_result['status']}, "
                    f"harmony={harmony_result['harmony_score']}"
                )

            # ========== ACT (conditional) ==========
            execution_result = None
            if self.trading_mode == TradingMode.AUTO:
                if risk_assessment and risk_assessment.decision == RiskDecision.APPROVE:
                    # check capital allocation approval
                    if capital_allocation and capital_allocation.approved:
                        if self.order_executor:
                            execution_result = await self._act(
                                proposal, capital_allocation, trace_id, current_price
                            )
                        else:
                            logger.warning("Auto mode active but no OrderExecutor configured!")
                            execution_result = {
                                "status": "skipped",
                                "reason": "No executor",
                            }
                    else:
                        logger.info(
                            f"Capital Allocation rejected: {capital_allocation.reasoning if capital_allocation else 'None'}"
                        )
                else:
                    logger.info(
                        f"Trade rejected, skipping execution: {risk_assessment.rationale if risk_assessment else 'No proposal'}"
                    )
            else:
                logger.info(f"Notify-Only mode: Skipping execution for {symbol}")

            # === KARMA FEEDBACK LOOP (Phase E) ===
            if self.karma_register and execution_result:
                try:
                    # Convert execution result to TradeOutcome
                    outcome = TradeOutcome(
                        pnl_percent=execution_result.get("pnl_percent", 0.0),
                        drawdown_percent=execution_result.get("drawdown_percent", 0.0),
                        execution_speed_ms=execution_result.get("execution_time_ms", 0.0),
                        compliance_violation=execution_result.get("compliance_error", False),
                    )
                    # Record action for learning
                    self.karma_register.register_feedback(
                        agent_name="trader_agent",
                        outcome=outcome,
                    )
                    logger.debug(f"Karma feedback recorded for trace_id={trace_id}")
                except Exception as e:
                    logger.warning(f"Karma feedback failed: {e}")

            # === CONSCIOUSNESS UPDATE (Phase E) ===
            if self.system_identity and execution_result:
                try:
                    # Calculate outcome score from execution
                    outcome_score = 0.0
                    if execution_result.get("status") == "executed":
                        outcome_score = execution_result.get("pnl_percent", 0.0)

                    self.system_identity.update_outcome(
                        action_id=hash(trace_id) % 10000,  # Simple ID generation
                        outcome=outcome_score,
                    )
                    logger.debug(f"SystemIdentity updated with outcome for trace_id={trace_id}")
                except Exception as e:
                    logger.warning(f"SystemIdentity update failed: {e}")

            self.cycles_completed += 1

            # Compile results
            result = {
                "trace_id": trace_id,
                "symbol": symbol,
                "observation": observation,
                "orientation": orientation,
                "research": {"bull": bull_hypothesis, "bear": bear_hypothesis},
                "proposal": proposal,
                "risk_assessment": risk_assessment,
                "capital_allocation": capital_allocation,
                "harmony": harmony_result,
                "execution": execution_result,
                "mode": self.trading_mode.value,
                "decision": self._get_decision_summary(proposal, risk_assessment),
            }

            # ========== AUDIT LOGGING ==========
            if self.audit_session_factory:
                try:
                    # Serialize execution_result (can be Pydantic model or dict)
                    exec_data = None
                    if execution_result is not None:
                        if hasattr(execution_result, "model_dump"):
                            exec_data = execution_result.model_dump(mode="json")
                        elif isinstance(execution_result, dict):
                            exec_data = execution_result
                        else:
                            exec_data = {"raw": str(execution_result)}

                    async with self.audit_session_factory() as session:
                        audit_logger = AuditLogger(session)
                        await audit_logger.log_decision(
                            trace_id=trace_id,
                            symbol=symbol,
                            observation=(
                                observation.model_dump(mode="json") if observation else None
                            ),
                            orientation=(
                                orientation.model_dump(mode="json") if orientation else None
                            ),
                            proposal=(proposal.model_dump(mode="json") if proposal else None),
                            risk_assessment=(
                                risk_assessment.model_dump(mode="json") if risk_assessment else None
                            ),
                            execution=exec_data,
                            decision_summary=result["decision"],
                            trading_mode=self.trading_mode.value,
                            strategy_id=strategy_id,
                        )
                except Exception as e:
                    logger.error(f"Failed to persist audit log: {e}", exc_info=True)

            logger.info(f"Cycle complete: {result['decision']}")

            return result

        except Exception as e:
            logger.error(f"OODA cycle failed: {e}", exc_info=True)
            raise

    async def _observe(self, symbol: str, trace_id: str) -> Observation:
        """OBSERVE fase."""
        logger.debug(f"[{trace_id}] OBSERVE: {symbol}")

        observation = await self.data_scout.observe(
            symbol=symbol,
            trace_id=trace_id,
            include_orderbook=True,
            include_funding=True,
        )

        return observation

    async def _orient(self, observation: Observation) -> tuple[Orientation, Any, Any]:
        """ORIENT fase."""
        logger.debug(f"[ORIENT] {observation.symbol}")

        # 1. Process door cognitive core
        core_sentiment = await self.cognitive_bridge.process_observation(observation)

        # 1b. Inject Guna Balance van CognitiveOrchestrator (Phase A)
        guna_context = None
        if self.cognitive_orchestrator:
            guna_context = self.cognitive_orchestrator.current_guna_balance

        # 2. Fetch RAG context (optioneel)
        rag_context = []
        if self.rag_retriever:
            try:
                rag_context = await self.rag_retriever.search_similar(
                    query=f"{observation.symbol} market analysis",
                    category="strategy",
                    limit=3,
                )
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")

        # 2b. Vedastro Oracle (Pre-Orient)
        if self.vedastro_agent:
            try:
                v_result = await self.vedastro_agent.analyze(
                    features={"symbol": observation.symbol, "price": observation.close_price},
                    context={},
                )
                if v_result:
                    action = v_result.get("action", "hold")
                    conf = v_result.get("confidence", 0.0)
                    reason = v_result.get("reason", "")
                    rag_context.append(
                        f"VEDASTRO_SIGNAL: {action.upper()} (conf: {conf:.2f}) - {reason}"
                    )
                    logger.debug(
                        f"[ORIENT] Vedastro Pre-Orient Signal: {action.upper()} (conf: {conf:.2f})"
                    )
            except Exception as e:
                logger.warning(f"Vedastro Oracle failed (proceeding): {e}")

        # 3. Analyst orientation (met guna context)
        orientation = await self.analyst.orient(
            observation=observation,
            core_sentiment=core_sentiment,
            rag_context=rag_context,
        )

        # Apply guna modulation to confidence (Phase B)
        # Since Orientation is frozen, we create a new instance with modulated confidence
        if guna_context:
            # Reduce confidence when tamas is high
            tamas_penalty = max(0, guna_context.tamas - 0.33) * 0.5
            modulated_confidence = max(0.0, orientation.confidence - tamas_penalty)

            if modulated_confidence != orientation.confidence:
                # Create new Orientation with modulated confidence
                orientation_data = orientation.model_dump()
                orientation_data["confidence"] = modulated_confidence
                orientation = Orientation(**orientation_data)
                logger.debug(
                    f"Guna modulation applied: tamas_penalty={tamas_penalty:.3f}, new_confidence={modulated_confidence:.3f}"
                )

        # 4. Contrarian Research (Parallel)
        bull_hypothesis = await self.bull_researcher.generate_hypothesis(
            symbol=observation.symbol, market_data=observation, analyst_view=orientation
        )

        bear_hypothesis = await self.bear_researcher.generate_hypothesis(
            symbol=observation.symbol, market_data=observation, analyst_view=orientation
        )

        return orientation, bull_hypothesis, bear_hypothesis

    async def _decide(
        self, orientation: Orientation, current_price: float, strategy_id: str
    ) -> tuple[TradeProposal | None, RiskAssessment | None, CapitalAllocation | None]:
        """DECIDE fase."""
        logger.debug(f"[DECIDE] {orientation.symbol}")

        # === TATTVA RISK FILTER (Kanchuka laag 6-12) (Phase B) ===
        if self.system_identity and self._current_tattva_state:
            if self._current_tattva_state.get("risk_gate_blocked"):
                logger.info("Tattva risk gate blocked - reducing position confidence")
                # Reduce orientation confidence (create new frozen instance)
                reduced_confidence = orientation.confidence * 0.5
                orientation_data = orientation.model_dump()
                orientation_data["confidence"] = reduced_confidence
                orientation = Orientation(**orientation_data)

        # 1. Trader genereert proposal
        proposal = await self.trader.propose_trade(
            orientation=orientation,
            current_price=current_price,
            strategy_id=strategy_id,
        )

        if proposal is None:
            logger.info("No trade signal from Trader")
            return None, None, None

        # === ELEMENTAL ORCHESTRATOR FALLBACK (Micro-Swarm) ===
        if proposal.confidence < 0.60 and self.elemental_orchestrator:
            logger.info(
                f"Trader proposal confidence low ({proposal.confidence:.2f}). Consulting ElementalOrchestrator fallback."
            )

            elemental_signal = {
                "inputs": {
                    "air": {"sentiment": orientation.core_sentiment},
                    "water": {"regime": orientation.regime.value},
                    "fire": {"approved": True},
                    "earth": {"valuation_gap": 0},
                }
            }
            fallback_result = await self.elemental_orchestrator.process_signal(elemental_signal)

            harmony_score = fallback_result.get("harmony_score", 0.5)
            synthesis = fallback_result.get("synthesis", {})

            logger.info(
                f"ElementalOrchestrator harmony: {harmony_score:.2f}, action: {synthesis.get('summary')}"
            )

            if harmony_score < 0.4:
                logger.warning("ElementalOrchestrator rejects cohesion. Abandoning trade.")
                from backend.core.schemas.ooda_types import RiskAssessment, RiskDecision

                risk_assessment = RiskAssessment(
                    decision=RiskDecision.REJECT,
                    risk_score=1.0,
                    rationale=f"ElementalOrchestrator blocked: harmony {harmony_score:.2f} too low",
                    var_95=None,
                    max_drawdown_pct=None,
                    recommended_position_size=0.0,
                )
                return proposal, risk_assessment, None
            elif harmony_score > 0.7:
                logger.info("ElementalOrchestrator confirms macro-harmony. Boosting confidence.")
                proposal.confidence = max(proposal.confidence, 0.65)

        # === RISK ORCHESTRATOR (Kanchuka-laag) (Phase C) ===
        if self.risk_orchestrator:
            try:
                from backend.risk.risk_orchestrator import TradeSignal

                portfolio = self._get_portfolio_state()

                # Convert proposal to TradeSignal
                signal = TradeSignal(
                    symbol=proposal.symbol,
                    side=proposal.side,
                    entry_price=proposal.entry_price,
                    stop_price=proposal.stop_loss,
                    confidence=proposal.confidence,
                    reward_to_risk=(
                        (proposal.take_profit - proposal.entry_price)
                        / (proposal.entry_price - proposal.stop_loss)
                        if proposal.side == "buy"
                        else (proposal.entry_price - proposal.take_profit)
                        / (proposal.stop_loss - proposal.entry_price)
                    ),
                    strategy=strategy_id,
                )

                # Get guna confidence for risk modulation

                risk_check = self.risk_orchestrator.pre_trade_check(
                    signal=signal,
                    portfolio_value=portfolio.total_equity,
                    current_positions_count=portfolio.num_open_positions,
                )

                if not risk_check.approved:
                    logger.warning(f"RiskOrchestrator blocked: {risk_check.reason}")
                    # Create rejection risk assessment
                    risk_assessment = RiskAssessment(
                        decision=RiskDecision.REJECT,
                        risk_score=1.0,
                        rationale=f"RiskOrchestrator: {risk_check.reason}",
                        var_95=None,
                        max_drawdown_pct=None,
                        recommended_position_size=0.0,
                    )
                    return proposal, risk_assessment, None

                # Apply recommended quantity from RiskOrchestrator
                if risk_check.recommended_quantity > 0:
                    logger.info(
                        f"RiskOrchestrator recommends quantity: {risk_check.recommended_quantity:.4f} "
                        f"(method: {risk_check.sizing_method})"
                    )

            except Exception as e:
                logger.warning(f"RiskOrchestrator check failed (proceeding): {e}")

        # 2. RiskManager beoordeelt proposal
        risk_assessment = await self.risk_manager.assess_risk(
            proposal=proposal,
            current_regime=orientation.regime,
            current_position_size=0.0,  # TODO: Track actual position
        )

        # 3. FundManager (Capital Allocation)
        capital_allocation = None
        if risk_assessment.decision == RiskDecision.APPROVE:
            capital_allocation = await self.fund_manager.allocate_capital(
                trade_proposal=proposal,
                risk_assessment=risk_assessment,
                portfolio_state=self._get_portfolio_state(),
            )

        return proposal, risk_assessment, capital_allocation

    async def _act(
        self,
        proposal: TradeProposal,
        allocation: CapitalAllocation,
        trace_id: str,
        current_price: float,
    ) -> dict[str, Any]:
        """
        ACT fase - Executes the trade via OrderExecutor.
        """
        logger.info(f"[ACT] Executing trade for {proposal.symbol} (trace_id={trace_id})")

        if not self.order_executor:
            return {"status": "failed", "error": "No OrderExecutor configured"}

        # Create execution plan from proposal and allocation
        plan = ExecutionPlan(
            trace_id=trace_id,
            symbol=proposal.symbol,
            side=proposal.side,
            quantity=(allocation.position_size_usd / current_price if current_price > 0 else 0.0),
            order_type="market",  # Defaulting to market for OODA v1
            price=None,  # Proposal.entry_price could be used for limit
            expected_price=proposal.entry_price or current_price,
            params={"max_slippage": 50},
            caller_name=self.trader.agent_name,
            caller_role=self.trader.agent_role,
        )

        # Execute
        outcome = await self.order_executor.execute_trade(plan)

        return {
            "status": "executed" if outcome.success else "failed",
            "outcome": (
                outcome.model_dump(mode="json") if hasattr(outcome, "model_dump") else str(outcome)
            ),
            "message": (
                outcome.error
                if not outcome.success
                else f"Filled {outcome.filled_qty} @ {outcome.avg_price}"
            ),
        }

    def _get_portfolio_state(self) -> PortfolioState:
        """
        Get current portfolio state for FundManager.
        TODO: Connect to real Portfolio/Account service.
        """
        return PortfolioState(
            total_equity=10000.0,  # Mock $10k account
            available_capital=10000.0,
            total_exposure_pct=0.0,
            num_open_positions=0,
        )

    def _get_decision_summary(
        self,
        proposal: TradeProposal | None,
        risk_assessment: RiskAssessment | None,
    ) -> str:
        """Creëer human-readable decision summary."""
        if proposal is None:
            return "NO_SIGNAL"

        if risk_assessment is None:
            return "PROPOSAL_GENERATED"

        decision = risk_assessment.decision.value.upper()

        if decision == "APPROVE":
            return f"APPROVED: {proposal.side.upper()} {proposal.symbol}"
        elif decision == "REJECT":
            return f"REJECTED: {risk_assessment.rationale[:50]}"
        else:
            return f"MODIFIED: {decision}"

    async def set_trading_mode(
        self,
        new_mode: TradingMode,
        user_id: str,
        reason: str | None = None,
        permission_service: Any | None = None,
    ) -> bool:
        """
        Change trading mode met RBAC enforcement.

        Args:
            new_mode: Nieuwe trading mode
            user_id: User die change wil maken
            reason: Optionele reden voor change
            permission_service: PermissionService voor authorization

        Returns:
            True if successful

        Raises:
            PermissionDeniedError: Als user geen permissie heeft
        """
        # Import here to avoid circular dependency
        from backend.governance.trading_permissions import get_required_permission_for_mode

        # Permission check
        if permission_service:
            required_perm = get_required_permission_for_mode(new_mode.value)
            permission_service.require_permission(user_id, required_perm)

            # Log change
            await permission_service.log_mode_change(
                user_id=user_id,
                previous_mode=self.trading_mode.value,
                new_mode=new_mode.value,
                reason=reason,
            )

        # Apply change
        old_mode = self.trading_mode
        self.trading_mode = new_mode

        logger.warning(
            f"[WARNING] TRADING_MODE CHANGED: {old_mode.value} -> {new_mode.value} "
            f"(user={user_id}, reason={reason or 'N/A'})"
        )

        return True

    def get_trading_mode(self) -> TradingMode:
        """
        Get current trading mode.

        Returns:
            Current TradingMode
        """
        return self.trading_mode

    def _get_tattva_risk_gate_state(self) -> dict[str, Any]:
        """
        Evaluate Kanchuka Tattvas (layers 6-12) for risk gate state.

        Returns:
            Dict with risk_gate_blocked, confidence_multiplier, etc.
        """
        if not self.system_identity:
            return {"risk_gate_blocked": False, "confidence_multiplier": 1.0}

        try:
            # Get current tattva coherence
            tattva_coherence = self.system_identity.system_state.get("tattva_coherence", {})

            # Kanchuka layers: 6-12
            kanchuka_layers = range(6, 13)
            kanchuka_coherence = [
                tattva_coherence.get(str(layer), 1.0) for layer in kanchuka_layers
            ]
            avg_kanchuka_coherence = (
                sum(kanchuka_coherence) / len(kanchuka_coherence) if kanchuka_coherence else 1.0
            )

            # If Kanchuka coherence is low, block high-risk trades
            risk_gate_blocked = avg_kanchuka_coherence < 0.7

            # Confidence multiplier based on Kanchuka coherence
            confidence_multiplier = 0.5 + (avg_kanchuka_coherence * 0.5)

            return {
                "risk_gate_blocked": risk_gate_blocked,
                "confidence_multiplier": confidence_multiplier,
                "avg_kanchuka_coherence": avg_kanchuka_coherence,
            }
        except Exception as e:
            logger.warning(f"Error getting tattva risk gate state: {e}")
            return {"risk_gate_blocked": False, "confidence_multiplier": 1.0}

    @property
    def current_guna_balance(self) -> Any | None:
        """Return current guna balance from CognitiveOrchestrator or Navagraha."""
        if self.cognitive_orchestrator:
            return self.cognitive_orchestrator.current_guna_balance
        return self._current_guna

    def get_unified_consciousness_state(self) -> dict[str, Any]:
        """
        Get complete unified consciousness state.

        Returns:
            Dict with all consciousness components' states
        """
        state = {
            "ooda_cycles_completed": self.cycles_completed,
            "trading_mode": self.trading_mode.value,
            "components": {},
        }

        if self.navagraha_service:
            state["components"]["navagraha"] = {
                "enabled": True,
                "current_guna": (self._current_guna.model_dump() if self._current_guna else None),
            }

        if self.system_identity:
            state["components"]["system_identity"] = {
                "enabled": True,
                "system_state": self.system_identity.system_state,
            }

        if self.cognitive_orchestrator:
            state["components"]["cognitive_orchestrator"] = {
                "enabled": True,
                "guna_balance": (
                    self.cognitive_orchestrator.current_guna_balance.to_dict()
                    if hasattr(self.cognitive_orchestrator.current_guna_balance, "to_dict")
                    else str(self.cognitive_orchestrator.current_guna_balance)
                ),
            }

        if self.risk_orchestrator:
            state["components"]["risk_orchestrator"] = {"enabled": True}

        if self.karma_register:
            state["components"]["karma_register"] = {"enabled": True}

        return state

    def get_statistics(self) -> dict[str, Any]:
        """Krijg coordinator statistieken."""
        stats = {
            "cycles_completed": self.cycles_completed,
            "trading_mode": self.trading_mode.value,
            "agents": {
                "data_scout": self.data_scout.get_statistics(),
                "analyst": self.analyst.get_statistics(),
                "trader": self.trader.get_statistics(),
                "risk_manager": self.risk_manager.get_statistics(),
            },
            "unified_consciousness": self.get_unified_consciousness_state(),
        }
        if self.orchestrator:
            stats["agents"]["orchestrator"] = self.orchestrator.get_statistics()
            stats["harmony_score"] = self.orchestrator.harmony_score
        return stats
