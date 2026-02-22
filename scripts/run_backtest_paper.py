"""
Paper Trading Backtest Runner
Runs backtests using historical data (2020-2026) with paper trading mode
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set trading mode to paper
os.environ["TRADING_MODE"] = "paper"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("PaperBacktest")


@dataclass
class BacktestResult:
    """Backtest result container"""

    session_id: str
    start_date: str
    end_date: str
    symbols: List[str]
    initial_capital: float
    final_value: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown_pct: float
    sharpe_ratio: float
    trades: List[Dict]
    equity_curve: List[Dict]
    vedic_metrics: Dict

    def to_dict(self) -> Dict:
        return asdict(self)

    def save(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info(f"Results saved to {filepath}")


class PaperBacktestRunner:
    """
    Backtest runner using paper trading mode

    Features:
    - Historical data replay from database
    - Paper trading execution (no real orders)
    - Vedic cycle integration
    - Agent-based decision making
    - Performance analytics
    """

    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0,
        speed: float = 1000.0,  # Simulation speed multiplier
    ):
        self.symbols = symbols
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        self.initial_capital = initial_capital
        self.speed = speed

        self.session_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trades = []
        self.equity_curve = []
        self.vedic_snapshots = []

        logger.info(f"Backtest Session: {self.session_id}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Symbols: {symbols}")
        logger.info(f"Initial Capital: €{initial_capital:,.2f}")

    async def initialize(self):
        """Initialize backtest components"""
        logger.info("Initializing backtest components...")

        # Import here to avoid circular imports
        from backend.events.event_bus import EventBus
        from backend.execution.backtest_engine import BacktestEngine
        from backend.execution.paper_trading import PaperTradingService
        from backend.services.portfolio_tracker import PortfolioTracker

        # Initialize event bus
        self.event_bus = EventBus()

        # Initialize backtest engine for historical data
        self.engine = BacktestEngine(
            start_date=self.start_date, end_date=self.end_date, speed=self.speed
        )

        # Initialize paper trading service
        self.paper_trading = PaperTradingService(initial_balance=self.initial_capital)

        # Initialize portfolio tracker
        self.portfolio = PortfolioTracker()

        logger.info("Components initialized")

    async def run(self) -> BacktestResult:
        """Run the backtest"""
        await self.initialize()

        logger.info("=" * 60)
        logger.info("BACKTEST STARTING")
        logger.info("=" * 60)

        # Process each symbol
        for symbol in self.symbols:
            await self._process_symbol(symbol)

        # Calculate final results
        result = self._calculate_results()

        logger.info("=" * 60)
        logger.info("BACKTEST COMPLETE")
        logger.info("=" * 60)
        self._print_summary(result)

        return result

    async def _process_symbol(self, symbol: str):
        """Process a single symbol through the backtest period"""
        logger.info(f"Processing {symbol}...")

        tick_count = 0
        async for tick in self.engine.stream_ticks(symbol):
            tick_count += 1

            # Simulate agent decision (placeholder for actual agent logic)
            decision = await self._make_decision(tick)

            if decision["action"] in ["buy", "sell"]:
                # Execute paper trade
                trade = await self._execute_trade(decision, tick)
                if trade:
                    self.trades.append(trade)

            # Record equity at intervals
            if tick_count % 100 == 0:
                self._record_equity(tick.timestamp)

            # Log progress
            if tick_count % 500 == 0:
                logger.info(
                    f"  {symbol}: {tick_count} ticks processed, "
                    f"{len([t for t in self.trades if t['symbol'] == symbol])} trades"
                )

        logger.info(
            f"{symbol}: {tick_count} ticks, "
            f"{len([t for t in self.trades if t['symbol'] == symbol])} trades"
        )

    async def _make_decision(self, tick) -> Dict:
        """
        Simulate agent decision making
        In production, this would call the actual cognitive agents
        """
        import random

        # Simple random strategy for demonstration
        # In production, use: from backend.agents.decision_engine import DecisionEngine

        actions = ["hold", "hold", "hold", "buy", "sell"]  # Mostly hold
        action = random.choice(actions)

        return {
            "action": action,
            "symbol": tick.symbol,
            "price": tick.last,
            "quantity": 0.1 if action in ["buy", "sell"] else 0,
            "timestamp": tick.timestamp.isoformat(),
        }

    async def _execute_trade(self, decision: Dict, tick) -> Optional[Dict]:
        """Execute a paper trade"""
        try:
            if decision["action"] == "buy":
                order = await self.paper_trading.create_order(
                    symbol=decision["symbol"],
                    side="buy",
                    quantity=decision["quantity"],
                    price=decision["price"],
                )
            else:
                order = await self.paper_trading.create_order(
                    symbol=decision["symbol"],
                    side="sell",
                    quantity=decision["quantity"],
                    price=decision["price"],
                )

            trade_record = {
                "timestamp": decision["timestamp"],
                "symbol": decision["symbol"],
                "action": decision["action"],
                "price": decision["price"],
                "quantity": decision["quantity"],
                "value": decision["price"] * decision["quantity"],
                "order_id": order.get("id", "unknown"),
            }

            logger.debug(f"Trade executed: {trade_record}")
            return trade_record

        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return None

    def _record_equity(self, timestamp: datetime):
        """Record equity curve point"""
        portfolio_value = self.paper_trading.get_portfolio_value()
        self.equity_curve.append(
            {
                "timestamp": timestamp.isoformat(),
                "value": portfolio_value,
                "cash": self.paper_trading.get_cash_balance(),
                "positions_value": portfolio_value
                - self.paper_trading.get_cash_balance(),
            }
        )

    def _calculate_results(self) -> BacktestResult:
        """Calculate final backtest results"""
        final_value = self.paper_trading.get_portfolio_value()
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        # Calculate trade statistics
        winning = [t for t in self.trades if t.get("pnl", 0) > 0]
        losing = [t for t in self.trades if t.get("pnl", 0) < 0]

        # Calculate max drawdown from equity curve
        max_dd = self._calculate_max_drawdown()

        # Calculate Sharpe ratio (simplified)
        sharpe = self._calculate_sharpe()

        # Vedic metrics
        vedic_metrics = {
            "total_cycles": len(self.vedic_snapshots),
            "avg_harmony_score": sum(s.get("harmony", 0) for s in self.vedic_snapshots)
            / max(len(self.vedic_snapshots), 1),
            "rahu_kala_blocks": sum(
                1 for s in self.vedic_snapshots if s.get("rahu_kala_active", False)
            ),
        }

        return BacktestResult(
            session_id=self.session_id,
            start_date=self.start_date.isoformat(),
            end_date=self.end_date.isoformat(),
            symbols=self.symbols,
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return_pct=total_return,
            total_trades=len(self.trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            max_drawdown_pct=max_dd,
            sharpe_ratio=sharpe,
            trades=self.trades,
            equity_curve=self.equity_curve,
            vedic_metrics=vedic_metrics,
        )

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if not self.equity_curve:
            return 0.0

        peak = self.equity_curve[0]["value"]
        max_dd = 0.0

        for point in self.equity_curve:
            value = point["value"]
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe(self) -> float:
        """Calculate simplified Sharpe ratio"""
        if len(self.equity_curve) < 2:
            return 0.0

        returns = []
        for i in range(1, len(self.equity_curve)):
            prev = self.equity_curve[i - 1]["value"]
            curr = self.equity_curve[i]["value"]
            if prev > 0:
                returns.append((curr - prev) / prev)

        if not returns:
            return 0.0

        import statistics

        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.001

        # Annualized Sharpe (assuming daily data, 252 trading days)
        if std_return == 0:
            return 0.0

        return (avg_return * 252) / (std_return * (252**0.5))

    def _print_summary(self, result: BacktestResult):
        """Print backtest summary"""
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Session ID:      {result.session_id}")
        print(f"Period:          {result.start_date[:10]} to {result.end_date[:10]}")
        print(
            f"Symbols:         {', '.join(result.symbols[:5])}{'...' if len(result.symbols) > 5 else ''}"
        )
        print("\nCapital:")
        print(f"  Initial:       €{result.initial_capital:,.2f}")
        print(f"  Final:         €{result.final_value:,.2f}")
        print(f"  Return:        {result.total_return_pct:+.2f}%")
        print("\nTrades:")
        print(f"  Total:         {result.total_trades}")
        print(f"  Winning:       {result.winning_trades}")
        print(f"  Losing:        {result.losing_trades}")
        print(
            f"  Win Rate:      {result.winning_trades/max(result.total_trades,1)*100:.1f}%"
        )
        print("\nRisk Metrics:")
        print(f"  Max Drawdown:  {result.max_drawdown_pct:.2f}%")
        print(f"  Sharpe Ratio:  {result.sharpe_ratio:.2f}")
        print("\nVedic Metrics:")
        print(f"  Total Cycles:  {result.vedic_metrics['total_cycles']}")
        print(f"  Avg Harmony:   {result.vedic_metrics['avg_harmony_score']:.2f}")
        print(f"  Rahu Blocks:   {result.vedic_metrics['rahu_kala_blocks']}")
        print("=" * 60)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run paper trading backtest")
    parser.add_argument(
        "--symbols", nargs="+", default=["BTC", "ETH"], help="Symbols to backtest"
    )
    parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2024-12-31", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--capital", type=float, default=10000.0, help="Initial capital"
    )
    parser.add_argument(
        "--speed", type=float, default=1000.0, help="Simulation speed multiplier"
    )
    parser.add_argument("--output", default=None, help="Output file path")

    args = parser.parse_args()

    runner = PaperBacktestRunner(
        symbols=args.symbols,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        speed=args.speed,
    )

    result = await runner.run()

    # Save results
    output_path = args.output or f"backtest_results/{result.session_id}.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.save(output_path)

    return result


if __name__ == "__main__":
    asyncio.run(main())
