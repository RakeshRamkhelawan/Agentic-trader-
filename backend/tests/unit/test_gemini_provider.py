"""
Tests for Gemini LLM Provider.

TDD Test Suite - Write tests FIRST before implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from backend.llm.provider_interface import LLMProvider

pytestmark = pytest.mark.unit


class AnalysisResult(BaseModel):
    """Test schema for structured output."""
    conclusion: str
    confidence: float


def test_gemini_provider_exists():
    """GREEN: GeminiProvider class exists."""
    from backend.llm.providers.gemini import GeminiProvider
    assert GeminiProvider is not None


def test_gemini_inherits_llm_provider():
    """GREEN: GeminiProvider inherits from LLMProvider."""
    from backend.llm.providers.gemini import GeminiProvider
    assert issubclass(GeminiProvider, LLMProvider)


def test_gemini_provider_init_with_api_key():
    """GREEN: GeminiProvider accepts api_key in __init__."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client'):
        provider = GeminiProvider(api_key="test-key-123")
        assert provider.api_key == "test-key-123"


def test_gemini_provider_init_with_model_name():
    """GREEN: GeminiProvider accepts optional model_name."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client'):
        provider = GeminiProvider(api_key="key", model_name="gemini-1.5-pro")
        assert provider.model_name == "gemini-1.5-pro"


def test_gemini_provider_default_model():
    """GREEN: GeminiProvider has default model name."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client'):
        provider = GeminiProvider(api_key="key")
        assert hasattr(provider, 'model_name')
        assert provider.model_name  # Not empty


def test_gemini_provider_requires_api_key():
    """GREEN: GeminiProvider raises error without API key."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="Google API Key is missing"):
            GeminiProvider(api_key=None)


@pytest.mark.asyncio
async def test_gemini_generate_text_returns_string():
    """GREEN: generate_text returns string."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client') as MockClient:
        mock_response = MagicMock()
        mock_response.text = "Gemini response text"
        
        mock_client = MagicMock()
        mock_aio = MagicMock()
        mock_models = AsyncMock()
        mock_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio.models = mock_models
        mock_client.aio = mock_aio
        MockClient.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        result = await provider.generate_text("What is AI?")
        
        assert isinstance(result, str)
        assert result == "Gemini response text"


@pytest.mark.asyncio
async def test_gemini_generate_text_with_system_prompt():
    """GREEN: generate_text supports system_prompt."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client') as MockClient:
        mock_response = MagicMock()
        mock_response.text = "Response with system context"
        
        mock_client = MagicMock()
        mock_aio = MagicMock()
        mock_models = AsyncMock()
        mock_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio.models = mock_models
        mock_client.aio = mock_aio
        MockClient.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        result = await provider.generate_text("User prompt", system_prompt="Be concise")
        
        assert isinstance(result, str)
        assert result == "Response with system context"
        
        # Verify config was passed with system instruction
        call_kwargs = mock_models.generate_content.call_args[1]
        assert 'config' in call_kwargs
        assert call_kwargs['config'] is not None


@pytest.mark.asyncio
async def test_gemini_generate_structured_returns_pydantic():
    """GREEN: generate_structured returns Pydantic model instance."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client') as MockClient:
        mock_response = MagicMock()
        mock_response.text = '{"conclusion": "AI is powerful", "confidence": 0.95}'
        
        mock_client = MagicMock()
        mock_aio = MagicMock()
        mock_models = AsyncMock()
        mock_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio.models = mock_models
        mock_client.aio = mock_aio
        MockClient.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        result = await provider.generate_structured("Analyze AI", AnalysisResult)
        
        assert isinstance(result, AnalysisResult)
        assert result.conclusion == "AI is powerful"
        assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_gemini_generate_structured_handles_json_parsing():
    """GREEN: generate_structured parses JSON from response."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client') as MockClient:
        # Gemini might return JSON in markdown code blocks
        mock_response = MagicMock()
        mock_response.text = '''```json
{
    "conclusion": "Machine learning advances",
    "confidence": 0.88
}
```'''
        
        mock_client = MagicMock()
        mock_aio = MagicMock()
        mock_models = AsyncMock()
        mock_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio.models = mock_models
        mock_client.aio = mock_aio
        MockClient.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        result = await provider.generate_structured("Evaluate ML", AnalysisResult)
        
        assert isinstance(result, AnalysisResult)
        assert result.conclusion == "Machine learning advances"
        assert result.confidence == 0.88


def test_gemini_api_key_from_env():
    """GREEN: GeminiProvider can read API key from environment."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client'):
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'env-key-123'}):
            provider = GeminiProvider()
            assert provider.api_key == 'env-key-123'


@pytest.mark.asyncio
async def test_gemini_handles_api_error():
    """GREEN: Should handle Gemini API errors gracefully."""
    from backend.llm.providers.gemini import GeminiProvider
    
    with patch('google.genai.Client') as MockClient:
        mock_client = MagicMock()
        mock_aio = MagicMock()
        mock_models = AsyncMock()
        mock_models.generate_content = AsyncMock(side_effect=Exception("API Error"))
        mock_aio.models = mock_models
        mock_client.aio = mock_aio
        MockClient.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        
        with pytest.raises(Exception) as exc_info:
            await provider.generate_text("test prompt")
        
        assert "API Error" in str(exc_info.value)

