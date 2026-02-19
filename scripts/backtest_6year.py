#!/usr/bin/env python3
"""
6-Year Backtest Engine

Run comprehensive backtests with 6 years of historical data (2020-2026).
Optimized for large datasets using chunked processing.

Usage:
    python scripts/backtest_6year.py --symbol BTC-EUR
    python scripts/backtest_6year.py --file data/historical_6year/BTC-EUR_1h_2020-2026_binance.parquet
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))


class LargeScaleBacktest:
    """
    Backtest engine optimized for large 6-year datasets.
    Uses chunked processing to handle 50k+ candles efficiently.
    """

    def __init__(self, data_path: str, capital: float = 100000.0):
        self.data_path = Path(data_path)
        self.initial_capital = capital
        self.capital = capital
        self.equity_curve = []
        self.trades = []

    def load_data_chunked(self, chunk_size: int = 10000) -> pd.DataFrame:
        """Load large dataset in chunks to manage memory."""
        logger.info(f"Loading data from: {self.data_path}")

        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        # Determine format
        suffix = self.data_path.suffix.lower()

        if suffix == ".parquet":
            # Parquet is already optimized, load directly
            df = pd.read_parquet(self.data_path)
        elif suffix == ".pkl" or suffix == ".pickle":
            df = pd.read_pickle(self.data_path)
        elif suffix == ".csv":
            # Load CSV in chunks if very large
            file_size = self.data_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # > 100MB
                logger.info("Large CSV detected, using chunked loading...")
                chunks = []
                for chunk in pd.read_csv(self.data_path, chunksize=chunk_size):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_csv(self.data_path)
        else:
            raise ValueError(f"Unsupported format: {suffix}")

        # Standardize
        df.columns = [c.lower().strip() for c in df.columns]

        # Ensure timestamp
        if "timestamp" not in df.columns and "date" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"])
        elif "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Sort
        df = df.sort_values("timestamp").reset_index(drop=True)

        logger.info(f"✓ Loaded {len(df):,} rows")
        logger.info(f"  Period: {df['timestamp'].min()} to {df['timestamp'].max()}")
        logger.info(f"  Columns: {list(df.columns)}")

        return df

    def run_consciousness_backtest(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Run consciousness-based backtest on large dataset.
        Simplified but effective for 6-year backtests.
        """
        logger.info("\n" + "=" * 70)
        logger.info("Running 6-Year Consciousness Backtest")
        logger.info("=" * 70)

        # Initialize state
        capital = self.initial_capital
        position = 0.0  # Current position size
        position_value = 0.0
        entry_price = 0.0

        # Tracking
        equity_curve = []
        trades = []
        signals = 0

        # Consciousness parameters
        sma_short_window = 20
        sma_long_window = 50
        rsi_window = 14

        # Process each candle
        total = len(df)
        log_interval = max(1, total // 20)

        logger.info(f"Processing {total:,} candles...")

        for i, row in df.iterrows():
            price = row["close"]
            timestamp = row["timestamp"]

            # Get price history up to this point
            if i < sma_long_window:
                equity_curve.append({"timestamp": timestamp, "equity": capital})
                continue

            prices = df["close"].iloc[: i + 1].values

            # Calculate indicators
            sma_short = np.mean(prices[-sma_short_window:])
            sma_long = np.mean(prices[-sma_long_window:])

            # RSI calculation
            deltas = np.diff(prices[-rsi_window - 1 :])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 0.001
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # Volatility (ATR-like)
            recent_prices = prices[-20:]
            volatility = np.std(recent_prices) / np.mean(recent_prices)

            # Signal generation
            signal = None
            confidence = 0.0

            # Trend following logic
            if sma_short > sma_long * 1.01 and position == 0:
                # Bullish crossover, no position
                if rsi < 70:  # Not overbought
                    signal = "BUY"
                    confidence = min(0.9, 0.5 + (sma_short / sma_long - 1) * 10)

            elif sma_short < sma_long * 0.99 and position > 0:
                # Bearish crossover, have position
                if rsi > 30:  # Not oversold
                    signal = "SELL"
                    confidence = min(0.9, 0.5 + (1 - sma_short / sma_long) * 10)

            # Mean reversion (counter-trend) in sideways markets
            elif abs(sma_short - sma_long) / sma_long < 0.02:  # Sideways
                if rsi < 30 and position == 0:
                    signal = "BUY"
                    confidence = 0.6
                elif rsi > 70 and position > 0:
                    signal = "SELL"
                    confidence = 0.6

            # Risk management
            if signal and confidence > 0.5:
                signals += 1

                # Position sizing (Kelly-inspired)
                kelly_fraction = confidence * 0.5  # Conservative Kelly

                # Reduce size in high volatility
                if volatility > 0.05:  # >5% daily vol
                    kelly_fraction *= 0.5

                # Max position: 25% of capital
                position_size = min(kelly_fraction, 0.25)

                if signal == "BUY" and position == 0:
                    # Open long position
                    position_value = capital * position_size
                    position = position_value / price
                    entry_price = price

                    trades.append(
                        {
                            "timestamp": timestamp,
                            "action": "BUY",
                            "price": price,
                            "size": position,
                            "value": position_value,
                            "confidence": confidence,
                        }
                    )

                elif signal == "SELL" and position > 0:
                    # Close position
                    sell_value = position * price
                    pnl = sell_value - position_value
                    pnl_pct = (price - entry_price) / entry_price * 100

                    capital += pnl

                    trades.append(
                        {
                            "timestamp": timestamp,
                            "action": "SELL",
                            "price": price,
                            "size": position,
                            "value": sell_value,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "confidence": confidence,
                        }
                    )

                    position = 0
                    position_value = 0

            # Calculate equity
            current_equity = capital
            if position > 0:
                unrealized = position * price - position_value
                current_equity += unrealized

            equity_curve.append(
                {
                    "timestamp": timestamp,
                    "equity": current_equity,
                    "price": price,
                    "position": position,
                }
            )

            # Progress log
            if i % log_interval == 0:
                progress = i / total * 100
                logger.info(
                    f"  {progress:.1f}% | Equity: €{current_equity:,.2f} | Trades: {len([t for t in trades if t.get('pnl') is not None])}"
                )

        # Close any open position at end
        if position > 0:
            final_price = df["close"].iloc[-1]
            sell_value = position * final_price
            pnl = sell_value - position_value
            capital += pnl

            trades.append(
                {
                    "timestamp": df["timestamp"].iloc[-1],
                    "action": "SELL (Final)",
                    "price": final_price,
                    "size": position,
                    "value": sell_value,
                    "pnl": pnl,
                    "pnl_pct": (final_price - entry_price) / entry_price * 100,
                }
            )

        # Calculate metrics
        return self._calculate_metrics(equity_curve, trades, capital)

    def _calculate_metrics(
        self, equity_curve: List[Dict], trades: List[Dict], final_capital: float
    ) -> Dict:
        """Calculate comprehensive backtest metrics."""

        equity_df = pd.DataFrame(equity_curve)

        # Basic returns
        total_return = (final_capital - self.initial_capital) / self.initial_capital

        # Calculate drawdowns
        equity_df["peak"] = equity_df["equity"].cummax()
        equity_df["drawdown"] = (equity_df["equity"] - equity_df["peak"]) / equity_df[
            "peak"
        ]
        max_drawdown = equity_df["drawdown"].min()

        # Trade analysis
        closed_trades = [t for t in trades if "pnl" in t]
        winning_trades = [t for t in closed_trades if t["pnl"] > 0]
        losing_trades = [t for t in closed_trades if t["pnl"] <= 0]

        total_trades = len(closed_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0

        # Profit factor
        gross_profit = sum(t["pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl"] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Sharpe ratio (simplified)
        returns = equity_df["equity"].pct_change().dropna()
        sharpe = (
            np.sqrt(252) * returns.mean() / returns.std()
            if len(returns) > 1 and returns.std() > 0
            else 0
        )

        # CAGR
        years = (
            equity_df["timestamp"].max() - equity_df["timestamp"].min()
        ).days / 365.25
        cagr = (
            (final_capital / self.initial_capital) ** (1 / years) - 1
            if years > 0
            else 0
        )

        return {
            "initial_capital": self.initial_capital,
            "final_capital": final_capital,
            "total_return": total_return * 100,
            "cagr": cagr * 100,
            "max_drawdown": max_drawdown * 100,
            "sharpe_ratio": sharpe,
            "profit_factor": profit_factor,
            "total_trades": total_trades,
            "win_rate": win_rate * 100,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "equity_curve": equity_curve,
            "trades": trades,
        }

    def save_results(self, results: Dict, symbol: str):
        """Save backtest results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{symbol.replace('/', '-')}_6year_backtest_{timestamp}"

        output_dir = Path("data/backtest_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save equity curve
        equity_df = pd.DataFrame(results["equity_curve"])
        equity_path = output_dir / f"{base_name}_equity.csv"
        equity_df.to_csv(equity_path, index=False)
        logger.info(f"✓ Saved equity curve: {equity_path}")

        # Save trades
        trades_df = pd.DataFrame(results["trades"])
        trades_path = output_dir / f"{base_name}_trades.csv"
        trades_df.to_csv(trades_path, index=False)
        logger.info(f"✓ Saved trades: {trades_path}")

        # Save summary JSON
        summary = {
            k: v for k, v in results.items() if k not in ["equity_curve", "trades"]
        }
        summary_path = output_dir / f"{base_name}_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        logger.info(f"✓ Saved summary: {summary_path}")

    def print_results(self, results: Dict, symbol: str):
        """Print formatted results."""
        print("\n" + "=" * 70)
        print("6-YEAR BACKTEST RESULTS")
        print("=" * 70)

        print("\n[CONFIGURATION]")
        print(f"  Symbol:           {symbol}")
        print(f"  Initial Capital:  €{results['initial_capital']:,.2f}")
        print(f"  Final Capital:    €{results['final_capital']:,.2f}")

        print("\n[PERFORMANCE]")
        print(f"  Total Return:     {results['total_return']:+.2f}%")
        print(f"  CAGR:             {results['cagr']:+.2f}%")
        print(f"  Max Drawdown:     {results['max_drawdown']:.2f}%")
        print(f"  Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
        print(f"  Profit Factor:    {results['profit_factor']:.2f}")

        print("\n[TRADING STATISTICS]")
        print(f"  Total Trades:     {results['total_trades']}")
        print(f"  Win Rate:         {results['win_rate']:.1f}%")
        print(f"  Winning Trades:   {results['winning_trades']}")
        print(f"  Losing Trades:    {results['losing_trades']}")
        if results["winning_trades"] > 0:
            print(f"  Avg Win:          €{results['avg_win']:,.2f}")
        if results["losing_trades"] > 0:
            print(f"  Avg Loss:         €{results['avg_loss']:,.2f}")

        print("\n" + "=" * 70)


async def main():
    parser = argparse.ArgumentParser(
        description="Run 6-year backtest with historical data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-download and backtest
  python scripts/backtest_6year.py --symbol BTC-EUR
  
  # Use existing data file
  python scripts/backtest_6year.py --file data/historical_6year/BTC-EUR_1h_2020-2026.parquet
  
  # Different capital
  python scripts/backtest_6year.py --symbol ETH-EUR --capital 50000
        """,
    )

    parser.add_argument("--symbol", default="BTC-EUR", help="Symbol to backtest")
    parser.add_argument("--file", help="Path to existing data file")
    parser.add_argument(
        "--capital", type=float, default=100000.0, help="Initial capital"
    )
    parser.add_argument(
        "--timeframe", default="1h", choices=["1h", "1d"], help="Timeframe"
    )

    args = parser.parse_args()

    # Determine data source
    if args.file:
        data_file = args.file
    else:
        # Check if file exists
        expected_path = (
            f"data/historical_6year/{args.symbol}_{args.timeframe}_2020-2026"
        )

        # Try different extensions
        for ext in [".parquet", ".feather", ".csv"]:
            path = Path(expected_path + ext)
            if path.exists():
                data_file = str(path)
                break
        else:
            # Need to download first
            print(f"\nData file not found for {args.symbol}")
            print("Downloading 6-year data first...")

            from scripts.download_6year_data import SixYearDataDownloader

            downloader = SixYearDataDownloader()
            success = await downloader.download_symbol(args.symbol, args.timeframe)

            if not success:
                print("✗ Failed to download data")
                return 1

            # Find downloaded file
            data_dir = Path("data/historical_6year")
            files = list(data_dir.glob(f"{args.symbol}_{args.timeframe}_*.parquet"))
            if not files:
                files = list(data_dir.glob(f"{args.symbol}_{args.timeframe}_*.feather"))

            if files:
                data_file = str(files[0])
            else:
                print("✗ Could not find downloaded file")
                return 1

    # Run backtest
    print(f"\nLoading data from: {data_file}")
    backtest = LargeScaleBacktest(data_file, capital=args.capital)

    try:
        # Load and run
        df = backtest.load_data_chunked()
        results = backtest.run_consciousness_backtest(df, args.symbol)

        # Print and save
        backtest.print_results(results, args.symbol)
        backtest.save_results(results, args.symbol)

        print("\n✓ Backtest completed!")
        return 0 if results["total_return"] > -50 else 1

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
