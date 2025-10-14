from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from money import Money


class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


@dataclass
class Account:
    account_id: str
    name: str
    type: AccountType


@dataclass
class LedgerEntry:
    """
    Represents a single debit or credit entry.

    entry_type must be 'debit' or 'credit'.
    amount is a Money instance with currency preserved.
    """
    entry_id: str
    account_id: str
    amount: Money
    entry_type: str  # 'debit' | 'credit'
    description: str = ""

    def __post_init__(self) -> None:
        et = self.entry_type.lower().strip()
        if et not in ("debit", "credit"):
            raise ValueError(f"entry_type must be 'debit' or 'credit', got {self.entry_type!r}")
        # Normalize entry_type
        object.__setattr__(self, "entry_type", et)
        if not isinstance(self.amount, Money):
            raise TypeError("LedgerEntry.amount must be a Money instance")


class TransactionType(str, Enum):
    ADJUSTING_ENTRY = "adjusting_entry"
    JOURNAL_ENTRY = "journal_entry"


@dataclass
class Transaction:
    """
    A double-entry accounting transaction with balanced debits and credits.
    """
    transaction_id: str
    transaction_type: TransactionType
    description: str = ""
    debits: List[LedgerEntry] = field(default_factory=list)
    credits: List[LedgerEntry] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def total_debits(self) -> Money:
        if not self.debits:
            return Money.zero()
        total = self.debits[0].amount * 0
        for e in self.debits:
            total = total + e.amount
        return total

    def total_credits(self) -> Money:
        if not self.credits:
            return Money.zero()
        total = self.credits[0].amount * 0
        for e in self.credits:
            total = total + e.amount
        return total

    def is_balanced(self) -> bool:
        return self.total_debits().cents == self.total_credits().cents


@dataclass
class FinancialStatement:
    """
    Minimal financial statement placeholder to satisfy import surfaces.
    """
    transactions: List[Transaction] = field(default_factory=list)

    def totals(self) -> Dict[str, Money]:
        total_debits = Money.zero()
        total_credits = Money.zero()
        for t in self.transactions:
            total_debits = total_debits + t.total_debits()
            total_credits = total_credits + t.total_credits()
        return {"debits": total_debits, "credits": total_credits}


class DoubleEntryLedgerService:
    """
    Minimal, in-memory double-entry ledger service.

    Responsibilities:
    - Validate that posted transactions are balanced (debits == credits)
    - Preserve Money currency semantics
    - Store transactions in-memory for retrieval by tests/services
    """

    def __init__(self) -> None:
        self._transactions: List[Transaction] = []

    async def post_transaction(self, txn: Transaction) -> None:
        """
        Post a transaction after validating balance.

        Raises:
            ValueError: if debits and credits do not balance
            TypeError: if entries contain invalid types
        """
        if not isinstance(txn, Transaction):
            raise TypeError("txn must be a Transaction")
        # Validate all entries are Money and correctly typed
        for e in list(txn.debits) + list(txn.credits):
            if not isinstance(e, LedgerEntry):
                raise TypeError("All entries must be LedgerEntry instances")
            if not isinstance(e.amount, Money):
                raise TypeError("LedgerEntry.amount must be a Money instance")
            if e.entry_type not in ("debit", "credit"):
                raise ValueError("LedgerEntry.entry_type must be 'debit' or 'credit'")

        if not txn.is_balanced():
            raise ValueError(
                f"Unbalanced transaction: debits={txn.total_debits()} credits={txn.total_credits()}"
            )
        self._transactions.append(txn)

    def list_transactions(self) -> List[Transaction]:
        return list(self._transactions)

    def clear(self) -> None:
        self._transactions.clear()


__all__ = [
    "Account",
    "AccountType",
    "LedgerEntry",
    "Transaction",
    "TransactionType",
    "DoubleEntryLedgerService",
    "FinancialStatement",
]