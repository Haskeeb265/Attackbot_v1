# backend/shared/schemas/report_jobs.py
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.shared.schemas.envelope import build_envelope


# ── Sub-schemas ────────────────────────────────────────────────────────────

class SeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low + self.informational


class ExploitChainRef(BaseModel):
    """Lightweight reference — full data fetched by Reporter from Postgres."""

    chain_id: UUID
    chain_name: str
    combined_severity: Literal["critical", "high", "medium", "low", "informational"]
    step_count: int


# ── Primary payload ────────────────────────────────────────────────────────

class ReportJobsPayload(BaseModel):
    """
    Payload schema for queue: report.jobs
    Event type:     scan.completed
    Schema version: 1.0
    Producer:       core-engine (core-worker)
    Consumer:       reporter-worker

    Note: Failed scans (failed_scope, failed_internal, failed_auth) never
    reach this queue. Only completed and partial scans are reported.

    Version history:
        1.0 — initial schema
    """

    model_config = ConfigDict(extra="ignore")

    # ── Scan identity ──────────────────────────────────────────────────
    scan_id: UUID
    program_id: UUID

    # ── Scan outcome ───────────────────────────────────────────────────
    status: Literal["completed", "partial"]
    partial_stages: list[str] = Field(
        default=[],
        description="Names of stages with non-fatal failures. Noted in Executive Summary.",
    )

    # ── Finding summary ────────────────────────────────────────────────
    has_findings: bool
    finding_count: int = Field(ge=0)
    verified_count: int = Field(ge=0)
    severity_breakdown: SeverityBreakdown

    # ── Exploit chains ─────────────────────────────────────────────────
    exploit_chains: list[ExploitChainRef] = Field(default=[])

    # ── Report generation parameters ──────────────────────────────────
    formats_requested: list[Literal["pdf", "docx"]] = Field(
        default=["pdf", "docx"],
        min_length=1,
    )
    include_evidence_screenshots: bool = Field(default=True)

    @field_validator("finding_count")
    @classmethod
    def validate_finding_count_consistency(cls, v: int, info: Any) -> int:
        has_findings = info.data.get("has_findings")
        if has_findings is True and v == 0:
            raise ValueError("has_findings=True but finding_count=0. Inconsistent state.")
        if has_findings is False and v > 0:
            raise ValueError("has_findings=False but finding_count>0. Inconsistent state.")
        return v


# ── Envelope builder helper ────────────────────────────────────────────────

def build_report_job_message(
    payload: ReportJobsPayload,
    source_service: str = "core-engine",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """
    Convenience builder. Always use this — never construct the dict manually.
    """
    return build_envelope(
        event_type="scan.completed",
        payload=payload.model_dump(mode="json"),
        source_service=source_service,
        schema_version="1.0",
        trace_id=trace_id,
    )