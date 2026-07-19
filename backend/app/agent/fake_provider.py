from app.agent.schemas import ExecutionPlan, ExecutionStep


class FakeLLMProvider:
    """Deterministic provider that keeps Phase 2 independent from real LLM APIs."""

    def create_plan(self, goal: str) -> ExecutionPlan:
        normalized_goal = goal.strip()
        if normalized_goal.lower().startswith("calculate:"):
            expression = normalized_goal.split(":", maxsplit=1)[1].strip()
            return ExecutionPlan(
                goal=goal,
                steps=[
                    ExecutionStep(
                        id="step_1",
                        description="Calculate the requested expression",
                        type="calculation",
                        tool_input={"expression": expression},
                    )
                ],
            )
        if normalized_goal.lower().startswith("analyze csv:"):
            file_path = normalized_goal.split(":", maxsplit=1)[1].strip()
            return ExecutionPlan(
                goal=goal,
                steps=[
                    ExecutionStep(
                        id="step_1",
                        description="Analyze CSV file",
                        type="file_analysis",
                        tool_input={"file_path": file_path},
                    )
                ],
            )
        return ExecutionPlan(
            goal=goal,
            steps=[
                ExecutionStep(id="step_1", description=f"Analyze and complete: {goal}"),
            ],
        )
