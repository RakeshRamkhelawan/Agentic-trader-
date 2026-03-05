"""
Analyst Agent - Orient Phase van OODA Loop.

Analyseert marktdata en genereert technische en sentiment indicatoren.

Enhanced met echte technische indicatoren via TechnicalIndicators library
en interne PriceHistoryManager voor sliding window analyse.
"""

import logging
from collections import deque
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.indicators.technical import TechnicalIndicators
from backend.core.ml.regime_detector import IntelligentRegimeDetector
from backend.core.schemas.ooda_types import MarketRegime, Observation, Orientation
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)

DEFAULT_MAX_PRICE_HISTORY = 200


class PriceHistoryManager:
    """
    Manages sliding window price/volume history per symbol.

    Builds up history over multiple orient() calls to enable
    real technical indicator calculations.
    """

    def __init__(self, max_history: int = DEFAULT_MAX_PRICE_HISTORY):
        self.max_history = max_history
        self._prices: dict[str, deque[float]] = {}
        self._volumes: dict[str, deque[float]] = {}

    def add(self, symbol: str, price: float, volume: float) -> None:
        """Add a new price/volume data point for a symbol."""
        if symbol not in self._prices:
            self._prices[symbol] = deque(maxlen=self.max_history)
            self._volumes[symbol] = deque(maxlen=self.max_history)

        self._prices[symbol].append(price)
        self._volumes[symbol].append(volume)

    def get_prices(self, symbol: str) -> list[float]:
        """Get price history for a symbol."""
        if symbol not in self._prices:
            return []
        return list(self._prices[symbol])

    def get_volumes(self, symbol: str) -> list[float]:
        """Get volume history for a symbol."""
        if symbol not in self._volumes:
            return []
        return list(self._volumes[symbol])

    def get_count(self, symbol: str) -> int:
        """Get number of data points for a symbol."""
        if symbol not in self._prices:
            return 0
        return len(self._prices[symbol])

    def clear(self, symbol: str | None = None) -> None:
        """Clear history for a symbol or all symbols."""
        if symbol:
            self._prices.pop(symbol, None)
            self._volumes.pop(symbol, None)
        else:
            self._prices.clear()
            self._volumes.clear()


