#!/usr/bin/env python3
"""
Ultimate Multi-Symbol Backtest - LLM vs Non-LLM Comparison

Features:
- Multi-asset portfolio (switches between symbols)
- LLM-powered vs Rule-based comparison
- Multiple strategies (Trend, Mean-Reversion, Momentum)
- Portfolio allocation optimization

Usage:
    python scripts/ultimate_backtest.py --symbols BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR --days 365 --use-llm
    python scripts/ultimate_backtest.py --symbols BTC-EUR,ETH-EUR --days 365 --no-llm
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UltimateBacktest")

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class Trade:
    symbol: str
    action: str  # BUY, SELL
    price: float
    size: float
    timestamp: datetime
    strategy: str
    confidence: float
    pnl: float = 0.0


@dataclass
class BacktestResult:
    strategy_name: str
    use_llm: bool
    initial_capital: float
    final_equity: float
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    calmar_ratio: float
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_trade_pnl: float
    trades: List[Trade]
    equity_curve: List[Dict]
    symbol_allocation: Dict[str, float]  # Time spent in each symbol
    strategy_usage: Dict[str, int]  # Count per strategy


class MultiSymbolBacktest:
    """
    Advanced backtest engine supporting multi-asset portfolios
    with dynamic symbol rotation and strategy selection.
    """

    def __init__(
        self,
        data_dir: str = "data/historical_6year",
        initial_capital: float = 100000.0,
        use_llm: bool = False,
    ):
        self.data_dir = Path(data_dir)
        self.initial_capital = initial_capital
        self.use_llm = use_llm
        self.capital = initial_capital
        self.cash = initial_capital

        # Portfolio state
        self.positions: Dict[str, float] = {}  # symbol -> quantity
        self.position_values: Dict[str, float] = {}  # symbol -> current value
        self.current_symbol: Optional[str] = None

        # Tracking
        self.equity_curve = []
        self.trades: List[Trade] = []
        self.symbol_time: Dict[str, int] = {}  # Time steps per symbol
        self.strategy_counts: Dict[str, int] = {}

        # Performance tracking
        self.peak_equity = initial_capital
        self.max_drawdown = 0.0

        # Initialize LLM if needed
        self.llm_provider = None
        if use_llm:
            self._init_llm()

    def _init_llm(self):
        """Initialize LLM provider."""
        try:
            # Use direct DeepSeek implementation (no google-genai dependency)
            from scripts.llm_direct import SimpleLLMFactory

            self.llm_provider = SimpleLLMFactory.create_for_agent("fund_manager")
            logger.info("✓ LLM initialized (Direct DeepSeek)")
        except Exception as e:
            logger.warning(f"⚠ Could not initialize LLM: {e}")
            self.use_llm = False

    def load_all_data(
        self, symbols: List[str], timeframe: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Load data for all symbols."""
        data = {}

        for symbol in symbols:
            # Try to find data file
            clean_symbol = symbol.replace("/", "-")

            # Try to find data file
            path = None

            # Try exact match first
            for ext in [".csv", ".pkl", ".parquet"]:
                test_path = (
                    self.data_dir / f"{clean_symbol}_{timeframe}_2020-2026_binance{ext}"
                )
                if test_path.exists():
                    path = test_path
                    break

            # Try glob pattern if exact not found
            if path is None:
                import glob

                for ext in [".csv", ".pkl", ".parquet"]:
                    pattern = str(self.data_dir / f"{clean_symbol}_{timeframe}_*{ext}")
                    files = glob.glob(pattern)
                    if files:
                        path = Path(files[0])
                        break

            if path is None or not path.exists():
                logger.warning(f"⚠ Data not found for {symbol}")
                continue

            try:
                # Load based on extension
                if str(path).endswith(".csv"):
                    df = pd.read_csv(path)
                elif str(path).endswith(".pkl"):
                    df = pd.read_pickle(path)
                else:
                    df = pd.read_parquet(path)

                # Standardize
                df.columns = [c.lower().strip() for c in df.columns]
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])

                df = df.sort_values("timestamp")
                data[symbol] = df
                logger.info(f"✓ Loaded {symbol}: {len(df)} rows")

            except Exception as e:
                logger.error(f"✗ Error loading {symbol}: {e}")

        return data

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for all strategies."""
        df = df.copy()

        # Trend indicators
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["ema_12"] = df["close"].ewm(span=12).mean()
        df["ema_26"] = df["close"].ewm(span=26).mean()
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["macd_signal"] = df["macd"].ewm(span=9).mean()

        # Momentum indicators
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Volatility
        df["atr"] = self._calculate_atr(df)
        df["volatility"] = (
            df["close"].rolling(window=20).std() / df["close"].rolling(window=20).mean()
        )

        # Bollinger Bands
        df["bb_middle"] = df["close"].rolling(window=20).mean()
        bb_std = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)

        return df

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()

    def select_best_symbol(
        self,
        data: Dict[str, pd.DataFrame],
        current_idx: int,
        exclude: Optional[str] = None,
    ) -> Tuple[str, str, float]:
        """
        Select best symbol to trade based on momentum and trend strength.
        Returns: (symbol, strategy, confidence)
        """
        candidates = []

        for symbol, df in data.items():
            if symbol == exclude:
                continue
            if current_idx >= len(df):
                continue

            row = df.iloc[current_idx]

            # Skip if not enough data
            if pd.isna(row["sma_50"]):
                continue

            # Calculate trend strength
            sma_20 = row["sma_20"]
            sma_50 = row["sma_50"]
            close = row["close"]
            rsi = row["rsi"]

            # Trend score
            trend_score = 0.0
            strategy = ""

            # Strong uptrend
            if close > sma_20 > sma_50:
                trend_score = 0.7 + (close / sma_20 - 1) * 2
                strategy = "Trend Following"

            # Mean reversion (oversold in uptrend)
            elif rsi < 30 and close > sma_50:
                trend_score = 0.6
                strategy = "Mean Reversion"

            # Momentum (RSI breakout)
            elif rsi > 60 and close > sma_20:
                trend_score = 0.5
                strategy = "Momentum"

            # Weak signal
            else:
                trend_score = 0.3
                strategy = "HOLD"

            # Adjust for volatility
            volatility = row.get("volatility", 0.02)
            if volatility > 0.05:  # High volatility penalty
                trend_score *= 0.8

            candidates.append((symbol, strategy, trend_score, close))

        if not candidates:
            return list(data.keys())[0], "HOLD", 0.0

        # Select best
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[0][0], candidates[0][1], candidates[0][2]

    async def llm_select_symbol(
        self, data: Dict[str, pd.DataFrame], current_idx: int, context: str
    ) -> Tuple[str, str, float]:
        """
        Use LLM to select best symbol.
        """
        if not self.use_llm or not self.llm_provider:
            return self.select_best_symbol(data, current_idx)

        # Build context for LLM
        market_data = []
        for symbol, df in data.items():
            if current_idx < len(df):
                row = df.iloc[current_idx]
                if not pd.isna(row["sma_50"]):
                    market_data.append(
                        {
                            "symbol": symbol,
                            "price": row["close"],
                            "sma_20": row["sma_20"],
                            "sma_50": row["sma_50"],
                            "rsi": row["rsi"],
                            "volatility": row.get("volatility", 0.02),
                        }
                    )

        prompt = f"""
