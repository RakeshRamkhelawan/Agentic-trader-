#!/usr/bin/env python3
"""
FEDERATED TRIAD BACKTEST ENGINE
Backtest het nieuwe systeem op 6 jaar historische data (2020-2026)
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
# Import Federated Triad
from trika_federated_system import (FederatedTriadSystem)

# Try to import old system for comparison
try:
    from trika_pure_system import TrikaSystem as OldTrikaSystem

    OLD_SYSTEM_AVAILABLE = True
except ImportError:
    OLD_SYSTEM_AVAILABLE = False


@dataclass
class BacktestConfig:
    """Configuration for backtest"""

    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    symbols: List[str] = field(default_factory=lambda: ["BTC-EUR"])
    timeframe: str = "1h"  # 1h, 1d
    initial_capital: float = 10000.0
    position_size: float = 0.1  # 10% of capital per trade
    max_positions: int = 1
    enable_federated: bool = True
    enable_legacy: bool = False  # Compare with old system
    save_results: bool = True
    verbose: bool = True


@dataclass
class Trade:
    """Record of a single trade"""

    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    size: float
    action: str  # buy/sell
    pnl: Optional[float]
    pnl_pct: Optional[float]
    exit_reason: Optional[str]


@dataclass
class BacktestResult:
    """Complete backtest results"""

    config: BacktestConfig
    start_time: datetime
    end_time: datetime
    trades: List[Trade]
    equity_curve: List[Dict]

    # Performance metrics
    total_return: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    num_trades: int = 0
    num_wins: int = 0
    num_losses: int = 0
    avg_trade: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0

    def calculate_metrics(self):
        """Calculate all performance metrics"""
        if not self.trades:
            return

        closed_trades = [t for t in self.trades if t.pnl is not None]
        if not closed_trades:
            return

        self.num_trades = len(closed_trades)
        wins = [t for t in closed_trades if t.pnl > 0]
        losses = [t for t in closed_trades if t.pnl <= 0]

        self.num_wins = len(wins)
        self.num_losses = len(losses)
        self.win_rate = self.num_wins / self.num_trades if self.num_trades > 0 else 0

        total_pnl = sum(t.pnl for t in closed_trades)
        total_wins = sum(t.pnl for t in wins)
        total_losses = abs(sum(t.pnl for t in losses))

        self.profit_factor = (
            total_wins / total_losses if total_losses > 0 else float("inf")
        )
        self.avg_trade = total_pnl / self.num_trades
        self.avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
        self.avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0

        # Calculate from equity curve
        if self.equity_curve:
            equity_values = [e["equity"] for e in self.equity_curve]
            self.total_return = equity_values[-1] - equity_values[0]
            self.total_return_pct = (self.total_return / equity_values[0]) * 100

            # Max drawdown
            peak = equity_values[0]
            max_dd = 0
            for eq in equity_values:
                if eq > peak:
                    peak = eq
                dd = peak - eq
                if dd > max_dd:
                    max_dd = dd
            self.max_drawdown = max_dd
            self.max_drawdown_pct = (max_dd / peak) * 100 if peak > 0 else 0

            # Sharpe ratio (simplified)
            returns = []
            for i in range(1, len(equity_values)):
                ret = (equity_values[i] - equity_values[i - 1]) / equity_values[i - 1]
                returns.append(ret)

            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                self.sharpe_ratio = (
                    (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
                )


class FederatedBacktestEngine:
    """
    Backtest engine for Federated Triad system.

    Features:
    - Multi-symbol backtesting
    - Performance metrics calculation
    - Comparison with legacy system
    - Detailed trade logging
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.federated_system = None
        self.legacy_system = None
        self.data = {}
        self.results = {}

    def load_data(self) -> bool:
        """Load historical data from data directory"""
        data_dir = Path(__file__).parent.parent / "data" / "historical"

        if not data_dir.exists():
            print(f"[ERROR] Data directory not found: {data_dir}")
            return False

        for symbol in self.config.symbols:
            # Convert symbol format (BTC-EUR -> BTC_USDT)
            symbol_file = symbol.replace("-", "_").replace("EUR", "USDT")

            # Try different file formats
            file_patterns = [
                f"binance/{symbol_file}_{self.config.timeframe}.csv",
                f"{symbol_file}_{self.config.timeframe}.csv",
                f"{symbol}_{self.config.timeframe}.csv",
                f"{symbol.replace('-', '_')}_{self.config.timeframe}.csv",
            ]

            file_path = None
            for pattern in file_patterns:
                potential_path = data_dir / pattern
                if potential_path.exists():
                    file_path = potential_path
                    break
                # Also search recursively
                matches = list(data_dir.rglob(pattern))
                if matches:
                    file_path = matches[0]
                    break

            if not file_path:
                print(f"[WARNING] No data file found for {symbol}")
                continue

            try:
                df = pd.read_csv(file_path)

                # Parse dates - handle both millisecond timestamps and ISO strings
                if "timestamp" in df.columns:
                    # Check if timestamp is in milliseconds (large number)
                    if df["timestamp"].iloc[0] > 1e10:
                        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    else:
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                elif "date" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["date"])
                elif "datetime" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["datetime"])

                # Filter by date range
                if self.config.start_date:
                    start_dt = pd.to_datetime(self.config.start_date)
                    df = df[df["timestamp"] >= start_dt]
                if self.config.end_date:
                    end_dt = pd.to_datetime(self.config.end_date)
                    df = df[df["timestamp"] <= end_dt]

                df = df.sort_values("timestamp")
                self.data[symbol] = df

                if self.config.verbose:
                    print(f"[OK] Loaded {len(df)} rows for {symbol}")
                    if len(df) > 0:
                        print(
                            f"     Date range: {df['timestamp'].min()} to {df['timestamp'].max()}"
                        )

            except Exception as e:
                print(f"[ERROR] Failed to load {file_path}: {e}")
                return False

        return len(self.data) > 0

    def prepare_systems(self):
        """Initialize trading systems"""
        if self.config.enable_federated:
            self.federated_system = FederatedTriadSystem(
                enable_caching=True, deliberation_iterations=3, chitta_max_nodes=10000
            )
            if self.config.verbose:
                print("[OK] Federated Triad System initialized")

        if self.config.enable_legacy and OLD_SYSTEM_AVAILABLE:
            self.legacy_system = OldTrikaSystem()
            if self.config.verbose:
                print("[OK] Legacy Trika System initialized")

    async def run_backtest(self) -> Dict[str, BacktestResult]:
        """Run backtest on all symbols"""
        if not self.data:
            print("[ERROR] No data loaded")
            return {}

        self.prepare_systems()

        for symbol, df in self.data.items():
            if self.config.verbose:
                print(f"\n{'='*70}")
                print(f"BACKTESTING: {symbol}")
                print(f"{'='*70}")

            # Run with federated system
            if self.config.enable_federated:
                result = await self._run_symbol_backtest(symbol, df, use_federated=True)
                self.results[f"{symbol}_federated"] = result

            # Run with legacy system for comparison
            if self.config.enable_legacy and OLD_SYSTEM_AVAILABLE:
                result = await self._run_symbol_backtest(
                    symbol, df, use_federated=False
                )
                self.results[f"{symbol}_legacy"] = result

        return self.results

    async def _run_symbol_backtest(
        self, symbol: str, df: pd.DataFrame, use_federated: bool = True
    ) -> BacktestResult:
        """Run backtest for a single symbol"""
        system_name = "Federated" if use_federated else "Legacy"
        system = self.federated_system if use_federated else self.legacy_system

        config = BacktestConfig(**self.config.__dict__)
        result = BacktestResult(
            config=config,
            start_time=datetime.now(),
            end_time=datetime.now(),
            trades=[],
            equity_curve=[],
        )

        # Initialize portfolio
        cash = config.initial_capital
        holdings = 0.0
        position = None  # None, 'long', 'short'

        # Track equity
        result.equity_curve.append(
            {
                "timestamp": df.iloc[0]["timestamp"],
                "equity": cash,
                "cash": cash,
                "holdings": 0,
                "price": df.iloc[0]["close"],
            }
        )

        # Iterate through data (use iloc indexing)
        for i in range(len(df)):
            row = df.iloc[i]
            price = row["close"]
            timestamp = row["timestamp"]

            # Calculate market data features
            market_data = self._calculate_market_features(df, i)

            # Get decision from system
            try:
                if use_federated:
                    cycle_result = await system.process_cycle(market_data)
                    action = cycle_result.get("decision", {}).get("action", "hold")
                    confidence = cycle_result.get("decision", {}).get("confidence", 0.5)
                else:
                    # Legacy system API may differ
                    cycle_result = await system.cycle(market_data)
                    action = cycle_result.get("action", "hold")
                    confidence = cycle_result.get("confidence", 0.5)

                # Execute trade
                if action == "buy" and position != "long":
                    # Close any existing position
                    if position == "short":
                        cash += holdings * price  # Cover short
                        holdings = 0

                    # Open long position
                    position_size = cash * config.position_size
                    shares = position_size / price
                    cash -= position_size
                    holdings += shares
                    position = "long"

                    # Record trade
                    trade = Trade(
                        entry_time=timestamp,
                        exit_time=None,
                        symbol=symbol,
                        entry_price=price,
                        exit_price=None,
                        size=shares,
                        action="buy",
                        pnl=None,
                        pnl_pct=None,
                        exit_reason=None,
                    )
                    result.trades.append(trade)

                    if config.verbose:
                        print(f"  BUY  @ ${price:,.2f} (confidence: {confidence:.0%})")

                elif action == "sell" and position == "long":
                    # Close long position
                    position_value = holdings * price
                    pnl = position_value - (holdings * result.trades[-1].entry_price)
                    pnl_pct = pnl / (holdings * result.trades[-1].entry_price)

                    cash += position_value

                    # Update trade record
                    result.trades[-1].exit_time = timestamp
                    result.trades[-1].exit_price = price
                    result.trades[-1].pnl = pnl
                    result.trades[-1].pnl_pct = pnl_pct
                    result.trades[-1].exit_reason = "sell_signal"

                    holdings = 0
                    position = None

                    if config.verbose:
                        print(
                            f"  SELL @ ${price:,.2f} (PnL: ${pnl:,.2f}, confidence: {confidence:.0%})"
                        )

            except Exception as e:
                if config.verbose:
                    print(f"  [ERROR] Cycle failed: {e}")
                continue

            # Update equity curve
            equity = cash + (holdings * price)
            result.equity_curve.append(
                {
                    "timestamp": timestamp,
                    "equity": equity,
                    "cash": cash,
                    "holdings": holdings,
                    "price": price,
                }
            )

        # Close any open position at end
        if position == "long" and holdings > 0:
            final_price = df.iloc[-1]["close"]
            position_value = holdings * final_price
            pnl = position_value - (holdings * result.trades[-1].entry_price)

            cash += position_value

            result.trades[-1].exit_time = df.iloc[-1]["timestamp"]
            result.trades[-1].exit_price = final_price
            result.trades[-1].pnl = pnl
            result.trades[-1].pnl_pct = pnl / (holdings * result.trades[-1].entry_price)
            result.trades[-1].exit_reason = "end_of_backtest"

            if config.verbose:
                print(
                    f"  CLOSE @ ${final_price:,.2f} (PnL: ${pnl:,.2f}) [End of Backtest]"
                )

        result.end_time = datetime.now()
        result.calculate_metrics()

        return result

    def _calculate_market_features(self, df: pd.DataFrame, index: int) -> Dict:
        """Calculate market features for current bar"""
        if index < 50:
            # Not enough history
            return {
                "price": df.iloc[index]["close"],
                "change": 0,
                "volume": df.iloc[index].get("volume", 0),
                "volatility": 0.2,
            }

        # Get window of data
        window = df.iloc[max(0, index - 50) : index + 1]

        current_price = df.iloc[index]["close"]
        prev_price = df.iloc[index - 1]["close"]

        # Calculate metrics
        price_change = (
            (current_price - prev_price) / prev_price if prev_price > 0 else 0
        )

        # Volatility (std of returns)
        returns = window["close"].pct_change().dropna()
        volatility = returns.std() if len(returns) > 0 else 0.2

        # SMA
        sma20 = window["close"].rolling(20).mean().iloc[-1]
        sma50 = window["close"].rolling(50).mean().iloc[-1]

        # Trend
        trend = (
            "up"
            if current_price > sma20 > sma50
            else "down"
            if current_price < sma20 < sma50
            else "sideways"
        )

        # Volume
        avg_volume = window["volume"].mean() if "volume" in window.columns else 0
        current_volume = df.iloc[index].get("volume", avg_volume)

        return {
            "price": current_price,
            "change": price_change,
            "volume": current_volume,
            "volatility": volatility,
            "trend": trend,
            "sma20": sma20,
            "sma50": sma50,
        }

    def print_results(self):
        """Print backtest results summary"""
        print("\n" + "=" * 70)
        print("BACKTEST RESULTS SUMMARY")
        print("=" * 70)

        for name, result in self.results.items():
            print(f"\n{name}:")
            print(
                f"  Total Return: ${result.total_return:,.2f} ({result.total_return_pct:+.2f}%)"
            )
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(
                f"  Max Drawdown: ${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)"
            )
            print(f"  Total Trades: {result.num_trades}")
            print(f"  Win Rate: {result.win_rate*100:.1f}%")
            print(f"  Profit Factor: {result.profit_factor:.2f}")
            print(f"  Avg Trade: ${result.avg_trade:,.2f}")

            if result.num_trades > 0:
                print(f"  Avg Win: ${result.avg_win:,.2f}")
                print(f"  Avg Loss: ${result.avg_loss:,.2f}")

        # Comparison
        if len(self.results) == 2:
            names = list(self.results.keys())
            r1, r2 = self.results[names[0]], self.results[names[1]]

            print("\n" + "-" * 70)
            print("COMPARISON:")
            print(f"  Return Diff: ${r1.total_return - r2.total_return:,.2f}")
            print(f"  Sharpe Diff: {r1.sharpe_ratio - r2.sharpe_ratio:+.2f}")
            print(f"  Win Rate Diff: {(r1.win_rate - r2.win_rate)*100:+.1f}%")

    def save_results(self, output_dir: str = "backtest_results"):
        """Save results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for name, result in self.results.items():
            # Save trades
            trades_df = pd.DataFrame(
                [
                    {
                        "entry_time": t.entry_time,
                        "exit_time": t.exit_time,
                        "symbol": t.symbol,
                        "entry_price": t.entry_price,
                        "exit_price": t.exit_price,
                        "size": t.size,
                        "action": t.action,
                        "pnl": t.pnl,
                        "pnl_pct": t.pnl_pct,
                        "exit_reason": t.exit_reason,
                    }
                    for t in result.trades
                ]
            )

            trades_file = output_path / f"{name}_{timestamp}_trades.csv"
            trades_df.to_csv(trades_file, index=False)

            # Save equity curve
            equity_df = pd.DataFrame(result.equity_curve)
            equity_file = output_path / f"{name}_{timestamp}_equity.csv"
            equity_df.to_csv(equity_file, index=False)

            # Save summary
            summary = {
                "name": name,
                "timestamp": timestamp,
                "config": {
                    "start_date": str(result.config.start_date),
                    "end_date": str(result.config.end_date),
                    "symbols": result.config.symbols,
                    "initial_capital": result.config.initial_capital,
                },
                "metrics": {
                    "total_return": result.total_return,
                    "total_return_pct": result.total_return_pct,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "num_trades": result.num_trades,
                    "win_rate": result.win_rate,
                    "profit_factor": result.profit_factor,
                    "avg_trade": result.avg_trade,
                },
            }

            summary_file = output_path / f"{name}_{timestamp}_summary.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2, default=str)

            print(f"[OK] Results saved for {name}")


async def main():
    """Main backtest runner"""
    print("=" * 70)
    print("FEDERATED TRIAD BACKTEST ENGINE")
    print("=" * 70)

    # Configuration
    config = BacktestConfig(
        # Use last 60 days for quick test
        start_date=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        end_date=None,
        symbols=["BTC-EUR"],
        timeframe="1h",
        initial_capital=10000.0,
        position_size=0.1,
        enable_federated=True,
        enable_legacy=False,  # Set to True if you want comparison
        save_results=True,
        verbose=True,
    )

    # Create engine
    engine = FederatedBacktestEngine(config)

    # Load data
    print("\n[1/4] Loading historical data...")
    if not engine.load_data():
        print("[ERROR] Failed to load data. Exiting.")
        return

    # Run backtest
    print("\n[2/4] Running backtest...")
    results = await engine.run_backtest()

    if not results:
        print("[ERROR] Backtest produced no results.")
        return

    # Print results
    print("\n[3/4] Calculating performance metrics...")
    engine.print_results()

    # Save results
    if config.save_results:
        print("\n[4/4] Saving results...")
        engine.save_results()

    print("\n" + "=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
