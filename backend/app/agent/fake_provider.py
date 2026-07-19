from app.agent.schemas import ExecutionPlan, ExecutionStep


class FakeLLMProvider:
    """Deterministic provider that keeps Phase 2 independent from real LLM APIs."""

    def create_plan(self, goal: str) -> ExecutionPlan:
        return ExecutionPlan(
            goal=goal,
            steps=[
                ExecutionStep(id="step_1", description=f"Analyze and complete: {goal}"),
            ],
        )
