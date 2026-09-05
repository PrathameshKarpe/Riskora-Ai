"""Database session management with per-URL engine caching.

Creates one engine (and therefore one connection pool) per unique DATABASE_URL
so that PostgreSQL connections are reused across requests instead of being
opened and closed on every call.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from .database import make_engine

# Module-level cache: url -> (engine, sessionmaker)
_factories: dict[str, sessionmaker] = {}


def make_session_factory(database_url: str) -> sessionmaker:
    """Return a cached sessionmaker for *database_url*."""
    if database_url not in _factories:
        engine = make_engine(database_url)
        _factories[database_url] = sessionmaker(
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
        )
    return _factories[database_url]


def get_db() -> Generator[Session, None, None]:
    from apps.api.app.core.config import settings

    session: Session = make_session_factory(settings.database_url)()
    try:
        yield session
    finally:
        session.close()
