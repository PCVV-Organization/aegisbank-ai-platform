"""Timeout enforcement utilities for bounded synchronous and asynchronous operations."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class ExecutionTimeoutError(Exception):
    """Raised when an operation exceeds its configured maximum execution time."""


def with_timeout(
    seconds: float,
    operation: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Execute a callable with a strict maximum duration in seconds."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(operation, *args, **kwargs)
        try:
            return future.result(timeout=seconds)
        except FuturesTimeoutError as exc:
            raise ExecutionTimeoutError(
                f"La operación excedió el tiempo límite máximo de {seconds} segundos."
            ) from exc


def timeout(seconds: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to enforce a strict timeout on function execution."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return with_timeout(seconds, fn, *args, **kwargs)

        return wrapper

    return decorator
