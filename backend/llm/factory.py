"""
LLM Factory for creating provider instances.

This factory enables easy switching between different LLM providers
based on environment configuration or explicit parameters.
"""
from typing import Optional, Dict, Any
import os

from backend.llm.provider_interface import LLMProvider
from backend.llm.providers.gemini import GeminiProvider
from backend.llm.providers.ollama import OllamaProvider


class LLMFactory:
    """Factory for creating LLM provider instances."""
    
    # Registry of available providers
    _PROVIDERS = {
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
    }
    
    # Default provider (local-first approach)
    _DEFAULT_PROVIDER = "ollama"
    
    @classmethod
    def create(
        cls,
        provider_type: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider ('gemini', 'ollama'). 
                          Reads from LLM_PROVIDER env var if not specified.
            **kwargs: Additional arguments passed to provider constructor.
        
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider_type is unknown
            
        Examples:
            >>> # Use environment variable
            >>> provider = LLMFactory.create()
            
            >>> # Explicit provider with custom config
            >>> provider = LLMFactory.create(
            ...     provider_type="gemini",
            ...     api_key="your-key",
            ...     model_name="gemini-2.0-flash-exp"
            ... )
            
            >>> # Local Ollama with custom model
            >>> provider = LLMFactory.create(
            ...     provider_type="ollama",
            ...     model_name="llama2"
            ... )
        """
        # Get provider type from argument or environment
        if provider_type is None:
            provider_type = os.getenv("LLM_PROVIDER", cls._DEFAULT_PROVIDER)
        
        # Normalize to lowercase for case-insensitive matching
        provider_type = provider_type.lower().strip()
        
        # Validate provider type
        if provider_type not in cls._PROVIDERS:
            available = ", ".join(cls._PROVIDERS.keys())
            raise ValueError(
                f"Unknown provider type: '{provider_type}'. "
                f"Available providers: {available}"
            )
        
        # Get provider class and instantiate
        provider_class = cls._PROVIDERS[provider_type]
        return provider_class(**kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get list of available provider types.
        
        Returns:
            List of provider type strings
            
        Example:
            >>> providers = LLMFactory.get_available_providers()
            >>> print(providers)
            ['gemini', 'ollama']
        """
        return list(cls._PROVIDERS.keys())
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type[LLMProvider]) -> None:
        """
        Register a new provider type.
        
        This allows extending the factory with custom providers.
        
        Args:
            name: Provider type name (will be normalized to lowercase)
            provider_class: Provider class that implements LLMProvider
            
        Raises:
            TypeError: If provider_class doesn't implement LLMProvider
            
        Example:
            >>> class CustomProvider(LLMProvider):
            ...     pass
            >>> LLMFactory.register_provider("custom", CustomProvider)
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(
                f"{provider_class.__name__} must implement LLMProvider interface"
            )
        
        cls._PROVIDERS[name.lower().strip()] = provider_class


# Convenience function for simpler usage
def create_llm_provider(
    provider_type: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Convenience function to create an LLM provider.
    
    This is a simpler alternative to using LLMFactory.create() directly.
    
    Args:
        provider_type: Type of provider ('gemini', 'ollama')
        **kwargs: Additional arguments for provider
    
    Returns:
        LLMProvider instance
    """
    return LLMFactory.create(provider_type=provider_type, **kwargs)
