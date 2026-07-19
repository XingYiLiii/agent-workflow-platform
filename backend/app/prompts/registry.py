"""In-memory versioned prompt registry used by the workflow nodes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    name: str
    version: str
    template: str

    def render(self, **values: str) -> str:
        return self.template.format(**values)


class PromptRegistry:
    def __init__(self) -> None:
        self._templates: dict[tuple[str, str], PromptTemplate] = {}

    def register(self, prompt: PromptTemplate) -> None:
        key = (prompt.name, prompt.version)
        if key in self._templates:
            raise ValueError(f"Prompt already registered: {prompt.name}:{prompt.version}")
        self._templates[key] = prompt

    def get(self, name: str, version: str = "v1") -> PromptTemplate:
        try:
            return self._templates[(name, version)]
        except KeyError as error:
            raise KeyError(f"Prompt not found: {name}:{version}") from error


prompt_registry = PromptRegistry()
prompt_registry.register(
    PromptTemplate(
        name="planner",
        version="v1",
        template="Plan a structured workflow for <goal>{goal}</goal>",
    )
)
prompt_registry.register(
    PromptTemplate(
        name="reviewer",
        version="v1",
        template="Review execution results for goal: {goal}",
    )
)
prompt_registry.register(
    PromptTemplate(
        name="finalizer",
        version="v1",
        template="Summarize verified results for goal: {goal}",
    )
)
