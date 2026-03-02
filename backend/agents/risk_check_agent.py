"""
Risk Check Agent - Risk-aware trading decisions.

This agent evaluates risk metrics before allowing trades,
ensuring portfolio protection and compliance with risk limits.
"""

import logging
from typing import Any

from backend.agents.agent_with_tools import AgentWithTools
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class RiskCheckAgent(AgentWithTools):
    """
    Agent that evaluates risk before executing trades.

    Checks:
    - Portfolio exposure limits
    - Position sizing constraints
    - VaR (Value at Risk)
    - Kelly criterion
    - Drawdown limits
    """

    def __init__(
        self,
        agent_name: str = "risk_guardian",
        tool_broker_url: str | None = None,
        max_position_size: float = 0.1,  # Max 10% of portfolio per position
        max_portfolio_var: float = 0.05,  # Max 5% VaR
        max_drawdown: float = 0.15,  # Max 15% drawdown
        kelly_fraction: float = 0.5,  # Half-Kelly for safety
        **kwargs,
    ):
        super().__init__(
            agent_name=agent_name,
            agent_role=AgentRole.STRATEGIST,
            tool_broker_url=tool_broker_url,
            **kwargs,
        )
        self.max_position_size = max_position_size
        self.max_portfolio_var = max_portfolio_var
        self.max_drawdown = max_drawdown
        self.kelly_fraction = kelly_fraction
        logger.info(
            f"{agent_name} initialized: "
            f"max_position={max_position_size}, max_var={max_portfolio_var}"
        )

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze risk and return approved/modified/rejected decision.

        Args:
            features: Must contain:
                     - 'symbol': Asset symbol
                     - 'price': Current price
                     - 'side': 'buy' or 'sell'
                     - 'proposed_quantity': Requested quantity
                     - 'portfolio_value': Total portfolio value
            context: Additional context including:
                     - 'signal_confidence': Confidence from other agents
                     - 'existing_position': Current position size

        Returns:
            Risk assessment with approved quantity and risk metrics
        """
        symbol = features.get("symbol", "BTC")
        price = features.get("price", 0.0)
        side = features.get("side", "buy").lower()
        proposed_qty = features.get("proposed_quantity", 0.0)
        portfolio_value = features.get("portfolio_value", 0.0)

        if portfolio_value <= 0:
            return {
                "action": "reject",
                "approved_quantity": 0.0,
                "confidence": 0.0,
                "reason": "Invalid portfolio value",
                "risk_metrics": {},
            }

        if price <= 0:
            return {
                "action": "reject",
                "approved_quantity": 0.0,
                "confidence": 0.0,
                "reason": "Invalid price",
                "risk_metrics": {},
            }

        try:
            # Gather risk metrics
            risk_metrics = await self._gather_risk_metrics(symbol, price, portfolio_value)

            # Check VaR limit
            portfolio_var = risk_metrics.get("portfolio_var", 0.0)
            if portfolio_var > self.max_portfolio_var:
                logger.warning(
                    f"VaR {portfolio_var:.2%} exceeds limit {self.max_portfolio_var:.2%}"
                )
                return {
                    "action": "reject",
                    "approved_quantity": 0.0,
                    "confidence": 0.0,
                    "reason": f"VaR {portfolio_var:.2%} exceeds limit {self.max_portfolio_var:.2%}",
                    "risk_metrics": risk_metrics,
                }

            # Check drawdown
            current_drawdown = risk_metrics.get("current_drawdown", 0.0)
            if current_drawdown > self.max_drawdown:
                logger.warning(
                    f"Drawdown {current_drawdown:.2%} exceeds limit {self.max_drawdown:.2%}"
                )
                return {
                    "action": "reject",
                    "approved_quantity": 0.0,
                    "confidence": 0.0,
                    "reason": f"Drawdown {current_drawdown:.2%} exceeds limit {self.max_drawdown:.2%}",
                    "risk_metrics": risk_metrics,
                }

            # Calculate Kelly criterion position size
            win_rate = risk_metrics.get("win_rate", 0.5)
            avg_win = risk_metrics.get("avg_win", 0.0)
            avg_loss = risk_metrics.get("avg_loss", 0.0)

            kelly_size = self._calculate_kelly_size(
                win_rate, avg_win, avg_loss, portfolio_value, price
            )

            # Apply Kelly fraction for safety
            safe_size = kelly_size * self.kelly_fraction

            # Check position size limit
            position_value = proposed_qty * price
            position_pct = position_value / portfolio_value if portfolio_value > 0 else 1.0

            if position_pct > self.max_position_size:
                # Reduce to max position size
                max_qty = (portfolio_value * self.max_position_size) / price
                approved_qty = min(proposed_qty, max_qty, safe_size)

                reason = (
                    f"Position size reduced from {proposed_qty} to {approved_qty:.4f} "
                    f"({position_pct:.1%} -> {(approved_qty * price / portfolio_value):.1%}) "
                    f"due to position limit {self.max_position_size:.1%}"
                )

                logger.info(f"{self.agent_name}: {symbol} position reduced to {approved_qty}")

                return {
                    "action": "modify",
                    "approved_quantity": approved_qty,
                    "confidence": 0.8,
                    "reason": reason,
                    "risk_metrics": risk_metrics,
                    "kelly_recommended": kelly_size,
                    "original_quantity": proposed_qty,
                }

            # Also cap by Kelly criterion
            if proposed_qty > safe_size:
                approved_qty = safe_size

                reason = (
                    f"Position size reduced from {proposed_qty} to {approved_qty:.4f} "
                    f"based on Kelly criterion (fraction: {self.kelly_fraction})"
                )

                logger.info(
                    f"{self.agent_name}: {symbol} position capped by Kelly to {approved_qty}"
                )

                return {
                    "action": "modify",
                    "approved_quantity": approved_qty,
                    "confidence": 0.85,
                    "reason": reason,
                    "risk_metrics": risk_metrics,
                    "kelly_recommended": kelly_size,
                    "original_quantity": proposed_qty,
                }

            # All checks passed
            logger.info(f"{self.agent_name}: {symbol} position approved at {proposed_qty}")

            return {
                "action": "approve",
                "approved_quantity": proposed_qty,
                "confidence": 0.95,
                "reason": (
                    f"Position approved: VaR {portfolio_var:.2%}, "
                    f"Drawdown {current_drawdown:.2%}, "
                    f"Size {position_pct:.1%} of portfolio"
                ),
                "risk_metrics": risk_metrics,
                "kelly_recommended": kelly_size,
            }

        except Exception as e:
            logger.exception(f"Error in risk analysis: {e}")
            return {
                "action": "reject",
                "approved_quantity": 0.0,
                "confidence": 0.0,
                "reason": f"Risk analysis error: {str(e)}",
                "risk_metrics": {},
            }

    async def _gather_risk_metrics(
        self, symbol: str, price: float, portfolio_value: float
    ) -> dict[str, Any]:
        """
        Gather risk metrics for the portfolio.

        In production, these would come from the risk management system.
        For now, we use simplified calculations or call MCP tools.
        """
        metrics = {
            "symbol": symbol,
            "price": price,
            "portfolio_value": portfolio_value,
            # Placeholder values - in production, fetch from risk system
            "portfolio_var": 0.03,  # 3% VaR
            "current_drawdown": 0.05,  # 5% drawdown
            "win_rate": 0.55,
            "avg_win": 0.08,  # 8% average win
            "avg_loss": 0.04,  # 4% average loss
            "sharpe_ratio": 1.2,
            "beta": 0.85,
        }

        # TODO: In production, call risk MCP tools:
        # var_result = await self.call_tool("risk__calculate_var", {...})
        # drawdown_result = await self.call_tool("risk__get_drawdown", {...})

        return metrics

    def _calculate_kelly_size(
        self, win_rate: float, avg_win: float, avg_loss: float, portfolio_value: float, price: float
    ) -> float:
        """
        Calculate Kelly criterion position size.

        Kelly formula: f = (p*b - q) / b
        where:
        - p = win rate
        - q = loss rate (1-p)
        - b = win/loss ratio

        Args:
            win_rate: Probability of winning (0-1)
            avg_win: Average win percentage
            avg_loss: Average loss percentage
            portfolio_value: Total portfolio value
            price: Current asset price

        Returns:
            Recommended quantity based on Kelly criterion
        """
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            # Invalid inputs, return conservative size
            return (portfolio_value * 0.01) / price  # 1% of portfolio

        # Calculate win/loss ratio
        b = avg_win / avg_loss

        # Kelly formula
        q = 1 - win_rate
        kelly_fraction = (win_rate * b - q) / b

        # Kelly fraction can be negative (don't trade)
        if kelly_fraction <= 0:
            return 0.0

        # Calculate quantity
        position_value = portfolio_value * kelly_fraction
        quantity = position_value / price

        return quantity

    async def check_emergency_stop(self) -> dict[str, Any]:
        """
        Check if emergency stop should be triggered.

        Returns:
            Emergency status with reason if triggered
        """
        # TODO: Check portfolio-level emergency conditions
        # - Circuit breakers
        # - Correlation spikes
        # - Liquidity crises

        return {"emergency_stop": False, "reason": None, "timestamp": None}
