"""
LLM Provider Interface for Conscious Agents
Supports DeepSeek, Ollama, and other LLM backends
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class LLMBackend(Enum):
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    backend: LLMBackend = LLMBackend.OLLAMA
    model: str = "llama3.2"  # or "deepseek-chat", "gpt-4", etc.
    temperature: float = 0.3  # Lower for more deterministic trading
    max_tokens: int = 500
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    def __post_init__(self):
        if self.backend == LLMBackend.DEEPSEEK:
            self.api_key = self.api_key or os.getenv("DEEPSEEK_API_KEY")
            self.base_url = self.base_url or "https://api.deepseek.com/v1"
        elif self.backend == LLMBackend.OLLAMA:
            self.base_url = self.base_url or "http://localhost:11434"
        elif self.backend == LLMBackend.OPENAI:
            self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")


class LLMProvider:
    """
    Unified LLM interface for conscious trading agents
    
    Usage:
        llm = LLMProvider(LLMConfig(backend=LLMBackend.OLLAMA, model="llama3.2"))
        response = llm.generate("Analyze BTC trend...")
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.request_count = 0
        self.token_count = 0
        
        print(f"[LLM] Initialized: {self.config.backend.value}/{self.config.model}")
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate response from LLM
        
        Returns:
            {
                'text': str,
                'confidence': float,
                'reasoning': str,
                'metadata': dict
            }
        """
        temp = temperature or self.config.temperature
        
        if self.config.backend == LLMBackend.OLLAMA:
            return self._generate_ollama(prompt, system_prompt, temp)
        elif self.config.backend == LLMBackend.DEEPSEEK:
            return self._generate_deepseek(prompt, system_prompt, temp)
        elif self.config.backend == LLMBackend.OPENAI:
            return self._generate_openai(prompt, system_prompt, temp)
        else:
            # Fallback to mock for testing
            return self._generate_mock(prompt, system_prompt, temp)
    
    def _generate_ollama(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float
    ) -> Dict[str, Any]:
        """Generate using Ollama local API"""
        try:
            url = f"{self.config.base_url}/api/generate"
            
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "system": system_prompt or "You are a trading analysis expert.",
                "temperature": temperature,
                "max_tokens": self.config.max_tokens,
                "stream": False,
                "format": "json"
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            text = result.get('response', '{}')
            
            # Try to parse as JSON
            try:
                parsed = json.loads(text)
                return {
                    'text': text,
                    'confidence': parsed.get('confidence', 0.5),
                    'reasoning': parsed.get('reasoning', 'No reasoning provided'),
                    'metadata': {'backend': 'ollama', 'model': self.config.model}
                }
            except json.JSONDecodeError:
                return {
                    'text': text,
                    'confidence': 0.5,
                    'reasoning': text[:200],
                    'metadata': {'backend': 'ollama', 'raw': True}
                }
                
        except Exception as e:
            print(f"[LLM] Ollama error: {e}")
            return self._generate_mock(prompt, system_prompt, temperature)
    
    def _generate_deepseek(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float
    ) -> Dict[str, Any]:
        """Generate using DeepSeek API"""
        try:
            url = f"{self.config.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": self.config.max_tokens,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            text = result['choices'][0]['message']['content']
            
            parsed = json.loads(text)
            return {
                'text': text,
                'confidence': parsed.get('confidence', 0.5),
                'reasoning': parsed.get('reasoning', 'No reasoning provided'),
                'metadata': {
                    'backend': 'deepseek',
                    'model': self.config.model,
                    'tokens': result.get('usage', {}).get('total_tokens', 0)
                }
            }
            
        except Exception as e:
            print(f"[LLM] DeepSeek error: {e}")
            return self._generate_mock(prompt, system_prompt, temperature)
    
    def _generate_openai(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float
    ) -> Dict[str, Any]:
        """Generate using OpenAI API"""
        try:
            import openai
            openai.api_key = self.config.api_key
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            text = response.choices[0].message.content
            parsed = json.loads(text)
            
            return {
                'text': text,
                'confidence': parsed.get('confidence', 0.5),
                'reasoning': parsed.get('reasoning', 'No reasoning provided'),
                'metadata': {
                    'backend': 'openai',
                    'model': self.config.model,
                    'tokens': response.usage.total_tokens
                }
            }
            
        except Exception as e:
            print(f"[LLM] OpenAI error: {e}")
            return self._generate_mock(prompt, system_prompt, temperature)
    
    def _generate_mock(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float
    ) -> Dict[str, Any]:
        """Mock LLM for testing without API"""
        # Extract some info from prompt for realistic mock
        import re
        
        # Check for bullish/bearish signals in prompt
        is_bullish = any(word in prompt.lower() for word in ['bullish', 'uptrend', 'buy'])
        is_bearish = any(word in prompt.lower() for word in ['bearish', 'downtrend', 'sell'])
        
        if is_bullish:
            action = "BUY"
            confidence = 0.65 + (temperature * 0.2)
        elif is_bearish:
            action = "SELL"
            confidence = 0.65 + (temperature * 0.2)
        else:
            action = "HOLD"
            confidence = 0.5
        
        return {
            'text': json.dumps({
                'action': action,
                'confidence': confidence,
                'reasoning': f'Mock LLM analysis based on prompt keywords'
            }),
            'confidence': confidence,
            'reasoning': f'Mock analysis: Detected {action} signals in market context',
            'metadata': {'backend': 'mock', 'temperature': temperature}
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics"""
        return {
            'backend': self.config.backend.value,
            'model': self.config.model,
            'requests': self.request_count,
            'tokens': self.token_count
        }


# Factory function
def create_llm_provider(
    backend = "ollama",
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """Factory to create LLM provider"""
    if isinstance(backend, LLMBackend):
        backend_enum = backend
    else:
        backend_enum = LLMBackend(backend.lower())
    
    if model is None:
        if backend_enum == LLMBackend.OLLAMA:
            model = "llama3.2"
        elif backend_enum == LLMBackend.DEEPSEEK:
            model = "deepseek-chat"
        elif backend_enum == LLMBackend.OPENAI:
            model = "gpt-4"
    
    config = LLMConfig(
        backend=backend_enum,
        model=model,
        **kwargs
    )
    
    return LLMProvider(config)
