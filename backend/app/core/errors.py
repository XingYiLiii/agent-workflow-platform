class AgentError(Exception):
    error_type = "agent_error"
    retryable = False

    def __init__(self, message: str, retryable: bool | None = None) -> None:
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable


class ValidationError(AgentError):
    error_type = "validation_error"


class ToolExecutionError(AgentError):
    error_type = "tool_execution_error"
    retryable = True


class LLMError(AgentError):
    error_type = "llm_error"
    retryable = True


class WorkflowTimeoutError(AgentError):
    error_type = "workflow_timeout"
    retryable = True


class PermissionError(AgentError):
    error_type = "permission_error"


def classify_error(error: Exception) -> AgentError:
    if isinstance(error, AgentError):
        return error
    if isinstance(error, ValueError):
        return ValidationError(str(error))
    return AgentError(str(error))
