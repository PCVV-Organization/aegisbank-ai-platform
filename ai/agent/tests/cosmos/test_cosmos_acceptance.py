"""Integration and acceptance tests for Azure Cosmos DB NoSQL adapter and Change Feed."""

from __future__ import annotations

import time
import urllib.request

import pytest

from aegisbank_agent.cosmos import (
    DEFAULT_COSMOS_KEY,
    CosmosChangeFeedProcessor,
    CosmosRepository,
)


def _has_cosmos_emulator() -> bool:
    """Helper to detect if Cosmos DB Emulator vNext is active locally."""
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8080/ready", timeout=1)
        return req.status == 200
    except Exception:
        return False


def test_cosmos_unavailable_endpoint_raises_error() -> None:
    """Verify invalid endpoint raises controlled RuntimeError or ConnectionError."""
    bad_repo = CosmosRepository(endpoint="http://127.0.0.1:58999", credential=DEFAULT_COSMOS_KEY)
    with pytest.raises(Exception):
        bad_repo.initialize()


def test_cosmos_missing_id_or_pk_raises_value_error() -> None:
    """Verify item validation raises ValueError when id or partition key is missing."""
    repo = CosmosRepository()
    with pytest.raises(ValueError, match="must contain an 'id' field"):
        repo.create_item({"customer_id": "CUST-001", "body": "test"})

    with pytest.raises(ValueError, match="must contain partition key field"):
        repo.create_item({"id": "evt_001", "body": "test"})


@pytest.mark.skipif(not _has_cosmos_emulator(), reason="Cosmos DB Emulator is not available")
def test_cosmos_crud_and_point_reads() -> None:
    """Verify CRUD lifecycle, point reads, patch, parameterized queries, and delete."""
    repo = CosmosRepository(
        database_name="aegisbank_test",
        container_name="test_crud_items",
        partition_key_path="/customer_id",
    )
    repo.initialize()

    item_id = f"evt_crud_{int(time.time() * 1000)}"
    cust_id = "CUST-101"
    item = {
        "id": item_id,
        "customer_id": cust_id,
        "schema_version": "1.0",
        "event_type": "loan_consultation",
        "correlation_id": "corr-101",
        "timestamp_utc": "2026-09-01T03:00:00Z",
        "payload": {"amount": 5000, "status": "draft"},
    }

    # 1. Create
    created = repo.create_item(item)
    assert created["id"] == item_id

    # Duplicate create fails
    with pytest.raises(ValueError, match="already exists"):
        repo.create_item(item)

    # 2. Point Read
    read_item = repo.read_item(item_id, partition_key=cust_id)
    assert read_item["id"] == item_id
    assert read_item["payload"]["amount"] == 5000

    # 3. Upsert
    item["payload"]["amount"] = 7500
    upserted = repo.upsert_item(item)
    assert upserted["payload"]["amount"] == 7500

    # 4. Patch
    patch_ops = [{"op": "replace", "path": "/payload/status", "value": "submitted"}]
    patched = repo.patch_item(item_id, partition_key=cust_id, patch_operations=patch_ops)
    assert patched["payload"]["status"] == "submitted"

    # 5. Query
    query = "SELECT * FROM c WHERE c.customer_id = @cust AND c.payload.status = @stat"
    params = [
        {"name": "@cust", "value": cust_id},
        {"name": "@stat", "value": "submitted"},
    ]
    results = repo.query_items(query, parameters=params, partition_key=cust_id)
    assert len(results) >= 1
    assert results[0]["id"] == item_id

    # 6. Delete
    repo.delete_item(item_id, partition_key=cust_id)
    with pytest.raises(KeyError):
        repo.read_item(item_id, partition_key=cust_id)


