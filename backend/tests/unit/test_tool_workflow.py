import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.agent.schemas import WorkflowState
from app.db.base import Base
from app.models.task import Task
from app.models.tool_call import ToolCall
from app.services.workflow_service import run_task_workflow
from app.workflow.graph import build_workflow


def test_workflow_executes_calculator_tool() -> None:
    state = WorkflowState(task_id=uuid.uuid4(), goal="calculate: 100*0.8").model_dump(mode="json")

    result = build_workflow().invoke(state)

    assert result["review_result"]["passed"] is True
    assert result["tool_results"][0]["tool_name"] == "calculator"
    assert result["tool_results"][0]["output"] == {"result": 80.0}


def test_workflow_persists_tool_call() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        task = Task(title="Calculate discount", input_text="calculate: 100*0.8")
        session.add(task)
        session.commit()
        session.refresh(task)

        workflow_run = run_task_workflow(task, session)
        tool_call = session.scalar(select(ToolCall))

        assert workflow_run.status == "success"
        assert tool_call is not None
        assert tool_call.workflow_run_id == workflow_run.id
        assert tool_call.tool_name == "calculator"
        assert tool_call.status == "success"
        assert tool_call.output == {"result": 80.0}
