from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from mock_core_banking.domain.enums import Currency, InstallmentStatus, LoanStatus
from mock_core_banking.persistence.models import Installment, Loan


def test_database_rejects_outstanding_balance_above_principal(database) -> None:
    invalid_loan = Loan(
        loan_id="LOAN-9998",
        customer_id="CUST-0001",
        product_code="INVALID_BALANCE_TEST",
        currency=Currency.PEN,
        principal_amount=Decimal("100.00"),
        outstanding_balance=Decimal("100.01"),
        status=LoanStatus.ACTIVE,
        opened_at=date(2026, 1, 1),
    )
    with database.session() as session:
        session.add(invalid_loan)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_database_rejects_inconsistent_installment_total(database) -> None:
    invalid_installment = Installment(
        installment_id="INST-9998",
        loan_id="LOAN-0001",
        installment_number=99,
        due_date=date(2026, 12, 1),
        principal_due=Decimal("100.00"),
        interest_due=Decimal("10.00"),
        fees_due=Decimal("1.00"),
        total_due=Decimal("999.00"),
        status=InstallmentStatus.PENDING,
    )
    with database.session() as session:
        session.add(invalid_installment)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
