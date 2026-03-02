"""
Elemental Agent Manager V2 - Vedic Trading Intelligence (OPTIMIZED)
Addresses critical issues from backtest analysis:
1. Planet-specific harmony thresholds (Saturn too restrictive)
2. Dynamic Water agent confidence (was hardcoded 0.51)
3. Weighted harmony calculation (consensus never reached)
4. Prana cost tuning (274x exhaustion events)
"""

import logging
import os
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.config.asset_universe import FULL_ASSET_UNIVERSE
from backend.core.navagraha.asset_affinity import PLANET_ASSET_AFFINITY

logger = logging.getLogger("ElementalAgentsV2")

# ============ FIX 1: PLANET-SPECIFIC HARMONY THRESHOLDS ============
HARMONY_THRESHOLDS = {
    "SATURN": 0.40,  # FIX: Lowered from 0.50 (Saturn = restrictive but not impossible)
    "MARS": 0.52,  # Higher for aggressive periods
    "JUPITER": 0.45,  # Moderate - Jupiter favors growth
    "SUN": 0.48,  # Standard
    "MOON": 0.47,  # Slightly lower - Moon favors flow
    "MERCURY": 0.50,  # Standard
    "VENUS": 0.46,  # Lower - Venus favors harmony
    "RAHU": 0.60,  # Higher - Rahu is tricky
    "KETU": 0.55,  # Higher - Ketu is spiritual/detached
    "DEFAULT": 0.48,
}

# ============ FIX 4: PRANA TUNING ============
PRANA_COSTS = {
    "orchestrator": 5,  # Reduced from 15 (batch-mode)
    "research": 3,  # Reduced from 10
    "risk": 2,  # Reduced from 5
    "valuation": 2,  # Reduced from 8
    "macro": 2,  # Reduced from 8
}

PRANA_REGEN_PER_DAY = 50.0  # Increased from 20


@dataclass
class NavagrahaState:
    """Current planetary state"""

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
    confidence: float  # FIX 2: Now dynamic
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


