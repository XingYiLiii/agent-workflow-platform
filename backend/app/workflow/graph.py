from collections.abc import Mapping
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.fake_provider import FakeLLMProvider
from app.agent.schemas import FinalOutput, ReviewResult, StepResult, WorkflowState


def _state(value: Mapping[str, Any] | WorkflowState) -> WorkflowState:
    return WorkflowState.model_validate(value)


def planner_node(value: Mapping[str, Any] | WorkflowState) -> dict[str, object]:
    state = _state(value)
    plan = FakeLLMProvider().create_plan(state.goal)
    return {"plan": plan.model_dump(mode="json"), "current_step": 0}


def executor_node(value: Mapping[str, Any] | WorkflowState) -> dict[str, object]:
    state = _state(value)
    if state.plan is None:
        return {"error": "Execution plan is missing"}
    results = [
        StepResult(
            step_id=step.id,
            status="completed",
            result=f"Completed simulated execution: {step.description}",
        ).model_dump(mode="json")
        for step in state.plan.steps
    ]
    return {"step_results": results, "current_step": len(results)}


def reviewer_node(value: Mapping[str, Any] | WorkflowState) -> dict[str, object]:
    state = _state(value)
    issues = [
        f"Step {result.step_id} has no result"
        for result in state.step_results
        if result.status != "completed" or not result.result.strip()
    ]
    if not state.step_results:
        issues.append("No execution results were produced")
    review = ReviewResult(passed=not issues, issues=issues)
    return {"review_result": review.model_dump(mode="json")}


def finalizer_node(value: Mapping[str, Any] | WorkflowState) -> dict[str, object]:
    state = _state(value)
    if state.review_result is None or not state.review_result.passed:
        return {"error": "Workflow review failed"}
    summary = "\n".join(result.result for result in state.step_results)
    output = FinalOutput(content=f"Goal: {state.goal}\n\n{summary}")
    return {"final_output": output.model_dump(mode="json")}


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("finalizer", finalizer_node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")
    graph.add_edge("reviewer", "finalizer")
    graph.add_edge("finalizer", END)
    return graph.compile()
