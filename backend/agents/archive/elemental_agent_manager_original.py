"""
Elemental Agent Manager - Vedic Trading Intelligence
Integrates Fire, Water, Air, Earth, and Ether agents into trading decisions
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

logger = logging.getLogger("ElementalAgents")


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
    """Fire Agent (Risk Guardian) output"""

    decision: str  # APPROVE, BLOCK, REDUCE
    confidence: float
    max_allowed_qty: float | None
    risk_score: float
    blocking_reasons: list[str]
    var_estimate_pct: float
    fire_dharma: str
    prana_consumed: float


@dataclass
class WaterRegime:
    """Water Agent (Macro Research) output"""

    regime: str  # expansion, contraction, neutral, recovery
    asset_class_outlook: dict[str, str]
    favored_symbols: list[str]
    avoid_symbols: list[str]
    macro_narrative: str
    confidence: float
    water_dharma: str


@dataclass
class AirSignal:
    """Air Agent (Technical Signals) output"""

    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    technical_summary: str
    indicators: dict[str, Any]
    air_dharma: str


@dataclass
class EarthValuation:
    """Earth Agent (Valuation) output"""

    symbol: str
    fair_value: float
    current_price: float
    valuation_gap_pct: float
    verdict: str  # UNDERVALUED, FAIR, OVERVALUED
    confidence: float
    methodology: str
    earth_dharma: str


@dataclass
class EtherSynthesis:
    """Ether Agent (Orchestrator) output"""

    final_decision: str  # EXECUTE, BLOCK, PARTIAL
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


class ElementalAgentManager:
    """
    Orchestrates all 5 elemental agents for trading decisions.
    Implements Vedic trading logic without requiring LLM calls.
    """

    def __init__(self):
        # Technical indicator buffers
        self.price_history: dict[str, deque] = {}
        self.volume_history: dict[str, deque] = {}
        self.history_length = 50

        # Asset universe mapping
        self.asset_map = {a.symbol: a for a in FULL_ASSET_UNIVERSE}

        # Performance tracking
        self.agent_confidence_history: dict[str, list[float]] = {
            "fire": [],
            "water": [],
            "air": [],
            "earth": [],
            "ether": [],
        }

    def _get_asset_info(self, symbol: str):
        """Get asset info from universe"""
        # Try exact match first
        if symbol in self.asset_map:
            return self.asset_map[symbol]

        # Try with /EUR suffix for crypto
        if f"{symbol}/EUR" in self.asset_map:
            return self.asset_map[f"{symbol}/EUR"]

        # Default fallback
        return None

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float:
        """Calculate RSI technical indicator"""
        if len(prices) < period + 1:
            return 50.0

        gains = []
        losses = []

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
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_ema(self, prices: list[float], period: int = 20) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _calculate_atr(
        self,
        highs: list[float],
        lows: list[float],
        closes: list[float],
        period: int = 14,
    ) -> float:
        """Calculate Average True Range"""
        if len(closes) < period + 1:
            return closes[-1] * 0.02 if closes else 0

        true_ranges = []
        for i in range(1, len(closes)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i - 1])
            tr3 = abs(lows[i] - closes[i - 1])
            true_ranges.append(max(tr1, tr2, tr3))

        return sum(true_ranges[-period:]) / period if len(true_ranges) >= period else 0

    def _calculate_volatility(self, prices: list[float]) -> float:
        """Calculate price volatility as percentage"""
        if len(prices) < 2:
            return 0

        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        if not returns:
            return 0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance**0.5

        return std_dev * 100  # As percentage

    def update_price_data(self, symbol: str, price: float, volume: float = 0):
        """Update price history for technical analysis"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.history_length)
            self.volume_history[symbol] = deque(maxlen=self.history_length)

        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)

    # ============ FIRE AGENT (Risk Guardian) ============

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
        """
        Fire Agent: Risk assessment and trade validation
        """
        blocking_reasons = []
        risk_score = 0.0

        # Rule 1: Rahu Kala check
        if navagraha.rahu_kala_active:
            return FireDecision(
                decision="BLOCK",
                confidence=1.0,
                max_allowed_qty=None,
                risk_score=1.0,
                blocking_reasons=["Rahu Kala actief - geen trading"],
                var_estimate_pct=0,
                fire_dharma="Agni waarschuwt: Rahu's invloed is te sterk",
                prana_consumed=0,
            )

        # Rule 2: Prana check
        if prana_level < 10:
            return FireDecision(
                decision="BLOCK",
                confidence=1.0,
                max_allowed_qty=None,
                risk_score=1.0,
                blocking_reasons=["Prana uitgeput - veiligheid eerste"],
                var_estimate_pct=0,
                fire_dharma="Systeemprana te laag voor risico",
                prana_consumed=0,
            )

        # Rule 3: Harmony check
        if harmony_score < 0.25:
            return FireDecision(
                decision="BLOCK",
                confidence=0.9,
                max_allowed_qty=None,
                risk_score=0.9,
                blocking_reasons=["Systemische disharmonie"],
                var_estimate_pct=0,
                fire_dharma="Agni blokkeert door disharmonie",
                prana_consumed=2.0,
            )

        # Get asset info
        asset = self._get_asset_info(symbol)
        asset_class = asset.asset_class.value if asset else "crypto"

        # Asset-specific risk limits
        asset_limits = {
            "crypto": 0.02,  # 2% for crypto
            "forex": 0.01,  # 1% for forex
            "commodities": 0.015,  # 1.5% for commodities
            "indices": 0.02,  # 2% for indices
            "equities": 0.015,  # 1.5% for equities
        }

        max_risk = asset_limits.get(asset_class, 0.01)
        trade_value = proposed_qty * price
        trade_risk_pct = trade_value / portfolio_value if portfolio_value > 0 else 0

        # Rule 4: Position size limit
        if trade_risk_pct > max_risk:
            risk_score += 0.3
            max_allowed = (portfolio_value * max_risk) / price
            blocking_reasons.append(f"Positie {trade_risk_pct:.2%} > limiet {max_risk:.2%}")
        else:
            max_allowed = proposed_qty

        # Rule 5: Volatility check
        if asset_class == "crypto" and volatility_24h > 8:
            risk_score += 0.2
            blocking_reasons.append("Crypto volatiliteit > 8%")
        elif asset_class == "forex" and volatility_24h > 2:
            risk_score += 0.2
            blocking_reasons.append("Forex volatiliteit > 2%")

        # Rule 6: Contraction regime check
        if market_regime == "contraction" and asset_class == "crypto":
            max_allowed *= 0.5
            risk_score += 0.15
            blocking_reasons.append("Contraction regime - reduceer crypto")

        # Navagraha affinity bonus
        dominant = navagraha.dominant_planet
        favored_assets = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored_assets or any(a in symbol for a in favored_assets):
            risk_score -= 0.1  # Lower risk for favored assets

        # Final decision
        if risk_score > 0.5:
            decision = "BLOCK"
        elif risk_score > 0.3:
            decision = "REDUCE"
        else:
            decision = "APPROVE"

        # VaR estimate (simplified)
        var_estimate = volatility_24h * 1.645  # 95% confidence

        # Dharma message
        if decision == "APPROVE":
            dharma = "Agni zegt: vuur zuivert, deze trade is acceptabel"
        elif decision == "REDUCE":
            dharma = "Agni waarschuwt: verminder risico, maar niet blokkeren"
        else:
            dharma = "Agni beschermt: te veel risico, trade geblokkeerd"

        return FireDecision(
            decision=decision,
            confidence=1.0 - risk_score,
            max_allowed_qty=max_allowed if decision != "BLOCK" else None,
            risk_score=risk_score,
            blocking_reasons=blocking_reasons,
            var_estimate_pct=var_estimate,
            fire_dharma=dharma,
            prana_consumed=5.0 if decision == "APPROVE" else 2.0,
        )

    # ============ WATER AGENT (Macro Research) ============

    def water_agent_analyze(
        self, market_data: dict[str, Any], navagraha: NavagrahaState
    ) -> WaterRegime:
        """
        Water Agent: Determine market regime and macro outlook
        """
        # Calculate market breadth
        prices = market_data.get("prices", {})

        if not prices:
            return WaterRegime(
                regime="neutral",
                asset_class_outlook={},
                favored_symbols=[],
                avoid_symbols=[],
                macro_narrative="Onvoldoende data voor regime bepaling",
                confidence=0.5,
                water_dharma="Water is stil - geen duidelijke stroming",
            )

        # Count advancing vs declining
        advancing = 0
        declining = 0

        for symbol, price_list in prices.items():
            if len(price_list) >= 20:
                change = (price_list[-1] - price_list[-20]) / price_list[-20]
                if change > 0.02:
                    advancing += 1
                elif change < -0.02:
                    declining += 1

        total = advancing + declining
        if total == 0:
            regime = "neutral"
        elif advancing / total > 0.6:
            regime = "expansion"
        elif declining / total > 0.6:
            regime = "contraction"
        elif advancing > declining:
            regime = "recovery"
        else:
            regime = "neutral"

        # Asset class outlook based on regime and dominant planet
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

        # Favored/avoid symbols based on planet affinity
        favored = PLANET_ASSET_AFFINITY.get(dominant, [])

        # Avoid symbols based on regime
        avoid = []
        if regime == "contraction":
            avoid = [
                s
                for s in prices.keys()
                if self._get_asset_info(s) and self._get_asset_info(s).asset_class.value == "crypto"
            ]

        # Confidence based on data quality
        confidence = min(0.9, 0.5 + (len(prices) / 100))

        # Narrative
        narratives = {
            "expansion": f"Markt in expansie onder {dominant}'s invloed - groei assets favoriet",
            "contraction": "Contractie fase - defensieve positie aangeraden",
            "recovery": f"Herstel bezig - selectieve kansen in {dominant} assets",
            "neutral": "Neutrale markt - wachten op duidelijke richting",
        }

        return WaterRegime(
            regime=regime,
            asset_class_outlook=asset_class_outlook,
            favored_symbols=favored,
            avoid_symbols=avoid,
            macro_narrative=narratives.get(regime, "Neutraal"),
            confidence=confidence,
            water_dharma=f"Water stroomt naar {regime} onder {dominant}'s getijden",
        )

    # ============ AIR AGENT (Technical Signals) ============

    def air_agent_generate_signals(
        self, symbol: str, current_price: float, navagraha: NavagrahaState
    ) -> AirSignal:
        """
        Air Agent: Generate technical trading signals
        """
        # Get price history
        prices = list(self.price_history.get(symbol, []))

        if len(prices) < 20:
            return AirSignal(
                symbol=symbol,
                action="HOLD",
                confidence=0.3,
                entry_price=current_price,
                stop_loss=current_price * 0.95,
                take_profit=current_price * 1.10,
                technical_summary="Onvoldoende data voor analyse",
                indicators={},
                air_dharma="Vayu wacht - geen wind in de zeilen",
            )

        # Calculate indicators
        rsi = self._calculate_rsi(prices)
        ema_20 = self._calculate_ema(prices, 20)
        ema_50 = self._calculate_ema(prices, 50) if len(prices) >= 50 else ema_20

        # Volatility for ATR-based stops
        volatility = self._calculate_volatility(prices)
        atr = current_price * (volatility / 100) * 0.5

        # Generate signal
        action = "HOLD"
        confidence = 0.5

        # Trend determination
        trend_bullish = current_price > ema_20 > ema_50
        trend_bearish = current_price < ema_20 < ema_50

        # RSI signals
        rsi_oversold = rsi < 30
        rsi_overbought = rsi > 70

        # Combined logic
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

        # Check planet affinity
        dominant = navagraha.dominant_planet
        favored = PLANET_ASSET_AFFINITY.get(dominant, [])
        if symbol in favored or any(f in symbol for f in favored):
            confidence = min(0.95, confidence + 0.1)

        # Calculate stop loss and take profit
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

        dharma_messages = {
            "BUY": "Vayu waait in kooprichting - stijgende wind",
            "SELL": "Vayu draait - verkoopwinden sterk",
            "HOLD": "Vayu is stil - geen duidelijke richting",
        }

        return AirSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            technical_summary=f"RSI {rsi:.1f}, trend {'bullish' if trend_bullish else 'bearish' if trend_bearish else 'neutral'}",
            indicators=indicators,
            air_dharma=dharma_messages.get(action, "Vayu observeert"),
        )

    # ============ EARTH AGENT (Valuation) ============

    def earth_agent_valuate(
        self, symbol: str, current_price: float, market_regime: str
    ) -> EarthValuation:
        """
        Earth Agent: Calculate fair value and valuation gaps
        """
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
                earth_dharma="Prithvi wacht - grond is nog onduidelijk",
            )

        # Different methodologies per asset class
        asset = self._get_asset_info(symbol)
        asset_class = asset.asset_class.value if asset else "crypto"

        if asset_class == "crypto":
            # Crypto: Mean reversion with trend adjustment
            sma_30 = sum(prices[-30:]) / 30
            trend = (prices[-1] - prices[-30]) / prices[-30]
            fair_value = sma_30 * (1 + trend * 0.3)  # Partial trend following
            methodology = "SMA30 met trend-adjustment"

        elif asset_class == "forex":
            # Forex: Longer-term mean
            sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else sum(prices) / len(prices)
            fair_value = sma_50
            methodology = "SMA50 mean reversion"

        elif asset_class == "commodities":
            # Commodities: Cost-of-carry approximation
            sma_20 = sum(prices[-20:]) / 20
            sma_40 = sum(prices[-40:]) / 40 if len(prices) >= 40 else sma_20
            fair_value = (sma_20 + sma_40) / 2
            methodology = "Dual SMA (20/40)"

        else:
            # Equities/Indices: PE approximation via price momentum
            sma_30 = sum(prices[-30:]) / 30
            momentum = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            fair_value = sma_30 * (1 + momentum * 0.5)
            methodology = "Momentum-adjusted SMA"

        # Calculate gap
        valuation_gap = (current_price - fair_value) / fair_value * 100

        # Verdict
        if valuation_gap < -10:
            verdict = "UNDERVALUED"
        elif valuation_gap > 10:
            verdict = "OVERVALUED"
        else:
            verdict = "FAIR"

        # Confidence
        confidence = min(0.9, 0.5 + (len(prices) / 100))

        # Dharma
        if verdict == "UNDERVALUED":
            dharma = "Prithvi toont waarde - grond is vruchtbaar voor koop"
        elif verdict == "OVERVALUED":
            dharma = "Prithvi waarschuwt - grond is overprijsd"
        else:
            dharma = "Prithvi is in balans - eerlijke prijs"

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

    # ============ ETHER AGENT (Orchestrator) ============

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
        Ether Agent: Synthesize all agent outputs into final decision
        """
        # Calculate harmony score (weighted average of agent confidences)
        guna_weights = {
            "fire": navagraha.guna_distribution.get("rajas", 0.3) * 1.5,  # Fire = Rajas
            "water": navagraha.guna_distribution.get("tamas", 0.15),  # Water = Tamas
            "air": navagraha.guna_distribution.get("rajas", 0.3),  # Air = Rajas
            "earth": navagraha.guna_distribution.get("tamas", 0.15) * 1.5,  # Earth = Tamas
            "ether": navagraha.guna_distribution.get("sattva", 0.55),  # Ether = Sattva
        }

        # Normalize weights
        total_weight = sum(guna_weights.values())
        guna_weights = {k: v / total_weight for k, v in guna_weights.items()}

        # Agent confidences
        confidences = {
            "fire": fire.confidence,
            "water": water.confidence,
            "air": air.confidence,
            "earth": earth.confidence,
        }

        # Calculate harmony score
        harmony_score = sum(confidences[agent] * guna_weights[agent] for agent in confidences)

        # Boost harmony if consensus
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
            harmony_score = min(1.0, harmony_score * 1.3)

        # Rule 1: Harmony too low = block
        if harmony_score < 0.3:
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
                cosmic_narrative=f"Kosmische disharmonie ({harmony_score:.2f}) - geen trading",
                ether_dharma="Akasha is troebel - wacht op helderheid",
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
                cosmic_narrative="Agni heeft gesproken - veiligheid boven winst",
                ether_dharma="Vuur beschermt het universum",
            )

        # Rule 3: Check Water regime
        if water.regime == "contraction" and air.action == "BUY":
            # Reduce position in contraction
            position_factor = 0.6
        else:
            position_factor = 1.0

        # Rule 4: Check Earth valuation
        if earth.verdict == "OVERVALUED" and air.action == "BUY":
            # Reduce if buying overvalued
            position_factor *= 0.6
        elif earth.verdict == "UNDERVALUED" and air.action == "BUY":
            # Increase if buying undervalued
            position_factor = min(1.0, position_factor * 1.2)

        # Rule 5: Fire reduce
        if fire.decision == "REDUCE":
            position_factor *= 0.7

        # Calculate final position size
        base_qty = 0.01  # Base quantity
        if asset := self._get_asset_info(air.symbol):
            base_qty = asset.min_qty * 10  # Scale by minimum

        approved_qty = base_qty * position_factor * harmony_score

        # Final decision
        if air.action in ["BUY", "SELL"]:
            final_decision = "EXECUTE"
            execution_urgency = "immediate" if harmony_score > 0.7 else "next_candle"
        else:
            final_decision = "BLOCK"
            execution_urgency = "none"

        # Asset class focus
        if asset := self._get_asset_info(air.symbol):
            pass

        # Cosmic narrative
        narrative = f"Onder {navagraha.dominant_planet}'s invloed: {water.regime} regime, "
        narrative += f"Air zegt {air.action}, Earth zegt {earth.verdict}. "
        narrative += f"Harmonie: {harmony_score:.2f}"

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
            cosmic_narrative=narrative,
            ether_dharma="Akasha harmoniseert alle elementen",
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
        """
        Process one complete trading cycle for a symbol.
        Returns the Ether Agent's final decision.
        """
        # Update price history
        self.update_price_data(symbol, current_price)

        # Get current Navagraha state (simplified - in production use real calculation)
        navagraha = self._get_current_navagraha_state()

        # Calculate current harmony base
        base_harmony = 0.6 + (prana_level / 100) * 0.3

        # 1. Water Agent: Analyze regime
        market_data = {"prices": {s: list(self.price_history.get(s, [])) for s in [symbol]}}
        water = self.water_agent_analyze(market_data, navagraha)

        # 2. Air Agent: Generate signal
        air = self.air_agent_generate_signals(symbol, current_price, navagraha)

        # 3. Earth Agent: Valuation
        earth = self.earth_agent_valuate(symbol, current_price, water.regime)

        # 4. Fire Agent: Risk assessment
        proposed_qty = 0.01  # Default
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

        # 5. Ether Agent: Synthesize
        ether = self.ether_agent_synthesize(
            fire=fire,
            water=water,
            air=air,
            earth=earth,
            navagraha=navagraha,
            portfolio_value=portfolio_value,
        )

        # Track agent confidences
        self.agent_confidence_history["fire"].append(fire.confidence)
        self.agent_confidence_history["water"].append(water.confidence)
        self.agent_confidence_history["air"].append(air.confidence)
        self.agent_confidence_history["earth"].append(earth.confidence)
        self.agent_confidence_history["ether"].append(ether.harmony_score)

        return ether

    def _get_current_navagraha_state(self) -> NavagrahaState:
        """
        Get current Navagraha state (simplified for backtest).
        In production, this would use real planetary calculations.
        """
        # Cycle through planets based on day of month
        day = datetime.now().day
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        dominant = planets[day % 7]

        # Random Rahu Kala (approximately 1/8 of time)
        rahu_active = (day % 8) == 0

        return NavagrahaState(
            dominant_planet=dominant,
            trading_gate_open=not rahu_active,
            rahu_kala_active=rahu_active,
            consciousness_level="Pure Awareness",
            guna_distribution={"sattva": 0.55, "rajas": 0.30, "tamas": 0.15},
        )

    def get_agent_stats(self) -> dict[str, Any]:
        """Get statistics about agent performance"""
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
