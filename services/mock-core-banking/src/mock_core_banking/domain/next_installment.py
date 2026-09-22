from collections.abc import Iterable
from datetime import date
from typing import Protocol, TypeVar

from sqlalchemy.orm import Mapped

from .enums import InstallmentStatus


class InstallmentCandidate(Protocol):
    @property
    def installment_id(self) -> str | Mapped[str]: ...

    @property
    def installment_number(self) -> int | Mapped[int]: ...

    @property
    def due_date(self) -> date | Mapped[date]: ...

    @property
    def status(self) -> InstallmentStatus | Mapped[InstallmentStatus]: ...


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
