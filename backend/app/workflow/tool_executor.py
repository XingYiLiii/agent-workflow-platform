import asyncio

from app.agent.schemas import StepResult, WorkflowState
from app.tools.base import ToolExecutionError
from app.tools.defaults import create_default_registry
from app.tools.schemas import ToolResult


def execute_steps(state: WorkflowState) -> dict[str, object]:
    registry = create_default_registry()
    results: list[dict[str, object]] = []
    tool_results: list[dict[str, object]] = []
    tool_by_step_type = {"file_analysis": "file_reader", "calculation": "calculator"}
    for step in state.plan.steps if state.plan else []:
        if step.type == "simulation":
            results.append(
                StepResult(
                    step_id=step.id,
                    status="completed",
                    result=f"Completed simulated execution: {step.description}",
                ).model_dump(mode="json")
            )
            continue
        tool_name = tool_by_step_type[step.type]
        try:
            output_data = asyncio.run(registry.execute(tool_name, step.tool_input)).model_dump(
                mode="json"
            )
            tool_results.append(
                ToolResult(
                    tool_name=tool_name,
                    input=step.tool_input,
                    output=output_data,
                    status="success",
                ).model_dump(mode="json")
            )
            results.append(
                StepResult(step_id=step.id, status="completed", result=str(output_data)).model_dump(
                    mode="json"
                )
            )
        except ToolExecutionError as error:
            tool_results.append(
                ToolResult(
                    tool_name=tool_name,
                    input=step.tool_input,
                    status="failed",
                    error_message=str(error),
                ).model_dump(mode="json")
            )
            results.append(
                StepResult(step_id=step.id, status="failed", result="").model_dump(mode="json")
            )
    return {"step_results": results, "tool_results": tool_results, "current_step": len(results)}
