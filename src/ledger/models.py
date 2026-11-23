"""SQLAlchemy tables for accounts and transactions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ledger.db import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    transactions: Mapped[list[Transaction]] = relationship(back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "date",
            "account_id",
            "description",
            "category",
            "amount",
            name="uq_transaction",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    # Money is Numeric/Decimal, never float.
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    account: Mapped[Account] = relationship(back_populates="transactions")
