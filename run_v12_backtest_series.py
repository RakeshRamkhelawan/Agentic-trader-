"""
V12 Backtest Series: 3 Runs with Progressive Optimization

Run 1: 20 symbols (2020-2025) - Baseline
Run 2: 50 symbols (2020-2025) - Optimize based on Run 1 learnings
Run 3: 100 symbols (2020-2025) - Final optimized run
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.mcp_broker.backtest_engine_v18_optimized import (
    OptimizedBacktestEngineV18,
    OptimizedBacktestConfig,
)
from backend.core.conscious.global_chitta import get_global_chitta


# Available symbols from cache
CACHE_DIR = Path("backend/data/backtest_cache")
AVAILABLE_SYMBOLS = [f.replace('.csv', '') for f in os.listdir(CACHE_DIR) if f.endswith('.csv')]

# Select diverse symbol sets
SYMBOL_SETS = {
    "run_1_20": [
        "BTC_EUR", "ETH_EUR", "AAPL", "MSFT", "GOOGL",
        "AMZN", "TSLA", "NVDA", "META", "NFLX",
        "AMD", "INTC", "CRM", "ADBE", "ORCL",
        "EUR_USD", "GBP_USD", "GOLD_USD", "SILVER_USD", "OIL_USD"
    ],
    "run_2_50": [
        # All from run 1 plus
        "ADA_EUR", "DOT_EUR", "SOL_EUR", "MATIC_EUR",
        "SPY", "QQQ", "IWM", "VTI", "VOO",
        "JPM", "BAC", "WFC", "GS", "C",
        "JNJ", "PFE", "UNH", "MRK", "ABBV",
        "DIS", "NKE", "SBUX", "MCD", "HD",
        "LOW", "TGT", "WMT", "COST", "PG",
        "KO", "PEP", "XOM", "CVX", "COP"
    ],
    "run_3_100": [
        # All from run 2 plus
        "ASML", "AIR", "SAP", "SIE", "ALV",
        "LMT", "BA", "RTX", "NOC", "GD",
        "V", "MA", "AXP", "DFS", "COF",
        "T", "VZ", "TMUS", "CMCSA", "CHTR",
        "CAT", "DE", "GE", "HON", "MMM",
        "UPS", "FDX", "CSX", "NSC", "UNP",
        "LIN", "APD", "SHW", "ECL", "NEM",
        "FCX", "DOW", "DD", "LYB", "PPG",
        "PLD", "AMT", "CCI", "EQIX", "DLR",
        "SPG", "O", "WELL", "PSA", "AVB"
    ]
}


def validate_symbols(symbols: List[str]) -> List[str]:
    """Filter to only available symbols."""
    available = set(AVAILABLE_SYMBOLS)
    valid = [s for s in symbols if s in available]
    missing = [s for s in symbols if s not in available]
    if missing:
        print(f"  Warning: {len(missing)} symbols not in cache: {missing[:5]}...")
    return valid


def analyze_results(results: Dict[str, Any], run_name: str) -> Dict[str, Any]:
    """Analyze backtest results and extract learnings."""
    trades = results.get("trades", [])
    signals = results.get("signals", [])

    if not trades:
        return {"error": "No trades generated"}

    # Calculate metrics
    df_trades = pd.DataFrame(trades)

    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.get("pnl", 0) > 0])
    losing_trades = total_trades - winning_trades
    winrate = winning_trades / total_trades if total_trades > 0 else 0

    total_pnl = sum(t.get("pnl", 0) for t in trades)
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

    # Sharpe ratio (simplified)
    returns = [t.get("pnl", 0) for t in trades]
    sharpe = (pd.Series(returns).mean() / pd.Series(returns).std() * (252 ** 0.5)) if len(returns) > 1 and pd.Series(returns).std() > 0 else 0

    # Max drawdown
    cumulative = pd.Series(returns).cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max).min()

    # Per-symbol analysis
    symbol_performance = {}
    for symbol in set(t.get("symbol") for t in trades):
        symbol_trades = [t for t in trades if t.get("symbol") == symbol]
        symbol_pnl = sum(t.get("pnl", 0) for t in symbol_trades)
        symbol_winrate = len([t for t in symbol_trades if t.get("pnl", 0) > 0]) / len(symbol_trades) if symbol_trades else 0
        symbol_performance[symbol] = {
            "trades": len(symbol_trades),
            "pnl": symbol_pnl,
            "winrate": symbol_winrate
        }

    # Top/bottom performers
    sorted_symbols = sorted(symbol_performance.items(), key=lambda x: x[1]["pnl"], reverse=True)
    top_performers = sorted_symbols[:5]
    bottom_performers = sorted_symbols[-5:]

    analysis = {
        "run_name": run_name,
        "total_trades": total_trades,
        "winrate": winrate,
        "total_pnl": total_pnl,
        "avg_pnl_per_trade": avg_pnl,
        "sharpe_ratio": sharpe,
        "max_drawdown": drawdown,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "symbol_performance": symbol_performance,
    }

    return analysis


def generate_learnings(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate optimization recommendations based on analysis."""
    learnings = {
        "threshold_adjustments": {},
        "symbol_weights": {},
        "regime_preferences": [],
        "risk_adjustments": {}
    }

    # Analyze winrate
    winrate = analysis.get("winrate", 0)
    if winrate < 0.5:
        learnings["threshold_adjustments"]["confidence_threshold"] = "Increase to 0.75"
        learnings["threshold_adjustments"]["vedastro_threshold"] = "Increase to 45"
    elif winrate > 0.65:
        learnings["threshold_adjustments"]["confidence_threshold"] = "Can lower to 0.65"

    # Identify best/worst symbols
    top_performers = analysis.get("top_performers", [])
    bottom_performers = analysis.get("bottom_performers", [])

    for symbol, perf in top_performers:
        learnings["symbol_weights"][symbol] = 1.5  # Boost weight

    for symbol, perf in bottom_performers:
        learnings["symbol_weights"][symbol] = 0.5  # Reduce weight

    # Risk adjustments based on drawdown
    max_dd = analysis.get("max_drawdown", 0)
    if max_dd < -0.15:
        learnings["risk_adjustments"]["position_size"] = "Reduce by 20%"
        learnings["risk_adjustments"]["stop_loss"] = "Tighten to 3%"

    return learnings


