from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ..domain.enums import (
    Currency,
    CustomerSegment,
    CustomerStatus,
    InstallmentStatus,
    LoanStatus,
    ServiceRequestCategory,
    ServiceRequestStatus,
)

CustomerId = Annotated[str, Field(pattern=r"^CUST-[0-9]{4}$")]
LoanId = Annotated[str, Field(pattern=r"^LOAN-[0-9]{4}$")]
InstallmentId = Annotated[str, Field(pattern=r"^INST-[0-9]{4}$")]
ServiceRequestId = Annotated[str, Field(pattern=r"^SR-[0-9]{6}$")]
MoneyAmount = Annotated[
    Decimal,
    Field(ge=Decimal("0.00"), max_digits=18, decimal_places=2),
]
Description = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OrmResponseModel(ApiModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class CustomerResponse(OrmResponseModel):
    customer_id: CustomerId
    display_name: str
    segment: CustomerSegment
    status: CustomerStatus
    created_at: datetime


class LoanResponse(OrmResponseModel):
    loan_id: LoanId
    customer_id: CustomerId
    product_code: str
    currency: Currency
    principal_amount: MoneyAmount
    outstanding_balance: MoneyAmount
    status: LoanStatus
    opened_at: date


class InstallmentResponse(OrmResponseModel):
    installment_id: InstallmentId
    loan_id: LoanId
    installment_number: int = Field(gt=0)
    due_date: date
    principal_due: MoneyAmount
    interest_due: MoneyAmount
    fees_due: MoneyAmount
    total_due: MoneyAmount
    status: InstallmentStatus


class ServiceRequestCreate(ApiModel):
    customer_id: CustomerId
    category: ServiceRequestCategory
    description: Description


class ServiceRequestResponse(OrmResponseModel):
    service_request_id: ServiceRequestId
    customer_id: CustomerId
    category: ServiceRequestCategory
    description: str
    status: ServiceRequestStatus
    created_at: datetime


class HealthResponse(ApiModel):
    status: Literal["ok"]
    service: Literal["aegisbank-mock-core"]
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")


class ErrorDetail(ApiModel):
    code: str
    message: str
    correlation_id: str


class ErrorEnvelope(ApiModel):
    error: ErrorDetail
