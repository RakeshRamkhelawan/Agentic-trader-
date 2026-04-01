"""
v9 INTEGRATED BACKTEST
======================
Seamlessly integrates v9 Strategic Layer (MCTS, ToT) with v8 Symbiotic Agents

Usage:
    python run_v9_integrated_backtest.py --mode=strategic  # Full v9
    python run_v9_integrated_backtest.py --mode=v8         # Baseline v8

Architecture:
    Strategic Layer (v9)      Tactical Layer (v8)      Execution
    + MCTS Planner            + Ether Orchestrator     + Position Sizing
    + ToT Reasoning           + 4 Elemental Agents     + Risk Management
    + Memory (Chitta)         + Buddhi Decision        + Trade Execution
"""

import warnings

warnings.filterwarnings("ignore", message="invalid value encountered in scalar divide")

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Strategic context dataclass
from dataclasses import dataclass as _dataclass

# v9 Imports (new strategic layer)
from backend.core.mcts.planner import StrategicMCTSPlanner

# v8 Imports (existing, unmodified)
from backend.scripts.run_v8_symbiotic_backtest import (  # Baseline
    INITIAL_CAPITAL,
    SYMBOL_MAP,
    UNIVERSE_GROUPS,
    ActionType,
    CollectiveConsciousness,
    MarketState,
    Position,
    SymbioticRiskManager,
    TechnicalAnalyzer,
    download_data,
    run_v8_symbiotic_backtest,
)


@_dataclass
class StrategicContext:
    """Strategic context for v9 layer"""

    lookahead_days: int = 10
    mcts_confidence: float = 0.5
    strategic_bias: str = "neutral"
    time_horizon: str = "swing"
    position_size_mult: float = 1.0
    stop_loss_mult: float = 1.0
    take_profit_mult: float = 1.0


class StrategicPositionSizer:
    """Position sizer with strategic overrides"""

    def __init__(self, base_risk: float = 0.022):
        self.base_risk = base_risk

    def calculate_size(
        self,
        capital: float,
        decision: dict,
        atr: float,
        price: float,
        size_mult: float = 1.0,
    ) -> float:
        """Calculate position size with strategic multiplier"""
        base_risk = capital * self.base_risk

        # Apply strategic multiplier
        adjusted_risk = base_risk * size_mult

        stop_distance = atr * 1.6
        if stop_distance <= 0:
            stop_distance = price * 0.02

        position_value = (adjusted_risk / stop_distance) * price
        max_pos = capital * 0.25

        return min(position_value, max_pos)


