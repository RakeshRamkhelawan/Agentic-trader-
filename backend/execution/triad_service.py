"""
Triad Service - Migrated with OODA Integration and Security.

Week 2 of Exchange Integration Refactor.

Changes:
- Uses OrderExecutor instead of OrderManager
- Integrates AgentGatekeeper for authorization
- Integrates AuditLogger for audit trail
- Publishes to EventBus
- Uses UnifiedOrderRequest
- Calls RiskManagerAgent for validation
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from backend.agents.portfolio_manager_agent import PortfolioManagerAgent

# Agents
from backend.agents.risk_manager_agent import RiskManagerAgent

# Feature flags
# OODA components
from backend.core.schemas.ooda_types import ExecutionPlan, RiskDecision, TradeProposal
from backend.core.security.audit_logger import AuditLogger

# Events
from backend.events.event_bus import EventBus
from backend.execution.bitvavo_adapter import BitvavoAdapter

# Execution components
from backend.execution.order_executor import OrderExecutor
from backend.execution.revolut_x_adapter import RevolutXAdapter

# Security & governance
from backend.governance.agent_gatekeeper import AgentGatekeeper, AgentRole, ToolPermission

# Unified schema

logger = logging.getLogger(__name__)


class TriadService:
    """
    Refactored Triad Service using OODA infrastructure.

    Provides unified trading interface with:
    - Multi-council decision making (Guna, Mind, Body)
    - Buddhi decision engine
    - Risk validation
    - Secure execution via OrderExecutor

    Usage:
        >>> service = TriadService(trading_mode="paper")
        >>> await service.initialize()
        >>> result = await service.execute_trade(decision, symbol="BTC/EUR")
    """

    def __init__(self, trading_mode: str = "paper"):
        """
        Initialize Triad Service.

        Args:
            trading_mode: "paper", "live", or "backtest"
        """
        self.trading_mode = trading_mode
        self.agent_name = "TriadService"
        self.agent_role = "executor"

        # OODA components
        self.order_executor: OrderExecutor | None = None
        self.risk_manager: RiskManagerAgent | None = None
        self.portfolio_manager: PortfolioManagerAgent | None = None

        # Security & audit
        self.gatekeeper = AgentGatekeeper()
        self.audit_logger = AuditLogger()
        self.event_bus: EventBus | None = None

        # Stats
        self.stats = {
            "trades_executed": 0,
            "trades_rejected": 0,
            "risk_rejections": 0,
            "auth_failures": 0,
        }

        logger.info(f"[TriadService] Initialized (mode={trading_mode})")

    async def initialize(
        self,
        event_bus: EventBus | None = None,
        exchange_adapter: Any | None = None,
        use_enhanced_risk: bool = False,
    ) -> bool:
        """
        Initialize service with dependencies.

        Args:
            event_bus: Event bus for publishing
            exchange_adapter: Exchange adapter (auto-created if None)
            use_enhanced_risk: Whether to use enhanced risk validator

        Returns:
            True if initialization successful
        """
        try:
            self.event_bus = event_bus

            # Initialize portfolio manager agent
            self.portfolio_manager = PortfolioManagerAgent(event_bus=event_bus)
            await self.portfolio_manager.initialize_adapters()

            # Initialize risk manager with portfolio access
            self.risk_manager = RiskManagerAgent(
                event_bus=event_bus,
                portfolio_manager=self.portfolio_manager,
                use_enhanced_validator=use_enhanced_risk,
            )

            # Initialize order executor
            if exchange_adapter is None:
                exchange_adapter = await self._create_default_adapter()

            if exchange_adapter:
                self.order_executor = OrderExecutor(
                    exchange_adapter=exchange_adapter, gatekeeper=self.gatekeeper
                )
                logger.info("[TriadService] OrderExecutor initialized")

            logger.info("[TriadService] Initialization complete")
            return True

        except Exception as e:
            logger.error(f"[TriadService] Initialization failed: {e}")
            return False

    async def _create_default_adapter(self) -> Any | None:
        """Create default exchange adapter based on config."""
        from backend.core.config.settings import settings

        # Try Bitvavo first
        if settings.BITVAVO_API_KEY:
            try:
                adapter = BitvavoAdapter()
                if await adapter.initialize():
                    logger.info("[TriadService] Using Bitvavo adapter")
                    return adapter
            except Exception as e:
                logger.warning(f"[TriadService] Bitvavo init failed: {e}")

        # Try Revolut
        if settings.REVOLUT_API_KEY:
            try:
                adapter = RevolutXAdapter()
                if await adapter.connect():
                    logger.info("[TriadService] Using Revolut adapter")
                    return adapter
            except Exception as e:
                logger.warning(f"[TriadService] Revolut init failed: {e}")

        logger.warning("[TriadService] No exchange adapter available")
        return None

    async def execute_trade(
        self,
        decision: Any,  # BuddhiDecision
        symbol: str = "BTC/EUR",
        quantity: Decimal | None = None,
        exchange_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute trade with full OODA integration and security.

        Flow:
        1. Check authorization (AgentGatekeeper)
        2. Create TradeProposal
        3. Risk assessment (RiskManagerAgent)
        4. Create ExecutionPlan
        5. Audit logging
        6. Execute via OrderExecutor
        7. Publish event

        Args:
            decision: BuddhiDecision from councils
            symbol: Trading pair (e.g., "BTC/EUR")
            quantity: Trade size (auto-calculated if None)
            exchange_id: Specific exchange (auto-selected if None)

        Returns:
            Execution result dictionary
        """

        # 1. Check authorization
        if not self.gatekeeper.authorize(
            agent_name=self.agent_name,
            agent_role=AgentRole.EXECUTOR,
            required_permission=ToolPermission.TRADE_EXECUTION,
        ):
            self.stats["auth_failures"] += 1
            from backend.core.security.audit_logger import AuditEventType

            self.audit_logger.log_event(
                event_type=AuditEventType.AUTHZ_DENIED,
                actor=self.agent_name,
                action="unauthorized_execution_attempt",
                resource="triad_service",
                output_status="DENIED",
                details={"symbol": symbol, "decision": str(decision)},
            )
            return {"status": "rejected", "reason": "Not authorized to place orders"}

        # Default quantity
        if quantity is None:
            quantity = Decimal(str(decision.confidence)) * Decimal("0.1")

        # 2. Create TradeProposal for risk assessment
        # Default entry price for calculation (will use market price)
        default_entry = 45000.0  # Approximate BTC price
        is_buy = decision.action == "bullish"

        proposal = TradeProposal(
            symbol=symbol,
            side="buy" if is_buy else "sell",
            size=float(quantity),
            entry_price=None,  # Market order
            stop_loss=default_entry * 0.9 if is_buy else default_entry * 1.1,  # 10% stop
            take_profit=default_entry * 1.1 if is_buy else default_entry * 0.9,  # 10% target
            rationale=decision.rationale,
            strategy_id="triad",
            confidence=decision.confidence,
        )

        # 3. Risk assessment
        if self.risk_manager:
            from backend.core.schemas.ooda_types import MarketRegime

            risk_assessment = await self.risk_manager.assess_risk(
                proposal=proposal, current_regime=MarketRegime.UNKNOWN, current_position_size=0.0
            )

            if risk_assessment.decision == RiskDecision.REJECT:
                self.stats["risk_rejections"] += 1
                # Log rejection via event
                from backend.core.security.audit_logger import AuditEventType

                self.audit_logger.log_event(
                    event_type=AuditEventType.TRADE_BLOCKED,
                    actor=self.agent_name,
                    action="risk_rejection",
                    resource="risk_manager",
                    output_status="REJECTED",
                    details={"reason": risk_assessment.rationale, "proposal": str(proposal)},
                )
                return {
                    "status": "rejected",
                    "reason": risk_assessment.rationale,
                    "risk_score": risk_assessment.risk_score,
                }

            if risk_assessment.decision == RiskDecision.REDUCE_SIZE:
                # Adjust size (create new proposal since TradeProposal is frozen)
                if risk_assessment.modified_size:
                    proposal = TradeProposal(
                        symbol=proposal.symbol,
                        side=proposal.side,
                        size=risk_assessment.modified_size,
                        entry_price=proposal.entry_price,
                        stop_loss=proposal.stop_loss,
                        take_profit=proposal.take_profit,
                        rationale=proposal.rationale + " (size reduced by risk manager)",
                        strategy_id=proposal.strategy_id,
                        confidence=proposal.confidence,
                        leverage=proposal.leverage,
                    )
                    quantity = Decimal(str(proposal.size))

        # 4. Create ExecutionPlan
        trace_id = f"triad-{datetime.utcnow().timestamp()}"
        plan = ExecutionPlan(
            symbol=proposal.symbol,
            side=proposal.side,
            quantity=proposal.size,
            order_type="MARKET" if proposal.entry_price is None else "LIMIT",
            price=proposal.entry_price,
            expected_price=proposal.entry_price
            or float(quantity * Decimal("45000")),  # Approximate
            trace_id=trace_id,
            caller_name=self.agent_name,
            caller_role=self.agent_role,
        )

        # 5. Log attempt
        self.audit_logger.log_trade_attempt(
            execution_plan=plan, outcome="ATTEMPT", details={"mode": self.trading_mode}
        )

        # 6. Execute via OrderExecutor
        if self.order_executor:
            try:
                outcome = await self.order_executor.execute_trade(plan)

                # 7. Publish event
                if self.event_bus:
                    await self.event_bus.publish(
                        "execution",
                        {
                            "trace_id": plan.trace_id,
                            "status": "filled" if outcome.success else "failed",
                            "symbol": plan.symbol,
                            "filled_qty": outcome.filled_qty,
                            "avg_price": outcome.avg_price,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

                if outcome.success:
                    self.stats["trades_executed"] += 1

                    # Record for risk tracking
                    if self.risk_manager and self.risk_manager.risk_validator:
                        order_value = Decimal(str(outcome.filled_qty)) * Decimal(
                            str(outcome.avg_price or 0)
                        )
                        self.risk_manager.risk_validator.record_trade(order_value)
                else:
                    self.stats["trades_rejected"] += 1

                return {
                    "status": "filled" if outcome.success else "failed",
                    "trace_id": plan.trace_id,
                    "order_id": outcome.order_id,
                    "filled_qty": outcome.filled_qty,
                    "avg_price": outcome.avg_price,
                    "fee": outcome.fee,
                    "error": outcome.error,
                }

            except Exception as e:
                logger.error(f"[TriadService] Execution error: {e}")
                return {"status": "error", "reason": str(e)}
        else:
            return {"status": "error", "reason": "OrderExecutor not initialized"}

    async def cancel_trade(self, order_id: str) -> bool:
        """
        Cancel a pending trade.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        if not self.order_executor:
            return False

        # Check authorization
        if not self.gatekeeper.authorize(
            agent_name=self.agent_name,
            agent_role=AgentRole.EXECUTOR,
            required_permission=ToolPermission.TRADE_EXECUTION,
        ):
            return False

        try:
            # Cancel via order executor
            success = await self.order_executor.cancel_order(order_id)

            if success and self.event_bus:
                await self.event_bus.publish(
                    "execution",
                    {
                        "event": "cancelled",
                        "order_id": order_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            return success

        except Exception as e:
            logger.error(f"[TriadService] Cancel error: {e}")
            return False

    async def get_portfolio(self) -> Any | None:
        """Get aggregated portfolio across all exchanges."""
        if self.portfolio_manager:
            return await self.portfolio_manager.get_portfolio_state()
        return None

    def get_statistics(self) -> dict[str, Any]:
        """Get service statistics."""
        stats = {
            **self.stats,
            "trading_mode": self.trading_mode,
        }

        if self.risk_manager:
            stats["risk_manager"] = self.risk_manager.get_stats()

        return stats

    async def close(self) -> None:
        """Close service and cleanup resources."""
        if self.order_executor:
            # Close exchange connections
            pass  # OrderExecutor handles this

        logger.info("[TriadService] Closed")


# Factory function
_triad_service: TriadService | None = None


def get_triad_service(trading_mode: str = "paper") -> TriadService:
    """Get or create TriadService singleton."""
    global _triad_service
    if _triad_service is None:
        _triad_service = TriadService(trading_mode=trading_mode)
    return _triad_service
