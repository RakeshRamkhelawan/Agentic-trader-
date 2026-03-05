"""
v11 Conscious Trader Backtest
Integrates Chitta (persistent memory) + Ahamkara (self-awareness)

Implements true 'consciousness' for trading:
- Learns from past trades (samskaras)
- Self-reflects before decisions
- Has intrinsic motivation (PnL max, DD < 8%)
- Pauses when impaired (anxiety/loss streaks)
"""

import warnings
warnings.filterwarnings('ignore')

import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# v8 components
from backend.scripts.run_v8_symbiotic_backtest import (
    TechnicalAnalyzer, CollectiveConsciousness,
    SymbioticRiskManager, Position, MarketState,
    ActionType, INITIAL_CAPITAL, SYMBOL_MAP, UNIVERSE_GROUPS,
    download_data
)

# v11 Conscious components
from backend.core.conscious.chitta_memory import ChittaMemory, TradeExperience
from backend.core.conscious.ahamkara import AhamkaraMetaAgent

# Audit
from backend.core.audit.trade_audit_logger import TradeAuditLogger


class ConsciousPosition(Position):
    """Position with conscious tracking"""
    
    def __init__(self):
        super().__init__()
        self.quality_score: float = 0.0
        self.conscious_context: Dict[str, Any] = {}
    
    def open_conscious(
        self,
        side: str,
        size_usd: float,
        price: float,
        atr: float,
        decision: Any,
        conscious_context: Dict[str, Any]
    ) -> float:
        """Open position with conscious context"""
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
        
        self.quality_score = conscious_context.get('quality_score', 0.5)
        self.conscious_context = conscious_context
        
        # Dynamic stops based on anxiety
        anxiety = conscious_context.get('anxiety_level', 0.5)
        if anxiety > 0.5:
            trailing_mult = 2.5  # Wider stops when anxious
        else:
            trailing_mult = 1.8
        
        tp_mult = 3.5
        
        if side == "buy":
            self.stop_price = price - atr * trailing_mult
            self.tp_price = price + atr * tp_mult
        else:
            self.stop_price = price + atr * trailing_mult
            self.tp_price = price - atr * tp_mult
        
        self.bars_in_trade = 0
        
        return size_usd * cost_pct


