"""
v10 VEDASTRO-POWERED BACKTEST
==============================

Integrates VedAstro Pre-Market Orchestrator with Symbiotic Trading System.

Architecture:
    Pre-Market (08:00 UTC)
    ├── VedAstro analyzes all assets
    ├── Ranks by astrological strength
    ├── Calculates Pancha Pakshi windows
    └── Generates DailyTradingPlan
    
    Trading Hours
    ├── Check: In favorable window?
    ├── Check: Asset in top-ranked?
    └── Yes → Activate Guna Agents
        └── Execute trades

This demonstrates the proper use of VedAstro:
- NOT: "Should I trade BTC NOW?" (every second)
- YES: "Trade BTC only at 09:36-12:00 today" (strategic planning)

Key Metrics to Compare vs v8:
- Win rate (should improve - only trading favorable times)
- Drawdown (should reduce - avoiding bad periods)
- Sharpe (should improve - better risk-adjusted returns)
- Trade frequency (should reduce - quality over quantity)
"""

import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, time as time_class
import time as time_module
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

# Import v8 components
from backend.scripts.run_v8_symbiotic_backtest import (
    TechnicalAnalyzer, ElementalAgent, EtherAgent, AirAgent, FireAgent, 
    WaterAgent, EarthAgent, CollectiveConsciousness, SymbioticRiskManager,
    Position, MarketState, ActionType, ElementType, GunaVector
)

# Import VedAstro
from backend.vedastro.premarket_orchestrator import (
    VedAstroPreMarketOrchestrator, DailyTradingPlan, TradingWindow, AssetScore
)

# =============================================================================
# CONFIGURATION
# =============================================================================

START_DATE = "2020-01-01"
END_DATE = "2026-03-04"
INITIAL_CAPITAL = 100_000.0

# Risk Parameters
MAX_POSITION_FRACTION = 0.22
RISK_PER_TRADE_BASE = 0.022
MIN_CONFIDENCE = 0.47
MAX_HOLD_BARS = 30

# ATR Multipliers
ATR_SL_MULT = 1.6
ATR_TP_MULT = 4.5
ATR_TRAILING_MULT = 1.25

# Cost Simulation
TRANSACTION_FEE = 0.0010
SLIPPAGE = 0.0003

# Directories
DATA_CACHE_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_cache"
LOG_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_logs"
RESULTS_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_results"

SYMBOL_MAP = {
    "BTC/EUR": "BTC-EUR", "ETH/EUR": "ETH-EUR", "ADA/EUR": "ADA-EUR",
    "DOT/EUR": "DOT-EUR", "XRP/EUR": "XRP-EUR", "SOL/EUR": "SOL-EUR",
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "EUR/GBP": "EURGBP=X", "USD/CHF": "CHF=X", "AUD/USD": "AUDUSD=X",
    "SPX500": "^GSPC", "NAS100": "^IXIC", "GER40": "^GDAXI", "UK100": "^FTSE",
    "XAU/USD": "GC=F", "XAG/USD": "SI=F", "OIL/USD": "CL=F", "COTTON/USD": "CT=F",
}

UNIVERSE_GROUPS = {
    "crypto": ["BTC/EUR", "ETH/EUR", "ADA/EUR", "DOT/EUR", "XRP/EUR", "SOL/EUR"],
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/GBP", "USD/CHF", "AUD/USD"],
    "indices": ["SPX500", "NAS100", "GER40", "UK100"],
    "commodities": ["XAU/USD", "XAG/USD", "OIL/USD", "COTTON/USD"],
}


