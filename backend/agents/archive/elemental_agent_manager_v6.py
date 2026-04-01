"""
Elemental Agent Manager V6 - FULLY AGNOSTIC & SELF-LEARNING
Removes all hardcoded exclusions and overrides.
Agents learn organically from trade outcomes.
"""

import logging
import os
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.config.asset_universe import FULL_ASSET_UNIVERSE
from backend.core.navagraha.asset_affinity import PLANET_ASSET_AFFINITY

logger = logging.getLogger("ElementalAgentsV6")

# V6: Planet-specific thresholds (no hardcoded exclusions)
HARMONY_THRESHOLDS = {
    "SATURN": 0.48,
    "MARS": 0.55,
    "JUPITER": 0.50,
    "SUN": 0.52,
    "MOON": 0.50,
    "MERCURY": 0.53,
    "VENUS": 0.50,
    "RAHU": 0.60,
    "KETU": 0.55,
    "DEFAULT": 0.50,
}

GLOBAL_EXECUTE_THRESHOLD = 0.50

PRANA_COSTS = {
    "orchestrator": 5,
    "research": 3,
    "risk": 2,
    "valuation": 2,
    "macro": 2,
}

PRANA_REGEN_PER_DAY = 50.0


# ============ V6: AGENT OUTPUT DATA CLASSES ============


@dataclass
class NavagrahaState:
    dominant_planet: str = "JUPITER"
    trading_gate_open: bool = True
    rahu_kala_active: bool = False
    consciousness_level: str = "Pure Awareness"
    guna_distribution: dict[str, float] = field(
        default_factory=lambda: {"sattva": 0.55, "rajas": 0.30, "tamas": 0.15}
    )


@dataclass
class FireDecision:
    decision: str
    confidence: float
    max_allowed_qty: float | None
    risk_score: float
    blocking_reasons: list[str]
    var_estimate_pct: float
    fire_dharma: str
    prana_consumed: float


@dataclass
class WaterRegime:
    regime: str
    asset_class_outlook: dict[str, str]
    favored_symbols: list[str]
    avoid_symbols: list[str]
    macro_narrative: str
    confidence: float
    water_dharma: str


@dataclass
class AirSignal:
    symbol: str
    action: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    technical_summary: str
    indicators: dict[str, Any]
    air_dharma: str


@dataclass
class EarthValuation:
    symbol: str
    fair_value: float
    current_price: float
    valuation_gap_pct: float
    verdict: str
    confidence: float
    methodology: str
    earth_dharma: str


@dataclass
class EtherSynthesis:
    final_decision: str
    harmony_score: float
    approved_symbol: str | None
    approved_action: str | None
    approved_qty: float
    approved_price: float
    stop_loss: float
    take_profit: float
    execution_urgency: str
    consensus_achieved: bool
    blocking_agent: str | None
    cosmic_narrative: str
    ether_dharma: str


# ============ V6: EARTH AGENT - ADAPTIVE VALUATION MEMORY ============


