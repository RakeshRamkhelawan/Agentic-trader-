"""
LLM Gateway - Intelligent Routing for Multi-Provider LLM Access

Routes requests to optimal LLM provider based on:
- Latency requirements (fast path vs slow path)
- Model capabilities needed
- Cost optimization
- Fallback handling

Providers:
- Ollama (local, GPU-accelerated) - for non-latency-sensitive tasks
- DeepSeek API (cloud) - for complex analysis
- OpenAI/Ollama mix - for balance
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import aiohttp

from backend.core.config.settings import settings

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers."""

    OLLAMA_LOCAL = "ollama_local"  # Fast, free, GPU-accelerated
    DEEPSEEK_API = "deepseek_api"  # Cloud, complex reasoning
    OPENAI_API = "openai_api"  # Cloud, general purpose


class LatencyRequirement(Enum):
    """Latency requirements for routing decisions."""

    REALTIME = "realtime"  # < 100ms - hot path trading
    FAST = "fast"  # < 500ms - UI interactions
    STANDARD = "standard"  # < 2000ms - sentiment analysis
    BATCH = "batch"  # > 2000ms - research, reports


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    content: str
    provider: LLMProvider
    latency_ms: float
    tokens_used: int | None = None
    model: str | None = None
    cached: bool = False


@dataclass
class LLMRequest:
    """LLM request configuration."""

    prompt: str
    latency_requirement: LatencyRequirement
    model_preference: str | None = None
    max_tokens: int = 500
    temperature: float = 0.3
    system_prompt: str | None = None
    json_mode: bool = False