You are a professional crypto fund manager. Select the best symbol to trade.

Current portfolio context: {context}

Available assets:
{json.dumps(market_data, indent=2)}

Analyze each asset and select ONE to trade.
Consider: trend strength, RSI, volatility, diversification.

Respond ONLY in this format:
SYMBOL: [SYMBOL-NAME]
STRATEGY: [Trend Following / Mean Reversion / Momentum / Hold]
CONFIDENCE: [0.0-1.0]
REASON: [1 sentence analysis]
"""

        try:
            response = await self.llm_provider.generate_text(prompt)

            # Parse response
            symbol = None
            strategy = "HOLD"
            confidence = 0.0

            for line in response.split("\n"):
                if line.startswith("SYMBOL:"):
                    symbol = line.split(":")[1].strip()
                elif line.startswith("STRATEGY:"):
                    strategy = line.split(":")[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":")[1].strip())
                    except:
                        confidence = 0.5

            if symbol and symbol in data:
                logger.info(
                    f"🤖 LLM selected: {symbol} ({strategy}) conf={confidence:.2f}"
                )
                return symbol, strategy, confidence

        except Exception as e:
            logger.error(f"LLM error: {e}")

        # Fallback to rule-based
        return self.select_best_symbol(data, current_idx)

    def calculate_position_size(
        self, symbol: str, strategy: str, confidence: float, volatility: float
    ) -> float:
        """Calculate position size based on strategy and risk."""

        # Base sizing on confidence
        base_size = confidence * 0.3  # Max 30% per position

        # Strategy adjustments
        if strategy == "Trend Following":
            multiplier = 1.0
        elif strategy == "Mean Reversion":
            multiplier = 0.8
        elif strategy == "Momentum":
            multiplier = 0.6
        else:
            multiplier = 0.3

        # Volatility adjustment
        vol_adjustment = max(0.3, 1 - (volatility * 5))

        # Final size
        size = base_size * multiplier * vol_adjustment

        return min(size, 0.25)  # Cap at 25%

    async def run_backtest(
        self, symbols: List[str], days: int = 365, timeframe: str = "1d"
    ) -> BacktestResult:
        """Run the complete multi-symbol backtest."""

        logger.info("=" * 70)
        logger.info(
            f"ULTIMATE MULTI-SYMBOL BACKTEST - {'LLM' if self.use_llm else 'RULE-BASED'}"
        )
        logger.info("=" * 70)
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Initial Capital: €{self.initial_capital:,.2f}")
        logger.info(f"Timeframe: {timeframe}")
        logger.info("=" * 70)

        # Load and prepare data
        logger.info("\n[1/5] Loading data...")
        data = self.load_all_data(symbols, timeframe)

        if not data:
            raise ValueError("No data loaded!")

        # Calculate indicators
        logger.info("[2/5] Calculating indicators...")
        for symbol in data:
            data[symbol] = self.calculate_indicators(data[symbol])

        # Align timestamps (use intersection)
        logger.info("[3/5] Aligning timestamps...")
        timestamps = None
        for df in data.values():
            if timestamps is None:
                timestamps = set(df["timestamp"])
            else:
                timestamps &= set(df["timestamp"])

        timestamps = sorted(list(timestamps))
        logger.info(f"Common timestamps: {len(timestamps)}")

        # Run simulation
        logger.info("[4/5] Running simulation...")

        for i, timestamp in enumerate(timestamps):
            # Progress
            if i % max(1, len(timestamps) // 10) == 0:
                progress = i / len(timestamps) * 100
                logger.info(
                    f"  {progress:.1f}% | Equity: €{self.cash + sum(self.position_values.values()):,.2f}"
                )

            # Get current prices for all symbols
            current_prices = {}
            for symbol, df in data.items():
                row = df[df["timestamp"] == timestamp]
                if not row.empty:
                    current_prices[symbol] = row["close"].values[0]

            # Update position values
            self.position_values = {
                sym: qty * current_prices.get(sym, 0)
                for sym, qty in self.positions.items()
            }

            # Calculate total equity
            total_equity = self.cash + sum(self.position_values.values())

            # Update peak and drawdown
            if total_equity > self.peak_equity:
                self.peak_equity = total_equity
            drawdown = (self.peak_equity - total_equity) / self.peak_equity
            self.max_drawdown = max(self.max_drawdown, drawdown)

            # Record equity
            self.equity_curve.append(
                {
                    "timestamp": timestamp,
                    "equity": total_equity,
                    "cash": self.cash,
                    "positions": self.position_values.copy(),
                    "current_symbol": self.current_symbol,
                }
            )

            # Skip initial warm-up period
            if i < 50:
                continue

            # Get current data index for each symbol
            data_idx = {}
            for symbol, df in data.items():
                idx = df[df["timestamp"] == timestamp].index
                if len(idx) > 0:
                    data_idx[symbol] = idx[0]

            if not data_idx:
                continue

            # Check if we should switch symbols or trade
            min_idx = min(data_idx.values())

            # Get current position info
            has_position = (
                self.current_symbol is not None
                and self.current_symbol in self.positions
            )

            if has_position:
                # Check exit conditions
                sym = self.current_symbol
                df = data[sym]
                row = df[df["timestamp"] == timestamp].iloc[0]

                # Exit logic
                should_exit = False
                exit_reason = ""

                # Stop loss (2x ATR)
                if row["close"] < row["sma_20"] - (2 * row["atr"]):
                    should_exit = True
                    exit_reason = "Stop Loss"

                # Take profit (RSI overbought)
                elif row["rsi"] > 75:
                    should_exit = True
                    exit_reason = "Take Profit"

                # Better opportunity exists
                else:
                    best_sym, best_strat, best_conf = await self.llm_select_symbol(
                        data, min_idx, f"Current: {sym}, looking for better opportunity"
                    )

                    if best_sym != sym and best_conf > 0.7:
                        should_exit = True
                        exit_reason = f"Switch to {best_sym}"

                if should_exit:
                    # Sell current position
                    qty = self.positions[sym]
                    price = row["close"]
                    sell_value = qty * price

                    # Calculate P&L
                    buy_trade = next(
                        (
                            t
                            for t in reversed(self.trades)
                            if t.symbol == sym and t.action == "BUY"
                        ),
                        None,
                    )
                    pnl = sell_value - (buy_trade.price * qty) if buy_trade else 0

                    self.cash += sell_value
                    del self.positions[sym]

                    self.trades.append(
                        Trade(
                            symbol=sym,
                            action="SELL",
                            price=price,
                            size=qty,
                            timestamp=timestamp,
                            strategy=exit_reason,
                            confidence=1.0,
                            pnl=pnl,
                        )
                    )

                    self.current_symbol = None
                    logger.info(
                        f"📤 SOLD {sym} @ €{price:,.2f} ({exit_reason}, P&L: €{pnl:,.2f})"
                    )

            # Look for new entry if no position
            if not self.positions:
                best_sym, strategy, confidence = await self.llm_select_symbol(
                    data, min_idx, "Looking for new entry"
                )

                if confidence > 0.5 and strategy != "HOLD":
                    df = data[best_sym]
                    row = df[df["timestamp"] == timestamp].iloc[0]

                    # Calculate position size
                    size = self.calculate_position_size(
                        best_sym, strategy, confidence, row.get("volatility", 0.02)
                    )

                    position_value = total_equity * size
                    qty = position_value / row["close"]

                    if qty > 0 and position_value > 100:  # Min trade size
                        self.positions[best_sym] = qty
                        self.cash -= position_value
                        self.current_symbol = best_sym

                        self.trades.append(
                            Trade(
                                symbol=best_sym,
                                action="BUY",
                                price=row["close"],
                                size=qty,
                                timestamp=timestamp,
                                strategy=strategy,
                                confidence=confidence,
                            )
                        )

                        # Track
                        self.symbol_time[best_sym] = (
                            self.symbol_time.get(best_sym, 0) + 1
                        )
                        self.strategy_counts[strategy] = (
                            self.strategy_counts.get(strategy, 0) + 1
                        )

                        logger.info(
                            f"📥 BOUGHT {best_sym} @ €{row['close']:,.2f} ({strategy}, conf={confidence:.2f}, size={size:.1%})"
                        )

        # Close all positions at end
        logger.info("[5/5] Closing final positions...")
        if self.positions:
            for sym, qty in list(self.positions.items()):
                if sym in data and sym in current_prices:
                    sell_value = qty * current_prices[sym]
                    self.cash += sell_value

                    buy_trade = next(
                        (
                            t
                            for t in reversed(self.trades)
                            if t.symbol == sym and t.action == "BUY"
                        ),
                        None,
                    )
                    if buy_trade:
                        pnl = sell_value - (buy_trade.price * qty)
                        buy_trade.pnl = pnl

                    del self.positions[sym]

        # Calculate metrics
        logger.info("Calculating final metrics...")
        return self._calculate_metrics()

    def _calculate_metrics(self) -> BacktestResult:
        """Calculate comprehensive backtest metrics."""

        final_equity = self.cash + sum(self.position_values.values())
        total_return = (
            (final_equity - self.initial_capital) / self.initial_capital * 100
        )

        # Time-based metrics
        if len(self.equity_curve) > 1:
            start_date = self.equity_curve[0]["timestamp"]
            end_date = self.equity_curve[-1]["timestamp"]
            years = (end_date - start_date).days / 365.25
            cagr = (
                ((final_equity / self.initial_capital) ** (1 / years) - 1) * 100
                if years > 0
                else 0
            )
        else:
            cagr = 0

        # Trade analysis
        closed_trades = [t for t in self.trades if t.action == "SELL"]
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl <= 0]

        total_trades = len(closed_trades)
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0

        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0.001
        profit_factor = gross_profit / gross_loss

        avg_trade_pnl = (
            sum(t.pnl for t in closed_trades) / total_trades if total_trades > 0 else 0
        )

        # Sharpe ratio
        if len(self.equity_curve) > 1:
            equity_values = [e["equity"] for e in self.equity_curve]
            returns = pd.Series(equity_values).pct_change().dropna()
            sharpe = (
                np.sqrt(252) * returns.mean() / returns.std()
                if returns.std() > 0
                else 0
            )
        else:
            sharpe = 0

        # Calmar ratio
        calmar = cagr / (self.max_drawdown * 100) if self.max_drawdown > 0 else 0

        # Symbol allocation
        total_time = sum(self.symbol_time.values())
        symbol_allocation = {
            sym: (count / total_time * 100) if total_time > 0 else 0
            for sym, count in self.symbol_time.items()
        }

        return BacktestResult(
            strategy_name="Multi-Symbol Rotation",
            use_llm=self.use_llm,
            initial_capital=self.initial_capital,
            final_equity=final_equity,
            total_return_pct=total_return,
            cagr_pct=cagr,
            max_drawdown_pct=self.max_drawdown * 100,
            sharpe_ratio=sharpe,
            calmar_ratio=calmar,
            total_trades=total_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_pnl=avg_trade_pnl,
            trades=self.trades,
            equity_curve=self.equity_curve,
            symbol_allocation=symbol_allocation,
            strategy_usage=self.strategy_counts,
        )


def print_comparison(results_llm: BacktestResult, results_rule: BacktestResult):
    """Print side-by-side comparison."""
    print("\n" + "=" * 80)
    print("LLM vs RULE-BASED COMPARISON")
    print("=" * 80)

    print(f"\n{'Metric':<25} {'LLM-Powered':>20} {'Rule-Based':>20} {'Winner':>10}")
    print("-" * 80)

    metrics = [
        ("Final Equity", "€{:,.2f}", "final_equity", True),
        ("Total Return", "{:+.2f}%", "total_return_pct", True),
        ("CAGR", "{:+.2f}%", "cagr_pct", True),
        ("Max Drawdown", "{:.2f}%", "max_drawdown_pct", False),  # Lower is better
        ("Sharpe Ratio", "{:.2f}", "sharpe_ratio", True),
        ("Calmar Ratio", "{:.2f}", "calmar_ratio", True),
        ("Total Trades", "{:.0f}", "total_trades", None),
        ("Win Rate", "{:.1f}%", "win_rate", True),
        ("Profit Factor", "{:.2f}", "profit_factor", True),
        ("Avg Trade P&L", "€{:,.2f}", "avg_trade_pnl", True),
    ]

    for name, fmt, attr, higher_is_better in metrics:
        llm_val = getattr(results_llm, attr)
        rule_val = getattr(results_rule, attr)

        if higher_is_better is None:
            winner = "-"
        elif higher_is_better:
            winner = "🤖 LLM" if llm_val > rule_val else "📊 Rule"
        else:
            winner = "🤖 LLM" if llm_val < rule_val else "📊 Rule"

        print(
            f"{name:<25} {fmt.format(llm_val):>20} {fmt.format(rule_val):>20} {winner:>10}"
        )

    print("\n[SYMBOL ALLOCATION - LLM]")
    for sym, pct in sorted(
        results_llm.symbol_allocation.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {sym}: {pct:.1f}%")

    print("\n[SYMBOL ALLOCATION - Rule-Based]")
    for sym, pct in sorted(
        results_rule.symbol_allocation.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {sym}: {pct:.1f}%")

    print("\n[STRATEGY USAGE - LLM]")
    for strat, count in sorted(
        results_llm.strategy_usage.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {strat}: {count} trades")

    print("\n[STRATEGY USAGE - Rule-Based]")
    for strat, count in sorted(
        results_rule.strategy_usage.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {strat}: {count} trades")

    print("\n" + "=" * 80)


async def main():
    parser = argparse.ArgumentParser(
        description="Ultimate Multi-Symbol Backtest Comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # LLM-powered backtest with multiple symbols
  python scripts/ultimate_backtest.py --symbols BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR --use-llm

  # Rule-based comparison
  python scripts/ultimate_backtest.py --symbols BTC-EUR,ETH-EUR --no-llm

  # Full comparison (both LLM and Rule-based)
  python scripts/ultimate_backtest.py --symbols BTC-EUR,ETH-EUR,SOL-EUR --compare
        """,
    )

    parser.add_argument(
        "--symbols", default="BTC-EUR,ETH-EUR", help="Comma-separated symbols"
    )
    parser.add_argument("--days", type=int, default=365, help="Backtest period (days)")
    parser.add_argument(
        "--timeframe", default="1d", choices=["1d", "1h"], help="Timeframe"
    )
    parser.add_argument(
        "--capital", type=float, default=100000.0, help="Initial capital"
    )
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for decisions")
    parser.add_argument("--no-llm", action="store_true", help="Force rule-based")
    parser.add_argument("--compare", action="store_true", help="Run both and compare")
    parser.add_argument(
        "--data-dir", default="data/historical_6year", help="Data directory"
    )

    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",")]

    print("!" * 80)
    print("ULTIMATE MULTI-SYMBOL BACKTEST")
    print("!" * 80)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Capital: €{args.capital:,.2f}")
    print(f"Period: {args.days} days")
    print("!" * 80)

    results = {}

    # Run LLM version
    if args.use_llm or args.compare:
        print("\n" + "=" * 80)
        print("RUNNING LLM-POWERED BACKTEST")
        print("=" * 80)

        backtest_llm = MultiSymbolBacktest(
            data_dir=args.data_dir, initial_capital=args.capital, use_llm=True
        )

        results["llm"] = await backtest_llm.run_backtest(
            symbols, args.days, args.timeframe
        )

    # Run Rule-based version
    if args.no_llm or args.compare:
        print("\n" + "=" * 80)
        print("RUNNING RULE-BASED BACKTEST")
        print("=" * 80)

        backtest_rule = MultiSymbolBacktest(
            data_dir=args.data_dir, initial_capital=args.capital, use_llm=False
        )

        results["rule"] = await backtest_rule.run_backtest(
            symbols, args.days, args.timeframe
        )

    # Compare if both ran
    if "llm" in results and "rule" in results:
        print_comparison(results["llm"], results["rule"])

    # Save results
    output_dir = Path("data/backtest_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for name, result in results.items():
        result_file = output_dir / f"ultimate_backtest_{name}_{timestamp}.json"
        with open(result_file, "w") as f:
            json.dump(
                {
                    "strategy_name": result.strategy_name,
                    "use_llm": result.use_llm,
                    "initial_capital": result.initial_capital,
                    "final_equity": result.final_equity,
                    "total_return_pct": result.total_return_pct,
                    "cagr_pct": result.cagr_pct,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "sharpe_ratio": result.sharpe_ratio,
                    "calmar_ratio": result.calmar_ratio,
                    "total_trades": result.total_trades,
                    "win_rate": result.win_rate,
                    "profit_factor": result.profit_factor,
                    "avg_trade_pnl": result.avg_trade_pnl,
                    "symbol_allocation": result.symbol_allocation,
                    "strategy_usage": result.strategy_usage,
                },
                f,
                indent=2,
                default=str,
            )

        logger.info(f"✓ Saved results: {result_file}")

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
