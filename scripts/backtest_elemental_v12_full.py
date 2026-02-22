"""
Elemental System Backtest V12 - FULL RUN (2020-2026)
54 assets (50 + 4 inverse ETFs) with hedge pairs and bond inverse logic.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["TRADING_MODE"] = "paper"

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("BacktestV12Full")

from sqlalchemy import create_engine, text

from scripts.backtest_elemental_v12 import V12BacktestEngine


def get_all_available_symbols():
    """Get all symbols from database"""
    db_url = (
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://trader:trading_secure@localhost:5456/trading_db",
        )
        .replace("+asyncpg", "+psycopg2")
        .replace("postgresql+psycopg2", "postgresql")
    )

    engine = create_engine(db_url)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT DISTINCT symbol FROM market_candles
            WHERE timestamp >= '2020-01-01'
            ORDER BY symbol
        """
            )
        )
        symbols = [row[0] for row in result]

    return symbols


def main():
    """Run full V12 backtest (2020-2026)"""

    logger.info("=" * 70)
    logger.info("V12 FULL BACKTEST: 2020-2026 (54 Assets)")
    logger.info("Hedge Pairs + Bond Inverse + Earth should_enter")
    logger.info("=" * 70)

    # Get all available symbols
    all_symbols = get_all_available_symbols()
    logger.info(f"Available symbols: {len(all_symbols)}")

    # Use all available symbols (up to 50) + inverse ETFs will be added via hedge logic
    symbols = all_symbols[:50]
    logger.info(f"Running with: {len(symbols)} primary assets")
    logger.info("Inverse ETFs (SH, PSQ, RWM, TBF) added via hedge logic")

    # Full period
    start_date = "2020-01-01"
    end_date = "2026-01-01"
    initial_capital = 100000.0

    logger.info(f"Period: {start_date} to {end_date}")
    logger.info(f"Initial Capital: ${initial_capital:,.2f}")

    # Create engine
    engine = V12BacktestEngine(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
    )

    # Run backtest
    result = engine.run_backtest()

    # Save results
    output_file = (
        f"backtest_v12_full_2020_2026_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    result.save(output_file)

    logger.info("\n" + "=" * 70)
    logger.info(f"RESULTS SAVED: {output_file}")
    logger.info("=" * 70)

    return result


if __name__ == "__main__":
    main()
