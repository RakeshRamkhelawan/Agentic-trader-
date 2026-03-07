"""
Full v7 Backtest - Consciousness Architecture (Optimized + Offline)
- Uses backtest-safe agent adapters (no external API calls)
- Direct synchronous calls to all agents
- Logs EVERY agent decision for fine-tuning
- 20 Symbols across 4 sectors
"""

import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# --- PROJECT SETUP ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from backend.councils.buddhi_mind import get_buddhi_mind

# --- CORE COMPONENTS ---
from backend.councils.dynamic_guna_council import DynamicGunaCouncil
from backend.orchestration.shiva_shakti_sync import get_synchronizer

# Reusing proven v6 infra
from backend.scripts.run_v6_backtest import (
    AgentDecisionLogger,
    PositionTracker,
    UnifiedMarketAnalyzer,
    UniverseRiskManager,
    download_data,
)

# =============================================================================
# CONFIG v7
# =============================================================================

START_DATE = "2020-01-01"
END_DATE = "2026-03-04"
INITIAL_CAPITAL = 100_000.0
MAX_POSITION_FRACTION = 0.15
RISK_PER_TRADE = 0.015
MIN_CONFIDENCE = 0.55
MAX_HOLD_BARS = 30
ATR_SL_MULT = 1.8
ATR_TP_MULT = 5.0

TRANSACTION_FEE = 0.0015
SLIPPAGE = 0.0005

DATA_CACHE_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_cache"
LOG_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_logs"
RESULTS_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_results"

SYMBOL_MAP = {
    "BTC/EUR": "BTC-EUR",
    "ETH/EUR": "ETH-EUR",
    "ADA/EUR": "ADA-EUR",
    "DOT/EUR": "DOT-EUR",
    "XRP/EUR": "XRP-EUR",
    "SOL/EUR": "SOL-EUR",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "EUR/GBP": "EURGBP=X",
    "USD/CHF": "CHF=X",
    "AUD/USD": "AUDUSD=X",
    "SPX500": "^GSPC",
    "NAS100": "^IXIC",
    "GER40": "^GDAXI",
    "UK100": "^FTSE",
    "XAU/USD": "GC=F",
    "XAG/USD": "SI=F",
    "OIL/USD": "CL=F",
    "COTTON/USD": "CT=F",
}

UNIVERSE_GROUPS = {
    "crypto": ["BTC/EUR", "ETH/EUR", "ADA/EUR", "DOT/EUR", "XRP/EUR", "SOL/EUR"],
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/GBP", "USD/CHF", "AUD/USD"],
    "indices": ["SPX500", "NAS100", "GER40", "UK100"],
    "commodities": ["XAU/USD", "XAG/USD", "OIL/USD", "COTTON/USD"],
}


# =============================================================================
# BACKTEST-SAFE AGENT ADAPTERS (No external API calls)
# =============================================================================


class BacktestSentimentAgent:
    """
    Offline sentiment agent for backtesting.
    Uses momentum and volatility as proxy for market sentiment.
    """

    def analyze(self, market_data: dict) -> dict:
        momentum = market_data.get("momentum_1d", 0.0)
        vol = market_data.get("volatility_1m", 0.02)
        rsi = market_data.get("rsi", 50.0)

        # RSI-based sentiment
        if rsi > 70:
            sentiment = 0.8  # Very bullish (but potentially overbought)
            perspective = "bullish"
        elif rsi > 55:
            sentiment = 0.6
            perspective = "bullish"
        elif rsi < 30:
            sentiment = 0.2  # Very bearish (but potentially oversold)
            perspective = "bearish"
        elif rsi < 45:
            sentiment = 0.4
            perspective = "bearish"
        else:
            sentiment = 0.5
            perspective = "neutral"

        # Adjust by momentum
        if momentum > 0.02:
            sentiment = min(1.0, sentiment + 0.15)
        elif momentum < -0.02:
            sentiment = max(0.0, sentiment - 0.15)

        # High vol reduces confidence
        confidence = max(0.3, 1.0 - vol * 10)

        action = 1 if perspective == "bullish" else 2 if perspective == "bearish" else 0

        return {
            "action": action,
            "confidence": round(confidence, 3),
            "reasoning": f"Sentiment(RSI={rsi:.0f}, Mom={momentum:.3f}): {perspective}",
            "sentiment_score": round(sentiment, 3),
        }


