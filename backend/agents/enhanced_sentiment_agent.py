"""
Enhanced Sentiment Agent with ToolBroker Integration.

This agent uses external tools via the ToolBroker to:
1. Analyze sentiment from news and social media
2. Get macro indicators for context
3. Calculate technical indicators
4. Make informed trading decisions

Example usage:
    agent = EnhancedSentimentAgent(tool_broker_url="http://localhost:8001")
    result = await agent.analyze(
        features={"symbol": "BTC", "price": 45000, "history": [...]},
        context={"portfolio_value": 100000}
    )
"""

import logging
from datetime import UTC, datetime
from typing import Any

from backend.agents.agent_with_tools import AgentWithTools
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class EnhancedSentimentAgent(AgentWithTools):
    """
    Enhanced sentiment agent that uses external tools for analysis.

    Tool Usage:
    - external__sentiment_analysis: Get sentiment from news/social
    - external__macro_indicators: Get macro economic context
    - external__technical_indicators: Calculate technical signals
    - external__market_news: Get latest news
    - vedastro__generate_signal: Get astrological signal
    - elemental__ether_consensus: Get elemental consensus
    """

    def __init__(
        self,
        llm_provider: Any = None,
        event_bus: Any = None,
        agent_role: AgentRole = AgentRole.STANDARD,
        tool_broker_url: str | None = None,
    ):
        super().__init__(
            agent_name="EnhancedSentimentAgent",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=agent_role,
            tool_broker_url=tool_broker_url,
        )

        self.sentiment_threshold = 0.6
        self.confidence_threshold = 0.7

    async def analyze(
        self,
        features: dict[str, Any],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze market using external tools.

        Args:
            features: Market features including symbol, price, history
            context: Trading context including portfolio value

        Returns:
            Trading decision with confidence and reasoning
        """
        symbol = features.get("symbol", "UNKNOWN")
        price = features.get("price", 0.0)
        price_history = features.get("history", [])
        portfolio_value = context.get("portfolio_value", 100000)

        self.logger.info(f"Analyzing {symbol} at ${price}")

        # === STEP 1: Get External Data via ToolBroker ===

        # 1.1 Sentiment Analysis
        sentiment_result = await self.call_tool(
            "tool__external_sentiment_analysis",
            {"symbol": symbol, "source": "combined"}
        )
        sentiment_score = sentiment_result.get("sentiment_score", 0.0)
        sentiment_confidence = sentiment_result.get("confidence", 0.5)

        # 1.2 Technical Indicators
        tech_result = await self.call_tool(
            "tool__external_technical_indicators",
            {
                "symbol": symbol,
                "price_history": price_history,
                "indicators": ["rsi", "macd", "sma", "bb"]
            }
        )
        tech_signal = tech_result.get("overall_signal", "neutral")
        tech_indicators = tech_result.get("indicators", {})

        # 1.3 Market News
        news_result = await self.call_tool(
            "tool__external_market_news",
            {"symbol": symbol, "category": "crypto", "limit": 3}
        )
        articles = news_result.get("articles", [])
        news_sentiment = self._aggregate_news_sentiment(articles)

        # 1.4 Macro Context
        macro_result = await self.call_tool(
            "tool__external_macro_indicators",
            {"indicator": "all"}
        )
        macro_trend = self._assess_macro_trend(macro_result)

        # === STEP 2: Get VedAstro Signal ===

        vedastro_result = await self.get_vedastro_signal(symbol, price)
        vedastro_signal = vedastro_result.get("signal", "hold")
        vedastro_confidence = vedastro_result.get("confidence", 0.5)

        # === STEP 3: Elemental Consensus ===

        # Convert signals to votes
        sentiment_vote = self._sentiment_to_vote(sentiment_score)
        tech_vote = self._tech_signal_to_vote(tech_signal)
        news_vote = self._sentiment_to_vote(news_sentiment)
        macro_vote = macro_trend

        consensus_result = await self.get_elemental_consensus(
            fire_vote=sentiment_vote,
            earth_vote=tech_vote,
            water_vote=news_vote,
            air_vote=macro_vote,
        )

        consensus_signal = consensus_result.get("consensus", "neutral")
        harmony_score = consensus_result.get("harmony_score", 0.5)

        # === STEP 4: Final Decision ===

        # Weight different signals
        final_score = (
            sentiment_score * 0.25 +
            self._vote_to_score(sentiment_vote) * 0.15 +
            self._vote_to_score(tech_vote) * 0.20 +
            self._vote_to_score(news_vote) * 0.15 +
            (1 if vedastro_signal == "buy" else -1 if vedastro_signal == "sell" else 0) * vedastro_confidence * 0.15 +
            self._vote_to_score(macro_vote) * 0.10
        )

        # Determine signal
        if final_score > 0.3 and consensus_signal == "approved":
            signal = "buy"
            confidence = min(abs(final_score) * harmony_score, 1.0)
        elif final_score < -0.3 and consensus_signal == "approved":
            signal = "sell"
            confidence = min(abs(final_score) * harmony_score, 1.0)
        else:
            signal = "hold"
            confidence = 0.5

        # === STEP 5: Position Sizing (if buy signal) ===

        position_size = None
        if signal == "buy" and confidence >= self.confidence_threshold:
            dominant_planet = vedastro_result.get("dominant_planet", "SUN")

            size_result = await self.calculate_position_size(
                symbol=symbol,
                portfolio_value=portfolio_value,
                vedastro_score=vedastro_result.get("score", 50),
                dominant_planet=dominant_planet,
                price_history=price_history,
            )
            position_size = size_result.get("position_eur")

        # Build reasoning
        reasoning = self._build_reasoning(
            symbol=symbol,
            sentiment_score=sentiment_score,
            tech_signal=tech_signal,
            news_sentiment=news_sentiment,
            vedastro_signal=vedastro_signal,
            consensus=consensus_signal,
            final_score=final_score,
        )

        # Publish thought
        await self.publish_thought(reasoning, confidence, {
            "symbol": symbol,
            "signal": signal,
            "sentiment": sentiment_score,
        })

        return {
            "agent": self.agent_name,
            "symbol": symbol,
            "signal": signal,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "position_size": position_size,
            "metadata": {
                "sentiment_score": sentiment_score,
                "technical_signal": tech_signal,
                "vedastro_signal": vedastro_signal,
                "consensus": consensus_signal,
                "harmony_score": harmony_score,
                "indicators": tech_indicators,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }

    def _sentiment_to_vote(self, sentiment: float) -> float:
        """Convert sentiment score to elemental vote."""
        if sentiment > 0.5:
            return 1.0  # Strong buy
        elif sentiment > 0.2:
            return 0.5  # Weak buy
        elif sentiment < -0.5:
            return -1.0  # Strong sell
        elif sentiment < -0.2:
            return -0.5  # Weak sell
        else:
            return 0.0  # Neutral

    def _tech_signal_to_vote(self, signal: str) -> float:
        """Convert technical signal to vote."""
        mapping = {
            "strong_buy": 1.0,
            "buy": 0.7,
            "neutral": 0.0,
            "sell": -0.7,
            "strong_sell": -1.0,
        }
        return mapping.get(signal, 0.0)

    def _vote_to_score(self, vote: float) -> float:
        """Convert vote to score."""
        return vote

    def _aggregate_news_sentiment(self, articles: list[dict]) -> float:
        """Aggregate sentiment from news articles."""
        if not articles:
            return 0.0

        scores = []
        for article in articles:
            sentiment = article.get("sentiment", "neutral")
            if sentiment == "positive":
                scores.append(0.7)
            elif sentiment == "negative":
                scores.append(-0.7)
            else:
                scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def _assess_macro_trend(self, macro: dict) -> float:
        """Assess macro trend for vote."""
        # Simplified macro assessment
        inflation = macro.get("inflation", {}).get("cpi_yoy", 3.0)
        rates = macro.get("rates", {}).get("fed_funds", 5.0)

        # High inflation + high rates = bearish
        if inflation > 4.0 and rates > 5.0:
            return -0.5
        # Low inflation + low rates = bullish
        elif inflation < 2.5 and rates < 3.0:
            return 0.5
        else:
            return 0.0

    def _build_reasoning(
        self,
        symbol: str,
        sentiment_score: float,
        tech_signal: str,
        news_sentiment: float,
        vedastro_signal: str,
        consensus: str,
        final_score: float,
    ) -> str:
        """Build human-readable reasoning."""
        parts = [
            f"Analysis for {symbol}:",
            f"- Sentiment: {sentiment_score:+.2f} ({self._sentiment_label(sentiment_score)})",
            f"- Technical: {tech_signal}",
            f"- News: {news_sentiment:+.2f}",
            f"- VedAstro: {vedastro_signal}",
            f"- Elemental Consensus: {consensus}",
            f"- Final Score: {final_score:+.2f}",
        ]

        return "\n".join(parts)

    def _sentiment_label(self, score: float) -> str:
        """Get label for sentiment score."""
        if score > 0.5:
            return "Very Bullish"
        elif score > 0.2:
            return "Bullish"
        elif score < -0.5:
            return "Very Bearish"
        elif score < -0.2:
            return "Bearish"
        else:
            return "Neutral"


# ============================================================================
# Example usage
# ============================================================================

async def example():
    """Example of using EnhancedSentimentAgent."""

    # Create agent
    agent = EnhancedSentimentAgent(
        tool_broker_url="http://localhost:8001"
    )

    # Check ToolBroker health
    health = await agent.check_toolbroker_health()
    print(f"ToolBroker health: {health}")

    # List available tools
    tools = await agent.list_available_tools()
    print(f"Available tools: {tools}")

    # Analyze
    result = await agent.analyze(
        features={
            "symbol": "BTC",
            "price": 45000.0,
            "history": [40000 + i * 100 for i in range(50)],  # Simulated history
        },
        context={
            "portfolio_value": 100000.0,
        }
    )

    print(f"\nDecision: {result['signal']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Reasoning:\n{result['reasoning']}")

    # Cleanup
    await agent.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example())
