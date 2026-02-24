"""
Elemental Agent Manager V7 - CALIBRATED ADAPTIVE
Fixes V6 regression with warm-start confidence and proper calibration
Expected: Restore V5 performance + organic adaptivity
"""

import logging
import os
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.core.navagraha.asset_affinity import PLANET_ASSET_AFFINITY

logger = logging.getLogger("ElementalAgentsV7")

# ============ V7: OPTIMIZED THRESHOLDS ============
HARMONY_THRESHOLDS = {
    "SATURN": 0.45,  # V7: Balanced for adaptive mode
    "MARS": 0.52,
    "JUPITER": 0.48,
    "SUN": 0.50,
    "MOON": 0.47,
    "MERCURY": 0.50,
    "VENUS": 0.48,
    "RAHU": 0.58,
    "KETU": 0.54,
    "DEFAULT": 0.48,
}

GLOBAL_EXECUTE_THRESHOLD = 0.45  # V7: Lower for new confidence range

# V7: Warm-start confidence per asset class (based on V4/V5 performance)
WARM_START_CONFIDENCE = {
    "crypto": 0.72,
    "equity_us": 0.85,
    "equity_eu": 0.78,
    "etf": 0.88,
    "commodities": 0.75,
    "forex": 0.80,
}

# V7: Asset class mapping
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
    "commodities": ["XAU", "XAG", "OIL"],
    "forex": ["EURUSD", "GBPUSD", "USDJPY"],
}

PRANA_COSTS = {
    "orchestrator": 5,
    "research": 3,
    "risk": 2,
    "valuation": 2,
    "macro": 2,
}

PRANA_REGEN_PER_DAY = 50.0


# ============ DATA CLASSES ============


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


# ============ V7: EARTH AGENT - WARM START ============


class EarthAgentV7:
    """Earth Agent with warm-start confidence per asset class"""

    def __init__(self):
        self.symbol_memory: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

    def _get_asset_class(self, symbol: str) -> str:
        for cls, symbols in ASSET_CLASSES.items():
            if symbol in symbols:
                return cls
        return "equity_us"

    def record_trade_outcome(self, symbol: str, pnl: float, win: bool):
        self.symbol_memory[symbol].append({"pnl": pnl, "win": win, "timestamp": datetime.utcnow()})

    def calculate_confidence(self, symbol: str) -> float:
        """V7: Warm-start with asset class baseline"""
        history = self.symbol_memory[symbol]
        asset_class = self._get_asset_class(symbol)

        # Not enough data: use warm-start confidence
        if len(history) < 5:
            return WARM_START_CONFIDENCE.get(asset_class, 0.80)

        # Calculate adaptive confidence
        recent_win_rate = sum(1 for t in history if t["win"]) / len(history)
        avg_pnl = sum(t["pnl"] for t in history) / len(history)

        base = 0.4 + (recent_win_rate * 0.5)
        pnl_factor = min(max(avg_pnl / 100, -0.15), 0.15)  # V7: Reduced impact

        confidence = base + pnl_factor

        # V7: Blend with warm-start (don't go too low)
        warm_start = WARM_START_CONFIDENCE.get(asset_class, 0.80)
        blended = (confidence * 0.7) + (warm_start * 0.3)  # 70% adaptive, 30% warm

        return min(max(blended, 0.40), 0.95)

    def valuate(
        self, symbol: str, current_price: float, prices: list[float], market_regime: str
    ) -> EarthValuation:
        if len(prices) < 30:
            return EarthValuation(
                symbol=symbol,
                fair_value=current_price,
                current_price=current_price,
                valuation_gap_pct=0,
                verdict="FAIR",
                confidence=self.calculate_confidence(symbol),
                methodology="Onvoldoende data",
                earth_dharma="Prithvi wacht",
            )

        # Standard valuation
        asset_class = self._get_asset_class(symbol)

        if asset_class == "crypto":
            sma_30 = sum(prices[-30:]) / 30
            trend = (prices[-1] - prices[-30]) / prices[-30]
            fair_value = sma_30 * (1 + trend * 0.3)
            methodology = "SMA30+trend"
        elif asset_class in ["equity_us", "equity_eu"]:
            sma_30 = sum(prices[-30:]) / 30
            momentum = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            fair_value = sma_30 * (1 + momentum * 0.5)
            methodology = "Momentum SMA"
        else:  # ETF
            sma_20 = sum(prices[-20:]) / 20
            sma_40 = sum(prices[-40:]) / 40 if len(prices) >= 40 else sma_20
            fair_value = (sma_20 + sma_40) / 2
            methodology = "Dual SMA"

        valuation_gap = (current_price - fair_value) / fair_value * 100

        if valuation_gap < -10:
            verdict = "UNDERVALUED"
        elif valuation_gap > 10:
            verdict = "OVERVALUED"
        else:
            verdict = "FAIR"

        confidence = self.calculate_confidence(symbol)

        return EarthValuation(
            symbol=symbol,
            fair_value=round(fair_value, 2),
            current_price=current_price,
            valuation_gap_pct=round(valuation_gap, 2),
            verdict=verdict,
            confidence=confidence,
            methodology=methodology,
            earth_dharma=f"Prithvi: {verdict} (conf: {confidence:.2f})",
        )


