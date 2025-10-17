from decimal import Decimal

import pytest
from fba_bench.money import MAX_MONEY_CENTS, Money


def test_negative_constructor_allows_negative_cents():
    m = Money(-500, "USD")
    assert m.cents == -500
    assert m.currency == "USD"


def test_from_dollars_negative_string_and_decimal():
    m1 = Money.from_dollars("-5.00", "USD")
    assert m1.cents == -500

    m2 = Money.from_dollars(Decimal("-12.345"), "USD")
    # Decimal("-12.345") -> -1234.5 cents -> rounded (ROUND_HALF_UP) to -1235
    assert m2.cents == -1235


def test_negation_and_arithmetic_with_negative_values():
    neg = Money(-200, "USD")
    pos = Money(500, "USD")
    total = pos + neg
    assert total.cents == 300
    assert (-neg).cents == 200


def test_overflow_protection_on_large_negative_values():
    big = -(MAX_MONEY_CENTS + 1)
    with pytest.raises(ValueError):
        Money(big, "USD")
