"""
Sentiment Agent - LLM-powered sentiment analysis using Ollama/DeepSeek
Local, free, and privacy-preserving sentiment scoring.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import aiohttp

from backend.core.memory_agent import MemoryAgent
from backend.schemas.agent_messages import AgentMessage

logger = logging.getLogger(__name__)


@dataclass
class SentimentAnalysis:
    """Result of sentiment analysis."""

    score: float  # 0.0 to 1.0
    trend: str  # bullish, bearish, neutral
    confidence: float  # 0.0 to 1.0
    rationale: str
    key_factors: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "trend": self.trend,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "key_factors": self.key_factors,
            "timestamp": self.timestamp.isoformat(),
        }


class SentimentAgent:
    """
    Sentiment Agent uses local LLM (DeepSeek via Ollama) for sentiment analysis.

    Features:
    - Free (no API costs)
    - Private (local processing)
    - Fast (no network latency to external APIs)
    - Customizable prompt engineering
    """

    def __init__(
        self,
        memory_agent: MemoryAgent | None = None,
        message_bus=None,
        ollama_url: str = "http://ollama:11434",
        model: str = "deepseek-r1:7b",
        temperature: float = 0.3,
    ):
        self.memory = memory_agent or MemoryAgent()
        self.message_bus = message_bus
        self.ollama_url = ollama_url
        self.model = model
        self.temperature = temperature

        self.name = "SentimentAgent"
        self.prana = 50.0
        self.is_active = True
        self._ollama_available = False

    async def check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=5) as resp:
                    self._ollama_available = resp.status == 200
                    return self._ollama_available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._ollama_available = False
            return False

    async def analyze_news(self, headlines: list[str], coin: str = "BTC") -> SentimentAnalysis:
        """
        Analyze sentiment of news headlines using DeepSeek.

        Args:
            headlines: List of news headlines
            coin: Coin symbol for context

        Returns:
            SentimentAnalysis with score, trend, and rationale
        """
        if not headlines:
            return SentimentAnalysis(
                score=0.5,
                trend="neutral",
                confidence=0.0,
                rationale="No headlines provided",
                key_factors=[],
            )

        # Check Ollama availability
        if not self._ollama_available:
            await self.check_ollama()

        if not self._ollama_available:
            # Fallback to rule-based scoring
            return self._fallback_analysis(headlines, coin)

        # Sanitize headlines to prevent prompt injection
        sanitized_headlines = self._sanitize_headlines(headlines[:15])
        headlines_text = "\n".join([f"- {h}" for h in sanitized_headlines])

        prompt = f"""You are a crypto trading sentiment analyst. Analyze the following news headlines for {coin} and provide a sentiment assessment.

HEADLINES:
{headlines_text}

Provide your analysis in this exact JSON format:
{{
    "score": 0.75,
    "trend": "bullish",
    "confidence": 0.85,
    "rationale": "Brief explanation of the sentiment",
    "key_factors": ["Factor 1", "Factor 2", "Factor 3"]
}}

Score: 0.0-0.4 bearish, 0.4-0.6 neutral, 0.6-1.0 bullish
Trend: exactly "bullish", "bearish", or "neutral"
Confidence: 0.0-1.0 based on clarity of signals

