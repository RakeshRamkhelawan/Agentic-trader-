"""
v8 Backtest with Full Audit Logging
Every agent decision, reasoning, and trade is logged for analysis
"""

import warnings

warnings.filterwarnings("ignore")

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Audit logger
from backend.core.audit.trade_audit_logger import TradeAuditLogger

# v8 components
from backend.scripts.run_v8_symbiotic_backtest import (
    INITIAL_CAPITAL,
    SYMBOL_MAP,
    UNIVERSE_GROUPS,
    ActionType,
    AgentSignal,
    AirAgent,
    CollectiveConsciousness,
    CollectiveDecision,
    EarthAgent,
    ElementalAgent,
    EtherAgent,
    FireAgent,
    GunaVector,
    MarketState,
    Position,
    SymbioticRiskManager,
    TechnicalAnalyzer,
    WaterAgent,
    download_data,
)


class AuditedCollectiveConsciousness(CollectiveConsciousness):
    """CollectiveConsciousness with audit logging"""

    def __init__(self, audit_logger: TradeAuditLogger):
        super().__init__()
        self.audit = audit_logger
        self.current_market: MarketState = None

    def deliberation(self, market: MarketState) -> CollectiveDecision:
        """Run deliberation with full audit trail"""
        self.current_market = market

        # Step 1: Collect agent signals (with audit)
        signals = []
        for agent in self.agents:
            signal = agent.analyze(market)
            signals.append(signal)

            # Log each agent's decision
            self.audit.log_agent_signal(
                agent_name=agent.name,
                agent_element=agent.element.value,
                market_state=market,
                signal=signal,
                prana_level=agent.prana,
                guna_state=(
                    {
                        "sattva": agent.guna.sattva,
                        "rajas": agent.guna.rajas,
                        "tamas": agent.guna.tamas,
                    }
                    if hasattr(agent, "guna")
                    else {}
                ),
            )

            # Regenerate prana
            agent.regenerate_prana(1.0)

        # Step 2: Ether harmonizes
        decision = self.ether.harmonize_signals(signals, market)

        # Step 3: Log collective decision
        decision_id = self.audit.log_collective_decision(
            agent_signals=signals, market_state=market, decision=decision, mcts_result=None
        )

        # Update state
        self.collective_guna = decision.guna_state
        self.harmony_history.append(decision.harmony_score)
        self.decision_history.append(decision)

        # Store decision ID for later reference
        decision.audit_id = decision_id

        return decision


def run_v8_audit_backtest() -> Dict[str, Any]:
    """
    Run v8 backtest with complete audit trail
    """
    print("=" * 90)
    print("  v8 SYMBIOTIC BACKTEST - FULL AUDIT MODE")
    print("=" * 90)
    print("  Every decision will be logged for analysis")
    print("=" * 90)

    # Initialize audit logger
    audit_logger = TradeAuditLogger(output_dir="backend/data/audit_logs")

    # Initialize components
    print("\n[INIT] Loading audited components...")
    tech_analyzer = TechnicalAnalyzer()
    v8_collective = AuditedCollectiveConsciousness(audit_logger)
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
    print(f"  Audit log session: {audit_logger.session_id}")

    # Initialize tracking
    positions = {sym: Position() for sym in all_data.keys()}
    price_history = {
        sym: {"prices": [], "volumes": [], "highs": [], "lows": []} for sym in all_data.keys()
    }

    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_history = []
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} for sym in all_data.keys()}

    # Track active trades for audit
    active_trades: Dict[str, str] = {}  # symbol -> trade_id

    # Simulation loop
    print("\n[RUN] Starting audited simulation...")
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

                exit_reason = pos.check_exit(bar["close"])
                if exit_reason:
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

                    # Log trade exit
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
                        }
                    )

                    # Close position
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

                # Get collective decision (with audit logging inside)
                decision = v8_collective.deliberation(market_state)
                decision_id = getattr(decision, "audit_id", "unknown")

                # Risk check (with audit)
                can_open = risk_manager.can_open(sym, sector, decision)

                audit_logger.log_risk_check(
                    symbol=sym,
                    sector=sector,
                    decision=decision,
                    risk_manager=risk_manager,
                    passed=can_open,
                    rejection_reason=(
                        ""
                        if can_open
                        else f"Harmony: {decision.harmony_score:.2f}, Maya: {decision.is_maya}"
                    ),
                )

                if not can_open:
                    continue

                if decision.action not in [ActionType.BUY, ActionType.SELL]:
                    continue

                # Position sizing
                pos_size = risk_manager.calculate_position_size(
                    capital, decision, market_state.atr, market_state.price
                )

                # Log sizing
                audit_logger.log_position_sizing(
                    symbol=sym,
                    capital=capital,
                    decision=decision,
                    atr=market_state.atr,
                    price=market_state.price,
                    calculated_size=pos_size,
                    final_size=pos_size,
                    strategic_mult=1.0,
                )

                # Execute trade
                if pos_size >= 200:
                    side = "buy" if decision.action == ActionType.BUY else "sell"
                    cost = pos.open(side, pos_size, market_state.price, market_state.atr, decision)
                    capital -= cost
                    risk_manager.add_position(sym, sector, side, pos_size, 0)

                    # Log trade execution
                    trade_id = audit_logger.log_trade_execution(
                        decision=decision,
                        position=pos,
                        market_state=market_state,
                        collective_decision_id=decision_id,
                    )
                    active_trades[sym] = trade_id

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

    # Drawdown
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)

    # Save audit log
    audit_path = audit_logger.save_session()

    # Print results
    print("\n" + "=" * 90)
    print("  v8 AUDIT BACKTEST RESULTS")
    print("=" * 90)
    print("  Period:        2020-01-01 -> 2026-03-04")
    print(f"  Final Capital: ${capital:,.2f}")
    print(f"  Total PNL:     ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Win Rate:      {win_rate:.1f}%")
    print(f"  Total Trades:  {total_trades}")
    print(f"  Max Drawdown:  {max_dd*100:.1f}%")
    print(f"  Sim Time:      {sim_elapsed:.1f}s")
    print("-" * 90)

    # Audit summary
    summary = audit_logger.get_summary()
    print(f"\n  AUDIT SUMMARY (Session {audit_logger.session_id})")
    print(f"  - Agent decisions logged:     {summary['agent_decisions']}")
    print(f"  - Collective deliberations:   {summary['collective_deliberations']}")
    print(f"  - Risk checks performed:      {summary['risk_checks']}")
    print(f"  - Trades executed:            {summary['trades_executed']}")
    print(f"  - Trades exited:              {summary['trades_exited']}")
    print(f"  - Rejection rate:             {summary['rejection_rate']:.1%}")
    print(f"\n  Audit log saved to: {audit_path}")
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
        "audit_summary": summary,
        "audit_path": audit_path,
    }


if __name__ == "__main__":
    results = run_v8_audit_backtest()

    # Also save results summary
    results_dir = Path("backend/data/backtest_results")
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(results_dir / "v8_audit_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results summary saved to: {results_dir / 'v8_audit_results.json'}")
