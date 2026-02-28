"""
RiskManager Agent - Enhanced with OrderRiskValidator.

Week 2 of Exchange Integration Refactor.

Integrates 10+ pre-trade validation checks from OrderRiskValidator
into OODA Risk Assessment flow.
"""

import logging
from decimal import Decimal
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (
    MarketRegime,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)
from backend.execution.fast_config import FastConfig
from backend.execution.risk_validator import OrderRiskValidator, RiskLimits
from backend.governance.agent_gatekeeper import AgentRole
from backend.schemas.unified_execution import OrderSide, OrderType, TimeInForce, UnifiedOrderRequest

logger = logging.getLogger(__name__)


class RiskManagerAgent(BaseAgent):
    """
    Enhanced Risk Manager with OrderRiskValidator integration.

    Combines existing risk assessment with comprehensive
    pre-trade validation (10+ checks).

    Rol in OODA: **DECIDE** (gatekeeping)
    - Beoordeelt proposed trades op risk constraints
    - Checked position limits
    - Evalueert market regime suitability
    - Output: RiskAssessment (APPROVE/REJECT/REDUCE_SIZE)
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        max_position_size: float = 1.0,
        max_leverage: float = 3.0,
        min_confidence: float = 0.6,
        portfolio_manager: Any | None = None,
        use_enhanced_validator: bool = False,  # Feature flag
    ):
        """
        Initialiseer RiskManager.

        Args:
            llm_provider: LLM (voor risk narratives)
            event_bus: Event bus
            max_position_size: Max position size als fractie van capital
            max_leverage: Max leverage multiplier
            min_confidence: Min confidence voor approval
            portfolio_manager: PortfolioManagerAgent for balance info
            use_enhanced_validator: Whether to use OrderRiskValidator
        """
        super().__init__(
            agent_name="RiskManager",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST,
        )

        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
        self.min_confidence = min_confidence
        self.portfolio_manager = portfolio_manager
        self.use_enhanced_validator = use_enhanced_validator

        # Initialize enhanced risk validator
        if use_enhanced_validator:
            self.risk_validator = OrderRiskValidator(
                RiskLimits(
                    max_position_pct=Decimal(str(max_position_size)),
                    max_order_pct=Decimal("0.10"),         # Max 10% per order
                    min_order_size=Decimal("10"),          # Min $10
                    max_daily_trades=50,
                    max_daily_volume_pct=Decimal("2.0"),   # Max 2x portfolio daily
                    max_daily_loss_pct=Decimal("0.05"),    # Max 5% daily loss
                    max_slippage_pct=Decimal("0.01"),      # Max 1% slippage
                    max_spread_pct=Decimal("0.02"),        # Max 2% spread
                )
            )
            logger.info("[RiskManagerAgent] Enhanced validator enabled")
        else:
            self.risk_validator = None

        self.assessments_made = 0
        self.trades_approved = 0
        self.trades_rejected = 0

    async def assess_risk(
        self,
        proposal: TradeProposal,
        current_regime: MarketRegime,
        current_position_size: float = 0.0,
    ) -> RiskAssessment:
        """
        Beoordeel trade proposal en genereer RiskAssessment.

        Enhanced with OrderRiskValidator when use_enhanced_validator=True.

        Args:
            proposal: Trade voorstel van TraderAgent
            current_regime: Current market regime
            current_position_size: Huidige position size (als fractie van capital)

        Returns:
            RiskAssessment met decision + rationale
        """
        self.heartbeat()

        try:
            # If enhanced validator is enabled, use it
            if self.use_enhanced_validator and self.risk_validator:
                return await self._assess_with_validator(
                    proposal, current_regime, current_position_size
                )
            else:
                # Use legacy assessment
                return await self._legacy_assess_risk(
                    proposal, current_regime, current_position_size
                )

        except Exception as e:
            logger.error(f"[RiskManagerAgent] Risk assessment error: {e}")
            # Fail safe: reject on error
            return RiskAssessment(
                trade_id=proposal.trade_id,
                decision=RiskDecision.REJECT,
                rationale=f"Risk assessment error: {str(e)}",
                risk_score=1.0,
                win_probability=0.0,
            )

    async def _assess_with_validator(
        self,
        proposal: TradeProposal,
        current_regime: MarketRegime,
        current_position_size: float
    ) -> RiskAssessment:
        """
        Assess risk using OrderRiskValidator.
        """
        # Convert TradeProposal to UnifiedOrderRequest
        order_request = self._convert_proposal(proposal)

        # Get portfolio info
        portfolio_value = Decimal("10000")  # Default
        current_positions = {proposal.symbol.split("/")[0]: Decimal(str(current_position_size))}

        if self.portfolio_manager:
            try:
                portfolio = await self.portfolio_manager.get_portfolio_state()
                portfolio_value = Decimal(str(portfolio.total_equity))
                # Could also get actual positions here
            except Exception as e:
                logger.warning(f"[RiskManagerAgent] Could not get portfolio: {e}")

        # Run validation
        validation = await self.risk_validator.validate_order(
            request=order_request,
            portfolio_value=portfolio_value,
            current_positions=current_positions,
            exchange=None,  # Could pass exchange adapter
            balance=None    # Could pass balance
        )

        # Combine with base risk assessment
        base_risk_score = self._calculate_base_risk(proposal, current_regime)

        # Adjust based on validation
        if not validation.is_valid:
            risk_score = 1.0  # Maximum risk
            decision = RiskDecision.REJECT
            rationale = f"Risk validation failed: {validation.overall_message}"
        elif validation.has_warnings:
            risk_score = min(base_risk_score * 1.2, 1.0)
            decision = RiskDecision.REDUCE_SIZE
            rationale = f"Risk warnings: {validation.overall_message}"
        else:
            risk_score = base_risk_score
            # Check base constraints
            if base_risk_score > 0.7:
                decision = RiskDecision.REJECT
                rationale = "Base risk score too high"
            elif base_risk_score > 0.5:
                decision = RiskDecision.REDUCE_SIZE
                rationale = "Elevated risk, reducing size"
            else:
                decision = RiskDecision.APPROVE
                rationale = "Risk validation passed"

        # Calculate win probability
        win_probability = self._calculate_win_probability(proposal, risk_score)

        # Determine modified size if needed
        modified_size = None
        if decision == RiskDecision.REDUCE_SIZE:
            modified_size = proposal.size * 0.5

        self.assessments_made += 1
        if decision == RiskDecision.APPROVE:
            self.trades_approved += 1
            # Record for daily stats
            order_value = order_request.quantity * (order_request.price or order_request.expected_price)
            self.risk_validator.record_trade(order_value)
        else:
            self.trades_rejected += 1

        # Publish thought
        await self.publish_thought(
            reasoning=rationale,
            confidence=1.0 - risk_score,
            data={
                "trade_id": proposal.trade_id,
                "risk_score": risk_score,
                "checks_performed": len(validation.checks),
                "validation_status": validation.status.value
            }
        )

        return RiskAssessment(
            trade_id=proposal.trade_id,
            decision=decision,
            rationale=rationale,
            risk_score=min(risk_score, 1.0),
            win_probability=win_probability,
            modified_size=modified_size,
        )

    def _convert_proposal(self, proposal: TradeProposal) -> UnifiedOrderRequest:
        """Convert TradeProposal to UnifiedOrderRequest."""
        # Default expected price for market orders (use stop_loss/take_profit average as approximation)
        if proposal.entry_price:
            expected = Decimal(str(proposal.entry_price))
        else:
            # For market orders, estimate from stop_loss and take_profit
            expected = Decimal(str((proposal.stop_loss + proposal.take_profit) / 2))

        return UnifiedOrderRequest(
            trace_id=f"risk-{proposal.trade_id}",
            symbol=proposal.symbol,
            side=OrderSide(proposal.side),
            order_type=OrderType.LIMIT if proposal.entry_price else OrderType.MARKET,
            quantity=Decimal(str(proposal.size)),
            price=Decimal(str(proposal.entry_price)) if proposal.entry_price else None,
            expected_price=expected,
            strategy_id=proposal.strategy_id,
            time_in_force=TimeInForce.GTC,
            post_only=False
        )

    def _calculate_base_risk(
        self,
        proposal: TradeProposal,
        current_regime: MarketRegime
    ) -> float:
        """Calculate base risk score from proposal."""
        base_risk = 0.3  # Start at 30%

        # Adjust based on confidence
        base_risk *= (1.0 - proposal.confidence)

        # Adjust based on leverage
        if proposal.leverage and proposal.leverage > 1:
            base_risk *= proposal.leverage / self.max_leverage

        # Adjust based on regime
        if current_regime == MarketRegime.VOLATILE:
            base_risk *= 1.3
        elif current_regime == MarketRegime.SIDEWAYS:
            base_risk *= 1.1

        return min(base_risk, 1.0)

    def _calculate_win_probability(
        self,
        proposal: TradeProposal,
        risk_score: float
    ) -> float:
        """Estimate win probability."""
        win_prob = proposal.confidence * (1.0 - risk_score)
        return max(0.0, min(1.0, win_prob))

    async def _legacy_assess_risk(
        self,
        proposal: TradeProposal,
        current_regime: MarketRegime,
        current_position_size: float
    ) -> RiskAssessment:
        """Legacy risk assessment (without OrderRiskValidator)."""
        violations = []

        # Dynamic min confidence from config
        try:
            config = FastConfig.read()
            dynamic_min_confidence = config.get("confidence", self.min_confidence)
        except Exception:
            dynamic_min_confidence = self.min_confidence

        if proposal.confidence < dynamic_min_confidence:
            violations.append(
                f"Confidence {proposal.confidence:.2f} < threshold {dynamic_min_confidence:.2f}"
            )

        # Position size check
        new_position = current_position_size + proposal.size
        if new_position > self.max_position_size:
            violations.append(
                f"Position {new_position:.2f} > max {self.max_position_size:.2f}"
            )

        # Leverage check
        if proposal.leverage and proposal.leverage > self.max_leverage:
            violations.append(f"Leverage {proposal.leverage}x > max {self.max_leverage}x")

        # Regime check
        if current_regime == MarketRegime.VOLATILE and proposal.leverage and proposal.leverage > 1:
            violations.append("Leverage not allowed in volatile regime")

        # Calculate risk metrics
        risk_score = len(violations) * 0.2
        if proposal.confidence < 0.7:
            risk_score += 0.2

        win_probability = proposal.confidence * (1 - risk_score)

        # Make decision
        if violations:
            decision = RiskDecision.REJECT
            modified_size = None
        elif risk_score > 0.5:
            decision = RiskDecision.REDUCE_SIZE
            modified_size = proposal.size * 0.5
        else:
            decision = RiskDecision.APPROVE
            modified_size = None

        self.assessments_made += 1
        if decision == RiskDecision.APPROVE:
            self.trades_approved += 1
        else:
            self.trades_rejected += 1

        rationale = (
            f"Violations: {', '.join(violations)}" if violations else "Risk checks passed"
        )

        await self.publish_thought(
            reasoning=rationale,
            confidence=proposal.confidence,
            data={"violations": violations, "risk_score": risk_score}
        )

        return RiskAssessment(
            trade_id=proposal.trade_id,
            decision=decision,
            rationale=rationale,
            risk_score=min(risk_score, 1.0),
            win_probability=win_probability,
            modified_size=modified_size,
        )

    def enable_enhanced_validator(self) -> None:
        """Enable OrderRiskValidator."""
        if self.risk_validator is None:
            self.risk_validator = OrderRiskValidator(
                RiskLimits(
                    max_position_pct=Decimal(str(self.max_position_size)),
                    max_order_pct=Decimal("0.10"),
                    min_order_size=Decimal("10"),
                    max_daily_trades=50,
                    max_daily_volume_pct=Decimal("2.0"),
                    max_daily_loss_pct=Decimal("0.05"),
                    max_slippage_pct=Decimal("0.01"),
                    max_spread_pct=Decimal("0.02"),
                )
            )
        self.use_enhanced_validator = True
        logger.info("[RiskManagerAgent] Enhanced validator enabled")

    def get_stats(self) -> dict:
        """Get agent statistics."""
        stats = {
            "assessments_made": self.assessments_made,
            "trades_approved": self.trades_approved,
            "trades_rejected": self.trades_rejected,
            "approval_rate": (
                self.trades_approved / self.assessments_made
                if self.assessments_made > 0 else 0
            ),
            "enhanced_validator": self.use_enhanced_validator,
        }

        if self.risk_validator:
            stats["daily_stats"] = self.risk_validator.get_daily_stats()

        return stats

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze trading opportunity and return risk assessment.

        Required abstract method from BaseAgent.

        Args:
            features: Trading signal features
            context: Additional context (market regime, portfolio state, etc.)

        Returns:
            Analysis result with risk assessment
        """
        from backend.core.schemas.ooda_types import MarketRegime, TradeProposal

        # Extract trade proposal from features
        proposal = features.get("proposal")
        if not proposal:
            # Create proposal from features with sensible defaults
            entry_price = features.get("entry_price", 45000)
            is_buy = features.get("side", "buy") == "buy"

            # Default stop loss: 10% below/above entry
            stop_loss_default = entry_price * 0.9 if is_buy else entry_price * 1.1
            # Default take profit: 10% above/below entry
            take_profit_default = entry_price * 1.1 if is_buy else entry_price * 0.9

            proposal = TradeProposal(
                symbol=features.get("symbol", "BTC/EUR"),
                side=features.get("side", "buy"),
                size=features.get("size", 0.01),  # Small default size
                entry_price=entry_price,
                stop_loss=features.get("stop_loss", stop_loss_default),
                take_profit=features.get("take_profit", take_profit_default),
                rationale=features.get("rationale", "Analysis from features"),
                strategy_id=features.get("strategy_id", "default"),
                confidence=features.get("confidence", 0.5)
            )

        regime = context.get("market_regime", MarketRegime.SIDEWAYS)
        position_size = context.get("current_position_size", 0.0)

        # Perform risk assessment
        assessment = await self.assess_risk(proposal, regime, position_size)

        return {
            "risk_score": assessment.risk_score,
            "decision": assessment.decision.value,
            "rationale": assessment.rationale,
            "win_probability": assessment.win_probability,
            "modified_size": assessment.modified_size,
            "trade_id": assessment.trade_id
        }
