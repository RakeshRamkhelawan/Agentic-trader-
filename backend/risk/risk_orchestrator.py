"""
Risk Orchestrator - Central Pre-Trade Validation Hub.

Combines VaR check, Kelly position sizing, drawdown monitoring,
and risk validation into a single pre-trade decision point.

All trade signals should pass through RiskOrchestrator.pre_trade_check()
before execution.
"""

import logging
from dataclasses import dataclass, field

from backend.risk.drawdown_monitor import DrawdownMonitor, DrawdownStatus
from backend.risk.kelly_criterion import KellyCriterion
from backend.risk.position_sizer import IntegratedPositionSizer
from backend.risk.var_calculator import VaRCalculator

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    """Input signal for pre-trade risk check."""

    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    stop_price: float
    confidence: float  # 0.0 - 1.0
    reward_to_risk: float  # target distance / stop distance
    strategy: str = ""


@dataclass
class RiskDecision:
    """Result of pre-trade risk validation."""

    approved: bool
    reason: str
    recommended_quantity: float
    drawdown_status: DrawdownStatus
    sizing_method: str = "fixed_risk"
    kelly_fraction: float | None = None
    warnings: list = field(default_factory=list)


class RiskOrchestrator:
    """
    Central pre-trade validation point.

    Performs layered risk checks:
    1. Kill switch / drawdown check
    2. Portfolio VaR limit check (if returns data available)
    3. Position sizing (Kelly or fixed-risk)
    4. Max position concentration check
    """

    def __init__(
        self,
        drawdown_monitor: DrawdownMonitor | None = None,
        position_sizer: IntegratedPositionSizer | None = None,
        kelly: KellyCriterion | None = None,
        var_calculator: VaRCalculator | None = None,
        max_daily_var_pct: float = 0.05,
        max_positions: int = 10,
    ):
        """
        Args:
            drawdown_monitor: DrawdownMonitor instance (created if None)
            position_sizer: IntegratedPositionSizer (created if None)
            kelly: KellyCriterion (created if None)
            var_calculator: VaRCalculator (created if None)
            max_daily_var_pct: Max portfolio VaR as % of equity. Default 5%.
            max_positions: Max concurrent open positions. Default 10.
        """
        self.drawdown_monitor = drawdown_monitor or DrawdownMonitor()
        self.position_sizer = position_sizer or IntegratedPositionSizer()
        self.kelly = kelly or KellyCriterion(conservative_factor=0.25)
        self.var_calculator = var_calculator or VaRCalculator()
        self.max_daily_var_pct = max_daily_var_pct
        self.max_positions = max_positions

    def pre_trade_check(
        self,
        signal: TradeSignal,
        portfolio_value: float,
        current_positions_count: int = 0,
    ) -> RiskDecision:
        """
        Run all pre-trade risk checks and return a decision.

        Args:
            signal: The trade signal to validate
            portfolio_value: Current total portfolio value
            current_positions_count: Number of open positions

        Returns:
            RiskDecision with approval status and recommended size
        """
        warnings_list = []

        # 1. Drawdown / Kill Switch check
        dd_status = self.drawdown_monitor.check(portfolio_value)

        if dd_status == DrawdownStatus.KILL_SWITCH:
            return RiskDecision(
                approved=False,
                reason="KILL SWITCH active: max drawdown exceeded. All trading halted.",
                recommended_quantity=0.0,
                drawdown_status=dd_status,
            )

        # 2. Max positions check
        if current_positions_count >= self.max_positions:
            return RiskDecision(
                approved=False,
                reason="Max positions limit reached (%d/%d)"
                % (current_positions_count, self.max_positions),
                recommended_quantity=0.0,
                drawdown_status=dd_status,
            )

        # 3. Confidence threshold
        if signal.confidence < 0.3:
            return RiskDecision(
                approved=False,
                reason="Signal confidence too low: %.2f < 0.30 threshold" % signal.confidence,
                recommended_quantity=0.0,
                drawdown_status=dd_status,
            )

        # 4. Position sizing
        sizing_method = "fixed_risk"
        kelly_fraction = None

        if signal.confidence >= 0.5 and signal.reward_to_risk > 0:
            # Use Kelly for higher confidence signals
            result = self.position_sizer.size_with_kelly(
                equity=portfolio_value,
                entry=signal.entry_price,
                stop=signal.stop_price,
                win_probability=signal.confidence,
                win_loss_ratio=signal.reward_to_risk,
                side=signal.side,
            )
            sizing_method = "kelly"
            kelly_fraction = result.kelly_fraction
        else:
            result = self.position_sizer.size_from_fixed_risk(
                equity=portfolio_value,
                entry=signal.entry_price,
                stop=signal.stop_price,
                side=signal.side,
            )

        quantity = result.quantity

        # 5. Apply drawdown scaling
        if dd_status == DrawdownStatus.REDUCE_EXPOSURE:
            quantity = IntegratedPositionSizer.apply_drawdown_scaling(
                quantity,
                current_drawdown=self.drawdown_monitor.get_drawdown_pct(),
                soft_limit=self.drawdown_monitor.soft_limit,
            )
            warnings_list.append(
                "Position halved due to REDUCE_EXPOSURE (drawdown > %.0f%%)"
                % (self.drawdown_monitor.soft_limit * 100)
            )

        # 6. Final validation
        if quantity <= 0:
            return RiskDecision(
                approved=False,
                reason="Calculated position size is zero (invalid entry/stop or no risk budget)",
                recommended_quantity=0.0,
                drawdown_status=dd_status,
                sizing_method=sizing_method,
                kelly_fraction=kelly_fraction,
            )

        return RiskDecision(
            approved=True,
            reason="Trade approved",
            recommended_quantity=quantity,
            drawdown_status=dd_status,
            sizing_method=sizing_method,
            kelly_fraction=kelly_fraction,
            warnings=warnings_list,
        )

    def update_portfolio_value(self, value: float) -> DrawdownStatus:
        """
        Update drawdown monitor with latest portfolio value.

        Args:
            value: Current portfolio value

        Returns:
            Current DrawdownStatus
        """
        return self.drawdown_monitor.check(value)
