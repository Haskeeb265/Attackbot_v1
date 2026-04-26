"""

Test verification for Issue #7: Absence of Event Sourcing



These tests verify that domain events are recorded and can be used

for audit trails and state reconstruction.

"""



import asyncio
import pytest

from uuid import uuid4

from datetime import datetime, timezone, timedelta

from sqlalchemy.future import select

from sqlalchemy import func, desc, delete



from backend.shared.db import get_session

from backend.shared.models.event_store import DomainEvent, EventType





class TestEventModel:

    """Tests for the DomainEvent model."""



    def test_event_model_fields(self):

        """Verify DomainEvent has all required fields."""

        # Check model definition

        from backend.shared.models.event_store import DomainEvent

        

        # Verify columns exist

        assert hasattr(DomainEvent, 'event_id')

        assert hasattr(DomainEvent, 'entity_type')

        assert hasattr(DomainEvent, 'entity_id')

        assert hasattr(DomainEvent, 'event_type')

        assert hasattr(DomainEvent, 'timestamp')

        assert hasattr(DomainEvent, 'sequence')

        assert hasattr(DomainEvent, 'data')

        assert hasattr(DomainEvent, 'metadata')

        assert hasattr(DomainEvent, 'triggered_by')

        assert hasattr(DomainEvent, 'aggregate_type')

        assert hasattr(DomainEvent, 'aggregate_id')



    def test_event_type_enum(self):

        """Verify EventType enum has all required event types."""

        from backend.shared.models.event_store import EventType

        

        # Check scan events

        assert EventType.SCAN_CREATED == "scan.created"

        assert EventType.SCAN_STARTED == "scan.started"

        assert EventType.SCAN_COMPLETED == "scan.completed"

        assert EventType.SCAN_FAILED == "scan.failed"

        

        # Check stage events

        assert EventType.STAGE_STARTED == "stage.started"

        assert EventType.STAGE_COMPLETED == "stage.completed"

        assert EventType.STAGE_FAILED == "stage.failed"

        

        # Check finding events

        assert EventType.FINDING_CREATED == "finding.created"

        assert EventType.FINDING_UPDATED == "finding.updated"

        assert EventType.FINDING_DELETED == "finding.deleted"





