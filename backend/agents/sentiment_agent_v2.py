"""
Sentiment Agent V2 - Optimized for GPU-accelerated Ollama
Uses LLM Gateway for intelligent routing.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.core.agent_router import AgentRouter
from backend.core.memory_agent import MemoryAgent
from backend.llm.gateway import LatencyRequirement, LLMGateway, LLMRequest
from backend.schemas.agent_messages import AgentMessage

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    score: float  # 0.0 to 1.0
    trend: str  # bullish, bearish, neutral
    confidence: float
    rationale: str
    key_factors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_used: str = "unknown"
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "trend": self.trend,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "key_factors": self.key_factors,
            "timestamp": self.timestamp.isoformat(),
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
        }


class SentimentAgentV2:
    """
    Optimized Sentiment Agent using LLM Gateway.
    
    Characteristics:
    - STANDARD_PATH (uses Ollama GPU)
    - Batch processing support
    - Caching for repeated queries
    """
    
    def __init__(
        self,
        memory_agent: Optional[MemoryAgent] = None,
        message_bus=None,
        llm_gateway: Optional[LLMGateway] = None,
        enable_cache: bool = True,
    ):
        self.memory = memory_agent or MemoryAgent()
        self.message_bus = message_bus
        self.llm_gateway = llm_gateway
        self.router: Optional[AgentRouter] = None
        
        self.name = "SentimentAgentV2"
        self.prana = 50.0
        self.is_active = True
        
        # Simple LRU cache
        self._cache: Dict[str, SentimentResult] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self.enable_cache = enable_cache
        
        # Batch processing queue
        self._batch_queue: List[Dict] = []
        self._batch_timer: Optional[asyncio.Task] = None
        self._batch_interval = 5.0  # Process batch every 5s
        
    async def initialize(self):
        """Initialize with LLM Gateway and Router."""
        if self.llm_gateway is None:
            from backend.llm.gateway import get_llm_gateway
            self.llm_gateway = await get_llm_gateway()
            
        self.router = AgentRouter(self.llm_gateway)
        
        # Start batch processor
        self._batch_timer = asyncio.create_task(self._batch_processor())
        
        logger.info("✅ SentimentAgentV2 initialized with GPU acceleration")
        
    async def analyze_news(
        self,
        headlines: List[str],
        coin: str = "BTC",
        use_cache: bool = True
    ) -> SentimentResult:
        """
        Analyze sentiment of news headlines.
        Uses Ollama GPU for fast local inference.
        """
        if not headlines:
            return SentimentResult(
                score=0.5, trend="neutral", confidence=0.0,
                rationale="No headlines provided"
            )
            
        # Check cache
        cache_key = self._make_cache_key(headlines, coin)
        if use_cache and self.enable_cache and cache_key in self._cache:
            self._cache_hits += 1
            cached = self._cache[cache_key]
            logger.debug(f"Cache hit for {coin}")
            return cached
            
        self._cache_misses += 1
        
        # Prepare prompt
        headlines_text = "\n".join([f"- {h}" for h in headlines[:20]])
        
        system_prompt = """You are a crypto trading sentiment analyst. 
Analyze news headlines and provide sentiment scores.
Be objective and base your analysis only on the provided text."""

        user_prompt = f"""Analyze the sentiment for {coin} based on these headlines:

{headlines_text}

Respond in JSON format:
{{
    "score": 0.75,
    "trend": "bullish",
    "confidence": 0.85,
    "rationale": "Brief explanation",
    "key_factors": ["Factor 1", "Factor 2"]
}}