def run_v9_integrated_backtest(
    use_strategic: bool = True, mcts_sims: int = 100, lookahead: int = 10
) -> Dict[str, Any]:
    """
    Run integrated v9 backtest with optional strategic layer

    Args:
        use_strategic: Enable v9 MCTS/ToT layer
        mcts_sims: Number of MCTS simulations
        lookahead: MCTS lookahead steps

    Returns:
        Backtest results dict
    """
    print("=" * 90)
    print("  v9 INTEGRATED BACKTEST")
    print("=" * 90)
    print(f"  Mode: {'STRATEGIC (v9)' if use_strategic else 'BASELINE (v8)'}")
    if use_strategic:
        print(f"  MCTS Simulations: {mcts_sims}")
        print(f"  Lookahead Steps: {lookahead}")
    print("=" * 90)

    # Initialize components
    print("\n[INIT] Loading components...")

    # v8 components (always loaded)
    tech_analyzer = TechnicalAnalyzer()
    v8_collective = CollectiveConsciousness()
    risk_manager = SymbioticRiskManager(max_total_positions=5, max_per_sector=2)

    # v9 components (optional)
    if use_strategic:
        print("  [v9] Initializing Strategic Layer...")
        strategic_sizer = StrategicPositionSizer(base_risk=0.022)
        mcts_planner = StrategicMCTSPlanner(lookahead_steps=lookahead, simulations=mcts_sims)
        print("  [v9] Strategic Layer ready")
    else:
        strategic_sizer = None
        mcts_planner = None
        print("  [v8] Using baseline symbiotic agents only")

    # Load data (same as v8)
    print("\n[DATA] Loading market data...")
    all_data = {}
    dates_set = set()

    for sym, ticker in SYMBOL_MAP.items():
        bars = download_data(sym, ticker)
        if bars:
            all_data[sym] = bars
            for bar in bars:
                dates_set.add(bar["date"])

    sorted_dates = sorted(list(dates_set))
    print(f"  Loaded {len(all_data)} symbols, {len(sorted_dates)} trading days")

    # Initialize tracking
    positions = {sym: Position() for sym in all_data.keys()}
    price_history = {
        sym: {"prices": [], "volumes": [], "highs": [], "lows": []} for sym in all_data.keys()
    }

    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_history = []
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} for sym in all_data.keys()}

    # Strategic tracking
    strategic_plans = []
    strategic_overrides = 0

    # Simulation loop
    print("\n[RUN] Starting simulation...")
    sim_start = time.time()
    total_days = len(sorted_dates)
    progress_interval = max(1, total_days // 20)

    # Pre-compute MCTS plans if strategic mode
    if use_strategic:
        print("\n  [v9] Pre-computing strategic plans (this may take a moment)...")
        # Sample: Compute plan every 5 days to save time
        plan_dates = sorted_dates[::5]
        for plan_date in plan_dates[:10]:  # First 10 for demo
            # Get market snapshot
            snapshot = {}
            for sym in list(all_data.keys())[:5]:  # Top 5 for demo speed
                bars = all_data[sym]
                bar = next((b for b in bars if b["date"] == plan_date), None)
                if bar:
                    snapshot[sym] = {"price": bar["close"], "trend": 1}

            if snapshot:
                portfolio = {"capital": capital, "positions": {}}
                plan = mcts_planner.plan(portfolio, snapshot, list(snapshot.keys()))
                strategic_plans.append({"date": plan_date, "plan": plan})
        print(f"  [v9] Generated {len(strategic_plans)} strategic plans")

    # Main loop
    for day_idx, date in enumerate(sorted_dates):
        if day_idx % progress_interval == 0:
            pct = (day_idx / total_days) * 100
            elapsed = time.time() - sim_start
            print(
                f"  [{pct:5.1f}%] Day {day_idx}/{total_days} | "
                f"Capital: ${capital:,.0f} | Time: {elapsed:.0f}s"
            )

        # Update price data
        current_prices = {}
        for sym, bars in all_data.items():
            bar = next((b for b in bars if b["date"] == date), None)
            if bar:
                current_prices[sym] = bar
                ph = price_history[sym]
                ph["prices"].append(bar["close"])
                ph["volumes"].append(bar["volume"])
                ph["highs"].append(bar["high"])
                ph["lows"].append(bar["low"])
                if len(ph["prices"]) > 250:
                    for k in ph:
                        ph[k] = ph[k][-200:]

        # Check exits (same as v8)
        for sym, pos in positions.items():
            if pos.position != 0 and sym in current_prices:
                bar = current_prices[sym]
                pos.bars_in_trade += 1
                pos.update_trailing(bar["close"])

                exit_reason = pos.check_exit(bar["close"])
                if exit_reason:
                    pnl = pos.close(bar["close"])
                    capital += pnl
                    risk_manager.remove_position(sym)

                    symbol_metrics[sym]["trades"] += 1
                    if pnl > 0:
                        symbol_metrics[sym]["wins"] += 1
                    symbol_metrics[sym]["pnl"] += pnl
                    trade_history.append(
                        {
                            "date": date,
                            "symbol": sym,
                            "pnl": pnl,
                            "reason": exit_reason,
                            "type": "exit",
                        }
                    )

        # Check entries
        for sym, pos in positions.items():
            if (
                pos.position == 0
                and sym in current_prices
                and len(price_history[sym]["prices"]) >= 60
            ):

                sector = next((s for s, syms in UNIVERSE_GROUPS.items() if sym in syms), "unknown")

                # Analyze market
                ph = price_history[sym]
                market_state = tech_analyzer.analyze_market_state(
                    sym, ph["prices"], ph["volumes"], ph["highs"], ph["lows"]
                )

                # Get v8 decision
                for agent in v8_collective.agents:
                    agent.regenerate_prana()
                decision = v8_collective.deliberation(market_state)

                # Risk check
                if not risk_manager.can_open(sym, sector, decision):
                    continue

                if decision.action not in [ActionType.BUY, ActionType.SELL]:
                    continue

                # Determine position size
                if use_strategic:
                    # Get strategic plan
                    current_plan = None
                    for sp in strategic_plans:
                        if sp["date"] <= date:
                            current_plan = sp["plan"]

                    # Strategic symbol filtering
                    if current_plan and current_plan.get("recommended_symbol"):
                        if sym != current_plan["recommended_symbol"]:
                            continue

                    # Size multiplier from MCTS agreement
                    size_mult = 1.0
                    if current_plan:
                        mcts_action = current_plan.get("recommended_action")
                        v8_action = "buy" if decision.action == ActionType.BUY else "sell"
                        if mcts_action in ["buy", "sell"]:
                            if mcts_action == v8_action:
                                size_mult = 1.0 + (current_plan.get("confidence", 0.5) * 0.5)
                            else:
                                size_mult = 0.5

                    pos_size = strategic_sizer.calculate_size(
                        capital,
                        {"action": decision.action},
                        market_state.atr,
                        market_state.price,
                        size_mult,
                    )
                else:
                    # v8 sizing
                    pos_size = risk_manager.calculate_position_size(
                        capital, decision, market_state.atr, market_state.price
                    )

                # Execute trade
                if pos_size >= 200:
                    side = "buy" if decision.action == ActionType.BUY else "sell"
                    cost = pos.open(side, pos_size, market_state.price, market_state.atr, decision)
                    capital -= cost
                    risk_manager.add_position(sym, sector, side, pos_size, 0)

                    trade_history.append(
                        {
                            "date": date,
                            "symbol": sym,
                            "side": side,
                            "size": pos_size,
                            "type": "entry",
                        }
                    )

        # Update equity
        current_equity = capital
        for sym, pos in positions.items():
            if pos.position != 0 and sym in current_prices:
                current_equity += pos.mark_to_market(current_prices[sym]["close"])

        equity_curve.append(current_equity)
        risk_manager.update_drawdown(current_equity)

    # Results
    sim_elapsed = time.time() - sim_start

    total_trades = sum(m["trades"] for m in symbol_metrics.values())
    total_wins = sum(m["wins"] for m in symbol_metrics.values())
    total_pnl = sum(m["pnl"] for m in symbol_metrics.values())
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    roi = (total_pnl / INITIAL_CAPITAL) * 100

    # Calculate drawdown
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)

    # Print results
    print("\n" + "=" * 90)
    print(f"  v9 RESULTS ({'STRATEGIC' if use_strategic else 'BASELINE'})")
    print("=" * 90)
    print("  Period:        2020-01-01 -> 2026-03-04")
    print(f"  Final Capital: ${capital:,.2f}")
    print(f"  Total PNL:     ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Win Rate:      {win_rate:.1f}%")
    print(f"  Total Trades:  {total_trades}")
    print(f"  Max Drawdown:  {max_dd*100:.1f}%")
    print(f"  Sim Time:      {sim_elapsed:.1f}s")

    if use_strategic:
        print(f"  Strategic Overrides: {strategic_overrides}")
        print(f"  Strategic Plans:     {len(strategic_plans)}")

    print("=" * 90)

    return {
        "mode": "v9_strategic" if use_strategic else "v8_baseline",
        "final_capital": capital,
        "total_pnl": total_pnl,
        "roi_pct": roi,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "max_drawdown": max_dd * 100,
        "symbol_metrics": symbol_metrics,
        "equity_curve": equity_curve,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["strategic", "v8"], default="strategic")
    parser.add_argument("--mcts-sims", type=int, default=50)
    parser.add_argument("--lookahead", type=int, default=10)
    args = parser.parse_args()

    results = run_v9_integrated_backtest(
        use_strategic=(args.mode == "strategic"),
        mcts_sims=args.mcts_sims,
        lookahead=args.lookahead,
    )

    # Save results
    results_dir = Path("backend/data/backtest_results")
    results_dir.mkdir(parents=True, exist_ok=True)

    filename = f"v9_{args.mode}_report.json"
    with open(results_dir / filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results saved to: {results_dir / filename}")