class TestEventStore:

    """Tests for the EventStore service."""



    @pytest.mark.asyncio

    async def test_append_event(self, db_session):

        """Verify events can be appended to the event store."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        

        scan_id = uuid4()
        event = await store.append_event(

            entity_type="scan",

            entity_id=uuid4(),

            event_type=EventType.SCAN_CREATED,

            data={"scan_id": str(scan_id), "status": "pending"},

            metadata={"source": "test"},

            triggered_by="test_user",

            aggregate_type="scan",

            aggregate_id=uuid4()

        )

        

        # Verify event was created

        assert event.event_id is not None

        assert event.entity_type == "scan"

        assert event.event_type == EventType.SCAN_CREATED.value

        assert event.data == {"scan_id": str(scan_id), "status": "pending"}

        assert event.metadata == {"source": "test"}

        assert event.triggered_by == "test_user"

        assert event.timestamp is not None

        assert event.sequence is not None



    @pytest.mark.asyncio

    async def test_get_events_for_entity(self, db_session):

        """Verify events can be retrieved for a specific entity."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        

        entity_id = uuid4()

        

        # Append multiple events for same entity

        await store.append_event(

            entity_type="scan",

            entity_id=entity_id,

            event_type=EventType.SCAN_CREATED,

            data={"status": "pending"}

        )

        

        await store.append_event(

            entity_type="scan",

            entity_id=entity_id,

            event_type=EventType.SCAN_STARTED,

            data={"status": "running"}

        )

        

        # Retrieve events

        events = await store.get_events_for_entity("scan", entity_id)

        

        assert len(events) == 2

        assert events[0].event_type == EventType.SCAN_CREATED.value

        assert events[1].event_type == EventType.SCAN_STARTED.value



    @pytest.mark.asyncio

    async def test_get_events_for_aggregate(self, db_session):

        """Verify events can be retrieved for an aggregate root."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        

        aggregate_id = uuid4()

        

        # Append events for aggregate

        await store.append_event(

            entity_type="scan",

            entity_id=uuid4(),

            event_type=EventType.SCAN_CREATED,

            data={},

            aggregate_type="scan",

            aggregate_id=aggregate_id

        )

        

        await store.append_event(

            entity_type="finding",

            entity_id=uuid4(),

            event_type=EventType.FINDING_CREATED,

            data={},

            aggregate_type="scan",

            aggregate_id=aggregate_id

        )

        

        # Retrieve all events for aggregate

        events = await store.get_events_for_aggregate("scan", aggregate_id)

        

        assert len(events) == 2

        # Both should have same aggregate_id

        for event in events:

            assert event.aggregate_id == aggregate_id



    @pytest.mark.asyncio

    async def test_get_events_by_type(self, db_session):

        """Verify events can be queried by type."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        

        # Create events of different types

        await store.append_event(

            entity_type="scan",

            entity_id=uuid4(),

            event_type=EventType.SCAN_CREATED,

            data={}

        )

        

        await store.append_event(

            entity_type="finding",

            entity_id=uuid4(),

            event_type=EventType.FINDING_CREATED,

            data={}

        )

        

        await store.append_event(

            entity_type="scan",

            entity_id=uuid4(),

            event_type=EventType.SCAN_CREATED,

            data={}

        )

        

        # Query for scan.created events only

        events = await store.get_events_by_type(EventType.SCAN_CREATED)

        

        assert len(events) == 2

        for event in events:

            assert event.event_type == EventType.SCAN_CREATED.value



    @pytest.mark.asyncio

    async def test_temporal_query(self, db_session):

        """Verify temporal queries work (events at a point in time)."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        

        aggregate_id = uuid4()

        

        # Create events at different times
        first_event = await store.append_event(

            entity_type="scan",

            entity_id=uuid4(),

            event_type=EventType.SCAN_CREATED,

            data={},

            aggregate_type="scan",

            aggregate_id=aggregate_id

        )

        

        # Wait a tiny bit to ensure different timestamps

        await asyncio.sleep(0.01)

        

        # This event should not be included in past query

        await store.append_event(

            entity_type="scan",

            entity_id=uuid4(),

            event_type=EventType.SCAN_COMPLETED,

            data={},

            aggregate_type="scan",

            aggregate_id=aggregate_id

        )

        

        # Query events up to just after first event
        base_time = first_event.timestamp
        past_time = base_time + timedelta(milliseconds=5)

        events = await store.get_aggregate_state_at("scan", aggregate_id, past_time)

        

        # Should only get first event

        assert len(events) == 1

        assert events[0].event_type == EventType.SCAN_CREATED.value



    @pytest.mark.asyncio

    async def test_sequence_numbers_unique(self, db_session):

        """Verify sequence numbers are unique and increasing."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        

        sequences = []

        

        for i in range(5):

            event = await store.append_event(

                entity_type="scan",

                entity_id=uuid4(),

                event_type=EventType.SCAN_CREATED,

                data={}

            )

            sequences.append(event.sequence)

        

        # Verify all sequences are unique

        assert len(sequences) == len(set(sequences))

        

        # Verify sequences are increasing

        assert sequences == sorted(sequences)





