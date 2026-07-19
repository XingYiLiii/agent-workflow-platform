from collections.abc import Callable
from typing import TypeVar

from app.core.errors import AgentError

T = TypeVar("T")


def run_with_retry(operation: Callable[[], T], max_retry: int = 2) -> tuple[T, int]:
    attempts = 0
    while True:
        try:
            return operation(), attempts
        except AgentError as error:
            if not error.retryable or attempts >= max_retry:
                raise
