from collections.abc import Mapping
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.schemas import ExecutionPlan, FinalOutput, ReviewResult, WorkflowState
from app.llm.fake_provider import FakeProvider
from app.prompts.registry import prompt_registry
from app.workflow.tool_executor import execute_steps


def _state(value: Mapping[str, Any] | WorkflowState) -> WorkflowState:
    return WorkflowState.model_validate(value)


def planner_node(value: Mapping[str, Any] | WorkflowState) -> dict[str, object]:
    state = _state(value)
    prompt = prompt_registry.get("planner", "v1").render(goal=state.goal)
    plan = FakeProvider().structured_generate(prompt, ExecutionPlan)
    return {"plan": plan.model_dump(mode="json"), "current_step": 0}


def executor_node(value: Mapping[str, Any] | WorkflowState) -> dict[str, object]:
    state = _state(value)
    if state.plan is None:
        return {"error": "Execution plan is missing"}
    return execute_steps(state)


def reviewer_node(value: Mapping[str, Any] | WorkflowState) -> dict[str, object]:
    state = _state(value)
    prompt_registry.get("reviewer", "v1").render(goal=state.goal)
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
    prompt_registry.get("finalizer", "v1").render(goal=state.goal)
    summary = "\n".join(result.result for result in state.step_results)
    output = FinalOutput(content=f"Goal: {state.goal}\n\n{summary}")
    return {"final_output": output.model_dump(mode="json")}


def build_workflow(start_node: str = "planner"):
    graph = StateGraph(WorkflowState)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("finalizer", finalizer_node)
    graph.add_edge(START, start_node)
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reviewer")
    graph.add_edge("reviewer", "finalizer")
    graph.add_edge("finalizer", END)
    return graph.compile()
