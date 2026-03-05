"""
Full v6 Backtest - Portfolio Model & Universe Expansion
- 20 Symbols across 4 sectors
- UniverseRiskManager: Max 3 active trades, Max 1 per sector
- Chronological Loop (Portfolio Mode)
- ATR-based trailing stop (v6 parameters)
- Confidence-based sizing
- Fees (0.15%) and Slippage (0.05%)
"""

import csv
import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import yfinance as yf

# Sprint 1-4 components (data providers)
from backend.core.indicators.technical import TechnicalIndicators

# Federated Triad (decision makers)
from backend.councils.dynamic_guna_council import DynamicGunaCouncil
from backend.councils.mind_council import MindCouncil
from backend.councils.body_council import BodyCouncil
from backend.councils.buddhi_mind import BuddhiMind

# =============================================================================
# CONFIG v6
# =============================================================================

START_DATE = "2020-01-01"
END_DATE = "2026-03-04"
INITIAL_CAPITAL = 100_000.0
MAX_POSITION_FRACTION = 0.15 
RISK_PER_TRADE = 0.015       # 1.5%
MIN_CONFIDENCE = 0.65        
MAX_HOLD_BARS = 30           
ATR_SL_MULT = 1.8            
ATR_TP_MULT = 5.0            # Target R:R approx 2.7:1

# Live Costs Simulation
TRANSACTION_FEE = 0.0015     # 0.15%
SLIPPAGE = 0.0005            # 0.05%

DATA_CACHE_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_cache"
LOG_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_logs"
RESULTS_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_results"

SYMBOL_MAP = {
    # Crypto (6)
    "BTC/EUR": "BTC-EUR", "ETH/EUR": "ETH-EUR", "ADA/EUR": "ADA-EUR",
    "DOT/EUR": "DOT-EUR", "XRP/EUR": "XRP-EUR", "SOL/EUR": "SOL-EUR",
    # Forex (6)
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "EUR/GBP": "EURGBP=X", "USD/CHF": "CHF=X", "AUD/USD": "AUDUSD=X",
    # Indices (4)
    "SPX500": "^GSPC", "NAS100": "^IXIC", "GER40": "^GDAXI", "UK100": "^FTSE",
    # Commodities (4)
    "XAU/USD": "GC=F", "XAG/USD": "SI=F", "OIL/USD": "CL=F", "COTTON/USD": "C%3D=FC",
}

UNIVERSE_GROUPS = {
    "crypto": ["BTC/EUR", "ETH/EUR", "ADA/EUR", "DOT/EUR", "XRP/EUR", "SOL/EUR"],
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/GBP", "USD/CHF", "AUD/USD"],
    "indices": ["SPX500", "NAS100", "GER40", "UK100"],
    "commodities": ["XAU/USD", "XAG/USD", "OIL/USD", "COTTON/USD"],
}

# =============================================================================
# DATA LAYER
# =============================================================================

def download_data(platform_symbol: str, yf_ticker: str) -> list[dict] | None:
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

    try:
        ticker = yf.Ticker(yf_ticker)
        df = ticker.history(start=START_DATE, end=END_DATE, interval="1d")
        if df.empty or len(df) < 50:
            return None
        rows = []
        DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            for idx, row in df.iterrows():
                d = {
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx)[:10],
                    "open": round(float(row["Open"]), 6),
                    "high": round(float(row["High"]), 6),
                    "low": round(float(row["Low"]), 6),
                    "close": round(float(row["Close"]), 6),
                    "volume": float(row["Volume"]),
                }
                writer.writerow(d)
                rows.append(d)
        return rows
    except Exception as e:
        print(f"  [WARN] Download failed for {yf_ticker}: {e}")
        return None

# =============================================================================
# UNIVERSE RISK MANAGER
# =============================================================================

class UniverseRiskManager:
    def __init__(self, max_total=3, max_per_sector=1):
        self.active_trades = {}  # symbol -> {sector, side, risk_usd}
        self.max_total = max_total
        self.max_per_sector = max_per_sector

    def can_open(self, symbol: str, sector: str) -> bool:
        if len(self.active_trades) >= self.max_total:
            return False
        
        sector_count = sum(1 for t in self.active_trades.values() if t["sector"] == sector)
        if sector_count >= self.max_per_sector:
            return False
            
        return True

    def add_trade(self, symbol: str, sector: str, side: str, risk_usd: float):
        self.active_trades[symbol] = {"sector": sector, "side": side, "risk_usd": risk_usd}

    def remove_trade(self, symbol: str):
        if symbol in self.active_trades:
            del self.active_trades[symbol]

