from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text response for a rendered prompt."""

    @abstractmethod
    def structured_generate(self, prompt: str, schema: type[StructuredOutput]) -> StructuredOutput:
        """Generate output validated against the requested Pydantic schema."""
