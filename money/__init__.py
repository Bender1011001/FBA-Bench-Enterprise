from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Union

# Import canonical implementation
from fba_bench.money import Money as BaseMoney, money as base_money, parse_money as base_parse_money
from fba_bench.money import get_minor_units


@dataclass(frozen=True)
class Money:
    """
    Compatibility Money that preserves the fba_bench.money API and adds:
    - Single-argument constructor treated as "cents" (USD by default): Money(1234) -> $12.34
    - .cents property (int) for legacy code
    - .to_float() helper for code expecting a float representation
    Arithmetic and comparisons delegate to the underlying BaseMoney using the same currency.
    """
    _m: BaseMoney

    # Flexible constructor
    def __init__(self, amount: Union[int, float, Decimal, str], currency: str = "USD") -> None:
        object.__setattr__(self, "_m", self._coerce(amount, currency))

    @staticmethod
    def _coerce(amount: Union[int, float, Decimal, str], currency: str) -> BaseMoney:
        # If currency provided explicitly and amount is a string/number, treat as "dollars" value
        # If currency is not provided by callers (legacy one-arg style), we interpret amount as cents.
        # We detect this by seeing if currency is provided by the call site: our __init__ always has currency,
        # so we accept single-arg call via positional and currency defaulted to "USD".
        if isinstance(amount, Money):
            return amount._m
        # Heuristic: numeric and caller passed only one positional -> treat as cents if currency is default
        # We can't see arg count directly, so support both:
        # - If amount is int and no decimal point: treat as cents
        # - If amount is Decimal/float/str and caller intended cents explicitly, they should use from_cents
        if isinstance(amount, int):
            # cents -> dollars
            return BaseMoney.from_dollars(Decimal(amount) / Decimal(10 ** get_minor_units(currency)), currency)
        if isinstance(amount, float):
            # Floats treated as dollars to preserve precision expectation in new API
            return BaseMoney.from_dollars(Decimal(str(amount)), currency)
        if isinstance(amount, Decimal):
            # Decimal treated as dollars
            return BaseMoney.from_dollars(amount, currency)
        if isinstance(amount, str):
            # If string looks like integer, assume dollars (consistent with BaseMoney.from_dollars)
            return BaseMoney.from_dollars(amount, currency)
        # Fallback
        return BaseMoney.from_dollars(Decimal(0), currency)

    # Alternate constructors
    @classmethod
    def zero(cls, currency: str = "USD") -> Money:
        return cls(BaseMoney.zero(currency).amount, currency)

    @classmethod
    def from_dollars(cls, amount: Union[str, float, int, Decimal], currency: str = "USD") -> Money:
        if isinstance(amount, (float, int)):
            amount = Decimal(str(amount))
        elif isinstance(amount, str):
            amount = Decimal(amount)
        return cls(BaseMoney.from_dollars(amount, currency).amount, currency)

    @classmethod
    def from_cents(cls, cents: int, currency: str = "USD") -> Money:
        return cls(BaseMoney.from_dollars(Decimal(cents) / Decimal(10 ** get_minor_units(currency)), currency).amount, currency)

    # Expose selected BaseMoney attributes
    @property
    def amount(self) -> Decimal:
        return self._m.amount

    @property
    def currency(self) -> str:
        return self._m.currency

    @property
    def cents(self) -> int:
        units = get_minor_units(self.currency)
        return int((self.amount * (Decimal(10) ** units)).to_integral_value())

    def to_decimal(self) -> Decimal:
        return self._m.to_decimal()

    def to_float(self) -> float:
        return float(self.amount)

    # Dunder arithmetic (return Money of same currency)
    def __add__(self, other: Any) -> Money:
        if isinstance(other, Money):
            bm = self._m + other._m
            return Money(bm.amount, bm.currency)
        raise TypeError("Can only add Money to Money")

    def __sub__(self, other: Any) -> Money:
        if isinstance(other, Money):
            bm = self._m - other._m
            return Money(bm.amount, bm.currency)
        raise TypeError("Can only subtract Money from Money")

    def __mul__(self, other: Union[int, float, Decimal]) -> Money:
        bm = self._m * (Decimal(str(other)) if isinstance(other, (int, float)) else other)
        return Money(bm.amount, bm.currency)

    def __rmul__(self, other: Union[int, float, Decimal]) -> Money:
        return self.__mul__(other)

    def __truediv__(self, other: Union[int, float, Decimal]) -> Money:
        bm = self._m / (Decimal(str(other)) if isinstance(other, (int, float)) else other)
        return Money(bm.amount, bm.currency)

    def __neg__(self) -> Money:
        bm = -self._m
        return Money(bm.amount, bm.currency)

    def __abs__(self) -> Money:
        bm = abs(self._m)
        return Money(bm.amount, bm.currency)

    # Comparisons
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._m == other._m

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._m < other._m

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._m <= other._m

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._m > other._m

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._m >= other._m

    # String representations
    def __str__(self) -> str:
        return str(self._m)

    def __repr__(self) -> str:
        return f"Money('{self.amount}', '{self.currency}')"


# Backwards-compatible factory functions returning compatibility Money
def money(amount: Union[int, float, Decimal, str], currency: str = "USD") -> Money:
    return Money(amount, currency)


def parse_money(s: str) -> Money:
    bm = base_parse_money(s)
    return Money(bm.amount, bm.currency)


__all__ = ["Money", "money", "parse_money"]