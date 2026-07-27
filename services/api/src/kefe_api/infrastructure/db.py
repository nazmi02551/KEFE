from __future__ import annotations

from sqlalchemy import Engine, create_engine


def build_engine(database_url: str) -> Engine:
    """Create the PostgreSQL engine without leaking SQLAlchemy into domain modules."""

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        future=True,
    )
