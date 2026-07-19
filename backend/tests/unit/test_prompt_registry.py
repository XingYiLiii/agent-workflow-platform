import pytest

from app.prompts.registry import PromptRegistry, PromptTemplate, prompt_registry


def test_prompt_registry_registers_and_gets_versioned_prompt() -> None:
    registry = PromptRegistry()
    prompt = PromptTemplate(name="planner", version="v2", template="Plan: {goal}")

    registry.register(prompt)

    assert registry.get("planner", "v2") is prompt
    assert registry.get("planner", "v2").render(goal="Analyze sales") == "Plan: Analyze sales"


def test_prompt_registry_rejects_unknown_version() -> None:
    with pytest.raises(KeyError, match="Prompt not found"):
        prompt_registry.get("planner", "v99")


def test_default_registry_contains_workflow_prompts() -> None:
    assert prompt_registry.get("planner", "v1").name == "planner"
    assert prompt_registry.get("reviewer", "v1").name == "reviewer"
    assert prompt_registry.get("finalizer", "v1").name == "finalizer"