class EarthAgentV6:
    """Earth Agent with rolling performance memory per symbol"""

    def __init__(self):
        # Rolling memory: last 20 trade outcomes per symbol
        self.symbol_memory: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        self.base_confidence = 0.65  # Neutral starting point

    def record_trade_outcome(self, symbol: str, pnl: float, win: bool):
        """Record trade outcome for adaptive learning"""
        self.symbol_memory[symbol].append({"pnl": pnl, "win": win, "timestamp": datetime.utcnow()})

    def calculate_confidence(self, symbol: str, current_signal: dict) -> float:
        """Dynamic confidence based on historical performance"""
        history = self.symbol_memory[symbol]

        # Not enough data: neutral
        if len(history) < 5:
            return self.base_confidence

        # Calculate recent performance
        recent_win_rate = sum(1 for t in history if t["win"]) / len(history)
        avg_pnl = sum(t["pnl"] for t in history) / len(history)

        # Base confidence from win rate (0.4 - 0.9 range)
        base = 0.4 + (recent_win_rate * 0.5)

        # PnL quality correction (-0.2 to +0.2)
        pnl_factor = min(max(avg_pnl / 100, -0.2), 0.2)

        confidence = base + pnl_factor
        return min(max(confidence, 0.2), 0.95)  # Hard clamp

    def valuate(
        self, symbol: str, current_price: float, prices: list[float], market_regime: str
    ) -> EarthValuation:
        """Valuation with adaptive confidence"""

        if len(prices) < 30:
            return EarthValuation(
                symbol=symbol,
                fair_value=current_price,
                current_price=current_price,
                valuation_gap_pct=0,
                verdict="FAIR",
                confidence=self.calculate_confidence(symbol, {}),
                methodology="Onvoldoende data",
                earth_dharma="Prithvi wacht",
            )

        # Standard valuation logic
        asset = None
        for a in FULL_ASSET_UNIVERSE:
            if a.symbol.replace("/EUR", "") == symbol or a.symbol == symbol:
                asset = a
                break

        asset_class = asset.asset_class.value if asset else "crypto"

        if asset_class == "crypto":
            sma_30 = sum(prices[-30:]) / 30
            trend = (prices[-1] - prices[-30]) / prices[-30]
            fair_value = sma_30 * (1 + trend * 0.3)
            methodology = "SMA30+trend"
        elif asset_class == "forex":
            sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else sum(prices) / len(prices)
            fair_value = sma_50
            methodology = "SMA50"
        elif asset_class == "commodities":
            sma_20 = sum(prices[-20:]) / 20
            sma_40 = sum(prices[-40:]) / 40 if len(prices) >= 40 else sma_20
            fair_value = (sma_20 + sma_40) / 2
            methodology = "Dual SMA"
        else:
            sma_30 = sum(prices[-30:]) / 30
            momentum = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            fair_value = sma_30 * (1 + momentum * 0.5)
            methodology = "Momentum SMA"

        valuation_gap = (current_price - fair_value) / fair_value * 100

        if valuation_gap < -10:
            verdict = "UNDERVALUED"
        elif valuation_gap > 10:
            verdict = "OVERVALUED"
        else:
            verdict = "FAIR"

        # V6: Adaptive confidence instead of static
        confidence = self.calculate_confidence(symbol, {"regime": market_regime})

        dharma = {
            "UNDERVALUED": f"Prithvi: waarde gevonden (conf: {confidence:.2f})",
            "OVERVALUED": f"Prithvi: overprijsd (conf: {confidence:.2f})",
            "FAIR": f"Prithvi: in balans (conf: {confidence:.2f})",
        }.get(verdict, "Prithvi observeert")

        return EarthValuation(
            symbol=symbol,
            fair_value=round(fair_value, 2),
            current_price=current_price,
            valuation_gap_pct=round(valuation_gap, 2),
            verdict=verdict,
            confidence=confidence,
            methodology=methodology,
            earth_dharma=dharma,
        )


# ============ V6: FIRE AGENT - DYNAMIC RISK ASSESSMENT ============