# ============ V7: FIRE AGENT - CALIBRATED RISK ============


class FireAgentV7:
    """Fire Agent with calibrated loss streak penalties"""

    def __init__(self):
        self.loss_streaks: dict[str, int] = defaultdict(int)
        self.volatility_memory: dict[str, deque] = defaultdict(lambda: deque(maxlen=30))

    def record_outcome(self, symbol: str, pnl: float, price_change_pct: float):
        if pnl < 0:
            self.loss_streaks[symbol] += 1
        else:
            self.loss_streaks[symbol] = 0
        self.volatility_memory[symbol].append(abs(price_change_pct))

    def calculate_confidence(self, symbol: str) -> float:
        """V7: Calibrated penalties (less aggressive than V6)"""
        streak = self.loss_streaks[symbol]
        vol_history = self.volatility_memory[symbol]

        # V7: Reduced streak penalty (was 0.08 per streak)
        streak_penalty = min(streak * 0.06, 0.30)  # Max -0.30 at 5+ losses

        if len(vol_history) >= 10:
            avg_vol = sum(vol_history) / len(vol_history)
            vol_penalty = min(avg_vol / 0.08, 0.25)  # Penalty if ATR > 8%
        else:
            vol_penalty = 0.0

        # V7: Higher base confidence (was 0.95)
        base_confidence = 0.92
        confidence = base_confidence - streak_penalty - vol_penalty

        return max(confidence, 0.35)

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
        blocking_reasons = []
        risk_score = 0.0

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

        # V7: Dynamic confidence
        dynamic_confidence = self.calculate_confidence(symbol)

        # V7: Only block if very low confidence (organic exclusion)
        if dynamic_confidence < 0.25:
            return FireDecision(
                decision="BLOCK",
                confidence=dynamic_confidence,
                max_allowed_qty=None,
                risk_score=0.8,
                blocking_reasons=[f"{symbol} loss streak: {self.loss_streaks[symbol]}"],
                var_estimate_pct=0,
                fire_dharma=f"Agni: {symbol} te riskant",
                prana_consumed=PRANA_COSTS["risk"],
            )

        # Standard risk limits
        asset_class = ASSET_CLASSES.get("equity_us")  # Default
        for cls, symbols in ASSET_CLASSES.items():
            if symbol in symbols:
                asset_class = cls
                break

        asset_limits = {
            "crypto": 0.02,
            "forex": 0.01,
            "commodities": 0.015,
            "indices": 0.02,
            "equities": 0.015,
            "etf": 0.02,
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

        # V7: Relaxed volatility checks
        if asset_class == "crypto" and volatility_24h > 10:  # Was 8
            risk_score += 0.15
            blocking_reasons.append("Crypto volatiliteit > 10%")
        elif asset_class == "forex" and volatility_24h > 3:  # Was 2
            risk_score += 0.15
            blocking_reasons.append("Forex volatiliteit > 3%")

        if market_regime == "contraction" and asset_class == "crypto":
            max_allowed *= 0.6
            risk_score += 0.1

        # Planet affinity
        dominant = navagraha.dominant_planet
        favored_assets = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored_assets or any(a in symbol for a in favored_assets):
            risk_score -= 0.1

        # Apply dynamic confidence
        risk_score += (1.0 - dynamic_confidence) * 0.4

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
            fire_dharma=f"Agni: {decision.lower()} (conf: {dynamic_confidence:.2f})",
            prana_consumed=PRANA_COSTS["risk"],
        )


# ============ V7: WATER AGENT ============


