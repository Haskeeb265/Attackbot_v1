# tests/integration/test_infra_startup.py
"""
Integration test: verifies the shared DB layer can connect and run a basic query.
Requires DATABASE_URL environment variable pointing to a live PostgreSQL instance.

Skipped automatically if DATABASE_URL is not set (e.g. in unit-test-only CI runs).
"""
import os

import pytest
import pytest_asyncio

from backend.shared.db import check_db_health, get_session, init_db

# Skip entire module if no live DB is available
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping integration tests",
)


@pytest.fixture(autouse=True)
def setup_db():
    """Initialize the shared DB for each test."""
    database_url = os.environ["DATABASE_URL"]
    init_db(database_url)
    yield


class TestDatabaseConnectivity:
    @pytest.mark.asyncio
    async def test_db_health_returns_true(self):
        healthy = await check_db_health()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_get_session_executes_query(self):
        from sqlalchemy import text

        async with get_session() as session:
            result = await session.execute(text("SELECT 1 AS val"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_programs_table_exists(self):
        """Validates the 001 Alembic migration has been applied."""
        from sqlalchemy import text

        async with get_session() as session:
            result = await session.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'programs'"
                )
            )
            row = result.fetchone()
            assert row is not None, (
                "programs table not found — run: alembic upgrade head"
            )

    @pytest.mark.asyncio
    async def test_scans_table_exists(self):
        """Validates the 001 Alembic migration has been applied."""
        from sqlalchemy import text

        async with get_session() as session:
            result = await session.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'scans'"
                )
            )
            row = result.fetchone()
            assert row is not None, (
                "scans table not found — run: alembic upgrade head"
            )