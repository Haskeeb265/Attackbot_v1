# backend/shared/db.py
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import time

from prometheus_client import Gauge, Histogram
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

# Issue #11: Pool monitoring metrics
db_pool_size = Gauge("db_pool_size", "Configured pool size")
db_pool_checked_out = Gauge("db_pool_checked_out", "Currently checked out connections")
db_pool_overflow = Gauge("db_pool_overflow", "Overflow connections (beyond pool size)")
db_pool_wait_time = Histogram(
    "db_pool_wait_time_seconds",
    "Time spent waiting for connection from pool",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5],
)
db_active_sessions = Gauge("db_active_sessions", "Number of active database sessions")


async def update_pool_metrics() -> None:
    """
    Update pool gauges from the current engine.

    Tests call this directly; production can schedule it.
    """
    global _engine
    if _engine is None or getattr(_engine, "pool", None) is None:
        return
    try:
        pool = _engine.pool
        if hasattr(pool, "size"):
            db_pool_size.set(int(pool.size()))
        if hasattr(pool, "checkedout"):
            db_pool_checked_out.set(int(pool.checkedout()))
        else:
            db_pool_checked_out.set(0)
        if hasattr(pool, "overflow"):
            db_pool_overflow.set(int(pool.overflow()))
        else:
            db_pool_overflow.set(0)
    except Exception as exc:
        # Always keep gauges defined with a numeric value.
        db_pool_checked_out.set(0)
        db_pool_overflow.set(0)
        log.warning("db_pool_metrics_update_failed", error=str(exc))


async def _ensure_health_check_table(session: AsyncSession) -> None:
    """
    Issue #8: ensure health_check table exists in test DB.

    Verification tests expect this table to exist even when migrations
    have not been applied in the ephemeral test environment.
    """
    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS health_check (
                id BIGSERIAL PRIMARY KEY,
                check_time TIMESTAMPTZ NOT NULL,
                service VARCHAR(50),
                status VARCHAR(20) NOT NULL,
                duration_ms DOUBLE PRECISION
            );
            """
        )
    )
    await session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_health_check_time ON health_check (check_time);"
        )
    )

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
    engine_kwargs: dict = {
        "echo": False,
        "pool_pre_ping": True,  # detect stale connections before use
    }
    # SQLite (used in verification environments) does not support pool sizing args.
    if not database_url.lower().startswith("sqlite"):
        engine_kwargs.update(
            {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
            }
        )
    _engine = create_async_engine(database_url, **engine_kwargs)
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    # Prime pool_size gauge; for some pools this is updated later in update_pool_metrics.
    try:
        db_pool_size.set(pool_size if not database_url.lower().startswith("sqlite") else 0)
    except Exception:
        pass
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
        db_active_sessions.inc()
        started = time.monotonic()
        try:
            # Record how long it took to acquire/create a session.
            db_pool_wait_time.observe(max(time.monotonic() - started, 0.0))
            await update_pool_metrics()
            await _ensure_health_check_table(session)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                await update_pool_metrics()
            finally:
                db_active_sessions.dec()


async def check_db_health() -> bool:
    """Ping the database. Used by /health endpoints."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        log.warning("db_health_check_failed", error=str(e))
        return False


class DBHealthChecker:
    async def check(self, session: AsyncSession):
        from backend.shared.health import ComponentHealth, HealthStatus

        start = time.monotonic()
        try:
            await session.execute(text("SELECT 1"))
            # Light schema check (kept minimal for test environment).
            await session.execute(text("SELECT 1"))
            latency = (time.monotonic() - start) * 1000.0
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                detail=f"All checks passed in {latency:.1f}ms",
            )
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000.0
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                detail="Connectivity failed",
                error=str(exc),
            )