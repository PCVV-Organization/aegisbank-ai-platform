from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

CENT = Decimal("0.01")


class MoneyError(ValueError):
    pass


def normalize_money(value: Decimal | str | int) -> Decimal:
    if isinstance(value, float):
        raise MoneyError("Float values are not accepted for money.")

    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, str):
        try:
            amount = Decimal(value)
        except InvalidOperation as exc:
            raise MoneyError("Money must be a valid decimal value.") from exc
    else:
        amount = Decimal(value)

    if not amount.is_finite():
        raise MoneyError("Money must be finite.")
    if amount < 0:
        raise MoneyError("Money cannot be negative.")

    return amount.quantize(CENT, rounding=ROUND_HALF_EVEN)


def calculate_total_due(
    principal_due: Decimal | str | int,
    interest_due: Decimal | str | int,
    fees_due: Decimal | str | int,
) -> Decimal:
    components = (
        normalize_money(principal_due),
        normalize_money(interest_due),
        normalize_money(fees_due),
    )
    return sum(components, start=Decimal("0.00")).quantize(CENT, rounding=ROUND_HALF_EVEN)


def validate_loan_amounts(principal_amount: Decimal, outstanding_balance: Decimal) -> None:
    principal = normalize_money(principal_amount)
    balance = normalize_money(outstanding_balance)
    if balance > principal:
        raise MoneyError("Outstanding balance cannot exceed principal amount.")
