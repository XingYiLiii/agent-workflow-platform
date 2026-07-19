from app.agent.schemas import ExecutionPlan
from app.llm.base import BaseLLMProvider
from app.llm.fake_provider import FakeProvider


def test_fake_provider_implements_base_interface() -> None:
    provider = FakeProvider()

    assert isinstance(provider, BaseLLMProvider)
    assert provider.generate("hello") == "hello"


def test_fake_provider_returns_valid_structured_plan() -> None:
    provider = FakeProvider()

    plan = provider.structured_generate(
        "Plan a structured workflow for <goal>calculate: 100*0.8</goal>", ExecutionPlan
    )

    assert isinstance(plan, ExecutionPlan)
    assert plan.steps[0].type == "calculation"
    assert plan.steps[0].tool_input == {"expression": "100*0.8"}