class BacktestVedAstroAgent:
    """
    Offline VedAstro proxy for backtesting.
    Simulates planetary-cycle alignment using lunar phase approximation.
    In production, this calls the real VedAstro API.
    """

    def analyze(self, date_str: str, market_data: dict) -> dict:
        # Simple lunar phase proxy: use day-of-year modulo 29.5 (synodic month)
        try:
            if isinstance(date_str, str):
                dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            else:
                dt = date_str
            day_of_year = dt.timetuple().tm_yday
        except:
            day_of_year = 1

        lunar_phase = (day_of_year % 29.5) / 29.5  # 0-1 cycle

        # Planetary alignment score (simplified)
        # New moon (0, 1) = caution, Full moon (0.5) = activity
        alignment = math.sin(lunar_phase * 2 * math.pi)

        # Combine with market trend
        trend = market_data.get("trend", 0)

        if alignment > 0.3 and trend > 0:
            action = 1  # Buy - favorable cosmic + trend
            confidence = 0.6 + alignment * 0.2
            reasoning = (
                f"VedAstro: Favorable alignment (phase={lunar_phase:.2f}, score={alignment:.2f})"
            )
        elif alignment < -0.3 and trend < 0:
            action = 2  # Sell - unfavorable cosmic + downtrend
            confidence = 0.6 + abs(alignment) * 0.2
            reasoning = (
                f"VedAstro: Unfavorable alignment (phase={lunar_phase:.2f}, score={alignment:.2f})"
            )
        else:
            action = 0  # Hold
            confidence = 0.5
            reasoning = (
                f"VedAstro: Neutral alignment (phase={lunar_phase:.2f}, score={alignment:.2f})"
            )

        return {
            "action": action,
            "confidence": round(min(confidence, 0.85), 3),
            "reasoning": reasoning,
            "lunar_phase": round(lunar_phase, 3),
            "alignment_score": round(alignment, 3),
        }


class BacktestRegimeAgent:
    """
    Offline regime detection agent for backtesting.
    Uses the RegimeDetector directly.
    """

    def __init__(self):
        from backend.core.regime_detector import RegimeDetector

        self.detector = RegimeDetector()

    def analyze(self, price_history: list, current_price: float) -> dict:
        if len(price_history) < 50:
            return {
                "action": 0,
                "confidence": 0.5,
                "reasoning": "Insufficient data",
                "regime": "unknown",
            }

        sma50, sma200, vol = self.detector.calculate_indicators(price_history)
        regime = self.detector.detect(current_price, sma50, sma200, vol)

        # Regime informs direction
        regime_str = regime.value if hasattr(regime, "value") else str(regime)
        if regime_str in ["bull", "BULL"]:
            action = 1
            confidence = 0.7
        elif regime_str in ["bear", "BEAR"]:
            action = 2
            confidence = 0.7
        elif regime_str in ["volatile", "VOLATILE"]:
            action = 0
            confidence = 0.8  # Confident in staying out
        else:
            action = 0
            confidence = 0.5

        return {
            "action": action,
            "confidence": round(confidence, 3),
            "reasoning": f"Regime: {regime_str} (SMA50={sma50:.2f}, SMA200={sma200:.2f})",
            "regime": regime_str,
        }


