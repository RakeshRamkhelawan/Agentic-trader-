"""
v10 Guardian Backtest - Quality over Quantity
Implements audit-driven improvements:
- Hard filters (harmony > 0.60, confidence > 0.45)
- Dynamic position sizing
- Optimized exit parameters
"""

import warnings

warnings.filterwarnings("ignore")

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Audit
from backend.core.audit.trade_audit_logger import TradeAuditLogger

# v10 Guardian
from backend.core.v10_guardian import V10Config, V10Guardian

# v8 components
from backend.scripts.run_v8_symbiotic_backtest import (
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
)


class V10Position(Position):
    """Position with v10 exit parameters"""

    def __init__(self):
        super().__init__()
        self.quality_score: float = 0.0
        self.entry_harmony: float = 0.0

    def open_v10(
        self,
        side: str,
        size_usd: float,
        price: float,
        atr: float,
        exit_params: Dict[str, float],
        decision: Any,
    ) -> float:
        """Open position with v10 parameters"""
        tx_fee = 0.0010
        slippage = 0.0003
        cost_pct = tx_fee + slippage
        net_size = size_usd * (1.0 - cost_pct)

        self.side = side
        self.position = net_size / price if side == "buy" else -net_size / price
        self.entry_price = price
        self.atr = atr
        self.highest_price = price
        self.lowest_price = price

        # v10 parameters
        self.quality_score = getattr(decision, "quality_score", 0.5)
        self.entry_harmony = getattr(decision, "harmony_score", 0.5)

        # Dynamic stops
        trailing_mult = exit_params.get("trailing_mult", 2.0)
        tp_mult = exit_params.get("tp_mult", 3.5)

        if side == "buy":
            self.stop_price = price - atr * trailing_mult
            self.tp_price = price + atr * tp_mult
        else:
            self.stop_price = price + atr * trailing_mult
            self.tp_price = price - atr * tp_mult

        self.bars_in_trade = 0
        self.max_hold = exit_params.get("max_hold", 10)

        return size_usd * cost_pct

    def check_exit_v10(self, price: float) -> tuple:
        """Check exit with v10 logic, returns (should_exit, reason)"""
        # Standard checks
        if self.position > 0:
            if price <= self.stop_price:
                return True, "trailing_stop"
            if price >= self.tp_price:
                return True, "take_profit"
        elif self.position < 0:
            if price >= self.stop_price:
                return True, "trailing_stop"
            if price <= self.tp_price:
                return True, "take_profit"

        # v10: Max hold based on quality
        if self.bars_in_trade >= self.max_hold:
            return True, "max_hold"

        return False, ""


