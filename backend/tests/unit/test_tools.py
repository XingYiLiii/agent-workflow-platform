import asyncio

import pytest

from app.tools.base import ToolExecutionError
from app.tools.builtins.calculator import CalculatorTool
from app.tools.builtins.file_reader import FileReaderTool
from app.tools.registry import ToolNotFoundError, ToolRegistry


def test_registry_registers_executes_and_rejects_unknown_tool() -> None:
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    assert registry.contains("calculator")
    assert registry.get("calculator").name == "calculator"
    assert asyncio.run(registry.execute("calculator", {"expression": "100*0.8"})).result == 80.0
    with pytest.raises(ToolNotFoundError):
        registry.get("missing")


def test_file_reader_analyzes_csv(tmp_path) -> None:
    (tmp_path / "sales.csv").write_text(
        "date,sales\n2026-01-01,100\n2026-01-02,120\n", encoding="utf-8"
    )

    result = asyncio.run(FileReaderTool(tmp_path).execute({"file_path": "sales.csv"}))

    assert result.rows == 2
    assert result.columns == ["date", "sales"]
    assert result.data_types["sales"] == "integer"


@pytest.mark.parametrize(
    "filename,content,error", [("empty.csv", "", "empty"), ("bad.txt", "x", "CSV")]
)
def test_file_reader_rejects_invalid_files(
    tmp_path, filename: str, content: str, error: str
) -> None:
    (tmp_path / filename).write_text(content, encoding="utf-8")

    with pytest.raises(ToolExecutionError, match=error):
        asyncio.run(FileReaderTool(tmp_path).execute({"file_path": filename}))
    with pytest.raises(ToolExecutionError, match="does not exist"):
        asyncio.run(FileReaderTool(tmp_path).execute({"file_path": "missing.csv"}))


def test_calculator_rejects_non_arithmetic_expressions() -> None:
    with pytest.raises(ToolExecutionError):
        asyncio.run(CalculatorTool().execute({"expression": "__import__('os').system('whoami')"}))
