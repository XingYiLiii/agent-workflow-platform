import uuid

from app.agent.schemas import ExecutionPlan, ExecutionStep, StepResult, WorkflowState
from app.workflow.graph import (
    build_workflow,
    executor_node,
    finalizer_node,
    planner_node,
    reviewer_node,
)


def initial_state() -> dict[str, object]:
    return WorkflowState(task_id=uuid.uuid4(), goal="Analyze sales").model_dump(mode="json")


def test_workflow_starts_and_generates_final_output() -> None:
    result = build_workflow().invoke(initial_state())

    assert result["review_result"]["passed"] is True
    assert "Analyze sales" in result["final_output"]["content"]


def test_planner_returns_structured_plan() -> None:
    result = planner_node(initial_state())

    plan = ExecutionPlan.model_validate(result["plan"])
    assert plan.goal == "Analyze sales"
    assert plan.steps[0].id == "step_1"


def test_executor_completes_planned_step() -> None:
    state = initial_state()
    state["plan"] = ExecutionPlan(
        goal="Analyze sales", steps=[ExecutionStep(id="step_1", description="Inspect sales")]
    ).model_dump(mode="json")

    result = executor_node(state)

    step_result = StepResult.model_validate(result["step_results"][0])
    assert step_result.status == "completed"


def test_reviewer_detects_empty_result() -> None:
    state = initial_state()
    state["step_results"] = [
        StepResult(step_id="step_1", status="completed", result="").model_dump(mode="json")
    ]

    result = reviewer_node(state)

    assert result["review_result"]["passed"] is False
    assert result["review_result"]["issues"]


def test_finalizer_creates_output() -> None:
    state = initial_state()
    state["step_results"] = [
        StepResult(step_id="step_1", status="completed", result="analysis completed").model_dump(
            mode="json"
        )
    ]
    state["review_result"] = {"passed": True, "issues": []}

    result = finalizer_node(state)

    assert "analysis completed" in result["final_output"]["content"]
