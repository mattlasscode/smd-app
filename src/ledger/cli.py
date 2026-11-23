"""Command line entry point for the ledger."""

import argparse
import sys

from rich.console import Console
from rich.table import Table

from ledger.db import get_session, init_db
from ledger.reports import balance, months, spending
from ledger.storage import add_transaction, import_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ledger",
        description="Personal finance ledger stored in SQLite.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="Load transactions from a CSV file")
    p_import.add_argument("file", nargs="?", default="data/transactions.csv")

    sub.add_parser("balance", help="Show the balance of each account")
    sub.add_parser("spending", help="Show spending by category")
    sub.add_parser("months", help="Show the net total for each month")

    p_add = sub.add_parser("add", help="Add one transaction")
    p_add.add_argument("account")
    p_add.add_argument("amount")
    p_add.add_argument("category")
    p_add.add_argument("description")
    p_add.add_argument(
        "--date",
        default=None,
        help="Date as YYYY-MM-DD (defaults to today)",
    )

    args = parser.parse_args()
    init_db()
    session = get_session()
    try:
        if args.command == "import":
            added = import_csv(session, args.file)
            print(f"Imported {added} new transaction(s) from {args.file}.")
        elif args.command == "balance":
            for account, total in balance(session).items():
                print(f"{account:<10} {total:>10}")
        elif args.command == "months":
            for month, total in months(session).items():
                print(f"{month:<10} {total:>10}")
        elif args.command == "spending":
            table = Table(title="Spending by category")
            table.add_column("Category")
            table.add_column("EUR", justify="right")
            for category, total in spending(session).items():
                table.add_row(category, f"{-total:,.2f}")
            Console().print(table)
        elif args.command == "add":
            add_transaction(
                session,
                args.account,
                args.amount,
                args.category,
                args.description,
                args.date,
            )
            print("Transaction added.")
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(exc, file=sys.stderr)
        session.rollback()
        raise SystemExit(1) from exc
    finally:
        session.close()