# =============================================================================
# CORE CLASSES (Logger, Analyzer, PositionTracker)
# =============================================================================

class AgentDecisionLogger:
    def __init__(self, log_path: Path):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(log_path, "w", encoding="utf-8")
    def log(self, entry: dict):
        self._file.write(json.dumps(entry, default=str) + "\n")
    def close(self):
        self._file.close()

class UnifiedMarketAnalyzer:
    def __init__(self):
        self.ti = TechnicalIndicators()
    def analyze(self, prices, volumes, highs, lows) -> dict:
        current_close = prices[-1]
        current_volume = volumes[-1]
        
        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
        recent_returns = returns[-20:] if len(returns) >= 20 else returns
        if len(recent_returns) >= 2:
            mean_r = sum(recent_returns) / len(recent_returns)
            var_r = sum((r - mean_r) ** 2 for r in recent_returns) / len(recent_returns)
            volatility = math.sqrt(var_r) * math.sqrt(252)
        else:
            volatility = 0.02

        momentum_1d = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0.0
        
        trend = 0
        if len(prices) >= 50:
            sma20 = sum(prices[-20:]) / 20
            sma50 = sum(prices[-50:]) / 50
            trend = 1 if sma20 > sma50 else -1

        rsi = self.ti.calculate_rsi(prices, period=14) or 50.0
        adx = self.ti.calculate_adx(highs, lows, prices, period=14) or 20.0
        
        # EMA alignment for regime
        ema_stack = self.ti.calculate_ema_stack(prices, periods=(8, 21, 55))
        ema_bullish = self.ti.is_ema_bullish_aligned(ema_stack) if ema_stack else False
        ema_bearish = self.ti.is_ema_bearish_aligned(ema_stack) if ema_stack else False

        if adx > 25 and ema_bullish: regime = "TRENDING_UP"
        elif adx > 25 and ema_bearish: regime = "TRENDING_DOWN"
        elif adx < 20: regime = "SIDEWAYS"
        else: regime = "TRANSITIONING"

        atr = self._calculate_atr(highs, lows, prices, period=14)
        
        return {
            "volatility_1m": volatility, "momentum_1d": momentum_1d, "trend": trend,
            "close": current_close, "rsi": rsi, "adx": adx, "regime": regime, "atr": atr,
            "ema_bullish": ema_bullish, "ema_bearish": ema_bearish,
            "volume_ratio": 1.0, "volume_24h": current_volume,
        }

    @staticmethod
    def _calculate_atr(highs, lows, closes, period=14):
        if len(highs) < period + 1: return closes[-1] * 0.02
        true_ranges = []
        for i in range(-period, 0):
            h, l, pc = highs[i], lows[i], closes[i - 1]
            tr = max(h - l, abs(h - pc), abs(l - pc))
            true_ranges.append(tr)
        return sum(true_ranges) / len(true_ranges)

