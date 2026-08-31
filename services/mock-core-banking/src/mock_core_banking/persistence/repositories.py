from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.enums import ServiceRequestCategory, ServiceRequestStatus
from ..domain.errors import (
    CustomerNotFoundError,
    LoanNotFoundError,
    ServiceRequestNotFoundError,
)
from .models import (
    Customer,
    IdempotencyRecord,
    Installment,
    Loan,
    OutboxEvent,
    ServiceRequest,
)


class CustomerRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, customer_id: str) -> Customer:
        result = self._session.get(Customer, customer_id)
        if not result:
            raise CustomerNotFoundError()
        return result


class LoanRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, loan_id: str) -> Loan:
        result = self._session.get(Loan, loan_id)
        if not result:
            raise LoanNotFoundError()
        return result

    def list_by_customer(self, customer_id: str) -> list[Loan]:
        return list(
            self._session.scalars(
                select(Loan).where(Loan.customer_id == customer_id).order_by(Loan.opened_at.asc())
            ).all()
        )


class InstallmentRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_by_loan(self, loan_id: str) -> list[Installment]:
        return list(
            self._session.scalars(
                select(Installment)
                .where(Installment.loan_id == loan_id)
                .order_by(Installment.installment_number.asc())
            ).all()
        )


class ServiceRequestRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, service_request_id: str) -> ServiceRequest:
        result = self._session.get(ServiceRequest, service_request_id)
        if not result:
            raise ServiceRequestNotFoundError()
        return result

    def list_by_customer(self, customer_id: str) -> list[ServiceRequest]:
        return list(
            self._session.scalars(
                select(ServiceRequest)
                .where(ServiceRequest.customer_id == customer_id)
                .order_by(ServiceRequest.created_at.asc())
            ).all()
        )

    def create(
        self,
        customer_id: str,
        category: ServiceRequestCategory,
        description: str,
    ) -> ServiceRequest:
        latest_id = self._session.scalar(
            select(ServiceRequest.service_request_id)
            .where(ServiceRequest.service_request_id.like("SR-%"))
            .order_by(ServiceRequest.service_request_id.desc())
            .limit(1)
        )
        next_num = int(latest_id.removeprefix("SR-")) + 1 if latest_id else 1
        new_id = f"SR-{next_num:06d}"

        now = datetime.now(timezone.utc)
        sr = ServiceRequest(
            service_request_id=new_id,
            customer_id=customer_id,
            category=category,
            description=description,
            status=ServiceRequestStatus.OPEN,
            created_at=now,
        )
        self._session.add(sr)

        # Transactional Outbox: record event atomically with state mutation
        cat_str = category.value if hasattr(category, "value") else str(category)
        outbox_event = OutboxEvent(
            event_id=f"EVT-{new_id}",
            event_type="ServiceRequestCreated",
            aggregate_type="service_request",
            aggregate_id=new_id,
            payload=json.dumps(
                {
                    "service_request_id": new_id,
                    "customer_id": customer_id,
                    "category": cat_str,
                    "description": description,
                    "status": sr.status.value,
                    "created_at": now.isoformat(),
                },
                ensure_ascii=False,
            ),
            status="PENDING",
            created_at=now,
        )
        self._session.add(outbox_event)
        self._session.flush()
        return sr


class IdempotencyRepository:
    """Repository for persisting and retrieving idempotency records."""

    def __init__(self, session: Session):
        self._session = session

    def get(self, idempotency_key: str) -> IdempotencyRecord | None:
        return self._session.get(IdempotencyRecord, idempotency_key)

    def save(
        self,
        idempotency_key: str,
        customer_id: str,
        resource_id: str,
        request_hash: str,
        response_data: str,
    ) -> IdempotencyRecord:
        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            customer_id=customer_id,
            resource_id=resource_id,
            request_hash=request_hash,
            response_data=response_data,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        self._session.flush()
        return record


class OutboxRepository:
    """Repository for transactional outbox pattern event processing."""

    def __init__(self, session: Session):
        self._session = session

    def save_event(
        self,
        event_id: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: str,
    ) -> OutboxEvent:
        event = OutboxEvent(
            event_id=event_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(event)
        self._session.flush()
        return event

    def list_pending(self, limit: int = 50) -> list[OutboxEvent]:
        return list(
            self._session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.status == "PENDING")
                .order_by(OutboxEvent.created_at.asc())
                .limit(limit)
            ).all()
        )

    def mark_published(self, event_id: str) -> OutboxEvent | None:
        event = self._session.get(OutboxEvent, event_id)
        if event:
            event.status = "PUBLISHED"
            event.published_at = datetime.now(timezone.utc)
            self._session.flush()
        return event
