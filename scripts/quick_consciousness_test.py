#!/usr/bin/env python3
"""Quick 3-day test of consciousness backtest"""

import asyncio
import sys

sys.path.insert(0, "/app")

import logging
from pathlib import Path

import pandas as pd

from scripts.consciousness_backtest import ConsciousnessBacktestEngine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def quick_test():
    # Load data
    data_dir = Path("/app/data/historical_6year")

    data = {}
    for symbol in ["BTC-EUR"]:
        df = pd.read_pickle(data_dir / f"{symbol}_1d_2020-2026_binance.pkl")
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, unit="ms")
        data[symbol] = df
        logger.info(f"Loaded {symbol}: {len(df)} rows")

    # Create engine
    engine = ConsciousnessBacktestEngine(initial_capital=100000, symbols=["BTC-EUR"])

    # Run for just 3 days
    logger.info("\n🧠 Running 3-day Consciousness Backtest...")
    results = await engine.run_backtest(data, days=3)

    logger.info(f'\n✓ Done! Final Equity: €{results["final_equity"]:,.2f}')
    logger.info(f'✓ Return: {results["total_return_pct"]:+.2f}%')
    logger.info(f'✓ Trades: {results["total_trades"]}')
    if results.get("tattva_analysis"):
        logger.info(f'✓ Dominant Guna: {results["tattva_analysis"]["dominant_guna"]}')


if __name__ == "__main__":
    asyncio.run(quick_test())
