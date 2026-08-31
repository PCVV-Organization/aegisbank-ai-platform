"""Tests for CircuitBreaker finite state machine and failure isolation."""

from __future__ import annotations

import pytest

from aegisbank_agent.reliability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


class MockClock:
    def __init__(self, start_time: float = 1000.0) -> None:
        self.current_time = start_time

    def time(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


def test_circuit_breaker_closed_state_success() -> None:
    clock = MockClock()
    cb = CircuitBreaker(name="core_banking", failure_threshold=3, time_fn=clock.time)
    assert cb.state == CircuitState.CLOSED

    res = cb.execute(lambda: "OK")
    assert res == "OK"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_trips_to_open_after_failures() -> None:
    clock = MockClock()
    cb = CircuitBreaker(
        name="core_banking",
        failure_threshold=3,
        recovery_timeout=5.0,
        time_fn=clock.time,
    )

    def failing_call() -> None:
        raise ConnectionError("Servidor no responde")

    # 1st failure
    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # 2nd failure
    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 2

    # 3rd failure -> trips to OPEN
    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.OPEN

    # Subsequent call fast-fails immediately without calling underlying function
    calls = 0

    def never_called() -> None:
        nonlocal calls
        calls += 1

    with pytest.raises(CircuitBreakerOpenError, match="estado OPEN"):
        cb.execute(never_called)

    assert calls == 0


def test_circuit_breaker_recovery_half_open_to_closed() -> None:
    clock = MockClock()
    cb = CircuitBreaker(
        name="core_banking",
        failure_threshold=2,
        recovery_timeout=5.0,
        time_fn=clock.time,
    )

    def failing_call() -> None:
        raise ConnectionError("Caído")

    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.OPEN

    # Advance clock beyond cooldown period
    clock.advance(5.1)
    assert cb.state == CircuitState.HALF_OPEN

    # Probe call succeeds -> closes circuit
    res = cb.execute(lambda: "RECOVERED")
    assert res == "RECOVERED"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_half_open_failure_returns_to_open() -> None:
    clock = MockClock()
    cb = CircuitBreaker(
        name="core_banking",
        failure_threshold=2,
        recovery_timeout=5.0,
        time_fn=clock.time,
    )

    def failing_call() -> None:
        raise ConnectionError("Caído")

    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.OPEN

    # Advance clock to HALF_OPEN
    clock.advance(5.1)
    assert cb.state == CircuitState.HALF_OPEN

    # Probe call fails -> trips back to OPEN
    with pytest.raises(ConnectionError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.OPEN
