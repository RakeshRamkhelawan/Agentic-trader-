"""
Analyst Agent - Orient Phase van OODA Loop.

Analyseert marktdata en genereert technische en sentiment indicatoren.
"""

import logging
from typing import Any, Dict, List, Optional

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (MarketRegime, Observation,
                                             Orientation)
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """
    Analyst Agent - Technical & Sentiment Analysis specialist.

    Rol in OODA: **ORIENT**
    - Berekent technische indicatoren (RSI, MACD, Bollinger)
    - Aggregeert sentiment scores
    - Detecteert market regime
    - Voor output: Orientation met confidence score
    """

    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        core_confidence_weight: float = 0.5,
    ):
        """
        Initialiseer Analyst.

        Args:
            llm_provider: LLM voor narrative generation
            event_bus: Event bus
            core_confidence_weight: Weight voor core_sentiment in total confidence
        """
        super().__init__(
            agent_name="Analyst",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST,
        )
        self.core_confidence_weight = core_confidence_weight
        self.analyses_completed = 0

    async def orient(
        self,
        observation: Observation,
        core_sentiment: float,
        rag_context: Optional[List[str]] = None,
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
            # Calculate technical indicators
            indicators = self._calculate_indicators(observation)

            # Detect market regime
            regime = self._detect_regime(indicators, observation)

            # Calculate total confidence
            # Combineer core_sentiment met technical strength
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

            logger.info(
                f"Orientation completed: {observation.symbol}, "
                f"regime={regime.value}, confidence={total_confidence:.3f}"
            )

            return orientation

        except Exception as e:
            logger.error(f"Orient failed for {observation.symbol}: {e}")
            self.record_activity(success=False)
            raise

    def _calculate_indicators(self, observation: Observation) -> Dict[str, float]:
        """
        Bereken technische indicatoren.

        Note: Deze implementatie gebruikt single-point data voor demo.
        In productie zou je een sliding window van prijzen gebruiken.

        Returns:
            Dict met indicator names en values
        """
        # Extract orderbook data
        bids = observation.orderbook.get("bids", [])
        asks = observation.orderbook.get("asks", [])

        # Calculate spread
        if bids and asks:
            bid_price = float(bids[0][0]) if bids else observation.price
            ask_price = float(asks[0][0]) if asks else observation.price
            spread_pct = ((ask_price - bid_price) / bid_price) * 100
        else:
            spread_pct = 0.0

        # Voor demo: simplified indicators
        # In productie: gebruik pandas_ta of eigen implementatie met historische data
        indicators = {
            "rsi": 50.0,  # Placeholder (zou berekend worden uit price history)
            "macd": 0.0,  # Placeholder
            "bb_width": spread_pct,  # Simplified Bollinger Band width proxy
            "volume_ma_ratio": 1.0,  # Volume vs moving average
            "spread_pct": spread_pct,
        }

        return indicators

    def _detect_regime(
        self, indicators: Dict[str, float], observation: Observation
    ) -> MarketRegime:
        """
        Detecteer market regime op basis van indicatoren.

        Simplified heuristiek:
        - VOLATILE: Hoge spread
        - BULL: RSI > 60
        - BEAR: RSI < 40
        - SIDEWAYS: Anders

        Returns:
            MarketRegime enum
        """
        rsi = indicators.get("rsi", 50.0)
        spread = indicators.get("spread_pct", 0.0)

        # Volatility check
        if spread > 0.5:  # >0.5% spread = volatiel
            return MarketRegime.VOLATILE

        # Trend checks
        if rsi > 60:
            return MarketRegime.BULL
        elif rsi < 40:
            return MarketRegime.BEAR
        else:
            return MarketRegime.SIDEWAYS

    def _calculate_technical_confidence(self, indicators: Dict[str, float]) -> float:
        """
        Bereken confidence score uit technische indicatoren.

        Heuristiek:
        - Lage spread = hogere confidence
        - RSI extremen = hogere confidence
        - Matige values = lagere confidence

        Returns:
            Confidence in [0, 1]
        """
        rsi = indicators.get("rsi", 50.0)
        spread = indicators.get("spread_pct", 0.0)

        # RSI extremen geven hogere confidence
        rsi_confidence = abs(rsi - 50) / 50.0  # 0.0 bij RSI=50, 1.0 bij RSI=0/100

        # Lage spread geeft hogere confidence
        spread_confidence = max(
            0.0, 1.0 - (spread / 1.0)
        )  # 1.0 bij spread=0, 0.0 bij spread=1%

        # Average
        confidence = (rsi_confidence + spread_confidence) / 2.0

        return max(0.0, min(1.0, confidence))

    async def analyze(
        self, features: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        BaseAgent abstract method - gebruik orient() in plaats daarvan.
        """
        logger.warning("analyze() called on Analyst - use orient() instead")
        return {
            "recommendation": "Use orient() method for AnalystAgent",
            "confidence": 0.0,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Krijg Analyst statistieken."""
        health = self.health_check()
        return {**health, "analyses_completed": self.analyses_completed}
