from decimal import Decimal

import pytest

from mock_core_banking.domain.money import (
    MoneyError,
    calculate_total_due,
    normalize_money,
    validate_loan_amounts,
)


def test_calculate_total_due_uses_decimal_components() -> None:
    result = calculate_total_due("833.33", "100.00", "5.00")
    assert result == Decimal("938.33")
    assert isinstance(result, Decimal)


@pytest.mark.parametrize("value", ["-0.01", Decimal("NaN"), Decimal("Infinity")])
def test_normalize_money_rejects_invalid_values(value: str | Decimal) -> None:
    with pytest.raises(MoneyError):
        normalize_money(value)


def test_normalize_money_rejects_float_input() -> None:
    with pytest.raises(MoneyError, match="Float"):
        normalize_money(0.1)  # type: ignore[arg-type]


def test_validate_loan_amounts_rejects_balance_above_principal() -> None:
    with pytest.raises(MoneyError, match="cannot exceed"):
        validate_loan_amounts(Decimal("100.00"), Decimal("100.01"))


def test_validate_loan_amounts_accepts_zero_balance() -> None:
    validate_loan_amounts(Decimal("100.00"), Decimal("0.00"))
