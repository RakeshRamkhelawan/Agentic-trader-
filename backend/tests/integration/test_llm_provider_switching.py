"""
Integration Tests for LLM Provider Switching.

Tests factory pattern with environment-based provider switching.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from backend.agents.sentiment_agent import SentimentAgent
from backend.llm.factory import LLMFactory, create_llm_provider
from backend.llm.providers.gemini import GeminiProvider
from backend.llm.providers.ollama import OllamaProvider

pytestmark = pytest.mark.integration


class SampleSchema(BaseModel):
    """Sample schema for structured output testing."""

    result: str
    score: float


@pytest.mark.asyncio
async def test_factory_creates_gemini_provider():
    """Integration: Factory should create Gemini provider from config."""
    mock_client = MagicMock()
    mock_client.aclose = AsyncMock()

    with patch.dict(
        os.environ, {"LLM_PROVIDER": "gemini", "GOOGLE_API_KEY": "test_key"}
    ):
        with patch(
            "backend.llm.providers.gemini.genai.Client", return_value=mock_client
        ):
            provider = create_llm_provider()

            assert provider is not None
            assert isinstance(provider, GeminiProvider)


@pytest.mark.asyncio
async def test_factory_creates_ollama_provider():
    """Integration: Factory should create Ollama provider from config."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
        provider = create_llm_provider()

        assert provider is not None
        assert isinstance(provider, OllamaProvider)


@pytest.mark.asyncio
async def test_agent_works_with_gemini_provider():
    """Integration: SentimentAgent should work with Gemini provider."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
        # Mock the Gemini client
        with patch("backend.llm.providers.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aclose = AsyncMock()  # Prevent aclose warning
            mock_response = MagicMock()
            mock_response.text = '{"sentiment": "bullish", "confidence": 0.9, "reasoning": "Strong signals", "key_factors": ["momentum"]}'
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            provider = GeminiProvider(api_key="test_key")
            agent = SentimentAgent(agent_name="gemini_agent", llm_provider=provider)

            result = await agent.analyze({"price": 50000.0}, {"symbol": "BTC/USD"})

            assert result is not None
            assert "sentiment" in result or "action" in result


@pytest.mark.asyncio
async def test_agent_works_with_ollama_provider():
    """Integration: SentimentAgent should work with Ollama provider."""
    # Mock httpx async client
    with patch("backend.llm.providers.ollama.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "response": '{"sentiment": "bearish", "confidence": 0.7, "reasoning": "Weak indicators", "key_factors": ["volume"]}'
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = OllamaProvider()
        agent = SentimentAgent(agent_name="ollama_agent", llm_provider=provider)

        result = await agent.analyze({"price": 45000.0}, {"symbol": "BTC/USD"})

        assert result is not None
        assert "sentiment" in result or "action" in result


@pytest.mark.asyncio
async def test_factory_switches_providers_via_environment():
    """Integration: Factory should switch providers based on environment."""
    # Test Gemini
    with patch.dict(os.environ, {"LLM_PROVIDER": "GEMINI", "GOOGLE_API_KEY": "key1"}):
        with patch("backend.llm.providers.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client
            provider1 = create_llm_provider()
            assert isinstance(provider1, GeminiProvider)

    # Test Ollama
    with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
        with patch(
            "backend.llm.providers.ollama.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client
            provider2 = create_llm_provider()
            assert isinstance(provider2, OllamaProvider)

    # Test case-insensitive
    with patch.dict(os.environ, {"LLM_PROVIDER": "GeMiNi", "GOOGLE_API_KEY": "key2"}):
        with patch("backend.llm.providers.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client
            provider3 = create_llm_provider()
            assert isinstance(provider3, GeminiProvider)


@pytest.mark.asyncio
async def test_agent_analyzes_with_different_providers():
    """Integration: Agent should produce results with either provider."""
    features = {"price": 50000.0, "volume": 1.5}
    context = {"symbol": "BTC/USD"}

    # Test with Gemini (mocked)
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
        with patch("backend.llm.providers.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aclose = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = '{"sentiment": "bullish", "confidence": 0.85, "reasoning": "Test", "key_factors": []}'
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            gemini_provider = GeminiProvider(api_key="test_key")
            gemini_agent = SentimentAgent(
                agent_name="gemini_test", llm_provider=gemini_provider
            )
            gemini_result = await gemini_agent.analyze(features, context)

            assert gemini_result is not None

    # Test with Ollama (mocked)
    with patch("backend.llm.providers.ollama.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "response": '{"sentiment": "neutral", "confidence": 0.6, "reasoning": "Test", "key_factors": []}'
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        ollama_provider = OllamaProvider()
        ollama_agent = SentimentAgent(
            agent_name="ollama_test", llm_provider=ollama_provider
        )
        ollama_result = await ollama_agent.analyze(features, context)

        assert ollama_result is not None


@pytest.mark.asyncio
async def test_factory_defaults_to_ollama_if_unspecified():
    """Integration: Factory should default to Ollama if no provider specified."""
    # Remove LLM_PROVIDER if it exists
    env_copy = os.environ.copy()
    env_copy.pop("LLM_PROVIDER", None)

    with patch.dict(os.environ, env_copy):
        provider = create_llm_provider()
        assert isinstance(provider, OllamaProvider)


@pytest.mark.asyncio
async def test_factory_handles_invalid_provider_type():
    """Integration: Factory should raise error for invalid provider."""
    with pytest.raises(ValueError, match="Unknown provider type"):
        with patch.dict(os.environ, {"LLM_PROVIDER": "invalid_provider"}):
            create_llm_provider()


@pytest.mark.asyncio
async def test_provider_switching_maintains_agent_functionality():
    """Integration: Agent functionality should be consistent across providers."""
    features = {"price": 51000.0}
    context = {"symbol": "ETH/USD"}

    results = []

    # Test Gemini
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "key"}):
        with patch("backend.llm.providers.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aclose = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = '{"sentiment": "bullish", "confidence": 0.9, "reasoning": "Up", "key_factors": ["price"]}'
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            provider = GeminiProvider(api_key="key")
            agent = SentimentAgent(agent_name="test1", llm_provider=provider)
            result = await agent.analyze(features, context)
            results.append(result)

    # Test Ollama
    with patch("backend.llm.providers.ollama.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "response": '{"sentiment": "bearish", "confidence": 0.8, "reasoning": "Down", "key_factors": ["volume"]}'
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = OllamaProvider()
        agent = SentimentAgent(agent_name="test2", llm_provider=provider)
        result = await agent.analyze(features, context)
        results.append(result)

    # Both should produce valid results
    assert len(results) == 2
    assert all(r is not None for r in results)
    assert all("sentiment" in r or "action" in r for r in results)


@pytest.mark.asyncio
async def test_llm_factory_registry_extensibility():
    """Integration: Factory registry should allow custom provider registration."""

    class CustomProvider(GeminiProvider):
        """Custom test provider."""

        pass

    # Register custom provider
    LLMFactory.register_provider("custom", CustomProvider)

    with patch.dict(os.environ, {"LLM_PROVIDER": "custom", "GOOGLE_API_KEY": "test"}):
        with patch("backend.llm.providers.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            provider = create_llm_provider()
            assert isinstance(provider, CustomProvider)
