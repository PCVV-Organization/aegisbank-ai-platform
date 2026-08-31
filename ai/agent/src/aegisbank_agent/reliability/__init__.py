"""Reliability, fault tolerance, and messaging foundation for AegisBank AI Platform."""

from __future__ import annotations

from .azure_servicebus_adapter import AzureServiceBusMessageBus
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from .idempotency import IdempotencyConflictError, IdempotencyGuard
from .messaging import (
    DeadLetterQueue,
    IdempotentConsumer,
    LocalMessageBus,
    MessageBus,
    OutboxProcessor,
)
from .retry import NonRetryableError, RetryPolicy, TransientError
from .timeout import ExecutionTimeoutError, with_timeout

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    "DeadLetterQueue",
    "ExecutionTimeoutError",
    "IdempotencyConflictError",
    "IdempotencyGuard",
    "IdempotentConsumer",
    "LocalMessageBus",
    "MessageBus",
    "NonRetryableError",
    "OutboxProcessor",
    "RetryPolicy",
    "TransientError",
    "with_timeout",
    "AzureServiceBusMessageBus",
]