class TestScanRepositoryEvents:

    """Tests for ScanRepository event recording."""



    @pytest.mark.asyncio

    async def test_create_scan_records_event(self, db_session):

        """Verify scan creation records an event."""

        from backend.services.core_engine.repository import ScanRepository

        

        repo = ScanRepository(db_session)

        program_id = uuid4()

        

        # Create scan

        scan = await repo.create_scan(

            program_id=program_id,

            config={"target": "test.com"},

            triggered_by="test"

        )

        

        await db_session.commit()

        

        # Verify event was recorded

        from backend.shared.event_sourcing.event_store import EventStore

        store = EventStore(db_session)

        

        events = await store.get_events_for_entity("scan", scan.scan_id)

        

        assert len(events) >= 1

        assert events[0].event_type == EventType.SCAN_CREATED.value

        assert events[0].data["scan_id"] == str(scan.scan_id)



    @pytest.mark.asyncio

    async def test_start_scan_records_event(self, db_session):

        """Verify scan start records an event."""

        from backend.services.core_engine.repository import ScanRepository

        from backend.shared.models.event_store import EventType

        

        repo = ScanRepository(db_session)

        program_id = uuid4()

        

        # Create scan

        scan = await repo.create_scan(program_id, {}, "test")

        await db_session.commit()

        

        # Start scan

        await repo.start_scan(scan.scan_id, "test")

        await db_session.commit()

        

        # Verify event

        from backend.shared.event_sourcing.event_store import EventStore

        store = EventStore(db_session)

        

        events = await store.get_events_for_entity("scan", scan.scan_id)

        event_types = [e.event_type for e in events]

        

        assert EventType.SCAN_STARTED.value in event_types



    @pytest.mark.asyncio

    async def test_scan_complete_records_event(self, db_session):

        """Verify scan completion records an event."""

        from backend.services.core_engine.repository import ScanRepository

        from backend.shared.models.event_store import EventType

        

        repo = ScanRepository(db_session)

        

        # Create and start scan

        scan = await repo.create_scan(uuid4(), {}, "test")

        await repo.start_scan(scan.scan_id, "test")

        await db_session.commit()

        

        # Complete scan

        await repo.mark_scan_complete(

            scan_id=scan.scan_id,

            status="completed",

            finding_count=10,

            severity_breakdown={"high": 5, "medium": 5}

        )

        await db_session.commit()

        

        # Verify completion event

        from backend.shared.event_sourcing.event_store import EventStore

        store = EventStore(db_session)

        

        events = await store.get_events_for_entity("scan", scan.scan_id)

        event_types = [e.event_type for e in events]

        

        assert EventType.SCAN_COMPLETED.value in event_types



    @pytest.mark.asyncio

    async def test_scan_lifecycle_events(self, db_session):

        """Verify all scan lifecycle events are recorded."""

        from backend.services.core_engine.repository import ScanRepository

        from backend.shared.models.event_store import EventType

        

        repo = ScanRepository(db_session)

        program_id = uuid4()

        

        # Create, start, and complete scan

        scan = await repo.create_scan(program_id, {}, "test")

        await repo.start_scan(scan.scan_id, "test")

        await repo.mark_scan_complete(

            scan.scan_id, "completed", 10, {}

        )

        await db_session.commit()

        

        # Verify all events

        from backend.shared.event_sourcing.event_store import EventStore

        store = EventStore(db_session)

        

        events = await store.get_events_for_entity("scan", scan.scan_id)

        event_types = [e.event_type for e in events]

        

        assert EventType.SCAN_CREATED.value in event_types

        assert EventType.SCAN_STARTED.value in event_types

        assert EventType.SCAN_COMPLETED.value in event_types





