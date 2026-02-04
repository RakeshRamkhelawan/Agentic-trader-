from typing import Optional, Type, TypeVar
import os
import json
import re
from pydantic import BaseModel
import httpx

from backend.llm.provider_interface import LLMProvider

T = TypeVar("T", bound=BaseModel)

class OllamaProvider(LLMProvider):
    """Ollama LLM Provider for local model inference."""
    
    def __init__(
        self, 
        base_url: Optional[str] = None, 
        model_name: str = "llama2"
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name
        self.generate_endpoint = f"{self.base_url}/api/generate"
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Ollama API."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.generate_endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["response"]
    
    async def generate_structured(
        self, 
        prompt: str, 
        schema: Type[T], 
        system_prompt: Optional[str] = None
    ) -> T:
        """Generate structured output using Ollama API."""
        # Add JSON format instruction to prompt
        schema_json = schema.model_json_schema()
        json_instruction = (
            f"\n\nReturn the result strictly as a valid JSON object matching this schema: "
            f"{json.dumps(schema_json)}\n"
            f"Return ONLY the JSON, no explanation."
        )
        
        full_prompt = prompt + json_instruction
        
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "format": "json"  # Ollama supports JSON mode
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.generate_endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            text = result["response"]
            
            # Clean markdown code blocks if present (fallback)
            text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
            text = text.strip()
            
            return schema.model_validate_json(text)