class FireAgentV6:
    """Fire Agent with symbol-specific risk assessment"""

    def __init__(self):
        self.loss_streaks: dict[str, int] = defaultdict(int)
        self.volatility_memory: dict[str, deque] = defaultdict(lambda: deque(maxlen=30))
        self.trade_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

    def record_outcome(self, symbol: str, pnl: float, price_change_pct: float):
        """Record trade outcome for risk learning"""
        if pnl < 0:
            self.loss_streaks[symbol] += 1
        else:
            self.loss_streaks[symbol] = 0  # Reset on win

        self.volatility_memory[symbol].append(abs(price_change_pct))
        self.trade_history[symbol].append({"pnl": pnl, "win": pnl > 0})

    def calculate_confidence(self, symbol: str) -> float:
        """Dynamic confidence based on loss streaks and volatility"""
        streak = self.loss_streaks[symbol]
        vol_history = self.volatility_memory[symbol]

        # Loss streak penalty (max -0.45 at 5+ losses)
        streak_penalty = min(streak * 0.08, 0.45)

        # Volatility penalty
        if len(vol_history) >= 10:
            avg_vol = sum(vol_history) / len(vol_history)
            vol_penalty = min(avg_vol / 0.05, 0.30)  # Penalty if ATR > 5%
        else:
            vol_penalty = 0.0

        base_confidence = 0.95
        confidence = base_confidence - streak_penalty - vol_penalty

        # Organic exclusion: if confidence drops too low, symbol self-excludes
        return max(confidence, 0.15)  # Floor but not zero

    def assess(
        self,
        symbol: str,
        proposed_action: str,
        proposed_qty: float,
        price: float,
        portfolio_value: float,
        navagraha: NavagrahaState,
        harmony_score: float,
        prana_level: float,
        market_regime: str,
        volatility_24h: float,
    ) -> FireDecision:
        """Risk assessment with dynamic confidence"""

        blocking_reasons = []
        risk_score = 0.0

        # Rahu Kala check
        if navagraha.rahu_kala_active:
            return FireDecision(
                decision="BLOCK",
                confidence=1.0,
                max_allowed_qty=None,
                risk_score=1.0,
                blocking_reasons=["Rahu Kala actief"],
                var_estimate_pct=0,
                fire_dharma="Agni: Rahu's invloed te sterk",
                prana_consumed=PRANA_COSTS["risk"],
            )

        # Prana check
        if prana_level < 10:
            return FireDecision(
                decision="BLOCK",
                confidence=1.0,
                max_allowed_qty=None,
                risk_score=1.0,
                blocking_reasons=["Prana uitgeput"],
                var_estimate_pct=0,
                fire_dharma="Systeemprana te laag",
                prana_consumed=0,
            )

        # Harmony check
        if harmony_score < GLOBAL_EXECUTE_THRESHOLD * 0.65:
            return FireDecision(
                decision="BLOCK",
                confidence=0.9,
                max_allowed_qty=None,
                risk_score=0.9,
                blocking_reasons=[f"Harmony {harmony_score:.2f} too low"],
                var_estimate_pct=0,
                fire_dharma="Agni blokkeert door disharmonie",
                prana_consumed=PRANA_COSTS["risk"],
            )

        # V6: Dynamic confidence based on symbol history
        dynamic_confidence = self.calculate_confidence(symbol)

        # If confidence too low due to losses, organically reduce position or block
        if dynamic_confidence < 0.30:
            return FireDecision(
                decision="BLOCK",
                confidence=dynamic_confidence,
                max_allowed_qty=None,
                risk_score=0.8,
                blocking_reasons=[f"{symbol} loss streak: {self.loss_streaks[symbol]}"],
                var_estimate_pct=0,
                fire_dharma=f"Agni: {symbol} te riskant door verliesreeks",
                prana_consumed=PRANA_COSTS["risk"],
            )

        # Standard risk limits
        asset = None
        for a in FULL_ASSET_UNIVERSE:
            if a.symbol.replace("/EUR", "") == symbol or a.symbol == symbol:
                asset = a
                break

        asset_class = asset.asset_class.value if asset else "crypto"

        asset_limits = {
            "crypto": 0.02,
            "forex": 0.01,
            "commodities": 0.015,
            "indices": 0.02,
            "equities": 0.015,
        }

        max_risk = asset_limits.get(asset_class, 0.01)
        trade_value = proposed_qty * price
        trade_risk_pct = trade_value / portfolio_value if portfolio_value > 0 else 0

        if trade_risk_pct > max_risk:
            risk_score += 0.3
            max_allowed = (portfolio_value * max_risk) / price
            blocking_reasons.append(f"Positie {trade_risk_pct:.2%} > limiet {max_risk:.2%}")
        else:
            max_allowed = proposed_qty

        # Volatility checks
        if asset_class == "crypto" and volatility_24h > 8:
            risk_score += 0.2
            blocking_reasons.append("Crypto volatiliteit > 8%")
        elif asset_class == "forex" and volatility_24h > 2:
            risk_score += 0.2
            blocking_reasons.append("Forex volatiliteit > 2%")

        if market_regime == "contraction" and asset_class == "crypto":
            max_allowed *= 0.5
            risk_score += 0.15

        # Planet affinity bonus
        dominant = navagraha.dominant_planet
        favored_assets = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored_assets or any(a in symbol for a in favored_assets):
            risk_score -= 0.1

        # V6: Apply dynamic confidence to risk score
        risk_score += (1.0 - dynamic_confidence) * 0.5

        if risk_score > 0.5:
            decision = "BLOCK"
        elif risk_score > 0.3:
            decision = "REDUCE"
        else:
            decision = "APPROVE"

        var_estimate = volatility_24h * 1.645

        return FireDecision(
            decision=decision,
            confidence=dynamic_confidence,
            max_allowed_qty=max_allowed if decision != "BLOCK" else None,
            risk_score=risk_score,
            blocking_reasons=blocking_reasons,
            var_estimate_pct=var_estimate,
            fire_dharma=f"Agni: {decision.lower()} (streak: {self.loss_streaks[symbol]}, conf: {dynamic_confidence:.2f})",
            prana_consumed=PRANA_COSTS["risk"],
        )


