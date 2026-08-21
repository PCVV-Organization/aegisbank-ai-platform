from typing import Annotated

from fastapi import APIRouter, Path

from ..domain.errors import InstallmentNotFoundError
from ..domain.next_installment import select_next_installment
from ..persistence.repositories import InstallmentRepository, LoanRepository
from ..schemas import ErrorEnvelope, InstallmentResponse, LoanResponse
from .dependencies import SessionDependency

router = APIRouter(prefix="/api/v1/loans", tags=["loans"])
LoanPath = Annotated[str, Path(pattern=r"^LOAN-[0-9]{4}$")]


@router.get(
    "/{loan_id}",
    response_model=LoanResponse,
    responses={
        404: {"model": ErrorEnvelope, "description": "Synthetic loan not found"},
        422: {"model": ErrorEnvelope, "description": "Path validation failed"},
    },
)
def get_loan(loan_id: LoanPath, session: SessionDependency) -> LoanResponse:
    loan = LoanRepository(session).get_by_id(loan_id)
    return LoanResponse.model_validate(loan)


@router.get(
    "/{loan_id}/installments/next",
    response_model=InstallmentResponse,
    responses={
        404: {"model": ErrorEnvelope, "description": "Loan or installment not found"},
        422: {"model": ErrorEnvelope, "description": "Path validation failed"},
    },
)
def get_next_installment(
    loan_id: LoanPath,
    session: SessionDependency,
) -> InstallmentResponse:
    LoanRepository(session).get_by_id(loan_id)
    installments = InstallmentRepository(session).list_by_loan(loan_id)
    installment = select_next_installment(installments)
    if installment is None:
        raise InstallmentNotFoundError()
    return InstallmentResponse.model_validate(installment)
