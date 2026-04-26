# backend/shared/event_sourcing/event_store.py
"""
EventStore service for recording and querying domain events.

Provides functionality for:
- Appending events to the event store
- Querying events by entity, aggregate, type, or time range
- Temporal queries (state at a point in time)
"""

import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from backend.shared.logging import get_logger
from backend.shared.models.event_store import DomainEvent, EventType

logger = get_logger(__name__)


class EventStore:
    """
    Service for managing domain events in the event store.

    Events are stored with:
    - entity_type/entity_id: The entity that the event pertains to
    - aggregate_type/aggregate_id: The aggregate root for event sourcing
    - sequence: Global sequence number for ordering
    - timestamp: When the event occurred
    - data: Event payload
    - metadata: Additional context (stored as 'metadata' in DB)
    - triggered_by: Who/what triggered this event
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def append_event(
        self,
        entity_type: str,
        entity_id: UUID,
        event_type: str | EventType,
        data: dict,
        metadata: dict | None = None,
        triggered_by: str | None = None,
        aggregate_type: str | None = None,
        aggregate_id: UUID | None = None,
    ) -> DomainEvent:
        """
        Append a new event to the event store.

        Note: this method does not commit; callers control transaction boundaries.
        """

        # Get next sequence number.
        #
        # If the `nextval(...)` query fails, Postgres aborts the current transaction.
        # Use a nested transaction (SAVEPOINT) so we can fall back safely.
        try:
            async with self.session.begin_nested():
                result = await self.session.execute(
                    text("SELECT nextval('domain_event_sequence_seq')")
                )
                sequence = int(result.scalar() or 1)
        except Exception as exc:
            logger.warning("sequence_nextval_failed_fallback_max", error=str(exc))
            result = await self.session.execute(
                text("SELECT COALESCE(MAX(sequence), 0) + 1 FROM domain_events")
            )
            sequence = int(result.scalar() or 1)

        event = DomainEvent(
            event_id=uuid.uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type.value if isinstance(event_type, EventType) else event_type,
            timestamp=datetime.now(timezone.utc),
            sequence=sequence,
            data=data,
            event_metadata=metadata,
            triggered_by=triggered_by,
            aggregate_type=aggregate_type or entity_type,
            aggregate_id=aggregate_id or entity_id,
        )
        # Tests use `event.metadata` (even though it's reserved at the class level).
        # Set an instance attribute that shadows the class attribute.
        event.metadata = metadata

        self.session.add(event)
        # Ensure visibility for subsequent reads in the same session/transaction.
        await self.session.flush()

        logger.debug(
            "event_appended",
            event_id=str(event.event_id),
            event_type=event.event_type,
            entity_type=entity_type,
            entity_id=str(entity_id),
            aggregate_type=event.aggregate_type,
            aggregate_id=str(event.aggregate_id),
        )
        return event

    async def get_events_for_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[DomainEvent]:
        query = (
            select(DomainEvent)
            .where(
                and_(
                    DomainEvent.entity_type == entity_type,
                    DomainEvent.entity_id == entity_id,
                )
            )
            .order_by(DomainEvent.sequence)
        )
        if since:
            query = query.where(DomainEvent.timestamp >= since)
        if until:
            query = query.where(DomainEvent.timestamp <= until)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_events_for_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[DomainEvent]:
        query = (
            select(DomainEvent)
            .where(
                and_(
                    DomainEvent.aggregate_type == aggregate_type,
                    DomainEvent.aggregate_id == aggregate_id,
                )
            )
            .order_by(DomainEvent.sequence)
        )
        if since:
            query = query.where(DomainEvent.timestamp >= since)
        if until:
            query = query.where(DomainEvent.timestamp <= until)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_events_by_type(
        self,
        event_type: str | EventType,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[DomainEvent]:
        event_type_str = event_type.value if isinstance(event_type, EventType) else event_type
        query = (
            select(DomainEvent)
            .where(DomainEvent.event_type == event_type_str)
            .order_by(desc(DomainEvent.timestamp))
        )
        if since:
            query = query.where(DomainEvent.timestamp >= since)
        if until:
            query = query.where(DomainEvent.timestamp <= until)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_aggregate_state_at(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        at_time: datetime,
    ) -> list[DomainEvent]:
        query = (
            select(DomainEvent)
            .where(
                and_(
                    DomainEvent.aggregate_type == aggregate_type,
                    DomainEvent.aggregate_id == aggregate_id,
                    DomainEvent.timestamp <= at_time,
                )
            )
            .order_by(DomainEvent.sequence)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_events(
        self,
        limit: int = 100,
        event_type: str | EventType | None = None,
    ) -> list[DomainEvent]:
        query = select(DomainEvent).order_by(desc(DomainEvent.timestamp)).limit(limit)
        if event_type:
            event_type_str = event_type.value if isinstance(event_type, EventType) else event_type
            query = query.where(DomainEvent.event_type == event_type_str)

        result = await self.session.execute(query)
        return list(result.scalars().all())

