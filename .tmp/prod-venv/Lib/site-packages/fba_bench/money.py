from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Optional, Union

Number = Union[int, float, Decimal, str]

# Hard limit to prevent integer overflow and unrealistic values (in cents)
# Large enough for all tests and typical financial simulations.
MAX_MONEY_CENTS: int = 10**12  # +/- 10,000,000,000.00


def _normalize_currency(code: Optional[str]) -> str:
    code = (code or "USD").strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError(f"Invalid currency code: {code!r}")
    return code


def _to_decimal_safe(value: Number) -> Decimal:
    """
    Convert a numeric-like value to Decimal with string normalization to avoid float precision loss.
    """
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Invalid numeric value: {value!r}") from e


class Money:
    """
    Immutable-like money value object represented in integer cents for exact arithmetic.

    Core guarantees:
    - Constructor requires integer cents (floats rejected).
    - from_dollars accepts str|int|float|Decimal and rounds half-up to nearest cent.
    - Arithmetic preserves currency, rounding half-up when needed.
    - Comparison only allowed for same-currency values.
    """

    __slots__ = ("cents", "currency")

    cents: int
    currency: str

    def __init__(self, cents: int, currency: str = "USD") -> None:
        if not isinstance(cents, int):
            raise TypeError(
                "Float not allowed in Money constructor; pass integer cents or use Money.from_dollars()."
            )
        currency = _normalize_currency(currency)

        if abs(cents) > MAX_MONEY_CENTS:
            raise ValueError(f"Cents exceeds MAX_MONEY_CENTS ({MAX_MONEY_CENTS})")

        object.__setattr__(self, "cents", cents)
        object.__setattr__(self, "currency", currency)

    # -----------------------
    # Constructors / factories
    # -----------------------
    @classmethod
    def from_dollars(cls, dollars: Number, currency: str = "USD") -> Money:
        """
        Create Money from a dollar-denominated number-like value, rounding HALF_UP to cents.
        Examples:
          - "12.345" -> 1235 cents
          - Decimal("-12.345") -> -1235 cents
        """
        d = _to_decimal_safe(dollars)
        cents = int((d * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return cls(cents, currency)

    @classmethod
    def zero(cls, currency: str = "USD") -> Money:
        return cls(0, currency)

    # -----------------------
    # Conversions / formatting
    # -----------------------
    def to_decimal(self) -> Decimal:
        """
        Return Decimal dollars value quantized to 2 dp (nearest cent).
        """
        return (Decimal(self.cents) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def to_float(self) -> float:
        return float(self.to_decimal())

    def __str__(self) -> str:
        sign = "-" if self.cents < 0 else ""
        abs_cents = abs(self.cents)
        dollars = abs_cents // 100
        cents = abs_cents % 100
        return f"{sign}${dollars:,}.{cents:02d} {self.currency}"

    def __repr__(self) -> str:
        return f"Money(cents={self.cents}, currency='{self.currency}')"

    # --------------
    # Hash / equality
    # --------------
    def __hash__(self) -> int:
        return hash((self.cents, self.currency))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.cents == other.cents and self.currency == other.currency

    # -------------
    # Comparisons
    # -------------
    def _ensure_same_currency(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError("Operation requires Money")
        if self.currency != other.currency:
            raise TypeError("Cross-currency comparison is not supported")

    def __lt__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.cents < other.cents

    def __le__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.cents <= other.cents

    def __gt__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.cents > other.cents

    def __ge__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.cents >= other.cents

    # -------------
    # Unary ops
    # -------------
    def __neg__(self) -> Money:
        return Money(-self.cents, self.currency)

    def __pos__(self) -> Money:
        return self

    # -------------
    # Arithmetic
    # -------------
    def __add__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        total = self.cents + other.cents
        if abs(total) > MAX_MONEY_CENTS:
            raise ValueError("Result exceeds MAX_MONEY_CENTS")
        return Money(total, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        total = self.cents - other.cents
        if abs(total) > MAX_MONEY_CENTS:
            raise ValueError("Result exceeds MAX_MONEY_CENTS")
        return Money(total, self.currency)

    def _mul_div_common(self, factor: Number, *, is_div: bool = False) -> Money:
        d = _to_decimal_safe(factor)
        base = Decimal(self.cents)
        if is_div:
            if d == 0:
                raise ZeroDivisionError("division by zero")
            raw = base / d
        else:
            raw = base * d
        cents = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if abs(cents) > MAX_MONEY_CENTS:
            raise ValueError("Result exceeds MAX_MONEY_CENTS")
        return Money(cents, self.currency)

    def __mul__(self, other: Number) -> Money:
        if not isinstance(other, (int, float, Decimal, str)):
            return NotImplemented
        return self._mul_div_common(other, is_div=False)

    def __truediv__(self, other: Number) -> Money:
        if not isinstance(other, (int, float, Decimal, str)):
            return NotImplemented
        return self._mul_div_common(other, is_div=True)


# -----------------------
# Helpers / utilities
# -----------------------
def sum_money(items: Iterable[Money], currency: Optional[str] = None) -> Money:
    total = 0
    cur: Optional[str] = _normalize_currency(currency) if currency else None
    for m in items:
        if not isinstance(m, Money):
            raise TypeError("sum_money expects an iterable of Money")
        if cur is None:
            cur = m.currency
        elif m.currency != cur:
            raise TypeError("sum_money does not support cross-currency aggregation")
        total += m.cents
    return Money(total, cur or "USD")


def max_money(items: Sequence[Money]) -> Money:
    if not items:
        raise ValueError("max_money requires at least one element")
    # Relies on __lt__ enforcing same-currency
    cur = items[0].currency
    for m in items:
        if m.currency != cur:
            raise TypeError("max_money does not support cross-currency comparison")
    return max(items)


def min_money(items: Sequence[Money]) -> Money:
    if not items:
        raise ValueError("min_money requires at least one element")
    cur = items[0].currency
    for m in items:
        if m.currency != cur:
            raise TypeError("min_money does not support cross-currency comparison")
    return min(items)


# Common zero constants for convenience
USD_ZERO: Money = Money.zero("USD")
EUR_ZERO: Money = Money.zero("EUR")
GBP_ZERO: Money = Money.zero("GBP")

__all__ = [
    "Money",
    "MAX_MONEY_CENTS",
    "USD_ZERO",
    "EUR_ZERO",
    "GBP_ZERO",
    "sum_money",
    "max_money",
    "min_money",
]
