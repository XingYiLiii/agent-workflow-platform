from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import WorkflowState
from app.models.task import Task, TaskStep
from app.models.tool_call import ToolCall
from app.models.workflow_checkpoint import WorkflowCheckpoint
from app.models.workflow_run import WorkflowRun
from app.workflow.graph import build_workflow


def run_task_workflow(
    task: Task,
    db: Session,
    state_snapshot: dict[str, object] | None = None,
    start_node: str = "planner",
) -> WorkflowRun:
    workflow_run = WorkflowRun(task_id=task.id, status="running", current_node="planner")
    task.status = "running"
    db.add(workflow_run)
    db.commit()
    db.refresh(workflow_run)

    state: dict[str, Any] = state_snapshot or WorkflowState(
        task_id=task.id, goal=task.input_text
    ).model_dump(mode="json")
    try:
        for update in build_workflow(start_node).stream(state, stream_mode="updates"):
            node_name, node_update = next(iter(update.items()))
            state.update(node_update)
            workflow_run.current_node = node_name
            workflow_run.node_history = [*workflow_run.node_history, node_name]
            db.commit()
            db.add(
                WorkflowCheckpoint(
                    task_id=task.id,
                    workflow_run_id=workflow_run.id,
                    current_node=node_name,
                    state_snapshot=WorkflowState.model_validate(state).model_dump(mode="json"),
                )
            )

        final_state = WorkflowState.model_validate(state)
        if final_state.plan is not None:
            result_by_step = {result.step_id: result for result in final_state.step_results}
            for step in final_state.plan.steps:
                result = result_by_step.get(step.id)
                db.add(
                    TaskStep(
                        task_id=task.id,
                        name=step.description,
                        status=result.status if result else "failed",
                        result=result.model_dump(mode="json") if result else None,
                    )
                )

        for tool_result in final_state.tool_results:
            db.add(
                ToolCall(
                    task_id=task.id,
                    workflow_run_id=workflow_run.id,
                    tool_name=tool_result.tool_name,
                    input=tool_result.input,
                    output=tool_result.output,
                    status=tool_result.status,
                    error_message=tool_result.error_message,
                )
            )
        workflow_run.result = {
            "final_output": final_state.final_output.model_dump(mode="json")
            if final_state.final_output
            else None,
            "review_result": final_state.review_result.model_dump(mode="json")
            if final_state.review_result
            else None,
            "tool_results": [result.model_dump(mode="json") for result in final_state.tool_results],
            "error": final_state.error,
        }
        succeeded = final_state.final_output is not None and final_state.error is None
        workflow_run.status = "success" if succeeded else "failed"
        task.status = workflow_run.status
        db.commit()
    except Exception:
        db.rollback()
        workflow_run.status = "failed"
        workflow_run.current_node = "failed"
        workflow_run.result = {"error": "Workflow execution failed"}
        task.status = "failed"
        db.commit()

    db.refresh(workflow_run)
    return workflow_run