class TestStateReconstruction:

    """Tests for state reconstruction from events."""



    @pytest.mark.asyncio

    async def test_rebuild_scan_state(self, db_session):

        """Verify scan state can be rebuilt from events."""

        from backend.services.core_engine.repository import ScanRepository

        

        repo = ScanRepository(db_session)

        

        # Create and complete scan

        scan = await repo.create_scan(uuid4(), {}, "test")

        await repo.start_scan(scan.scan_id)

        await repo.mark_scan_complete(

            scan.scan_id, "completed", 7, {"high": 3, "medium": 4}

        )

        await db_session.commit()

        

        # Rebuild state from events

        reconstructed = await repo.rebuild_scan_state(scan.scan_id)

        

        # Verify reconstruction

        assert reconstructed["scan_id"] == str(scan.scan_id)

        assert reconstructed["status"] == "completed"

        assert reconstructed["finding_count"] == 7

        assert reconstructed["severity_breakdown"]["high"] == 3

        assert reconstructed["severity_breakdown"]["medium"] == 4



    @pytest.mark.asyncio

    async def test_rebuild_incomplete_scan(self, db_session):

        """Verify incomplete scan state can be rebuilt."""

        from backend.services.core_engine.repository import ScanRepository

        

        repo = ScanRepository(db_session)

        

        # Create and start scan but don't complete

        scan = await repo.create_scan(uuid4(), {}, "test")

        await repo.start_scan(scan.scan_id)

        await db_session.commit()

        

        # Rebuild state

        reconstructed = await repo.rebuild_scan_state(scan.scan_id)

        

        assert reconstructed["scan_id"] == str(scan.scan_id)

        assert reconstructed["status"] == "running"



    @pytest.mark.asyncio

    async def test_rebuild_failed_scan(self, db_session):

        """Verify failed scan state can be rebuilt."""

        from backend.services.core_engine.repository import ScanRepository

        

        repo = ScanRepository(db_session)

        

        # Create scan and mark as failed

        scan = await repo.create_scan(uuid4(), {}, "test")

        await repo.start_scan(scan.scan_id)

        await repo.mark_scan_complete(

            scan.scan_id, "failed", 0, {},

            error_detail="Test failure"

        )

        await db_session.commit()

        

        # Rebuild state

        reconstructed = await repo.rebuild_scan_state(scan.scan_id)

        

        assert reconstructed["scan_id"] == str(scan.scan_id)

        assert reconstructed["status"] == "failed"

        assert "error_detail" in reconstructed



    @pytest.mark.asyncio

    async def test_rebuild_with_no_events(self, db_session):

        """Verify rebuild returns empty state when no events exist."""

        from backend.services.core_engine.repository import ScanRepository

        

        repo = ScanRepository(db_session)

        

        # Try to rebuild non-existent scan

        reconstructed = await repo.rebuild_scan_state(uuid4())

        

        # Should return basic structure

        assert "scan_id" in reconstructed

        assert reconstructed["status"] is None





