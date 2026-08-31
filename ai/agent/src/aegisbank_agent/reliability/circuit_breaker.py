"""Finite State Machine Circuit Breaker for cascading failure prevention."""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when an operation is attempted while the circuit breaker is in OPEN state."""


class CircuitBreaker:
    """Protects dependencies from cascading failures with CLOSED, OPEN, and HALF_OPEN states."""

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        recovery_timeout: float = 2.0,
        success_threshold: int = 1,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self._time = time_fn or time.time

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._success_count: int = 0
        self._last_failure_time: float | None = None
        self._last_state_change: float = self._time()

    @property
    def state(self) -> CircuitState:
        """Current state of the circuit breaker, automatically evaluating cooldown."""
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            if self._time() - self._last_failure_time >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def _transition_to(self, new_state: CircuitState) -> None:
        self._state = new_state
        self._last_state_change = self._time()
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0

    def execute(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute operation guarded by the circuit breaker."""
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Cortacircuitos '{self.name}' en estado OPEN. "
                "Operación rechazada de forma inmediata."
            )

        try:
            result = operation(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise exc

    def _on_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def _on_failure(self) -> None:
        self._last_failure_time = self._time()
        self._failure_count += 1

        if self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
        elif self._state == CircuitState.CLOSED and self._failure_count >= self.failure_threshold:
            self._transition_to(CircuitState.OPEN)