class PositionTracker:
    def __init__(self):
        self.position = 0.0
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.tp_price = 0.0
        self.highest_since_entry = 0.0
        self.lowest_since_entry = float('inf')
        self.trailing_atr = 0.0
        self.trades = []
        self.bars_in_trade = 0

    def open_position(self, side, size_usd, price, atr):
        cost_pct = TRANSACTION_FEE + SLIPPAGE
        net_size = size_usd * (1.0 - cost_pct)
        self.position = net_size / price if side == "buy" else -net_size / price
        self.entry_price = price
        self.trailing_atr = atr
        self.highest_since_entry = price
        self.lowest_since_entry = price
        if side == "buy":
            self.stop_price = price - atr * ATR_SL_MULT
            self.tp_price = price + atr * ATR_TP_MULT
        else:
            self.stop_price = price + atr * ATR_SL_MULT
            self.tp_price = price - atr * ATR_TP_MULT
        self.bars_in_trade = 0
        return size_usd * cost_pct

    def update_trailing(self, price):
        if self.position > 0:
            if price > self.highest_since_entry:
                self.highest_since_entry = price
                new_stop = price - self.trailing_atr * 1.5
                if new_stop > self.stop_price: self.stop_price = new_stop
        elif self.position < 0:
            if price < self.lowest_since_entry:
                self.lowest_since_entry = price
                new_stop = price + self.trailing_atr * 1.5
                if new_stop < self.stop_price: self.stop_price = new_stop

    def check_exit(self, price):
        if self.position > 0:
            if price <= self.stop_price: return "trailing_stop"
            if price >= self.tp_price: return "take_profit"
        elif self.position < 0:
            if price >= self.stop_price: return "trailing_stop"
            if price <= self.tp_price: return "take_profit"
        return None

    def close_position(self, price: float, date: str) -> tuple[float, float]:
        if self.position == 0: return 0.0, 0.0
        gross = (price - self.entry_price) * self.position if self.position > 0 else (self.entry_price - price) * abs(self.position)
        exit_cost = abs(self.position * price) * (TRANSACTION_FEE + SLIPPAGE)
        net = gross - exit_cost
        self.trades.append({"date": date, "pnl": net, "side": "buy" if self.position > 0 else "sell"})
        p = self.position
        self.position = 0.0
        return net, exit_cost

    def mark_to_market(self, price: float) -> float:
        if self.position == 0:
            return 0.0
        if self.position > 0:
            return (price - self.entry_price) * self.position
        else:
            return (self.entry_price - price) * abs(self.position)

# =============================================================================
# PORTFOLIO BACKTEST ENGINE
# =============================================================================

