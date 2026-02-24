"""
REAL Paper Trading V18 - MCP Edition with VedAstro

Exact copy of Backtest V18 logic but for live paper trading:
- VedAstro signals via MCP
- Elemental Agent Manager for entry/exit
- V17/V18 constraints (2% max, €2k cap)
- Real-time market data
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.mcp_broker.client import MCPClientWrapper
from backend.mcp_broker.elemental_manager_v18 import ElementalAgentManagerV18
from backend.services.data_prefetch_agent import DataPreFetchAgent, get_data_agent
from backend.services.paper_trading_ws_broadcast import (
    broadcast_agent_decision,
    broadcast_stats,
    broadcast_trade,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RealPaperTradingV18")


@dataclass
class PaperTradingConfig:
    """Configuration matching Backtest V18."""

    initial_cash: float = 10000.0
    account_id: str = "paper_v18"

    # V17/V18 constraints
    max_position_pct: float = 0.02  # 2% of portfolio
    max_position_eur: float = 2000.0  # €2k cap

    # VedAstro settings
    min_vedastro_confidence: float = 50.0
    min_vedastro_score: float = 45.0

    # Trading cycle settings
    cycle_interval_seconds: int = 30  # Check every 30 seconds
    symbols_per_cycle: int = 20  # Analyze 20 symbols per cycle


@dataclass
class PaperTradingState:
    """Current state of paper trading."""

    cash: float
    total_value: float
    open_positions: dict[str, dict[str, Any]] = field(default_factory=dict)
    trades: list[dict[str, Any]] = field(default_factory=list)
    total_trades: int = 0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0


class RealPaperTradingV18:
    """
    V18 Paper Trading Engine - Exact Backtest V18 Logic.

    Uses:
    - MCP client for VedAstro signals
    - ElementalAgentManagerV18 for entry/exit
    - Real-time market data via DataPreFetchAgent
    - Same constraints as backtest
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.config = PaperTradingConfig(initial_cash=initial_capital)
        self.state = PaperTradingState(cash=initial_capital, total_value=initial_capital)

        # MCP Infrastructure (same as backtest)
        self.mcp_client: MCPClientWrapper | None = None
        self.elemental_manager: ElementalAgentManagerV18 | None = None

        # Portfolio and Data
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_capital)
        self.data_agent: DataPreFetchAgent | None = None
        self.all_symbols: list[str] = []

        # State
        self.running = False
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self._cycle_count = 0

        print("=" * 80)
        print("     REAL PAPER TRADING V18 - MCP Edition with VedAstro")
        print("=" * 80)
        print(f"\nInitial Capital: EUR {initial_capital:,.2f}")
        print(
            f"Max Position: {self.config.max_position_pct:.0%} or EUR {self.config.max_position_eur:,.0f}"
        )
        print(f"VedAstro Min Confidence: {self.config.min_vedastro_confidence}%")
        print(f"VedAstro Min Score: {self.config.min_vedastro_score}")
        print()

    async def initialize(self):
        """Initialize MCP client, Elemental Manager, and Data Agent."""
        logger.info("Initializing Paper Trading V18...")

        # 1. Initialize MCP client (same as backtest)
        self.mcp_client = MCPClientWrapper()
        await self.mcp_client.initialize()
        logger.info("MCP client initialized")

        # 2. Initialize Elemental Manager (same as backtest)
        self.elemental_manager = ElementalAgentManagerV18(self.mcp_client)
        await self.elemental_manager.initialize()
        logger.info("Elemental Manager initialized")

        # 3. Initialize Data Pre-fetch Agent
        self.data_agent = get_data_agent()
        await self.data_agent.initialize()
        self.all_symbols = self.data_agent.symbols
        logger.info(f"Data agent initialized with {len(self.all_symbols)} symbols")

        # 4. Warm up data (ensure we have prices)
        logger.info("Warming up data cache...")
        await asyncio.sleep(5)  # Let data agent collect initial prices

        logger.info("Paper Trading V18 ready")

    async def close(self):
        """Cleanup resources."""
        self.running = False

        if self.data_agent:
            await self.data_agent.stop()

        if self.elemental_manager:
            await self.elemental_manager.close()

        if self.mcp_client:
            await self.mcp_client.close()

        logger.info("Paper Trading V18 closed")

    async def run(self, duration_hours: int = 8):
        """Run paper trading session."""
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        self.running = True

        print(f"[START] {self.start_time}")
        print(f"[END]   {self.end_time}")
        print(
            f"[CYCLE] Every {self.config.cycle_interval_seconds}s, {self.config.symbols_per_cycle} symbols"
        )
        print()

        # Start status reporter
        reporter = asyncio.create_task(self._status_reporter(interval=60))

        try:
            while datetime.utcnow() < self.end_time and self.running:
                await self._trading_cycle()
                await asyncio.sleep(self.config.cycle_interval_seconds)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Trading loop error: {e}")
        finally:
            self.running = False
            reporter.cancel()
            try:
                await reporter
            except asyncio.CancelledError:
                pass

        await self._final_status()

    async def _trading_cycle(self):
        """Execute one trading cycle - Exact Backtest V18 Logic."""
        self._cycle_count += 1

        if not self.data_agent or not self.elemental_manager:
            return

        # Get fresh prices from data agent
        prices = await self.data_agent.get_all_prices()

        if len(prices) < 10:
            logger.warning(f"Limited fresh prices: {len(prices)}")
            return

        # Update portfolio value
        self.state.total_value = await self._calculate_portfolio_value(prices)

        # Select symbols to analyze (rotating to cover all over time)
        available = list(prices.keys())
        cycle_offset = (self._cycle_count * self.config.symbols_per_cycle) % len(available)
        to_analyze = []
        for i in range(self.config.symbols_per_cycle):
            idx = (cycle_offset + i) % len(available)
            to_analyze.append(available[idx])

        trades_this_cycle = 0

        for symbol in to_analyze:
            try:
                price_data = prices[symbol]
                current_price = price_data.price

                # Get price history for technical analysis
                price_history = await self.data_agent.get_price_history(symbol, days=30)

                # Check if we have an open position (EXACT backtest logic)
                if self.elemental_manager.has_open_position(symbol):
                    # Evaluate exit
                    exit_triggered = await self._evaluate_exit(symbol, current_price)
                    if exit_triggered:
                        trades_this_cycle += 1
                else:
                    # Evaluate entry (EXACT backtest logic)
                    entry_triggered = await self._evaluate_entry(
                        symbol, current_price, price_history
                    )
                    if entry_triggered:
                        trades_this_cycle += 1

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        if trades_this_cycle > 0:
            logger.info(f"Cycle {self._cycle_count}: {trades_this_cycle} trades executed")

        # Broadcast stats
        await self._broadcast_stats()

    async def _evaluate_entry(
        self, symbol: str, current_price: float, price_history: list[float]
    ) -> bool:
        """Evaluate entry - EXACT Backtest V18 Logic."""
        try:
            # 1. Get VedAstro signal via MCP (same as backtest)
            vedastro_result = await self.mcp_client.call_tool(
                "vedastro__generate_signal", {"symbol": symbol, "current_price": current_price}
            )

            confidence = vedastro_result.get("confidence", 0)
            strength_score = vedastro_result.get("strength_score", 0)
            signal = vedastro_result.get("signal", "HOLD")

            # 2. Check VedAstro thresholds (same as backtest)
            if confidence < self.config.min_vedastro_confidence:
                logger.debug(f"{symbol}: VedAstro confidence too low ({confidence}%)")
                return False

            if strength_score < self.config.min_vedastro_score:
                logger.debug(f"{symbol}: VedAstro strength too low ({strength_score})")
                return False

            if signal not in ["BUY", "STRONG_BUY"]:
                logger.debug(f"{symbol}: Signal is {signal}, not BUY")
                return False

            # 3. Get dominant planet
            dominant_planet = self._get_dominant_planet(datetime.utcnow())

            # 4. Evaluate entry via Elemental Manager (same as backtest)
            entry = await self.elemental_manager.evaluate_entry(
                symbol=symbol,
                current_price=current_price,
                portfolio_value=self.state.total_value,
                vedastro_score=strength_score,
                dominant_planet=dominant_planet,
                price_history=price_history,
            )

            if not entry:
                return False

            # 5. Apply V17/V18 constraints
            position_size = entry.get("position_size", 0)

            # Max position constraint
            max_position = min(
                self.state.total_value * self.config.max_position_pct, self.config.max_position_eur
            )
            position_size = min(position_size, max_position)

            if position_size < 100:  # Minimum EUR 100 trade
                logger.debug(f"{symbol}: Position size too small ({position_size})")
                return False

            # 6. Execute trade via MCP (same as backtest)
            quantity = position_size / current_price

            result = await self.mcp_client.call_tool(
                "execution__execute_paper_trade",
                {
                    "symbol": symbol,
                    "action": "BUY",
                    "quantity": quantity,
                    "current_price": current_price,
                    "account_id": self.config.account_id,
                },
            )

            if result.get("status") != "FILLED":
                logger.warning(f"{symbol}: Trade not filled")
                return False

            # 7. Update state
            cost = quantity * current_price
            commission = result.get("commission", cost * 0.0005)

            self.state.cash -= cost + commission
            self.state.open_positions[symbol] = {
                "entry_date": datetime.utcnow().isoformat(),
                "entry_price": current_price,
                "quantity": quantity,
                "position_size": position_size,
                "commission": commission,
            }

            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": current_price,
                "position_size": position_size,
                "commission": commission,
                "vedastro_confidence": confidence,
                "vedastro_score": strength_score,
                "dominant_planet": dominant_planet,
                "type": "entry",
            }

            self.state.trades.append(trade)
            self.state.total_trades += 1

            # 8. Broadcast
            await broadcast_trade(trade)
            await broadcast_agent_decision(
                agent="V18_Elemental",
                strategy="vedastro_consensus",
                symbol=symbol,
                decision="BUY",
                confidence=confidence / 100,
                reason=f"VedAstro score {strength_score}, {dominant_planet}",
                executed=True,
            )

            logger.info(
                f"ENTRY: {symbol} {quantity:.4f} @ EUR {current_price:.2f} (Size: EUR {position_size:.2f})"
            )

            return True

        except Exception as e:
            logger.error(f"Error evaluating entry for {symbol}: {e}")
            return False

    async def _evaluate_exit(self, symbol: str, current_price: float) -> bool:
        """Evaluate exit - EXACT Backtest V18 Logic."""
        try:
            # 1. Check exit via Elemental Manager (same as backtest)
            should_exit, reason = await self.elemental_manager.evaluate_exit(
                symbol=symbol,
                current_price=current_price,
                current_date=datetime.utcnow().isoformat(),
            )

            if not should_exit:
                return False

            # 2. Get position details
            position = self.state.open_positions.get(symbol)
            if not position:
                return False

            quantity = position["quantity"]
            entry_price = position["entry_price"]

            # 3. Execute exit via MCP (same as backtest)
            result = await self.mcp_client.call_tool(
                "execution__execute_paper_trade",
                {
                    "symbol": symbol,
                    "action": "SELL",
                    "quantity": quantity,
                    "current_price": current_price,
                    "account_id": self.config.account_id,
                },
            )

            if result.get("status") != "FILLED":
                logger.warning(f"{symbol}: Exit trade not filled")
                return False

            # 4. Calculate P&L
            proceeds = quantity * current_price
            commission = result.get("commission", proceeds * 0.0005)
            net_proceeds = proceeds - commission

            cost_basis = position["position_size"] + position.get("commission", 0)
            pnl = net_proceeds - cost_basis
            pnl_pct = pnl / cost_basis if cost_basis > 0 else 0

            # 5. Update state
            self.state.cash += net_proceeds
            del self.state.open_positions[symbol]

            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "action": "SELL",
                "quantity": quantity,
                "price": current_price,
                "commission": commission,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": reason,
                "type": "exit",
            }

            self.state.trades.append(trade)
            self.state.total_trades += 1
            self.state.total_pnl += pnl

            # 6. Broadcast
            await broadcast_trade(trade)
            await broadcast_agent_decision(
                agent="V18_Elemental",
                strategy="exit_manager",
                symbol=symbol,
                decision="SELL",
                confidence=0.8,
                reason=reason,
                executed=True,
            )

            logger.info(
                f"EXIT: {symbol} {quantity:.4f} @ EUR {current_price:.2f} (P&L: {pnl_pct*100:+.2f}%) [{reason}]"
            )

            return True

        except Exception as e:
            logger.error(f"Error evaluating exit for {symbol}: {e}")
            return False

    async def _calculate_portfolio_value(self, prices: dict[str, Any]) -> float:
        """Calculate total portfolio value."""
        value = self.state.cash

        for symbol, position in self.state.open_positions.items():
            if symbol in prices:
                price = prices[symbol].price
                qty = position["quantity"]
                value += qty * price

        return value

    def _get_dominant_planet(self, date: datetime) -> str:
        """Get dominant planet for date."""
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        return planets[date.day % 7]

    async def _status_reporter(self, interval: int = 60):
        """Periodically report status."""
        while self.running:
            try:
                await asyncio.sleep(interval)

                if not self.data_agent:
                    continue

                prices = await self.data_agent.get_all_prices()
                portfolio_value = await self._calculate_portfolio_value(prices)
                elapsed = datetime.utcnow() - self.start_time if self.start_time else timedelta(0)

                pnl = portfolio_value - self.config.initial_cash
                pnl_pct = (pnl / self.config.initial_cash) * 100

                print()
                print("=" * 80)
                print(f"STATUS | Elapsed: {elapsed} | Cycles: {self._cycle_count}")
                print(
                    f"       | Trades: {self.state.total_trades} | Positions: {len(self.state.open_positions)}"
                )
                print(
                    f"       | Portfolio: EUR {portfolio_value:,.2f} | P&L: EUR {pnl:+,.2f} ({pnl_pct:+.2f}%)"
                )
                print(f"       | Cash: EUR {self.state.cash:,.2f} | Cache: {len(prices)} prices")
                print("=" * 80)

            except Exception as e:
                logger.error(f"Status reporter error: {e}")

    async def _broadcast_stats(self):
        """Broadcast current stats."""
        try:
            await broadcast_stats(
                {
                    "total_trades": self.state.total_trades,
                    "open_positions": len(self.state.open_positions),
                    "cash": self.state.cash,
                    "portfolio_value": self.state.total_value,
                    "total_pnl": self.state.total_pnl,
                    "cycle": self._cycle_count,
                }
            )
        except Exception as e:
            logger.debug(f"Broadcast error: {e}")

    async def _final_status(self):
        """Print final status."""
        elapsed = datetime.utcnow() - self.start_time if self.start_time else timedelta(0)

        print()
        print("=" * 80)
        print("     SESSION COMPLETE")
        print("=" * 80)
        print(f"Duration: {elapsed}")
        print(f"Total Trades: {self.state.total_trades}")
        print(f"Final Portfolio: EUR {self.state.total_value:,.2f}")
        print(f"Total P&L: EUR {self.state.total_pnl:+,.2f}")
        print("=" * 80)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=8)
    parser.add_argument("--capital", type=float, default=10000.0)
    args = parser.parse_args()

    engine = RealPaperTradingV18(initial_capital=args.capital)

    try:
        await engine.initialize()
        await engine.run(duration_hours=args.duration)
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
