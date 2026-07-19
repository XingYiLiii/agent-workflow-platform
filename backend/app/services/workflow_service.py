from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import WorkflowState
from app.models.task import Task, TaskStep
from app.models.workflow_run import WorkflowRun
from app.workflow.graph import build_workflow


def run_task_workflow(task: Task, db: Session) -> WorkflowRun:
    workflow_run = WorkflowRun(task_id=task.id, status="running", current_node="planner")
    task.status = "running"
    db.add(workflow_run)
    db.commit()
    db.refresh(workflow_run)

    state: dict[str, Any] = WorkflowState(task_id=task.id, goal=task.input_text).model_dump(
        mode="json"
    )
    try:
        for update in build_workflow().stream(state, stream_mode="updates"):
            node_name, node_update = next(iter(update.items()))
            state.update(node_update)
            workflow_run.current_node = node_name
            workflow_run.node_history = [*workflow_run.node_history, node_name]
            db.commit()

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

        workflow_run.result = {
            "final_output": final_state.final_output.model_dump(mode="json")
            if final_state.final_output
            else None,
            "review_result": final_state.review_result.model_dump(mode="json")
            if final_state.review_result
            else None,
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
