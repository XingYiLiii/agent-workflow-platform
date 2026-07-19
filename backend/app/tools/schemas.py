from pydantic import BaseModel, Field


class FileReaderInput(BaseModel):
    file_path: str = Field(min_length=1)


class FileReaderOutput(BaseModel):
    rows: int
    columns: list[str]
    data_types: dict[str, str]
    summary: str


class CalculatorInput(BaseModel):
    expression: str = Field(min_length=1, max_length=200)


class CalculatorOutput(BaseModel):
    result: int | float


class ToolResult(BaseModel):
    tool_name: str
    input: dict[str, object]
    output: dict[str, object] | None = None
    status: str
    error_message: str | None = None
