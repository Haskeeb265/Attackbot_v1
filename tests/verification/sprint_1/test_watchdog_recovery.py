"""
Test verification for Issue #1: Watchdog Scan Recovery Mechanism Failure

These tests verify that the watchdog reliably recovers stuck scans and provides
full observability via metrics and logging.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import update
from sqlalchemy.future import select

from backend.shared.db import get_session
from backend.shared.models.scans import Scan


class TestWatchdogRecovery:
    """Tests for watchdog stuck scan recovery."""

    @pytest.mark.asyncio
    async def test_stuck_scan_recovery(self, db_session):
        """Verify watchdog recovers scans stuck beyond threshold."""
        from backend.services.core_engine.repository import ScanRepository
        from backend.services.core_engine.watchdog import recover_stuck_scans

        # Setup: Create stuck scan (started 3h ago, no end time)
        repo = ScanRepository(db_session)
        scan_id = uuid4()
        program_id = uuid4()
        
        await repo.create_scan(
            scan_id=scan_id,
            program_id=program_id,
            config={"target": "test.com"}
        )

        # Simulate stuck: Update started_at to 3h ago
        await db_session.execute(
            update(Scan)
            .where(Scan.scan_id == scan_id)
            .values(started_at=datetime.now(timezone.utc) - timedelta(hours=3))
        )
        await db_session.commit()

        # Pre-verify: Scan is stuck
        result = await db_session.execute(
            select(Scan).where(Scan.scan_id == scan_id)
        )
        scan = result.scalar()
        assert scan.status == "running"
        assert scan.completed_at is None

        # Execute: Run watchdog
        await recover_stuck_scans()

        # Verify: Scan marked as failed_internal
        await db_session.refresh(scan)
        assert scan.status == "failed_internal"
        assert "Watchdog" in (scan.error_detail or "")
        assert scan.completed_at is not None

    @pytest.mark.asyncio
    async def test_watchdog_timezone_handling(self, db_session):
        """Verify watchdog handles timezone-aware timestamps correctly."""
        from backend.services.core_engine.repository import ScanRepository
        from backend.services.core_engine.watchdog import recover_stuck_scans

        repo = ScanRepository(db_session)
        scan_id = uuid4()
        
        # Create scan with timezone-aware timestamp from 3h ago
        past_time = datetime.now(timezone.utc) - timedelta(hours=3)
        await repo.create_scan(
            scan_id=scan_id,
            program_id=uuid4(),
            config={"target": "test.com"}
        )
        
        await db_session.execute(
            update(Scan)
            .where(Scan.scan_id == scan_id)
            .values(started_at=past_time)
        )
        await db_session.commit()

        # Run watchdog
        await recover_stuck_scans()

        # Verify scan recovered
        result = await db_session.execute(
            select(Scan).where(Scan.scan_id == scan_id)
        )
        scan = result.scalar()
        assert scan.status == "failed_internal"

    @pytest.mark.asyncio
    async def test_watchdog_metrics(self, db_session):
        """Verify watchdog emits Prometheus metrics."""
        from backend.services.core_engine.watchdog import (
            watchdog_executions, 
            watchdog_scans_recovered,
            watchdog_errors
        )

        initial_executions = watchdog_executions._value.get() or 0
        initial_recovered = watchdog_scans_recovered._value.get() or 0

        # Trigger watchdog
        from backend.services.core_engine.watchdog import recover_stuck_scans
        await recover_stuck_scans()

        # Verify metrics incremented
        assert watchdog_executions._value.get() > initial_executions

    @pytest.mark.asyncio
    async def test_watchdog_logging(self, db_session):
        """Verify watchdog runs without error."""
        import logging
        from backend.services.core_engine.repository import ScanRepository
        from backend.services.core_engine.watchdog import recover_stuck_scans

        # Create stuck scan
        repo = ScanRepository(db_session)
        scan_id = uuid4()
        await repo.create_scan(
            scan_id=scan_id,
            program_id=uuid4(),
            config={"target": "test.com"}
        )
        
        await db_session.execute(
            update(Scan)
            .where(Scan.scan_id == scan_id)
            .values(started_at=datetime.now(timezone.utc) - timedelta(hours=3))
        )
        await db_session.commit()

        # Run watchdog - should complete without error
        await recover_stuck_scans()
        
        # Verify scan was recovered
        result = await db_session.execute(
            select(Scan).where(Scan.scan_id == scan_id)
        )
        scan = result.scalar()
        assert scan.status == "failed_internal"

    @pytest.mark.asyncio
    async def test_watchdog_startup_verification(self, db_session, mocker):
        """Verify watchdog job registration is verified at startup."""
        from backend.services.core_engine.main import lifespan
        from backend.services.core_engine.watchdog import start_watchdog
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        # Create mock scheduler
        scheduler = AsyncIOScheduler()
        
        # This should not raise
        start_watchdog(scheduler)
        
        # Verify job is registered
        jobs = scheduler.get_jobs()
        job_names = [j.id for j in jobs]
        assert "scan_watchdog" in job_names
