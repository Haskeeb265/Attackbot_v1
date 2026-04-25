# backend/shared/models/idempotency.py
"""
Idempotency key tracking for at-least-once message delivery.

Ensures that redelivered messages do not cause duplicate processing.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import DateTime, Index, JSON, String, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.db import Base


class IdempotencyKey(Base):
    """
    Tracks processed message IDs to ensure idempotent message handling.

    When a message arrives, check if its event_id exists in this table:
    - If exists: Return cached response (message already processed)
    - If not exists: Process message, store response, then ack

    TTL: Keys expire after 7 days to prevent unbounded growth.
    """
    __tablename__ = "idempotency_keys"

    # event_id from MessageEnvelope
    key: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )

    # Service that processed the message
    service: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Operation performed (e.g., "scan.start", "report.generate")
    operation: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # When message was first processed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # When key expires (auto-cleanup)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=7),
    )

    # Response cached for replay (optional)
    response: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
    )

    # Related entity ID (e.g., scan_id, report_id)
    entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    __table_args__ = (
        PrimaryKeyConstraint('key', 'service', 'operation', name='pk_idempotency'),
        Index('idx_idempotency_created_at', 'created_at'),
        Index('idx_idempotency_expires_at', 'expires_at'),
        Index('idx_idempotency_service_operation', 'service', 'operation'),
    )
