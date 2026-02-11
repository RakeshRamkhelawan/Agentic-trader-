"""
LLM Factory for creating provider instances.

This factory enables easy switching between different LLM providers
based on environment configuration or explicit parameters.
"""
from typing import Optional, Dict, Any
import os
import logging

_logger = logging.getLogger(__name__)

from backend.llm.provider_interface import LLMProvider
from backend.llm.providers.gemini import GeminiProvider
from backend.llm.providers.ollama import OllamaProvider
from backend.llm.providers.deepseek import DeepSeekProvider


class LLMFactory:
    """Factory for creating LLM provider instances."""
    
    # Registry of available providers
    _PROVIDERS = {
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
        "deepseek": DeepSeekProvider,
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
    def create_for_agent(
        cls,
        agent_role: str,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider configured for a specific agent role.
        
        Lookup order (provider-agnostic):
          1. LLM_AGENT_{ROLE}_PROVIDER / LLM_AGENT_{ROLE}_MODEL
          2. LLM_PROVIDER / LLM_MODEL  (global defaults)
          3. Factory defaults
        
        Args:
            agent_role: Agent identifier (e.g. 'risk_manager', 'bull_researcher')
            **kwargs: Additional arguments passed to provider constructor
            
        Examples:
            >>> # Uses LLM_AGENT_RISK_MANAGER_PROVIDER env var
            >>> provider = LLMFactory.create_for_agent("risk_manager")
            
            >>> # Falls back to LLM_PROVIDER if no agent-specific var set
            >>> provider = LLMFactory.create_for_agent("data_scout")
        """
        role_key = agent_role.upper().replace("-", "_").replace(" ", "_")
        
        # Per-agent env vars
        agent_provider = os.getenv(f"LLM_AGENT_{role_key}_PROVIDER")
        agent_model = os.getenv(f"LLM_AGENT_{role_key}_MODEL")
        
        # Global fallbacks
        provider_type = agent_provider or os.getenv("LLM_PROVIDER", cls._DEFAULT_PROVIDER)
        model_name = agent_model or os.getenv("LLM_MODEL")
        
        # Pass model_name if resolved
        if model_name and "model_name" not in kwargs:
            kwargs["model_name"] = model_name
        
        _logger.info(
            f"LLM routing: agent={agent_role} -> "
            f"provider={provider_type}, model={kwargs.get('model_name', 'default')}"
        )
        
        return cls.create(provider_type=provider_type, **kwargs)
    
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


# Convenience functions
def create_llm_provider(
    provider_type: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Convenience function to create an LLM provider.
    
    This is a simpler alternative to using LLMFactory.create() directly.
    
    Args:
        provider_type: Type of provider ('gemini', 'ollama', 'deepseek')
        **kwargs: Additional arguments for provider
    
    Returns:
        LLMProvider instance
    """
    return LLMFactory.create(provider_type=provider_type, **kwargs)


def create_agent_llm(agent_role: str, **kwargs) -> LLMProvider:
    """
    Create an LLM provider for a specific agent role.
    
    Reads per-agent config from env vars:
      LLM_AGENT_{ROLE}_PROVIDER, LLM_AGENT_{ROLE}_MODEL
    Falls back to LLM_PROVIDER / LLM_MODEL globals.
    
    Args:
        agent_role: Agent identifier (e.g. 'risk_manager')
        **kwargs: Additional provider arguments
    
    Returns:
        LLMProvider instance configured for the agent
    """
    return LLMFactory.create_for_agent(agent_role=agent_role, **kwargs)

