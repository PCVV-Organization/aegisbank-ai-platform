from typing import Annotated

from fastapi import APIRouter, Path

from ..persistence.repositories import CustomerRepository, LoanRepository
from ..schemas import CustomerResponse, ErrorEnvelope, LoanResponse
from .dependencies import SessionDependency

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])
CustomerPath = Annotated[str, Path(pattern=r"^CUST-[0-9]{4}$")]


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    responses={
        404: {"model": ErrorEnvelope, "description": "Synthetic customer not found"},
        422: {"model": ErrorEnvelope, "description": "Path validation failed"},
    },
)
def get_customer(customer_id: CustomerPath, session: SessionDependency) -> CustomerResponse:
    customer = CustomerRepository(session).get_by_id(customer_id)
    return CustomerResponse.model_validate(customer)


@router.get(
    "/{customer_id}/loans",
    response_model=list[LoanResponse],
    responses={
        404: {"model": ErrorEnvelope, "description": "Synthetic customer not found"},
        422: {"model": ErrorEnvelope, "description": "Path validation failed"},
    },
)
def get_customer_loans(
    customer_id: CustomerPath,
    session: SessionDependency,
) -> list[LoanResponse]:
    CustomerRepository(session).get_by_id(customer_id)
    loans = LoanRepository(session).list_by_customer(customer_id)
    return [LoanResponse.model_validate(loan) for loan in loans]
