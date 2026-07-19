from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.task import Task
from app.models.workflow_checkpoint import WorkflowCheckpoint
from app.services.workflow_recovery_service import WorkflowRecoveryService
from app.services.workflow_service import run_task_workflow


def test_recovery_starts_after_latest_checkpoint() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        task = Task(title="Recover", input_text="calculate: 100*0.8")
        session.add(task)
        session.commit()
        session.refresh(task)
        original_run = run_task_workflow(task, session)
        checkpoint = session.scalar(
            select(WorkflowCheckpoint)
            .where(WorkflowCheckpoint.workflow_run_id == original_run.id)
            .where(WorkflowCheckpoint.current_node == "planner")
        )
        assert checkpoint is not None
        task.status = "failed"
        session.commit()
        recovered_run = WorkflowRecoveryService().recover(task, session)

        assert recovered_run.node_history == ["executor", "reviewer", "finalizer"]
        assert task.status == "success"