def aggregate_agent_decisions(sentiment, vedastro, regime, guna_result):
    """
    Aggregate individual agent decisions into a collective view.
    Weights: Sentiment=0.25, VedAstro=0.25, Regime=0.25, Guna=0.25
    """
    weights = {
        "sentiment": 0.25,
        "vedastro": 0.25,
        "regime": 0.25,
        "guna": 0.25,
    }

    agents = {
        "sentiment": sentiment,
        "vedastro": vedastro,
        "regime": regime,
        "guna": {
            "action": (
                1
                if guna_result.get("perspective") == "bullish"
                else 2 if guna_result.get("perspective") == "bearish" else 0
            ),
            "confidence": guna_result.get("confidence", 0.5),
            "reasoning": f"Guna: {guna_result.get('guna', {}).get('dominant', 'unknown')} dominant",
        },
    }

    # Weighted vote
    buy_score = 0.0
    sell_score = 0.0
    hold_score = 0.0
    total_conf = 0.0

    for name, dec in agents.items():
        w = weights[name]
        c = dec["confidence"]
        if dec["action"] == 1:
            buy_score += w * c
        elif dec["action"] == 2:
            sell_score += w * c
        else:
            hold_score += w * c
        total_conf += w * c

    if buy_score > sell_score and buy_score > hold_score:
        action = 1
        confidence = buy_score / (buy_score + sell_score + hold_score + 1e-9)
    elif sell_score > buy_score and sell_score > hold_score:
        action = 2
        confidence = sell_score / (buy_score + sell_score + hold_score + 1e-9)
    else:
        action = 0
        confidence = hold_score / (buy_score + sell_score + hold_score + 1e-9)

    return {
        "action": action,
        "confidence": round(confidence, 3),
        "agent_inputs": agents,
        "reasoning": f"Collective: buy={buy_score:.2f} sell={sell_score:.2f} hold={hold_score:.2f}",
    }


# =============================================================================
# MAIN BACKTEST
# =============================================================================


