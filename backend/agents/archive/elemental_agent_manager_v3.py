"""
Elemental Agent Manager V3 - Vedic Trading Intelligence (FINAL OPTIMIZED)
Addresses remaining issues from V2 analysis:
1. Planet parsing bug (| instead of planet name) - FIXED
2. Harmony threshold too high (84% still blocked) - LOWERED to 0.55
3. TSLA volatility filter (ATR > 4% skip) - ADDED
4. Consensus bonus not triggering - FIXED
5. Execute % only 15.8% - INCREASED by better thresholds
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

logger = logging.getLogger("ElementalAgentsV3")

# ============ V3: LOWER HARMONY THRESHOLDS ============
# Analysis showed 84% was still blocked - lower thresholds
HARMONY_THRESHOLDS = {
    "SATURN": 0.55,  # V3: Was 0.40, now 0.55 but base harmony higher
    "MARS": 0.58,
    "JUPITER": 0.52,
    "SUN": 0.55,
    "MOON": 0.53,
    "MERCURY": 0.56,
    "VENUS": 0.52,
    "RAHU": 0.65,
    "KETU": 0.60,
    "DEFAULT": 0.55,  # V3: Lower default for more trades
}

# Global execute threshold - if harmony above this, trade executes
GLOBAL_EXECUTE_THRESHOLD = 0.55  # V3: Fixed threshold regardless of planet

PRANA_COSTS = {
    "orchestrator": 5,
    "research": 3,
    "risk": 2,
    "valuation": 2,
    "macro": 2,
}

PRANA_REGEN_PER_DAY = 50.0


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


class ElementalAgentManagerV3:
    """
    V3: Final optimized version with:
    - Lower execute thresholds for more trading activity
    - TSLA volatility filter
    - Fixed planet name parsing
    - Working consensus bonus
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

        # Track consensus achievements
        self.consensus_count = 0
        self.total_cycles = 0

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

    def _calculate_atr(self, prices: list[float]) -> float:
        """Calculate Average True Range for volatility filtering"""
        if len(prices) < 14:
            return 0
        tr_list = []
        for i in range(1, len(prices)):
            tr = abs(prices[i] - prices[i - 1])
            tr_list.append(tr)
        return sum(tr_list[-14:]) / 14 if tr_list else 0

    def update_price_data(self, symbol: str, price: float, volume: float = 0):
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.history_length)
            self.volume_history[symbol] = deque(maxlen=self.history_length)
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)

    # ============ FIRE AGENT V3 ============

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

        # V3: TSLA Volatility Filter - Skip TSLA if ATR > 4%
        if symbol == "TSLA":
            prices = list(self.price_history.get(symbol, []))
            if len(prices) >= 14:
                atr = self._calculate_atr(prices)
                atr_pct = (atr / price) * 100 if price > 0 else 0
                if atr_pct > 4.0:
                    return FireDecision(
                        decision="BLOCK",
                        confidence=1.0,
                        max_allowed_qty=None,
                        risk_score=1.0,
                        blocking_reasons=["TSLA ATR > 4% - too volatile"],
                        var_estimate_pct=0,
                        fire_dharma="Agni: TSLA volatility too high",
                        prana_consumed=PRANA_COSTS["risk"],
                    )

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

        # V3: Use global execute threshold (lower for more activity)
        if harmony_score < GLOBAL_EXECUTE_THRESHOLD * 0.7:
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

        return FireDecision(
            decision=decision,
            confidence=1.0 - risk_score,
            max_allowed_qty=max_allowed if decision != "BLOCK" else None,
            risk_score=risk_score,
            blocking_reasons=blocking_reasons,
            var_estimate_pct=var_estimate,
            fire_dharma=f"Agni: {decision.lower()} (risk: {risk_score:.2f})",
            prana_consumed=PRANA_COSTS["risk"],
        )

    # ============ WATER AGENT V3 ============

    def water_agent_analyze(
        self, symbol: str, market_data: dict[str, Any], navagraha: NavagrahaState
    ) -> WaterRegime:
        prices = list(self.price_history.get(symbol, []))

        if len(prices) < 20:
            return WaterRegime(
                regime="neutral",
                asset_class_outlook={},
                favored_symbols=[],
                avoid_symbols=[],
                macro_narrative="Onvoldoende data",
                confidence=0.35,
                water_dharma="Water is stil",
            )

        price_change_7d = (
            (prices[-1] - prices[-min(7, len(prices))]) / prices[-min(7, len(prices))] * 100
        )
        trend_score = min(abs(price_change_7d) / 10, 0.4)

        volatility = self._calculate_volatility(prices)
        vol_penalty = min(volatility / 10, 0.2)

        volumes = list(self.volume_history.get(symbol, []))
        volume_ratio = 1.0
        if len(volumes) >= 10:
            avg_volume = sum(volumes[-10:]) / 10
            recent_volume = volumes[-1] if volumes[-1] > 0 else 1
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        volume_score = min(max((volume_ratio - 0.5) * 0.2, 0), 0.15)

        price_change_30d = (
            (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))] * 100
        )
        regime_clarity = 0.1 if abs(price_change_30d) > 20 else 0.0

        base_confidence = 0.35
        confidence = base_confidence + trend_score - vol_penalty + volume_score + regime_clarity
        confidence = max(0.25, min(0.85, confidence))

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

        return WaterRegime(
            regime=regime,
            asset_class_outlook=asset_class_outlook,
            favored_symbols=favored,
            avoid_symbols=avoid,
            macro_narrative=f"{dominant} regime: {regime}",
            confidence=round(confidence, 3),
            water_dharma=f"Water: {regime} (conf: {confidence:.2f})",
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
            "trend": ("bullish" if trend_bullish else "bearish" if trend_bearish else "neutral"),
        }

        return AirSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            technical_summary=f"RSI {rsi:.1f}, {indicators['trend']}",
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

    # ============ ETHER AGENT V3 ============

    def ether_agent_synthesize(
        self,
        fire: FireDecision,
        water: WaterRegime,
        air: AirSignal,
        earth: EarthValuation,
        navagraha: NavagrahaState,
        portfolio_value: float,
    ) -> EtherSynthesis:
        """V3: Fixed consensus logic and lower execute threshold"""

        self.total_cycles += 1

        # V3: Fixed weights
        weights = {
            "fire": 0.30,
            "earth": 0.25,
            "water": 0.20,
            "air": 0.15,
            "ether": 0.10,
        }

        confidences = {
            "fire": fire.confidence,
            "water": water.confidence,
            "earth": earth.confidence,
            "air": air.confidence,
        }

        harmony_score = sum(confidences[agent] * weights[agent] for agent in confidences)

        # V3: Use GLOBAL_EXECUTE_THRESHOLD (0.55) for more trades
        execute_threshold = GLOBAL_EXECUTE_THRESHOLD

        # V3: FIXED consensus logic - count agents above their typical levels
        agents_above_baseline = sum(
            1 for agent, conf in confidences.items() if conf > 0.55  # Above typical operating level
        )
        consensus_achieved = agents_above_baseline >= 3  # 3+ agents confident

        if consensus_achieved:
            harmony_score = min(1.0, harmony_score * 1.20)
            self.consensus_count += 1

        # V3: Lower threshold check
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
                consensus_achieved=consensus_achieved,
                blocking_agent="ether",
                cosmic_narrative=f"H:{harmony_score:.2f}<{execute_threshold}|{navagraha.dominant_planet}",
                ether_dharma="Akasha wacht",
            )

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
                cosmic_narrative="Agni blokkeert",
                ether_dharma="Vuur beschermt",
            )

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
            execution_urgency = "immediate" if harmony_score > 0.65 else "next_candle"
        else:
            final_decision = "BLOCK"
            execution_urgency = "none"

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
            cosmic_narrative=f"{navagraha.dominant_planet}|H:{harmony_score:.2f}|C:{consensus_achieved}",
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
        """Process one complete trading cycle"""

        self.update_price_data(symbol, current_price)
        navagraha = self._get_current_navagraha_state()

        # V3: Higher base harmony for more trading activity
        base_harmony = 0.55 + (prana_level / 100) * 0.25

        market_data = {"prices": {s: list(self.price_history.get(s, [])) for s in [symbol]}}
        water = self.water_agent_analyze(symbol, market_data, navagraha)
        air = self.air_agent_generate_signals(symbol, current_price, navagraha)
        earth = self.earth_agent_valuate(symbol, current_price, water.regime)

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

        ether = self.ether_agent_synthesize(
            fire=fire,
            water=water,
            air=air,
            earth=earth,
            navagraha=navagraha,
            portfolio_value=portfolio_value,
        )

        self.agent_confidence_history["fire"].append(fire.confidence)
        self.agent_confidence_history["water"].append(water.confidence)
        self.agent_confidence_history["air"].append(air.confidence)
        self.agent_confidence_history["earth"].append(earth.confidence)
        self.agent_confidence_history["ether"].append(ether.harmony_score)

        return ether

    def _get_current_navagraha_state(self) -> NavagrahaState:
        """V3: Fixed planet name parsing"""
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
        # V3: Add consensus stats
        stats["consensus_achieved_pct"] = (
            (self.consensus_count / self.total_cycles * 100) if self.total_cycles > 0 else 0
        )
        stats["total_cycles"] = self.total_cycles
        stats["consensus_count"] = self.consensus_count
        return stats
