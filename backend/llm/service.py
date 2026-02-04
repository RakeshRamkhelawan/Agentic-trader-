from typing import Dict, Any, List, Optional
import os
import logging
from pydantic import BaseModel
from backend.llm.providers import LLMProvider, MockProvider, GeminiProvider, OpenAIProvider, OllamaProvider

logger = logging.getLogger(__name__)

class LLMMessage(BaseModel):
    role: str
    content: str

class LLMService:
    def __init__(self, provider: LLMProvider):
        self.provider = provider
    
    @classmethod
    def create_from_env(cls) -> 'LLMService':
        """
        Factory to create LLMService based on environment variables.
        """
        provider_type = os.getenv("LLM_PROVIDER", "mock").lower()
        api_key = os.getenv("LLM_API_KEY", "")
        model = os.getenv("LLM_MODEL", "")
        
        provider = None
        
        try:
            if provider_type == "gemini":
                if not model: model = "gemini-pro"
                provider = GeminiProvider(api_key=api_key, model_name=model)
            elif provider_type == "openai":
                if not model: model = "gpt-4-turbo-preview"
                provider = OpenAIProvider(api_key=api_key, model_name=model)
            elif provider_type == "ollama":
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                if not model: model = "llama3"
                provider = OllamaProvider(base_url=base_url, model_name=model)
            else:
                provider = MockProvider()
                logger.warning(f"Unknown or mock provider selected: {provider_type}")
        except Exception as e:
            logger.error(f"Failed to initialize {provider_type} provider: {e}")
            provider = MockProvider()
            
        logger.info(f"LLM Service initialized with provider: {provider.__class__.__name__}")
        return cls(provider)

    async def generate_explanation(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a human-readable explanation using the LLM.
        """
        system_prompt = "You are an expert financial analyst. Explain the rationale clearly."
        if context and context.get("role"):
             system_prompt += f" Act as a {context['role']}."
             
        return await self.provider.generate_text(prompt, system_instruction=system_prompt)

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyzes sentiment and returns structured JSON.
        """
        system_prompt = "Analyze the sentiment of the following text. Return JSON with 'sentiment' (positive/negative/neutral) and 'score' (0.0-1.0)."
        return await self.provider.generate_json(text, system_instruction=system_prompt)
