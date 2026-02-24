"""
Elemental Agent Manager V18 - MCP Edition.

Refactored V17 Elemental Agents to use MCP tools instead of direct calls.
This provides better isolation, resilience, and LLM orchestration capabilities.
"""

import logging
from datetime import datetime
from typing import Any

from backend.mcp_broker.client import MCPClientWrapper

logger = logging.getLogger(__name__)


class ElementalAgentManagerV18:
    """
    V18 Elemental Agent Manager using MCP tools.

    This replaces the direct agent calls in V17 with MCP tool invocations,
    providing better resilience and enabling LLM orchestration.
    """

    def __init__(self, mcp_client: MCPClientWrapper | None = None):
        """
        Initialize Elemental Agent Manager V18.

        Args:
            mcp_client: Optional MCP client. If not provided, creates new connection.
        """
        self.mcp_client = mcp_client
        self._owns_client = mcp_client is None

        # Track trade history for each symbol
        self.trade_history: dict[str, list[dict[str, Any]]] = {}

        # Track open positions
        self.open_positions: dict[str, dict[str, Any]] = {}

        # Track peak prices for trailing stops
        self.peak_prices: dict[str, float] = {}

        logger.info("ElementalAgentManagerV18 initialized")

    async def initialize(self):
        """Initialize MCP connection if needed."""
        if self._owns_client:
            self.mcp_client = MCPClientWrapper()
            await self.mcp_client.initialize()
            logger.info("MCP client initialized")

    async def close(self):
        """Close MCP connection if owned."""
        if self._owns_client and self.mcp_client:
            await self.mcp_client.close()
            logger.info("MCP client closed")

    async def evaluate_entry(
        self,
        symbol: str,
        current_price: float,
        portfolio_value: float,
        vedastro_score: float,
        dominant_planet: str,
        price_history: list[float],
    ) -> dict[str, Any] | None:
        """
        Evaluate entry opportunity using MCP tools.

        Flow:
        1. Check if entry is allowed (Earth - 3-loss rule)
        2. Get Water regime check
        3. Calculate position size (Fire)
        4. Return entry dict if all checks pass

        Args:
            symbol: Asset symbol
            current_price: Current market price
            portfolio_value: Total portfolio value
            vedastro_score: VedAstro strength score (0-100)
            dominant_planet: Dominant planet for the day
            price_history: Recent price history

        Returns:
            Entry dict or None if entry not allowed
        """
        logger.info(f"Evaluating entry for {symbol} @ ${current_price}")

        # Check 1: Earth entry check (3-loss rule)
        trade_history = self.trade_history.get(symbol, [])

        earth_result = await self.mcp_client.call_tool(
            "elemental__earth_entry_check", {"symbol": symbol, "trade_history": trade_history}
        )

        if not earth_result.get("can_enter", True):
            logger.info(f"Entry blocked for {symbol}: {earth_result.get('blocking_reason')}")
            return None

        # Check 2: Water regime check
        if len(price_history) >= 20:
            water_result = await self.mcp_client.call_tool(
                "elemental__water_regime_check", {"symbol": symbol, "prices": price_history}
            )

            # For bonds, check regime shift
            if symbol in ["TLT", "IEF", "AGG", "BND"]:
                entry_risk_on = water_result.get("risk_on_score", 0.5)
                if water_result.get("regime") == "contraction" and entry_risk_on < 0.35:
                    logger.info(f"Entry blocked for {symbol}: unfavorable regime")
                    return None

        # Check 3: Calculate position size (Fire)
        fire_result = await self.mcp_client.call_tool(
            "elemental__fire_position_size",
            {
                "symbol": symbol,
                "portfolio_value": portfolio_value,
                "vedastro_score": vedastro_score,
                "dominant_planet": dominant_planet,
                "price_history": price_history,
            },
        )

        position_size = fire_result.get("position_size_eur", 0)

        if position_size <= 0:
            logger.info(f"Entry blocked for {symbol}: zero position size")
            return None

        # Calculate quantity
        quantity = position_size / current_price

        if quantity <= 0:
            return None

        # Record entry
        self.open_positions[symbol] = {
            "entry_date": datetime.utcnow().isoformat(),
            "entry_price": current_price,
            "quantity": quantity,
            "position_size": position_size,
        }
        self.peak_prices[symbol] = current_price

        logger.info(f"Entry approved for {symbol}: {quantity:.2f} shares @ ${current_price}")

        return {
            "symbol": symbol,
            "action": "BUY",
            "entry_price": current_price,
            "quantity": quantity,
            "position_size": position_size,
            "vedastro_score": vedastro_score,
            "dominant_planet": dominant_planet,
            "elemental_consensus": fire_result.get("sizing_factors", {}),
        }

    async def evaluate_exit(
        self, symbol: str, current_price: float, current_date: str | None = None
    ) -> tuple[bool, str]:
        """
        Evaluate if position should be exited using MCP tools.

        Args:
            symbol: Asset symbol
            current_price: Current market price
            current_date: Optional current date (ISO format)

        Returns:
            Tuple of (should_exit, reason)
        """
        if symbol not in self.open_positions:
            return False, ""

        position = self.open_positions[symbol]
        entry_date = position["entry_date"]
        entry_price = position["entry_price"]

        # Update peak price
        if symbol not in self.peak_prices:
            self.peak_prices[symbol] = entry_price

        if current_price > self.peak_prices[symbol]:
            self.peak_prices[symbol] = current_price

        peak_price = self.peak_prices[symbol]

        if current_date is None:
            current_date = datetime.utcnow().isoformat()

        # Call Earth exit check via MCP
        result = await self.mcp_client.call_tool(
            "elemental__earth_exit_check",
            {
                "symbol": symbol,
                "entry_date": entry_date,
                "current_date": current_date,
                "entry_price": entry_price,
                "current_price": current_price,
                "peak_price": peak_price,
            },
        )

        should_exit = result.get("should_exit", False)
        reasons = result.get("exit_reasons", [])

        if should_exit:
            reason_str = ", ".join(reasons)
            logger.info(f"Exit triggered for {symbol}: {reason_str}")

            # Record trade outcome
            pnl_pct = (current_price - entry_price) / entry_price
            self.record_trade_outcome(symbol, pnl_pct, pnl_pct > 0)

            # Clear position tracking
            del self.open_positions[symbol]
            del self.peak_prices[symbol]

            return True, reason_str

        return False, ""

    async def get_elemental_consensus(
        self, fire_vote: float, earth_vote: float, water_vote: float, air_vote: float
    ) -> dict[str, Any]:
        """
        Get elemental consensus using MCP tool.

        Args:
            fire_vote: Fire element score (0-1)
            earth_vote: Earth element score (0-1)
            water_vote: Water element score (0-1)
            air_vote: Air element score (0-1)

        Returns:
            Consensus result
        """
        result = await self.mcp_client.call_tool(
            "elemental__ether_consensus",
            {
                "fire_vote": fire_vote,
                "earth_vote": earth_vote,
                "water_vote": water_vote,
                "air_vote": air_vote,
            },
        )

        return result

    def record_trade_outcome(self, symbol: str, pnl_pct: float, win: bool):
        """Record trade outcome for tracking."""
        if symbol not in self.trade_history:
            self.trade_history[symbol] = []

        self.trade_history[symbol].append(
            {
                "symbol": symbol,
                "pnl": pnl_pct,
                "win": win,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Keep only last 50 trades per symbol
        self.trade_history[symbol] = self.trade_history[symbol][-50:]

    def get_open_position(self, symbol: str) -> dict[str, Any] | None:
        """Get open position for a symbol."""
        return self.open_positions.get(symbol)

    def has_open_position(self, symbol: str) -> bool:
        """Check if symbol has open position."""
        return symbol in self.open_positions

    def get_stats(self) -> dict[str, Any]:
        """Get manager statistics."""
        total_trades = sum(len(trades) for trades in self.trade_history.values())
        winning_trades = sum(
            sum(1 for t in trades if t.get("win", False)) for trades in self.trade_history.values()
        )

        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        return {
            "open_positions": len(self.open_positions),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": win_rate,
            "symbols_tracked": len(self.trade_history),
        }
