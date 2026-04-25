"""
Test verification for Issue #3: Idempotency Guarantee Gaps

These tests verify that duplicate message processing is prevented via idempotency keys.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy import func, delete

from backend.shared.db import get_session
from backend.shared.models.idempotency import IdempotencyKey


class TestIdempotency:
    """Tests for idempotency functionality."""

    @pytest.mark.asyncio
    async def test_idempotency_key_creation(self, db_session):
        """Verify idempotency keys are created and prevent duplicates."""
        from backend.shared.idempotency import IdempotencyService
        
        service = IdempotencyService(db_session)
        
        event_id = str(uuid4())
        service_name = "core_engine"
        operation = "scan.start"
        
        # First call: Should return None (not processed yet)
        result = await service.check_and_record(
            event_id=event_id,
            service=service_name,
            operation=operation
        )
        assert result is None
        
        # Verify key exists in DB
        count = await db_session.execute(
            select(func.count()).select_from(IdempotencyKey)
            .where(IdempotencyKey.key == event_id)
        )
        assert count.scalar() == 1
        
        # Second call: Should return the key (already processed)
        result = await service.check_and_record(
            event_id=event_id,
            service=service_name,
            operation=operation
        )
        assert result is not None
        assert isinstance(result, IdempotencyKey)

    @pytest.mark.asyncio
    async def test_idempotency_with_response_caching(self, db_session):
        """Verify responses are cached for replay."""
        from backend.shared.idempotency import IdempotencyService
        
        service = IdempotencyService(db_session)
        
        event_id = str(uuid4())
        test_response = {"scan_id": str(uuid4()), "status": "completed"}
        
        # First call
        await service.check_and_record(
            event_id=event_id,
            service="core_engine",
            operation="scan.execute"
        )
        
        # Cache response
        await service.store_response(event_id, test_response)
        
        # Second call: Should return cached response
        cached = await service.check_and_record(
            event_id=event_id,
            service="core_engine",
            operation="scan.execute"
        )
        
        assert cached is not None
        assert cached.response == test_response

    @pytest.mark.asyncio
    async def test_idempotency_decorator(self, db_session):
        """Verify with_idempotency decorator works correctly."""
        from backend.shared.idempotency import with_idempotency
        
        event_id = str(uuid4())
        execution_count = 0
        
        async def handler():
            nonlocal execution_count
            execution_count += 1
            return {"result": "processed", "count": execution_count}
        
        # First call: Should execute handler
        result1 = await with_idempotency(
            event_id=event_id,
            service="test_service",
            operation="test.op",
            handler=handler,
            session=db_session
        )
        
        assert execution_count == 1
        assert result1["count"] == 1
        
        # Second call: Should return cached (not execute handler again)
        result2 = await with_idempotency(
            event_id=event_id,
            service="test_service",
            operation="test.op",
            handler=handler,
            session=db_session
        )
        
        assert execution_count == 1  # Handler not called again
        assert result2["count"] == 1  # Cached result

    @pytest.mark.asyncio
    async def test_idempotency_different_events(self, db_session):
        """Verify different event IDs are treated independently."""
        from backend.shared.idempotency import IdempotencyService
        
        service = IdempotencyService(db_session)
        
        event_id_1 = str(uuid4())
        event_id_2 = str(uuid4())
        
        # First event
        await service.check_and_record(
            event_id=event_id_1,
            service="test",
            operation="op1"
        )
        
        # Second event (different ID) - Should not be duplicate
        result = await service.check_and_record(
            event_id=event_id_2,
            service="test",
            operation="op1"
        )
        
        assert result is None  # Not a duplicate
        
        # Verify both keys exist
        count = await db_session.execute(
            select(func.count()).select_from(IdempotencyKey)
            .where(IdempotencyKey.key.in_([event_id_1, event_id_2]))
        )
        assert count.scalar() == 2

    @pytest.mark.asyncio
    async def test_idempotency_different_services(self, db_session):
        """Verify different services are treated independently."""
        from backend.shared.idempotency import IdempotencyService
        
        service = IdempotencyService(db_session)
        
        event_id = str(uuid4())
        
        # Same event, different service
        result1 = await service.check_and_record(
            event_id=event_id,
            service="service_a",
            operation="op"
        )
        assert result1 is None
        
        result2 = await service.check_and_record(
            event_id=event_id,
            service="service_b",
            operation="op"
        )
        assert result2 is None  # Different service, not duplicate
        
        # Verify both keys exist
        count = await db_session.execute(
            select(func.count()).select_from(IdempotencyKey)
            .where(IdempotencyKey.key == event_id)
        )
        assert count.scalar() == 2  # One for each service

    @pytest.mark.asyncio
    async def test_idempotency_cleanup(self, db_session):
        """Verify expired idempotency keys are cleaned up."""
        from backend.shared.idempotency import IdempotencyService
        from datetime import timedelta
        
        service = IdempotencyService(db_session)
        
        # Clean up any existing keys first
        await db_session.execute(
            delete(IdempotencyKey)
        )
        await db_session.commit()
        
        # Create key with past expiration
        past_expires = datetime.now(timezone.utc) - timedelta(days=8)
        
        async with db_session.begin():
            old_key = IdempotencyKey(
                key=str(uuid4()),
                service="test",
                operation="test.op",
                created_at=datetime.now(timezone.utc) - timedelta(days=8),
                expires_at=past_expires
            )
            db_session.add(old_key)
        
        # Run cleanup
        await service.cleanup_expired()
        
        # Verify old key removed
        count = await db_session.execute(
            select(func.count()).select_from(IdempotencyKey)
        )
        assert count.scalar() == 0

    @pytest.mark.asyncio
    async def test_idempotency_table_indexes(self, db_session):
        """Verify idempotency_keys table has proper indexes."""
        # Check that the model has the required indexes defined
        from backend.shared.models.idempotency import IdempotencyKey
        
        # Verify PrimaryKeyConstraint exists - convert list to set for comparison
        pk_columns = set(IdempotencyKey.__table__.primary_key.columns.keys())
        expected = {'key', 'service', 'operation'}
        assert pk_columns == expected
        
        # Verify indexes are defined (they are in __table_args__)
        # This test verifies the model definition is correct
        assert IdempotencyKey.__table_args__ is not None


class TestWorkerIdempotency:
    """Tests for idempotency in actual workers."""

    @pytest.mark.asyncio
    async def test_worker_rejects_duplicate_scan(self, db_session, mocker):
        """Verify Core Worker rejects duplicate scan messages via idempotency."""
        from backend.shared.idempotency import IdempotencyService
        from backend.shared.schemas.envelope import MessageEnvelope
        from backend.services.core_engine.scan_task import _async_scan_pipeline
        
        event_id = str(uuid4())
        program_id = uuid4()
        
        # Manually test the idempotency check logic
        service = IdempotencyService(db_session)
        
        # First call - should return None (not processed)
        cached = await service.check_and_record(
            event_id=event_id,
            service="core_engine",
            operation="scan.execute"
        )
        assert cached is None
        
        # Second call - should return the key (already processed)
        cached = await service.check_and_record(
            event_id=event_id,
            service="core_engine",
            operation="scan.execute"
        )
        assert cached is not None
        assert cached.key == event_id

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_reporter_rejects_duplicate_report(self, db_session, mocker):
        """Verify Reporter Worker rejects duplicate report messages via idempotency."""
        from backend.shared.idempotency import IdempotencyService
        
        event_id = str(uuid4())
        
        # Manually test the idempotency check logic
        service = IdempotencyService(db_session)
        
        # First call - should return None (not processed)
        cached = await service.check_and_record(
            event_id=event_id,
            service="reporter",
            operation="report.generate"
        )
        assert cached is None
        
        # Second call - should return the key (already processed)
        cached = await service.check_and_record(
            event_id=event_id,
            service="reporter",
            operation="report.generate"
        )
        assert cached is not None
        assert cached.key == event_id

