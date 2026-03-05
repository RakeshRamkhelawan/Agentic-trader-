"""
Full Unified Backtest v4 - 2020 to 2026
Fixes from v3 diagnosis:
  1. ATR-based trailing stop (replaces fixed -3% SL)
  2. Trend filter (only trade WITH the trend)
  3. Regime filter (no SIDEWAYS trading)
  4. Risk-per-trade sizing (1.5% risk via ATR)
  5. Min confidence 0.65 for entry
  6. Max hold 30 bars (was 10)

Usage:
    python backend/scripts/run_full_backtest.py
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
from backend.councils.body_council import BodyCouncil
from backend.councils.buddhi_mind import BuddhiMind

# Federated Triad (decision makers)
from backend.councils.dynamic_guna_council import DynamicGunaCouncil
from backend.councils.mind_council import MindCouncil

# =============================================================================
# CONFIG v5 - Meta-Edge Optimalisatie
# =============================================================================

START_DATE = "2020-01-01"
END_DATE = "2026-03-04"
INITIAL_CAPITAL = 100_000.0
MAX_POSITION_FRACTION = 0.15  # Max 15% per trade
RISK_PER_TRADE = 0.015  # Risk 1.5% of capital per trade
MIN_CONFIDENCE = 0.65  # Minimum Buddhi confidence for entry
MAX_HOLD_BARS = 30  # Max holding period
ATR_SL_MULT = 1.8  # v5: Strakker (was 2.0)
ATR_TP_MULT = 4.5  # v5: Ruimer (was 4.0) -> R:R targets 2.5 theo, 1.8-2.0 real

# Live Costs Simulation
TRANSACTION_FEE = 0.0015  # 0.15% per side
SLIPPAGE = 0.0005  # 0.05% per side

DATA_CACHE_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_cache"
LOG_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_logs"
RESULTS_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_results"

SYMBOL_MAP = {
    "BTC/EUR": "BTC-EUR",
    "ETH/EUR": "ETH-EUR",
    "SOL/EUR": "SOL-EUR",
    "ADA/EUR": "ADA-EUR",
    "XRP/EUR": "XRP-EUR",
    "LINK/EUR": "LINK-EUR",
    "DOT/EUR": "DOT-EUR",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "EUR/GBP": "EURGBP=X",
    "USD/CHF": "CHF=X",
    "XAU/USD": "GC=F",
    "XAG/USD": "SI=F",
    "OIL/USD": "CL=F",
    "SPX500": "^GSPC",
    "NAS100": "^IXIC",
    "GER40": "^GDAXI",
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "META": "META",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
}

SECTOR_MAP = {
    "BTC/EUR": "CRYPTO",
    "ETH/EUR": "CRYPTO",
    "SOL/EUR": "CRYPTO",
    "ADA/EUR": "CRYPTO",
    "XRP/EUR": "CRYPTO",
    "LINK/EUR": "CRYPTO",
    "DOT/EUR": "CRYPTO",
    "EUR/USD": "FOREX",
    "GBP/USD": "FOREX",
    "USD/JPY": "FOREX",
    "EUR/GBP": "FOREX",
    "USD/CHF": "FOREX",
    "XAU/USD": "COMMODITY",
    "XAG/USD": "COMMODITY",
    "OIL/USD": "COMMODITY",
    "SPX500": "INDEX",
    "NAS100": "INDEX",
    "GER40": "INDEX",
    "AAPL": "TECH",
    "MSFT": "TECH",
    "GOOGL": "TECH",
    "AMZN": "TECH",
    "META": "TECH",
    "NVDA": "TECH",
    "TSLA": "TECH",
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
                    rows.append(
                        {
                            "date": row["date"],
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]),
                        }
                    )
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
            writer = csv.DictWriter(
                f, fieldnames=["date", "open", "high", "low", "close", "volume"]
            )
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
# AGENT DECISION LOGGER
# =============================================================================


class AgentDecisionLogger:
    def __init__(self, log_path: Path):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(log_path, "w", encoding="utf-8")

    def log(self, entry: dict):
        self._file.write(json.dumps(entry, default=str) + "\n")

    def close(self):
        self._file.close()


# =============================================================================
# UNIFIED MARKET ANALYZER - Sprint 1-4 enriches council data
# =============================================================================


class UnifiedMarketAnalyzer:
    """
    Bridge: Sprint 1-4 TechnicalIndicators -> enriched market_data dict
    for the Federated Triad councils.
    """

    def __init__(self):
        self.ti = TechnicalIndicators()

    def analyze(
        self,
        prices: list[float],
        volumes: list[float],
        highs: list[float],
        lows: list[float],
    ) -> dict:
        """Build enriched market_data dict from OHLCV window."""
        current_close = prices[-1]
        current_volume = volumes[-1]

        # ── Basic features (what councils already expected) ──
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

        momentum_1d = 0.0
        if len(prices) >= 2 and prices[-2] > 0:
            momentum_1d = (prices[-1] - prices[-2]) / prices[-2]

        momentum_3d = 0.0
        if len(prices) >= 4 and prices[-4] > 0:
            momentum_3d = (prices[-1] - prices[-4]) / prices[-4]

        recent_vols = volumes[-20:] if len(volumes) >= 20 else volumes
        avg_volume = sum(recent_vols) / len(recent_vols) if recent_vols else 1.0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        trend = 0
        if len(prices) >= 100:
            sma50 = sum(prices[-50:]) / 50
            sma100 = sum(prices[-100:]) / 100
            trend = 1 if sma50 > sma100 else -1
        elif len(prices) >= 50:
            sma20 = sum(prices[-20:]) / 20
            sma50 = sum(prices[-50:]) / 50
            trend = 1 if sma20 > sma50 else -1

        bid_ask_spread = max(0.0001, 0.001 * (1 + volatility))

        # ── Sprint 1-4 Enriched features ──
        rsi = self.ti.calculate_rsi(prices, period=14) or 50.0
        macd_result = self.ti.calculate_macd(prices)
        macd_hist = macd_result.histogram if macd_result else 0.0
        bb = self.ti.calculate_bollinger_bands(prices, period=20)
        bb_width = bb.width if bb else 0.0
        adx = self.ti.calculate_adx(highs, lows, prices, period=14) or 20.0

        # EMA alignment for regime context
        ema_stack = self.ti.calculate_ema_stack(prices, periods=(8, 21, 55))
        ema_bullish = self.ti.is_ema_bullish_aligned(ema_stack) if ema_stack else False
        ema_bearish = self.ti.is_ema_bearish_aligned(ema_stack) if ema_stack else False

        # Regime classification from indicators
        if adx > 25 and ema_bullish:
            regime = "TRENDING_UP"
        elif adx > 25 and ema_bearish:
            regime = "TRENDING_DOWN"
        elif adx < 20:
            regime = "SIDEWAYS"
        else:
            regime = "TRANSITIONING"

        # Sentiment score from price action (simplified without external data)
        sentiment_score = 0.5
        if rsi < 30:
            sentiment_score = 0.2  # Oversold = fear
        elif rsi > 70:
            sentiment_score = 0.8  # Overbought = greed
        elif momentum_1d > 0.01:
            sentiment_score = 0.6
        elif momentum_1d < -0.01:
            sentiment_score = 0.4

        # ATR calculation (14-period)
        atr = self._calculate_atr(highs, lows, prices, period=14)

        return {
            # Base council keys
            "volatility_1m": volatility,
            "momentum_1d": momentum_1d,
            "momentum_3d": momentum_3d,
            "volume_ratio": volume_ratio,
            "bid_ask_spread": bid_ask_spread,
            "trend": trend,
            "volume_24h": current_volume,
            "order_book_depth": current_volume * current_close * 0.01,
            "close": current_close,
            # Sprint 1-4 enriched keys
            "rsi": rsi,
            "macd_hist": macd_hist,
            "adx": adx,
            "bb_width": bb_width,
            "regime": regime,
            "ema_bullish": ema_bullish,
            "ema_bearish": ema_bearish,
            "sentiment_score": sentiment_score,
            "atr": atr,
        }

    @staticmethod
    def _calculate_atr(highs, lows, closes, period=14):
        """Calculate Average True Range."""
        if len(highs) < period + 1:
            # Fallback: simple range
            if len(highs) >= 2:
                ranges = [highs[i] - lows[i] for i in range(-min(period, len(highs)), 0)]
                return sum(ranges) / len(ranges) if ranges else closes[-1] * 0.02
            return closes[-1] * 0.02

        true_ranges = []
        for i in range(-period, 0):
            h, l, pc = highs[i], lows[i], closes[i - 1]
            tr = max(h - l, abs(h - pc), abs(l - pc))
            true_ranges.append(tr)
        return sum(true_ranges) / len(true_ranges)


# =============================================================================
# POSITION TRACKER
# =============================================================================


class PositionTracker:
    def __init__(self):
        self.position = 0.0
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.tp_price = 0.0
        self.highest_since_entry = 0.0  # For trailing stop
        self.lowest_since_entry = float("inf")  # For short trailing
        self.trailing_atr = 0.0
        self.trades: list[dict] = []

    def open_position(
        self,
        side: str,
        size_usd: float,
        price: float,
        atr: float,
        sl_mult: float = 2.0,
        tp_mult: float = 4.0,
    ):
        # Apply entry costs (Fee + Slippage)
        entry_cost_pct = TRANSACTION_FEE + SLIPPAGE
        net_size_usd = size_usd * (1.0 - entry_cost_pct)

        qty = net_size_usd / price
        self.position = qty if side == "buy" else -qty
        self.entry_price = price
        self.trailing_atr = atr
        self.highest_since_entry = price
        self.lowest_since_entry = price

        if side == "buy":
            self.stop_price = price - atr * sl_mult
            self.tp_price = price + atr * tp_mult
        else:  # sell/short
            self.stop_price = price + atr * sl_mult
            self.tp_price = price - atr * tp_mult

        return size_usd * entry_cost_pct  # Return total cost paid

    def update_trailing_stop(self, price: float):
        """Tighten stop as price moves in our favor."""
        if self.position > 0:  # Long
            if price > self.highest_since_entry:
                self.highest_since_entry = price
                # Trail stop at 1.5x ATR from highest
                new_stop = price - self.trailing_atr * 1.5
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
        elif self.position < 0:  # Short
            if price < self.lowest_since_entry:
                self.lowest_since_entry = price
                new_stop = price + self.trailing_atr * 1.5
                if new_stop < self.stop_price:
                    self.stop_price = new_stop

    def check_exit(self, price: float) -> str | None:
        """Check if stop or TP is hit. Returns reason or None."""
        if self.position > 0:  # Long
            if price <= self.stop_price:
                return "trailing_stop"
            if price >= self.tp_price:
                return "take_profit"
        elif self.position < 0:  # Short
            if price >= self.stop_price:
                return "trailing_stop"
            if price <= self.tp_price:
                return "take_profit"
        return None

    def close_position(self, price: float, date: str) -> tuple[float, float]:
        if self.position == 0:
            return 0.0, 0.0

        if self.position > 0:
            gross_pnl = (price - self.entry_price) * self.position
        else:
            gross_pnl = (self.entry_price - price) * abs(self.position)

        # Apply exit costs (Fee + Slippage)
        exit_value = abs(self.position * price)
        exit_cost = exit_value * (TRANSACTION_FEE + SLIPPAGE)
        net_pnl = gross_pnl - exit_cost

        self.trades.append(
            {
                "entry": self.entry_price,
                "exit": price,
                "pnl": net_pnl,
                "costs": exit_cost,
                "side": "buy" if self.position > 0 else "sell",
                "date": date,
            }
        )
        self.position = 0.0
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.tp_price = 0.0
        return net_pnl, exit_cost

    def mark_to_market(self, price: float) -> float:
        if self.position == 0:
            return 0.0
        if self.position > 0:
            return (price - self.entry_price) * self.position
        else:
            return (self.entry_price - price) * abs(self.position)


# =============================================================================
# METRICS
# =============================================================================


def calculate_sharpe(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    std_r = math.sqrt(var_r) if var_r > 0 else 0.0001
    return mean_r * math.sqrt(252) / std_r


def calculate_max_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


# =============================================================================
# MOCK EXO-AGENTS FOR BACKTESTING
# =============================================================================
import datetime


class MockVedastroAgent:
    """Mock agent to provide deterministic planetary signals for backtesting without API overhead."""

    def analyze_sync(self, date_str: str, symbol: str) -> dict:
        try:
            # Simple deterministic logic based on the date
            # e.g., '2024-01-01T00:00:00Z' or '2024-01-01'
            d_str = date_str[:10]
            dt = datetime.datetime.strptime(d_str, "%Y-%m-%d")

            # Mondays (0): Bullish (Moon), Fridays (4): Bearish (Venus retrograde mock), else Neutral
            if dt.weekday() == 0:
                return {"council": "vedastro", "perspective": "bullish", "confidence": 0.65}
            elif dt.weekday() == 4:
                return {"council": "vedastro", "perspective": "bearish", "confidence": 0.65}
            else:
                return {"council": "vedastro", "perspective": "neutral", "confidence": 0.50}
        except Exception:
            return {"council": "vedastro", "perspective": "neutral", "confidence": 0.50}


# =============================================================================
# MAIN BACKTEST LOOP - UNIFIED PIPELINE
# =============================================================================


def run_backtest_for_symbol(
    platform_symbol: str,
    bars: list[dict],
    analyzer: UnifiedMarketAnalyzer,
    guna: DynamicGunaCouncil,
    mind: MindCouncil,
    body: BodyCouncil,
    buddhi: BuddhiMind,
    vedastro: MockVedastroAgent,
    logger: AgentDecisionLogger,
    capital: float,
) -> dict:
    tracker = PositionTracker()
    prices_w, volumes_w, highs_w, lows_w = [], [], [], []
    equity_curve = [capital]
    running_capital = capital
    win_count = loss_count = bar_count = bars_in_trade = 0
    total_pnl = 0.0
    gross_wins = 0.0
    gross_losses = 0.0
    filtered_count = 0

    for bar in bars:
        bar_count += 1
        close, volume, date = bar["close"], bar["volume"], bar["date"]
        prices_w.append(close)
        volumes_w.append(volume)
        highs_w.append(bar["high"])
        lows_w.append(bar["low"])

        if len(prices_w) > 200:
            prices_w = prices_w[-200:]
            volumes_w = volumes_w[-200:]
            highs_w = highs_w[-200:]
            lows_w = lows_w[-200:]

        if len(prices_w) < 60:  # Need 60 bars for reliable ATR + indicators
            equity_curve.append(running_capital + tracker.mark_to_market(close))
            continue

        # == UNIFIED MARKET ANALYZER (Sprint 1-4 -> enriched dict) ==
        market_data = analyzer.analyze(prices_w, volumes_w, highs_w, lows_w)

        # == EXO-SYSTEM ==
        vedastro_signal = vedastro.analyze_sync(date, platform_symbol)

        # == COUNCILS ==
        guna_view = guna.analyze(market_data)
        mind_view = mind.analyze(market_data)
        body_view = body.analyze_execution_environment(market_data)

        # == BUDDHI MIND ==
        council_views = [guna_view, mind_view, body_view, vedastro_signal]
        decision = buddhi.decide(
            council_views=council_views,
            market_data=market_data,
            session_id=f"bt_{platform_symbol}_{date}",
            timestamp=date,
        )

        logger.log(
            {
                "ts": date,
                "symbol": platform_symbol,
                "agent": "BuddhiMind",
                "action": "decide",
                "decision": decision.action,
                "confidence": decision.confidence,
                "coherence": decision.coherence,
                "rationale": decision.rationale[:100],
                "risk_level": decision.risk_assessment.get("level", "?"),
                "executable": decision.is_executable(),
                "regime": market_data["regime"],
                "adx": market_data["adx"],
                "trend": market_data["trend"],
                "vedastro_signal": vedastro_signal["perspective"],
            }
        )

        # == POSITION EXIT CHECK (ATR trailing stop) ==
        if tracker.position != 0:
            bars_in_trade += 1

            # Update trailing stop
            tracker.update_trailing_stop(close)

            # Check ATR-based stop and TP
            exit_reason = tracker.check_exit(close)

            # Max hold check
            if not exit_reason and bars_in_trade >= MAX_HOLD_BARS:
                exit_reason = f"max_hold ({MAX_HOLD_BARS} bars)"

            # Buddhi reversal
            if not exit_reason:
                if (
                    tracker.position > 0
                    and decision.action == "bearish"
                    and decision.confidence >= 0.60
                ):
                    exit_reason = "buddhi_reversal"
                elif (
                    tracker.position < 0
                    and decision.action == "bullish"
                    and decision.confidence >= 0.60
                ):
                    exit_reason = "buddhi_reversal"

            if exit_reason:
                net_pnl, exit_cost = tracker.close_position(close, date)
                total_pnl += net_pnl
                running_capital += net_pnl
                if net_pnl > 0:
                    win_count += 1
                    gross_wins += net_pnl
                else:
                    loss_count += 1
                    gross_losses += abs(net_pnl)

                # Bars in trade reset for next trade
                bars_in_trade_reset_val = bars_in_trade
                bars_in_trade = 0

                logger.log(
                    {
                        "ts": date,
                        "symbol": platform_symbol,
                        "agent": "PositionTracker",
                        "action": "close",
                        "reason": exit_reason,
                        "pnl": round(net_pnl, 2),
                        "exit_cost": round(exit_cost, 2),
                        "bars_held": bars_in_trade_reset_val,
                        "running_capital": round(running_capital, 2),
                    }
                )

            equity_curve.append(running_capital + tracker.mark_to_market(close))
            continue

        # == ENTRY FILTERS ==
        # Filter 1: Must have directional signal
        if decision.action not in ("bullish", "bearish"):
            equity_curve.append(running_capital)
            continue

        # Filter 2: Minimum confidence threshold
        if decision.confidence < MIN_CONFIDENCE:
            filtered_count += 1
            equity_curve.append(running_capital)
            continue

        # Filter 3: Regime filter - do NOT trade in sideways markets
        regime = market_data["regime"]
        adx = market_data["adx"]
        if regime == "SIDEWAYS" or adx < 20:
            filtered_count += 1
            equity_curve.append(running_capital)
            continue

        # Filter 4: Trend alignment - only trade WITH the trend
        trend = market_data["trend"]
        if decision.action == "bullish" and trend < 0:
            filtered_count += 1
            equity_curve.append(running_capital)
            continue
        if decision.action == "bearish" and trend > 0:
            filtered_count += 1
            equity_curve.append(running_capital)
            continue

        # == ATR-BASED POSITION SIZING ==
        atr = market_data.get("atr", close * 0.02)
        if atr <= 0:
            atr = close * 0.02

        # Risk = 1.5% of capital (standard)
        risk_dollars = running_capital * RISK_PER_TRADE

        # v5 Confidence-based sizing buckets
        if decision.confidence >= 0.85:
            risk_dollars *= 1.25  # High confidence boost
        elif decision.confidence < 0.75:
            risk_dollars *= 0.75  # Low confidence discount

        # Stop distance = 1.8x ATR (v5)
        stop_distance = atr * ATR_SL_MULT
        # Position size = risk / stop_distance * price
        position_qty = risk_dollars / stop_distance
        position_usd = position_qty * close

        # Cap at max position fraction
        max_usd = running_capital * MAX_POSITION_FRACTION
        if position_usd > max_usd:
            position_usd = max_usd

        if position_usd < 200:
            equity_curve.append(running_capital)
            continue

        side = "buy" if decision.action == "bullish" else "sell"
        entry_cost = tracker.open_position(
            side, position_usd, close, atr, sl_mult=ATR_SL_MULT, tp_mult=ATR_TP_MULT
        )
        # Immediate capital hit for entry costs
        running_capital -= entry_cost
        bars_in_trade = 0

        logger.log(
            {
                "ts": date,
                "symbol": platform_symbol,
                "agent": "TraderExecution",
                "action": "open",
                "side": side,
                "size_usd": round(position_usd, 2),
                "entry_price": close,
                "stop_price": round(tracker.stop_price, 4),
                "tp_price": round(tracker.tp_price, 4),
                "atr": round(atr, 4),
                "buddhi_conf": decision.confidence,
                "buddhi_coh": decision.coherence,
                "guna": guna_view["guna_vector"]["dominant"],
                "fg": mind_view["fear_greed_index"],
                "rsi": market_data["rsi"],
                "adx": adx,
                "regime": regime,
                "trend": trend,
            }
        )

        equity_curve.append(running_capital + tracker.mark_to_market(close))

    if tracker.position != 0 and bars:
        pnl, exit_cost = tracker.close_position(bars[-1]["close"], bars[-1]["date"])
        total_pnl += pnl
        running_capital += pnl
        if pnl > 0:
            win_count += 1
            gross_wins += pnl
        else:
            loss_count += 1
            gross_losses += abs(pnl)

    daily_returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] > 0:
            daily_returns.append((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1])

    total_trades = win_count + loss_count
    profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else 0.0
    avg_win = (gross_wins / win_count) if win_count > 0 else 0.0
    avg_loss = (gross_losses / loss_count) if loss_count > 0 else 0.0
    return {
        "symbol": platform_symbol,
        "bars": bar_count,
        "trades": total_trades,
        "wins": win_count,
        "losses": loss_count,
        "win_rate": (win_count / total_trades * 100) if total_trades > 0 else 0.0,
        "total_pnl": round(total_pnl, 2),
        "total_return_pct": round((running_capital - capital) / capital * 100, 2),
        "final_capital": round(running_capital, 2),
        "sharpe": round(calculate_sharpe(daily_returns), 2),
        "max_drawdown_pct": round(calculate_max_drawdown(equity_curve) * 100, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "filtered": filtered_count,
    }


async def main_async():
    print("=" * 70)
    print("  UNIFIED BACKTEST v4 - ATR Risk Management + Dynamic Universe")
    print("  Fixes: trailing stop, trend filter, regime filter, ATR sizing")
    print(f"  Period: {START_DATE} to {END_DATE}")
    print(f"  Capital: ${INITIAL_CAPITAL:,.0f} per symbol")
    print("=" * 70)

    # 1. Haal Dynamic Universe op
    from backend.agents.portfolio_manager_agent import PortfolioManagerAgent
    from backend.execution.portfolio_manager import get_portfolio_manager

    pm_agent = PortfolioManagerAgent(portfolio_manager=get_portfolio_manager())

    universe = await pm_agent.get_tradable_universe()
    print(f"  Tradable Universe found in DB: {len(universe)} symbols")

    # 2. Filter the hardcoded map
    dynamic_map = {}
    for sym in universe:
        if sym in SYMBOL_MAP:
            dynamic_map[sym] = SYMBOL_MAP[sym]
        else:
            # Basic conversion for cryptos if not in map
            if sym.endswith("/EUR"):
                dynamic_map[sym] = sym.replace("/", "-")
            elif sym.endswith("/USD"):
                dynamic_map[sym] = sym.replace("/", "-")
            else:
                dynamic_map[sym] = sym

    print(f"  Mapped Symbols to test: {len(dynamic_map)}")

    from backend.storage.clickhouse_client import ClickHouseClient

    clickhouse_client = ClickHouseClient()
    # Assume connected or just provide for late binding

    analyzer = UnifiedMarketAnalyzer()
    guna_council = DynamicGunaCouncil()
    mind_council = MindCouncil()
    body_council = BodyCouncil()
    buddhi = BuddhiMind()
    vedastro_agent = MockVedastroAgent()

    # Inject ClickHouse for persistence
    for agent in [guna_council, mind_council, body_council, buddhi]:
        if hasattr(agent, "clickhouse_client"):
            agent.clickhouse_client = clickhouse_client

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logger = AgentDecisionLogger(LOG_DIR / "v5_decisions.jsonl")

    all_results = []
    skipped = []
    t_start = time.time()

    for i, (platform_sym, yf_ticker) in enumerate(dynamic_map.items(), 1):
        print(f"\n[{i}/{len(dynamic_map)}] {platform_sym} ({yf_ticker})...", end=" ", flush=True)
        bars = download_data(platform_sym, yf_ticker)
        if bars is None:
            print("SKIPPED")
            skipped.append(platform_sym)
            continue

        print(f"{len(bars)} bars", end=" -> ", flush=True)
        result = run_backtest_for_symbol(
            platform_sym,
            bars,
            analyzer,
            guna_council,
            mind_council,
            body_council,
            buddhi,
            vedastro_agent,
            logger,
            INITIAL_CAPITAL,
        )
        all_results.append(result)

        sign = "+" if result["total_pnl"] >= 0 else ""
        print(
            f"{result['trades']} trades | "
            f"WR: {result['win_rate']:.0f}% | "
            f"PnL: {sign}${result['total_pnl']:,.0f} | "
            f"Sharpe: {result['sharpe']:.2f}"
        )

    logger.close()
    elapsed = time.time() - t_start

    # == PER-SYMBOL CSV ==
    csv_path = RESULTS_DIR / "v5_per_symbol.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "symbol",
                "bars",
                "trades",
                "wins",
                "losses",
                "win_rate",
                "total_pnl",
                "total_return_pct",
                "final_capital",
                "sharpe",
                "max_drawdown_pct",
                "profit_factor",
                "avg_win",
                "avg_loss",
                "filtered",
            ],
        )
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)

    # == AGGREGATE ==
    total_trades = sum(r["trades"] for r in all_results)
    total_wins = sum(r["wins"] for r in all_results)
    total_pnl = sum(r["total_pnl"] for r in all_results)
    total_capital = INITIAL_CAPITAL * len(all_results)
    agg_return = (total_pnl / total_capital * 100) if total_capital > 0 else 0
    agg_winrate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    sharpes = [r["sharpe"] for r in all_results if r["trades"] > 0]
    avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0.0
    avg_dd = (
        sum(r["max_drawdown_pct"] for r in all_results) / len(all_results) if all_results else 0
    )
    total_filtered = sum(r.get("filtered", 0) for r in all_results)
    total_gross_w = sum(r["avg_win"] * r["wins"] for r in all_results)
    total_gross_l = sum(r["avg_loss"] * r["losses"] for r in all_results)
    agg_pf = (total_gross_w / total_gross_l) if total_gross_l > 0 else 0.0
    agg_avg_win = (total_gross_w / total_wins) if total_wins > 0 else 0
    agg_avg_loss = (
        (total_gross_l / (total_trades - total_wins)) if (total_trades - total_wins) > 0 else 0
    )

    sorted_by_pnl = sorted(all_results, key=lambda x: x["total_pnl"], reverse=True)

    # == REPORT ==
    report_path = RESULTS_DIR / "v5_summary_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Unified Backtest Report v5 - Meta-Edge Optimalisatie\n\n")
        f.write(
            "**Pipeline:** TechnicalIndicators -> Councils -> Buddhi -> ATR Trailing Stop (v5)\n"
        )
        f.write("**Optimizations:** ATR SL 1.8, TP 4.5, Fees 0.15%, Slippage 0.05%, Conf-Sizing\n")
        f.write(f"**Period:** {START_DATE} to {END_DATE}\n")
        f.write(
            f"**Symbols:** {len(all_results)} tested, {len(skipped)} skipped (from dynamic universe)\n"
        )
        f.write(f"**Capital:** ${INITIAL_CAPITAL:,.0f} per symbol\n")
        f.write(f"**Runtime:** {elapsed:.1f}s\n\n")

        f.write("## Aggregate Performance\n\n")
        f.write("| Metric | Value |\n|---|---|\n")
        f.write(f"| Total Trades | {total_trades} |\n")
        f.write(f"| Filtered (blocked by trend/regime/conf) | {total_filtered} |\n")
        f.write(f"| Win Rate | {agg_winrate:.1f}% |\n")
        f.write(f"| Total PnL | ${total_pnl:,.2f} |\n")
        f.write(f"| Aggregate Return | {agg_return:.2f}% |\n")
        f.write(f"| Profit Factor | {agg_pf:.2f} |\n")
        f.write(f"| Avg Win | ${agg_avg_win:,.0f} |\n")
        f.write(f"| Avg Loss | ${agg_avg_loss:,.0f} |\n")
        f.write(
            f"| R:R Ratio | {(agg_avg_win / agg_avg_loss if agg_avg_loss > 0 else 0):.2f}:1 |\n"
        )
        f.write(f"| Average Sharpe | {avg_sharpe:.2f} |\n")
        f.write(f"| Average Max Drawdown | {avg_dd:.2f}% |\n\n")

        f.write("## Comparison: v1 vs v2 vs v3 vs v4\n\n")
        f.write("| | v1 (Sprint 1-4) | v2 (Triad) | v3 (Unified) | v4 (ATR) |\n")
        f.write("|---|---|---|---|---|\n")
        f.write(f"| Trades | 503 | 0 | 8,889 | {total_trades} |\n")
        f.write(f"| Win Rate | 46.7% | N/A | 45.1% | {agg_winrate:.1f}% |\n")
        f.write(f"| Total PnL | +$5,558 | $0 | +$24,989 | ${total_pnl:+,.0f} |\n")
        f.write(f"| Profit Factor | ? | N/A | 0.95 | {agg_pf:.2f} |\n")
        f.write(f"| Avg Sharpe | -0.13 | N/A | -0.00 | {avg_sharpe:.2f} |\n\n")

        f.write("## Top 10 Performers\n\n")
        f.write("| Symbol | Trades | WR | PnL | Return | Sharpe | PF | Avg W/L |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in sorted_by_pnl[:10]:
            s = "+" if r["total_pnl"] >= 0 else ""
            wl = f"${r['avg_win']:,.0f}/${r['avg_loss']:,.0f}" if r["trades"] > 0 else "N/A"
            f.write(
                f"| {r['symbol']} | {r['trades']} | {r['win_rate']:.0f}% "
                f"| {s}${r['total_pnl']:,.0f} | {r['total_return_pct']:.1f}% "
                f"| {r['sharpe']:.2f} | {r['profit_factor']:.1f} | {wl} |\n"
            )

        f.write("\n## Bottom 10 Performers\n\n")
        f.write("| Symbol | Trades | WR | PnL | Return | Sharpe | PF | Avg W/L |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in sorted_by_pnl[-10:]:
            s = "+" if r["total_pnl"] >= 0 else ""
            wl = f"${r['avg_win']:,.0f}/${r['avg_loss']:,.0f}" if r["trades"] > 0 else "N/A"
            f.write(
                f"| {r['symbol']} | {r['trades']} | {r['win_rate']:.0f}% "
                f"| {s}${r['total_pnl']:,.0f} | {r['total_return_pct']:.1f}% "
                f"| {r['sharpe']:.2f} | {r['profit_factor']:.1f} | {wl} |\n"
            )

        if skipped:
            f.write(f"\n## Skipped\n{', '.join(skipped)}\n")

    print("\n" + "=" * 70)
    print("  UNIFIED BACKTEST v4 COMPLETE")
    print("=" * 70)
    print(f"  Symbols: {len(all_results)} tested, {len(skipped)} skipped")
    print(f"  Total Trades: {total_trades} (filtered: {total_filtered})")
    print(f"  Win Rate: {agg_winrate:.1f}%")
    print(f"  Total PnL: ${total_pnl:,.2f}")
    print(f"  Profit Factor: {agg_pf:.2f}")
    rr = agg_avg_win / agg_avg_loss if agg_avg_loss > 0 else 0
    print(f"  Avg Win/Loss: ${agg_avg_win:,.0f} / ${agg_avg_loss:,.0f} (R:R {rr:.2f}:1)")
    print(f"  Average Sharpe: {avg_sharpe:.2f}")
    print(f"  Average Max DD: {avg_dd:.2f}%")
    print(f"  Runtime: {elapsed:.1f}s")
    print(f"\n  Report: {report_path}")
    print(f"  CSV: {csv_path}")
    print(f"  Log: {LOG_DIR / 'v4_decisions.jsonl'}")
    print("=" * 70)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main_async())
