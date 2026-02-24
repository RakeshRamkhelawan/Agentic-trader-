"""
Research Agent Service.

Responsibility:
- Continuous monitoring of news sources.
- Scrape -> Parse -> LLM Analyze -> Publish/Store.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from backend.core.memory_agent import MemoryAgent
from backend.schemas.agent_messages import AgentMessage


async def analyze_text_with_llm(text: str) -> dict[str, Any]:
    """
    Analyze text using DeepSeek LLM via LLMService.
    Returns sentiment analysis, impact score, and summary.
    """
    from backend.llm.service import LLMService

    try:
        # Initialize LLM service (uses DEEPSEEK_API_KEY from env)
        llm_service = LLMService.create_from_env()

        system_prompt = """You are a financial news analyst. Analyze the given text and return a JSON object with:
- sentiment: float between -1.0 (very bearish) and 1.0 (very bullish)
- impact: integer 1-10 indicating news importance (10 = market moving)
- summary: concise 1-sentence summary
- keywords: array of 3-5 relevant keywords

Respond ONLY with valid JSON."""

        prompt = f"Analyze this financial news:\n\n{text[:2000]}"  # Limit input size

        response = await llm_service.provider.generate_text(
            prompt=prompt, system_prompt=system_prompt
        )

        # Parse JSON response
        import json

        try:
            result = json.loads(response.strip())
            return {
                "sentiment": float(result.get("sentiment", 0)),
                "impact": int(result.get("impact", 5)),
                "summary": result.get("summary", text[:100] + "..."),
                "keywords": result.get("keywords", ["crypto", "market"]),
            }
        except json.JSONDecodeError:
            # Fallback: extract info from text response
            logging.warning(f"LLM returned non-JSON: {response[:200]}")
            return _fallback_analysis(text)

    except Exception as e:
        logging.error(f"LLM analysis failed: {e}")
        return _fallback_analysis(text)


def _fallback_analysis(text: str) -> dict[str, Any]:
    """Fallback keyword-based analysis if LLM fails."""
    text_lower = text.lower()
    sentiment = 0.0
    impact = 5

    # Positive indicators
    positive_words = [
        "bull",
        "approve",
        "surge",
        "rally",
        "gain",
        "up",
        "rise",
        "growth",
    ]
    # Negative indicators
    negative_words = ["bear", "crash", "ban", "drop", "fall", "down", "decline", "fear"]

    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)

    if pos_count > neg_count:
        sentiment = 0.5 + min(0.3, pos_count * 0.1)
        impact = min(10, 5 + pos_count)
    elif neg_count > pos_count:
        sentiment = -0.5 - min(0.3, neg_count * 0.1)
        impact = min(10, 5 + neg_count)

    return {
        "summary": text[:100] + "...",
        "sentiment": sentiment,
        "impact": impact,
        "keywords": ["crypto", "market"],
    }


class ResearchAgent:
    def __init__(self, memory_agent: MemoryAgent = None, message_bus=None, strategy=None):
        self.sources = [
            "https://finance.yahoo.com/crypto",
            "https://cointelegraph.com",
            # "https://www.reuters.com/finance"
        ]
        self.memory = memory_agent or MemoryAgent()
        self.message_bus = message_bus  # Callback function or Kafka Producer
        self.logger = logging.getLogger("ResearchAgent")
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

        # Strategy Injection (Phase 11)
        if strategy:
            self.strategy = strategy
        else:
            # Default to MVP Strategy
            from backend.strategies.simple_tremor import SimpleTremorStrategy

            self.strategy = SimpleTremorStrategy(
                {"window_size": 5, "deviation_threshold": 0.02, "max_history": 100}
            )

    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages from the orchestrator."""
        self.logger.info(f"Research Agent received message: {message.type} from {message.source}")
        if message.type == "TIMER_TICK_1MIN":
            await self.run_cycle()
        elif message.type == "TICK_DATA":
            # Ensure payload is dict, might be Pydantic model in some paths
            payload = message.payload
            if hasattr(payload, "to_dict"):
                payload = payload.to_dict()
            await self.process_tick(payload)
        elif message.type == "SIGNAL" and message.payload.get("signal") == "RUN_RESEARCH":
            await self.run_cycle()

    async def process_tick(self, tick_data: dict[str, Any]):
        """
        Phase 11: Delegate to Strategy Strategy.
        """
        # Convert dict to UnifiedMarketEvent if needed, or Strategy handles dict?
        # BaseStrategy expects UnifiedMarketEvent. Use helper or robust casting.

        from backend.core.market_data.models import EventType, UnifiedMarketEvent

        # Try to construct event from dict
        try:
            # Check if it's already an object
            if hasattr(tick_data, "symbol"):
                event = tick_data
            else:
                # Basic validation/defaulting
                from datetime import UTC, datetime

                event = UnifiedMarketEvent(
                    event_type=EventType.TICKER,
                    exchange=tick_data.get("venue", "unknown"),
                    symbol=tick_data.get("symbol", "UNKNOWN"),
                    timestamp=datetime.now(UTC),
                    price=float(tick_data.get("price") or tick_data.get("bid") or 0.0),
                )
        except Exception as e:
            self.logger.warning(f"Failed to parse tick for strategy: {e}")
            return

        # Delegate
        signal_payload = await self.strategy.on_tick(event)

        if signal_payload:
            await self._emit_signal_payload(signal_payload)

    async def _emit_signal_payload(self, payload: dict[str, Any]):
        """Emit formatted signal to orchestrator."""
        direction = "BULLISH" if "BULLISH" in payload.get("signal", "") else "BEARISH"
        symbol = payload.get("symbol")
        price = payload.get("price")

        self.logger.info(f"STRATEGY SIGNAL: {direction} {symbol} @ {price}")

        msg = AgentMessage(
            source="research_v1",
            target="orchestrator_v1",
            type="SIGNAL",
            payload=payload,
        )
        if self.message_bus:
            if asyncio.iscoroutinefunction(self.message_bus):
                await self.message_bus(msg)
            else:
                self.message_bus(msg)

    async def run_cycle(self):
        """One full scrape cycle."""
        self.logger.info("Starting Research Cycle...")

        for url in self.sources:
            try:
                article = await self.fetch_and_parse(url)
                if not article:
                    continue

                # 1. Analyze
                analysis = await analyze_text_with_llm(article["text"])

                # 2. Store in Memory (RAG)
                self.memory.store_thought(
                    agent_id="research_v1",  # Use agent ID from profile
                    text=f"Source: {url}\nContent: {article['text'][:1000]}",  # Store first 1k chars
                    metadata={
                        "type": "news_scrape",
                        "url": url,
                        "sentiment": analysis["sentiment"],
                        "impact": analysis["impact"],
                    },
                )

                # 3. Publish Signal if High Impact (Hot Path)
                if analysis["impact"] >= 7:
                    await self.publish_signal(analysis)

            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")

    async def fetch_and_parse(self, url: str) -> dict[str, str] | None:
        """Fetch URL and extract readable text."""
        try:
            # Fake User Agent is often needed
            headers = {"User-Agent": "Mozilla/5.0 AgenticTrader/1.0"}
            response = await self.client.get(url, headers=headers)

            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch {url}: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Simple heuristic: Get all paragraph text
            # In production: Use specific selectors per domain
            paragraphs = soup.find_all("p")
            text_content = "\n".join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])

            if not text_content:
                return None

            return {
                "url": url,
                "title": soup.title.string if soup.title else "No Title",
                "text": text_content,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Scrape error: {e}")
            return None

    async def publish_signal(self, analysis: dict[str, Any]):
        """Publish high-impact news to Kafka."""
        msg = AgentMessage(
            source="research_v1",  # Use agent ID from profile
            target="orchestrator_v1",  # Direct to orchestrator for now
            type="NEWS_DATA",  # Veranderd naar DATA type
            payload={
                "signal": "NEWS_EVENT",
                "sentiment": analysis["sentiment"],
                "impact": analysis["impact"],
                "summary": analysis["summary"],
            },
        )
        self.logger.info(f"🚨 NEWS SIGNAL: {analysis['summary']} (Sent: {analysis['sentiment']})")

        if self.message_bus:
            if asyncio.iscoroutinefunction(self.message_bus):
                return await self.message_bus(msg)
            else:
                return self.message_bus(msg)


async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Research Agent Service...")

    # Initialize dependencies
    try:
        # In a real system, the orchestrator would create and manage agents
        memory = MemoryAgent()
        agent = ResearchAgent(memory_agent=memory)

        while True:
            await agent.run_cycle()
            # Wait 5 minutes between cycles
            await asyncio.sleep(300)

    except Exception as e:
        logging.error(f"Service crashed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
