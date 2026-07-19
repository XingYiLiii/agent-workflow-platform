from app.llm.base import BaseLLMProvider, StructuredOutput


class OpenAICompatibleProvider(BaseLLMProvider):
    """Extension point for OpenAI-compatible APIs; network calls are intentionally absent."""

    def __init__(self, model: str, base_url: str | None = None) -> None:
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        raise NotImplementedError("OpenAI-compatible calls are not configured in Phase 4")

    def structured_generate(self, prompt: str, schema: type[StructuredOutput]) -> StructuredOutput:
        raise NotImplementedError("OpenAI-compatible calls are not configured in Phase 4")
