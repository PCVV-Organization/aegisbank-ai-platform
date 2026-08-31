"""Bounded retry policy with exponential backoff and jitter for transient faults."""

from __future__ import annotations

import random
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class TransientError(Exception):
    """Exception indicating a temporary, recoverable failure (e.g. network glitch, DB lock)."""


class NonRetryableError(Exception):
    """Exception indicating a permanent failure that must NOT be retried."""


def default_transient_classifier(exc: Exception) -> bool:
    """Classify whether an exception is transient (recoverable) or permanent."""
    if isinstance(exc, (TransientError, TimeoutError, ConnectionError, OSError)):
        return True
    error_str = str(exc).lower()
    transient_indicators = (
        "busy",
        "locked",
        "timeout",
        "temporarily unavailable",
        "connection reset",
    )
    if any(term in error_str for term in transient_indicators):
        return True
    return False


class RetryPolicy:
    """Bounded exponential backoff retry policy with full jitter."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.05,
        max_delay: float = 2.0,
        jitter: bool = True,
        is_transient_classifier: Callable[[Exception], bool] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.is_transient = is_transient_classifier or default_transient_classifier
        self.sleep_fn = sleep_fn or time.sleep

    def compute_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with optional full jitter."""
        backoff = min(self.max_delay, self.base_delay * (2**attempt))
        if self.jitter:
            return random.uniform(0, backoff)
        return backoff

    def execute(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute operation with retry logic for transient exceptions."""
        attempt = 0
        while True:
            try:
                return operation(*args, **kwargs)
            except Exception as exc:
                if not self.is_transient(exc):
                    # Permanent/non-transient error -> fail fast without retry
                    raise exc

                attempt += 1
                if attempt > self.max_retries:
                    # Max retries exhausted
                    raise exc

                delay = self.compute_delay(attempt - 1)
                if delay > 0:
                    self.sleep_fn(delay)