def run_v10_guardian_backtest() -> Dict[str, Any]:
    """Run v10 guardian backtest"""
    print("=" * 90)
    print("  v10 GUARDIAN BACKTEST - Quality over Quantity")
    print("=" * 90)
    print("  Filters:")
    print("    - Harmony > 0.60")
    print("    - Confidence > 0.45")
    print("    - Max 5 positions")
    print("    - Dynamic sizing: risk = 1.5% * harmony * (1 - vol)")
    print("=" * 90)

    # Initialize
    audit_logger = TradeAuditLogger(output_dir="backend/data/audit_logs")
    guardian = V10Guardian(V10Config())

    print("\n[INIT] Loading components...")
    tech_analyzer = TechnicalAnalyzer()
    v8_collective = CollectiveConsciousness()
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
    positions = {sym: V10Position() for sym in all_data.keys()}
    price_history = {
        sym: {"prices": [], "volumes": [], "highs": [], "lows": []} for sym in all_data.keys()
    }

    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_history = []
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} for sym in all_data.keys()}

    active_trades: Dict[str, str] = {}

    # Simulation
    print("\n[RUN] Starting v10 simulation...")
    sim_start = time.time()
    total_days = len(sorted_dates)
    progress_interval = max(1, total_days // 20)

    for day_idx, date in enumerate(sorted_dates):
        if day_idx % progress_interval == 0:
            pct = (day_idx / total_days) * 100
            elapsed = time.time() - sim_start
            print(
                f"  [{pct:5.1f}%] Day {day_idx}/{total_days} | "
                f"Capital: ${capital:,.0f} | Time: {elapsed:.0f}s"
            )

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

                should_exit, exit_reason = pos.check_exit_v10(bar["close"])
                if should_exit:
                    # Calculate PnL
                    gross_pnl = (
                        (bar["close"] - pos.entry_price) * pos.position
                        if pos.position > 0
                        else (pos.entry_price - bar["close"]) * abs(pos.position)
                    )
                    exit_cost = abs(pos.position * bar["close"]) * 0.0013
                    net_pnl = gross_pnl - exit_cost

                    capital += net_pnl
                    risk_manager.remove_position(sym)

                    # Log exit
                    if sym in active_trades:
                        audit_logger.log_trade_exit(
                            trade_id=active_trades[sym],
                            symbol=sym,
                            position=pos,
                            exit_price=bar["close"],
                            exit_reason=exit_reason,
                            gross_pnl=gross_pnl,
                            net_pnl=net_pnl,
                        )
                        del active_trades[sym]

                    symbol_metrics[sym]["trades"] += 1
                    if net_pnl > 0:
                        symbol_metrics[sym]["wins"] += 1
                    symbol_metrics[sym]["pnl"] += net_pnl

                    trade_history.append(
                        {
                            "date": date,
                            "symbol": sym,
                            "pnl": net_pnl,
                            "reason": exit_reason,
                            "type": "exit",
                            "quality_score": pos.quality_score,
                        }
                    )

                    pos.close(bar["close"])

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

                # Get collective decision
                decision = v8_collective.deliberation(market_state)

                # v10 Guardian check
                active_count = len([p for p in positions.values() if p.position != 0])
                should_trade, reason, quality_score = guardian.should_trade(
                    decision, market_state, active_count
                )

                # Log risk check
                audit_logger.log_risk_check(
                    symbol=sym,
                    sector=sector,
                    decision=decision,
                    risk_manager=risk_manager,
                    passed=should_trade,
                    rejection_reason=reason if not should_trade else "",
                )

                if not should_trade:
                    continue

                # Get v10 exit parameters
                exit_params = guardian.get_exit_params(decision, market_state)

                # Calculate base size from risk manager
                base_size = risk_manager.calculate_position_size(
                    capital, decision, market_state.atr, market_state.price
                )

                # v10 dynamic sizing
                v10_size = guardian.calculate_position_size(
                    capital, decision, market_state, base_size
                )

                # Log sizing
                audit_logger.log_position_sizing(
                    symbol=sym,
                    capital=capital,
                    decision=decision,
                    atr=market_state.atr,
                    price=market_state.price,
                    calculated_size=base_size,
                    final_size=v10_size,
                    strategic_mult=quality_score,
                )

                # Execute
                if v10_size >= 200:
                    side = "buy" if decision.action == ActionType.BUY else "sell"
                    cost = pos.open_v10(
                        side,
                        v10_size,
                        market_state.price,
                        market_state.atr,
                        exit_params,
                        decision,
                    )
                    capital -= cost
                    risk_manager.add_position(sym, sector, side, v10_size, 0)

                    # Log execution
                    trade_id = audit_logger.log_trade_execution(
                        decision=decision,
                        position=pos,
                        market_state=market_state,
                        collective_decision_id=getattr(decision, "audit_id", "unknown"),
                    )
                    active_trades[sym] = trade_id

                    trade_history.append(
                        {
                            "date": date,
                            "symbol": sym,
                            "side": side,
                            "size": v10_size,
                            "type": "entry",
                            "quality_score": quality_score,
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

    # Drawdown
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)

    # Save audit
    audit_path = audit_logger.save_session()

    # Guardian stats
    guardian_stats = guardian.get_stats()

    print("\n" + "=" * 90)
    print("  v10 GUARDIAN RESULTS")
    print("=" * 90)
    print("  Period:        2020-01-01 -> 2026-03-04")
    print(f"  Final Capital: ${capital:,.2f}")
    print(f"  Total PnL:     ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Win Rate:      {win_rate:.1f}%")
    print(f"  Total Trades:  {total_trades}")
    print(f"  Max Drawdown:  {max_dd*100:.1f}%")
    print(f"  Sim Time:      {sim_elapsed:.1f}s")
    print("-" * 90)
    print("  v10 Guardian Statistics:")
    print(f"    Total checked:    {guardian_stats['total_checked']}")
    print(f"    Passed:           {guardian_stats['passed']} ({guardian_stats['pass_rate']:.1%})")
    print(f"    Rejected:         {guardian_stats['total_checked'] - guardian_stats['passed']}")
    print(f"    - Harmony too low: {guardian_stats['harmony_too_low']}")
    print(f"    - Confidence low:  {guardian_stats['confidence_too_low']}")
    print(f"    - Maya detected:   {guardian_stats['maya_detected']}")
    print(f"    - Max positions:   {guardian_stats['max_positions']}")
    print("=" * 90)

    return {
        "final_capital": capital,
        "total_pnl": total_pnl,
        "roi_pct": roi,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "max_drawdown": max_dd * 100,
        "symbol_metrics": symbol_metrics,
        "equity_curve": equity_curve,
        "guardian_stats": guardian_stats,
        "audit_path": str(audit_path),
    }


if __name__ == "__main__":
    results = run_v10_guardian_backtest()

    # Save results
    results_dir = Path("backend/data/backtest_results")
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(results_dir / "v10_guardian_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results saved to: {results_dir / 'v10_guardian_results.json'}")
