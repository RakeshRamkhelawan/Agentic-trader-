#!/usr/bin/env python3
"""
Backtest met Echte Historische Data

Gebruik gedownloade CSV data voor realistische backtests.

Usage:
    python scripts/backtest_with_real_data.py --file data/historical/BTC-EUR_1h_cryptodatadownload.csv
    python scripts/backtest_with_real_data.py --symbol BTC-EUR --timeframe 1h --days 365
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.backtesting.consciousness_strategy import ConsciousnessStrategy
from backend.backtesting.data_feed_historical import HistoricalCSVData
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.models import BacktestConfig
from backend.backtesting.strategies.simple_ma import MovingAverageStrategy


class RealDataBacktest:
    """Run backtest with real historical data."""

    def __init__(self, data_path: str, capital: float = 10000.0):
        self.data_path = Path(data_path)
        self.capital = capital

    def load_data(self) -> pd.DataFrame:
        """Load and validate data."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        # Try CSV first
        if self.data_path.suffix == ".csv":
            df = pd.read_csv(self.data_path)
        elif self.data_path.suffix == ".parquet":
            df = pd.read_parquet(self.data_path)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")

        # Standardize columns
        df.columns = [c.lower().strip() for c in df.columns]

        # Ensure required columns exist
        required = ["open", "high", "low", "close", "volume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        # Parse timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        elif "date" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"])

        # Sort by timestamp
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp")

        return df

    async def run(
        self, strategy_type: str = "consciousness", symbol: str = None
    ) -> dict:
        """Run backtest with loaded data."""

        # Load data
        print(f"Loading data from: {self.data_path}")
        df = self.load_data()
        print(f"✓ Loaded {len(df)} rows")

        # Determine symbol
        if symbol is None:
            # Try to extract from filename
            symbol = self.data_path.stem.split("_")[0]

        # Get date range
        if "timestamp" in df.columns:
            start_date = df["timestamp"].min()
            end_date = df["timestamp"].max()
        else:
            start_date = datetime.now() - pd.Timedelta(days=len(df))
            end_date = datetime.now()

        print("\nBacktest Configuration:")
        print(f"  Symbol:      {symbol}")
        print(f"  Period:      {start_date} to {end_date}")
        print(f"  Duration:    {(end_date - start_date).days} days")
        print(f"  Rows:        {len(df):,}")
        print(f"  Capital:     €{self.capital:,.2f}")
        print(f"  Strategy:    {strategy_type}")

        # Create temporary CSV in expected format
        temp_csv = Path("/tmp/backtest_data.csv")
        df.to_csv(temp_csv, index=False)

        # Setup data feed
        data_feed = HistoricalCSVData(str(temp_csv))
        data_feed.load_data(symbols=[symbol], start_date=start_date, end_date=end_date)

        # Setup engine
        engine = BacktestEngine(data_feed, initial_capital=self.capital)

        # Setup strategy
        if strategy_type == "consciousness":
            strategy = ConsciousnessStrategy(engine.exchange)
        elif strategy_type == "moving_average":
            strategy = MovingAverageStrategy(engine.exchange)
        else:
            raise ValueError(f"Unknown strategy: {strategy_type}")

        # Setup config
        config = BacktestConfig(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.capital,
            strategy_name=strategy_type,
        )

        # Run backtest
        print("\nRunning backtest...")
        print("-" * 70)

        result = await engine.run(strategy, config)

        # Calculate results
        final_equity = (
            result.equity_curve[-1]["equity"] if result.equity_curve else self.capital
        )
        total_return = (final_equity - self.capital) / self.capital * 100

        # Print results
        print("\n" + "=" * 70)
        print("BACKTEST RESULTS")
        print("=" * 70)

        print("\n[PERFORMANCE]")
        print(f"  Initial Equity:   €{self.capital:,.2f}")
        print(f"  Final Equity:     €{final_equity:,.2f}")
        print(f"  Total Return:     {total_return:+.2f}%")
        print(f"  Sharpe Ratio:     {result.metrics.sharpe_ratio:.2f}")
        print(f"  Max Drawdown:     {result.metrics.max_drawdown*100:.2f}%")
        print(f"  CAGR:             {result.metrics.cagr*100:.2f}%")

        print("\n[TRADING]")
        print(f"  Total Trades:     {result.metrics.total_trades}")
        print(f"  Win Rate:         {result.metrics.win_rate*100:.1f}%")

        if result.trades:
            winning_trades = [t for t in result.trades if (t.pnl or 0) > 0]
            losing_trades = [t for t in result.trades if (t.pnl or 0) <= 0]

            if winning_trades:
                avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades)
                print(f"  Avg Win:          €{avg_win:,.2f}")

            if losing_trades:
                avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades)
                print(f"  Avg Loss:         €{avg_loss:,.2f}")

        # Calculate additional metrics
        if result.equity_curve:
            equity_values = [p["equity"] for p in result.equity_curve]
            peak = max(equity_values)

            print("\n[EQUITY CURVE]")
            print(f"  Peak Equity:      €{peak:,.2f}")
            print(f"  Min Equity:       €{min(equity_values):,.2f}")
            print(f"  Volatility:       {result.metrics.volatility*100:.2f}%")

        print("\n" + "=" * 70)

        return {
            "symbol": symbol,
            "strategy": strategy_type,
            "initial_capital": self.capital,
            "final_equity": final_equity,
            "total_return_pct": total_return,
            "sharpe_ratio": result.metrics.sharpe_ratio,
            "max_drawdown_pct": result.metrics.max_drawdown * 100,
            "total_trades": result.metrics.total_trades,
            "win_rate": result.metrics.win_rate * 100,
            "trades": result.trades,
            "equity_curve": result.equity_curve,
        }


