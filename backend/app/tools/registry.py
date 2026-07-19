from pydantic import BaseModel

from app.tools.base import BaseTool, ToolExecutionError


class ToolNotFoundError(ToolExecutionError):
    """Raised when a requested tool is not registered."""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        try:
            return self._tools[name]
        except KeyError as error:
            raise ToolNotFoundError(f"Tool is not registered: {name}") from error

    def contains(self, name: str) -> bool:
        return name in self._tools

    async def execute(self, name: str, payload: dict[str, object]) -> BaseModel:
        tool = self.get(name)
        arguments = tool.args_schema.model_validate(payload)
        result = await tool.execute(arguments)
        return tool.result_schema.model_validate(result)
