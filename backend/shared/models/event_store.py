# backend/shared/models/event_store.py
"""
SQLAlchemy ORM model for domain_events table.
Event sourcing for audit trail and state reconstruction.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Index, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.db import Base


class EventType(str, Enum):
    """Domain event types for the AttackBot system."""

    # Scan events
    SCAN_CREATED = "scan.created"
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"

    # Stage events
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    STAGE_FAILED = "stage.failed"

    # Finding events
    FINDING_CREATED = "finding.created"
    FINDING_UPDATED = "finding.updated"
    FINDING_DELETED = "finding.deleted"


class DomainEvent(Base):
    """
    ORM model for the domain_events table.

    Stores all domain events for audit trail and state reconstruction.
    """

    __tablename__ = "domain_events"
    __table_args__ = (
        Index("idx_domain_events_entity", "entity_type", "entity_id"),
        Index("idx_domain_events_aggregate", "aggregate_type", "aggregate_id"),
        Index("idx_domain_events_sequence", "sequence"),
        Index("idx_domain_events_timestamp", "timestamp"),
        Index("idx_domain_events_event_type", "event_type"),
    )

    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=lambda: UUID(int=0)
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Column is named "metadata" in DB, but attribute can't be "metadata"
    # because SQLAlchemy reserves it on Declarative models.
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
