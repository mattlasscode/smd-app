"""SQLite engine and sessions for the ledger."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DB = "db.sqlite3"

_engine = None
_SessionFactory = None


class Base(DeclarativeBase):
    pass


def get_engine(path: str = DEFAULT_DB):
    """Create the engine once and reuse it."""
    global _engine, _SessionFactory
    if _engine is None:
        _engine = create_engine(f"sqlite:///{path}")
        _SessionFactory = sessionmaker(bind=_engine)
    return _engine


def init_db(path: str = DEFAULT_DB):
    """Create tables if they do not exist yet."""
    engine = get_engine(path)
    # Register models with Base.metadata before create_all.
    from ledger import models as _models  # noqa: F401

    Base.metadata.create_all(engine)
    return engine


def get_session() -> Session:
    if _SessionFactory is None:
        init_db()
    return _SessionFactory()