def run_v7_backtest():
    print("=" * 80)
    print("  v7 PORTFOLIO BACKTEST - CONSCIOUSNESS ARCHITECTURE (OPTIMIZED)")
    print("  Agents: Guna | Sentiment | VedAstro | Regime | Buddhi | Spanda")
    print("=" * 80)

    # 1. Download & Align Data
    all_data = {}
    dates_set = set()
    for sym, ticker in SYMBOL_MAP.items():
        bars = download_data(sym, ticker)
        if bars:
            all_data[sym] = bars
            for b in bars:
                dates_set.add(b["date"])

    sorted_dates = sorted(list(dates_set))
    print(f"\n  Data: {len(all_data)} symbols, {len(sorted_dates)} trading days")

    # 2. Initialize Agents (ALL SYNCHRONOUS, NO EXTERNAL CALLS)
    analyzer = UnifiedMarketAnalyzer()
    guna_council = DynamicGunaCouncil()
    buddhi = get_buddhi_mind()
    sentiment_agent = BacktestSentimentAgent()
    vedastro_agent = BacktestVedAstroAgent()
    regime_agent = BacktestRegimeAgent()
    sync = get_synchronizer()

    risk_manager = UniverseRiskManager(max_total=5, max_per_sector=2)
    trackers = {sym: PositionTracker() for sym in all_data.keys()}

    capital = INITIAL_CAPITAL
    equity_curve = []

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    decision_logger = AgentDecisionLogger(LOG_DIR / "v7_agent_decisions.jsonl")
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} for sym in all_data.keys()}
    price_history = {
        sym: {"prices": [], "vols": [], "highs": [], "lows": []} for sym in all_data.keys()
    }

    fine_tuning_records = []
    total_days = len(sorted_dates)
    progress_interval = max(1, total_days // 20)

    print("  Starting simulation...")
    sim_start = time.time()

    for day_idx, date in enumerate(sorted_dates):
        if day_idx % progress_interval == 0:
            pct = (day_idx / total_days) * 100
            elapsed = time.time() - sim_start
            print(
                f"  [{pct:5.1f}%] Day {day_idx}/{total_days} | Capital: ${capital:,.0f} | Time: {elapsed:.0f}s"
            )

        # Step 1: Update bars
        current_prices = {}
        for sym, bars in all_data.items():
            bar = next((b for b in bars if b["date"] == date), None)
            if bar:
                current_prices[sym] = bar
                p_hist = price_history[sym]
                p_hist["prices"].append(bar["close"])
                p_hist["vols"].append(bar["volume"])
                p_hist["highs"].append(bar["high"])
                p_hist["lows"].append(bar["low"])
                if len(p_hist["prices"]) > 200:
                    for k in p_hist:
                        p_hist[k] = p_hist[k][-200:]

        # Step 2: Check Exits
        for sym, tracker in trackers.items():
            if tracker.position != 0 and sym in current_prices:
                bar = current_prices[sym]
                tracker.bars_in_trade += 1
                tracker.update_trailing(bar["close"])
                reason = tracker.check_exit(bar["close"])

                # Spanda Sync Exit
                if not reason and len(price_history[sym]["prices"]) >= 20:
                    m_data = analyzer.analyze(
                        price_history[sym]["prices"],
                        price_history[sym]["vols"],
                        price_history[sym]["highs"],
                        price_history[sym]["lows"],
                    )
                    sync_report = sync.calculate_sync(
                        tracker.mark_to_market(bar["close"]),
                        m_data["volatility_1m"],
                        capital,
                    )
                    if sync_report["harmony_level"] == "low":
                        reason = "spanda_disharmony"

                if not reason and tracker.bars_in_trade >= MAX_HOLD_BARS:
                    reason = "max_hold"

                if reason:
                    pnl, cost = tracker.close_position(bar["close"], date)
                    capital += pnl
                    risk_manager.remove_trade(sym)
                    symbol_metrics[sym]["trades"] += 1
                    if pnl > 0:
                        symbol_metrics[sym]["wins"] += 1
                    symbol_metrics[sym]["pnl"] += pnl
                    decision_logger.log(
                        {
                            "ts": date,
                            "symbol": sym,
                            "action": "close",
                            "reason": reason,
                            "pnl": round(pnl, 2),
                        }
                    )

        # Step 3: Scan for Entries
        for sym, tracker in trackers.items():
            if (
                tracker.position == 0
                and sym in current_prices
                and len(price_history[sym]["prices"]) >= 65
            ):
                sector = next((s for s, syms in UNIVERSE_GROUPS.items() if sym in syms), "unknown")

                if risk_manager.can_open(sym, sector):
                    p_hist = price_history[sym]
                    market_data = analyzer.analyze(
                        p_hist["prices"], p_hist["vols"], p_hist["highs"], p_hist["lows"]
                    )

                    # ========== CONSCIOUSNESS ARCHITECTURE ==========

                    # L1: Guna Council (Samkhya Interaction Logic)
                    guna_result = guna_council.analyze(market_data)

                    # L2: Sentiment Agent (Offline - RSI/Momentum based)
                    sentiment_result = sentiment_agent.analyze(market_data)

                    # L2: VedAstro Oracle (Offline - Lunar phase proxy)
                    vedastro_result = vedastro_agent.analyze(date, market_data)

                    # L2: Regime Agent (Direct detector)
                    regime_result = regime_agent.analyze(p_hist["prices"], market_data["close"])

                    # L2: Aggregate all agents
                    collective = aggregate_agent_decisions(
                        sentiment_result, vedastro_result, regime_result, guna_result
                    )

                    # L2: Buddhi Mind (Viveka Filter)
                    # Map views to council_types that Buddhi expects: guna, mind, body
                    guna_dict = guna_result.get("guna", {})
                    council_views = [
                        {
                            "council_type": "guna",
                            "perspective": guna_result.get("perspective", "neutral"),
                            "confidence": guna_result.get("confidence", 0.5),
                            # Viveka filter needs these:
                            "guna_vector": {
                                "sattva": guna_dict.get("sattva", 0.33),
                                "rajas": guna_dict.get("rajas", 0.33),
                                "tamas": guna_dict.get("tamas", 0.33),
                            },
                            "interactions": guna_result.get("interactions", {}),
                        },
                        {
                            # "mind" = Sentiment + VedAstro aggregated
                            "council_type": "mind",
                            "perspective": (
                                "bullish"
                                if (sentiment_result["action"] + vedastro_result["action"]) >= 2
                                else (
                                    "bearish"
                                    if (sentiment_result["action"] + vedastro_result["action"]) >= 4
                                    else (
                                        "neutral"
                                        if (
                                            sentiment_result["action"] == 0
                                            and vedastro_result["action"] == 0
                                        )
                                        else (
                                            "bullish"
                                            if sentiment_result["action"] == 1
                                            or vedastro_result["action"] == 1
                                            else (
                                                "bearish"
                                                if sentiment_result["action"] == 2
                                                or vedastro_result["action"] == 2
                                                else "neutral"
                                            )
                                        )
                                    )
                                )
                            ),
                            "confidence": (
                                sentiment_result["confidence"] + vedastro_result["confidence"]
                            )
                            / 2,
                        },
                        {
                            # "body" = Regime detection
                            "council_type": "body",
                            "perspective": (
                                "bullish"
                                if regime_result["action"] == 1
                                else "bearish" if regime_result["action"] == 2 else "neutral"
                            ),
                            "confidence": regime_result["confidence"],
                        },
                    ]

                    buddhi_market_data = {
                        "volatility_1m": market_data.get("volatility_1m", 0.02),
                        "regime": regime_result.get("regime", "sideways"),
                        "market_guna": guna_result.get("guna", {}),
                    }

                    decision = buddhi.decide(
                        council_views=council_views,
                        market_data=buddhi_market_data,
                        session_id="v7_backtest",
                        timestamp=date,
                    )

                    # L3: Spanda Sync (Harmony Check)
                    sync_report = sync.calculate_sync(0, market_data["volatility_1m"], capital)

                    # ========== DECISION EXECUTION ==========
                    if decision.action in ["buy", "sell"] and decision.confidence >= MIN_CONFIDENCE:
                        if sync_report["harmony_level"] != "low":
                            action = "bullish" if decision.action == "buy" else "bearish"
                            confidence = decision.confidence

                            risk_usd = capital * RISK_PER_TRADE
                            if confidence >= 0.85:
                                risk_usd *= 1.25
                            stop_dist = market_data["atr"] * ATR_SL_MULT
                            if stop_dist <= 0:
                                stop_dist = 0.01
                            pos_usd = (risk_usd / stop_dist) * market_data["close"]

                            if pos_usd >= 200:
                                cost = tracker.open_position(
                                    action, pos_usd, market_data["close"], market_data["atr"]
                                )
                                capital -= cost
                                risk_manager.add_trade(sym, sector, action, risk_usd)

                                # === FINE-TUNING LOG ===
                                log_entry = {
                                    "ts": date,
                                    "symbol": sym,
                                    "sector": sector,
                                    "action": "open",
                                    "side": action,
                                    "confidence": round(confidence, 3),
                                    "pos_usd": round(pos_usd, 2),
                                    # L1: Guna
                                    "guna_dominant": guna_result.get("guna", {}).get(
                                        "dominant", "?"
                                    ),
                                    "guna_sattva": round(
                                        guna_result.get("guna", {}).get("sattva", 0), 3
                                    ),
                                    "guna_rajas": round(
                                        guna_result.get("guna", {}).get("rajas", 0), 3
                                    ),
                                    "guna_tamas": round(
                                        guna_result.get("guna", {}).get("tamas", 0), 3
                                    ),
                                    "guna_perspective": guna_result.get("perspective", "?"),
                                    # L2: Sentiment
                                    "sentiment_action": sentiment_result["action"],
                                    "sentiment_confidence": sentiment_result["confidence"],
                                    "sentiment_reasoning": sentiment_result["reasoning"][:100],
                                    # L2: VedAstro
                                    "vedastro_action": vedastro_result["action"],
                                    "vedastro_confidence": vedastro_result["confidence"],
                                    "vedastro_lunar_phase": vedastro_result.get("lunar_phase", 0),
                                    "vedastro_alignment": vedastro_result.get("alignment_score", 0),
                                    # L2: Regime
                                    "regime_action": regime_result["action"],
                                    "regime_confidence": regime_result["confidence"],
                                    "regime_detected": regime_result.get("regime", "?"),
                                    # L2: Buddhi
                                    "buddhi_action": decision.action,
                                    "buddhi_coherence": round(decision.coherence, 3),
                                    "buddhi_rationale": decision.rationale[:200],
                                    # L3: Spanda
                                    "spanda_harmony": sync_report["harmony_level"],
                                    "spanda_score": round(sync_report.get("sync_score", 0.5), 3),
                                    # Market
                                    "price": round(market_data["close"], 4),
                                    "atr": round(market_data["atr"], 6),
                                    "volatility": round(market_data["volatility_1m"], 4),
                                    "rsi": round(market_data.get("rsi", 50), 1),
                                }
                                decision_logger.log(log_entry)
                                fine_tuning_records.append(log_entry)

        equity_curve.append(capital)

    # ============================
    # FINAL REPORT
    # ============================
    sim_elapsed = time.time() - sim_start
    total_trades = sum(m["trades"] for m in symbol_metrics.values())
    total_wins = sum(m["wins"] for m in symbol_metrics.values())
    total_pnl = sum(m["pnl"] for m in symbol_metrics.values())
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    roi = (total_pnl / INITIAL_CAPITAL) * 100

    peak = max(equity_curve) if equity_curve else INITIAL_CAPITAL
    trough = min(equity_curve) if equity_curve else INITIAL_CAPITAL
    max_dd = ((peak - trough) / peak) * 100 if peak > 0 else 0

    print("\n" + "=" * 80)
    print("  v7 BACKTEST RESULTATEN - CONSCIOUSNESS ARCHITECTURE")
    print("=" * 80)
    print(f"  Periode:           {START_DATE} -> {END_DATE}")
    print(f"  Startkapitaal:     ${INITIAL_CAPITAL:,.2f}")
    print(f"  Eindkapitaal:      ${capital:,.2f}")
    print(f"  Totaal PNL:        ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Trades:            {total_trades}")
    print(f"  Winratio:          {win_rate:.1f}%")
    print(f"  Max Drawdown:      {max_dd:.1f}%")
    print(f"  Simulatietijd:     {sim_elapsed:.1f}s")
    print(f"  Fine-tuning data:  {len(fine_tuning_records)} entries")
    print("=" * 80)

    # Per-sector breakdown
    print("\n  --- PER SECTOR ---")
    for sector, syms in UNIVERSE_GROUPS.items():
        s_trades = sum(
            symbol_metrics.get(s, {}).get("trades", 0) for s in syms if s in symbol_metrics
        )
        s_wins = sum(symbol_metrics.get(s, {}).get("wins", 0) for s in syms if s in symbol_metrics)
        s_pnl = sum(symbol_metrics.get(s, {}).get("pnl", 0) for s in syms if s in symbol_metrics)
        s_wr = (s_wins / s_trades * 100) if s_trades > 0 else 0
        print(f"  {sector:12s} | Trades: {s_trades:3d} | WR: {s_wr:5.1f}% | PNL: ${s_pnl:>10,.2f}")

    # Per-symbol breakdown (top performers)
    print("\n  --- TOP SYMBOLEN ---")
    sorted_syms = sorted(symbol_metrics.items(), key=lambda x: x[1]["pnl"], reverse=True)
    for sym, m in sorted_syms:
        if m["trades"] > 0:
            wr = m["wins"] / m["trades"] * 100
            print(
                f"  {sym:12s} | Trades: {m['trades']:3d} | WR: {wr:5.1f}% | PNL: ${m['pnl']:>10,.2f}"
            )

    # Save fine-tuning data
    ft_path = RESULTS_DIR / "v7_fine_tuning_data.jsonl"
    with open(ft_path, "w", encoding="utf-8") as f:
        for record in fine_tuning_records:
            f.write(json.dumps(record, default=str) + "\n")
    print(f"\n  Fine-tuning data: {ft_path}")

    # Save equity curve
    eq_path = RESULTS_DIR / "v7_equity_curve.csv"
    with open(eq_path, "w", encoding="utf-8") as f:
        f.write("day,equity\n")
        for i, eq in enumerate(equity_curve):
            f.write(f"{i},{eq:.2f}\n")
    print(f"  Equity curve:     {eq_path}")
    print(f"  Agent logs:       {LOG_DIR / 'v7_agent_decisions.jsonl'}")


if __name__ == "__main__":
    run_v7_backtest()
