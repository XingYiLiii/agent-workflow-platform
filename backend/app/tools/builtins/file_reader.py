import csv
from pathlib import Path

from pydantic import BaseModel

from app.tools.base import BaseTool, ToolExecutionError
from app.tools.schemas import FileReaderInput, FileReaderOutput


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Read and summarize a CSV file from the approved tool input directory."
    args_schema = FileReaderInput
    result_schema = FileReaderOutput

    def __init__(self, allowed_directory: Path) -> None:
        self.allowed_directory = allowed_directory.resolve()

    async def execute(self, arguments: BaseModel) -> FileReaderOutput:
        payload = FileReaderInput.model_validate(arguments)
        file_path = self._resolve_path(payload.file_path)
        if file_path.suffix.lower() != ".csv":
            raise ToolExecutionError("Only CSV files are supported")
        if not file_path.exists() or not file_path.is_file():
            raise ToolExecutionError("CSV file does not exist")
        if file_path.stat().st_size == 0:
            raise ToolExecutionError("CSV file is empty")

        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                columns = reader.fieldnames or []
                if not columns:
                    raise ToolExecutionError("CSV file has no header row")
                rows = list(reader)
        except UnicodeDecodeError as error:
            raise ToolExecutionError("CSV file must use UTF-8 encoding") from error
        except csv.Error as error:
            raise ToolExecutionError("CSV file is malformed") from error

        data_types = {
            column: self._infer_type([row.get(column, "") for row in rows]) for column in columns
        }
        return FileReaderOutput(
            rows=len(rows),
            columns=columns,
            data_types=data_types,
            summary=f"CSV contains {len(rows)} rows and {len(columns)} columns.",
        )

    def _resolve_path(self, requested_path: str) -> Path:
        candidate = Path(requested_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ToolExecutionError("File path must be relative to the approved directory")
        resolved = (self.allowed_directory / candidate).resolve()
        if not resolved.is_relative_to(self.allowed_directory):
            raise ToolExecutionError("File path is outside the approved directory")
        return resolved

    @staticmethod
    def _infer_type(values: list[str]) -> str:
        populated = [value for value in values if value.strip()]
        if not populated:
            return "empty"
        if all(value.lstrip("+-").isdigit() for value in populated):
            return "integer"
        try:
            for value in populated:
                float(value)
        except ValueError:
            return "string"
        return "number"
