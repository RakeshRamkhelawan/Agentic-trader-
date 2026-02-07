from typing import Dict, Any, List, Optional
import os
import logging
from pydantic import BaseModel
from backend.llm.providers import LLMProvider, MockProvider, GeminiProvider, OpenAIProvider, OllamaProvider
from backend.llm.usage_tracker import UsageTracker
from backend.storage.tenant_aware_clickhouse import TenantAwareClickHouseClient
from backend.core.auth.context import get_current_tenant_optional

logger = logging.getLogger(__name__)

class LLMMessage(BaseModel):
    role: str
    content: str
    
class LLMResponse(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None

class LLMService:
    def __init__(self, provider: LLMProvider, usage_tracker: Optional[UsageTracker] = None):
        self.provider = provider
        self.usage_tracker = usage_tracker
        
        if self.usage_tracker:
             # Start the usage tracker background task if not already started
             # logic for start/stop might need to be handled at app lifecycle level
             import asyncio
             try:
                 loop = asyncio.get_running_loop()
                 loop.create_task(self.usage_tracker.start())
             except RuntimeError:
                 pass # No running loop yet

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
            
        # Initialize Usage Tracker
        clickhouse_client = TenantAwareClickHouseClient(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
            # password and user handled by env vars in client init
        )
        usage_tracker = UsageTracker(clickhouse_client=clickhouse_client)
            
        logger.info(f"LLM Service initialized with provider: {provider.__class__.__name__}")
        return cls(provider, usage_tracker)

    async def _track_usage(self, prompt: str, response_text: str, model: str):
        if self.usage_tracker:
            try:
                # Determine model name from provider if possible, else use env/passed
                # For now using the model string passed to methods or from env
                
                # Count tokens
                prompt_tokens = self.usage_tracker.token_counter.count_tokens(prompt, model)
                completion_tokens = self.usage_tracker.token_counter.count_tokens(response_text, model)
                
                # Calculate cost
                cost = self.usage_tracker.token_counter.calculate_cost(prompt_tokens, completion_tokens, model)
                
                tenant_id = get_current_tenant_optional() or "system"
                
                await self.usage_tracker.log_usage(
                    tenant_id=tenant_id,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost
                )
            except Exception as e:
                logger.warning(f"Failed to track usage: {e}")

    async def generate_explanation(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a human-readable explanation using the LLM.
        """
        system_prompt = "You are an expert financial analyst. Explain the rationale clearly."
        if context and context.get("role"):
             system_prompt += f" Act as a {context['role']}."
        
        # Determine model for tracking - simpler to assume configured model
        model = getattr(self.provider, 'model_name', os.getenv("LLM_MODEL", "unknown"))

        response_text = await self.provider.generate_text(prompt, system_instruction=system_prompt)
        
        await self._track_usage(prompt + system_prompt, response_text, model)
        
        return response_text

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyzes sentiment and returns structured JSON.
        """
        system_prompt = "Analyze the sentiment of the following text. Return JSON with 'sentiment' (positive/negative/neutral) and 'score' (0.0-1.0)."
        
        model = getattr(self.provider, 'model_name', os.getenv("LLM_MODEL", "unknown"))
        
        response_json = await self.provider.generate_json(text, system_instruction=system_prompt)
        
        # Convert JSON back to string for token counting approximation
        import json
        response_text = json.dumps(response_json)
        
        await self._track_usage(text + system_prompt, response_text, model)
        
        return response_json
