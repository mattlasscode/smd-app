"""Load CSV files and add new transactions."""

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ledger.models import Account, Transaction


def parse_amount(text: str) -> Decimal:
    """Parse money as Decimal. Reject more than two decimal places."""
    try:
        amount = Decimal(str(text).strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount: {text}") from exc
    if amount.as_tuple().exponent < -2:
        raise ValueError("Amount can have at most two decimal places.")
    return amount


def parse_date(text: str) -> date:
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid date: {text}. Use YYYY-MM-DD.") from exc


def get_or_create_account(session, name: str) -> Account:
    account = session.scalar(select(Account).where(Account.name == name))
    if account is None:
        account = Account(name=name)
        session.add(account)
        session.flush()
    return account


def get_account(session, name: str) -> Account:
    account = session.scalar(select(Account).where(Account.name == name))
    if account is None:
        raise ValueError(
            f"Unknown account: {name}. Import the CSV first, or use an existing name."
        )
    return account


def import_csv(session, path: str) -> int:
    """Insert rows from a CSV file. Skip rows that are already in the database."""
    added = 0
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        account = get_or_create_account(session, row["account"].strip())
        amount = parse_amount(row["amount"])
        tx_date = parse_date(row["date"])
        description = row["description"].strip()
        category = row["category"].strip()
        exists = session.scalar(
            select(Transaction).where(
                Transaction.date == tx_date,
                Transaction.account_id == account.id,
                Transaction.description == description,
                Transaction.category == category,
                Transaction.amount == amount,
            )
        )
        if exists is not None:
            continue
        session.add(
            Transaction(
                date=tx_date,
                account=account,
                description=description,
                category=category,
                amount=amount,
            )
        )
        added += 1
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    return added


def add_transaction(
    session, account_name, amount_text, category, description, date_text=None
):
    """Add one transaction after checking the account and the amount."""
    account = get_account(session, account_name)
    amount = parse_amount(amount_text)
    tx_date = parse_date(date_text) if date_text else date.today()
    session.add(
        Transaction(
            date=tx_date,
            account=account,
            description=description,
            category=category,
            amount=amount,
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("That transaction is already in the database.") from exc
