"""
Sentiment Agent using LLM for market sentiment analysis.

Uses LLM's generate_structured to analyze market sentiment from context.
"""

from backend.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from backend.llm.provider_interface import LLMProvider
    from backend.events.event_bus import EventBus


class SentimentAnalysis(BaseModel):
    """Structured sentiment analysis result."""

    sentiment: str = Field(
        ..., description="Market sentiment: bullish, bearish, or neutral"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Explanation of sentiment analysis")
    key_factors: list[str] = Field(
        default_factory=list, description="Key factors influencing sentiment"
    )


class SentimentAgent(BaseAgent):
    """
    Market sentiment analyzer using LLM.
    Analyzes news, social signals, and market context to determine sentiment.
    """

    SYSTEM_PROMPT = """You are an expert market sentiment analyst for cryptocurrency trading.
Analyze the provided market data and context to determine the overall market sentiment.

Consider:
- News headlines and events
- Social media sentiment
- Market indicators (price, volume)
- Historical patterns

Provide sentiment as: bullish, bearish, or neutral
Give confidence between 0.0 and 1.0
Explain your reasoning clearly
List key factors that influenced your analysis"""

    def __init__(
        self,
        agent_name: str = "SentimentAgent",
        llm_provider: Optional["LLMProvider"] = None,
        event_bus: Optional["EventBus"] = None,
    ):
        super().__init__(
            agent_name=agent_name, llm_provider=llm_provider, event_bus=event_bus
        )

    async def analyze(
        self, features: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze market sentiment using LLM.

        Args:
            features: Market features (price, volume, etc.)
            context: Additional context (news, social signals, symbol)

        Returns:
            Dict with sentiment, action, confidence, and reasoning
        """
        # If no LLM, return fallback
        if not self.llm_provider:
            return {
                "sentiment": "neutral",
                "action": "hold",
                "confidence": 0.3,
                "reasoning": "LLM provider not available - using fallback",
                "key_factors": [],
            }

        # Build prompt with context
        prompt = self._build_prompt(features, context)

        try:
            # Use LLM to analyze sentiment
            analysis = await self.llm_provider.generate_structured(
                prompt=prompt,
                schema=SentimentAnalysis,
                system_prompt=self.SYSTEM_PROMPT,
            )

            # Map sentiment to action
            action = self._sentiment_to_action(analysis.sentiment)

            # Prepare result
            result = {
                "sentiment": analysis.sentiment,
                "action": action,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "key_factors": analysis.key_factors,
            }

            # Publish thought to event bus
            if self.event_bus:
                await self.publish_thought(
                    reasoning=analysis.reasoning,
                    confidence=analysis.confidence,
                    data={
                        "sentiment": analysis.sentiment,
                        "key_factors": analysis.key_factors,
                    },
                )

            return result

        except Exception as e:
            self.logger.error(f"Sentiment analysis error: {e}")
            return {
                "sentiment": "neutral",
                "action": "hold",
                "confidence": 0.2,
                "reasoning": f"Error during analysis: {str(e)}",
                "key_factors": [],
            }

    def _build_prompt(self, features: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build analysis prompt from features and context."""
        symbol = context.get("symbol", "Unknown")
        news = context.get("news", "No news available")
        price = features.get("price", "N/A")
        volume = features.get("volume", "N/A")

        prompt = f"""Analyze market sentiment for {symbol}:

Market Data:
- Current Price: {price}
- Volume: {volume}

Context:
{news}

Additional Information:
{str(context)}

Provide your sentiment analysis."""

        return prompt

    def _sentiment_to_action(self, sentiment: str) -> str:
        """Map sentiment to trading action."""
        sentiment_lower = sentiment.lower()

        if sentiment_lower == "bullish":
            return "buy"
        elif sentiment_lower == "bearish":
            return "sell"
        else:
            return "hold"
