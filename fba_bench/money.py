from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from typing import List, Union, Any
import re

# Currency minor units mapping (ISO 4217)
CURRENCY_UNITS = {
    'USD': 2,
    'EUR': 2,
    'GBP': 2,
    'JPY': 0,
    'CAD': 2,
    'AUD': 2,
    'CHF': 2,
    'CNY': 2,
    'SEK': 2,
    'NOK': 2,
    # Default to 2 for others
}

def get_minor_units(currency: str) -> int:
    """Get minor units for currency, default 2."""
    return CURRENCY_UNITS.get(currency.upper(), 2)

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        # Normalize currency
        currency = self.currency.upper()
        # Quantize amount
        units = get_minor_units(currency)
        quantize = Decimal('1.' + '0' * units)
        amount = self.amount.quantize(quantize, rounding=ROUND_HALF_EVEN)
        # Freeze with normalized values
        object.__setattr__(self, 'currency', currency)
        object.__setattr__(self, 'amount', amount)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Money:
        """Create Money from dict {'amount': str/Decimal, 'currency': str}."""
        amount = Decimal(str(d['amount']))
        currency = d.get('currency', 'USD')
        return cls(amount, currency)

    def to_dict(self) -> dict[str, Any]:
        """To dict for JSON serialization."""
        return {
            'amount': str(self.amount),
            'currency': self.currency
        }

    def to_decimal(self) -> Decimal:
        """Get amount as Decimal."""
        return self.amount

    @classmethod
    def zero(cls, currency: str = 'USD') -> Money:
        """Zero Money in given currency."""
        return cls(Decimal(0), currency)

    @classmethod
    def from_dollars(cls, amount: Union[str, float, int, Decimal], currency: str = 'USD') -> Money:
        """Create from dollars (or specified currency)."""
        if isinstance(amount, (float, int)):
            amount = Decimal(str(amount))
        elif isinstance(amount, str):
            amount = Decimal(amount)
        return cls(amount, currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"

    def __repr__(self) -> str:
        return f"Money('{self.amount}', '{self.currency}')"

    # Arithmetic
    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money) or self.currency != other.currency:
            raise ValueError("Cannot add Money of different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money) or self.currency != other.currency:
            raise ValueError("Cannot subtract Money of different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, other: Union[int, float, Decimal]) -> Money:
        if isinstance(other, (int, float)):
            other = Decimal(str(other))
        return Money(self.amount * other, self.currency)

    def __rmul__(self, other: Union[int, float, Decimal]) -> Money:
        return self.__mul__(other)

    def __truediv__(self, other: Union[int, float, Decimal]) -> Money:
        if other == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        if isinstance(other, (int, float)):
            other = Decimal(str(other))
        return Money(self.amount / other, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __abs__(self) -> Money:
        return Money(abs(self.amount), self.currency)

    # Comparisons (same currency only)
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money of different currencies")
        return self.amount == other.amount

    def __lt__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money of different currencies")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money of different currencies")
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money of different currencies")
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money of different currencies")
        return self.amount >= other.amount

    def allocate(self, ratios: List[Union[int, Decimal]], precision: int = 2) -> List[Money]:
        """
        Allocate this Money across ratios, handling remainder to preserve sum.
        ratios: list of int or Decimal weights
        Returns list of Money in same currency, sum equals self.
        """
        if not ratios:
            return []
        total_ratio = sum(Decimal(str(r)) if isinstance(r, int) else r for r in ratios)
        if total_ratio == 0:
            raise ValueError("Total ratio cannot be zero")
        result = []
        remainder = self.amount
        for i, ratio in enumerate(ratios):
            r = Decimal(str(ratio)) if isinstance(ratio, int) else ratio
            share = (r / total_ratio * self.amount).quantize(
                Decimal('1.' + '0' * precision), rounding=ROUND_HALF_EVEN
            )
            result.append(Money(share, self.currency))
            remainder -= share
        # Distribute remainder to last item
        if remainder != 0 and result:
            last = result[-1]
            result[-1] = Money(last.amount + remainder, self.currency)
        return result

def money(amount: Union[int, float, Decimal, str], currency: str = 'USD') -> Money:
    """Convenience factory."""
    if isinstance(amount, (int, float, str)):
        amount = Decimal(str(amount))
    return Money(amount, currency)

def parse_money(s: str) -> Money:
    """Parse 'USD 123.45' or '123.45 USD'."""
    s = s.strip()
    match = re.match(r'([A-Z]{3})\s+(.+)', s)
    if match:
        currency, amt_str = match.groups()
        return money(amt_str, currency)
    match = re.match(r'(.+)\s+([A-Z]{3})', s)
    if match:
        amt_str, currency = match.groups()
        return money(amt_str, currency)
    # Assume USD
    return money(s)

__all__ = ["Money", "money", "parse_money"]