from collections.abc import Iterable
from datetime import date
from typing import Protocol, TypeVar

from .enums import InstallmentStatus


class InstallmentCandidate(Protocol):
    installment_id: str
    installment_number: int
    due_date: date
    status: InstallmentStatus


InstallmentType = TypeVar("InstallmentType", bound=InstallmentCandidate)


def select_next_installment(
    installments: Iterable[InstallmentType],
) -> InstallmentType | None:
    unpaid = (
        installment
        for installment in installments
        if installment.status in {InstallmentStatus.OVERDUE, InstallmentStatus.PENDING}
    )
    return min(
        unpaid,
        key=lambda installment: (
            installment.due_date,
            installment.installment_number,
            installment.installment_id,
        ),
        default=None,
    )
