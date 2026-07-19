import ast
import operator

from pydantic import BaseModel

from app.tools.base import BaseTool, ToolExecutionError
from app.tools.schemas import CalculatorInput, CalculatorOutput


class CalculatorTool(BaseTool):
    name = "calculator"
    description = (
        "Safely evaluate arithmetic expressions using numbers, operators, and parentheses."
    )
    args_schema = CalculatorInput
    result_schema = CalculatorOutput

    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
    }

    async def execute(self, arguments: BaseModel) -> CalculatorOutput:
        payload = CalculatorInput.model_validate(arguments)
        try:
            node = ast.parse(payload.expression, mode="eval").body
            result = self._evaluate(node)
        except (SyntaxError, ValueError, ZeroDivisionError) as error:
            raise ToolExecutionError("Expression is invalid or unsupported") from error
        return CalculatorOutput(result=result)

    def _evaluate(self, node: ast.expr) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self._evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in self._operators:
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            return self._operators[type(node.op)](left, right)
        raise ValueError("Unsupported expression node")
