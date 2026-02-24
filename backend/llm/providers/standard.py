import json
import logging
from typing import Any

import aiohttp

# Optional imports for providers
try:
    from google import genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

from ..provider_interface import LLMProvider

logger = logging.getLogger(__name__)


class MockProvider(LLMProvider):
    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        return f"Mock response to: {prompt[:20]}..."

    async def generate_json(
        self, prompt: str, schema: dict | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        return {"mock": "data", "prompt_preview": prompt[:20]}

    async def generate_structured(
        self,
        prompt: str,
        schema: type[Any],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Generate a Pydantic object based on the schema (mock implementation)."""
        # Return a mock instance of the schema with default values
        return schema()


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        if not genai:
            raise ImportError("google-genai package not installed. Run 'pip install google-genai'")
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        try:
            config = {}
            if system_prompt:
                config["system_instruction"] = system_prompt

            # The new SDK uses a synchronous call by default, we wrap it
            # Note: For production high-load, one would use the async client if available
            response = self.client.models.generate_content(
                model=self.model, contents=prompt, config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"Error: {e}"

    async def generate_json(
        self, prompt: str, schema: dict | None = None, **kwargs
    ) -> dict[str, Any]:
        try:
            config = {"response_mime_type": "application/json"}
            if schema:
                config["response_schema"] = schema

            response = self.client.models.generate_content(
                model=self.model, contents=prompt, config=config
            )
            # The new SDK can return structured objects if schema is provided,
            # but response.text will contain the JSON string.
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini JSON parse failed: {e}")
            return {}


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4-turbo-preview"):
        if not openai:
            raise ImportError("openai package not installed")
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model_name

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages, **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Error: {e}"

    async def generate_json(
        self, prompt: str, schema: dict | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        # Force JSON mode
        kwargs["response_format"] = {"type": "json_object"}
        text = await self.generate_text(prompt, **kwargs)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3"):
        self.base_url = base_url
        self.model = model_name

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, **kwargs: Any
    ) -> str:
        url = f"{self.base_url}/api/generate"

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\nUser: {prompt}"

        payload = {"model": self.model, "prompt": full_prompt, "stream": False}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"Ollama error: {resp.status}")
                        return f"Error: {resp.status}"
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return f"Error: {e}"

    async def generate_json(
        self, prompt: str, schema: dict | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{prompt}\nReturn JSON only.",
            "format": "json",
            "stream": False,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return json.loads(result.get("response", "{}"))
        except Exception as e:
            logger.error(f"Ollama JSON failed: {e}")
        return {}