class WaterAgentV7:
    """Water Agent with asset class awareness"""

    def __init__(self):
        pass

    def _get_asset_class(self, symbol: str) -> str:
        for cls, symbols in ASSET_CLASSES.items():
            if symbol in symbols:
                return cls
        return "equity_us"

    def analyze_regime(
        self, symbol: str, navagraha: NavagrahaState, prices: list[float]
    ) -> WaterRegime:
        if len(prices) < 20:
            # V7: Use warm-start for insufficient data
            asset_class = self._get_asset_class(symbol)
            base_conf = WARM_START_CONFIDENCE.get(asset_class, 0.80)
            return WaterRegime(
                regime="neutral",
                asset_class_outlook={},
                favored_symbols=[],
                avoid_symbols=[],
                macro_narrative="Onvoldoende data",
                confidence=base_conf * 0.85,  # Slightly lower for uncertainty
                water_dharma="Water: onvoldoende data",
            )

        # Calculate trend and regime
        price_change_30d = (
            (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))] * 100
        )

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

        # Asset class specific confidence
        asset_class = self._get_asset_class(symbol)
        base_conf = WARM_START_CONFIDENCE.get(asset_class, 0.80)

        # Adjust based on regime
        if regime == "expansion":
            confidence = base_conf * 1.05
        elif regime == "contraction":
            confidence = base_conf * 0.85
        else:
            confidence = base_conf

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

        avoid = []
        if regime == "contraction" and asset_class == "crypto":
            avoid.append(symbol)

        return WaterRegime(
            regime=regime,
            asset_class_outlook=asset_class_outlook,
            favored_symbols=favored,
            avoid_symbols=avoid,
            macro_narrative=f"{dominant} | {regime} | {asset_class}",
            confidence=round(min(confidence, 0.90), 3),
            water_dharma=f"Water: {regime} voor {asset_class}",
        )


# ============ V7: AIR AGENT ============


class AirAgentV7:
    """Air Agent with regime detection"""

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

    def generate_signals(
        self,
        symbol: str,
        current_price: float,
        navagraha: NavagrahaState,
        prices: list[float],
    ) -> AirSignal:
        if len(prices) < 20:
            # V7: Higher default confidence
            return AirSignal(
                symbol=symbol,
                action="HOLD",
                confidence=0.65,
                entry_price=current_price,
                stop_loss=current_price * 0.95,
                take_profit=current_price * 1.10,
                technical_summary="Onvoldoende data",
                indicators={},
                air_dharma="Vayu: wacht op data",
            )

        rsi = self._calculate_rsi(prices)
        ema20 = self._calculate_ema(prices, 20)
        ema50 = self._calculate_ema(prices, 50) if len(prices) >= 50 else ema20

        trend_up = ema20 > ema50
        trend_down = ema20 < ema50

        # ATR calculation
        if len(prices) >= 14:
            atr = sum(abs(prices[i] - prices[i - 1]) for i in range(-14, 0)) / 14
        else:
            atr = current_price * 0.02
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 2.0

        is_trending = atr_pct > 1.5

        action = "HOLD"
        confidence = 0.60  # V7: Higher base

        if is_trending:
            if trend_up and rsi < 70:
                action = "BUY"
                confidence = 0.78
            elif trend_down and rsi > 30:
                action = "SELL"
                confidence = 0.40
            elif rsi >= 70:
                action = "SELL"
                confidence = 0.65
            elif rsi <= 30:
                action = "BUY"
                confidence = 0.55
        else:
            if rsi < 35:
                action = "BUY"
                confidence = 0.72
            elif rsi > 65:
                action = "SELL"
                confidence = 0.35
            else:
                action = "HOLD"
                confidence = 0.55

        # Planet affinity
        dominant = navagraha.dominant_planet
        favored = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored or any(f in symbol for f in favored):
            confidence = min(0.95, confidence + 0.08)

        # Calculate stops
        atr_value = current_price * (atr_pct / 100) if atr_pct > 0 else current_price * 0.02

        if action == "BUY":
            stop_loss = current_price - (atr_value * 2)
            take_profit = current_price + (atr_value * 3)
        elif action == "SELL":
            stop_loss = current_price + (atr_value * 2)
            take_profit = current_price - (atr_value * 3)
        else:
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05

        return AirSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            technical_summary=f"RSI {rsi:.1f}, {action}",
            indicators={"rsi": round(rsi, 2), "atr_pct": round(atr_pct, 2)},
            air_dharma=f"Vayu: {action} (conf: {confidence:.2f})",
        )


# ============ V7: ETHER ORCHESTRATOR ============


