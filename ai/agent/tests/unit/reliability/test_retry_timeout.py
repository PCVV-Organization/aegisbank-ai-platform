"""Tests for RetryPolicy and timeout enforcement."""

from __future__ import annotations

import time

import pytest

from aegisbank_agent.reliability.retry import (
    RetryPolicy,
    TransientError,
)
from aegisbank_agent.reliability.timeout import (
    ExecutionTimeoutError,
    timeout,
    with_timeout,
)

pytestmark = pytest.mark.unit


class TestRetryPolicy:
    def test_transient_error_retries_and_succeeds(self) -> None:
        attempts = 0
        delays: list[float] = []

        def flaky_operation() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise TransientError("Conexión perdida temporalmente")
            return "SUCCESS"

        policy = RetryPolicy(
            max_retries=3,
            base_delay=0.01,
            max_delay=0.1,
            jitter=False,
            sleep_fn=delays.append,
        )

        result = policy.execute(flaky_operation)
        assert result == "SUCCESS"
        assert attempts == 3
        assert len(delays) == 2
        assert delays[0] == 0.01
        assert delays[1] == 0.02

    def test_max_retries_exhausted_raises_exception(self) -> None:
        attempts = 0
        delays: list[float] = []

        def continuously_failing() -> None:
            nonlocal attempts
            attempts += 1
            raise TransientError("Falla persistente")

        policy = RetryPolicy(
            max_retries=2,
            base_delay=0.01,
            jitter=False,
            sleep_fn=delays.append,
        )

        with pytest.raises(TransientError, match="Falla persistente"):
            policy.execute(continuously_failing)

        assert attempts == 3  # initial attempt + 2 retries
        assert len(delays) == 2

    def test_non_transient_error_fails_immediately_without_retry(self) -> None:
        attempts = 0
        delays: list[float] = []

        def validation_failure() -> None:
            nonlocal attempts
            attempts += 1
            raise ValueError("Parámetro inválido")

        policy = RetryPolicy(
            max_retries=3,
            base_delay=0.01,
            sleep_fn=delays.append,
        )

        with pytest.raises(ValueError, match="Parámetro inválido"):
            policy.execute(validation_failure)

        assert attempts == 1  # 0 retries
        assert len(delays) == 0

    def test_jitter_generates_bounded_delay(self) -> None:
        policy = RetryPolicy(base_delay=1.0, max_delay=10.0, jitter=True)
        for attempt in range(4):
            max_backoff = min(10.0, 1.0 * (2**attempt))
            delay = policy.compute_delay(attempt)
            assert 0.0 <= delay <= max_backoff


class TestTimeout:
    def test_fast_operation_completes_within_timeout(self) -> None:
        def fast_fn() -> int:
            return 42

        assert with_timeout(1.0, fast_fn) == 42

    def test_slow_operation_raises_execution_timeout_error(self) -> None:
        def slow_fn() -> None:
            time.sleep(0.5)

        with pytest.raises(ExecutionTimeoutError, match="excedió el tiempo límite"):
            with_timeout(0.05, slow_fn)

    def test_timeout_decorator(self) -> None:
        @timeout(0.05)
        def sleeping_fn() -> None:
            time.sleep(0.5)

        with pytest.raises(ExecutionTimeoutError):
            sleeping_fn()
