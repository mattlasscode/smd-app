# smd-app

Personal finance ledger for the command line: balances, spending and monthly reports, stored in a SQLite database.

## Run it

    uv run ledger import
    uv run ledger balance
    uv run ledger spending
    uv run ledger months
    uv run ledger add checking -12.50 restaurants "Lunch"

Amounts are stored as Decimal values (NUMERIC), never as floats. `import` loads `data/transactions.csv` by default and skips rows that are already in the database.

## Roadmap

- A web API and a dashboard

## Author

mattlasscode - Matthieu Lassiouve