class ElementalAgentManagerV2:
    """
    Optimized Elemental Agent Manager with fixes for:
    - Saturn over-blocking (FIX 1)
    - Water agent hardcoded confidence (FIX 2)
    - Consensus never reached (FIX 3)
    - Prana exhaustion (FIX 4)
    """

    def __init__(self):
        self.price_history: dict[str, deque] = {}
        self.volume_history: dict[str, deque] = {}
        self.history_length = 50
        self.asset_map = {a.symbol: a for a in FULL_ASSET_UNIVERSE}

        self.agent_confidence_history: dict[str, list[float]] = {
            "fire": [],
            "water": [],
            "air": [],
            "earth": [],
            "ether": [],
        }

        # Track regime changes for Water agent
        self.regime_history: dict[str, list[str]] = {}

    def _get_asset_info(self, symbol: str):
        if symbol in self.asset_map:
            return self.asset_map[symbol]
        if f"{symbol}/EUR" in self.asset_map:
            return self.asset_map[f"{symbol}/EUR"]
        return None

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

    def _calculate_volatility(self, prices: list[float]) -> float:
        if len(prices) < 2:
            return 0
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        if not returns:
            return 0
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return (variance**0.5) * 100

    def update_price_data(self, symbol: str, price: float, volume: float = 0):
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.history_length)
            self.volume_history[symbol] = deque(maxlen=self.history_length)
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)

    # ============ FIRE AGENT ============

    def fire_agent_assess(
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

        # FIX 1: Use planet-specific threshold
        threshold = HARMONY_THRESHOLDS.get(navagraha.dominant_planet, HARMONY_THRESHOLDS["DEFAULT"])
        if harmony_score < threshold * 0.8:  # Even Fire uses adjusted threshold
            return FireDecision(
                decision="BLOCK",
                confidence=0.9,
                max_allowed_qty=None,
                risk_score=0.9,
                blocking_reasons=[f"Harmony {harmony_score:.2f} < threshold {threshold:.2f}"],
                var_estimate_pct=0,
                fire_dharma="Agni blokkeert door disharmonie",
                prana_consumed=PRANA_COSTS["risk"],
            )

        asset = self._get_asset_info(symbol)
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

        if asset_class == "crypto" and volatility_24h > 8:
            risk_score += 0.2
            blocking_reasons.append("Crypto volatiliteit > 8%")
        elif asset_class == "forex" and volatility_24h > 2:
            risk_score += 0.2
            blocking_reasons.append("Forex volatiliteit > 2%")

        if market_regime == "contraction" and asset_class == "crypto":
            max_allowed *= 0.5
            risk_score += 0.15

        dominant = navagraha.dominant_planet
        favored_assets = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored_assets or any(a in symbol for a in favored_assets):
            risk_score -= 0.1

        if risk_score > 0.5:
            decision = "BLOCK"
        elif risk_score > 0.3:
            decision = "REDUCE"
        else:
            decision = "APPROVE"

        var_estimate = volatility_24h * 1.645

        dharma_messages = {
            "APPROVE": "Agni zegt: vuur zuivert, deze trade is acceptabel",
            "REDUCE": "Agni waarschuwt: verminder risico",
            "BLOCK": "Agni beschermt: te veel risico",
        }

        return FireDecision(
            decision=decision,
            confidence=1.0 - risk_score,
            max_allowed_qty=max_allowed if decision != "BLOCK" else None,
            risk_score=risk_score,
            blocking_reasons=blocking_reasons,
            var_estimate_pct=var_estimate,
            fire_dharma=dharma_messages.get(decision, "Agni observeert"),
            prana_consumed=PRANA_COSTS["risk"],
        )

    # ============ FIX 2: WATER AGENT - DYNAMIC CONFIDENCE ============

    def water_agent_analyze(
        self, symbol: str, market_data: dict[str, Any], navagraha: NavagrahaState
    ) -> WaterRegime:
        """Water Agent with DYNAMIC confidence calculation (was hardcoded 0.51)"""

        prices = list(self.price_history.get(symbol, []))

        if len(prices) < 20:
            return WaterRegime(
                regime="neutral",
                asset_class_outlook={},
                favored_symbols=[],
                avoid_symbols=[],
                macro_narrative="Onvoldoende data",
                confidence=0.35,  # Low but not fixed
                water_dharma="Water is stil - geen duidelijke stroming",
            )

        # Calculate dynamic confidence based on market conditions
        # 1. Trend strength (0-0.4)
        price_change_7d = (
            (prices[-1] - prices[-min(7, len(prices))]) / prices[-min(7, len(prices))] * 100
        )
        trend_score = min(abs(price_change_7d) / 10, 0.4)

        # 2. Volatility penalty (0-0.2)
        volatility = self._calculate_volatility(prices)
        vol_penalty = min(volatility / 10, 0.2)

        # 3. Volume confirmation (if available)
        volumes = list(self.volume_history.get(symbol, []))
        volume_ratio = 1.0
        if len(volumes) >= 10:
            avg_volume = sum(volumes[-10:]) / 10
            recent_volume = volumes[-1] if volumes[-1] > 0 else 1
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        volume_score = min(max((volume_ratio - 0.5) * 0.2, 0), 0.15)

        # 4. Regime clarity bonus
        price_change_30d = (
            (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))] * 100
        )
        if abs(price_change_30d) > 20:
            regime_clarity = 0.1  # Clear trend
        else:
            regime_clarity = 0.0

        # Calculate final dynamic confidence
        base_confidence = 0.35
        confidence = base_confidence + trend_score - vol_penalty + volume_score + regime_clarity
        confidence = max(0.25, min(0.85, confidence))  # Clamp 0.25-0.85

        # Determine regime
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

        # Asset class outlook based on regime and planet
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
        if regime == "contraction":
            asset = self._get_asset_info(symbol)
            if asset and asset.asset_class.value == "crypto":
                avoid.append(symbol)

        narratives = {
            "expansion": f"Markt in expansie onder {dominant} - trend score {trend_score:.2f}",
            "contraction": "Contractie fase - defensief",
            "recovery": f"Herstel bezig - regime clarity {regime_clarity:.2f}",
            "neutral": f"Neutrale markt - vol penalty {vol_penalty:.2f}",
        }

        return WaterRegime(
            regime=regime,
            asset_class_outlook=asset_class_outlook,
            favored_symbols=favored,
            avoid_symbols=avoid,
            macro_narrative=narratives.get(regime, "Neutraal"),
            confidence=round(confidence, 3),  # FIX 2: Dynamic!
            water_dharma=f"Water stroomt naar {regime} (conf: {confidence:.2f})",
        )

    # ============ AIR AGENT ============

    def air_agent_generate_signals(
        self, symbol: str, current_price: float, navagraha: NavagrahaState
    ) -> AirSignal:
        prices = list(self.price_history.get(symbol, []))

        if len(prices) < 20:
            return AirSignal(
                symbol=symbol,
                action="HOLD",
                confidence=0.3,
                entry_price=current_price,
                stop_loss=current_price * 0.95,
                take_profit=current_price * 1.10,
                technical_summary="Onvoldoende data",
                indicators={},
                air_dharma="Vayu wacht",
            )

        rsi = self._calculate_rsi(prices)
        ema_20 = self._calculate_ema(prices, 20)
        ema_50 = self._calculate_ema(prices, 50) if len(prices) >= 50 else ema_20

        volatility = self._calculate_volatility(prices)
        atr = current_price * (volatility / 100) * 0.5

        action = "HOLD"
        confidence = 0.5

        trend_bullish = current_price > ema_20 > ema_50
        trend_bearish = current_price < ema_20 < ema_50
        rsi_oversold = rsi < 30
        rsi_overbought = rsi > 70

        if trend_bullish and rsi_oversold:
            action = "BUY"
            confidence = 0.8
        elif trend_bullish and 30 <= rsi <= 50:
            action = "BUY"
            confidence = 0.6
        elif trend_bearish and rsi_overbought:
            action = "SELL"
            confidence = 0.8
        elif trend_bearish and 50 <= rsi <= 70:
            action = "SELL"
            confidence = 0.6
        elif rsi < 20:
            action = "BUY"
            confidence = 0.7
        elif rsi > 80:
            action = "SELL"
            confidence = 0.7

        dominant = navagraha.dominant_planet
        favored = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored or any(f in symbol for f in favored):
            confidence = min(0.95, confidence + 0.1)

        if action == "BUY":
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 3)
        elif action == "SELL":
            stop_loss = current_price + (atr * 2)
            take_profit = current_price - (atr * 3)
        else:
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05

        indicators = {
            "rsi": round(rsi, 2),
            "ema_20": round(ema_20, 2),
            "ema_50": round(ema_50, 2),
            "volatility_pct": round(volatility, 2),
            "trend": "bullish" if trend_bullish else "bearish" if trend_bearish else "neutral",
        }

        return AirSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            technical_summary=f"RSI {rsi:.1f}, trend {indicators['trend']}",
            indicators=indicators,
            air_dharma=f"Vayu: {action} (conf: {confidence:.2f})",
        )

    # ============ EARTH AGENT ============

    def earth_agent_valuate(
        self, symbol: str, current_price: float, market_regime: str
    ) -> EarthValuation:
        prices = list(self.price_history.get(symbol, []))

        if len(prices) < 30:
            return EarthValuation(
                symbol=symbol,
                fair_value=current_price,
                current_price=current_price,
                valuation_gap_pct=0,
                verdict="FAIR",
                confidence=0.4,
                methodology="Onvoldoende data",
                earth_dharma="Prithvi wacht",
            )

        asset = self._get_asset_info(symbol)
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

        confidence = min(0.9, 0.5 + (len(prices) / 100))

        dharma = {
            "UNDERVALUED": "Prithvi: waarde gevonden",
            "OVERVALUED": "Prithvi: overprijsd",
            "FAIR": "Prithvi: in balans",
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

    # ============ FIX 3: ETHER AGENT - WEIGHTED HARMONY ============

    def ether_agent_synthesize(
        self,
        fire: FireDecision,
        water: WaterRegime,
        air: AirSignal,
        earth: EarthValuation,
        navagraha: NavagrahaState,
        portfolio_value: float,
    ) -> EtherSynthesis:
        """
        FIX 3: Weighted harmony calculation instead of consensus requirement.
        This ensures trades actually happen!
        """

        # WEIGHTED AVERAGE of agent confidences (not requiring consensus)
        # FIX: Adjusted weights to favor Fire (risk) and Earth (value)
        weights = {
            "fire": 0.30,  # Risk guardian: heaviest weight
            "earth": 0.25,  # Valuation: stable
            "water": 0.20,  # Macro: medium
            "air": 0.15,  # Signals: lighter
            "ether": 0.10,  # Meta: coordination
        }

        confidences = {
            "fire": fire.confidence,
            "water": water.confidence,
            "earth": earth.confidence,
            "air": air.confidence,
        }

        # Calculate weighted harmony
        harmony_score = sum(confidences[agent] * weights[agent] for agent in confidences)

        # FIX 1: Use planet-specific threshold
        execute_threshold = HARMONY_THRESHOLDS.get(
            navagraha.dominant_planet, HARMONY_THRESHOLDS["DEFAULT"]
        )

        # Boost for consensus (but not required)
        unique_actions = len(
            set(
                [
                    "BLOCK" if fire.decision == "BLOCK" else "PASS",
                    water.regime,
                    air.action,
                    earth.verdict,
                ]
            )
        )
        consensus_achieved = unique_actions <= 2

        if consensus_achieved:
            harmony_score = min(1.0, harmony_score * 1.15)  # Reduced from 1.3

        # Rule 1: Harmony too low = block
        if harmony_score < execute_threshold:
            return EtherSynthesis(
                final_decision="BLOCK",
                harmony_score=harmony_score,
                approved_symbol=None,
                approved_action=None,
                approved_qty=0,
                approved_price=0,
                stop_loss=0,
                take_profit=0,
                execution_urgency="none",
                consensus_achieved=False,
                blocking_agent="ether",
                cosmic_narrative=f"Harmony {harmony_score:.2f} < threshold {execute_threshold:.2f} ({navagraha.dominant_planet})",
                ether_dharma="Akasha wacht op betere alignering",
            )

        # Rule 2: Fire blocks = always block
        if fire.decision == "BLOCK":
            return EtherSynthesis(
                final_decision="BLOCK",
                harmony_score=harmony_score,
                approved_symbol=air.symbol,
                approved_action=None,
                approved_qty=0,
                approved_price=0,
                stop_loss=0,
                take_profit=0,
                execution_urgency="none",
                consensus_achieved=consensus_achieved,
                blocking_agent="fire",
                cosmic_narrative="Agni heeft gesproken",
                ether_dharma="Vuur beschermt",
            )

        # Calculate position size with adjustments
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
        if asset := self._get_asset_info(air.symbol):
            base_qty = asset.min_qty * 10

        approved_qty = base_qty * position_factor * harmony_score

        if air.action in ["BUY", "SELL"]:
            final_decision = "EXECUTE"
            execution_urgency = "immediate" if harmony_score > 0.6 else "next_candle"
        else:
            final_decision = "BLOCK"
            execution_urgency = "none"

        if asset := self._get_asset_info(air.symbol):
            pass

        return EtherSynthesis(
            final_decision=final_decision,
            harmony_score=harmony_score,
            approved_symbol=air.symbol,
            approved_action=air.action if final_decision == "EXECUTE" else "HOLD",
            approved_qty=approved_qty,
            approved_price=air.entry_price,
            stop_loss=air.stop_loss,
            take_profit=air.take_profit,
            execution_urgency=execution_urgency,
            consensus_achieved=consensus_achieved,
            blocking_agent=None,
            cosmic_narrative=f"{navagraha.dominant_planet} | H:{harmony_score:.2f} | {water.regime} | {air.action} | {earth.verdict}",
            ether_dharma="Akasha harmoniseert",
        )

    # ============ MAIN INTERFACE ============

    def process_trading_cycle(
        self,
        symbol: str,
        current_price: float,
        portfolio_value: float,
        current_positions: dict[str, Any],
        prana_level: float = 85.0,
    ) -> EtherSynthesis:
        """Process one complete trading cycle with all fixes applied"""

        self.update_price_data(symbol, current_price)
        navagraha = self._get_current_navagraha_state()

        # FIX 1: Adjust base harmony by planet threshold
        HARMONY_THRESHOLDS.get(navagraha.dominant_planet, 0.48)
        base_harmony = 0.5 + (prana_level / 100) * 0.3

        # 1. Water Agent: Analyze regime (FIX 2: Dynamic confidence)
        market_data = {"prices": {s: list(self.price_history.get(s, [])) for s in [symbol]}}
        water = self.water_agent_analyze(symbol, market_data, navagraha)

        # 2. Air Agent: Generate signal
        air = self.air_agent_generate_signals(symbol, current_price, navagraha)

        # 3. Earth Agent: Valuation
        earth = self.earth_agent_valuate(symbol, current_price, water.regime)

        # 4. Fire Agent: Risk assessment
        proposed_qty = 0.01
        volatility = self._calculate_volatility(list(self.price_history.get(symbol, [])))

        fire = self.fire_agent_assess(
            symbol=symbol,
            proposed_action=air.action,
            proposed_qty=proposed_qty,
            price=current_price,
            portfolio_value=portfolio_value,
            navagraha=navagraha,
            harmony_score=base_harmony,
            prana_level=prana_level,
            market_regime=water.regime,
            volatility_24h=volatility,
        )

        # 5. Ether Agent: Synthesize (FIX 3: Weighted harmony)
        ether = self.ether_agent_synthesize(
            fire=fire,
            water=water,
            air=air,
            earth=earth,
            navagraha=navagraha,
            portfolio_value=portfolio_value,
        )

        # Track
        self.agent_confidence_history["fire"].append(fire.confidence)
        self.agent_confidence_history["water"].append(water.confidence)
        self.agent_confidence_history["air"].append(air.confidence)
        self.agent_confidence_history["earth"].append(earth.confidence)
        self.agent_confidence_history["ether"].append(ether.harmony_score)

        return ether

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
        stats = {}
        for agent, confidences in self.agent_confidence_history.items():
            if confidences:
                stats[agent] = {
                    "avg_confidence": sum(confidences) / len(confidences),
                    "min_confidence": min(confidences),
                    "max_confidence": max(confidences),
                    "samples": len(confidences),
                }
        return stats
