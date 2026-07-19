from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel


class ToolExecutionError(Exception):
    """Raised when a validated tool request cannot be completed."""


class BaseTool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    args_schema: ClassVar[type[BaseModel]]
    result_schema: ClassVar[type[BaseModel]]

    @abstractmethod
    async def execute(self, arguments: BaseModel) -> BaseModel:
        """Execute a validated tool request and return a validated result."""
        raise NotImplementedError
