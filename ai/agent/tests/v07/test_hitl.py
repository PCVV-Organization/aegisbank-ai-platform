"""Unit tests for HITL approval manager and state machine."""

from __future__ import annotations

import pytest

from aegisbank_agent.hitl import (
    ApprovalNotFoundError,
    ApprovalStateError,
    ApprovalStatus,
    ArgumentTamperingError,
    CustomerMismatchError,
    HITLApprovalManager,
)


class TestHITLApprovalLifecycle:
    """Test standard approval lifecycle transitions."""

    def test_create_pending_request(self) -> None:
        mgr = HITLApprovalManager()
        req = mgr.create_request(
            tool_name="create_service_request",
            customer_id="CUST-0001",
            arguments={"category": "CLAIM", "description": "Cobro duplicado"},
        )
        assert req.status == ApprovalStatus.PENDING
        assert req.approval_id.startswith("APPR-")
        assert req.synthetic_customer_id == "CUST-0001"
        assert req.tool_name == "create_service_request"
        assert req.argument_hash != ""

    def test_approve_request(self) -> None:
        mgr = HITLApprovalManager()
        req = mgr.create_request(
            tool_name="create_service_request",
            customer_id="CUST-0001",
            arguments={"category": "CLAIM", "description": "Cobro duplicado"},
        )
        approved = mgr.approve(req.approval_id, reviewer_customer_id="CUST-0001")
        assert approved.status == ApprovalStatus.APPROVED
        assert approved.reviewed_at is not None

    def test_reject_request(self) -> None:
        mgr = HITLApprovalManager()
        req = mgr.create_request(
            tool_name="create_service_request",
            customer_id="CUST-0001",
            arguments={"category": "CLAIM", "description": "Cobro duplicado"},
        )
        rejected = mgr.reject(
            req.approval_id, reviewer_customer_id="CUST-0001", reason="No autorizado"
        )
        assert rejected.status == ApprovalStatus.REJECTED
        assert rejected.rejection_reason == "No autorizado"

    def test_verify_and_mark_executed(self) -> None:
        mgr = HITLApprovalManager()
        args = {"category": "CLAIM", "description": "Cobro duplicado"}
        req = mgr.create_request("create_service_request", "CUST-0001", args)
        mgr.approve(req.approval_id, "CUST-0001")

        executed = mgr.verify_and_mark_executed(
            approval_id=req.approval_id,
            customer_id="CUST-0001",
            arguments_to_execute=args,
            execution_result={"service_request_id": "SR-0001"},
        )
        assert executed.status == ApprovalStatus.EXECUTED
        assert executed.execution_result == {"service_request_id": "SR-0001"}


class TestHITLSecurityGuards:
    """Test security guards against tampering, replay, and cross-customer misuse."""

    def test_tampering_arguments_rejected(self) -> None:
        mgr = HITLApprovalManager()
        original_args = {"category": "CLAIM", "description": "Cobro duplicado"}
        req = mgr.create_request("create_service_request", "CUST-0001", original_args)
        mgr.approve(req.approval_id, "CUST-0001")

        tampered_args = {"category": "CLAIM", "description": "Cobro duplicado y transferir dinero"}
        with pytest.raises(ArgumentTamperingError):
            mgr.verify_and_mark_executed(
                approval_id=req.approval_id,
                customer_id="CUST-0001",
                arguments_to_execute=tampered_args,
                execution_result={"status": "FAKE"},
            )

        # Status should have switched to REJECTED
        post_req = mgr.get_request(req.approval_id)
        assert post_req.status == ApprovalStatus.REJECTED

    def test_replay_execution_blocked(self) -> None:
        mgr = HITLApprovalManager()
        args = {"category": "CLAIM", "description": "Cobro duplicado"}
        req = mgr.create_request("create_service_request", "CUST-0001", args)
        mgr.approve(req.approval_id, "CUST-0001")

        mgr.verify_and_mark_executed(
            approval_id=req.approval_id,
            customer_id="CUST-0001",
            arguments_to_execute=args,
            execution_result={"service_request_id": "SR-0001"},
        )

        with pytest.raises(ApprovalStateError, match="ya fue ejecutada"):
            mgr.verify_and_mark_executed(
                approval_id=req.approval_id,
                customer_id="CUST-0001",
                arguments_to_execute=args,
                execution_result={"service_request_id": "SR-0002"},
            )

    def test_cross_customer_approval_blocked(self) -> None:
        mgr = HITLApprovalManager()
        req = mgr.create_request("create_service_request", "CUST-0001", {"cat": "X"})
        with pytest.raises(CustomerMismatchError):
            mgr.approve(req.approval_id, reviewer_customer_id="CUST-0002")

    def test_cross_customer_execution_blocked(self) -> None:
        mgr = HITLApprovalManager()
        args = {"cat": "X"}
        req = mgr.create_request("create_service_request", "CUST-0001", args)
        mgr.approve(req.approval_id, "CUST-0001")
        with pytest.raises(CustomerMismatchError):
            mgr.verify_and_mark_executed(
                approval_id=req.approval_id,
                customer_id="CUST-0002",
                arguments_to_execute=args,
                execution_result={},
            )

    def test_nonexistent_approval_id_raises_error(self) -> None:
        mgr = HITLApprovalManager()
        with pytest.raises(ApprovalNotFoundError):
            mgr.get_request("APPR-NONEXISTENT")
