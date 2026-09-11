"""Regression tests for structured conversational session state."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.session_store import OwnershipViolationError, SQLiteSessionStore

pytestmark = pytest.mark.unit


def test_last_loan_reference_survives_separate_orchestrator_instances(
    tool_registry,
) -> None:
    store = SQLiteSessionStore(":memory:")
    first = AgentOrchestrator(client=MagicMock(), registry=tool_registry, session_store=store)

    initial = first.run(
        "Dame detalle de mi prestamo LOAN-0001",
        customer_id="CUST-0001",
        session_id="SESSION-A",
    )
    assert initial.success
    assert initial.rounds == 0

    second = AgentOrchestrator(client=MagicMock(), registry=tool_registry, session_store=store)
    follow_up = second.run(
        "¿Cuál fue el último préstamo que te consulté?",
        customer_id="CUST-0001",
        session_id="SESSION-A",
    )

    assert follow_up.success
    assert follow_up.rounds == 0
    assert follow_up.tool_calls[0].arguments == {"loan_id": "LOAN-0001"}
    second._client.chat.completions.create.assert_not_called()


def test_last_loan_reference_without_history_asks_for_identifier(tool_registry) -> None:
    client = MagicMock()
    result = AgentOrchestrator(
        client=client,
        registry=tool_registry,
        session_store=SQLiteSessionStore(":memory:"),
    ).run(
        "¿Cuál fue el último préstamo que te consulté?",
        customer_id="CUST-0001",
        session_id="SESSION-EMPTY",
    )

    assert result.success
    assert result.rounds == 0
    assert "No tengo un préstamo previo" in result.answer
    client.chat.completions.create.assert_not_called()


def test_session_store_rejects_cross_customer_resume() -> None:
    store = SQLiteSessionStore(":memory:")
    store.get_or_create("SESSION-A", "CUST-0001")

    with pytest.raises(OwnershipViolationError):
        store.get_or_create("SESSION-A", "CUST-0002")
