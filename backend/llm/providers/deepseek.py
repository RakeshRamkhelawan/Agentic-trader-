"""
DeepSeek LLM Provider.

Uses the OpenAI-compatible API via the openai Python library
with a custom base_url pointed at https://api.deepseek.com.

Supported models:
  - deepseek-chat      (DeepSeek-V3, fast general-purpose)
  - deepseek-reasoner  (DeepSeek-R1, chain-of-thought reasoning)
"""

import os
import json
import re
import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from backend.llm.provider_interface import LLMProvider

try:
    import openai
except ImportError:
    openai = None

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek LLM provider using the OpenAI-compatible chat completions API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek-chat",
        base_url: Optional[str] = None,
    ):
        if not openai:
            raise ImportError("openai package not installed. Run 'pip install openai'")

        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key is missing. "
                "Set DEEPSEEK_API_KEY in .env or pass api_key=."
            )

        self.model_name = model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)

        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        logger.info(
            f"DeepSeekProvider initialized: model={self.model_name}, "
            f"base_url={self.base_url}"
        )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate raw text from a prompt."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"DeepSeek generate_text failed: {e}")
            return f"Error: {e}"

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        """Generate a Pydantic object based on the schema."""
        schema_json = schema.model_json_schema()
        json_instruction = (
            "\n\nReturn the result strictly as a valid JSON object "
            f"matching this schema: {json.dumps(schema_json)}"
        )

        full_prompt = prompt + json_instruction

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": full_prompt})

        try:
            # deepseek-chat supports response_format, deepseek-reasoner does not
            create_kwargs = {
                "model": self.model_name,
                "messages": messages,
            }
            if self.model_name != "deepseek-reasoner":
                create_kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**create_kwargs)
            text = response.choices[0].message.content or "{}"

            # Strip markdown code fences if present
            text = re.sub(r"^```json\s*", "", text, flags=re.MULTILINE)
            text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
            text = text.strip()

            return schema.model_validate_json(text)
        except Exception as e:
            logger.error(f"DeepSeek generate_structured failed: {e}")
            raise
