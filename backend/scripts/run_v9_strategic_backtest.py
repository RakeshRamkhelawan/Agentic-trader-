"""
v9 Strategic Backtest - MCTS-enhanced v8 Symbiotic Agents

Uses StrategicEtherAgent with 10-step lookahead for enhanced decision making.

Usage:
    python run_v9_strategic_backtest.py --mcts-iter=1000
"""

import warnings
warnings.filterwarnings('ignore')

import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

# v8 components
from backend.scripts.run_v8_symbiotic_backtest import (
    TechnicalAnalyzer,
    AirAgent, FireAgent, WaterAgent, EarthAgent, EtherAgent,
    SymbioticRiskManager, Position, MarketState,
    ActionType, INITIAL_CAPITAL, SYMBOL_MAP, UNIVERSE_GROUPS,
    download_data, GunaVector, AgentSignal, CollectiveDecision
)

# v9 Strategic Ether
from backend.agents.strategic.ether_strategic import StrategicEtherAgent, StrategicCollectiveDecision


class StrategicCollectiveConsciousness:
    """
    v8 Collective Consciousness with Strategic Ether
    """
    
    def __init__(self, use_mcts: bool = True, mcts_iterations: int = 500):
        # Elemental Agents (v8)
        self.air = AirAgent()
        self.fire = FireAgent()
        self.water = WaterAgent()
        self.earth = EarthAgent()
        
        # Ether: v8 or Strategic (v9)
        if use_mcts:
            print(f"  [v9] Strategic Ether Agent (MCTS {mcts_iterations} iter)")
            self.ether = StrategicEtherAgent(mcts_iterations=mcts_iterations)
        else:
            print("  [v8] Standard Ether Agent")
            self.ether = EtherAgent()
        
        self.agents = [self.air, self.fire, self.water, self.earth]
        
        # State tracking
        self.collective_guna = GunaVector()
        self.decision_count = 0
    
    def deliberation(self, market: MarketState) -> CollectiveDecision:
        """Run symbiotic deliberation with strategic overlay"""
        # Collect agent signals
        signals = []
        for agent in self.agents:
            signal = agent.analyze(market)
            signals.append(signal)
            agent.regenerate_prana(1.0)
        
        # Ether harmonizes (with or without MCTS)
        decision = self.ether.harmonize_signals(signals, market)
        
        self.collective_guna = decision.guna_state
        self.decision_count += 1
        
        return decision
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collective stats"""
        if isinstance(self.ether, StrategicEtherAgent):
            return {
                'decisions': self.decision_count,
                'mcts_stats': self.ether.get_stats()
            }
        return {'decisions': self.decision_count}


def run_v9_strategic_backtest(
    use_mcts: bool = True,
    mcts_iterations: int = 500
) -> Dict[str, Any]:
    """
    Run v9 strategic backtest
    
    Args:
        use_mcts: Enable MCTS strategic layer
        mcts_iterations: Number of MCTS simulations per decision
    """
    print("=" * 90)
    print("  v9 STRATEGIC BACKTEST (MCTS-enhanced)")
    print("=" * 90)
    print(f"  Mode: {'MCTS Strategic' if use_mcts else 'v8 Baseline'}")
    if use_mcts:
        print(f"  MCTS Iterations: {mcts_iterations}")
    print("=" * 90)
    
    # Initialize components
    print("\n[INIT] Loading components...")
    tech_analyzer = TechnicalAnalyzer()
    v9_collective = StrategicCollectiveConsciousness(
        use_mcts=use_mcts,
        mcts_iterations=mcts_iterations
    )
    risk_manager = SymbioticRiskManager(max_total_positions=5, max_per_sector=2)
    
    # Load data
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
    price_history = {sym: {"prices": [], "volumes": [], "highs": [], "lows": []} 
                     for sym in all_data.keys()}
    
    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_history = []
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} 
                      for sym in all_data.keys()}
    
    # Simulation loop
    print("\n[RUN] Starting simulation...")
    sim_start = time.time()
    total_days = len(sorted_dates)
    progress_interval = max(1, total_days // 20)
    
    for day_idx, date in enumerate(sorted_dates):
        if day_idx % progress_interval == 0:
            pct = (day_idx / total_days) * 100
            elapsed = time.time() - sim_start
            print(f"  [{pct:5.1f}%] Day {day_idx}/{total_days} | "
                  f"Capital: ${capital:,.0f} | Time: {elapsed:.0f}s")
        
        # Update prices
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
        
        # Check exits
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
                    trade_history.append({
                        "date": date, "symbol": sym, "pnl": pnl,
                        "reason": exit_reason, "type": "exit"
                    })
        
        # Check entries
        for sym, pos in positions.items():
            if pos.position == 0 and sym in current_prices and \
               len(price_history[sym]["prices"]) >= 60:
                
                sector = next(
                    (s for s, syms in UNIVERSE_GROUPS.items() if sym in syms),
                    "unknown"
                )
                
                # Analyze market
                ph = price_history[sym]
                market_state = tech_analyzer.analyze_market_state(
                    sym, ph["prices"], ph["volumes"],
                    ph["highs"], ph["lows"]
                )
                
                # v9 Strategic deliberation
                decision = v9_collective.deliberation(market_state)
                
                # Risk check
                if not risk_manager.can_open(sym, sector, decision):
                    continue
                
                if decision.action not in [ActionType.BUY, ActionType.SELL]:
                    continue
                
                # Position sizing
                pos_size = risk_manager.calculate_position_size(
                    capital, decision, market_state.atr, market_state.price
                )
                
                # Execute
                if pos_size >= 200:
                    side = "buy" if decision.action == ActionType.BUY else "sell"
                    cost = pos.open(side, pos_size, market_state.price, market_state.atr, decision)
                    capital -= cost
                    risk_manager.add_position(sym, sector, side, pos_size, 0)
                    
                    trade_history.append({
                        "date": date, "symbol": sym, "side": side,
                        "size": pos_size, "type": "entry",
                        "mcts_action": getattr(decision, 'mcts_action', 'N/A'),
                        "mcts_conf": getattr(decision, 'mcts_confidence', 0)
                    })
        
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
    
    # Drawdown
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)
    
    # Strategic stats
    collective_stats = v9_collective.get_stats()
    
    print("\n" + "=" * 90)
    print(f"  v9 RESULTS ({'MCTS' if use_mcts else 'v8'})")
    print("=" * 90)
    print(f"  Period:        2020-01-01 -> 2026-03-04")
    print(f"  Final Capital: ${capital:,.2f}")
    print(f"  Total PNL:     ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Win Rate:      {win_rate:.1f}%")
    print(f"  Total Trades:  {total_trades}")
    print(f"  Max Drawdown:  {max_dd*100:.1f}%")
    print(f"  Sim Time:      {sim_elapsed:.1f}s")
    
    if use_mcts and 'mcts_stats' in collective_stats:
        mcts_stats = collective_stats['mcts_stats']
        print(f"\n  MCTS Statistics:")
        print(f"    Runs:          {mcts_stats.get('mcts_runs', 0)}")
        print(f"    Agreements:    {mcts_stats.get('agreements', 0)}")
        print(f"    Overrides:     {mcts_stats.get('mcts_override', 0)}")
        print(f"    Agreement Rate: {mcts_stats.get('agreement_rate', 0):.1%}")
    
    print("=" * 90)
    
    return {
        "mode": "v9_mcts" if use_mcts else "v8_baseline",
        "final_capital": capital,
        "total_pnl": total_pnl,
        "roi_pct": roi,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "max_drawdown": max_dd * 100,
        "symbol_metrics": symbol_metrics,
        "equity_curve": equity_curve,
        "collective_stats": collective_stats
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcts", action="store_true", help="Enable MCTS strategic layer")
    parser.add_argument("--mcts-iter", type=int, default=500, help="MCTS iterations per decision")
    parser.add_argument("--baseline", action="store_true", help="Run v8 baseline (no MCTS)")
    args = parser.parse_args()
    
    use_mcts = args.mcts and not args.baseline
    
    results = run_v9_strategic_backtest(
        use_mcts=use_mcts,
        mcts_iterations=args.mcts_iter
    )
    
    # Save results
    results_dir = Path("backend/data/backtest_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    mode_str = "mcts" if use_mcts else "baseline"
    filename = f"v9_{mode_str}_{args.mcts_iter}iter_report.json"
    
    with open(results_dir / filename, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  Results saved to: {results_dir / filename}")
