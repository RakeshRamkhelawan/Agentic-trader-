#!/usr/bin/env python3
"""
Real Paper Trading V18 - Pancha-Tattva Agentic Consensus Engine

Gebruikt de V18 engine met:
- Jala (Water): Dynamische gewichten per regime
- Vayu (Air): Volatiliteits dampening
- Gunas: VedAstro multiplier
- Earth: Hard veto op -7% stop loss

Usage:
    python scripts/real_paper_trading_v18.py --duration 8 --capital 10000
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.real_paper_trading_v18_direct import RealPaperTradingV18, PaperTradingConfig


async def main():
    parser = argparse.ArgumentParser(description="V18 Paper Trading - Pancha-Tattva Consensus")
    parser.add_argument("--duration", type=int, default=8, help="Trading duration in hours")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital")
    parser.add_argument("--symbols-per-cycle", type=int, default=20, help="Symbols analyzed per cycle")
    args = parser.parse_args()

    print("="*80)
    print("    V18 PANCHA-TATTVA PAPER TRADING")
    print("="*80)
    print(f"    Duration: {args.duration} hours")
    print(f"    Capital: EUR {args.capital:,.2f}")
    print(f"    Symbols per cycle: {args.symbols_per_cycle}")
    print()
    print("    Consensus Architecture:")
    print("    - VedAstro (Akasha): Cosmic timing")
    print("    - Earth (Prithvi): Capital protection")
    print("    - Fire (Agni): Position sizing")
    print("    - Water (Jala): Regime detection")
    print("    - Air (Vayu): Volatility dampening")
    print("    - Gunas: VedAstro quality multiplier")
    print("="*80)
    print()

    # Initialize and run (V18 engine creates its own config)
    engine = RealPaperTradingV18(initial_capital=args.capital)

    try:
        await engine.initialize()
        await engine.run(duration_hours=args.duration)
    except KeyboardInterrupt:
        print("\n[STOPPED] Interrupted by user")
    finally:
        await engine.close()

        # Print final stats
        if engine.state:
            print("\n" + "="*80)
            print("    FINAL RESULTS")
            print("="*80)
            print(f"    Total Trades: {engine.state.total_trades}")
            print(f"    Final Portfolio: EUR {engine.state.total_value:,.2f}")
            print(f"    Total P&L: EUR {engine.state.total_pnl:+,.2f}")
            print(f"    Cycles Completed: {engine._cycle_count}")
            print("="*80)

            # Analytics locatie
            log_dir = Path("paper_trading_analytics")
            if log_dir.exists():
                print(f"\nAnalytics saved to: {log_dir}/")
                jsonl_files = list(log_dir.glob("v18_analytics_*.jsonl"))
                if jsonl_files:
                    print(f"  - {jsonl_files[-1].name}")


if __name__ == "__main__":
    asyncio.run(main())
