"""
AttackBot scraper SQLAlchemy ORM models.
Maps to tables created by migration 002_scraper_full.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base


class Program(Base):
    __tablename__ = "programs"

    program_id:      Mapped[uuid.UUID]           = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform:        Mapped[str]                 = mapped_column(String(50), nullable=False)
    handle:          Mapped[str]                 = mapped_column(String(255), unique=True, nullable=False)
    name:            Mapped[Optional[str]]        = mapped_column(String(500))
    url:             Mapped[Optional[str]]        = mapped_column(String(2048))
    bounty_type:     Mapped[Optional[str]]        = mapped_column(String(50))
    max_bounty:      Mapped[Optional[int]]        = mapped_column(Integer)
    is_active:       Mapped[bool]                 = mapped_column(Boolean, default=True)
    summary_file:    Mapped[Optional[str]]        = mapped_column(String(1024))
    raw_policy:      Mapped[Optional[dict]]       = mapped_column(JSONB)
    queued_for_scan: Mapped[bool]                 = mapped_column(Boolean, default=False)
    last_scraped_at: Mapped[Optional[datetime]]   = mapped_column(TIMESTAMPTZ)
    created_at:      Mapped[datetime]             = mapped_column(
        TIMESTAMPTZ, default=lambda: datetime.now(timezone.utc)
    )
    updated_at:      Mapped[datetime]             = mapped_column(
        TIMESTAMPTZ,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    scopes:   Mapped[list["ProgramScope"]]  = relationship(
        "ProgramScope", back_populates="program", cascade="all, delete-orphan"
    )
    policies: Mapped[list["ProgramPolicy"]] = relationship(
        "ProgramPolicy", back_populates="program", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Program handle={self.handle!r} platform={self.platform!r}>"


class ProgramScope(Base):
    __tablename__ = "program_scopes"

    scope_id:   Mapped[uuid.UUID]        = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID]        = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.program_id", ondelete="CASCADE"), nullable=False
    )
    scope_type: Mapped[str]              = mapped_column(String(20), nullable=False)  # in_scope | out_of_scope
    asset_type: Mapped[str]              = mapped_column(String(50), nullable=False)
    value:      Mapped[str]              = mapped_column(String(2048), nullable=False)
    notes:      Mapped[Optional[str]]    = mapped_column(Text)
    created_at: Mapped[datetime]         = mapped_column(
        TIMESTAMPTZ, default=lambda: datetime.now(timezone.utc)
    )

    program: Mapped["Program"] = relationship("Program", back_populates="scopes")

    def __repr__(self) -> str:
        return f"<ProgramScope {self.scope_type} {self.asset_type}={self.value!r}>"


class ProgramPolicy(Base):
    __tablename__ = "program_policies"

    policy_id:            Mapped[uuid.UUID]           = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id:           Mapped[uuid.UUID]           = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.program_id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    disclosure_policy:    Mapped[Optional[str]]       = mapped_column(Text)
    testing_restrictions: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text))
    safe_harbor:          Mapped[Optional[bool]]      = mapped_column(Boolean)
    created_at:           Mapped[datetime]            = mapped_column(
        TIMESTAMPTZ, default=lambda: datetime.now(timezone.utc)
    )

    program: Mapped["Program"] = relationship("Program", back_populates="policies")