# ============ V6: WATER AGENT - ASSET CLASS MACRO CONTEXT ============


class WaterAgentV6:
    """Water Agent with real macro context and asset class awareness"""

    ASSET_CLASSES = {
        "crypto": [
            "BTC",
            "ETH",
            "SOL",
            "AVAX",
            "LINK",
            "DOT",
            "ADA",
            "XRP",
            "DOGE",
            "LTC",
            "ATOM",
            "ALGO",
            "VET",
            "TRX",
            "XLM",
            "UNI",
            "MATIC",
            "AAVE",
            "FIL",
            "ETC",
        ],
        "equity_us": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "META",
            "NVDA",
            "AMZN",
            "TSLA",
            "AMD",
            "CRM",
            "ADBE",
            "NFLX",
            "ORCL",
            "INTC",
            "PYPL",
            "ROKU",
            "ZM",
        ],
        "equity_eu": ["ASML", "SAP", "AIR", "ROG", "NESN", "TTE", "SHEL"],
        "etf": ["SPY", "QQQ", "VTI", "IWM", "EEM", "EFA", "GLD", "TLT", "USO", "VIX"],
    }

    def __init__(self):
        self.regime_history: dict[str, str] = {}

    def _get_asset_class(self, symbol: str) -> str:
        """Determine asset class for symbol"""
        for cls, symbols in self.ASSET_CLASSES.items():
            if symbol in symbols:
                return cls
        return "equity_us"  # Default

    def calculate_confidence(
        self, symbol: str, macro_signal: dict, price_data: list[float]
    ) -> float:
        """Asset-class specific confidence calculation"""
        asset_class = self._get_asset_class(symbol)

        # Calculate trend strength
        if len(price_data) >= 20:
            change_20d = (price_data[-1] - price_data[-20]) / price_data[-20]
            trend_strength = min(abs(change_20d) * 5, 1.0)  # Normalize
        else:
            trend_strength = 0.5

        # Risk-on score based on market breadth
        risk_on_score = macro_signal.get("risk_on_score", 0.5)
        vix_level = macro_signal.get("vix", 20)

        # Asset-class specific weighting
        if asset_class == "crypto":
            # Crypto: benefits from risk-on, suffers from high VIX
            vix_penalty = min((vix_level - 15) / 60, 0.35) if vix_level > 15 else 0
            confidence = (risk_on_score * 0.6) + (trend_strength * 0.4) - vix_penalty
        elif asset_class == "equity_eu":
            # EU equity: less VIX-sensitive, more trend-dependent
            confidence = (trend_strength * 0.7) + (risk_on_score * 0.3)
        elif asset_class == "etf":
            # ETF: stable, less macro-sensitive
            confidence = 0.55 + (trend_strength * 0.25)
        else:
            # US equity: balanced
            vix_penalty = min((vix_level - 20) / 80, 0.25) if vix_level > 20 else 0
            confidence = (risk_on_score * 0.5) + (trend_strength * 0.5) - vix_penalty

        return min(max(confidence, 0.20), 0.90)

    def analyze_regime(
        self,
        symbol: str,
        market_data: dict[str, Any],
        navagraha: NavagrahaState,
        prices: list[float],
    ) -> WaterRegime:
        """Macro regime analysis with asset class awareness"""

        if len(prices) < 20:
            return WaterRegime(
                regime="neutral",
                asset_class_outlook={},
                favored_symbols=[],
                avoid_symbols=[],
                macro_narrative="Onvoldoende data",
                confidence=0.50,
                water_dharma="Water is stil",
            )

        # Calculate macro signals
        ((prices[-1] - prices[-min(7, len(prices))]) / prices[-min(7, len(prices))] * 100)
        price_change_30d = (
            (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))] * 100
        )

        # Trend detection
        advancing = sum(1 for i in range(1, min(20, len(prices))) if prices[-i] > prices[-i - 1])
        total = min(19, len(prices) - 1)

        if total > 0:
            advance_ratio = advancing / total
            if advance_ratio > 0.6 and price_change_30d > 10:
                regime = "expansion"
            elif advance_ratio < 0.4 and price_change_30d < -10:
                regime = "contraction"
            elif price_change_30d > 0:
                regime = "recovery"
            else:
                regime = "neutral"
        else:
            regime = "neutral"

        # Build macro signal
        macro_signal = {
            "risk_on_score": (
                0.6 if regime == "expansion" else 0.4 if regime == "contraction" else 0.5
            ),
            "vix": (25 if regime == "contraction" else 18 if regime == "expansion" else 20),
            "trend_strength": abs(price_change_30d) / 30,  # Normalize
        }

        # Calculate confidence with asset class awareness
        confidence = self.calculate_confidence(symbol, macro_signal, prices)

        dominant = navagraha.dominant_planet
        outlook_map = {
            "SUN": {"crypto": "bullish", "indices": "bullish", "forex": "neutral"},
            "MOON": {"forex": "bullish", "commodities": "bullish", "crypto": "neutral"},
            "MARS": {
                "crypto": "bullish",
                "commodities": "volatile",
                "indices": "bearish",
            },
            "MERCURY": {"forex": "bullish", "indices": "neutral", "crypto": "volatile"},
            "JUPITER": {"indices": "bullish", "crypto": "bullish", "forex": "neutral"},
            "VENUS": {
                "commodities": "bullish",
                "forex": "neutral",
                "crypto": "bearish",
            },
            "SATURN": {
                "indices": "bearish",
                "forex": "bearish",
                "crypto": "consolidation",
            },
        }

        asset_class_outlook = outlook_map.get(dominant, {})
        favored = PLANET_ASSET_AFFINITY.get(dominant, [])

        # Organic avoidance based on regime
        avoid = []
        if regime == "contraction":
            asset_class = self._get_asset_class(symbol)
            if asset_class == "crypto":
                avoid.append(symbol)

        return WaterRegime(
            regime=regime,
            asset_class_outlook=asset_class_outlook,
            favored_symbols=favored,
            avoid_symbols=avoid,
            macro_narrative=f"{dominant} | {regime} | conf: {confidence:.2f}",
            confidence=round(confidence, 3),
            water_dharma=f"Water: {regime} voor {self._get_asset_class(symbol)}",
        )