class EtherOrchestratorV7:
    """Ether with reduced disagreement penalty"""

    AGENT_WEIGHTS = {
        "fire": 0.30,
        "earth": 0.25,
        "water": 0.20,
        "air": 0.15,
        "ether": 0.10,
    }

    def synthesize(
        self,
        fire: FireDecision,
        water: WaterRegime,
        air: AirSignal,
        earth: EarthValuation,
    ) -> tuple[float, bool]:
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

        # V7: Reduced disagreement penalty (was 0.15 in V6, 0.08 in adjusted V6)
        values = list(confidences.values())
        spread = max(values) - min(values)
        disagreement_penalty = spread * 0.05  # V7: Further reduced

        harmony = weighted_harmony - disagreement_penalty
        harmony = min(max(harmony, 0.0), 1.0)

        # V7: Relaxed consensus (4 of 5 agents above threshold)
        min_threshold = 0.35
        agents_above = sum(1 for c in confidences.values() if c >= min_threshold)
        consensus = agents_above >= 4

        return harmony, consensus

    def should_execute(self, harmony: float, consensus: bool, dominant_planet: str) -> bool:
        threshold = HARMONY_THRESHOLDS.get(dominant_planet, HARMONY_THRESHOLDS["DEFAULT"])
        return consensus and harmony >= threshold


# ============ V7: MAIN MANAGER ============


class ElementalAgentManagerV7:
    """V7: Calibrated adaptive system"""

    def __init__(self):
        self.price_history: dict[str, deque] = {}
        self.volume_history: dict[str, deque] = {}
        self.history_length = 50

        self.earth_agent = EarthAgentV7()
        self.fire_agent = FireAgentV7()
        self.water_agent = WaterAgentV7()
        self.air_agent = AirAgentV7()
        self.ether_orchestrator = EtherOrchestratorV7()

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
        self.update_price_data(symbol, current_price)
        navagraha = self._get_current_navagraha_state()
        prices = list(self.price_history.get(symbol, []))

        self.total_cycles += 1

        # Run all agents
        water = self.water_agent.analyze_regime(symbol, navagraha, prices)
        air = self.air_agent.generate_signals(symbol, current_price, navagraha, prices)
        earth = self.earth_agent.valuate(symbol, current_price, prices, water.regime)

        # Fire assessment
        volatility = 0
        if len(prices) >= 2:
            returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
            volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 * 100 if returns else 0

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

        # Ether synthesis
        harmony, consensus = self.ether_orchestrator.synthesize(fire, water, air, earth)

        if consensus:
            self.consensus_count += 1

        should_trade = self.ether_orchestrator.should_execute(
            harmony, consensus, navagraha.dominant_planet
        )

        # Track stats
        for agent, conf in [
            ("fire", fire.confidence),
            ("water", water.confidence),
            ("air", air.confidence),
            ("earth", earth.confidence),
        ]:
            self.agent_confidence_history[agent].append(conf)
        self.agent_confidence_history["ether"].append(harmony)

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
                blocking_agent="ether",
                cosmic_narrative=f"H:{harmony:.2f}|{navagraha.dominant_planet}|consensus:{consensus}",
                ether_dharma="Akasha: disharmonie",
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
                ether_dharma="Vuur beschermt",
            )

        # V7: Position sizing with MAX_POSITION_USD normalization
        position_factor = 1.0

        if water.regime == "contraction" and air.action == "BUY":
            position_factor *= 0.6

        if earth.verdict == "OVERVALUED" and air.action == "BUY":
            position_factor *= 0.6
        elif earth.verdict == "UNDERVALUED" and air.action == "BUY":
            position_factor = min(1.0, position_factor * 1.2)

        if fire.decision == "REDUCE":
            position_factor *= 0.7

        # V7: Normalize position size across all assets
        max_position_usd = portfolio_value * 0.002  # Max 0.2% per trade
        base_qty = max_position_usd / current_price if current_price > 0 else 0.001
        approved_qty = base_qty * position_factor * harmony

        if air.action in ["BUY", "SELL"]:
            final_decision = "EXECUTE"
            execution_urgency = "immediate" if harmony > 0.60 else "next_candle"
            self.execute_count += 1
        else:
            final_decision = "BLOCK"
            execution_urgency = "none"

        return EtherSynthesis(
            final_decision=final_decision,
            harmony_score=harmony,
            approved_symbol=symbol,
            approved_action=air.action if final_decision == "EXECUTE" else "HOLD",
            approved_qty=approved_qty,
            approved_price=current_price,
            stop_loss=air.stop_loss,
            take_profit=air.take_profit,
            execution_urgency=execution_urgency,
            consensus_achieved=consensus,
            blocking_agent=None,
            cosmic_narrative=f"{navagraha.dominant_planet}|H:{harmony:.2f}|C:{consensus}",
            ether_dharma="Akasha harmoniseert",
        )

    def _get_current_navagraha_state(self) -> NavagrahaState:
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
