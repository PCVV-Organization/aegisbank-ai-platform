"""Low-cost, customer-partitioned durable conversation storage."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .cosmos import CosmosRepository


class ConversationStore:
    """Stores chat turns in Cosmos with point-readable customer partitions."""

    def __init__(self, repository: CosmosRepository | None = None) -> None:
        self._repository = repository or CosmosRepository(
            endpoint=os.getenv("CONVERSATION_COSMOS_ENDPOINT")
            or os.getenv("AEGISBANK_AUTH_COSMOS_ENDPOINT")
            or os.getenv("COSMOS_ENDPOINT"),
            database_name=os.getenv("CONVERSATION_COSMOS_DATABASE", "aegisbank-chat"),
            container_name=os.getenv("CONVERSATION_COSMOS_CONTAINER", "messages"),
            partition_key_path="/customer_id",
        )
        self._ttl = int(os.getenv("CONVERSATION_TTL_SECONDS", "2592000"))

    @property
    def repository(self) -> CosmosRepository:
        return self._repository

    def ready(self) -> None:
        self._repository.initialize(default_ttl=self._ttl)

    def append_turn(
        self,
        *,
        customer_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Unsupported conversation role")
        if not content or len(content) > 20000:
            raise ValueError("Conversation content is invalid")
        if not customer_id or not session_id:
            raise ValueError("Conversation ownership fields are required")
        self._repository.create_item(
            {
                "id": f"turn:{session_id}:{uuid.uuid4().hex}",
                "customer_id": customer_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ttl": self._ttl,
            }
        )

    def list_sessions(self, customer_id: str, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 50))
        items = self._repository.query_items(
            "SELECT c.session_id, MAX(c.created_at) AS updated_at, COUNT(1) AS turn_count "
            "FROM c WHERE c.customer_id = @customer_id GROUP BY c.session_id",
            [{"name": "@customer_id", "value": customer_id}],
            partition_key=customer_id,
        )
        return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)[:safe_limit]

    def get_session(self, customer_id: str, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        items = self._repository.query_items(
            "SELECT c.session_id, c.role, c.content, c.created_at FROM c "
            "WHERE c.customer_id = @customer_id AND c.session_id = @session_id "
            "ORDER BY c.created_at ASC",
            [
                {"name": "@customer_id", "value": customer_id},
                {"name": "@session_id", "value": session_id},
            ],
            partition_key=customer_id,
        )
        return items[:safe_limit]