@pytest.mark.skipif(not _has_cosmos_emulator(), reason="Cosmos DB Emulator is not available")
def test_cosmos_partitioning_isolation() -> None:
    """Verify logical partition isolation: point reads with wrong partition key fail."""
    repo = CosmosRepository(
        database_name="aegisbank_test",
        container_name="test_partition_isolation",
        partition_key_path="/customer_id",
    )
    repo.initialize()

    item_id = f"evt_iso_{int(time.time() * 1000)}"
    repo.create_item(
        {
            "id": item_id,
            "customer_id": "CUST-AAA",
            "schema_version": "1.0",
            "event_type": "security_alert",
            "correlation_id": "corr-aaa",
            "timestamp_utc": "2026-09-01T03:00:00Z",
            "payload": {"data": "A"},
        }
    )

    # Point read with correct partition key succeeds
    assert repo.read_item(item_id, partition_key="CUST-AAA")["id"] == item_id

    # Point read with wrong partition key fails
    with pytest.raises(KeyError):
        repo.read_item(item_id, partition_key="CUST-BBB")


@pytest.mark.skipif(not _has_cosmos_emulator(), reason="Cosmos DB Emulator is not available")
def test_cosmos_ttl_expiration() -> None:
    """Verify item expiration using Cosmos DB TTL (Time-To-Live)."""
    repo = CosmosRepository(
        database_name="aegisbank_test",
        container_name="test_ttl_items",
        partition_key_path="/customer_id",
    )
    # Enable TTL on container
    repo.initialize(default_ttl=-1)

    item_id = f"evt_ttl_{int(time.time() * 1000)}"
    cust_id = "CUST-TTL"
    repo.create_item(
        {
            "id": item_id,
            "customer_id": cust_id,
            "schema_version": "1.0",
            "event_type": "ephemeral_session_token",
            "correlation_id": "corr-ttl",
            "timestamp_utc": "2026-09-01T03:00:00Z",
            "payload": {"token": "temp_xyz"},
            "ttl": 2,  # 2 seconds TTL
        }
    )

    # Visible immediately
    assert repo.read_item(item_id, partition_key=cust_id)["id"] == item_id

    # Wait for TTL expiration
    time.sleep(4)

    # Item expired (either not found or filtered)
    with pytest.raises(KeyError):
        repo.read_item(item_id, partition_key=cust_id)


@pytest.mark.skipif(not _has_cosmos_emulator(), reason="Cosmos DB Emulator is not available")
def test_cosmos_change_feed_and_idempotent_processor() -> None:
    """Verify incremental Change Feed reading, checkpointing, and idempotent event dispatch."""
    repo = CosmosRepository(
        database_name="aegisbank_test",
        container_name="test_change_feed_items",
        partition_key_path="/customer_id",
    )
    repo.initialize()

    processor = CosmosChangeFeedProcessor(repository=repo)
    observed_events: list[dict] = []
    processor.register_handler(lambda evt: observed_events.append(evt))

    # Initial poll to advance continuation token
    processor.process_latest_changes()

    # 1. Create item -> observe via Change Feed
    item_id = f"evt_cf_{int(time.time() * 1000)}"
    cust_id = "CUST-CF"
    repo.create_item(
        {
            "id": item_id,
            "customer_id": cust_id,
            "schema_version": "1.0",
            "event_type": "claim_drafted",
            "correlation_id": "corr-cf-1",
            "timestamp_utc": "2026-09-01T03:00:00Z",
            "payload": {"claim_id": "CLM-001", "status": "draft"},
        }
    )

    count_1 = processor.process_latest_changes()
    assert count_1 >= 1
    assert any(e["id"] == item_id for e in observed_events)

    # 2. Update item -> observe update via Change Feed
    repo.upsert_item(
        {
            "id": item_id,
            "customer_id": cust_id,
            "schema_version": "1.0",
            "event_type": "claim_drafted",
            "correlation_id": "corr-cf-1",
            "timestamp_utc": "2026-09-01T03:01:00Z",
            "payload": {"claim_id": "CLM-001", "status": "approved"},
        }
    )

    count_2 = processor.process_latest_changes()
    assert count_2 >= 1
    approved_events = [
        e
        for e in observed_events
        if e["id"] == item_id and e.get("payload", {}).get("status") == "approved"
    ]
    assert len(approved_events) >= 1

    # 3. Reprocess without new changes -> idempotent 0 new processed items
    count_3 = processor.process_latest_changes()
    assert count_3 == 0
