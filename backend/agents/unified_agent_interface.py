"""
Unified Agent Interface - Wrapper for consistent signal generation
Makes all agents compatible with MetaOrchestrator
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class UnifiedAgentInterface(ABC):
    """
    Unified interface that wraps any agent to provide consistent:
    - analyze(features, context) -> signal
    - generate_signal(market_state) -> signal
    """

    def __init__(self, agent: Any, agent_name: str = None):
        self.wrapped_agent = agent
        self.agent_name = agent_name or getattr(agent, "agent_name", "UnknownAgent")
        self.agent_type = type(agent).__name__

        # Copy attributes from wrapped agent
        if hasattr(agent, "chitta"):
            self.chitta = agent.chitta
        if hasattr(agent, "prana_level"):
            self.prana_level = agent.prana_level
        if hasattr(agent, "guna_balance"):
            self.guna_balance = agent.guna_balance
        if hasattr(agent, "llm_provider"):
            self.llm_provider = agent.llm_provider

    async def analyze(self, features: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main interface method - converts features/context to signal.
        All agents MUST implement this.
        """
        try:
            # Extract market state from features/context
            market_state = features.copy()
            if "market_state" in context:
                market_state.update(context["market_state"])

            # Generate signal using unified method
            signal = await self.generate_signal(market_state)
            return signal

        except Exception as e:
            logger.error(f"[{self.agent_name}] analyze error: {e}")
            return self._default_signal()

    @abstractmethod
    async def generate_signal(self, market_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading signal from market state.
        Must return: {action, confidence, harmony, reasoning}
        """
        pass

    def _default_signal(self) -> Dict[str, Any]:
        """Default HOLD signal on error."""
        return {
            "action": "HOLD",
            "confidence": 0.0,
            "harmony": 0.0,
            "reasoning": "Error in signal generation",
        }

    def _calculate_confidence(self, indicators: Dict) -> float:
        """Calculate confidence from indicators."""
        confidence = 0.5

        # Adjust based on RSI strength
        rsi = indicators.get("rsi", 50)
        if rsi < 30 or rsi > 70:
            confidence += 0.2

        # Adjust based on ADX trend strength
        adx = indicators.get("adx", 20)
        if adx > 25:
            confidence += 0.15

        # Adjust based on regime clarity
        regime = indicators.get("regime", "neutral")
        if regime in ["bullish", "bearish"]:
            confidence += 0.1

        return min(1.0, confidence)


class SentimentAgentWrapper(UnifiedAgentInterface):
    """Wrapper for SentimentAgentV2."""

    async def generate_signal(self, market_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sentiment-based signal."""
        try:
            # Check if wrapped agent has sentiment analysis
            if hasattr(self.wrapped_agent, "analyze_sentiment"):
                sentiment = await self.wrapped_agent.analyze_sentiment(
                    market_state.get("symbol", "BTC"), market_state
                )
                sentiment_score = sentiment.get("score", 0.5)
            else:
                # Simple sentiment logic
                rsi = market_state.get("rsi", 50)
                sentiment_score = (100 - rsi) / 100 if rsi > 50 else rsi / 100

            # Convert sentiment to action
            if sentiment_score > 0.6:
                action = "BUY"
            elif sentiment_score < 0.4:
                action = "SELL"
            else:
                action = "HOLD"

            confidence = abs(sentiment_score - 0.5) * 2  # 0 to 1

            return {
                "action": action,
                "confidence": confidence,
                "harmony": confidence * 0.8,
                "reasoning": f"Sentiment score: {sentiment_score:.2f}",
                "sentiment_score": sentiment_score,
            }

        except Exception as e:
            logger.error(f"[SentimentWrapper] Error: {e}")
            return self._default_signal()


class AnalystAgentWrapper(UnifiedAgentInterface):
    """Wrapper for AnalystAgent."""

    async def generate_signal(self, market_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate technical analysis signal."""
        try:
            # Get technical indicators
            rsi = market_state.get("rsi", 50)
            adx = market_state.get("adx", 20)
            regime = market_state.get("regime", "neutral")

            # Technical analysis logic
            action = "HOLD"
            confidence = 0.5

            # RSI-based signals
            if rsi < 30:
                action = "BUY"
                confidence = 0.6 + (30 - rsi) / 100
            elif rsi > 70:
                action = "SELL"
                confidence = 0.6 + (rsi - 70) / 100

            # ADX trend confirmation
            if adx > 25:
                confidence += 0.1

            # Regime alignment
            if regime == "bullish" and action == "BUY":
                confidence += 0.1
            elif regime == "bearish" and action == "SELL":
                confidence += 0.1

            confidence = min(1.0, confidence)

            return {
                "action": action,
                "confidence": confidence,
                "harmony": confidence * 0.7,
                "reasoning": f"RSI: {rsi}, ADX: {adx}, Regime: {regime}",
                "indicators": {"rsi": rsi, "adx": adx, "regime": regime},
            }

        except Exception as e:
            logger.error(f"[AnalystWrapper] Error: {e}")
            return self._default_signal()


class ElementalAgentWrapper(UnifiedAgentInterface):
    """Wrapper for Elemental agents (Water, Air, Earth, Fire)."""

    def __init__(self, agent: Any, element: str, agent_name: str = None):
        super().__init__(agent, agent_name)
        self.element = element

        # Element-specific characteristics
        self.element_traits = {
            "Water": {"trend_following": 1.0, "momentum": 0.3},
            "Air": {"regime_detection": 1.0, "adaptability": 0.9},
            "Earth": {"execution": 1.0, "stability": 0.8},
            "Fire": {"momentum": 1.0, "aggression": 0.7},
        }

    async def generate_signal(self, market_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate element-specific signal."""
        try:
            traits = self.element_traits.get(self.element, {})

            rsi = market_state.get("rsi", 50)
            adx = market_state.get("adx", 20)
            regime = market_state.get("regime", "neutral")

            # Element-specific logic
            if self.element == "Water":
                # Trend following - hold positions longer
                action = self._water_logic(rsi, adx, regime)
            elif self.element == "Air":
                # Regime detection - quick adaptation
                action = self._air_logic(rsi, adx, regime)
            elif self.element == "Earth":
                # Conservative execution
                action = self._earth_logic(rsi, adx, regime)
            elif self.element == "Fire":
                # Momentum chasing
                action = self._fire_logic(rsi, adx, regime)
            else:
                action = "HOLD"

            confidence = self._calculate_element_confidence(rsi, adx, traits)

            return {
                "action": action,
                "confidence": confidence,
                "harmony": confidence * 0.6,
                "reasoning": f"{self.element} element logic applied",
                "element": self.element,
            }

        except Exception as e:
            logger.error(f"[ElementalWrapper-{self.element}] Error: {e}")
            return self._default_signal()

    def _water_logic(self, rsi, adx, regime) -> str:
        if adx > 20 and regime == "bullish":
            return "BUY"
        elif adx > 20 and regime == "bearish":
            return "SELL"
        return "HOLD"

    def _air_logic(self, rsi, adx, regime) -> str:
        if regime == "bullish" and rsi > 50:
            return "BUY"
        elif regime == "bearish" and rsi < 50:
            return "SELL"
        return "HOLD"

    def _earth_logic(self, rsi, adx, regime) -> str:
        # Conservative - need strong confirmation
        if rsi < 25 and adx > 25:
            return "BUY"
        elif rsi > 75 and adx > 25:
            return "SELL"
        return "HOLD"

    def _fire_logic(self, rsi, adx, regime) -> str:
        # Aggressive momentum
        if rsi > 60 and adx > 20:
            return "BUY"
        elif rsi < 40 and adx > 20:
            return "SELL"
        return "HOLD"

    def _calculate_element_confidence(self, rsi, adx, traits) -> float:
        base = 0.5
        if adx > 25:
            base += 0.2
        if rsi < 30 or rsi > 70:
            base += 0.2
        return min(1.0, base)


def wrap_agent(agent: Any, agent_type: str = None) -> UnifiedAgentInterface:
    """
    Factory function to wrap any agent with unified interface.
    """
    agent_class = type(agent).__name__

    if "Sentiment" in agent_class:
        return SentimentAgentWrapper(agent)
    elif "Analyst" in agent_class:
        return AnalystAgentWrapper(agent)
    elif any(elem in agent_class for elem in ["Water", "Air", "Earth", "Fire"]):
        # Determine element from class name
        element = None
        for elem in ["Water", "Air", "Earth", "Fire"]:
            if elem in agent_class:
                element = elem
                break
        return ElementalAgentWrapper(agent, element or "Unknown")
    else:
        # Generic wrapper
        return AnalystAgentWrapper(agent)