class AnalystAgent(BaseAgent):
    """
    Analyst Agent - Technical & Sentiment Analysis specialist.

    Rol in OODA: **ORIENT**
    - Berekent echte technische indicatoren (RSI, MACD, Bollinger, ADX)
    - Aggregeert sentiment scores
    - Detecteert market regime met multi-indicator logica
    - Voor output: Orientation met confidence score

    De agent bouwt intern een price history op via PriceHistoryManager.
    Na voldoende datapunten (>= 35) worden echte indicatoren berekend.
    Bij onvoldoende data worden fallback-waarden gebruikt die neutraal zijn.
    """

    # Minimum datapoints voor echte indicatoren
    MIN_DATA_FOR_RSI = 15  # period=14 + 1
    MIN_DATA_FOR_MACD = 35  # slow=26 + signal=9
    MIN_DATA_FOR_BB = 20  # period=20
    MIN_DATA_FOR_ADX = 29  # period=14 * 2 + 1

    def __init__(
        self,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        core_confidence_weight: float = 0.5,
        max_price_history: int = DEFAULT_MAX_PRICE_HISTORY,
    ):
        """
        Initialiseer Analyst.

        Args:
            llm_provider: LLM voor narrative generation
            event_bus: Event bus
            core_confidence_weight: Weight voor core_sentiment in total confidence
            max_price_history: Max datapunten per symbol in sliding window
        """
        super().__init__(
            agent_name="Analyst",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST,
        )
        self.core_confidence_weight = core_confidence_weight
        self.analyses_completed = 0
        self.price_history = PriceHistoryManager(max_history=max_price_history)
        self.regime_detector = IntelligentRegimeDetector()

    async def orient(
        self,
        observation: Observation,
        core_sentiment: float,
        rag_context: list[str] | None = None,
    ) -> Orientation:
        """
        Analyseer observation en genereer Orientation.

        Args:
            observation: Raw marktdata
            core_sentiment: Confidence van CognitiveBridge/SystemIdentity
            rag_context: Historical context uit VectorMemory

        Returns:
            Orientation met regime, indicators, confidence
        """
        self.heartbeat()

        try:
            # Update price history
            self.price_history.add(
                observation.symbol,
                observation.price,
                observation.volume,
            )

            # Calculate technical indicators
            indicators = self._calculate_indicators(observation)

            # Detect market regime
            regime = self._detect_regime(indicators, observation)

            # Calculate total confidence
            technical_confidence = self._calculate_technical_confidence(indicators)
            total_confidence = (
                self.core_confidence_weight * core_sentiment
                + (1 - self.core_confidence_weight) * technical_confidence
            )

            # Create Orientation
            orientation = Orientation(
                symbol=observation.symbol,
                regime=regime,
                indicators=indicators,
                core_sentiment=core_sentiment,
                rag_context=rag_context or [],
                confidence=total_confidence,
            )

            self.analyses_completed += 1
            self.record_activity(success=True)

            data_count = self.price_history.get_count(observation.symbol)
            logger.info(
                "Orientation completed: %s, " "regime=%s, confidence=%.3f, data_points=%d",
                observation.symbol,
                regime.value,
                total_confidence,
                data_count,
            )

            return orientation

        except Exception as e:
            logger.error("Orient failed for %s: %s", observation.symbol, e)
            self.record_activity(success=False)
            raise

    def _calculate_indicators(self, observation: Observation) -> dict[str, float]:
        """
        Bereken technische indicatoren uit price history.

        Gebruikt echte berekeningen via TechnicalIndicators wanneer
        voldoende datapunten beschikbaar zijn. Anders fallback naar
        neutrale waarden.

        Returns:
            Dict met indicator names en values
        """
        symbol = observation.symbol
        prices = self.price_history.get_prices(symbol)
        volumes = self.price_history.get_volumes(symbol)

        # Spread berekening (altijd beschikbaar vanuit orderbook)
        spread_pct = self._calculate_spread(observation)

        # RSI
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        if rsi is None:
            rsi = 50.0  # Neutrale fallback

        # MACD
        macd_result = TechnicalIndicators.calculate_macd(prices)
        if macd_result is not None:
            macd = macd_result.macd_line
            macd_signal = macd_result.signal_line
            macd_histogram = macd_result.histogram
        else:
            macd = 0.0
            macd_signal = 0.0
            macd_histogram = 0.0

        # Bollinger Bands
        bb_result = TechnicalIndicators.calculate_bollinger_bands(prices)
        if bb_result is not None:
            bb_upper = bb_result.upper
            bb_lower = bb_result.lower
            bb_width = bb_result.width
            bb_percent_b = bb_result.percent_b
        else:
            bb_upper = observation.price
            bb_lower = observation.price
            bb_width = 0.0
            bb_percent_b = 0.5

        # ADX - voor trend strength
        # Zonder OHLC data gebruiken we close als proxy voor high/low
        adx = None
        if len(prices) >= self.MIN_DATA_FOR_ADX:
            # Simuleer high/low uit close prijzen met kleine offset
            highs = [p * 1.002 for p in prices]  # +0.2% als proxy
            lows = [p * 0.998 for p in prices]  # -0.2% als proxy
            adx = TechnicalIndicators.calculate_adx(highs, lows, prices, period=14)
        if adx is None:
            adx = 25.0  # Neutrale fallback

        # Volume ratio
        volume_ma_ratio = 1.0
        if len(volumes) >= 20:
            avg_vol = sum(volumes[-20:]) / 20
            if avg_vol > 0:
                volume_ma_ratio = volumes[-1] / avg_vol

        indicators = {
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_histogram": macd_histogram,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "bb_width": bb_width,
            "bb_percent_b": bb_percent_b,
            "adx": adx,
            "spread_pct": spread_pct,
            "volume_ma_ratio": volume_ma_ratio,
            "data_points": float(len(prices)),
        }

        return indicators

    def _calculate_spread(self, observation: Observation) -> float:
        """Bereken bid/ask spread percentage."""
        bids = observation.orderbook.get("bids", [])
        asks = observation.orderbook.get("asks", [])

        if bids and asks:
            bid_price = float(bids[0][0]) if bids else observation.price
            ask_price = float(asks[0][0]) if asks else observation.price
            if bid_price > 0:
                return ((ask_price - bid_price) / bid_price) * 100
        return 0.0

    def _detect_regime(
        self, indicators: dict[str, float], observation: Observation
    ) -> MarketRegime:
        """
        Detecteer market regime met de IntelligentRegimeDetector (ML pipeline).

        Berekent additionele features zoals volatiliteit en momentum voor
        het ml-model.
        """
        import math

        prices = self.price_history.get_prices(observation.symbol)

        # Calculate trailing momentum (10 periods if available)
        momentum_10d = 0.0
        if len(prices) >= 11:
            momentum_10d = (prices[-1] - prices[-11]) / prices[-11]

        # Volatility 20d
        volatility_20d = 0.0
        if len(prices) >= 20:
            recent_20 = prices[-20:]
            mean_20 = sum(recent_20) / 20.0
            variance_20 = sum((p - mean_20) ** 2 for p in recent_20) / 20.0
            std_20 = math.sqrt(variance_20)
            # Normaliseer volatiliteit relatief naar standaard deviatie
            vol_raw = std_20 / mean_20 if mean_20 > 0 else 0.0
            # Cap on reasonable norm factor
            volatility_20d = min(vol_raw * 20.0, 1.0)

        features = {
            "volatility_20d": volatility_20d,
            "price_momentum_10d": momentum_10d,
            "rsi_14": indicators.get("rsi", 50.0),
            "adx_14": indicators.get("adx", 25.0),
            "bb_width_norm": min(indicators.get("bb_width", 0.0) / 5.0, 1.0),
        }

        return self.regime_detector.detect_regime(features)

    def _calculate_technical_confidence(self, indicators: dict[str, float]) -> float:
        """
        Bereken composite confidence score uit meerdere indicatoren.

        Gewichten:
        - RSI extremen: 30% (sterke signalen bij <30 of >70)
        - MACD alignment: 25% (histogram grootte als maat voor momentum)
        - ADX trend strength: 25% (ADX > 25 = strong signal)
        - Spread: 20% (lage spread = betere marktcondities)

        Returns:
            Confidence in [0, 1]
        """
        rsi = indicators.get("rsi", 50.0)
        macd_histogram = indicators.get("macd_histogram", 0.0)
        adx = indicators.get("adx", 25.0)
        spread = indicators.get("spread_pct", 0.0)

        # RSI extremen → hogere confidence (0.0 bij RSI=50, 1.0 bij RSI=0/100)
        rsi_confidence = abs(rsi - 50.0) / 50.0

        # MACD histogram → sterker histogram = hogere confidence
        # Normaliseer met tanh om extreme waarden te beperken
        import math

        macd_confidence = abs(math.tanh(macd_histogram * 0.01))

        # ADX → >25 is sterk, >40 is heel sterk
        adx_confidence = min(adx / 50.0, 1.0)

        # Spread → lage spread = hogere confidence
        spread_confidence = max(0.0, 1.0 - (spread / 1.0))

        # Gewogen gemiddelde
        confidence = (
            0.30 * rsi_confidence
            + 0.25 * macd_confidence
            + 0.25 * adx_confidence
            + 0.20 * spread_confidence
        )

        return max(0.0, min(1.0, confidence))

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        BaseAgent abstract method - gebruik orient() in plaats daarvan.
        """
        logger.warning("analyze() called on Analyst - use orient() instead")
        return {
            "recommendation": "Use orient() method for AnalystAgent",
            "confidence": 0.0,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Krijg Analyst statistieken."""
        health = self.health_check()
        return {**health, "analyses_completed": self.analyses_completed}
