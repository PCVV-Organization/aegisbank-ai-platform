from datetime import date, datetime, timezone
from decimal import Decimal

from ..domain.enums import (
    Currency,
    CustomerSegment,
    CustomerStatus,
    InstallmentStatus,
    LoanStatus,
    ServiceRequestCategory,
    ServiceRequestStatus,
)
from ..domain.money import calculate_total_due
from .database import Database
from .models import Customer, Installment, Loan, ServiceRequest

SEED_TIMESTAMP = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _installment(
    installment_id: str,
    loan_id: str,
    installment_number: int,
    due_date: date,
    principal_due: str,
    interest_due: str,
    fees_due: str,
    status: InstallmentStatus,
) -> Installment:
    return Installment(
        installment_id=installment_id,
        loan_id=loan_id,
        installment_number=installment_number,
        due_date=due_date,
        principal_due=Decimal(principal_due),
        interest_due=Decimal(interest_due),
        fees_due=Decimal(fees_due),
        total_due=calculate_total_due(principal_due, interest_due, fees_due),
        status=status,
    )


def build_seed_data() -> tuple[
    list[Customer],
    list[Loan],
    list[Installment],
    list[ServiceRequest],
]:
    customers = [
        Customer(
            customer_id="CUST-0001",
            display_name="Synthetic Customer 0001",
            segment=CustomerSegment.MICRO_BUSINESS,
            status=CustomerStatus.ACTIVE,
            created_at=SEED_TIMESTAMP,
        ),
        Customer(
            customer_id="CUST-0002",
            display_name="Synthetic Customer 0002",
            segment=CustomerSegment.SMALL_BUSINESS,
            status=CustomerStatus.ACTIVE,
            created_at=SEED_TIMESTAMP,
        ),
        Customer(
            customer_id="CUST-0003",
            display_name="Synthetic Customer 0003",
            segment=CustomerSegment.INDIVIDUAL,
            status=CustomerStatus.INACTIVE,
            created_at=SEED_TIMESTAMP,
        ),
    ]

    loans = [
        Loan(
            loan_id="LOAN-0001",
            customer_id="CUST-0001",
            product_code="WORKING_CAPITAL",
            currency=Currency.PEN,
            principal_amount=Decimal("10000.00"),
            outstanding_balance=Decimal("2800.00"),
            status=LoanStatus.DELINQUENT,
            opened_at=date(2026, 1, 1),
        ),
        Loan(
            loan_id="LOAN-0002",
            customer_id="CUST-0001",
            product_code="EQUIPMENT",
            currency=Currency.PEN,
            principal_amount=Decimal("5000.00"),
            outstanding_balance=Decimal("1750.00"),
            status=LoanStatus.ACTIVE,
            opened_at=date(2026, 1, 1),
        ),
        Loan(
            loan_id="LOAN-0003",
            customer_id="CUST-0002",
            product_code="BUSINESS_GROWTH",
            currency=Currency.PEN,
            principal_amount=Decimal("20000.00"),
            outstanding_balance=Decimal("18000.00"),
            status=LoanStatus.ACTIVE,
            opened_at=date(2026, 1, 1),
        ),
        Loan(
            loan_id="LOAN-0004",
            customer_id="CUST-0003",
            product_code="MICRO_LOAN",
            currency=Currency.PEN,
            principal_amount=Decimal("3000.00"),
            outstanding_balance=Decimal("0.00"),
            status=LoanStatus.CLOSED,
            opened_at=date(2025, 1, 1),
        ),
    ]

    installments = [
        _installment(
            "INST-0001",
            "LOAN-0001",
            1,
            date(2026, 2, 1),
            "833.33",
            "100.00",
            "0.00",
            InstallmentStatus.PAID,
        ),
        _installment(
            "INST-0002",
            "LOAN-0001",
            2,
            date(2026, 3, 1),
            "833.33",
            "100.00",
            "5.00",
            InstallmentStatus.OVERDUE,
        ),
        _installment(
            "INST-0003",
            "LOAN-0001",
            3,
            date(2026, 4, 1),
            "833.33",
            "100.00",
            "0.00",
            InstallmentStatus.PENDING,
        ),
        _installment(
            "INST-0004",
            "LOAN-0002",
            1,
            date(2026, 2, 1),
            "833.33",
            "41.67",
            "0.00",
            InstallmentStatus.PAID,
        ),
        _installment(
            "INST-0005",
            "LOAN-0002",
            2,
            date(2026, 3, 1),
            "833.33",
            "41.67",
            "0.00",
            InstallmentStatus.PENDING,
        ),
        _installment(
            "INST-0006",
            "LOAN-0003",
            1,
            date(2026, 2, 1),
            "833.33",
            "166.67",
            "0.00",
            InstallmentStatus.OVERDUE,
        ),
        _installment(
            "INST-0007",
            "LOAN-0003",
            2,
            date(2026, 3, 1),
            "833.33",
            "166.67",
            "0.00",
            InstallmentStatus.PENDING,
        ),
        _installment(
            "INST-0008",
            "LOAN-0003",
            3,
            date(2026, 4, 1),
            "833.33",
            "166.67",
            "0.00",
            InstallmentStatus.PENDING,
        ),
        _installment(
            "INST-0009",
            "LOAN-0004",
            1,
            date(2025, 2, 1),
            "1000.00",
            "20.00",
            "0.00",
            InstallmentStatus.PAID,
        ),
        _installment(
            "INST-0010",
            "LOAN-0004",
            2,
            date(2025, 3, 1),
            "1000.00",
            "20.00",
            "0.00",
            InstallmentStatus.PAID,
        ),
    ]

    service_requests = [
        ServiceRequest(
            service_request_id="SR-000001",
            customer_id="CUST-0001",
            category=ServiceRequestCategory.LOAN,
            description="Review the synthetic loan summary.",
            status=ServiceRequestStatus.OPEN,
            created_at=SEED_TIMESTAMP,
        ),
        ServiceRequest(
            service_request_id="SR-000002",
            customer_id="CUST-0002",
            category=ServiceRequestCategory.INSTALLMENT,
            description="Review the synthetic installment schedule.",
            status=ServiceRequestStatus.IN_REVIEW,
            created_at=SEED_TIMESTAMP,
        ),
    ]
    return customers, loans, installments, service_requests


def seed_database(database: Database) -> None:
    customers, loans, installments, service_requests = build_seed_data()

    with database.session_factory.begin() as session:
        for customer in customers:
            if session.get(Customer, customer.customer_id) is None:
                session.add(customer)
        session.flush()

        for loan in loans:
            if session.get(Loan, loan.loan_id) is None:
                session.add(loan)
        session.flush()

        for installment in installments:
            if session.get(Installment, installment.installment_id) is None:
                session.add(installment)
        session.flush()

        for service_request in service_requests:
            if session.get(ServiceRequest, service_request.service_request_id) is None:
                session.add(service_request)
