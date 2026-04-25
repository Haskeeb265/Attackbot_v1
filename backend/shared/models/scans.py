# backend/shared/models/scans.py
"""
SQLAlchemy ORM model for scans table.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.db import Base


class Scan(Base):
    """
    ORM model for the scans table.
    
    Represents a security scan execution with its lifecycle state.
    """
    __tablename__ = "scans"

    scan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=lambda: UUID(int=0),  # Will be overridden by server_default
    )
    program_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )
    priority: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
    )
    feature_flags: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    partial_detail: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    error_detail: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )
    finding_count: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )
    severity_breakdown: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