JSON response only:"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": 500,
                        },
                    },
                    timeout=60,
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Ollama returned {resp.status}")
                    result = await resp.json()

            response_text = result.get("response", "")

            # Extract JSON from response
            analysis = self._parse_llm_response(response_text)

            logger.info(f"Sentiment analysis for {coin}: {analysis.trend} ({analysis.score:.2f})")
            return analysis

        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {e}")
            return self._fallback_analysis(headlines, coin)

    def _parse_llm_response(self, text: str) -> SentimentAnalysis:
        """Parse JSON response from LLM."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[^}]*"score"[^}]*"trend"[^}]*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Try full response as JSON
                data = json.loads(text)

            return SentimentAnalysis(
                score=float(data.get("score", 0.5)),
                trend=data.get("trend", "neutral"),
                confidence=float(data.get("confidence", 0.5)),
                rationale=data.get("rationale", "No rationale provided"),
                key_factors=data.get("key_factors", []),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON: {e}")
            # Try regex extraction as last resort
            return self._regex_extract(text)

    def _regex_extract(self, text: str) -> SentimentAnalysis:
        """Extract sentiment info using regex as fallback."""
        text_lower = text.lower()

        # Determine trend
        if "bullish" in text_lower or "positive" in text_lower:
            trend = "bullish"
            score = 0.75
        elif "bearish" in text_lower or "negative" in text_lower:
            trend = "bearish"
            score = 0.25
        else:
            trend = "neutral"
            score = 0.5

        # Extract confidence if mentioned
        confidence = 0.5
        conf_match = re.search(r"confidence[:\s]+([0-9.]+)", text_lower)
        if conf_match:
            confidence = float(conf_match.group(1))

        # Extract key factors (bullet points)
        factors = re.findall(r"[-*]\s*([^\n]+)", text)

        return SentimentAnalysis(
            score=score,
            trend=trend,
            confidence=confidence,
            rationale=text[:200] + "..." if len(text) > 200 else text,
            key_factors=factors[:5],
        )

    def _fallback_analysis(self, headlines: list[str], coin: str) -> SentimentAnalysis:
        """Rule-based fallback when LLM is unavailable."""
        positive_words = [
            "surge",
            "rally",
            "bull",
            "breakout",
            "adoption",
            "partnership",
            "launch",
            "upgrade",
            "growth",
            "gain",
            "up",
            "high",
            "record",
            "moon",
            "pump",
            "explode",
            "soar",
            "massive",
            "bullish",
            "support",
        ]

        negative_words = [
            "crash",
            "dump",
            "bear",
            "decline",
            "fall",
            "drop",
            "low",
            "hack",
            "scam",
            "fud",
            "ban",
            "regulation",
            "sec",
            "lawsuit",
            "down",
            "loss",
            "bearish",
            "resistance",
            "sell",
            "short",
        ]

        all_text = " ".join(headlines).lower()

        pos_count = sum(1 for word in positive_words if word in all_text)
        neg_count = sum(1 for word in negative_words if word in all_text)

        total = pos_count + neg_count
        if total == 0:
            score = 0.5
            trend = "neutral"
        else:
            score = pos_count / total
            if score > 0.6:
                trend = "bullish"
            elif score < 0.4:
                trend = "bearish"
            else:
                trend = "neutral"

        confidence = min(1.0, total / 10)  # More hits = higher confidence

        # Extract key factors (words that matched)
        factors = []
        for word in positive_words[:3]:
            if word in all_text:
                factors.append(f"Positive: {word}")
        for word in negative_words[:3]:
            if word in all_text:
                factors.append(f"Negative: {word}")

        return SentimentAnalysis(
            score=score,
            trend=trend,
            confidence=confidence,
            rationale=f"Rule-based analysis: {pos_count} positive, {neg_count} negative indicators",
            key_factors=factors[:5],
        )

    async def analyze_social_media(
        self, texts: list[str], source: str = "twitter"
    ) -> SentimentAnalysis:
        """
        Analyze sentiment of social media posts.

        Args:
            texts: List of social media posts
            source: Source platform (twitter, reddit, etc.)
        """
        # Similar to analyze_news but with social media specific prompt
        if not texts:
            return SentimentAnalysis(
                score=0.5,
                trend="neutral",
                confidence=0.0,
                rationale="No texts provided",
            )

        if not self._ollama_available:
            await self.check_ollama()

        if not self._ollama_available:
            return self._fallback_analysis(texts, "SOCIAL")

        posts_text = "\n".join([f"- {t[:200]}" for t in texts[:20]])  # Limit length

        prompt = f"""Analyze the sentiment of these {source} posts about cryptocurrency:

POSTS:
{posts_text}

Provide analysis in JSON format:
{{
    "score": 0.65,
    "trend": "bullish",
    "confidence": 0.70,
    "rationale": "Brief summary",
    "key_factors": ["Factor 1", "Factor 2"]
}}

JSON only:"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": self.temperature},
                    },
                    timeout=60,
                ) as resp:
                    result = await resp.json()
                    return self._parse_llm_response(result.get("response", ""))
        except Exception as e:
            logger.error(f"Social media analysis failed: {e}")
            return self._fallback_analysis(texts, "SOCIAL")

    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        if message.type == "ANALYZE_SENTIMENT":
            headlines = message.payload.get("headlines", [])
            coin = message.payload.get("coin", "BTC")

            analysis = await self.analyze_news(headlines, coin)

            # Store in memory
            self.memory.store_thought(
                agent_id=self.name,
                text=f"Sentiment analysis for {coin}: {analysis.trend} (score: {analysis.score:.2f}, confidence: {analysis.confidence:.2f})",
                metadata={
                    "type": "sentiment_analysis",
                    "coin": coin,
                    "trend": analysis.trend,
                    "score": analysis.score,
                    "confidence": analysis.confidence,
                },
            )

            # Broadcast result
            if self.message_bus:
                await self.message_bus(
                    AgentMessage(
                        source=self.name,
                        target=message.source or "all",
                        type="SENTIMENT_UPDATE",
                        payload={
                            "coin": coin,
                            "analysis": analysis.to_dict(),
                        },
                    )
                )

            return analysis.to_dict()

        elif message.type == "NEWS_UPDATE":
            # Auto-analyze news when received
            news = message.payload.get("news", {})
            sentiments = message.payload.get("sentiments", {})

            for coin, items in news.items():
                if isinstance(items, list) and len(items) > 0:
                    headlines = [i.get("title", "") for i in items if isinstance(i, dict)]
                    if headlines:
                        await self.handle_message(
                            AgentMessage(
                                source=message.source,
                                target=self.name,
                                type="ANALYZE_SENTIMENT",
                                payload={"headlines": headlines, "coin": coin},
                            )
                        )

    async def start(self):
        """Start the agent."""
        logger.info("SentimentAgent starting...")
        self.is_active = True
        await self.check_ollama()
        if self._ollama_available:
            logger.info(f"SentimentAgent connected to Ollama ({self.model})")
        else:
            logger.warning("SentimentAgent using fallback mode (Ollama unavailable)")

    async def stop(self):
        """Stop the agent."""
        logger.info("SentimentAgent stopped")
        self.is_active = False
