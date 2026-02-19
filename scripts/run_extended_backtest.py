#!/usr/bin/env python3
"""
EXTENDED FEDERATED TRIAD BACKTEST
Meer data, betere statistieken, vergelijking met buy-and-hold
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from trika_federated_system import FederatedTriadSystem


class SimpleBacktestRunner:
    """Simplified backtest runner for faster execution"""

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.system = FederatedTriadSystem()

    def load_data(self, symbol: str = "BTC_USDT", days: int = 180) -> pd.DataFrame:
        """Load historical data"""
        data_file = (
            Path(__file__).parent.parent
            / "data"
            / "historical"
            / "binance"
            / f"{symbol}_1h.csv"
        )

        if not data_file.exists():
            raise FileNotFoundError(f"Data file not found: {data_file}")

        df = pd.read_csv(data_file)

        # Parse timestamp
        if df["timestamp"].iloc[0] > 1e10:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Take last N days
        cutoff = df["timestamp"].max() - timedelta(days=days)
        df = (
            df[df["timestamp"] >= cutoff]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        return df

    def calculate_features(self, df: pd.DataFrame, idx: int) -> Dict:
        """Calculate market features"""
        if idx < 20:
            return {
                "price": df.iloc[idx]["close"],
                "change": 0,
                "volume": df.iloc[idx].get("volume", 0),
                "volatility": 0.2,
                "trend": "unknown",
            }

        window = df.iloc[max(0, idx - 20) : idx + 1]
        current_price = df.iloc[idx]["close"]
        prev_price = df.iloc[idx - 1]["close"]

        returns = window["close"].pct_change().dropna()
        volatility = returns.std() if len(returns) > 0 else 0.2

        sma5 = window["close"].rolling(5).mean().iloc[-1]
        sma20 = window["close"].rolling(20).mean().iloc[-1]

        trend = (
            "up"
            if current_price > sma5 > sma20
            else "down"
            if current_price < sma5 < sma20
            else "neutral"
        )

        return {
            "price": current_price,
            "change": (current_price - prev_price) / prev_price
            if prev_price > 0
            else 0,
            "volume": df.iloc[idx].get("volume", 0),
            "volatility": volatility,
            "trend": trend,
            "sma5": sma5,
            "sma20": sma20,
        }

    async def run(self, df: pd.DataFrame) -> Dict:
        """Run backtest"""
        print(f"Running backtest on {len(df)} bars...")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        cash = self.initial_capital
        holdings = 0.0
        trades = []
        equity_curve = []

        position = None
        entry_price = 0

        for i in range(len(df)):
            row = df.iloc[i]
            price = row["close"]
            timestamp = row["timestamp"]

            # Calculate features
            features = self.calculate_features(df, i)

            # Skip first 50 bars for warm-up
            if i < 50:
                equity = cash + (holdings * price)
                equity_curve.append(
                    {"timestamp": timestamp, "equity": equity, "price": price}
                )
                continue

            # Get system decision
            try:
                result = await self.system.process_cycle(features)
                action = result.get("decision", {}).get("action", "hold")
                confidence = result.get("decision", {}).get("confidence", 0)
            except Exception:
                action = "hold"
                confidence = 0

            # Execute trades
            if action == "buy" and position is None:
                # Buy with 20% of capital
                invest = cash * 0.2
                shares = invest / price
                cash -= invest
                holdings += shares
                position = "long"
                entry_price = price

                trades.append(
                    {
                        "type": "buy",
                        "timestamp": timestamp,
                        "price": price,
                        "shares": shares,
                        "confidence": confidence,
                    }
                )

                if len(trades) <= 5 or len(trades) % 10 == 0:
                    print(
                        f"  [{timestamp}] BUY  @ ${price:,.2f} (conf: {confidence:.0%})"
                    )

            elif action == "sell" and position == "long":
                # Sell position
                sell_value = holdings * price
                pnl = sell_value - (holdings * entry_price)
                pnl_pct = pnl / (holdings * entry_price) * 100

                cash += sell_value

                trades.append(
                    {
                        "type": "sell",
                        "timestamp": timestamp,
                        "price": price,
                        "shares": holdings,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "confidence": confidence,
                    }
                )

                if len(trades) <= 5 or len(trades) % 10 == 0:
                    print(
                        f"  [{timestamp}] SELL @ ${price:,.2f} (PnL: ${pnl:+.2f}, conf: {confidence:.0%})"
                    )

                holdings = 0
                position = None
                entry_price = 0

            # Record equity
            equity = cash + (holdings * price)
            equity_curve.append(
                {
                    "timestamp": timestamp,
                    "equity": equity,
                    "cash": cash,
                    "holdings": holdings,
                    "price": price,
                    "position": position,
                }
            )

        # Close final position
        if position == "long" and holdings > 0:
            final_price = df.iloc[-1]["close"]
            sell_value = holdings * final_price
            pnl = sell_value - (holdings * entry_price)

            cash += sell_value

            trades.append(
                {
                    "type": "sell",
                    "timestamp": df.iloc[-1]["timestamp"],
                    "price": final_price,
                    "shares": holdings,
                    "pnl": pnl,
                    "pnl_pct": pnl / (holdings * entry_price) * 100,
                    "confidence": 0,
                    "note": "end_of_backtest",
                }
            )

            print(f"  [CLOSE] Final position @ ${final_price:,.2f} (PnL: ${pnl:+.2f})")
            holdings = 0

        # Calculate metrics
        final_equity = cash
        total_return = final_equity - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Buy and hold comparison
        start_price = df.iloc[50]["close"]  # After warm-up
        end_price = df.iloc[-1]["close"]
        buy_hold_return = (end_price - start_price) / start_price * 100

        # Trade statistics
        closed_trades = [t for t in trades if t["type"] == "sell" and "pnl" in t]
        wins = [t for t in closed_trades if t["pnl"] > 0]
        losses = [t for t in closed_trades if t["pnl"] <= 0]

        win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
        avg_win = np.mean([t["pnl"] for t in wins]) if wins else 0
        avg_loss = np.mean([t["pnl"] for t in losses]) if losses else 0

        # Calculate max drawdown
        equity_values = [e["equity"] for e in equity_curve]
        peak = equity_values[0]
        max_dd = 0
        for eq in equity_values:
            if eq > peak:
                peak = eq
            dd = peak - eq
            if dd > max_dd:
                max_dd = dd
        max_dd_pct = (max_dd / peak) * 100 if peak > 0 else 0

        return {
            "trades": trades,
            "equity_curve": equity_curve,
            "metrics": {
                "initial_capital": self.initial_capital,
                "final_equity": final_equity,
                "total_return": total_return,
                "total_return_pct": total_return_pct,
                "buy_hold_return_pct": buy_hold_return,
                "outperformance": total_return_pct - buy_hold_return,
                "num_trades": len(closed_trades),
                "win_rate": win_rate,
                "num_wins": len(wins),
                "num_losses": len(losses),
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "max_drawdown": max_dd,
                "max_drawdown_pct": max_dd_pct,
                "profit_factor": abs(sum(t["pnl"] for t in wins))
                / abs(sum(t["pnl"] for t in losses))
                if losses
                else float("inf"),
            },
        }


def print_results(results: Dict):
    """Print backtest results"""
    m = results["metrics"]

    print("\n" + "=" * 70)
    print("BACKTEST RESULTS - FEDERATED TRIAD SYSTEM")
    print("=" * 70)

    print("\nPERFORMANCE METRICS:")
    print(f"  Initial Capital:  ${m['initial_capital']:>12,.2f}")
    print(f"  Final Equity:     ${m['final_equity']:>12,.2f}")
    print(
        f"  Total Return:     ${m['total_return']:>12,.2f} ({m['total_return_pct']:+.2f}%)"
    )
    print(
        f"  Max Drawdown:     ${m['max_drawdown']:>12,.2f} ({m['max_drawdown_pct']:.2f}%)"
    )

    print("\nBENCHMARK COMPARISON:")
    print(f"  Strategy Return:  {m['total_return_pct']:>10.2f}%")
    print(f"  Buy & Hold:       {m['buy_hold_return_pct']:>10.2f}%")
    print(f"  Outperformance:   {m['outperformance']:>+10.2f}%")

    print("\nTRADE STATISTICS:")
    print(f"  Total Trades:     {m['num_trades']:>10}")
    print(f"  Win Rate:         {m['win_rate']:>10.1f}%")
    print(f"  Wins/Losses:      {m['num_wins']:>5} / {m['num_losses']}")
    print(f"  Avg Win:          ${m['avg_win']:>10,.2f}")
    print(f"  Avg Loss:         ${m['avg_loss']:>10,.2f}")
    print(f"  Profit Factor:    {m['profit_factor']:>10.2f}")

    # Trade log
    print("\nTRADE LOG (first 10):")
    sells = [t for t in results["trades"] if t["type"] == "sell" and "pnl" in t][:10]
    for i, t in enumerate(sells, 1):
        pnl_str = f"${t['pnl']:>+,.2f}" if "pnl" in t else "N/A"
        print(f"  {i}. {t['timestamp']} @ ${t['price']:>10,.2f} -> PnL: {pnl_str}")

    print("\n" + "=" * 70)


def save_results(results: Dict, symbol: str = "BTC"):
    """Save results to files"""
    output_dir = Path("backtest_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save equity curve
    equity_df = pd.DataFrame(results["equity_curve"])
    equity_file = output_dir / f"federated_{symbol}_{timestamp}_equity.csv"
    equity_df.to_csv(equity_file, index=False)

    # Save trades
    trades_df = pd.DataFrame(results["trades"])
    trades_file = output_dir / f"federated_{symbol}_{timestamp}_trades.csv"
    trades_df.to_csv(trades_file, index=False)

    # Save summary
    summary_file = output_dir / f"federated_{symbol}_{timestamp}_summary.json"
    with open(summary_file, "w") as f:
        json.dump(
            {"symbol": symbol, "timestamp": timestamp, "metrics": results["metrics"]},
            f,
            indent=2,
            default=str,
        )

    print(f"\nResults saved to {output_dir}/")
    print(f"   - {equity_file.name}")
    print(f"   - {trades_file.name}")
    print(f"   - {summary_file.name}")


async def main():
    """Main entry point"""
    print("=" * 70)
    print("FEDERATED TRIAD - EXTENDED BACKTEST")
    print("=" * 70)

    # Create runner
    runner = SimpleBacktestRunner(initial_capital=10000.0)

    # Load data (last 180 days for more trades)
    print("\n[1/3] Loading data...")
    try:
        df = runner.load_data(symbol="BTC_USDT", days=180)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return

    # Run backtest
    print("\n[2/3] Running backtest (this may take a minute)...")
    results = await runner.run(df)

    # Print results
    print("\n[3/3] Analyzing results...")
    print_results(results)

    # Save results
    save_results(results, symbol="BTC")

    print("\n[OK] Backtest complete!")


if __name__ == "__main__":
    asyncio.run(main())
