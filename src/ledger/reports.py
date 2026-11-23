"""Read totals from the database."""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select

from ledger.models import Account, Transaction


def _all_transactions(session):
    return list(session.scalars(select(Transaction)).all())


def balance(session):
    """Total amount per account."""
    totals = defaultdict(Decimal)
    # Start with every account, even if it has no transactions yet.
    for account in session.scalars(select(Account)).all():
        totals[account.name] = Decimal("0.00")
    for tx in _all_transactions(session):
        totals[tx.account.name] += tx.amount
    return dict(sorted(totals.items()))


def spending(session):
    """Spending per category (outgoing amounts, transfers excluded)."""
    totals = defaultdict(Decimal)
    for tx in _all_transactions(session):
        if tx.amount < 0 and tx.category != "transfer":
            totals[tx.category] += tx.amount
    return dict(sorted(totals.items(), key=lambda item: item[1]))


def months(session):
    """Net total per calendar month."""
    totals = defaultdict(Decimal)
    for tx in _all_transactions(session):
        totals[tx.date.isoformat()[:7]] += tx.amount
    return dict(sorted(totals.items()))