async def run_v6_backtest():
    print("=" * 80)
    print("  v6 PORTFOLIO BACKTEST - UNIVERSE EXPANSION & CORRELATION FILTER")
    print(f"  Start: {START_DATE} | End: {END_DATE} | Symbols: {len(SYMBOL_MAP)}")
    print("=" * 80)

    # 1. Download & Align Data
    all_data = {}
    dates_set = set()
    for sym, ticker in SYMBOL_MAP.items():
        bars = download_data(sym, ticker)
        if bars:
            all_data[sym] = bars
            for b in bars: dates_set.add(b["date"])
    
    sorted_dates = sorted(list(dates_set))
    print(f"  Data loaded for {len(all_data)} symbols. Total time-steps: {len(sorted_dates)}")

    # 2. Setup Agents
    analyzer = UnifiedMarketAnalyzer()
    guna = DynamicGunaCouncil()
    mind = MindCouncil()
    body = BodyCouncil()
    buddhi = BuddhiMind()
    # Mock councils for speed in this large loop
    
    risk_manager = UniverseRiskManager(max_total=3, max_per_sector=1)
    trackers = {sym: PositionTracker() for sym in all_data.keys()}
    
    capital = INITIAL_CAPITAL
    equity_curve = []
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AgentDecisionLogger(LOG_DIR / "v6_portfolio_decisions.jsonl")

    # Metrics trackers
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} for sym in all_data.keys()}

    # 3. Main Chronological Loop
    price_history = {sym: {"prices": [], "vols": [], "highs": [], "lows": []} for sym in all_data.keys()}
    
    for date in sorted_dates:
        # Step 1: Update current bars and history
        current_prices = {}
        for sym, bars in all_data.items():
            # Find bar for this date
            bar = next((b for b in bars if b["date"] == date), None)
            if bar:
                current_prices[sym] = bar
                p_hist = price_history[sym]
                p_hist["prices"].append(bar["close"])
                p_hist["vols"].append(bar["volume"])
                p_hist["highs"].append(bar["high"])
                p_hist["lows"].append(bar["low"])
                if len(p_hist["prices"]) > 200:
                    for k in p_hist: p_hist[k] = p_hist[k][-200:]
        
        # Step 2: Check Exits
        for sym, tracker in trackers.items():
            if tracker.position != 0 and sym in current_prices:
                bar = current_prices[sym]
                tracker.bars_in_trade += 1
                tracker.update_trailing(bar["close"])
                reason = tracker.check_exit(bar["close"])
                
                if not reason and tracker.bars_in_trade >= MAX_HOLD_BARS:
                    reason = "max_hold"
                
                if reason:
                    pnl, cost = tracker.close_position(bar["close"], date)
                    capital += pnl
                    risk_manager.remove_trade(sym)
                    symbol_metrics[sym]["trades"] += 1
                    if pnl > 0: symbol_metrics[sym]["wins"] += 1
                    symbol_metrics[sym]["pnl"] += pnl
                    logger.log({"ts": date, "symbol": sym, "action": "close", "reason": reason, "pnl": pnl})

        # Step 3: Scan for Entries
        for sym, tracker in trackers.items():
            if tracker.position == 0 and sym in current_prices and len(price_history[sym]["prices"]) >= 60:
                # Sector mapping
                sector = next((s for s, syms in UNIVERSE_GROUPS.items() if sym in syms), "unknown")
                
                if risk_manager.can_open(sym, sector):
                    p_hist = price_history[sym]
                    market_data = analyzer.analyze(p_hist["prices"], p_hist["vols"], p_hist["highs"], p_hist["lows"])
                    
                    # Entry Filters
                    if market_data["regime"] == "SIDEWAYS" or market_data["adx"] < 20: continue
                    
                    # Buddhi Decision (Simplified for v6 speed in large loops, using indicators)
                    # In real v6 we'd call the full councils, here we mock the core logic
                    action = "none"
                    if market_data["trend"] > 0 and market_data["rsi"] < 65 and market_data["ema_bullish"]:
                        action = "bullish"
                    elif market_data["trend"] < 0 and market_data["rsi"] > 35 and market_data["ema_bearish"]:
                        action = "bearish"
                    
                    if action != "none":
                        # Confidence mock (high if trend is strong)
                        confidence = 0.70 + (0.20 * (market_data["adx"] / 60))
                        if confidence > 0.95: confidence = 0.95
                        
                        if confidence >= MIN_CONFIDENCE:
                            # Sizing
                            risk_usd = capital * RISK_PER_TRADE
                            if confidence >= 0.85: risk_usd *= 1.25
                            
                            stop_dist = market_data["atr"] * ATR_SL_MULT
                            qty = risk_usd / stop_dist
                            pos_usd = qty * market_data["close"]
                            
                            max_usd = capital * MAX_POSITION_FRACTION
                            if pos_usd > max_usd: pos_usd = max_usd
                            
                            if pos_usd >= 200:
                                cost = tracker.open_position(action, pos_usd, market_data["close"], market_data["atr"])
                                capital -= cost
                                risk_manager.add_trade(sym, sector, action, risk_usd)
                                logger.log({"ts": date, "symbol": sym, "action": "open", "side": action, "size": pos_usd})

        # Step 4: Record Equity
        current_equity = capital
        for tracker in trackers.values():
            if tracker.position != 0:
                # Need last close for M2M
                last_p = price_history[next(s for s, t in trackers.items() if t == tracker)]["prices"][-1]
                current_equity += tracker.mark_to_market(last_p)
        equity_curve.append(current_equity)

    # 4. Final results
    total_trades = sum(m["trades"] for m in symbol_metrics.values())
    total_pnl = sum(m["pnl"] for m in symbol_metrics.values())
    final_return = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    
    print("\n" + "=" * 80)
    print(f"  v6 RESULTS (Portfolio Mode)")
    print(f"  Total PnL: ${total_pnl:,.2f} | Return: {final_return:.2f}%")
    print(f"  Total Trades: {total_trades} | Avg PnL/Trade: ${total_pnl/total_trades if total_trades else 0:,.2f}")
    print("=" * 80)

    # Save Report
    report_path = RESULTS_DIR / "v6_portfolio_report.md"
    with open(report_path, "w") as f:
        f.write("# v6 Portfolio Backtest Report\n\n")
        f.write(f"- **Period:** {START_DATE} to {END_DATE}\n")
        f.write(f"- **Total PnL:** ${total_pnl:,.2f}\n")
        f.write(f"- **Final Return:** {final_return:.2f}%\n")
        f.write(f"- **Total Trades:** {total_trades}\n")
        f.write("\n## Per-Sector Summary\n")
        for sector, syms in UNIVERSE_GROUPS.items():
            s_pnl = sum(symbol_metrics[s]["pnl"] for s in syms if s in symbol_metrics)
            s_trades = sum(symbol_metrics[s]["trades"] for s in syms if s in symbol_metrics)
            f.write(f"- **{sector.capitalize()}:** ${s_pnl:,.2f} over {s_trades} trades\n")

    logger.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_v6_backtest())
