from __future__ import annotations

from typing import Iterable

from money import Money

from . import LedgerEntry, Transaction


def sum_entries(entries: Iterable[LedgerEntry]) -> Money:
    """
    Sum Money amounts across a list of ledger entries.
    Returns Money(0) when the list is empty.
    """
    entries = list(entries)
    if not entries:
        return Money.zero()
    total = entries[0].amount * 0  # preserve currency via zeroed Money
    for e in entries:
        if not isinstance(e.amount, Money):
            raise TypeError("LedgerEntry.amount must be a Money instance")
        total = total + e.amount
    return total


def is_balanced(txn: Transaction) -> bool:
    """
    Return True if the transaction's debits equal credits by cents.
    """
    if not isinstance(txn, Transaction):
        raise TypeError("txn must be a Transaction")
    return txn.is_balanced()


def to_cents(m: Money) -> int:
    """
    Utility to read Money's smallest unit for comparisons.
    """
    if not isinstance(m, Money):
        raise TypeError("m must be a Money instance")
    return m.cents


__all__ = ["sum_entries", "is_balanced", "to_cents"]