"""Azure Cosmos DB NoSQL adapter and Change Feed processor for AegisBank AI Platform.

Provides partitioned document storage, point reads, parameterized queries,
TTL lifecycle management, and incremental Change Feed consumption.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import (
    CosmosResourceExistsError,
    CosmosResourceNotFoundError,
)

from .configuration.environment import resolve_runtime_environment

DEFAULT_COSMOS_ENDPOINT = "http://127.0.0.1:8081"
DEFAULT_COSMOS_KEY = (
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)
DEFAULT_DATABASE_NAME = "aegisbank"
DEFAULT_CONTAINER_NAME = "agent_events"


@dataclass
class CosmosRepository:
    """Canonical repository for Azure Cosmos DB NoSQL document and event storage."""

    endpoint: str | None = None
    credential: Any = None
    database_name: str = DEFAULT_DATABASE_NAME
    container_name: str = DEFAULT_CONTAINER_NAME
    partition_key_path: str = "/customer_id"

    def __post_init__(self) -> None:
        environment = resolve_runtime_environment()
        if self.endpoint is None:
            self.endpoint = os.getenv("COSMOS_ENDPOINT", DEFAULT_COSMOS_ENDPOINT)
        if self.credential is None:
            if environment.is_cloud:
                from azure.identity import DefaultAzureCredential

                self.credential = DefaultAzureCredential()
            else:
                self.credential = os.getenv("COSMOS_KEY", DEFAULT_COSMOS_KEY)
        self._client: CosmosClient | None = None
        self._db: Any = None
        self._container: Any = None

    def _get_client(self) -> CosmosClient:
        if not self.endpoint or not self.endpoint.strip():
            raise RuntimeError("COSMOS_ENDPOINT is required for Cosmos DB access")
        if self._client is None:
            self._client = CosmosClient(self.endpoint, credential=self.credential)
        return self._client

    def initialize(self, default_ttl: int | None = None) -> None:
        """Create database and container if they do not exist."""
        client = self._get_client()
        self._db = client.create_database_if_not_exists(id=self.database_name)

        container_kwargs: dict[str, Any] = {
            "id": self.container_name,
            "partition_key": PartitionKey(path=self.partition_key_path),
        }
        if default_ttl is not None:
            container_kwargs["default_ttl"] = default_ttl

        self._container = self._db.create_container_if_not_exists(**container_kwargs)

    @property
    def container(self) -> Any:
        if self._container is None:
            self.initialize()
        return self._container

    def create_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Create a new item in the container. Fails if item with same ID and PK exists."""
        if "id" not in item:
            raise ValueError("Item must contain an 'id' field")
        pk_field = self.partition_key_path.lstrip("/")
        if pk_field not in item:
            raise ValueError(f"Item must contain partition key field '{pk_field}'")

        try:
            return self.container.create_item(body=item)
        except CosmosResourceExistsError as err:
            raise ValueError(f"Item with id '{item['id']}' already exists") from err

    def read_item(self, item_id: str, partition_key: str) -> dict[str, Any]:
        """Point read by item ID and partition key (exact 1-hop physical lookup)."""
        if not item_id or not partition_key:
            raise ValueError("item_id and partition_key are required for point read")
        try:
            return self.container.read_item(item=item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError as err:
            raise KeyError(f"Item '{item_id}' not found in partition '{partition_key}'") from err

    def upsert_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Idempotent insert or replace of an item."""
        if "id" not in item:
            raise ValueError("Item must contain an 'id' field")
        pk_field = self.partition_key_path.lstrip("/")
        if pk_field not in item:
            raise ValueError(f"Item must contain partition key field '{pk_field}'")
        return self.container.upsert_item(body=item)

    def patch_item(
        self,
        item_id: str,
        partition_key: str,
        patch_operations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Apply partial document update (PATCH) by ID and partition key."""
        return self.container.patch_item(
            item=item_id,
            partition_key=partition_key,
            patch_operations=patch_operations,
        )

    def query_items(
        self,
        query: str,
        parameters: list[dict[str, Any]] | None = None,
        partition_key: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute parameterized SQL query within a partition or cross-partition."""
        query_kwargs: dict[str, Any] = {
            "query": query,
            "enable_cross_partition_query": partition_key is None,
        }
        if parameters:
            query_kwargs["parameters"] = parameters
        if partition_key:
            query_kwargs["partition_key"] = partition_key

        return list(self.container.query_items(**query_kwargs))

    def delete_item(self, item_id: str, partition_key: str) -> None:
        """Delete an item by ID and partition key."""
        try:
            self.container.delete_item(item=item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError:
            pass

    def read_change_feed(
        self,
        partition_key: str | None = None,
        continuation_token: str | None = None,
        max_item_count: int = 100,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Read incremental changes from the Change Feed."""
        feed_kwargs: dict[str, Any] = {
            "max_item_count": max_item_count,
        }
        if partition_key is not None:
            feed_kwargs["partition_key"] = partition_key
        if continuation_token is not None:
            feed_kwargs["continuation"] = continuation_token

        query_iterable = self.container.query_items_change_feed(**feed_kwargs)
        items = list(query_iterable)
        new_continuation = getattr(query_iterable, "continuation_token", None)
        return items, new_continuation


@dataclass
class CosmosChangeFeedProcessor:
    """Incremental Change Feed processor with checkpointing and idempotent execution."""

    repository: CosmosRepository
    checkpoint_token: str | None = None
    processed_count: int = 0
    _handlers: list[Callable[[dict[str, Any]], None]] = field(default_factory=list)
    _seen_ids: set[str] = field(default_factory=set)

    def register_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback handler for new or updated documents."""
        self._handlers.append(handler)

    def process_latest_changes(self, max_item_count: int = 100) -> int:
        """Poll and dispatch incremental changes to registered handlers."""
        items, next_token = self.repository.read_change_feed(
            continuation_token=self.checkpoint_token,
            max_item_count=max_item_count,
        )
        new_items_processed = 0
        for item in items:
            item_id = item.get("id", "")
            # Deduplicate by internal change / etag or item id
            etag = item.get("_etag", item_id)
            dedup_key = f"{item_id}:{etag}"
            if dedup_key in self._seen_ids:
                continue

            self._seen_ids.add(dedup_key)
            for handler in self._handlers:
                handler(item)
            new_items_processed += 1

        self.processed_count += new_items_processed
        if next_token:
            self.checkpoint_token = next_token
        return new_items_processed
