"""
Tests for LLM Provider Interface.

TDD Test Suite - Tests for the Abstract Base Class and concrete implementations.
"""

from abc import ABC

import pytest
from pydantic import BaseModel

from backend.llm.provider_interface import LLMProvider

pytestmark = pytest.mark.unit


class SentimentSchema(BaseModel):
    """Schema for structured generation tests."""
    sentiment: str
    confidence: float


def test_llm_provider_is_abstract():
    """RED: LLMProvider should be an Abstract Base Class."""
    assert issubclass(LLMProvider, ABC)


def test_llm_provider_has_generate_text():
    """RED: LLMProvider should have generate_text method."""
    assert hasattr(LLMProvider, 'generate_text')
    assert callable(getattr(LLMProvider, 'generate_text'))


def test_llm_provider_has_generate_structured():
    """RED: LLMProvider should have generate_structured method."""
    assert hasattr(LLMProvider, 'generate_structured')
    assert callable(getattr(LLMProvider, 'generate_structured'))


def test_llm_provider_cannot_be_instantiated():
    """RED: Cannot instantiate abstract LLMProvider directly."""
    with pytest.raises(TypeError):
        LLMProvider()


@pytest.mark.asyncio
async def test_concrete_provider_must_implement_generate_text():
    """RED: Concrete provider must implement generate_text."""
    
    class IncompleteProvider(LLMProvider):
        async def generate_structured(self, prompt, schema, system_prompt=None):
            return schema(sentiment="neutral", confidence=0.5)
    
    with pytest.raises(TypeError):
        IncompleteProvider()


@pytest.mark.asyncio
async def test_concrete_provider_must_implement_generate_structured():
    """RED: Concrete provider must implement generate_structured."""
    
    class IncompleteProvider(LLMProvider):
        async def generate_text(self, prompt, system_prompt=None):
            return "test response"
    
    with pytest.raises(TypeError):
        IncompleteProvider()


@pytest.mark.asyncio
async def test_valid_concrete_provider_can_be_instantiated():
    """GREEN: Valid provider implementing both methods should work."""
    
    class ValidProvider(LLMProvider):
        async def generate_text(self, prompt, system_prompt=None):
            return f"Response to: {prompt}"
        
        async def generate_structured(self, prompt, schema, system_prompt=None):
            # Return a valid instance of the schema
            if schema == SentimentSchema:
                return SentimentSchema(sentiment="positive", confidence=0.9)
            return schema()
    
    provider = ValidProvider()
    assert isinstance(provider, LLMProvider)
    
    # Test generate_text
    result = await provider.generate_text("test prompt")
    assert isinstance(result, str)
    assert "test prompt" in result
    
    # Test generate_structured
    structured = await provider.generate_structured("analyze", SentimentSchema)
    assert isinstance(structured, SentimentSchema)
    assert structured.sentiment == "positive"
    assert structured.confidence == 0.9


@pytest.mark.asyncio
async def test_provider_accepts_optional_system_prompt():
    """GREEN: Providers should accept optional system_prompt parameter."""
    
    class TestProvider(LLMProvider):
        async def generate_text(self, prompt, system_prompt=None):
            if system_prompt:
                return f"System: {system_prompt}. User: {prompt}"
            return prompt
        
        async def generate_structured(self, prompt, schema, system_prompt=None):
            return SentimentSchema(sentiment="neutral", confidence=0.5)
    
    provider = TestProvider()
    
    # Without system prompt
    result1 = await provider.generate_text("hello")
    assert result1 == "hello"
    
    # With system prompt
    result2 = await provider.generate_text("hello", system_prompt="Be helpful")
    assert "Be helpful" in result2
    assert "hello" in result2
