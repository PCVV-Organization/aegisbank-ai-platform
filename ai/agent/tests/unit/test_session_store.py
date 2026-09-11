"""Unit tests for SQLiteSessionStore and deterministic conversational memory."""

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.session_store import (
    OwnershipViolationError,
    SessionData,
    SQLiteSessionStore,
)
from aegisbank_agent.tools.registry import ToolRegistry


def test_session_store_create_and_retrieve(tmp_path):
    db_file = tmp_path / "sessions.db"
    store = SQLiteSessionStore(db_file)

    session = store.get_or_create("sess-1", "CUST-0001")
    assert session.session_id == "sess-1"
    assert session.customer_id == "CUST-0001"
    assert session.last_loan_id is None

    store.record_loan_access("sess-1", "CUST-0001", "LOAN-0001")
    reloaded = store.get_or_create("sess-1", "CUST-0001")
    assert reloaded.last_loan_id == "LOAN-0001"
    assert reloaded.last_intent == "GET_LOAN_DETAILS"


def test_session_store_ownership_boundary(tmp_path):
    db_file = tmp_path / "sessions.db"
    store = SQLiteSessionStore(db_file)

    store.get_or_create("sess-cust1", "CUST-0001")

    with pytest.raises(OwnershipViolationError, match="Cross-customer violation"):
        store.get_or_create("sess-cust1", "CUST-0002")


def test_session_store_update_ownership_check(tmp_path):
    db_file = tmp_path / "sessions.db"
    store = SQLiteSessionStore(db_file)

    store.get_or_create("sess-cust1", "CUST-0001")
    tampered = SessionData("sess-cust1", "CUST-0002", last_loan_id="LOAN-9999")

    with pytest.raises(OwnershipViolationError, match="Cross-customer mutation denied"):
        store.update(tampered)


def test_agent_anaphora_identity_resolution(tmp_path):
    db_file = tmp_path / "sessions.db"
    store = SQLiteSessionStore(db_file)
    registry = ToolRegistry(include_write_tools=False)

    orchestrator = AgentOrchestrator(
        registry=registry,
        session_store=store,
        client=object(),  # Dummy client; should not be called
    )

    # Turn 1: query explicit loan
    res1 = orchestrator.run(
        "Dame detalle de mi prestamo LOAN-0001",
        customer_id="CUST-0001",
        session_id="sess-test",
    )
    assert res1.success is True
    assert res1.rounds == 0

    # Turn 2: ask for the identity of the last loan
    res2 = orchestrator.run(
        "¿cual fue el ultimo prestamo por el que te consulte?",
        customer_id="CUST-0001",
        session_id="sess-test",
    )
    assert res2.success is True
    assert res2.rounds == 0
    assert len(res2.tool_calls) == 1
    assert res2.tool_calls[0].arguments == {"loan_id": "LOAN-0001"}
    assert "LOAN-0001" in res2.answer


def test_agent_anaphora_empty_session_clarification(tmp_path):
    db_file = tmp_path / "sessions.db"
    store = SQLiteSessionStore(db_file)
    registry = ToolRegistry(include_write_tools=False)

    orchestrator = AgentOrchestrator(
        registry=registry,
        session_store=store,
        client=object(),
    )

    res = orchestrator.run(
        "¿cual fue el ultimo prestamo?",
        customer_id="CUST-0001",
        session_id="sess-empty",
    )
    assert res.success is True
    assert res.rounds == 0
    assert "No tengo un préstamo previo registrado en esta sesión" in res.answer


def test_agent_cross_customer_session_denial(tmp_path):
    db_file = tmp_path / "sessions.db"
    store = SQLiteSessionStore(db_file)
    registry = ToolRegistry(include_write_tools=False)

    orchestrator = AgentOrchestrator(
        registry=registry,
        session_store=store,
        client=object(),
    )

    # Customer 1 initiates session
    orchestrator.run(
        "Dame detalle de mi prestamo LOAN-0001",
        customer_id="CUST-0001",
        session_id="shared-session",
    )

    # Customer 2 attempts to resume Customer 1's session
    res = orchestrator.run(
        "¿cual fue el ultimo prestamo?",
        customer_id="CUST-0002",
        session_id="shared-session",
    )
    assert res.success is False
    assert "No tienes acceso a esta sesión" in res.answer
