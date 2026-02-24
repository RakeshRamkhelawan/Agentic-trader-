"""
Tests for LLM Provider Factory.

TDD Test Suite - Write tests FIRST before implementation.
"""

from unittest.mock import patch

import pytest

from backend.llm.provider_interface import LLMProvider

pytestmark = pytest.mark.unit


def test_factory_function_exists():
    """RED: create_llm_provider function should exist."""
    from backend.llm.factory import create_llm_provider

    assert create_llm_provider is not None
    assert callable(create_llm_provider)


def test_factory_creates_gemini_provider():
    """RED: Factory should create GeminiProvider when type is 'gemini'."""
    from backend.llm.factory import create_llm_provider
    from backend.llm.providers.gemini import GeminiProvider

    with patch("google.genai.Client"):
        provider = create_llm_provider(provider_type="gemini", api_key="test-key")
        assert isinstance(provider, GeminiProvider)


def test_factory_creates_ollama_provider():
    """RED: Factory should create OllamaProvider when type is 'ollama'."""
    from backend.llm.factory import create_llm_provider
    from backend.llm.providers.ollama import OllamaProvider

    provider = create_llm_provider(provider_type="ollama")
    assert isinstance(provider, OllamaProvider)


def test_factory_returns_llm_provider_interface():
    """RED: Factory should return LLMProvider interface."""
    from backend.llm.factory import create_llm_provider

    with patch("google.genai.Client"):
        provider = create_llm_provider(provider_type="gemini", api_key="key")
        assert isinstance(provider, LLMProvider)


def test_factory_reads_from_env():
    """RED: Factory should read LLM_PROVIDER from environment."""
    from backend.llm.factory import create_llm_provider

    with patch.dict("os.environ", {"LLM_PROVIDER": "ollama"}):
        provider = create_llm_provider()
        from backend.llm.providers.ollama import OllamaProvider

        assert isinstance(provider, OllamaProvider)


def test_factory_env_gemini_requires_api_key():
    """RED: Factory with gemini should use GOOGLE_API_KEY from env."""
    from backend.llm.factory import create_llm_provider

    with patch.dict("os.environ", {"LLM_PROVIDER": "gemini", "GOOGLE_API_KEY": "env-key"}):
        with patch("google.genai.Client"):
            provider = create_llm_provider()
            from backend.llm.providers.gemini import GeminiProvider

            assert isinstance(provider, GeminiProvider)
            assert provider.api_key == "env-key"


def test_factory_passes_model_name():
    """RED: Factory should pass model_name to provider."""
    from backend.llm.factory import create_llm_provider

    provider = create_llm_provider(provider_type="ollama", model_name="llama3")
    assert provider.model_name == "llama3"


def test_factory_passes_base_url_to_ollama():
    """RED: Factory should pass base_url to OllamaProvider."""
    from backend.llm.factory import create_llm_provider

    provider = create_llm_provider(provider_type="ollama", base_url="http://custom:8080")
    assert provider.base_url == "http://custom:8080"


def test_factory_invalid_provider_type():
    """RED: Factory should raise error for invalid provider type."""
    from backend.llm.factory import create_llm_provider

    with pytest.raises(ValueError, match="Unknown provider type"):
        create_llm_provider(provider_type="invalid")


def test_factory_default_to_ollama():
    """RED: Factory should default to ollama if no env set."""
    from backend.llm.factory import create_llm_provider

    with patch.dict("os.environ", {}, clear=True):
        provider = create_llm_provider()
        from backend.llm.providers.ollama import OllamaProvider

        assert isinstance(provider, OllamaProvider)


def test_factory_case_insensitive():
    """RED: Factory should handle case-insensitive provider types."""
    from backend.llm.factory import create_llm_provider

    with patch("google.genai.Client"):
        provider1 = create_llm_provider(provider_type="GEMINI", api_key="key")
        provider2 = create_llm_provider(provider_type="Gemini", api_key="key")

        from backend.llm.providers.gemini import GeminiProvider

        assert isinstance(provider1, GeminiProvider)
        assert isinstance(provider2, GeminiProvider)


def test_factory_with_kwargs():
    """RED: Factory should pass additional kwargs to provider."""
    from backend.llm.factory import create_llm_provider

    with patch("google.genai.Client"):
        provider = create_llm_provider(
            provider_type="gemini", api_key="test", model_name="gemini-2.0-flash"
        )
        assert provider.model_name == "gemini-2.0-flash"
