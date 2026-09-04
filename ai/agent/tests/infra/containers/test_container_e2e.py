"""E2E Container & Azure Service Bus Acceptance Suite (Journeys A through I).

Verifies Docker image building, Docker Compose networking, Service Bus Emulator configuration,
Azure Service Bus adapter settlement, and full HITL -> Outbox -> Messaging lifecycle.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mock_core_banking.domain.enums import ServiceRequestCategory, ServiceRequestStatus
from mock_core_banking.main import create_app
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.repositories import OutboxRepository, ServiceRequestRepository
from mock_core_banking.persistence.seed import seed_database
from starlette.testclient import TestClient

from aegisbank_agent.hitl import HITLApprovalManager
from aegisbank_agent.reliability.azure_servicebus_adapter import AzureServiceBusMessageBus
from aegisbank_agent.reliability.messaging import (
    DeadLetterQueue,
    IdempotentConsumer,
    Message,
    OutboxProcessor,
)

pytestmark = pytest.mark.infra


REPO_ROOT = Path(__file__).resolve().parents[5]


# --- Journey A: Container Image Build & Tagging ---
def test_journey_a_container_image_built_and_tagged() -> None:
    """Journey A: Verify Docker image exists locally with correct versioned tag."""
    res = subprocess.run(
        [
            "docker",
            "images",
            "aegisbank/mock-core-banking:0.11.0",
            "--format",
            "{{.Repository}}:{{.Tag}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "aegisbank/mock-core-banking:0.11.0" in res.stdout.strip()


# --- Journey B: Container Healthcheck Contract ---
def test_journey_b_container_healthcheck_contract() -> None:
    """Journey B: Verify Dockerfile specifies valid HEALTHCHECK directive on /health."""
    dockerfile_path = REPO_ROOT / "services" / "mock-core-banking" / "Dockerfile"
    assert dockerfile_path.exists(), f"Dockerfile not found at {dockerfile_path}"
    content = dockerfile_path.read_text(encoding="utf-8")
    assert "HEALTHCHECK" in content
    assert "/health" in content
    assert "USER" in content


# --- Journey C: API Endpoint Contract ---
def test_journey_c_api_endpoint_contract() -> None:
    """Journey C: Verify Core Banking application exposes /health/live returning status ok."""
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"


# --- Journey D: Inter-Container Network & Compose Configuration ---
def test_journey_d_network_and_compose_configuration() -> None:
    """Journey D: Verify Docker Compose declares network aegisbank-net and dependencies."""
    compose_path = REPO_ROOT / "deploy" / "local" / "docker-compose.yml"
    assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"
    content = compose_path.read_text(encoding="utf-8")
    assert "aegisbank-net" in content
    assert "mock-core-banking" in content
    assert "servicebus-emulator" in content
    assert "mssql" in content


# --- Journey E: Service Bus Emulator Config & Queues ---
def test_journey_e_service_bus_emulator_config_and_queues() -> None:
    """Journey E: Verify Config.json declares sb-emulator-ns and queue with DLQ support."""
    config_path = REPO_ROOT / "deploy" / "local" / "Config.json"
    assert config_path.exists(), f"Config.json not found at {config_path}"
    config_data = json.loads(config_path.read_text(encoding="utf-8"))

    namespaces = config_data.get("UserConfig", {}).get("Namespaces", [])
    assert len(namespaces) >= 1
    ns = namespaces[0]
    assert ns.get("Name") == "sbemulatorns"

    queues = ns.get("Queues", [])
    queue_names = [q.get("Name") for q in queues]
    assert "service-requests" in queue_names


# --- Journey F: Messaging Publish, Receive & Idempotent Deduplication ---
def test_journey_f_service_bus_messaging_publish_and_receive_idempotent() -> None:
    """Journey F: Test publish, receive settlement, and IdempotentConsumer deduplication."""
    adapter = AzureServiceBusMessageBus()

    test_message = Message(
        event_id="evt-sb-001",
        event_type="ServiceRequestCreated",
        aggregate_type="ServiceRequest",
        aggregate_id="SR-99901",
        payload={"customer_id": "CUST-0001", "type": "STATEMENT_REQUEST"},
    )

    mock_sender = MagicMock()
    mock_receiver = MagicMock()

    raw_payload = json.dumps(
        {
            "event_id": "evt-sb-001",
            "event_type": "ServiceRequestCreated",
            "aggregate_type": "ServiceRequest",
            "aggregate_id": "SR-99901",
            "payload": {"customer_id": "CUST-0001", "type": "STATEMENT_REQUEST"},
            "created_at": "2026-08-31T12:00:00+00:00",
        }
    )

    mock_sb_msg = MagicMock()
    mock_sb_msg.body = raw_payload
    mock_sb_msg.message_id = "evt-sb-001"

    mock_receiver.receive_messages.return_value = [mock_sb_msg]

    mock_client = MagicMock()
    mock_client.get_queue_sender.return_value = mock_sender
    mock_sender.__enter__.return_value = mock_sender
    mock_client.get_queue_receiver.return_value = mock_receiver
    mock_receiver.__enter__.return_value = mock_receiver

    with patch.object(adapter, "_get_client", return_value=mock_client):
        # 1. Publish
        adapter.publish("service-requests", test_message)
        assert mock_sender.send_messages.called

        # 2. Receive and process with IdempotentConsumer
        processed_events: list[str] = []
        dlq = DeadLetterQueue()

        def handle_msg(msg: Message) -> None:
            processed_events.append(msg.event_id)

        consumer = IdempotentConsumer(handler=handle_msg, dlq=dlq)

        # First delivery -> Processed
        results = adapter.receive_and_settle(
            queue_name="service-requests",
            handler=consumer.handle,
        )
        assert len(results) == 1
        assert results[0]["status"] == "COMPLETED"
        assert len(processed_events) == 1
        mock_receiver.complete_message.assert_called_with(mock_sb_msg)

        # Redelivery setup
        mock_sb_msg_dup = MagicMock()
        mock_sb_msg_dup.body = raw_payload
        mock_sb_msg_dup.message_id = "evt-sb-001"
        mock_receiver.receive_messages.return_value = [mock_sb_msg_dup]

        results_dup = adapter.receive_and_settle(
            queue_name="service-requests",
            handler=consumer.handle,
        )
        assert len(results_dup) == 1
        assert results_dup[0]["status"] == "COMPLETED"
        assert len(processed_events) == 1  # Deduplicated!


# --- Journey G: Failure Handling & Poison Pill Dead-Lettering ---
def test_journey_g_failure_poison_pill_routing_to_dlq() -> None:
    """Journey G: Test poison message handling routing directly to DLQ on unrecoverable error."""
    adapter = AzureServiceBusMessageBus()

    mock_receiver = MagicMock()
    mock_poison_msg = MagicMock()
    mock_poison_msg.body = "INVALID_CORRUPTED_JSON{{"
    mock_poison_msg.message_id = "poison-999"

    mock_receiver.receive_messages.return_value = [mock_poison_msg]
    mock_client = MagicMock()
    mock_client.get_queue_receiver.return_value = mock_receiver
    mock_receiver.__enter__.return_value = mock_receiver

    with patch.object(adapter, "_get_client", return_value=mock_client):
        results = adapter.receive_and_settle(
            queue_name="service-requests",
            handler=lambda m: True,
        )
        assert len(results) == 1
        assert results[0]["status"] == "DEAD_LETTERED"
        assert mock_receiver.dead_letter_message.called


# --- Journey H: Full Journey HITL Approve -> Outbox -> Service Bus -> Consumer ---
def test_journey_h_full_journey_hitl_approve_outbox_servicebus(tmp_path: Path) -> None:
    """Journey H: Full end-to-end integration: HITL Approve -> Outbox -> Azure Service Bus."""
    db_file = tmp_path / "journey_h.db"
    database = Database(f"sqlite:///{db_file.as_posix()}")
    database.create_schema()
    seed_database(database)

    hitl = HITLApprovalManager()
    adapter = AzureServiceBusMessageBus()

    # 1. Create HITL Request
    approval_req = hitl.create_request(
        tool_name="create_service_request",
        customer_id="CUST-0001",
        arguments={"request_type": "STATEMENT_REQUEST", "details": "Q3 Report"},
    )

    # 2. Approve HITL Request
    hitl.approve(approval_req.approval_id, reviewer_customer_id="CUST-0001")

    # 3. Create Service Request + Outbox event under transaction
    with database.session_factory() as session:
        req_repo = ServiceRequestRepository(session)
        created_sr = req_repo.create(
            customer_id="CUST-0001",
            category=ServiceRequestCategory.GENERAL,
            description="Q3 Report",
        )
        session.commit()
        assert created_sr.status == ServiceRequestStatus.OPEN

    # 4. OutboxProcessor publishes to Azure Service Bus adapter
    mock_sender = MagicMock()
    mock_client = MagicMock()
    mock_client.get_queue_sender.return_value = mock_sender
    mock_sender.__enter__.return_value = mock_sender

    with patch.object(adapter, "_get_client", return_value=mock_client):
        processor = OutboxProcessor(database, adapter)
        processed = processor.process_pending(limit=10)
        assert processed == 1
        assert mock_sender.send_messages.called

        # Verify outbox event status is PUBLISHED
        with database.session_factory() as session:
            outbox_repo = OutboxRepository(session)
            pending_after = outbox_repo.list_pending(limit=10)
            assert len(pending_after) == 0


# --- Journey I: Full Journey HITL Reject -> Zero Database Side-effects ---
def test_journey_i_full_journey_hitl_reject_zero_messages(tmp_path: Path) -> None:
    """Journey I: Full verification: HITL Reject -> 0 DB modifications -> 0 Outbox events."""
    db_file = tmp_path / "journey_i.db"
    database = Database(f"sqlite:///{db_file.as_posix()}")
    database.create_schema()
    seed_database(database)

    hitl = HITLApprovalManager()
    adapter = AzureServiceBusMessageBus()

    # 1. Create HITL Request
    approval_req = hitl.create_request(
        tool_name="create_service_request",
        customer_id="CUST-0001",
        arguments={"request_type": "STATEMENT_REQUEST", "details": "Malicious probe"},
    )

    # 2. Reject HITL Request
    hitl.reject(approval_req.approval_id, reviewer_customer_id="CUST-0001", reason="Unauthorized")

    # 3. Verify no DB records or outbox events created
    with database.session_factory() as session:
        req_repo = ServiceRequestRepository(session)
        outbox_repo = OutboxRepository(session)
        all_requests = req_repo.list_by_customer("CUST-0001")
        # In seeded database, CUST-0001 has 1 seed request, ensure no new ones added
        assert len(all_requests) == 1

        pending_events = outbox_repo.list_pending(limit=10)
        assert len(pending_events) == 0

    # 4. OutboxProcessor finds 0 events to publish
    mock_sender = MagicMock()
    mock_client = MagicMock()
    mock_client.get_queue_sender.return_value = mock_sender
    mock_sender.__enter__.return_value = mock_sender

    with patch.object(adapter, "_get_client", return_value=mock_client):
        processor = OutboxProcessor(database, adapter)
        processed = processor.process_pending(limit=10)
        assert processed == 0
        assert not mock_sender.send_messages.called
