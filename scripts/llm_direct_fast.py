#!/usr/bin/env python3
"""
Direct DeepSeek LLM Implementation - FAST VERSION
Uses deepseek-chat for speed (not deepseek-reasoner)
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class DirectDeepSeekLLM:
    """Direct DeepSeek API client - always uses fast chat model."""

    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        # FORCE FAST MODEL
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com"

        if not self.api_key:
            raise ValueError("DeepSeek API key required. Set DEEPSEEK_API_KEY env var.")

    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using DeepSeek API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(
                        f"DeepSeek API error: {response.status_code} - {response.text}"
                    )
                    raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            logger.error(f"DeepSeek request failed: {e}")
            raise


class SimpleLLMFactory:
    """Simple factory that only creates DeepSeek LLM."""

    @staticmethod
    def create_deepseek(model: str = "deepseek-chat") -> DirectDeepSeekLLM:
        """Create DeepSeek LLM instance."""
        return DirectDeepSeekLLM(model=model)

    @staticmethod
    def create_for_agent(agent_role: str) -> DirectDeepSeekLLM:
        """Create LLM configured for specific agent role."""
        # ALWAYS USE FAST MODEL
        logger.info(f"LLM for {agent_role}: using deepseek-chat (FAST)")
        return DirectDeepSeekLLM(model="deepseek-chat")
