from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    @abstractmethod
    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generates raw text from a prompt."""
        pass

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None
    ) -> T:
        """Generates a Pydantic object based on the schema."""
        pass
