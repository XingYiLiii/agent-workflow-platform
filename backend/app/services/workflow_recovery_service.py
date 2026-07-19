from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.workflow_checkpoint import WorkflowCheckpoint
from app.models.workflow_run import WorkflowRun
from app.services.workflow_service import run_task_workflow

_NEXT_NODE = {
    "planner": "executor",
    "executor": "reviewer",
    "reviewer": "finalizer",
}


class WorkflowRecoveryService:
    def recover(self, task: Task, db: Session) -> WorkflowRun:
        if task.status != "failed":
            raise ValueError("Only failed tasks can be recovered")
        checkpoint = db.scalar(
            select(WorkflowCheckpoint)
            .where(WorkflowCheckpoint.task_id == task.id)
            .order_by(WorkflowCheckpoint.created_at.desc())
        )
        if checkpoint is None:
            raise ValueError("No checkpoint is available")
        start_node = _NEXT_NODE.get(checkpoint.current_node)
        if start_node is None:
            raise ValueError("Checkpoint has no remaining workflow node")
        task.status = "running"
        return run_task_workflow(task, db, checkpoint.state_snapshot, start_node)