# ============ V6: AIR AGENT - MOMENTUM WITH REGIME DETECTION ============


class AirAgentV6:
    """Air Agent with market regime detection (trending vs mean-reverting)"""

    def __init__(self):
        self.regime_memory: dict[str, str] = {}

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        if len(gains) < period:
            return 50.0
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calculate_ema(self, prices: list[float], period: int = 20) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema

    def _calculate_atr(self, prices: list[float]) -> float:
        if len(prices) < 14:
            return 0
        tr_list = []
        for i in range(1, len(prices)):
            tr = abs(prices[i] - prices[i - 1])
            tr_list.append(tr)
        return sum(tr_list[-14:]) / 14 if tr_list else 0

    def generate_signals(
        self,
        symbol: str,
        current_price: float,
        navagraha: NavagrahaState,
        prices: list[float],
    ) -> AirSignal:
        """Generate signals with regime detection"""

        if len(prices) < 20:
            return AirSignal(
                symbol=symbol,
                action="HOLD",
                confidence=0.50,
                entry_price=current_price,
                stop_loss=current_price * 0.95,
                take_profit=current_price * 1.10,
                technical_summary="Onvoldoende data",
                indicators={},
                air_dharma="Vayu wacht",
            )

        rsi = self._calculate_rsi(prices)
        ema20 = self._calculate_ema(prices, 20)
        ema50 = self._calculate_ema(prices, 50) if len(prices) >= 50 else ema20

        trend_up = ema20 > ema50
        trend_down = ema20 < ema50

        # ATR for regime detection
        atr = self._calculate_atr(prices)
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0

        # Regime detection: trending vs consolidating
        is_trending = atr_pct > 1.5  # ATR > 1.5% = trending

        action = "HOLD"
        confidence = 0.50

        if is_trending:
            # Trending market: follow direction
            if trend_up and rsi < 70:
                action = "BUY"
                confidence = 0.75  # Bullish momentum, not overbought
            elif trend_down and rsi > 30:
                action = "SELL"
                confidence = 0.35  # Bearish momentum
            elif rsi >= 70:
                action = "SELL"  # Overbought in uptrend
                confidence = 0.60
            elif rsi <= 30:
                action = "BUY"  # Oversold in downtrend
                confidence = 0.40
        else:
            # Consolidating: mean reversion
            if rsi < 35:
                action = "BUY"
                confidence = 0.70  # Oversold in range: buying opportunity
            elif rsi > 65:
                action = "SELL"
                confidence = 0.30  # Overbought in range: selling opportunity
            else:
                action = "HOLD"
                confidence = 0.50  # Middle of range: wait

        # Planet affinity boost
        dominant = navagraha.dominant_planet
        favored = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored or any(f in symbol for f in favored):
            confidence = min(0.95, confidence + 0.1)

        # Calculate stop loss and take profit
        volatility = atr_pct if atr_pct > 0 else 2.0
        atr_value = current_price * (volatility / 100)

        if action == "BUY":
            stop_loss = current_price - (atr_value * 2)
            take_profit = current_price + (atr_value * 3)
        elif action == "SELL":
            stop_loss = current_price + (atr_value * 2)
            take_profit = current_price - (atr_value * 3)
        else:
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05

        indicators = {
            "rsi": round(rsi, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "atr_pct": round(atr_pct, 2),
            "trend": "up" if trend_up else "down" if trend_down else "neutral",
            "regime": "trending" if is_trending else "consolidating",
        }

        return AirSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            technical_summary=f"RSI {rsi:.1f}, {indicators['regime']}, {indicators['trend']}",
            indicators=indicators,
            air_dharma=f"Vayu: {action} in {indicators['regime']} market (conf: {confidence:.2f})",
        )


