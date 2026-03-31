from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.shared.schemas.envelope import build_envelope


class ReportsCompletedPayload(BaseModel):
    """
    Payload schema for queue: reports.completed
    Event type: report.generated
    Schema version: 1.0
    Producer: reporter-worker
    """

    model_config = ConfigDict(extra="ignore")

    report_id: UUID
    scan_id: UUID
    program_id: UUID
    format: Literal["pdf", "docx"]
    status: Literal["completed", "partial"]
    storage_path: str
    file_size_bytes: int = Field(ge=0)
    generated_at: datetime


def build_reports_completed_message(
    payload: ReportsCompletedPayload,
    source_service: str = "reporter-worker",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """
    Convenience builder. Always use this - never construct the dict manually.
    """
    return build_envelope(
        event_type="report.generated",
        payload=payload.model_dump(mode="json"),
        source_service=source_service,
        schema_version="1.0",
        trace_id=trace_id,
    )
