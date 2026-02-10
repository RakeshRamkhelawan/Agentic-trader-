"""
OODA Loop Coordinator - Central Orchestration.

Coordineert de volledige Observe -> Orient -> Decide -> Act cyclus.
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional
from enum import Enum

from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.agents.trader_agent import TraderAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.governance.circuit_breaker import CircuitBreaker, CircuitBreakerTrippedError
from backend.core.schemas.ooda_types import (
    Observation,
    Orientation,
    TradeProposal,
    RiskAssessment,
    RiskDecision,
    ExecutionPlan
)
from backend.governance.agent_gatekeeper import AgentRole
from backend.execution.fast_config import FastConfig
from backend.execution.order_executor import OrderExecutor

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
        cognitive_bridge: CognitiveBridge,
        orchestrator: Optional[OrchestratorAgent] = None,
        order_executor: Optional[OrderExecutor] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        trading_mode: TradingMode = TradingMode.NOTIFY_ONLY,
        rag_retriever: Optional[Any] = None
    ):
        """
        Initialiseer OODA Coordinator.
        
        Args:
            data_scout: DataScoutAgent instance
            analyst: AnalystAgent instance
            trader: TraderAgent instance
            risk_manager: RiskManagerAgent instance
            cognitive_bridge: CognitiveBridge instance
            orchestrator: OrchestratorAgent (Cognitive Core) voor harmony checks
            order_executor: Order execution engine
            circuit_breaker: Optional CircuitBreaker voor safety
            trading_mode: Execution mode (notify_only / auto)
            rag_retriever: Optional RAG retriever voor historical context
        """
        self.data_scout = data_scout
        self.analyst = analyst
        self.trader = trader
        self.risk_manager = risk_manager
        self.cognitive_bridge = cognitive_bridge
        self.orchestrator = orchestrator
        self.order_executor = order_executor
        self.circuit_breaker = circuit_breaker
        self.trading_mode = trading_mode
        self.rag_retriever = rag_retriever
        
        self.cycles_completed = 0
        
        logger.info(
            f"OODA Coordinator initialized, mode={trading_mode.value}, "
            f"circuit_breaker={'enabled' if circuit_breaker else 'disabled'}, "
            f"orchestrator={'enabled' if orchestrator else 'disabled'}"
        )
    
    async def run_cycle(
        self,
        symbol: str,
        current_price: float,
        strategy_id: str = "momentum_v1"
    ) -> Dict[str, Any]:
        """
        Voer één complete OODA cyclus uit.
        
        Args:
            symbol: Trading pair
            current_price: Current market price (voor entry calculation)
            strategy_id: Strategy identifier
        
        Returns:
            Dict met cyclus resultaat
        """
        # Check FastConfig overrides
        try:
            config = FastConfig.read()
            action_override = config.get('action', 0)
            if action_override != 0:
                logger.warning(f"Manual override active: action={action_override}")
                # 0=Hold, 1=Long, 2=Short
                # In a real system, this would force a trade. 
                # For now we just log it as a proof of concept bridge.
        except Exception:
            pass

        return await self._execute_ooda_loop(symbol, current_price, strategy_id)

    async def _execute_ooda_loop(
        self,
        symbol: str, 
        current_price: float, 
        strategy_id: str
    ) -> Dict[str, Any]:
        """
        Internal execution of the loop.
        
        Returns:
            Dict met cycle results en decision
        """
        trace_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting OODA cycle for {symbol} (trace_id={trace_id})"
        )
        
        try:
            # ========== SAFETY CHECK ==========
            if self.circuit_breaker:
                if await self.circuit_breaker.is_tripped():
                    reason = await self.circuit_breaker.get_trip_reason()
                    logger.error(
                        f"Circuit breaker TRIPPED ({reason}) - halting cycle"
                    )
                    raise CircuitBreakerTrippedError(
                        f"Trading halted: circuit breaker tripped ({reason})"
                    )
            
            # ========== OBSERVE ==========
            observation = await self._observe(symbol, trace_id)
            
            # ========== ORIENT ==========
            orientation = await self._orient(observation)
            
            # ========== DECIDE ==========
            proposal, risk_assessment = await self._decide(
                orientation,
                current_price,
                strategy_id
            )
            
            # ========== HARMONIZE (Orchestrator) ==========
            harmony_result = None
            if self.orchestrator:
                proposals = [proposal] if proposal else []
                assessments = [risk_assessment] if risk_assessment else []
                harmony_result = await self.orchestrator.harmonize(
                    observation=observation,
                    orientation=orientation,
                    proposals=proposals,
                    risk_assessments=assessments
                )
                logger.info(
                    f"[HARMONIZE] status={harmony_result['status']}, "
                    f"harmony={harmony_result['harmony_score']}"
                )
            
            # ========== ACT (conditional) ==========
            execution_result = None
            if self.trading_mode == TradingMode.AUTO:
                if risk_assessment and risk_assessment.decision == RiskDecision.APPROVE:
                    if self.order_executor:
                        execution_result = await self._act(proposal, trace_id, current_price)
                    else:
                        logger.warning("Auto mode active but no OrderExecutor configured!")
                        execution_result = {"status": "skipped", "reason": "No executor"}
                else:
                    logger.info(f"Trade rejected, skipping execution: {risk_assessment.rationale if risk_assessment else 'No proposal'}")
            else:
                logger.info(f"Notify-Only mode: Skipping execution for {symbol}")
            
            self.cycles_completed += 1
            
            # Compile results
            result = {
                "trace_id": trace_id,
                "symbol": symbol,
                "observation": observation,
                "orientation": orientation,
                "proposal": proposal,
                "risk_assessment": risk_assessment,
                "harmony": harmony_result,
                "execution": execution_result,
                "mode": self.trading_mode.value,
                "decision": self._get_decision_summary(proposal, risk_assessment)
            }
            
            logger.info(
                f"Cycle complete: {result['decision']}"
            )
            
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
            include_funding=True
        )
        
        return observation
    
    async def _orient(self, observation: Observation) -> Orientation:
        """ORIENT fase."""
        logger.debug(f"[ORIENT] {observation.symbol}")
        
        # 1. Process door cognitive core
        core_sentiment = await self.cognitive_bridge.process_observation(observation)
        
        # 2. Fetch RAG context (optioneel)
        rag_context = []
        if self.rag_retriever:
            try:
                rag_context = await self.rag_retriever.search_similar(
                    query=f"{observation.symbol} market analysis",
                    category="strategy",
                    limit=3
                )
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        # 3. Analyst orientation
        orientation = await self.analyst.orient(
            observation=observation,
            core_sentiment=core_sentiment,
            rag_context=rag_context
        )
        
        return orientation
    
    async def _decide(
        self,
        orientation: Orientation,
        current_price: float,
        strategy_id: str
    ) -> tuple[Optional[TradeProposal], Optional[RiskAssessment]]:
        """DECIDE fase."""
        logger.debug(f"[DECIDE] {orientation.symbol}")
        
        # 1. Trader genereert proposal
        proposal = await self.trader.propose_trade(
            orientation=orientation,
            current_price=current_price,
            strategy_id=strategy_id
        )
        
        if proposal is None:
            logger.info("No trade signal from Trader")
            return None, None
        
        # 2. RiskManager beoordeelt proposal
        risk_assessment = await self.risk_manager.assess_risk(
            proposal=proposal,
            current_regime=orientation.regime,
            current_position_size=0.0  # TODO: Track actual position
        )
        
        return proposal, risk_assessment
    
    async def _act(
        self,
        proposal: TradeProposal,
        trace_id: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        ACT fase - Executes the trade via OrderExecutor.
        """
        logger.info(f"[ACT] Executing trade for {proposal.symbol} (trace_id={trace_id})")
        
        if not self.order_executor:
            return {"status": "failed", "error": "No OrderExecutor configured"}
            
        # Create execution plan from proposal
        # In a real system, we might need a separate 'Converter' or 'ExecutionStrategist'
        # For now, we map 1:1
        plan = ExecutionPlan(
            trace_id=trace_id,
            symbol=proposal.symbol,
            side=proposal.side,
            quantity=proposal.size,
            order_type="market",  # Defaulting to market for OODA v1
            price=None,     # Proposal.entry_price could be used for limit
            expected_price=proposal.entry_price or current_price,
            params={"max_slippage": 50},
            caller_name=self.trader.agent_name,
            caller_role=self.trader.agent_role
        )
        
        # Execute
        outcome = await self.order_executor.execute_trade(plan)
        
        return {
            "status": "executed" if outcome.success else "failed",
            "outcome": outcome,
            "message": outcome.error if not outcome.success else f"Filled {outcome.filled_qty} @ {outcome.avg_price}"
        }
    
    def _get_decision_summary(
        self,
        proposal: Optional[TradeProposal],
        risk_assessment: Optional[RiskAssessment]
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
        reason: Optional[str] = None,
        permission_service: Optional[Any] = None
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
        from backend.governance.permission_service import PermissionService
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
                reason=reason
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """Krijg coordinator statistieken."""
        stats = {
            "cycles_completed": self.cycles_completed,
            "trading_mode": self.trading_mode.value,
            "agents": {
                "data_scout": self.data_scout.get_statistics(),
                "analyst": self.analyst.get_statistics(),
                "trader": self.trader.get_statistics(),
                "risk_manager": self.risk_manager.get_statistics()
            }
        }
        if self.orchestrator:
            stats["agents"]["orchestrator"] = self.orchestrator.get_statistics()
            stats["harmony_score"] = self.orchestrator.harmony_score
        return stats
