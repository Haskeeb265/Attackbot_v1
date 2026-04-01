# backend/shared/db.py
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.shared.logging import get_logger

log = get_logger(__name__)


class Base(DeclarativeBase):
    """All SQLAlchemy ORM models inherit from this."""

    pass


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
) -> None:
    """
    Call once at service startup.
    Creates the async engine and session factory.
    """
    global _engine, _session_factory
    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=False,
        pool_pre_ping=True,  # detect stale connections before use
    )
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    log.info("db_initialized", pool_size=pool_size, max_overflow=max_overflow)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_session() as session:
            result = await session.execute(...)
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_health() -> bool:
    """Ping the database. Used by /health endpoints."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        log.warning("db_health_check_failed", error=str(e))
        return False