async def main():
    parser = argparse.ArgumentParser(
        description="Backtest with real historical data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use existing CSV file
  python scripts/backtest_with_real_data.py --file data/historical/BTC-EUR_1h.csv
  
  # Auto-download and backtest
  python scripts/backtest_with_real_data.py --symbol BTC-EUR --timeframe 1h --days 365
  
  # Different strategy
  python scripts/backtest_with_real_data.py --file BTC-EUR.csv --strategy moving_average
        """,
    )

    parser.add_argument("--file", help="Path to CSV/Parquet file with OHLCV data")
    parser.add_argument(
        "--symbol", default="BTC-EUR", help="Symbol to download if --file not provided"
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        choices=["1d", "1h", "15m", "5m"],
        help="Timeframe for auto-download",
    )
    parser.add_argument(
        "--days", type=int, default=365, help="Days of history for auto-download"
    )
    parser.add_argument(
        "--capital", type=float, default=10000.0, help="Initial capital"
    )
    parser.add_argument(
        "--strategy",
        default="consciousness",
        choices=["consciousness", "moving_average"],
        help="Trading strategy",
    )

    args = parser.parse_args()

    # Determine data source
    if args.file:
        data_file = args.file
    else:
        # Auto-download first
        print("Downloading historical data first...")
        from scripts.download_historical_data import CryptoDataDownloader

        downloader = CryptoDataDownloader()
        df = downloader.download_cryptodatadownload(
            symbol=args.symbol, timeframe=args.timeframe
        )

        if df is None:
            print("Failed to download data. Try different symbol/timeframe.")
            return 1

        # Save temporarily
        data_file = f"data/historical/{args.symbol}_{args.timeframe}_temp.csv"
        downloader.save_data(df, args.symbol, args.timeframe, "temp")

    # Run backtest
    backtest = RealDataBacktest(data_file, capital=args.capital)

    try:
        result = await backtest.run(strategy_type=args.strategy, symbol=args.symbol)

        print("\n✓ Backtest completed successfully!")
        print(f"  Return: {result['total_return_pct']:+.2f}%")
        print(f"  Trades: {result['total_trades']}")

        return 0 if result["total_return_pct"] > -50 else 1

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nTip: Download data first with:")
        print(
            f"  python scripts/download_historical_data.py --symbol {args.symbol} --timeframe {args.timeframe}"
        )
        return 1
    except Exception as e:
        print(f"\n✗ Error during backtest: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
