from app.agent.schemas import ExecutionPlan, ExecutionStep
from app.llm.base import BaseLLMProvider, StructuredOutput


def _extract_goal(prompt: str) -> str:
    start_tag = "<goal>"
    end_tag = "</goal>"
    if start_tag in prompt and end_tag in prompt:
        return prompt.split(start_tag, maxsplit=1)[1].split(end_tag, maxsplit=1)[0].strip()
    return prompt.strip()


class FakeProvider(BaseLLMProvider):
    """Deterministic provider that keeps tests independent from external LLM APIs."""

    def generate(self, prompt: str) -> str:
        return prompt

    def structured_generate(self, prompt: str, schema: type[StructuredOutput]) -> StructuredOutput:
        if schema is not ExecutionPlan:
            raise ValueError(f"FakeProvider does not support schema: {schema.__name__}")
        goal = _extract_goal(prompt)
        return self.create_plan(goal)  # type: ignore[return-value]

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
            steps=[ExecutionStep(id="step_1", description=f"Analyze and complete: {goal}")],
        )
