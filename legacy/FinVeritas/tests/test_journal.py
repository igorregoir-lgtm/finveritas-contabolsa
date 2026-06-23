import pytest
from decimal import Decimal

from src.domain.models.journal import Journal, create_entry, JournalLine, Account, AccountType


def test_double_entry_enforced():
    journal = Journal()
    cash = Account("1.1.01", "Caixa", AccountType.ASSET)
    revenue = Account("3.1.01", "Receita", AccountType.REVENUE)

    entry = create_entry("Venda", [
        JournalLine(cash, debit=Decimal("1000")),
        JournalLine(revenue, credit=Decimal("1000")),
    ])
    journal.append(entry)
    assert journal.entry_count == 1
    assert journal.trial_balance()["1.1.01"] == Decimal("1000")


def test_unbalanced_rejected():
    cash = Account("1.1.01", "Caixa", AccountType.ASSET)
    revenue = Account("3.1.01", "Receita", AccountType.REVENUE)

    with pytest.raises(ValueError, match="Double-entry violation"):
        create_entry("Ruim", [
            JournalLine(cash, debit=Decimal("100")),
            JournalLine(revenue, credit=Decimal("90")),
        ])


def test_immutable_append_only():
    journal = Journal()
    cash = Account("1.1.01", "Caixa", AccountType.ASSET)
    equity = Account("2.3.01", "Capital", AccountType.EQUITY)

    e1 = create_entry("Aporte", [JournalLine(cash, debit=Decimal("50000")), JournalLine(equity, credit=Decimal("50000"))])
    journal.append(e1)

    with pytest.raises(ValueError, match="Duplicate entry id"):
        journal.append(e1)
