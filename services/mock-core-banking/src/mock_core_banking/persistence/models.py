from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..domain.enums import (
    Currency,
    CustomerSegment,
    CustomerStatus,
    InstallmentStatus,
    LoanStatus,
    ServiceRequestCategory,
    ServiceRequestStatus,
)
from .base import Base
from .types import UTCDateTime


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    segment: Mapped[CustomerSegment] = mapped_column(
        Enum(CustomerSegment, native_enum=False, create_constraint=True), nullable=False
    )
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, native_enum=False, create_constraint=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("principal_amount >= 0", name="ck_loan_principal_nonnegative"),
        CheckConstraint("outstanding_balance >= 0", name="ck_loan_outstanding_nonnegative"),
        CheckConstraint(
            "outstanding_balance <= principal_amount",
            name="ck_loan_outstanding_not_above_principal",
        ),
    )

    loan_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("customers.customer_id"), nullable=False, index=True
    )
    product_code: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, native_enum=False, create_constraint=True), nullable=False
    )
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, native_enum=False, create_constraint=True), nullable=False
    )
    opened_at: Mapped[date] = mapped_column(Date, nullable=False)


class Installment(Base):
    __tablename__ = "installments"
    __table_args__ = (
        UniqueConstraint("loan_id", "installment_number", name="uq_installment_loan_number"),
        CheckConstraint("installment_number > 0", name="ck_installment_number_positive"),
        CheckConstraint("principal_due >= 0", name="ck_installment_principal_nonnegative"),
        CheckConstraint("interest_due >= 0", name="ck_installment_interest_nonnegative"),
        CheckConstraint("fees_due >= 0", name="ck_installment_fees_nonnegative"),
        CheckConstraint(
            "total_due = principal_due + interest_due + fees_due",
            name="ck_installment_total_matches_components",
        ),
    )

    installment_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    loan_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("loans.loan_id"), nullable=False, index=True
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    interest_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fees_due: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    total_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[InstallmentStatus] = mapped_column(
        Enum(InstallmentStatus, native_enum=False, create_constraint=True), nullable=False
    )


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    __table_args__ = (
        CheckConstraint("length(trim(description)) > 0", name="ck_service_request_description"),
    )

    service_request_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("customers.customer_id"), nullable=False, index=True
    )
    category: Mapped[ServiceRequestCategory] = mapped_column(
        Enum(ServiceRequestCategory, native_enum=False, create_constraint=True), nullable=False
    )
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[ServiceRequestStatus] = mapped_column(
        Enum(ServiceRequestStatus, native_enum=False, create_constraint=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
