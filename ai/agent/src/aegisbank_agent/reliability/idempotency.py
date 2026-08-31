"""Idempotency guard and hash verification for banking write operations."""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Callable

from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.repositories import IdempotencyRepository


class IdempotencyConflictError(Exception):
    """Raised when an Idempotency-Key is reused with different request arguments."""


def canonical_arguments_hash(arguments: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 digest of canonicalized JSON arguments."""
    canonical_json = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class IdempotencyGuard:
    """Ensures exactly-once business execution per Idempotency-Key."""

    _global_lock = threading.RLock()

    def __init__(self, database: Database) -> None:
        self._database = database

    def execute_idempotent(
        self,
        idempotency_key: str,
        customer_id: str,
        arguments: dict[str, Any],
        operation: Callable[[], dict[str, Any]],
        resource_id_extractor: Callable[[dict[str, Any]], str] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        """Execute operation or return cached result if idempotency key was previously processed.

        Returns:
            tuple[dict[str, Any], bool]: (response_dict, was_cached)

        Raises:
            IdempotencyConflictError: If key was used with different arguments or customer.
        """
        current_hash = canonical_arguments_hash(arguments)

        with self._global_lock:
            with self._database.session() as session:
                repo = IdempotencyRepository(session)
                existing = repo.get(idempotency_key)

                if existing is not None:
                    # Validate customer and argument hash integrity
                    if existing.customer_id != customer_id or existing.request_hash != current_hash:
                        raise IdempotencyConflictError(
                            f"La Idempotency-Key '{idempotency_key}' ya fue utilizada previamente "
                            "con parámetros o cliente diferentes."
                        )

                    cached_data = json.loads(existing.response_data)
                    return cached_data, True

            # Key is new -> execute the underlying transactional write
            result_data = operation()
            resource_id = ""
            if resource_id_extractor:
                resource_id = resource_id_extractor(result_data)
            elif "service_request_id" in result_data:
                resource_id = result_data["service_request_id"]

            # Persist idempotency record
            with self._database.session() as session:
                repo = IdempotencyRepository(session)
                repo.save(
                    idempotency_key=idempotency_key,
                    customer_id=customer_id,
                    resource_id=resource_id,
                    request_hash=current_hash,
                    response_data=json.dumps(result_data, ensure_ascii=False),
                )
                session.commit()

            return result_data, False