def download_data(platform_symbol: str, yf_ticker: str) -> List[Dict]:
    """Download and cache market data"""
    import csv
    cache_file = DATA_CACHE_DIR / f"{platform_symbol.replace('/', '_')}.csv"
    if cache_file.exists():
        rows = []
        with open(cache_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rows.append({
                        "date": row["date"],
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    })
                except (ValueError, KeyError):
                    continue
        if rows:
            return rows
    return []


# =============================================================================
# MOCK VEDASTRO FOR BACKTEST (simulated)
# =============================================================================

class MockVedAstroOrchestrator:
    """
    Mock VedAstro orchestrator for backtesting
    
    In production, this would use real VedAstro calculations.
    For backtest, we simulate the effects based on market conditions.
    """
    
    def __init__(self):
        self.daily_plans: Dict[str, DailyTradingPlan] = {}
        self.current_plan: Optional[DailyTradingPlan] = None
    
    def generate_daily_plan(self, date_str: str, symbols: List[str], 
                           market_data: Dict[str, Any]) -> DailyTradingPlan:
        """
        Generate simulated daily plan based on market conditions
        
        This mimics how VedAstro would work:
        - Strong trend days = favorable
        - High volatility = unfavorable
        - Good volume = favorable
        """
        from backend.vedastro.premarket_orchestrator import TimeWindow
        
        # Calculate day quality based on market conditions
        avg_volatility = np.mean([m.get("volatility", 0.02) for m in market_data.values()])
        avg_adx = np.mean([m.get("adx", 20) for m in market_data.values()])
        
        # Simulate Muhurtha rating
        if avg_adx > 30 and avg_volatility < 0.04:
            muhurtha_rating = 8.5
            tithi_type = "Nanda"
            is_favorable = True
        elif avg_adx > 25 and avg_volatility < 0.05:
            muhurtha_rating = 7.0
            tithi_type = "Bhadra"
            is_favorable = True
        elif avg_volatility > 0.06:
            muhurtha_rating = 3.5
            tithi_type = "Rikta"
            is_favorable = False
        else:
            muhurtha_rating = 5.5
            tithi_type = "Jaya"
            is_favorable = True
        
        # Score assets based on their trend strength
        asset_scores = []
        for symbol in symbols:
            data = market_data.get(symbol, {})
            trend_score = data.get("trend_1d", 0) * 20 + 50  # 0-100 scale
            
            score = AssetScore(
                symbol=symbol,
                overall_score=min(100, max(0, trend_score)),
                signal_strength=0.6,
                confidence=0.7,
                dasha_lord="Jupiter" if trend_score > 60 else "Saturn",
                top_yoga="Dhana Yoga" if trend_score > 70 else "None",
                muhurtha_rating=muhurtha_rating,
                pancha_pakshi_strength=0.8 if trend_score > 60 else 0.4,
                warnings=["Rikta Tithi"] if tithi_type == "Rikta" else [],
                recommendation="buy" if trend_score > 60 else "hold"
            )
            asset_scores.append(score)
        
        # Sort by score
        asset_scores.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Top assets
        top_assets = [a for a in asset_scores if a.overall_score >= 65][:5]
        avoid_assets = [a.symbol for a in asset_scores if a.overall_score < 50]
        
        # Create time windows based on day quality
        trading_windows = []
        blocked_windows = []
        
        if is_favorable and muhurtha_rating >= 7:
            # Excellent day - multiple trading windows
            trading_windows = [
                TimeWindow(time_class(9, 0), time_class(11, 0), TradingWindow.PRIME, 1.0, 
                          "Morning Eating period", "Entry/Exit"),
                TimeWindow(time_class(13, 0), time_class(15, 0), TradingWindow.GOOD, 0.9,
                          "Afternoon Ruling period", "Exit/Trim"),
                TimeWindow(time_class(15, 0), time_class(17, 0), TradingWindow.MODERATE, 0.7,
                          "Late afternoon Walking", "Monitor only"),
            ]
            blocked_windows = [
                TimeWindow(time_class(0, 0), time_class(9, 0), TradingWindow.BLOCK, 0.1,
                          "Pre-market Sleeping", "No trading"),
                TimeWindow(time_class(17, 0), time_class(23, 59), TradingWindow.AVOID, 0.4,
                          "Evening Sleeping", "No new positions"),
            ]
            best_entry = [time_class(9, 0), time_class(13, 0)]
            best_exit = [time_class(11, 0), time_class(15, 0)]
        elif is_favorable:
            # Good day - limited windows
            trading_windows = [
                TimeWindow(time_class(10, 0), time_class(12, 0), TradingWindow.PRIME, 1.0,
                          "Midday Eating period", "Entry/Exit"),
                TimeWindow(time_class(14, 0), time_class(16, 0), TradingWindow.MODERATE, 0.7,
                          "Afternoon Walking", "Cautious"),
            ]
            blocked_windows = [
                TimeWindow(time_class(0, 0), time_class(10, 0), TradingWindow.BLOCK, 0.1, "Pre-market", ""),
                TimeWindow(time_class(12, 0), time_class(14, 0), TradingWindow.AVOID, 0.4, "Lunch Sleeping", ""),
                TimeWindow(time_class(16, 0), time_class(23, 59), TradingWindow.BLOCK, 0.1, "After hours", ""),
            ]
            best_entry = [time_class(10, 0)]
            best_exit = [time_class(12, 0), time_class(16, 0)]
        else:
            # Bad day - minimal or no trading
            trading_windows = [
                TimeWindow(time_class(11, 0), time_class(12, 0), TradingWindow.MODERATE, 0.6,
                          "Brief favorable window", "Extreme caution"),
            ]
            blocked_windows = [
                TimeWindow(time_class(0, 0), time_class(11, 0), TradingWindow.BLOCK, 0.1, "Morning Dying", ""),
                TimeWindow(time_class(12, 0), time_class(23, 59), TradingWindow.BLOCK, 0.1, "Afternoon Dying", ""),
            ]
            best_entry = []
            best_exit = [time_class(12, 0)]
        
        plan = DailyTradingPlan(
            date=date_str,
            muhurtha_rating=muhurtha_rating,
            tithi="Simulated",
            tithi_type=tithi_type,
            is_favorable_day=is_favorable,
            warnings=["Rikta Tithi - Avoid new beginnings"] if tithi_type == "Rikta" else [],
            top_assets=top_assets,
            avoid_assets=avoid_assets,
            trading_windows=trading_windows,
            blocked_windows=blocked_windows,
            best_entry_times=best_entry,
            best_exit_times=best_exit,
            max_positions=3 if muhurtha_rating >= 7 else 2,
            risk_adjustment=1.2 if muhurtha_rating >= 8 else 1.0 if muhurtha_rating >= 6 else 0.6
        )
        
        self.daily_plans[date_str] = plan
        self.current_plan = plan
        return plan
    
    def can_trade_now(self, symbol: str, date_str: str, current_time: time) -> Tuple[bool, str]:
        """Check if trading is allowed now"""
        plan = self.daily_plans.get(date_str)
        if not plan:
            return False, "No plan for today"
        
        # Check if symbol in top assets
        top_symbols = [a.symbol for a in plan.top_assets]
        if symbol not in top_symbols:
            return False, f"{symbol} not in today's top assets"
        
        # Check if in favorable window
        for window in plan.trading_windows:
            if window.start_time <= current_time < window.end_time:
                if window.window_type in [TradingWindow.PRIME, TradingWindow.GOOD]:
                    return True, f"OK: {window.description}"
                elif window.window_type == TradingWindow.MODERATE:
                    return False, "MODERATE window - No new positions"
        
        # Check if in blocked window
        for window in plan.blocked_windows:
            if window.start_time <= current_time < window.end_time:
                return False, f"BLOCKED: {window.description}"
        
        return False, "Outside trading hours"


# =============================================================================
# V10 BACKTEST ENGINE
# =============================================================================

def run_v10_vedastro_backtest():
    print("=" * 90)
    print("  v10 VEDASTRO-POWERED BACKTEST")
    print("=" * 90)
    print("  Architecture:")
    print("    1. Pre-Market: VedAstro ranks assets & determines time windows")
    print("    2. Trading: Only trade top assets during favorable windows")
    print("    3. Result: Quality over quantity - fewer but better trades")
    print("=" * 90)
    
    # Initialize components
    vedastro = MockVedAstroOrchestrator()
    tech_analyzer = TechnicalAnalyzer()
    collective = CollectiveConsciousness()
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
    price_history = {sym: {"prices": [], "volumes": [], "highs": [], "lows": []} for sym in all_data.keys()}
    
    # Performance tracking
    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_history = []
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} for sym in all_data.keys()}
    
    # Trading statistics
    vedastro_blocked_trades = 0
    vedastro_allowed_trades = 0
    
    # Simulation loop
    print("\n[VEDASTRO] Initializing pre-market analysis...")
    print("  Each day: VedAstro ranks assets -> Guna agents trade only top-ranked")
    print()
    
    sim_start = time_module.time()
    total_days = len(sorted_dates)
    progress_interval = max(1, total_days // 20)
    
    current_date = None
    daily_plan = None
    
    for day_idx, date in enumerate(sorted_dates):
        if day_idx % progress_interval == 0:
            pct = (day_idx / total_days) * 100
            elapsed = time_module.time() - sim_start
            print(f"  [{pct:5.1f}%] Day {day_idx}/{total_days} | Capital: ${capital:,.0f} | Time: {elapsed:.0f}s")
        
        # Generate new VedAstro plan at start of each day
        if date != current_date:
            current_date = date
            
            # Get market snapshot for all symbols at start of day
            market_snapshot = {}
            for sym in all_data.keys():
                bars = all_data[sym]
                day_bar = next((b for b in bars if b["date"] == date), None)
                if day_bar and len(price_history[sym]["prices"]) >= 50:
                    ph = price_history[sym]
                    ms = tech_analyzer.analyze_market_state(sym, ph["prices"], ph["volumes"], ph["highs"], ph["lows"])
                    market_snapshot[sym] = {
                        "volatility": ms.volatility,
                        "adx": ms.adx,
                        "trend_1d": ms.trend_1d
                    }
            
            # Generate daily plan
            if market_snapshot:
                daily_plan = vedastro.generate_daily_plan(date, list(all_data.keys()), market_snapshot)
                top_assets = [a.symbol for a in daily_plan.top_assets]
                print(f"    {date}: Top assets: {top_assets}, Rating: {daily_plan.muhurtha_rating:.1f}/10")
        
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
        
        # Simulate trading day (check at noon for simplicity)
        current_time = time_class(12, 0)  # Midday check
        
        # Check exits first (always allowed for risk management)
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
                    trade_history.append({"date": date, "symbol": sym, "pnl": pnl, "reason": exit_reason})
        
        # Check entries (VedAstro filtered)
        for sym, pos in positions.items():
            if pos.position == 0 and sym in current_prices and len(price_history[sym]["prices"]) >= 60:
                
                # VEDASTRO CHECK: Can we trade this symbol now?
                can_trade, reason = vedastro.can_trade_now(sym, date, current_time)
                
                if not can_trade:
                    vedastro_blocked_trades += 1
                    continue
                
                vedastro_allowed_trades += 1
                
                # Continue with Guna analysis
                sector = next((s for s, syms in UNIVERSE_GROUPS.items() if sym in syms), "unknown")
                
                if risk_manager.can_open(sym, sector):
                    ph = price_history[sym]
                    market_state = tech_analyzer.analyze(sym, ph["prices"], ph["volumes"], ph["highs"], ph["lows"])
                    
                    # Agent analysis
                    for agent in collective.agents:
                        agent.regenerate_prana()
                    decision = collective.deliberation(market_state)
                    
                    if decision.action in [ActionType.BUY, ActionType.SELL] and decision.confidence >= MIN_CONFIDENCE:
                        pos_size = risk_manager.calculate_position_size(capital, decision, market_state.atr, market_state.price)
                        
                        if pos_size >= 200:
                            side = "buy" if decision.action == ActionType.BUY else "sell"
                            cost = pos.open_position(side, pos_size, market_state.price, market_state.atr, decision)
                            capital -= cost
                            risk_manager.add_position(sym, sector, side, pos_size)
        
        # Update equity
        current_equity = capital
        for sym, pos in positions.items():
            if pos.position != 0 and sym in current_prices:
                current_equity += pos.mark_to_market(current_prices[sym]["close"])
        
        equity_curve.append(current_equity)
        risk_manager.update_drawdown(current_equity)
    
    # Final results
    sim_elapsed = time_module.time() - sim_start
    
    total_trades = sum(m["trades"] for m in symbol_metrics.values())
    total_wins = sum(m["wins"] for m in symbol_metrics.values())
    total_pnl = sum(m["pnl"] for m in symbol_metrics.values())
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    roi = (total_pnl / INITIAL_CAPITAL) * 100
    
    # Calculate metrics
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)
    
    returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] 
               for i in range(1, len(equity_curve)) if equity_curve[i-1] > 0]
    sharpe = (np.mean(returns) / np.std(returns) * math.sqrt(252)) if returns and np.std(returns) > 0 else 0
    
    # Print results
    print("\n" + "=" * 90)
    print("  v10 VEDASTRO-POWERED BACKTEST RESULTS")
    print("=" * 90)
    print(f"  Period:             {START_DATE} -> {END_DATE}")
    print(f"  Start Capital:      ${INITIAL_CAPITAL:,.2f}")
    print(f"  End Capital:        ${capital:,.2f}")
    print(f"  Total PNL:          ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Win Rate:           {win_rate:.1f}%")
    print(f"  Total Trades:       {total_trades}")
    print(f"  Max Drawdown:       {max_dd*100:.1f}%")
    print(f"  Sharpe Ratio:       {sharpe:.2f}")
    print(f"  Simulation Time:    {sim_elapsed:.1f}s")
    print("=" * 90)
    
    # VedAstro statistics
    print("\n  VEDASTRO FILTER STATISTICS:")
    print(f"    Trades Allowed:   {vedastro_allowed_trades}")
    print(f"    Trades Blocked:   {vedastro_blocked_trades}")
    print(f"    Filter Rate:      {vedastro_blocked_trades / (vedastro_allowed_trades + vedastro_blocked_trades) * 100:.1f}%")
    
    # Sector breakdown
    print("\n  PER SECTOR PERFORMANCE:")
    for sector, syms in UNIVERSE_GROUPS.items():
        s_trades = sum(symbol_metrics.get(s, {}).get("trades", 0) for s in syms if s in symbol_metrics)
        s_wins = sum(symbol_metrics.get(s, {}).get("wins", 0) for s in syms if s in symbol_metrics)
        s_pnl = sum(symbol_metrics.get(s, {}).get("pnl", 0) for s in syms if s in symbol_metrics)
        s_wr = (s_wins / s_trades * 100) if s_trades > 0 else 0
        indicator = "[+]" if s_pnl > 0 else "[-]"
        print(f"    {indicator} {sector:12s} | Trades: {s_trades:3d} | WR: {s_wr:5.1f}% | PNL: ${s_pnl:>10,.2f}")
    
    # Top symbols
    print("\n  TOP PERFORMING SYMBOLS:")
    sorted_syms = sorted(symbol_metrics.items(), key=lambda x: x[1]["pnl"], reverse=True)
    for i, (sym, m) in enumerate(sorted_syms[:8]):
        if m["trades"] > 0:
            wr = (m["wins"] / m["trades"] * 100)
            rank = ["[1]", "[2]", "[3]", "[+]"][min(i, 3)]
            print(f"    {rank} {sym:12s} | Trades: {m['trades']:3d} | WR: {wr:5.1f}% | PNL: ${m['pnl']:>10,.2f}")
    
    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    report = {
        "version": "v10_vedastro",
        "metrics": {
            "total_return_pct": roi,
            "total_trades": total_trades,
            "win_rate_pct": win_rate,
            "max_drawdown_pct": max_dd * 100,
            "sharpe_ratio": sharpe,
            "final_capital": capital
        },
        "vedastro_stats": {
            "trades_allowed": vedastro_allowed_trades,
            "trades_blocked": vedastro_blocked_trades,
            "filter_rate_pct": vedastro_blocked_trades / (vedastro_allowed_trades + vedastro_blocked_trades) * 100
        },
        "symbol_metrics": symbol_metrics
    }
    
    report_path = RESULTS_DIR / "v10_vedastro_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    eq_path = RESULTS_DIR / "v10_equity_curve.csv"
    with open(eq_path, "w") as f:
        f.write("day,equity\n")
        for i, eq in enumerate(equity_curve):
            f.write(f"{i},{eq:.2f}\n")
    
    print(f"\n  Results saved:")
    print(f"    - Report: {report_path}")
    print(f"    - Equity: {eq_path}")
    
    print("\n" + "=" * 90)
    print("  v10 VEDASTRO-POWERED BACKTEST COMPLETE")
    print("  Concept: Strategic timing (When + What) vs Tactical guessing (Now)")
    print("=" * 90)
    
    return report


if __name__ == "__main__":
    run_v10_vedastro_backtest()
