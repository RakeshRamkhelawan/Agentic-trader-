"""
Multi-LLM Provider - DeepSeek, OpenAI, Google GenAI

Ondersteunt meerdere LLM providers voor reflections:
- DeepSeek (primary)
- OpenAI (fallback 1)
- Google GenAI (fallback 2)
- Ollama (local fallback)
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# Load environment variables
from dotenv import load_dotenv

from backend.core.llm.llm_provider import LLMBackend, create_llm_provider

load_dotenv(".env")

logger = logging.getLogger(__name__)


class LLMProviderType(Enum):
    """Supported LLM providers."""

    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class LLMResponse:
    """Unified LLM response."""

    text: str
    provider: str
    model: str
    latency_ms: float
    tokens_used: Optional[int] = None


class MultiLLMProvider:
    """
    Multi-provider LLM client with failover.
    Priority: DeepSeek > OpenAI > Google > Ollama
    """

    def __init__(self):
        self.providers: Dict[LLMProviderType, Any] = {}
        self.current_provider: Optional[LLMProviderType] = None
        self._init_providers()

    def _init_providers(self):
        """Initialize alle beschikbare providers."""
        # DeepSeek (primary)
        if os.getenv("DEEPSEEK_API_KEY"):
            try:
                self.providers[LLMProviderType.DEEPSEEK] = create_llm_provider(
                    backend=LLMBackend.DEEPSEEK,
                    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                )
                logger.info("[MultiLLM] DeepSeek initialized")
            except Exception as e:
                logger.warning(f"[MultiLLM] DeepSeek init failed: {e}")

        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.providers[LLMProviderType.OPENAI] = create_llm_provider(
                    backend=LLMBackend.OPENAI,
                    model="gpt-4o-mini",
                    api_key=os.getenv("OPENAI_API_KEY"),
                )
                logger.info("[MultiLLM] OpenAI initialized")
            except Exception as e:
                logger.warning(f"[MultiLLM] OpenAI init failed: {e}")

        # Ollama (local fallback)
        try:
            self.providers[LLMProviderType.OLLAMA] = create_llm_provider(
                backend=LLMBackend.OLLAMA, model="llama3.2"
            )
            logger.info("[MultiLLM] Ollama initialized")
        except Exception as e:
            logger.warning(f"[MultiLLM] Ollama init failed: {e}")

        # Set primary
        for provider in [LLMProviderType.DEEPSEEK, LLMProviderType.OPENAI, LLMProviderType.OLLAMA]:
            if provider in self.providers:
                self.current_provider = provider
                logger.info(f"[MultiLLM] Primary LLM: {provider.value}")
                break

    def generate(
        self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_retries: int = 3
    ) -> LLMResponse:
        """
        Generate with automatic failover.
        """
        providers_to_try: List[LLMProviderType] = list(self.providers.keys())

        # Move current provider to front
        if self.current_provider and self.current_provider in providers_to_try:
            providers_to_try.remove(self.current_provider)
            providers_to_try.insert(0, self.current_provider)

        last_error = None

        for provider in providers_to_try:
            try:
                llm = self.providers[provider]

                import time

                start = time.time()

                response = llm.generate(
                    prompt=prompt, system_prompt=system_prompt, temperature=temperature
                )

                latency = (time.time() - start) * 1000

                # Update current provider on success
                self.current_provider = provider

                return LLMResponse(
                    text=response.get("text", str(response)),
                    provider=provider.value,
                    model=self._get_model_name(provider),
                    latency_ms=latency,
                )

            except Exception as e:
                logger.warning(f"{provider.value} failed: {e}")
                last_error = e
                continue

        # All failed
        logger.error(f"All LLM providers failed: {last_error}")
        raise last_error

    def _get_model_name(self, provider: LLMProviderType) -> str:
        """Get model name for provider."""
        models = {
            LLMProviderType.DEEPSEEK: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            LLMProviderType.OPENAI: "gpt-4o-mini",
            LLMProviderType.OLLAMA: "llama3.2",
        }
        return models.get(provider, "unknown")


# Singleton
_multi_llm = None


def get_multi_llm() -> MultiLLMProvider:
    """Get singleton multi-LLM provider."""
    global _multi_llm
    if _multi_llm is None:
        _multi_llm = MultiLLMProvider()
    return _multi_llm
