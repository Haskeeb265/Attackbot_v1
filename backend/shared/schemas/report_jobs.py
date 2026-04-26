# backend/shared/schemas/report_jobs.py
from typing import Any, Literal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field

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


# ── V2 Embedded Data Schemas (for eliminating HTTP calls) ────────────────

class FindingData(BaseModel):
    """Embedded finding data to avoid HTTP calls to Core Engine."""

    finding_id: UUID
    title: str
    severity: str = "unknown"
    vulnerability_type: str | None = None
    cvss_score: float | None = None
    cvss_vector: str | None = None
    affected_url: str | None = None
    affected_parameter: str | None = None
    description: str | None = None
    reproduction_steps: str | None = None
    is_verified: bool = False
    is_false_positive: bool = False
    false_positive_reason: str | None = None
    deduplication_hash: str | None = None
    source: str | None = None
    raw_output: dict | None = None
    created_at: datetime | None = None
    program_id: UUID | None = None


class EvidenceData(BaseModel):
    """Embedded evidence data to avoid HTTP calls to Core Engine."""

    evidence_id: UUID
    finding_id: UUID | None = None
    artifact_type: str | None = None
    storage_path: str | None = None
    description: str | None = None
    captured_at: datetime | None = None


class ScanSummary(BaseModel):
    """Summary of scan to avoid HTTP calls to Core Engine."""

    scan_id: UUID
    program_id: UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str
    total_findings: int = 0
    severity_breakdown: dict = Field(default_factory=dict)
    partial_detail: dict | None = None
    error_detail: str | None = None


# ── Primary payload ────────────────────────────────────────────────────────

class ReportJobsPayload(BaseModel):
    """
    Payload schema for queue: report.jobs
    Event type:     scan.completed
    Schema version: 1.0 or 2.0 (with embedded data)
    Producer:       core-engine (core-worker)
    Consumer:       reporter-worker

    Note: Failed scans (failed_scope, failed_internal, failed_auth) never
    reach this queue. Only completed and partial scans are reported.

    Version history:
        1.0 — initial schema
        2.0 — embedded data (findings, evidence) to eliminate HTTP calls
    """

    model_config = ConfigDict(extra="ignore")

    # ── Scan identity ──────────────────────────────────────────────────
    scan_id: UUID
    program_id: UUID

    # ── Scan outcome ───────────────────────────────────────────────────
    status: Literal["completed", "partial"] = Field(
        default="completed",
        description="Scan completion status",
    )
    partial_stages: list[str] = Field(
        default_factory=list,
        description="Names of stages with non-fatal failures. Noted in Executive Summary.",
    )

    # ── Finding summary ────────────────────────────────────────────────
    has_findings: bool = Field(
        default=False,
        description="Whether the scan has any findings",
    )
    finding_count: int = Field(
        default=0,
        ge=0,
        description="Total number of findings",
    )
    verified_count: int = Field(
        default=0,
        ge=0,
        description="Number of verified findings",
    )
    severity_breakdown: SeverityBreakdown = Field(
        default_factory=SeverityBreakdown,
        description="Breakdown of findings by severity",
    )

    # ── Exploit chains ─────────────────────────────────────────────────
    exploit_chains: list[ExploitChainRef] = Field(default_factory=list)

    # ── Report generation parameters ──────────────────────────────────
    formats_requested: list[Literal["pdf", "docx", "json"]] = Field(
        default_factory=lambda: ["pdf", "docx"],
    )
    report_ids: dict[Literal["pdf", "docx"], UUID] | None = None
    include_evidence_screenshots: bool = Field(default=True)

    # ── V2: Embedded data (eliminates HTTP calls) ────────────────────
    payload_version: int = Field(default=2, ge=1, description="1=legacy, 2=embedded data")
    scan_summary: ScanSummary | None = Field(
        default=None,
        description="Embedded scan summary to avoid HTTP call to Core Engine"
    )
    findings: list[FindingData] = Field(
        default_factory=list,
        description="Embedded findings to avoid HTTP calls to Core Engine"
    )
    evidence: list[EvidenceData] = Field(
        default_factory=list,
        description="Embedded evidence to avoid HTTP calls to Core Engine"
    )

    # Computed fields for backward compatibility
    def is_legacy(self) -> bool:
        """Check if this is a legacy payload without embedded data."""
        return self.payload_version < 2

    def has_embedded_data(self) -> bool:
        """Check if this payload has embedded data."""
        return self.payload_version >= 2 and len(self.findings) > 0

    @field_validator("finding_count")
    @classmethod
    def validate_finding_count_consistency(cls, v: int, info: Any) -> int:
        has_findings = info.data.get("has_findings")
        if has_findings is True and v == 0:
            raise ValueError("has_findings=True but finding_count=0. Inconsistent state.")
        if has_findings is False and v > 0:
            raise ValueError("has_findings=False but finding_count>0. Inconsistent state.")
        return v

    @field_validator("formats_requested", mode="before")
    @classmethod
    def normalize_formats_requested(cls, v: Any) -> list[str]:
        # Legacy alias used by some tests/code paths.
        if isinstance(v, dict) and "formats" in v:
            v = v.get("formats")
        if v is None:
            return ["pdf", "docx"]
        if isinstance(v, list) and len(v) == 0:
            # Compatibility rule for M4: empty list means "use defaults".
            return ["pdf", "docx"]
        return v

    @model_validator(mode="before")
    @classmethod
    def map_legacy_formats_field(cls, values: Any) -> Any:
        if isinstance(values, dict) and "formats_requested" not in values and "formats" in values:
            values = dict(values)
            values["formats_requested"] = values.pop("formats")
        return values

    @model_validator(mode="after")
    def validate_report_ids_match_formats(self) -> "ReportJobsPayload":
        if self.report_ids is None:
            return self
        requested = set(self.formats_requested)
        provided = set(self.report_ids.keys())
        if requested != provided:
            raise ValueError(
                "report_ids keys must exactly match formats_requested when report_ids is provided."
            )
        return self


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
        schema_version="2.0",
        trace_id=trace_id,
    )
