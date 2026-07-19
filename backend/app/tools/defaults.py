from pathlib import Path

from app.tools.builtins.calculator import CalculatorTool
from app.tools.builtins.file_reader import FileReaderTool
from app.tools.registry import ToolRegistry


def create_default_registry(tool_input_directory: Path | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(FileReaderTool(tool_input_directory or Path("data/tool_inputs")))
    registry.register(CalculatorTool())
    return registry