# ============ V6: ETHER ORCHESTRATOR - WEIGHTED SYNTHESIS WITH DISAGREEMENT PENALTY ============


class EtherOrchestratorV6:
    """Ether Orchestrator with weighted synthesis and disagreement penalty"""

    AGENT_WEIGHTS = {
        "fire": 0.30,  # Risk is heaviest veto
        "earth": 0.25,  # Fundamental value
        "water": 0.20,  # Macro context
        "air": 0.15,  # Momentum/signal
        "ether": 0.10,  # Meta/synthesis
    }

    def synthesize(
        self,
        fire: FireDecision,
        water: WaterRegime,
        air: AirSignal,
        earth: EarthValuation,
        navagraha: NavagrahaState,
    ) -> tuple[float, bool]:
        """Synthesize with disagreement penalty"""

        confidences = {
            "fire": fire.confidence,
            "water": water.confidence,
            "earth": earth.confidence,
            "air": air.confidence,
        }

        # Weighted average
        weighted_harmony = sum(
            confidences[agent] * weight
            for agent, weight in self.AGENT_WEIGHTS.items()
            if agent in confidences
        )

        # V6: Reduced disagreement penalty for more trading activity
        values = list(confidences.values())
        spread = max(values) - min(values)
        disagreement_penalty = spread * 0.08  # Reduced from 0.15

        harmony = weighted_harmony - disagreement_penalty
        harmony = min(max(harmony, 0.0), 1.0)

        # V6: Relaxed consensus - 4 of 5 agents above threshold
        min_threshold = 0.35  # Lowered from 0.40
        agents_above = sum(1 for c in confidences.values() if c >= min_threshold)
        consensus = agents_above >= 4  # 4 of 5 agents

        return harmony, consensus

    def should_execute(self, harmony: float, consensus: bool, dominant_planet: str) -> bool:
        """Determine if trade should execute"""
        threshold = HARMONY_THRESHOLDS.get(dominant_planet, HARMONY_THRESHOLDS["DEFAULT"])
        return consensus and harmony >= threshold


