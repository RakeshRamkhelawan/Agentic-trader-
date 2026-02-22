"""
Paper Trading Backtest Runner
Uses historical data from database (2020-2026) for backtesting
"""

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
    trades: List[Dict]
    equity_curve: List[Dict]

    def to_dict(self) -> Dict:
        return asdict(self)

    def save(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info(f"Results saved to {filepath}")


class SimplePaperBacktest:
    """
    Simple backtest using database historical data
    """

    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0,
    ):
        self.symbols = symbols
        self.start_date = datetime.fromisoformat(start_date)
        self.end_date = datetime.fromisoformat(end_date)
        self.initial_capital = initial_capital

        self.session_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trades = []
        self.equity_curve = []
        self.positions = {}  # symbol -> {qty, avg_price}
        self.cash = initial_capital

        logger.info(f"Backtest Session: {self.session_id}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Symbols: {symbols}")
        logger.info(f"Initial Capital: €{initial_capital:,.2f}")

    def fetch_historical_data(self, symbol: str) -> List[Dict]:
        """Fetch OHLCV data from database"""
        from sqlalchemy import create_engine, text

        DATABASE_URL = (
            os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db",
            )
            .replace("+asyncpg", "+psycopg2")
            .replace("postgresql+psycopg2", "postgresql")
        )

        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT symbol, timestamp, open, high, low, close, volume
                FROM market_candles
                WHERE symbol = :symbol
                  AND timestamp >= :start
                  AND timestamp <= :end
                ORDER BY timestamp ASC
            """
                ),
                {"symbol": symbol, "start": self.start_date, "end": self.end_date},
            )

            rows = []
            for row in result:
                rows.append(
                    {
                        "symbol": row[0],
                        "timestamp": row[1],
                        "open": row[2],
                        "high": row[3],
                        "low": row[4],
                        "close": row[5],
                        "volume": row[6],
                    }
                )

            return rows

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        value = self.cash
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol, position["avg_price"])
            value += position["qty"] * price
        return value

    def execute_trade(
        self, symbol: str, action: str, price: float, timestamp: datetime
    ) -> Optional[Dict]:
        """Execute a paper trade"""
        qty = 0.1  # Fixed position size for simplicity
        value = qty * price

        if action == "buy":
            if value > self.cash:
                return None  # Insufficient funds

            if symbol in self.positions:
                # Update average price
                old_qty = self.positions[symbol]["qty"]
                old_price = self.positions[symbol]["avg_price"]
                new_qty = old_qty + qty
                new_price = (old_qty * old_price + qty * price) / new_qty
                self.positions[symbol] = {"qty": new_qty, "avg_price": new_price}
            else:
                self.positions[symbol] = {"qty": qty, "avg_price": price}

            self.cash -= value

        elif action == "sell":
            if symbol not in self.positions or self.positions[symbol]["qty"] < qty:
                return None  # No position to sell

            self.positions[symbol]["qty"] -= qty
            if self.positions[symbol]["qty"] <= 0:
                del self.positions[symbol]

            self.cash += value

        trade = {
            "timestamp": timestamp.isoformat(),
            "symbol": symbol,
            "action": action,
            "price": price,
            "qty": qty,
            "value": value,
        }

        self.trades.append(trade)
        return trade

    def simple_strategy(self, candle: Dict, prev_candle: Optional[Dict]) -> str:
        """
        Simple momentum strategy:
        - Buy if close > previous close (uptrend)
        - Sell if close < previous close (downtrend)
        """
        if prev_candle is None:
            return "hold"

        curr_close = candle["close"]
        prev_close = prev_candle["close"]

        # Add some randomness to avoid over-trading
        if curr_close > prev_close * 1.01:  # 1% up
            return "buy"
        elif curr_close < prev_close * 0.99:  # 1% down
            return "sell"

        return "hold"

    def run(self) -> BacktestResult:
        """Run the backtest"""
        logger.info("=" * 60)
        logger.info("BACKTEST STARTING")
        logger.info("=" * 60)

        all_data = {}
        for symbol in self.symbols:
            data = self.fetch_historical_data(symbol)
            if data:
                all_data[symbol] = data
                logger.info(f"Loaded {len(data)} candles for {symbol}")
            else:
                logger.warning(f"No data for {symbol}")

        if not all_data:
            raise ValueError("No historical data found for any symbol")

        # Process day by day (simplified - assumes all symbols have same dates)
        first_symbol = list(all_data.keys())[0]
        dates = [c["timestamp"] for c in all_data[first_symbol]]

        logger.info(f"Processing {len(dates)} trading days...")

        prev_candles = {}

        for i, timestamp in enumerate(dates):
            current_prices = {}

            for symbol, data in all_data.items():
                if i < len(data):
                    candle = data[i]
                    current_prices[symbol] = candle["close"]

                    # Apply strategy
                    prev = prev_candles.get(symbol)
                    action = self.simple_strategy(candle, prev)

                    if action in ["buy", "sell"]:
                        self.execute_trade(symbol, action, candle["close"], timestamp)

                    prev_candles[symbol] = candle

            # Record equity curve every 10 days
            if i % 10 == 0:
                portfolio_value = self.get_portfolio_value(current_prices)
                self.equity_curve.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "value": portfolio_value,
                        "cash": self.cash,
                        "positions_value": portfolio_value - self.cash,
                    }
                )

        # Calculate final results
        final_prices = {s: all_data[s][-1]["close"] for s in all_data if all_data[s]}
        final_value = self.get_portfolio_value(final_prices)

        return self._calculate_results(final_value)

    def _calculate_results(self, final_value: float) -> BacktestResult:
        """Calculate final backtest results"""
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        # Calculate trade statistics
        winning = [t for t in self.trades if t["action"] == "sell"]  # Simplified
        losing = []  # Would need PnL tracking per trade

        # Calculate max drawdown
        max_dd = self._calculate_max_drawdown()

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
            trades=self.trades[-50:],  # Last 50 trades for brevity
            equity_curve=self.equity_curve,
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

    def print_summary(self, result: BacktestResult):
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
        print(f"  Max Drawdown:  {result.max_drawdown_pct:.2f}%")
        print("=" * 60)


def main():
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
    parser.add_argument("--output", default=None, help="Output file path")

    args = parser.parse_args()

    backtest = SimplePaperBacktest(
        symbols=args.symbols,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
    )

    result = backtest.run()
    backtest.print_summary(result)

    # Save results
    output_path = args.output or f"backtest_results/{result.session_id}.json"
    os.makedirs(os.path.dirname(output_path) or "backtest_results", exist_ok=True)
    result.save(output_path)

    return result


if __name__ == "__main__":
    result = main()
