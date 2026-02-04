from google import genai
from google.genai import types
from typing import Optional, Type, TypeVar
import os
import json
import re
from pydantic import BaseModel

from backend.llm.provider_interface import LLMProvider

T = TypeVar("T", bound=BaseModel)

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("Google API Key is missing")
        
        self.client = genai.Client(api_key=self.api_key)

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        
        config = None
        if system_prompt:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )
        return response.text

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None) -> T:
        # Use JSON mode with schema for structured output
        schema_json = schema.model_json_schema()
        json_instruction = f"\n\nReturn the result strictly as a valid JSON object matching this schema: {json.dumps(schema_json)}"
        
        full_prompt = prompt + json_instruction
        contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]
        
        config_params = {
            "response_mime_type": "application/json"
        }
        
        if system_prompt:
            config_params["system_instruction"] = system_prompt
        
        config = types.GenerateContentConfig(**config_params)
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )
        
        text = response.text
        
        # Clean markdown code blocks if present (fallback for models that don't respect JSON mode)
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        return schema.model_validate_json(text)