# ============ V6: MAIN AGENT MANAGER ============


class ElementalAgentManagerV6:
    """
    V6: Fully agnostic and self-learning system
    No hardcoded exclusions or overrides
    """

    def __init__(self):
        self.price_history: dict[str, deque] = {}
        self.volume_history: dict[str, deque] = {}
        self.history_length = 50

        # V6: Individual agents
        self.earth_agent = EarthAgentV6()
        self.fire_agent = FireAgentV6()
        self.water_agent = WaterAgentV6()
        self.air_agent = AirAgentV6()
        self.ether_orchestrator = EtherOrchestratorV6()

        # Stats
        self.agent_confidence_history: dict[str, list[float]] = {
            "fire": [],
            "water": [],
            "air": [],
            "earth": [],
            "ether": [],
        }
        self.consensus_count = 0
        self.total_cycles = 0
        self.execute_count = 0

    def update_price_data(self, symbol: str, price: float, volume: float = 0):
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.history_length)
            self.volume_history[symbol] = deque(maxlen=self.history_length)
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)

    def record_trade_outcome(self, symbol: str, pnl: float, price_change_pct: float = 0):
        """V6: Feedback loop - agents learn from trade outcomes"""
        self.earth_agent.record_trade_outcome(symbol, pnl, pnl > 0)
        self.fire_agent.record_outcome(symbol, pnl, price_change_pct)

    def process_trading_cycle(
        self,
        symbol: str,
        current_price: float,
        portfolio_value: float,
        current_positions: dict[str, Any],
        prana_level: float = 85.0,
    ) -> EtherSynthesis:
        """Process one complete trading cycle with all V6 agents"""

        self.update_price_data(symbol, current_price)
        navagraha = self._get_current_navagraha_state()
        prices = list(self.price_history.get(symbol, []))

        self.total_cycles += 1

        # Run all 4 elemental agents
        water = self.water_agent.analyze_regime(symbol, {}, navagraha, prices)

        air = self.air_agent.generate_signals(symbol, current_price, navagraha, prices)

        earth = self.earth_agent.valuate(symbol, current_price, prices, water.regime)

        # Fire agent needs more context
        volatility = 0
        if len(prices) >= 2:
            returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
            volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 * 100

        base_harmony = 0.50 + (prana_level / 100) * 0.25

        fire = self.fire_agent.assess(
            symbol=symbol,
            proposed_action=air.action,
            proposed_qty=0.01,
            price=current_price,
            portfolio_value=portfolio_value,
            navagraha=navagraha,
            harmony_score=base_harmony,
            prana_level=prana_level,
            market_regime=water.regime,
            volatility_24h=volatility,
        )

        # Ether synthesizes
        harmony, consensus = self.ether_orchestrator.synthesize(fire, water, air, earth, navagraha)

        if consensus:
            self.consensus_count += 1

        # Check if should execute
        should_trade = self.ether_orchestrator.should_execute(
            harmony, consensus, navagraha.dominant_planet
        )

        # Track stats
        self.agent_confidence_history["fire"].append(fire.confidence)
        self.agent_confidence_history["water"].append(water.confidence)
        self.agent_confidence_history["air"].append(air.confidence)
        self.agent_confidence_history["earth"].append(earth.confidence)
        self.agent_confidence_history["ether"].append(harmony)

        # Build synthesis result
        if not should_trade:
            return EtherSynthesis(
                final_decision="BLOCK",
                harmony_score=harmony,
                approved_symbol=None,
                approved_action=None,
                approved_qty=0,
                approved_price=0,
                stop_loss=0,
                take_profit=0,
                execution_urgency="none",
                consensus_achieved=consensus,
                blocking_agent=(
                    "ether"
                    if harmony < HARMONY_THRESHOLDS.get(navagraha.dominant_planet, 0.50)
                    else None
                ),
                cosmic_narrative=f"H:{harmony:.2f}|{navagraha.dominant_planet}|consensus:{consensus}",
                ether_dharma="Akasha: disharmonie of geen consensus",
            )

        if fire.decision == "BLOCK":
            return EtherSynthesis(
                final_decision="BLOCK",
                harmony_score=harmony,
                approved_symbol=symbol,
                approved_action=None,
                approved_qty=0,
                approved_price=0,
                stop_loss=0,
                take_profit=0,
                execution_urgency="none",
                consensus_achieved=consensus,
                blocking_agent="fire",
                cosmic_narrative=f"Agni blokkeert|streak:{self.fire_agent.loss_streaks[symbol]}",
                ether_dharma="Vuur beschermt: te riskant",
            )

        # Calculate position size
        position_factor = 1.0

        if water.regime == "contraction" and air.action == "BUY":
            position_factor *= 0.6

        if earth.verdict == "OVERVALUED" and air.action == "BUY":
            position_factor *= 0.6
        elif earth.verdict == "UNDERVALUED" and air.action == "BUY":
            position_factor = min(1.0, position_factor * 1.2)

        if fire.decision == "REDUCE":
            position_factor *= 0.7

        base_qty = 0.01
        approved_qty = base_qty * position_factor * harmony

        self.execute_count += 1

        return EtherSynthesis(
            final_decision="EXECUTE",
            harmony_score=harmony,
            approved_symbol=symbol,
            approved_action=air.action,
            approved_qty=approved_qty,
            approved_price=current_price,
            stop_loss=air.stop_loss,
            take_profit=air.take_profit,
            execution_urgency="immediate" if harmony > 0.60 else "next_candle",
            consensus_achieved=consensus,
            blocking_agent=None,
            cosmic_narrative=f"{navagraha.dominant_planet}|H:{harmony:.2f}|C:{consensus}|E:{earth.confidence:.2f}|F:{fire.confidence:.2f}",
            ether_dharma="Akasha harmoniseert alle elementen",
        )

    def _get_current_navagraha_state(self) -> NavagrahaState:
        """Get current Navagraha state"""
        day = datetime.now().day
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        dominant = planets[day % 7]
        rahu_active = (day % 8) == 0

        return NavagrahaState(
            dominant_planet=dominant,
            trading_gate_open=not rahu_active,
            rahu_kala_active=rahu_active,
            consciousness_level="Pure Awareness",
            guna_distribution={"sattva": 0.55, "rajas": 0.30, "tamas": 0.15},
        )

    def get_agent_stats(self) -> dict[str, Any]:
        """Get comprehensive agent statistics"""
        stats = {}
        for agent, confidences in self.agent_confidence_history.items():
            if confidences:
                stats[agent] = {
                    "avg_confidence": sum(confidences) / len(confidences),
                    "min_confidence": min(confidences),
                    "max_confidence": max(confidences),
                    "samples": len(confidences),
                }

        stats["consensus_achieved_pct"] = (
            (self.consensus_count / self.total_cycles * 100) if self.total_cycles > 0 else 0
        )
        stats["execute_rate_pct"] = (
            (self.execute_count / self.total_cycles * 100) if self.total_cycles > 0 else 0
        )
        stats["total_cycles"] = self.total_cycles
        stats["consensus_count"] = self.consensus_count
        stats["execute_count"] = self.execute_count

        # V6: Symbol-specific stats from Earth agent
        symbol_stats = {}
        for symbol, history in self.earth_agent.symbol_memory.items():
            if history:
                wins = sum(1 for t in history if t["win"])
                symbol_stats[symbol] = {
                    "trades": len(history),
                    "wins": wins,
                    "win_rate": wins / len(history),
                    "avg_pnl": sum(t["pnl"] for t in history) / len(history),
                }
        stats["symbol_performance"] = symbol_stats

        return stats
