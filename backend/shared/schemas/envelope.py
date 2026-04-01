# backend/shared/schemas/envelope.py
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MessageEnvelope(BaseModel):
    """
    Canonical wrapper for all AttackBot queue messages.
    Every producer MUST use build_envelope(). Every consumer MUST validate against this.

    Versioning rules:
      - Field addition  → backward compatible, minor version bump
      - Field removal   → breaking change, major version bump + coordinated deploy
      - Field rename    → breaking change (treat as removal + addition)
      - Type change     → breaking change (even widening)

    Consumers check get_major_version() and reject unknown major versions to DLQ.
    """

    model_config = ConfigDict(extra="ignore")  # forward-compat: ignore unknown fields

    # ── Identity ───────────────────────────────────────────────────────
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Globally unique message ID. Used for deduplication and DLQ tracing.",
    )
    event_type: str = Field(
        description=(
            "Identifies the message type. Format: noun.verb (e.g. 'program.scraped'). "
            "Consumers reject unknown event_types to DLQ."
        ),
    )
    schema_version: str = Field(
        default="1.0",
        description="Version of the payload schema. Breaking changes bump major.",
    )

    # ── Tracing ────────────────────────────────────────────────────────
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of message creation.",
    )
    trace_id: str | None = Field(
        default=None,
        description=(
            "Distributed trace ID from originating HTTP request. "
            "Set by api-gateway; passed through all downstream messages."
        ),
    )
    source_service: str = Field(
        description="Name of the service that produced this message.",
    )

    # ── Payload ────────────────────────────────────────────────────────
    payload: dict[str, Any] = Field(
        description="Event-specific data. Schema defined per event_type.",
    )

    def get_major_version(self) -> int:
        """Returns the major version integer for compatibility checks."""
        return int(self.schema_version.split(".")[0])


def build_envelope(
    event_type: str,
    payload: dict[str, Any],
    source_service: str,
    schema_version: str = "1.0",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """
    Factory for creating envelope dicts. Always use this — never construct manually.

    Example:
        msg = build_envelope(
            event_type="program.scraped",
            payload=scan_payload.model_dump(mode="json"),
            source_service="scraper",
        )
        await publisher.publish(Queues.SCAN_JOBS, msg)
    """
    return MessageEnvelope(
        event_type=event_type,
        payload=payload,
        source_service=source_service,
        schema_version=schema_version,
        trace_id=trace_id,
    ).model_dump(mode="json")