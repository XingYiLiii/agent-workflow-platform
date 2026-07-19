import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.api.routes.tasks import retry_task
from app.db.base import Base
from app.models.task import Task
from app.models.workflow_checkpoint import WorkflowCheckpoint
from app.services.workflow_service import run_task_workflow


def test_failed_task_retry_recovers_workflow() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        task = Task(title="Retry", input_text="calculate: 100*0.8")
        session.add(task)
        session.commit()
        session.refresh(task)
        run_task_workflow(task, session)
        planner_checkpoint = session.scalar(
            select(WorkflowCheckpoint).where(
                WorkflowCheckpoint.task_id == task.id,
                WorkflowCheckpoint.current_node == "planner",
            )
        )
        assert planner_checkpoint is not None
        session.execute(
            delete(WorkflowCheckpoint).where(
                WorkflowCheckpoint.task_id == task.id,
                WorkflowCheckpoint.id != planner_checkpoint.id,
            )
        )
        task.status = "failed"
        task.error_type = "ToolExecutionError"
        task.error_message = "temporary file error"
        session.commit()

        response = retry_task(task.id, session)

        assert response["status"] == "success"
        assert task.retry_count == 1
        assert task.status == "success"
        assert task.error_type == "ToolExecutionError"
        assert task.error_message == "temporary file error"


def test_non_failed_task_retry_is_rejected() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        task = Task(title="Not failed", input_text="calculate: 1+1")
        session.add(task)
        session.commit()

        with pytest.raises(HTTPException) as error:
            retry_task(task.id, session)

    assert error.value.status_code == 409