Score: 0.0-0.4 bearish, 0.4-0.6 neutral, 0.6-1.0 bullish"""

        start_time = asyncio.get_event_loop().time()
        
        try:
            # Ensure router is initialized
            if self.router is None:
                raise RuntimeError("SentimentAgentV2 router is not initialized. Call 'await initialize()' before using this method.")
            # Route through AgentRouter (uses Ollama GPU)
            response_text = await self.router.route_request(  # type: ignore[union-attr]
                agent_id="sentiment_v1",
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500,
                json_mode=True,
            )

            latency = (asyncio.get_event_loop().time() - start_time) * 1000

            # Parse response
            result = self._parse_response(response_text)
            result.latency_ms = latency
            import os
            gpu_model = os.environ.get("SENTIMENT_AGENT_GPU_MODEL", "Unknown GPU")
            result.model_used = f"ollama/deepseek-r1:7b (GPU - {gpu_model})"

            # Cache result
            if self.enable_cache:
                self._cache[cache_key] = result

            logger.info(
                f"Sentiment for {coin}: {result.trend} "
                f"({result.score:.2f}) in {latency:.0f}ms [GPU]"
            )

            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._fallback_analysis(headlines, coin)
            
    def _make_cache_key(self, headlines: List[str], coin: str) -> str:
        """Create cache key from headlines."""
        import hashlib
        content = coin + "".join(sorted(headlines))
        return hashlib.md5(content.encode()).hexdigest()[:16]
        
    def _parse_response(self, text: str) -> SentimentResult:
        """Parse JSON response from LLM."""
        try:
            # Extract JSON
            import re
            json_match = re.search(r'\{[^}]*"score"[^}]*"trend"[^}]*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(text)
                
            return SentimentResult(
                score=float(data.get("score", 0.5)),
                trend=data.get("trend", "neutral"),
                confidence=float(data.get("confidence", 0.5)),
                rationale=data.get("rationale", ""),
                key_factors=data.get("key_factors", []),
            )
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return self._regex_extract(text)
            
    def _regex_extract(self, text: str) -> SentimentResult:
        """Fallback regex extraction."""
        text_lower = text.lower()
        
        if "bullish" in text_lower:
            trend, score = "bullish", 0.7
        elif "bearish" in text_lower:
            trend, score = "bearish", 0.3
        else:
            trend, score = "neutral", 0.5
            
        return SentimentResult(
            score=score, trend=trend, confidence=0.5,
            rationale=text[:200], key_factors=[]
        )
        
    def _fallback_analysis(self, headlines: List[str], coin: str) -> SentimentResult:
        """Rule-based fallback."""
        all_text = " ".join(headlines).lower()
        
        positive = ["surge", "rally", "bull", "breakout", "adoption", "pump", "gain"]
        negative = ["crash", "dump", "bear", "decline", "hack", "ban", "loss"]
        
        pos_count = sum(1 for w in positive if w in all_text)
        neg_count = sum(1 for w in negative if w in all_text)
        
        total = pos_count + neg_count
        if total == 0:
            score, trend = 0.5, "neutral"
        else:
            score = pos_count / total
            trend = "bullish" if score > 0.6 else "bearish" if score < 0.4 else "neutral"
            
        return SentimentResult(
            score=score, trend=trend, confidence=0.3,
            rationale="Rule-based fallback", key_factors=[],
            model_used="rule-based (fallback)"
        )
        
    async def analyze_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[SentimentResult]:
        """
        Batch analyze multiple items (GPU optimized).
        """
        prompts = []
        for item in items:
            headlines = item.get("headlines", [])
            coin = item.get("coin", "BTC")
            headlines_text = "\n".join([f"- {h}" for h in headlines[:15]])
            
            prompt = f"Analyze {coin} sentiment:\n{headlines_text}"
            prompts.append(prompt)
            
        # Ensure router is initialized
        if self.router is None:
            raise RuntimeError("SentimentAgentV2 router is not initialized. Call 'await initialize()' before using this method.")
        # Route batch through router
        results = await self.router.route_batch(  # type: ignore[union-attr]
            agent_id="sentiment_v1",
            prompts=prompts,
        )
        
        sentiments = []
        import os
        gpu_model = os.environ.get("SENTIMENT_AGENT_GPU_MODEL", "Unknown GPU")
        for text in results:
            try:
                result = self._parse_response(text)
                result.model_used = f"ollama/deepseek-r1:7b (GPU batch - {gpu_model})"
                sentiments.append(result)
            except:
                sentiments.append(self._fallback_analysis([], "UNKNOWN"))
                
        return sentiments
        
    async def _batch_processor(self):
        """Background batch processor."""
        while self.is_active:
            await asyncio.sleep(self._batch_interval)
            
            if self._batch_queue:
                batch = self._batch_queue[:10]  # Process max 10
                self._batch_queue = self._batch_queue[10:]
                
                try:
                    results = await self.analyze_batch(batch)
                    # Broadcast results
                    for item, result in zip(batch, results):
                        if self.message_bus:
                            await self.message_bus(AgentMessage(
                                source=self.name,
                                target=item.get("source", "all"),
                                type="SENTIMENT_UPDATE",
                                payload={
                                    "coin": item.get("coin"),
                                    "result": result.to_dict(),
                                }
                            ))
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    
    def queue_analysis(self, headlines: List[str], coin: str, source: str = "all"):
        """Queue item for batch processing."""
        self._batch_queue.append({
            "headlines": headlines,
            "coin": coin,
            "source": source,
        })
        
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        if message.type == "ANALYZE_SENTIMENT":
            headlines = message.payload.get("headlines", [])
            coin = message.payload.get("coin", "BTC")
            
            # Use batch queue for non-urgent requests
            if message.payload.get("urgent", False):
                result = await self.analyze_news(headlines, coin)
            else:
                self.queue_analysis(headlines, coin, message.source)
                result = None  # Will be processed in batch
                
            if result and self.message_bus:
                await self.message_bus(AgentMessage(
                    source=self.name,
                    target=message.source or "all",
                    type="SENTIMENT_UPDATE",
                    payload={"coin": coin, "result": result.to_dict()}
                ))
                
        elif message.type == "NEWS_UPDATE":
            # Auto-analyze news
            news = message.payload.get("news", {})
            for coin, items in news.items():
                if isinstance(items, list):
                    headlines = [i.get("title", "") for i in items if isinstance(i, dict)]
                    if headlines:
                        self.queue_analysis(headlines, coin, "system")
                        
    async def start(self):
        """Start agent."""
        await self.initialize()
        logger.info(f"✅ {self.name} started with cache (hits: {self._cache_hits}, misses: {self._cache_misses})")
        
    async def stop(self):
        """Stop agent."""
        self.is_active = False
        if self._batch_timer:
            self._batch_timer.cancel()
        logger.info(f"🛑 {self.name} stopped")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": f"{hit_rate:.1%}",
            "queue_size": len(self._batch_queue),
            "gateway_stats": self.llm_gateway.get_stats() if self.llm_gateway else {},
        }