class LLMGateway:
    """
    Intelligent LLM Gateway with provider routing.

    Fast Path (API): Real-time trading decisions, risk checks
    Slow Path (Ollama): Sentiment, research, analysis, summaries
    """

    # Provider latency characteristics (typical)
    LATENCY_PROFILES = {
        LLMProvider.OLLAMA_LOCAL: {
            LatencyRequirement.REALTIME: 50,  # GPU inference
            LatencyRequirement.FAST: 100,
            LatencyRequirement.STANDARD: 500,
            LatencyRequirement.BATCH: 2000,
        },
        LLMProvider.DEEPSEEK_API: {
            LatencyRequirement.REALTIME: 200,  # Network + API
            LatencyRequirement.FAST: 500,
            LatencyRequirement.STANDARD: 1500,
            LatencyRequirement.BATCH: 5000,
        },
        LLMProvider.OPENAI_API: {
            LatencyRequirement.REALTIME: 150,
            LatencyRequirement.FAST: 300,
            LatencyRequirement.STANDARD: 1000,
            LatencyRequirement.BATCH: 3000,
        },
    }

    def __init__(
        self,
        ollama_url: str = "http://ollama:11434",
        deepseek_api_key: str | None = None,
        openai_api_key: str | None = None,
        enable_gpu: bool = True,
    ):
        self.ollama_url = ollama_url
        self.deepseek_api_key = deepseek_api_key or settings.LLM_API_KEY
        self.openai_api_key = openai_api_key
        self.enable_gpu = enable_gpu

        # Provider health status
        self._provider_health: dict[LLMProvider, bool] = {
            LLMProvider.OLLAMA_LOCAL: False,
            LLMProvider.DEEPSEEK_API: False,
            LLMProvider.OPENAI_API: False,
        }

        # Performance metrics
        self._latency_stats: dict[LLMProvider, list[float]] = {p: [] for p in LLMProvider}

        # Default models per provider
        self._default_models = {
            LLMProvider.OLLAMA_LOCAL: "deepseek-r1:7b",
            LLMProvider.DEEPSEEK_API: "deepseek-chat",
            LLMProvider.OPENAI_API: "gpt-4o-mini",
        }

        # Ollama-specific model assignments by task (RTX 4090 8GB optimized)
        self._ollama_models = {
            "sentiment": "deepseek-r1:7b",  # 4.7GB - Fast sentiment
            "analysis": "deepseek-r1:7b",  # 4.7GB - Fits in 8GB VRAM
            "summarization": "phi3:mini",  # 2.2GB - Fast summarization
            "coding": "deepseek-r1:7b",  # 4.7GB - Code tasks
            "chat": "phi3:mini",  # 2.2GB - General chat
        }

    async def initialize(self):
        """Check provider availability."""
        await self._check_ollama_health()
        await self._check_api_health()

    async def _check_ollama_health(self):
        """Check if Ollama is running and GPU is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m["name"] for m in data.get("models", [])]
                        logger.info(f"✅ Ollama healthy. Models: {models}")

                        # Check GPU availability
                        gpu_info = await self._get_gpu_info()
                        if gpu_info:
                            logger.info(f"🎮 GPU detected: {gpu_info}")
                        else:
                            logger.warning("⚠️ No GPU detected, using CPU")

                        self._provider_health[LLMProvider.OLLAMA_LOCAL] = True
                    else:
                        logger.warning(f"⚠️ Ollama unhealthy: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {e}")

    async def _check_api_health(self):
        """Check cloud API availability."""
        # Check DeepSeek
        if self.deepseek_api_key:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.deepseek_api_key}"},
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": "hi"}],
                            "max_tokens": 5,
                        },
                        timeout=5,
                    ) as resp:
                        self._provider_health[LLMProvider.DEEPSEEK_API] = resp.status == 200
                        logger.info(
                            f"✅ DeepSeek API: {'healthy' if resp.status == 200 else 'unhealthy'}"
                        )
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek API unavailable: {e}")

        # Check OpenAI
        if self.openai_api_key:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"},
                        timeout=5,
                    ) as resp:
                        self._provider_health[LLMProvider.OPENAI_API] = resp.status == 200
                        logger.info(
                            f"✅ OpenAI API: {'healthy' if resp.status == 200 else 'unhealthy'}"
                        )
            except Exception as e:
                logger.warning(f"⚠️ OpenAI API unavailable: {e}")

    async def _get_gpu_info(self) -> str | None:
        """Get GPU information from Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/ps", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Ollama ps shows running models with GPU usage
                        return f"Models loaded: {len(data.get('models', []))}"
        except:
            pass
        return None

    def select_provider(
        self, requirement: LatencyRequirement, force_provider: LLMProvider | None = None
    ) -> LLMProvider:
        """
        Select optimal provider based on latency requirement.

        Strategy:
        - REALTIME: Ollama (if available) else API
        - FAST: Ollama preferred (GPU fast enough)
        - STANDARD: Ollama (batchable, free)
        - BATCH: Ollama (cost-free for large jobs)
        """
        if force_provider:
            return force_provider

        # Prefer Ollama for non-realtime tasks (free, no rate limits)
        if requirement in [LatencyRequirement.STANDARD, LatencyRequirement.BATCH]:
            if self._provider_health[LLMProvider.OLLAMA_LOCAL]:
                return LLMProvider.OLLAMA_LOCAL

        # For fast requirements, use fastest available
        if requirement == LatencyRequirement.FAST:
            if self._provider_health[LLMProvider.OLLAMA_LOCAL]:
                return LLMProvider.OLLAMA_LOCAL
            if self._provider_health[LLMProvider.OPENAI_API]:
                return LLMProvider.OPENAI_API

        # For realtime, use API (more consistent latency)
        if requirement == LatencyRequirement.REALTIME:
            if self._provider_health[LLMProvider.OPENAI_API]:
                return LLMProvider.OPENAI_API
            if self._provider_health[LLMProvider.DEEPSEEK_API]:
                return LLMProvider.DEEPSEEK_API

        # Fallback to any available
        for provider in LLMProvider:
            if self._provider_health[provider]:
                return provider

        raise Exception("No LLM providers available")

    async def generate(
        self, request: LLMRequest, force_provider: LLMProvider | None = None
    ) -> LLMResponse:
        """
        Generate completion with optimal provider selection.
        """
        provider = self.select_provider(request.latency_requirement, force_provider)
        start_time = time.time()

        try:
            if provider == LLMProvider.OLLAMA_LOCAL:
                response = await self._generate_ollama(request)
            elif provider == LLMProvider.DEEPSEEK_API:
                response = await self._generate_deepseek(request)
            elif provider == LLMProvider.OPENAI_API:
                response = await self._generate_openai(request)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            latency = (time.time() - start_time) * 1000
            self._latency_stats[provider].append(latency)

            return LLMResponse(
                content=response,
                provider=provider,
                latency_ms=latency,
                model=self._default_models[provider],
            )

        except Exception as e:
            logger.error(f"Provider {provider.value} failed: {e}")
            # Try fallback provider
            return await self._fallback_generate(request, provider)

    async def _fallback_generate(
        self, request: LLMRequest, failed_provider: LLMProvider
    ) -> LLMResponse:
        """Fallback to next available provider."""
        for provider in LLMProvider:
            if provider != failed_provider and self._provider_health[provider]:
                logger.info(f"Falling back to {provider.value}")
                return await self.generate(request, force_provider=provider)
        raise Exception("All providers failed")

    async def _generate_ollama(self, request: LLMRequest) -> str:
        """Generate using local Ollama (GPU accelerated)."""
        # Select model based on task type hint
        model = self._select_ollama_model(request)

        payload = {
            "model": model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        if request.system_prompt:
            payload["system"] = request.system_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=300 if request.latency_requirement == LatencyRequirement.BATCH else 60,
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Ollama error: {resp.status}")
                data = await resp.json()
                return data.get("response", "")

    def _select_ollama_model(self, request: LLMRequest) -> str:
        """Select optimal Ollama model based on request characteristics."""
        prompt_lower = request.prompt.lower()

        # Task detection
        if any(w in prompt_lower for w in ["sentiment", "bullish", "bearish", "mood"]):
            return self._ollama_models.get("sentiment", "deepseek-r1:7b")
        elif any(w in prompt_lower for w in ["code", "function", "script", "programming"]):
            return self._ollama_models.get("coding", "codellama:7b")
        elif any(w in prompt_lower for w in ["summarize", "summary", "tl;dr", "brief"]):
            return self._ollama_models.get("summarization", "phi3:medium")
        elif len(request.prompt) > 2000:
            return self._ollama_models.get("analysis", "deepseek-r1:14b")
        else:
            return self._ollama_models.get("chat", "llama3.1:8b")

    async def _generate_deepseek(self, request: LLMRequest) -> str:
        """Generate using DeepSeek API."""
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": request.model_preference or "deepseek-chat",
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.deepseek_api_key}"},
                json=payload,
                timeout=60,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"DeepSeek error: {resp.status} - {text}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def _generate_openai(self, request: LLMRequest) -> str:
        """Generate using OpenAI API."""
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": request.model_preference or "gpt-4o-mini",
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_api_key}"},
                json=payload,
                timeout=60,
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"OpenAI error: {resp.status}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    def get_stats(self) -> dict[str, Any]:
        """Get gateway performance statistics."""
        stats = {}
        for provider, latencies in self._latency_stats.items():
            if latencies:
                stats[provider.value] = {
                    "avg_latency_ms": sum(latencies) / len(latencies),
                    "min_latency_ms": min(latencies),
                    "max_latency_ms": max(latencies),
                    "calls": len(latencies),
                    "healthy": self._provider_health[provider],
                }
        return stats

    async def batch_generate(
        self, requests: list[LLMRequest], max_concurrency: int = 4
    ) -> list[LLMResponse]:
        """
        Batch process multiple requests (ideal for Ollama GPU batching).
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def bounded_generate(req: LLMRequest) -> LLMResponse:
            async with semaphore:
                return await self.generate(req)

        tasks = [bounded_generate(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)


# Singleton instance
_llm_gateway: LLMGateway | None = None


async def get_llm_gateway() -> LLMGateway:
    """Get or initialize LLM Gateway singleton."""
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = LLMGateway()
        await _llm_gateway.initialize()
    return _llm_gateway
