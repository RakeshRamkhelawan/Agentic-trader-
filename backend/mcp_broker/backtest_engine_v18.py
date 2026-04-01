"""
BacktestEngine V18 - MCP Edition.

Uses MCP tools for all trading decisions instead of direct agent calls.
This provides resilience, LLM orchestration, and better error isolation.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from backend.mcp_broker.client import MCPClientWrapper
from backend.mcp_broker.elemental_manager_v18 import ElementalAgentManagerV18

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtest."""

    start_date: datetime
    end_date: datetime
    symbols: list[str]
    initial_cash: float = 100000.0
    account_id: str = "backtest_v18"

    # V17 constraints (preserved)
    max_position_pct: float = 0.02  # 2% of portfolio
    max_position_eur: float = 2000.0  # €2k cap

    # VedAstro settings
    min_vedastro_confidence: float = 50.0
    min_vedastro_score: float = 45.0


@dataclass
class BacktestState:
    """Current state of backtest."""

    cash: float
    total_value: float
    open_positions: dict[str, dict[str, Any]] = field(default_factory=dict)
    trades: list[dict[str, Any]] = field(default_factory=list)
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    day_count: int = 0


class BacktestEngineV18:
    """
    V18 Backtest Engine using MCP tools.

    Key differences from V17:
    - Uses MCP tool calls instead of direct agent methods
    - Better error isolation via circuit breakers
    - Supports LLM orchestration
    - All V17 constraints preserved
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize BacktestEngine V18.

        Args:
            config: Backtest configuration
        """
        self.config = config
        self.state = BacktestState(cash=config.initial_cash, total_value=config.initial_cash)

        self.mcp_client: MCPClientWrapper | None = None
        self.elemental_manager: ElementalAgentManagerV18 | None = None

        logger.info("BacktestEngineV18 initialized")
        logger.info(f"  Period: {config.start_date.date()} to {config.end_date.date()}")
        logger.info(f"  Symbols: {', '.join(config.symbols)}")
        logger.info(f"  Initial cash: €{config.initial_cash:,.2f}")

    async def initialize(self):
        """Initialize MCP connection and managers."""
        logger.info("Initializing BacktestEngineV18...")

        # Initialize MCP client
        self.mcp_client = MCPClientWrapper()
        await self.mcp_client.initialize()

        # Initialize Elemental Manager with MCP client
        self.elemental_manager = ElementalAgentManagerV18(self.mcp_client)

        logger.info("BacktestEngineV18 ready")

    async def close(self):
        """Cleanup resources."""
        if self.mcp_client:
            await self.mcp_client.close()
            logger.info("BacktestEngineV18 closed")

    async def run_backtest(self) -> dict[str, Any]:
        """
        Run complete backtest.

        Returns:
            Backtest results summary
        """
        logger.info("=" * 60)
        logger.info("STARTING BACKTEST V18")
        logger.info("=" * 60)

        current_date = self.config.start_date

        while current_date <= self.config.end_date:
            await self._process_day(current_date)
            current_date += timedelta(days=1)
            self.state.day_count += 1

            # Log progress every 30 days
            if self.state.day_count % 30 == 0:
                logger.info(
                    f"Day {self.state.day_count}: Portfolio value: €{self.state.total_value:,.2f}"
                )

        # Generate results
        results = self._generate_results()

        logger.info("=" * 60)
        logger.info("BACKTEST COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Final portfolio value: €{self.state.total_value:,.2f}")
        logger.info(
            f"Total return: {(self.state.total_value / self.config.initial_cash - 1) * 100:.2f}%"
        )
        logger.info(f"Total trades: {len(self.state.trades)}")

        return results

    async def _process_day(self, date: datetime):
        """Process a single trading day."""
        logger.debug(f"Processing {date.date()}")

        for symbol in self.config.symbols:
            # Check if we have an open position
            if self.elemental_manager.has_open_position(symbol):
                # Evaluate exit
                await self._evaluate_exit(symbol, date)
            else:
                # Evaluate entry
                await self._evaluate_entry(symbol, date)

    async def _evaluate_entry(self, symbol: str, date: datetime):
        """Evaluate entry opportunity for a symbol."""
        try:
            # Get current price (mock for now, would fetch from data source)
            current_price = await self._get_price(symbol, date)

            if current_price is None:
                return

            # Get VedAstro signal
            vedastro_result = await self.mcp_client.call_tool(
                "vedastro__generate_signal",
                {"symbol": symbol, "current_price": current_price},
            )

            # Check VedAstro confidence
            confidence = vedastro_result.get("confidence", 0)
            strength_score = vedastro_result.get("strength_score", 0)
            signal = vedastro_result.get("signal", "HOLD")

            if confidence < self.config.min_vedastro_confidence:
                logger.debug(f"{symbol}: VedAstro confidence too low ({confidence}%)")
                return

            if strength_score < self.config.min_vedastro_score:
                logger.debug(f"{symbol}: VedAstro strength too low ({strength_score})")
                return

            if signal not in ["BUY", "STRONG_BUY"]:
                logger.debug(f"{symbol}: Signal is {signal}, not BUY")
                return

            # Get price history
            price_history = await self._get_price_history(symbol, date)

            # Get dominant planet
            dominant_planet = self._get_dominant_planet(date)

            # Evaluate entry via Elemental Manager
            entry = await self.elemental_manager.evaluate_entry(
                symbol=symbol,
                current_price=current_price,
                portfolio_value=self.state.total_value,
                vedastro_score=strength_score,
                dominant_planet=dominant_planet,
                price_history=price_history,
            )

            if entry:
                # Execute trade
                await self._execute_entry(entry, date)

        except Exception as e:
            logger.error(f"Error evaluating entry for {symbol}: {e}")
            # Continue with next symbol - error isolation via MCP

    async def _evaluate_exit(self, symbol: str, date: datetime):
        """Evaluate exit for open position."""
        try:
            current_price = await self._get_price(symbol, date)

            if current_price is None:
                return

            should_exit, reason = await self.elemental_manager.evaluate_exit(
                symbol=symbol,
                current_price=current_price,
                current_date=date.isoformat(),
            )

            if should_exit:
                await self._execute_exit(symbol, current_price, reason, date)

        except Exception as e:
            logger.error(f"Error evaluating exit for {symbol}: {e}")

    async def _execute_entry(self, entry: dict[str, Any], date: datetime):
        """Execute entry trade."""
        symbol = entry["symbol"]
        quantity = entry["quantity"]
        price = entry["entry_price"]

        try:
            # Execute via MCP
            result = await self.mcp_client.call_tool(
                "execution__execute_paper_trade",
                {
                    "symbol": symbol,
                    "action": "BUY",
                    "quantity": quantity,
                    "current_price": price,
                    "account_id": self.config.account_id,
                },
            )

            # Update state
            cost = quantity * price
            commission = result.get("commission", cost * 0.0005)
            total_cost = cost + commission

            self.state.cash -= total_cost
            self.state.open_positions[symbol] = {
                "entry_date": date.isoformat(),
                "entry_price": price,
                "quantity": quantity,
                "cost_basis": total_cost,
            }

            self.state.trades.append(
                {
                    "date": date.isoformat(),
                    "symbol": symbol,
                    "action": "BUY",
                    "quantity": quantity,
                    "price": price,
                    "commission": commission,
                    "type": "entry",
                }
            )

            logger.info(f"ENTRY: {symbol} {quantity:.2f} @ ${price:.2f}")

        except Exception as e:
            logger.error(f"Failed to execute entry for {symbol}: {e}")

    async def _execute_exit(self, symbol: str, price: float, reason: str, date: datetime):
        """Execute exit trade."""
        position = self.state.open_positions.get(symbol)
        if not position:
            return

        quantity = position["quantity"]

        try:
            # Execute via MCP
            result = await self.mcp_client.call_tool(
                "execution__execute_paper_trade",
                {
                    "symbol": symbol,
                    "action": "SELL",
                    "quantity": quantity,
                    "current_price": price,
                    "account_id": self.config.account_id,
                },
            )

            # Update state
            proceeds = quantity * price
            commission = result.get("commission", proceeds * 0.0005)
            net_proceeds = proceeds - commission

            # Calculate P&L
            cost_basis = position["cost_basis"]
            pnl = net_proceeds - cost_basis
            pnl_pct = pnl / cost_basis if cost_basis > 0 else 0

            self.state.cash += net_proceeds
            del self.state.open_positions[symbol]

            self.state.trades.append(
                {
                    "date": date.isoformat(),
                    "symbol": symbol,
                    "action": "SELL",
                    "quantity": quantity,
                    "price": price,
                    "commission": commission,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "reason": reason,
                    "type": "exit",
                }
            )

            logger.info(
                f"EXIT: {symbol} {quantity:.2f} @ ${price:.2f} (P&L: {pnl_pct*100:+.2f}%) [{reason}]"
            )

        except Exception as e:
            logger.error(f"Failed to execute exit for {symbol}: {e}")

    async def _get_price(self, symbol: str, date: datetime) -> float | None:
        """Get price for symbol on date (mock implementation)."""
        # In production, this would fetch from data source
        # For now, return mock price based on symbol hash
        import hashlib

        hash_val = int(
            hashlib.blake2b(f"{symbol}{date.date()}".encode(), digest_size=8).hexdigest(),
            16,
        )
        return 100.0 + (hash_val % 100)

    async def _get_price_history(self, symbol: str, date: datetime) -> list[float]:
        """Get price history for symbol (mock implementation)."""
        # Generate 30 days of mock prices
        prices = []
        await self._get_price(symbol, date)

        for i in range(30):
            prev_date = date - timedelta(days=i)
            price = await self._get_price(symbol, prev_date)
            prices.insert(0, price)

        return prices

    def _get_dominant_planet(self, date: datetime) -> str:
        """Get dominant planet for date."""
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        return planets[date.day % 7]

    def _generate_results(self) -> dict[str, Any]:
        """Generate backtest results summary."""
        # Calculate metrics
        total_trades = len([t for t in self.state.trades if t["type"] == "exit"])
        winning_trades = len([t for t in self.state.trades if t.get("pnl", 0) > 0])
        losing_trades = total_trades - winning_trades

        total_return = self.state.total_value / self.config.initial_cash - 1

        gross_pnl = sum(t.get("pnl", 0) for t in self.state.trades if t["type"] == "exit")
        total_commission = sum(t.get("commission", 0) for t in self.state.trades)

        return {
            "config": {
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat(),
                "symbols": self.config.symbols,
                "initial_cash": self.config.initial_cash,
            },
            "results": {
                "final_value": self.state.total_value,
                "total_return_pct": total_return * 100,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
                "gross_pnl": gross_pnl,
                "total_commission": total_commission,
                "net_pnl": gross_pnl - total_commission,
                "day_count": self.state.day_count,
            },
            "trades": self.state.trades,
            "engine_version": "V18_MCP",
        }


async def run_backtest_v18(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime,
    initial_cash: float = 100000.0,
) -> dict[str, Any]:
    """
    Convenience function to run a backtest.

    Args:
        symbols: List of symbols to trade
        start_date: Start date
        end_date: End date
        initial_cash: Initial cash

    Returns:
        Backtest results
    """
    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        symbols=symbols,
        initial_cash=initial_cash,
    )

    engine = BacktestEngineV18(config)

    try:
        await engine.initialize()
        results = await engine.run_backtest()
        return results
    finally:
        await engine.close()


# For testing
if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run a quick test
    async def test():
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        symbols = ["AAPL", "MSFT"]

        results = await run_backtest_v18(symbols, start, end, initial_cash=50000.0)

        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Total return: {results['results']['total_return_pct']:.2f}%")
        print(f"Total trades: {results['results']['total_trades']}")
        print(f"Win rate: {results['results']['win_rate']*100:.1f}%")

    asyncio.run(test())
