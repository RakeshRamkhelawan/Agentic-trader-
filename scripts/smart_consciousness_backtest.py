#!/usr/bin/env python3
"""
SMART Consciousness Backtest - Optimized Version
Features: Batched API calls, Intelligent Caching, Hybrid Rule+LLM
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from scripts.smart_consciousness_agents import SmartConsciousnessOrchestrator


class SmartConsciousnessBacktest:
    """Optimized backtest with smart caching and batched API calls"""

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.equity_curve: List[Dict] = []
        self.trades: List[Dict] = []

        # Smart orchestrator
        self.orchestrator = SmartConsciousnessOrchestrator()

    async def run(self, data: Dict[str, pd.DataFrame], days: int = 90) -> Dict:
        """Run optimized backtest"""
        logger.info("=" * 70)
        logger.info("🧠 SMART CONSCIOUSNESS BACKTEST (Optimized)")
        logger.info("=" * 70)
        logger.info(f"Symbols: {', '.join(data.keys())}")
        logger.info(f"Period: {days} days")
        logger.info(f"Capital: €{self.initial_capital:,.2f}")
        logger.info("Features: Batched API + Smart Cache + Rule+LLM Hybrid")
        logger.info("-" * 70)

        # Align data
        aligned = self._align_data(data, days)
        if not aligned:
            return {"error": "No data"}

        dates = aligned[list(aligned.keys())[0]].index

        # Run simulation
        for i, date in enumerate(dates):
            progress = (i / len(dates)) * 100

            # Progress logging every 10 candles
            if i % 10 == 0:
                equity = self._calculate_equity(aligned, date)
                cache_stats = self.orchestrator.get_stats()
                logger.info(
                    f"  {progress:5.1f}% | {date.strftime('%Y-%m-%d')} | "
                    f"Equity: €{equity:>12,.2f} | "
                    f"API: {cache_stats['api_calls']} | Cache: {cache_stats['cache_hits']}"
                )

            # Process each symbol
            for symbol in aligned.keys():
                df = aligned[symbol]

                # Get data slice up to current date
                df_slice = df.loc[:date]
                if len(df_slice) < 20:  # Need at least 20 candles
                    continue

                # Build portfolio context
                portfolio = {"cash": self.cash, "positions": self.positions}

                # Smart analysis
                try:
                    decision = await self.orchestrator.analyze(
                        symbol, df_slice, portfolio
                    )

                    # Execute decision
                    await self._execute(decision, symbol, df_slice, date, aligned)

                except Exception as e:
                    logger.error(f"Analysis failed: {e}")
                    continue

            # Record equity
            equity = self._calculate_equity(aligned, date)
            self.equity_curve.append(
                {
                    "date": date,
                    "equity": equity,
                    "cash": self.cash,
                    "positions": len(self.positions),
                }
            )

        # Generate results
        return self._generate_results(aligned)

    def _align_data(self, data: Dict, days: int) -> Dict:
        """Align data to common range"""
        aligned = {}
        for symbol, df in data.items():
            if df is None or df.empty:
                continue
            df = df.copy()
            # Convert timestamp column to index if needed
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df.set_index("timestamp", inplace=True)
            elif not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, unit="ms")
            if len(df) > days:
                df = df.iloc[-days:].copy()
            aligned[symbol] = df
        return aligned

    async def _execute(
        self,
        decision: Dict,
        symbol: str,
        df_slice: pd.DataFrame,
        date: datetime,
        all_data: Dict,
    ):
        """Execute trading decision"""
        final = decision.get("final_decision", {})
        action = final.get("action", "HOLD")
        confidence = final.get("confidence", 0.5)

        current = df_slice.iloc[-1]
        price = float(current["close"])

        # Skip low confidence
        if confidence < 0.4:
            return

        # BUY
        if action == "BUY" and symbol not in self.positions:
            size_pct = min(final.get("position_size_pct", 10.0), 20.0)
            position_value = self.cash * (size_pct / 100) * confidence

            if position_value > 100:
                quantity = position_value / price
                self.positions[symbol] = {
                    "entry_date": date,
                    "entry_price": price,
                    "quantity": quantity,
                    "value": position_value,
                    "confidence": confidence,
                }
                self.cash -= position_value

                # Log with cache status
                cache_hit = decision.get("cache_hit", False)
                cache_str = "[CACHE]" if cache_hit else "[API]"

                logger.info(
                    f"    📥 {cache_str} BUY {symbol} @ €{price:,.2f} "
                    f"(size: {size_pct:.1f}%, conf: {confidence:.2f})"
                )

                self.trades.append(
                    {
                        "date": date,
                        "symbol": symbol,
                        "action": "BUY",
                        "price": price,
                        "quantity": quantity,
                        "value": position_value,
                        "confidence": confidence,
                        "cache_hit": cache_hit,
                        "deliberation": decision.get("council_deliberation", {}),
                    }
                )

        # SELL
        elif action == "SELL" and symbol in self.positions:
            position = self.positions[symbol]
            quantity = position["quantity"]
            sale_value = quantity * price
            pnl = sale_value - position["value"]
            pnl_pct = (pnl / position["value"]) * 100

            self.cash += sale_value

            cache_hit = decision.get("cache_hit", False)
            cache_str = "[CACHE]" if cache_hit else "[API]"

            logger.info(
                f"    📤 {cache_str} SELL {symbol} @ €{price:,.2f} "
                f"(P&L: €{pnl:,.2f}, {pnl_pct:+.2f}%)"
            )

            self.trades.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "action": "SELL",
                    "price": price,
                    "quantity": quantity,
                    "value": sale_value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "hold_days": (date - position["entry_date"]).days,
                    "cache_hit": cache_hit,
                }
            )

            del self.positions[symbol]

    def _calculate_equity(self, data: Dict, date: datetime) -> float:
        """Calculate total equity"""
        equity = self.cash
        for symbol, pos in self.positions.items():
            if symbol in data and date in data[symbol].index:
                price = data[symbol].loc[date, "close"]
                equity += pos["quantity"] * price
        return equity

    def _generate_results(self, data: Dict) -> Dict:
        """Generate results"""
        if not self.equity_curve:
            return {"error": "No data"}

        equity_df = pd.DataFrame(self.equity_curve)
        final_equity = equity_df["equity"].iloc[-1]
        total_return = (
            (final_equity - self.initial_capital) / self.initial_capital * 100
        )

        # Daily returns
        equity_df["daily_return"] = equity_df["equity"].pct_change()

        # Metrics
        volatility = equity_df["daily_return"].std() * np.sqrt(365) * 100
        sharpe = (
            (equity_df["daily_return"].mean() / equity_df["daily_return"].std())
            * np.sqrt(365)
            if equity_df["daily_return"].std() > 0
            else 0
        )

        # Max drawdown
        equity_df["peak"] = equity_df["equity"].cummax()
        equity_df["drawdown"] = (equity_df["equity"] - equity_df["peak"]) / equity_df[
            "peak"
        ]
        max_dd = equity_df["drawdown"].min() * 100

        # Trade stats
        closed = [t for t in self.trades if t["action"] == "SELL"]
        winners = [t for t in closed if t.get("pnl", 0) > 0]

        win_rate = len(winners) / len(closed) * 100 if closed else 0

        # Cache stats
        cache_stats = self.orchestrator.get_stats()

        # Guna analysis from trades
        guna_counts = {"sattva": 0, "rajas": 0, "tamas": 0}
        for trade in self.trades:
            delim = trade.get("deliberation", {})
            ahamkara = delim.get("ahamkara", {})
            guna = ahamkara.get("dominant_guna", "unknown")
            if guna in guna_counts:
                guna_counts[guna] += 1

        results = {
            "backtest_type": "SMART_CONSCIOUSNESS",
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_return_pct": total_return,
            "cagr_pct": (
                (final_equity / self.initial_capital) ** (365 / len(equity_df)) - 1
            )
            * 100
            if len(equity_df) > 0
            else 0,
            "volatility_pct": volatility,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd,
            "total_trades": len(closed),
            "win_rate": win_rate,
            "cache_stats": cache_stats,
            "guna_distribution": guna_counts,
            "equity_curve": self.equity_curve,
            "trades": self.trades,
        }

        return results


async def main():
    """Run smart backtest"""

    # Load data
    data_dir = Path("/app/data/historical_6year")
    data = {}

    for symbol in ["BTC-EUR", "ETH-EUR"]:
        file_path = data_dir / f"{symbol}_1d_2020-2026_binance.pkl"
        if file_path.exists():
            df = pd.read_pickle(file_path)
            data[symbol] = df
            logger.info(f"✓ Loaded {symbol}: {len(df)} rows")

    if not data:
        logger.error("No data found!")
        return

    # Run backtest
    engine = SmartConsciousnessBacktest(initial_capital=100000)
    results = await engine.run(data, days=30)  # 30 days for demo

    # Print results
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESULTS")
    logger.info("=" * 70)
    logger.info(f"Final Equity:    €{results['final_equity']:,.2f}")
    logger.info(f"Total Return:    {results['total_return_pct']:+.2f}%")
    logger.info(f"CAGR:            {results['cagr_pct']:.2f}%")
    logger.info(f"Sharpe Ratio:    {results['sharpe_ratio']:.2f}")
    logger.info(f"Max Drawdown:    {results['max_drawdown_pct']:.2f}%")
    logger.info(f"\nTrades:          {results['total_trades']}")
    logger.info(f"Win Rate:        {results['win_rate']:.1f}%")

    cache = results["cache_stats"]
    logger.info("\n💾 Cache Stats:")
    logger.info(f"   API Calls:    {cache['api_calls']}")
    logger.info(f"   Cache Hits:   {cache['cache_hits']}")
    logger.info(f"   Hit Rate:     {cache['cache_hit_rate']*100:.1f}%")

    if results["guna_distribution"]:
        logger.info("\n🕉️  Guna Distribution:")
        for guna, count in results["guna_distribution"].items():
            logger.info(f"   {guna.capitalize()}: {count}")

    # Save results
    output_dir = Path("/app/data/backtest_results")
    output_dir.mkdir(exist_ok=True)
    output_file = (
        output_dir
        / f"smart_consciousness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"\n💾 Saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