class TestAuditAPI:

    """Tests for audit API endpoints."""



    @pytest.mark.asyncio

    async def test_get_scan_events_endpoint(self, client, db_session):

        """Verify GET /api/v1/scans/{scan_id}/events endpoint."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        scan_id = uuid4()

        

        # Create some events

        await store.append_event(

            entity_type="scan",

            entity_id=scan_id,

            event_type=EventType.SCAN_CREATED,

            data={"status": "pending"},

            aggregate_type="scan",

            aggregate_id=scan_id

        )

        

        await store.append_event(

            entity_type="scan",

            entity_id=scan_id,

            event_type=EventType.SCAN_STARTED,

            data={"status": "running"},

            aggregate_type="scan",

            aggregate_id=scan_id

        )

        

        await db_session.commit()

        

        # Call API

        response = client.get(f"/api/v1/scans/{scan_id}/events")

        

        assert response.status_code == 200

        data = response.json()

        assert "events" in data

        assert "total" in data

        assert len(data["events"]) >= 2



    @pytest.mark.asyncio

    async def test_get_scan_state_at_endpoint(self, client, db_session):

        """Verify GET /api/v1/scans/{scan_id}/state-at endpoint."""

        from backend.services.core_engine.repository import ScanRepository

        

        repo = ScanRepository(db_session)

        scan_id = uuid4()

        

        # Create and complete scan

        await repo.create_scan(scan_id, {}, "test")

        await repo.start_scan(scan_id)

        await repo.mark_scan_complete(scan_id, "completed", 5, {})

        await db_session.commit()

        

        # Call API

        at_time = datetime.now(timezone.utc).isoformat()

        response = client.get(

            f"/api/v1/scans/{scan_id}/state-at?at_time={at_time}"

        )

        

        assert response.status_code == 200

        data = response.json()

        assert "scan_id" in data

        assert "at_time" in data

        assert "state" in data

        assert data["state"]["status"] == "completed"



    @pytest.mark.asyncio

    async def test_audit_findings_created_endpoint(self, client, db_session):

        """Verify GET /api/v1/audit/findings-created endpoint."""

        from backend.shared.event_sourcing.event_store import EventStore

        

        store = EventStore(db_session)

        

        # Create finding created events

        for i in range(5):

            await store.append_event(

                entity_type="finding",

                entity_id=uuid4(),

                event_type=EventType.FINDING_CREATED,

                data={"finding_id": str(uuid4()), "severity": "high"},

                aggregate_type="scan",

                aggregate_id=uuid4()

            )

        

        await db_session.commit()

        

        # Call API

        from_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        response = client.get(

            f"/api/v1/audit/findings-created?from_time={from_time}"

        )

        

        assert response.status_code == 200

        data = response.json()

        assert "events" in data

        assert "total" in data





class TestDisasterRecovery:

    """Tests for disaster recovery scenarios."""



    @pytest.mark.asyncio

    async def test_delete_scan_rebuild_from_events(self, db_session):

        """Verify scan can be rebuilt from events after deletion."""

        from backend.services.core_engine.repository import ScanRepository

        from backend.shared.models.scans import Scan

        

        repo = ScanRepository(db_session)

        scan_id = uuid4()

        

        # Create and complete scan

        await repo.create_scan(scan_id, {}, "test")

        await repo.start_scan(scan_id)

        await repo.mark_scan_complete(scan_id, "completed", 10, {"high": 5})

        await db_session.commit()

        

        # Verify scan exists

        result = await db_session.execute(

            select(Scan).where(Scan.scan_id == scan_id)

        )

        scan = result.scalar()

        assert scan is not None

        

        # Delete scan (simulate data loss)

        await db_session.execute(

            delete(Scan).where(Scan.scan_id == scan_id)

        )

        await db_session.commit()

        

        # Verify scan is gone

        result = await db_session.execute(

            select(Scan).where(Scan.scan_id == scan_id)

        )

        assert result.scalar() is None

        

        # Rebuild from events

        reconstructed = await repo.rebuild_scan_state(scan_id)

        

        # Verify rebuilt state

        assert reconstructed["scan_id"] == str(scan_id)

        assert reconstructed["status"] == "completed"

        assert reconstructed["finding_count"] == 10



    @pytest.mark.asyncio

    async def test_audit_trail_completeness(self, db_session):

        """Verify complete audit trail is available."""

        from backend.services.core_engine.repository import ScanRepository

        from backend.shared.event_sourcing.event_store import EventStore

        

        repo = ScanRepository(db_session)

        scan_id = uuid4()

        

        # Perform various operations

        await repo.create_scan(scan_id, {}, "test")

        await repo.start_scan(scan_id)

        # Simulate stage completion

        from backend.shared.models.event_store import EventType

        

        store = EventStore(db_session)

        await store.append_event(

            entity_type="stage",

            entity_id=uuid4(),

            event_type=EventType.STAGE_COMPLETED,

            data={"stage_name": "discovery", "stage_number": 1},

            aggregate_type="scan",

            aggregate_id=scan_id

        )

        

        await repo.mark_scan_complete(scan_id, "completed", 5, {})

        await db_session.commit()

        

        # Get all events

        events = await store.get_events_for_aggregate("scan", scan_id)

        

        event_types = [e.event_type for e in events]

        

        # Verify all expected events are present

        assert EventType.SCAN_CREATED.value in event_types

        assert EventType.SCAN_STARTED.value in event_types

        assert EventType.STAGE_COMPLETED.value in event_types

        assert EventType.SCAN_COMPLETED.value in event_types

