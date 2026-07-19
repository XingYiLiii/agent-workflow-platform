from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.task import Task
from app.models.workflow_checkpoint import WorkflowCheckpoint
from app.services.workflow_service import run_task_workflow


def test_workflow_saves_and_reads_checkpoints() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        task = Task(title="Calculate", input_text="calculate: 100*0.8")
        session.add(task)
        session.commit()
        session.refresh(task)

        workflow_run = run_task_workflow(task, session)
        checkpoints = list(
            session.scalars(
                select(WorkflowCheckpoint)
                .where(WorkflowCheckpoint.workflow_run_id == workflow_run.id)
                .order_by(WorkflowCheckpoint.created_at)
            )
        )

    assert [checkpoint.current_node for checkpoint in checkpoints] == [
        "planner",
        "executor",
        "reviewer",
        "finalizer",
    ]
