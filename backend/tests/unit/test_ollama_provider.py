"""
Tests for Ollama LLM Provider (Local).

TDD Test Suite - Write tests FIRST before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel
from backend.llm.provider_interface import LLMProvider


pytestmark = pytest.mark.unit


class SentimentOutput(BaseModel):
    """Test schema for structured output."""
    sentiment: str
    score: float


def test_ollama_provider_exists():
    """RED: OllamaProvider class should exist."""
    from backend.llm.providers.ollama import OllamaProvider
    assert OllamaProvider is not None


def test_ollama_inherits_llm_provider():
    """RED: OllamaProvider should inherit from LLMProvider."""
    from backend.llm.providers.ollama import OllamaProvider
    assert issubclass(OllamaProvider, LLMProvider)


def test_ollama_provider_init_with_base_url():
    """RED: OllamaProvider should accept base_url in __init__."""
    from backend.llm.providers.ollama import OllamaProvider
    provider = OllamaProvider(base_url="http://localhost:11434")
    assert provider.base_url == "http://localhost:11434"


def test_ollama_provider_default_base_url():
    """RED: OllamaProvider should have default base_url."""
    from backend.llm.providers.ollama import OllamaProvider
    provider = OllamaProvider()
    assert provider.base_url == "http://localhost:11434"


def test_ollama_provider_init_with_model_name():
    """RED: OllamaProvider should accept model_name."""
    from backend.llm.providers.ollama import OllamaProvider
    provider = OllamaProvider(model_name="llama2")
    assert provider.model_name == "llama2"


def test_ollama_provider_default_model():
    """RED: OllamaProvider should have default model."""
    from backend.llm.providers.ollama import OllamaProvider
    provider = OllamaProvider()
    assert hasattr(provider, 'model_name')
    assert provider.model_name  # Not empty


@pytest.mark.asyncio
async def test_ollama_generate_text_returns_string():
    """GREEN: generate_text returns string."""
    from backend.llm.providers.ollama import OllamaProvider
    
    with patch('httpx.AsyncClient') as MockClient:
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Ollama generated text'}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider()
        result = await provider.generate_text("What is AI?")
        
        assert isinstance(result, str)
        assert result == "Ollama generated text"


@pytest.mark.asyncio
async def test_ollama_generate_text_with_system_prompt():
    """GREEN: generate_text supports system_prompt."""
    from backend.llm.providers.ollama import OllamaProvider
    
    with patch('httpx.AsyncClient') as MockClient:
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Response with context'}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider()
        result = await provider.generate_text("Tell me", system_prompt="Be concise")
        
        assert isinstance(result, str)
        # Verify system prompt was included in request
        call_kwargs = mock_client.post.call_args[1]
        assert 'json' in call_kwargs
        assert call_kwargs['json'].get('system') == 'Be concise'


@pytest.mark.asyncio
async def test_ollama_generate_structured_returns_pydantic():
    """GREEN: generate_structured returns Pydantic model instance."""
    from backend.llm.providers.ollama import OllamaProvider
    
    with patch('httpx.AsyncClient') as MockClient:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': '{"sentiment": "positive", "score": 0.9}'
        }
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider()
        result = await provider.generate_structured("Analyze sentiment", SentimentOutput)
        
        assert isinstance(result, SentimentOutput)
        assert result.sentiment == "positive"
        assert result.score == 0.9


@pytest.mark.asyncio
async def test_ollama_generate_structured_handles_json_parsing():
    """GREEN: generate_structured parses JSON from response."""
    from backend.llm.providers.ollama import OllamaProvider
    
    with patch('httpx.AsyncClient') as MockClient:
        # Ollama might return JSON in markdown blocks
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': '''```json
{"sentiment": "negative", "score": 0.3}
```'''
        }
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider()
        result = await provider.generate_structured("Check mood", SentimentOutput)
        
        assert isinstance(result, SentimentOutput)
        assert result.sentiment == "negative"
        assert result.score == 0.3


@pytest.mark.asyncio
async def test_ollama_request_format():
    """GREEN: Should send correct request format to Ollama API."""
    from backend.llm.providers.ollama import OllamaProvider
    
    with patch('httpx.AsyncClient') as MockClient:
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'test'}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider(model_name="llama2")
        await provider.generate_text("test prompt")
        
        # Verify request was made to correct endpoint
        call_args = mock_client.post.call_args
        assert "http://localhost:11434/api/generate" in call_args[0][0]
        
        # Verify request body contains model and prompt
        request_body = call_args[1]['json']
        assert request_body['model'] == 'llama2'
        assert 'prompt' in request_body


@pytest.mark.asyncio
async def test_ollama_handles_connection_error():
    """GREEN: Should handle connection errors gracefully."""
    from backend.llm.providers.ollama import OllamaProvider
    
    with patch('httpx.AsyncClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider()
        
        with pytest.raises(Exception) as exc_info:
            await provider.generate_text("test")
        
        assert "Connection refused" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ollama_handles_api_error_response():
    """GREEN: Should handle API error responses."""
    from backend.llm.providers.ollama import OllamaProvider
    import httpx
    
    with patch('httpx.AsyncClient') as MockClient:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=MagicMock(status_code=500)
        )
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider()
        
        with pytest.raises(httpx.HTTPStatusError):
            await provider.generate_text("test")


@pytest.mark.asyncio
async def test_ollama_with_custom_base_url():
    """GREEN: Should support custom base_url."""
    from backend.llm.providers.ollama import OllamaProvider
    
    with patch('httpx.AsyncClient') as MockClient:
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'test'}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client
        
        provider = OllamaProvider(base_url="http://remote:8080")
        await provider.generate_text("test")
        
        call_args = mock_client.post.call_args
        assert "http://remote:8080/api/generate" in call_args[0][0]
