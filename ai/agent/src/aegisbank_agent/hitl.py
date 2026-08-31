"""Human-in-the-Loop (HITL) approval state machine and management for AegisBank."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ApprovalStatus(Enum):
    """Lifecycle states for a human approval request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


class HITLError(Exception):
    """Base exception for HITL validation errors."""


class ApprovalNotFoundError(HITLError):
    """Raised when an approval ID does not exist."""


class CustomerMismatchError(HITLError):
    """Raised when an approval is accessed by a different customer."""


class ApprovalStateError(HITLError):
    """Raised when an approval is in an invalid state for the operation."""


class ArgumentTamperingError(HITLError):
    """Raised when normalized arguments do not match the approved proposal."""


def _canonical_json(data: dict[str, Any]) -> str:
    """Produce deterministic, sorted JSON representation for integrity comparison."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """Immutable snapshot of a state-changing operation proposal awaiting or completing review."""

    approval_id: str
    tool_name: str
    synthetic_customer_id: str
    normalized_arguments: dict[str, Any]
    status: ApprovalStatus
    created_at: datetime
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    execution_result: dict[str, Any] | None = None
    argument_hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.argument_hash:
            # Compute deterministic canonical hash
            canonical = _canonical_json(self.normalized_arguments)
            object.__setattr__(self, "argument_hash", canonical)

    def as_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "tool_name": self.tool_name,
            "synthetic_customer_id": self.synthetic_customer_id,
            "normalized_arguments": self.normalized_arguments,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "rejection_reason": self.rejection_reason,
            "execution_result": self.execution_result,
        }


class HITLApprovalManager:
    """Manages creation, review, and verification of human approval requests."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        tool_name: str,
        customer_id: str,
        arguments: dict[str, Any],
    ) -> ApprovalRequest:
        """Create a new PENDING approval request for a tool proposal."""
        approval_id = f"APPR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        req = ApprovalRequest(
            approval_id=approval_id,
            tool_name=tool_name,
            synthetic_customer_id=customer_id,
            normalized_arguments=arguments,
            status=ApprovalStatus.PENDING,
            created_at=now,
        )
        self._requests[approval_id] = req
        return req

    def get_request(self, approval_id: str) -> ApprovalRequest:
        """Retrieve an approval request by ID."""
        req = self._requests.get(approval_id)
        if req is None:
            raise ApprovalNotFoundError(f"Approval request '{approval_id}' no encontrado.")
        return req

    def approve(
        self,
        approval_id: str,
        reviewer_customer_id: str,
    ) -> ApprovalRequest:
        """Approve a pending request ensuring reviewer customer matches."""
        req = self.get_request(approval_id)
        if req.synthetic_customer_id != reviewer_customer_id:
            raise CustomerMismatchError(
                f"El cliente '{reviewer_customer_id}' no puede autorizar la solicitud "
                f"de '{req.synthetic_customer_id}'."
            )
        if req.status != ApprovalStatus.PENDING:
            raise ApprovalStateError(
                f"La solicitud '{approval_id}' está en estado '{req.status.value}' "
                "y no puede ser aprobada."
            )

        now = datetime.now(timezone.utc)
        approved_req = ApprovalRequest(
            approval_id=req.approval_id,
            tool_name=req.tool_name,
            synthetic_customer_id=req.synthetic_customer_id,
            normalized_arguments=req.normalized_arguments,
            status=ApprovalStatus.APPROVED,
            created_at=req.created_at,
            reviewed_at=now,
            argument_hash=req.argument_hash,
        )
        self._requests[approval_id] = approved_req
        return approved_req

    def reject(
        self,
        approval_id: str,
        reviewer_customer_id: str | None = None,
        reason: str = "Rechazado por el revisor humano",
    ) -> ApprovalRequest:
        """Reject a pending request."""
        req = self.get_request(approval_id)
        if reviewer_customer_id and req.synthetic_customer_id != reviewer_customer_id:
            raise CustomerMismatchError(
                f"El cliente '{reviewer_customer_id}' no puede rechazar la solicitud "
                f"de '{req.synthetic_customer_id}'."
            )
        if req.status != ApprovalStatus.PENDING:
            raise ApprovalStateError(
                f"La solicitud '{approval_id}' está en estado '{req.status.value}' "
                "y no puede ser rechazada."
            )

        now = datetime.now(timezone.utc)
        rejected_req = ApprovalRequest(
            approval_id=req.approval_id,
            tool_name=req.tool_name,
            synthetic_customer_id=req.synthetic_customer_id,
            normalized_arguments=req.normalized_arguments,
            status=ApprovalStatus.REJECTED,
            created_at=req.created_at,
            reviewed_at=now,
            rejection_reason=reason,
            argument_hash=req.argument_hash,
        )
        self._requests[approval_id] = rejected_req
        return rejected_req

    def verify_and_mark_executed(
        self,
        approval_id: str,
        customer_id: str,
        arguments_to_execute: dict[str, Any],
        execution_result: dict[str, Any],
    ) -> ApprovalRequest:
        """Verify approval validity, arguments integrity, and mark as EXECUTED."""
        req = self.get_request(approval_id)

        # 1. Customer verification
        if req.synthetic_customer_id != customer_id:
            raise CustomerMismatchError(
                f"El cliente '{customer_id}' no coincide con el solicitante "
                f"'{req.synthetic_customer_id}'."
            )

        # 2. State verification
        if req.status == ApprovalStatus.EXECUTED:
            raise ApprovalStateError(
                f"La solicitud '{approval_id}' ya fue ejecutada previamente. "
                "No se permite re-ejecución."
            )
        if req.status != ApprovalStatus.APPROVED:
            raise ApprovalStateError(
                f"La solicitud '{approval_id}' no ha sido aprobada "
                f"(estado actual: '{req.status.value}')."
            )

        # 3. Argument tampering verification
        exec_hash = _canonical_json(arguments_to_execute)
        if exec_hash != req.argument_hash:
            # Mark request as REJECTED due to tampering
            tampered_req = ApprovalRequest(
                approval_id=req.approval_id,
                tool_name=req.tool_name,
                synthetic_customer_id=req.synthetic_customer_id,
                normalized_arguments=req.normalized_arguments,
                status=ApprovalStatus.REJECTED,
                created_at=req.created_at,
                reviewed_at=datetime.now(timezone.utc),
                rejection_reason="Argumentos alterados con respecto a la propuesta aprobada",
                argument_hash=req.argument_hash,
            )
            self._requests[approval_id] = tampered_req
            raise ArgumentTamperingError(
                "Los argumentos enviados para ejecución no coinciden "
                "con la propuesta aprobada por el humano."
            )

        # 4. Mark as EXECUTED
        executed_req = ApprovalRequest(
            approval_id=req.approval_id,
            tool_name=req.tool_name,
            synthetic_customer_id=req.synthetic_customer_id,
            normalized_arguments=req.normalized_arguments,
            status=ApprovalStatus.EXECUTED,
            created_at=req.created_at,
            reviewed_at=req.reviewed_at,
            execution_result=execution_result,
            argument_hash=req.argument_hash,
        )
        self._requests[approval_id] = executed_req
        return executed_req
