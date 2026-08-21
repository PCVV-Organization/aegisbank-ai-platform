from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.enums import ServiceRequestCategory, ServiceRequestStatus
from ..domain.errors import (
    CustomerNotFoundError,
    LoanNotFoundError,
    ServiceRequestNotFoundError,
)
from .models import Customer, Installment, Loan, ServiceRequest


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
            self._session.execute(
                select(Loan).where(Loan.customer_id == customer_id).order_by(Loan.loan_id)
            )
            .scalars()
            .all()
        )


class InstallmentRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_by_loan(self, loan_id: str) -> list[Installment]:
        return list(
            self._session.execute(
                select(Installment)
                .where(Installment.loan_id == loan_id)
                .order_by(
                    Installment.due_date,
                    Installment.installment_number,
                    Installment.installment_id,
                )
            )
            .scalars()
            .all()
        )


class ServiceRequestRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, service_request_id: str) -> ServiceRequest:
        result = self._session.get(ServiceRequest, service_request_id)
        if not result:
            raise ServiceRequestNotFoundError()
        return result

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
        self._session.flush()
        return sr
