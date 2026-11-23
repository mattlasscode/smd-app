"""Short checks for parsing, CSV import, and the reports."""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from ledger.db import Base
from ledger.models import Transaction
from ledger.reports import balance, months, spending
from ledger.storage import import_csv, parse_amount, parse_date


def _session(tmp_path):
    # A throwaway file database. Each connection keeps the same tables.
    engine = create_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_parse_amount_accepts_two_decimals():
    assert parse_amount("12.50") == Decimal("12.50")
    assert parse_amount("-3.40") == Decimal("-3.40")


def test_parse_amount_rejects_three_decimals():
    with pytest.raises(ValueError):
        parse_amount("12.345")


def test_parse_date_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_date("15/01/2026")


def test_import_csv_skips_duplicates(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "date,account,description,category,amount\n"
        "2026-01-02,checking,Coffee,restaurants,-3.50\n"
        "2026-02-02,savings,Interest,interest,1.00\n",
        encoding="utf-8",
    )
    session = _session(tmp_path)
    # The second import finds the same rows and adds nothing.
    assert import_csv(session, str(csv_path)) == 2
    assert import_csv(session, str(csv_path)) == 0
    count = len(session.scalars(select(Transaction)).all())
    assert count == 2
    session.close()


def test_reports_return_decimal_totals(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "date,account,description,category,amount\n"
        "2026-01-15,checking,Lunch,restaurants,-12.50\n"
        "2026-01-20,checking,Salary,income,100.00\n"
        "2026-01-28,checking,To savings,transfer,-30.00\n"
        "2026-01-28,savings,From checking,transfer,30.00\n"
        "2026-02-01,checking,Rent,housing,-40.00\n",
        encoding="utf-8",
    )
    session = _session(tmp_path)
    import_csv(session, str(csv_path))

    balances = balance(session)
    assert balances["checking"] == Decimal("17.50")
    assert balances["savings"] == Decimal("30.00")
    assert all(isinstance(total, Decimal) for total in balances.values())

    spent = spending(session)
    # Transfers are not spending. Totals stay negative Decimals.
    assert spent["housing"] == Decimal("-40.00")
    assert spent["restaurants"] == Decimal("-12.50")
    assert "transfer" not in spent
    assert all(isinstance(total, Decimal) for total in spent.values())

    by_month = months(session)
    assert by_month["2026-01"] == Decimal("87.50")
    assert by_month["2026-02"] == Decimal("-40.00")
    assert all(isinstance(total, Decimal) for total in by_month.values())
    session.close()