def run_v11_conscious_backtest() -> Dict[str, Any]:
    """Run v11 conscious trader backtest"""
    print("=" * 90)
    print("  v11 CONSCIOUS TRADER BACKTEST")
    print("=" * 90)
    print("  Features:")
    print("    - Chitta: Persistent memory (learns from past)")
    print("    - Ahamkara: Self-awareness + intrinsic motivation")
    print("    - Goal: Max PnL with DD < 8%")
    print("    - Auto-pause: Loss streaks, high anxiety, DD > 6%")
    print("=" * 90)
    
    # Initialize conscious components
    print("\n[INIT] Initializing conscious components...")
    audit_logger = TradeAuditLogger(output_dir="backend/data/audit_logs")
    chitta = ChittaMemory(storage_path="backend/data/conscious_memory")
    ahamkara = AhamkaraMetaAgent()
    
    print(f"  [CHITTA] Loaded {len(chitta.trades)} past trades")
    print(f"  [AHAMKARA] Self-awareness active")
    
    # v8 components
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
    print(f"  Loaded {len(all_data)} symbols, {len(sorted_dates)} days")
    
    # Initialize tracking
    positions = {sym: ConsciousPosition() for sym in all_data.keys()}
    price_history = {sym: {"prices": [], "volumes": [], "highs": [], "lows": []} 
                     for sym in all_data.keys()}
    
    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_history = []
    
    active_trades: Dict[str, str] = {}
    
    # Simulation
    print("\n[RUN] Starting conscious simulation...")
    sim_start = time.time()
    total_days = len(sorted_dates)
    progress_interval = max(1, total_days // 20)
    
    pause_active = False
    pause_reason = ""
    
    for day_idx, date in enumerate(sorted_dates):
        if day_idx % progress_interval == 0:
            pct = (day_idx / total_days) * 100
            elapsed = time.time() - sim_start
            status = "PAUSED" if pause_active else "ACTIVE"
            print(f"  [{pct:5.1f}%] Day {day_idx}/{total_days} | "
                  f"Capital: ${capital:,.0f} | Status: {status} | Time: {elapsed:.0f}s")
        
        # Update Chitta drawdown tracking only (not Ahamkara every iteration)
        current_equity = capital
        for sym, pos in positions.items():
            if pos.position != 0 and sym in all_data:
                bars = all_data[sym]
                bar = next((b for b in bars if b["date"] == date), None)
                if bar:
                    current_equity += pos.mark_to_market(bar["close"])
        
        # Only update Ahamkara state periodically or on trade events
        chitta.update_drawdown(current_equity)
        
        # Check if should pause
        should_pause, reason = ahamkara.should_pause(drawdown_limit=0.08)
        if should_pause and not pause_active:
            pause_active = True
            pause_reason = reason
            print(f"    [AHAMKARA] PAUSED: {reason}")
        elif not should_pause and pause_active:
            pause_active = False
            pause_reason = ""
            print(f"    [AHAMKARA] RESUMED")
        
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
        
        # Check exits (always, even when paused)
        for sym, pos in positions.items():
            if pos.position != 0 and sym in current_prices:
                bar = current_prices[sym]
                pos.bars_in_trade += 1
                pos.update_trailing(bar["close"])
                
                exit_reason = pos.check_exit(bar["close"])
                if exit_reason:
                    # Calculate PnL
                    gross_pnl = (bar["close"] - pos.entry_price) * pos.position if pos.position > 0 else \
                                (pos.entry_price - bar["close"]) * abs(pos.position)
                    exit_cost = abs(pos.position * bar["close"]) * 0.0013
                    net_pnl = gross_pnl - exit_cost
                    
                    capital += net_pnl
                    risk_manager.remove_position(sym)
                    
                    # Store in Chitta memory
                    trade_exp = TradeExperience(
                        trade_id=active_trades.get(sym, 'unknown'),
                        timestamp=datetime.now().isoformat(),
                        symbol=sym,
                        side=pos.side,
                        entry_price=pos.entry_price,
                        exit_price=bar["close"],
                        size=abs(pos.position) * pos.entry_price,
                        net_pnl=net_pnl,
                        return_pct=net_pnl / (abs(pos.position) * pos.entry_price) if pos.position != 0 else 0,
                        bars_held=pos.bars_in_trade,
                        market_regime=pos.conscious_context.get('market_regime', 'unknown'),
                        trend_1d=pos.conscious_context.get('trend_1d', 0),
                        adx=pos.conscious_context.get('adx', 25),
                        rsi=pos.conscious_context.get('rsi', 50),
                        volatility=pos.conscious_context.get('volatility', 0.02),
                        harmony_score=pos.conscious_context.get('harmony_score', 0.5),
                        confidence=pos.conscious_context.get('confidence', 0.5),
                        coherence=pos.conscious_context.get('coherence', 0.5),
                        dominant_element=pos.conscious_context.get('dominant_element', 'unknown'),
                        guna_dominant=pos.conscious_context.get('guna_dominant', 'unknown'),
                        is_maya=pos.conscious_context.get('is_maya', False),
                        exit_reason=exit_reason
                    )
                    chitta.store_trade(trade_exp)
                    ahamkara.record_trade_result({'net_pnl': net_pnl})
                    
                    # Log exit
                    if sym in active_trades:
                        audit_logger.log_trade_exit(
                            trade_id=active_trades[sym],
                            symbol=sym,
                            position=pos,
                            exit_price=bar["close"],
                            exit_reason=exit_reason,
                            gross_pnl=gross_pnl,
                            net_pnl=net_pnl
                        )
                        del active_trades[sym]
                    
                    trade_history.append({
                        "date": date, "symbol": sym, "pnl": net_pnl,
                        "reason": exit_reason, "type": "exit"
                    })
                    
                    pos.close(bar["close"])
        
        # Skip entries if paused
        if pause_active:
            equity_curve.append(current_equity)
            continue
        
        # Check entries (only if not paused)
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
                
                # Get v8 collective decision
                decision = v8_collective.deliberation(market_state)
                
                # Retrieve similar setups from Chitta
                similar = chitta.retrieve_similar_setups(market_state, top_k=5)
                similar_performance = None
                if similar:
                    avg_pnl = sum(t.net_pnl for t in similar) / len(similar)
                    similar_performance = f"Similar setups avg PnL: ${avg_pnl:.2f}"
                
                # Get memory reflection
                memory_insights = chitta.reflect_recent(5)
                
                # Ahamkara conscious decision
                conscious_decision = ahamkara.decide_action(
                    market_state, decision, memory_insights
                )
                
                # Log risk check
                audit_logger.log_risk_check(
                    symbol=sym,
                    sector=sector,
                    decision=decision,
                    risk_manager=risk_manager,
                    passed=conscious_decision['action'] != 'HOLD',
                    rejection_reason=conscious_decision['reason'] if conscious_decision['action'] == 'HOLD' else ""
                )
                
                if conscious_decision['action'] == 'HOLD':
                    continue
                
                # Calculate position size (reduced by anxiety)
                base_size = risk_manager.calculate_position_size(
                    capital, decision, market_state.atr, market_state.price
                )
                anxiety_modifier = conscious_decision.get('anxiety_modifier', 1.0)
                final_size = base_size * anxiety_modifier
                
                # Execute
                if final_size >= 200:
                    side = "buy" if decision.action == ActionType.BUY else "sell"
                    
                    conscious_context = {
                        'quality_score': conscious_decision['confidence'],
                        'anxiety_level': ahamkara.state.anxiety_level,
                        'harmony_score': getattr(decision, 'harmony_score', 0.5),
                        'confidence': getattr(decision, 'confidence', 0.5),
                        'coherence': getattr(decision, 'coherence', 0.5),
                        'dominant_element': str(getattr(decision, 'dominant_element', 'unknown')),
                        'guna_dominant': getattr(decision, 'guna_state', {}).dominant() if hasattr(getattr(decision, 'guna_state', {}), 'dominant') else 'unknown',
                        'is_maya': getattr(decision, 'is_maya', False),
                        'market_regime': 'unknown',  # Would need regime detection
                        'trend_1d': getattr(market_state, 'trend_1d', 0),
                        'adx': getattr(market_state, 'adx', 25),
                        'rsi': getattr(market_state, 'rsi', 50),
                        'volatility': getattr(market_state, 'volatility', 0.02)
                    }
                    
                    cost = pos.open_conscious(
                        side, final_size, market_state.price, 
                        market_state.atr, decision, conscious_context
                    )
                    capital -= cost
                    risk_manager.add_position(sym, sector, side, final_size, 0)
                    
                    # Log execution
                    trade_id = audit_logger.log_trade_execution(
                        decision=decision,
                        position=pos,
                        market_state=market_state,
                        collective_decision_id=getattr(decision, 'audit_id', 'unknown')
                    )
                    active_trades[sym] = trade_id
                    
                    trade_history.append({
                        "date": date, "symbol": sym, "side": side,
                        "size": final_size, "type": "entry",
                        "conscious": True
                    })
        
        equity_curve.append(current_equity)
        risk_manager.update_drawdown(current_equity)
    
    # Results
    sim_elapsed = time.time() - sim_start
    
    total_trades = len([t for t in trade_history if t['type'] == 'exit'])
    winning_trades = len([t for t in trade_history if t['type'] == 'exit' and t['pnl'] > 0])
    total_pnl = sum(t['pnl'] for t in trade_history if t['type'] == 'exit')
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    roi = (total_pnl / INITIAL_CAPITAL) * 100
    
    # Drawdown
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)
    
    # Save results
    audit_path = audit_logger.save_session()
    chitta_summary = chitta.get_summary()
    ahamkara_summary = ahamkara.get_summary()
    
    print("\n" + "=" * 90)
    print("  v11 CONSCIOUS TRADER RESULTS")
    print("=" * 90)
    print(f"  Period:        2020-01-01 -> 2026-03-04")
    print(f"  Final Capital: ${capital:,.2f}")
    print(f"  Total PnL:     ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Win Rate:      {win_rate:.1f}%")
    print(f"  Total Trades:  {total_trades}")
    print(f"  Max Drawdown:  {max_dd*100:.1f}%")
    print(f"  Sim Time:      {sim_elapsed:.1f}s")
    print("-" * 90)
    print(f"  [CHITTA] Memory:")
    print(f"    - Trades stored: {chitta_summary['total_trades_stored']}")
    print(f"    - Active strategies: {chitta_summary['active_strategies']}")
    print(f"    - Overall win rate: {chitta_summary['overall_win_rate']:.1%}")
    print(f"  [AHAMKARA] Self-awareness:")
    print(f"    - Reflections: {ahamkara_summary['reflections_count']}")
    print(f"    - Current anxiety: {ahamkara.state.anxiety_level:.0%}")
    print(f"    - Current confidence: {ahamkara.state.confidence_level:.0%}")
    print("=" * 90)
    
    return {
        "final_capital": capital,
        "total_pnl": total_pnl,
        "roi_pct": roi,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "max_drawdown": max_dd * 100,
        "chitta_summary": chitta_summary,
        "ahamkara_summary": ahamkara_summary,
        "audit_path": str(audit_path)
    }


if __name__ == "__main__":
    results = run_v11_conscious_backtest()
    
    # Save results
    results_dir = Path("backend/data/backtest_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    with open(results_dir / "v11_conscious_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  Results saved to: {results_dir / 'v11_conscious_results.json'}")
