from dataclasses import dataclass
from datetime import date

from mock_core_banking.domain.enums import InstallmentStatus
from mock_core_banking.domain.next_installment import select_next_installment


@dataclass(frozen=True)
class Candidate:
    installment_id: str
    installment_number: int
    due_date: date
    status: InstallmentStatus


def test_next_installment_excludes_paid_and_uses_earliest_due_date() -> None:
    installments = [
        Candidate("INST-0001", 1, date(2026, 1, 1), InstallmentStatus.PAID),
        Candidate("INST-0002", 2, date(2026, 3, 1), InstallmentStatus.OVERDUE),
        Candidate("INST-0003", 3, date(2026, 2, 1), InstallmentStatus.PENDING),
    ]

    result = select_next_installment(installments)

    assert result is not None
    assert result.installment_id == "INST-0003"


def test_next_installment_uses_number_then_id_as_tie_breakers() -> None:
    installments = [
        Candidate("INST-0003", 3, date(2026, 2, 1), InstallmentStatus.PENDING),
        Candidate("INST-0002", 2, date(2026, 2, 1), InstallmentStatus.OVERDUE),
        Candidate("INST-0001", 2, date(2026, 2, 1), InstallmentStatus.PENDING),
    ]

    result = select_next_installment(installments)

    assert result is not None
    assert result.installment_id == "INST-0001"


def test_next_installment_returns_none_when_every_installment_is_paid() -> None:
    installments = [
        Candidate("INST-0001", 1, date(2026, 1, 1), InstallmentStatus.PAID),
    ]
    assert select_next_installment(installments) is None