async def run_backtest(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    run_name: str,
    apply_learnings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Run a single backtest."""
    print(f"\n{'='*60}")
    print(f"BACKTEST: {run_name}")
    print(f"Symbols: {len(symbols)}")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"{'='*60}")

    # Validate symbols
    valid_symbols = validate_symbols(symbols)
    print(f"Valid symbols: {len(valid_symbols)}")

    if len(valid_symbols) < 5:
        print("ERROR: Not enough valid symbols!")
        return {"error": "Insufficient symbols"}

    # Configure engine
    config = OptimizedBacktestConfig(
        initial_capital=100000.0,
        max_position_eur=2000.0,
        enable_caching=True,
        enable_parallel_processing=True,
        enable_batch_processing=True,
        max_workers=4,
    )

    # Apply learnings if provided
    if apply_learnings:
        print("\nApplying optimizations from previous run...")
        # Adjust position size if needed
        if "position_size" in apply_learnings.get("risk_adjustments", {}):
            config.max_position_eur = 1600.0  # 20% reduction

    engine = OptimizedBacktestEngineV18(config)

    # Run backtest
    start_time = datetime.now()
    try:
        results = await engine.run_backtest(
            symbols=valid_symbols,
            start_date=start_date,
            end_date=end_date,
            interval="1d"
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        results["elapsed_seconds"] = elapsed

        print(f"\nBacktest completed in {elapsed:.1f}s")
        print(f"Total trades: {len(results.get('trades', []))}")

        return results

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


async def main():
    """Run the 3-phase backtest series."""
    results_dir = Path("backend/data/backtest_results/v12_series")
    results_dir.mkdir(parents=True, exist_ok=True)

    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 3, 5)

    all_results = {}
    learnings = None

    # === RUN 1: 20 Symbols ===
    print("\n" + "="*60)
    print("PHASE 1: Baseline with 20 Symbols")
    print("="*60)

    symbols_20 = SYMBOL_SETS["run_1_20"]
    results_1 = await run_backtest(
        symbols=symbols_20,
        start_date=start_date,
        end_date=end_date,
        run_name="run_1_baseline_20symbols"
    )

    if "error" not in results_1:
        analysis_1 = analyze_results(results_1, "run_1_baseline_20symbols")
        learnings = generate_learnings(analysis_1)

        # Save results
        with open(results_dir / "run_1_results.json", "w") as f:
            json.dump({
                "analysis": analysis_1,
                "learnings": learnings,
                "performance": results_1.get("performance", {})
            }, f, indent=2, default=str)

        print("\n" + "-"*60)
        print("RUN 1 RESULTS:")
        print(f"  Winrate: {analysis_1['winrate']:.1%}")
        print(f"  Total PnL: {analysis_1['total_pnl']:.2f}")
        print(f"  Sharpe: {analysis_1['sharpe_ratio']:.2f}")
        print(f"  Max DD: {analysis_1['max_drawdown']:.2%}")
        print(f"  Top Performers: {[s for s, _ in analysis_1['top_performers']]}")
        print("-"*60)

        all_results["run_1"] = analysis_1

    # === RUN 2: 50 Symbols + Optimization ===
    print("\n" + "="*60)
    print("PHASE 2: 50 Symbols with Optimization")
    print("="*60)

    # Use top performers from run 1 + new symbols
    if learnings:
        top_symbols = [s for s, _ in analysis_1.get("top_performers", [])]
        symbols_50 = list(dict.fromkeys(top_symbols + SYMBOL_SETS["run_2_50"]))[:50]
    else:
        symbols_50 = SYMBOL_SETS["run_2_50"][:50]

    results_2 = await run_backtest(
        symbols=symbols_50,
        start_date=start_date,
        end_date=end_date,
        run_name="run_2_optimized_50symbols",
        apply_learnings=learnings
    )

    if "error" not in results_2:
        analysis_2 = analyze_results(results_2, "run_2_optimized_50symbols")
        learnings_2 = generate_learnings(analysis_2)

        with open(results_dir / "run_2_results.json", "w") as f:
            json.dump({
                "analysis": analysis_2,
                "learnings": learnings_2,
                "performance": results_2.get("performance", {})
            }, f, indent=2, default=str)

        print("\n" + "-"*60)
        print("RUN 2 RESULTS:")
        print(f"  Winrate: {analysis_2['winrate']:.1%}")
        print(f"  Total PnL: {analysis_2['total_pnl']:.2f}")
        print(f"  Sharpe: {analysis_2['sharpe_ratio']:.2f}")
        print(f"  Max DD: {analysis_2['max_drawdown']:.2%}")
        print("-"*60)

        all_results["run_2"] = analysis_2
        learnings = learnings_2  # Update for run 3

    # === RUN 3: 100 Symbols + Final Optimization ===
    print("\n" + "="*60)
    print("PHASE 3: 100 Symbols - Final Optimized")
    print("="*60)

    # Use available symbols up to 100
    symbols_100 = list(dict.fromkeys(
        list(SYMBOL_SETS["run_1_20"]) +
        list(SYMBOL_SETS["run_2_50"]) +
        list(SYMBOL_SETS["run_3_100"])
    ))[:100]

    results_3 = await run_backtest(
        symbols=symbols_100,
        start_date=start_date,
        end_date=end_date,
        run_name="run_3_final_100symbols",
        apply_learnings=learnings
    )

    if "error" not in results_3:
        analysis_3 = analyze_results(results_3, "run_3_final_100symbols")

        with open(results_dir / "run_3_results.json", "w") as f:
            json.dump({
                "analysis": analysis_3,
                "performance": results_3.get("performance", {})
            }, f, indent=2, default=str)

        print("\n" + "-"*60)
        print("RUN 3 RESULTS:")
        print(f"  Winrate: {analysis_3['winrate']:.1%}")
        print(f"  Total PnL: {analysis_3['total_pnl']:.2f}")
        print(f"  Sharpe: {analysis_3['sharpe_ratio']:.2f}")
        print(f"  Max DD: {analysis_3['max_drawdown']:.2%}")
        print("-"*60)

        all_results["run_3"] = analysis_3

    # === SUMMARY ===
    print("\n" + "="*60)
    print("BACKTEST SERIES SUMMARY")
    print("="*60)

    for run_name, analysis in all_results.items():
        print(f"\n{run_name.upper()}:")
        print(f"  Trades: {analysis['total_trades']}")
        print(f"  Winrate: {analysis['winrate']:.1%}")
        print(f"  PnL: {analysis['total_pnl']:.2f}")
        print(f"  Sharpe: {analysis['sharpe_ratio']:.2f}")
        print(f"  Max DD: {analysis['max_drawdown']:.2%}")

    # Save summary
    with open(results_dir / "summary.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nResults saved to: {results_dir}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
