# backend/shared/schemas/scan_jobs.py
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.shared.schemas.envelope import build_envelope


# ── Sub-schemas ────────────────────────────────────────────────────────────

class ScopeEntry(BaseModel):
    """One typed scope entry from program_scopes."""

    asset_type: Literal["url", "domain", "wildcard_domain", "ip_range", "mobile_app", "api"]
    value: str
    notes: str | None = None


class ScopeDefinition(BaseModel):
    in_scope: list[ScopeEntry] = Field(min_length=1)
    out_of_scope: list[ScopeEntry] = []


class FeatureFlags(BaseModel):
    """
    Pipeline stage gates. All flags default to their production-safe default.
    Extra flags are ignored for forward compatibility.
    """

    model_config = ConfigDict(extra="ignore")

    # Enabled by default
    asset_discovery: bool = True
    fingerprinting: bool = True
    enumeration: bool = True
    nuclei: bool = True
    xss: bool = True
    cors: bool = True
    secret_js: bool = True
    browser_session: bool = True
    api_fuzzing: bool = True

    # Disabled by default — require explicit opt-in
    crlf: bool = False
    sqli: bool = False
    ssrf: bool = False
    takeover: bool = False
    secret_repo: bool = False
    scenario_runner: bool = False
    ai_hypothesis: bool = False
    idor_verification: bool = False  # gates two-session bootstrap (M5)


# ── Primary payload ────────────────────────────────────────────────────────

class ScanJobsPayload(BaseModel):
    """
    Payload schema for queue: scan.jobs
    Event type:     program.scraped
    Schema version: 1.0
    Producer:       scraper
    Consumer:       core-worker

    Version history:
        1.0 — initial schema
    """

    model_config = ConfigDict(extra="ignore")

    # ── Program identity ───────────────────────────────────────────────
    program_id: UUID
    platform: Literal["hackerone", "bugcrowd", "intigriti", "yeswehack"]
    handle: str

    # ── Scope ──────────────────────────────────────────────────────────
    scope: ScopeDefinition = Field(
        description=(
            "Fully resolved scope from program_scopes. "
            "Stage 0 builds ScopeFilter directly from this."
        ),
    )

    # ── Optional assets hint ───────────────────────────────────────────
    summary_file: str | None = Field(
        default=None,
        description="MinIO path to program summary artifact, if available.",
    )

    # ── Scan configuration ─────────────────────────────────────────────
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    priority: int = Field(default=1, ge=1, le=10)
    scan_timeout_seconds: int = Field(default=14400, ge=300, le=86400)
    max_concurrent_requests: int = Field(default=10, ge=1, le=50)

    @field_validator("scope")
    @classmethod
    def scope_must_have_entries(cls, v: ScopeDefinition) -> ScopeDefinition:
        if not v.in_scope:
            raise ValueError("scope.in_scope must contain at least one entry")
        return v


# ── Envelope builder helper ────────────────────────────────────────────────

def build_scan_job_message(
    payload: ScanJobsPayload,
    source_service: str = "scraper",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """
    Convenience builder. Always use this — never construct the dict manually.

    Example:
        msg = build_scan_job_message(
            ScanJobsPayload(program_id=..., platform="hackerone", handle="...", scope=...),
            source_service="scraper",
        )
        await publisher.publish(Queues.SCAN_JOBS, msg)
    """
    return build_envelope(
        event_type="program.scraped",
        payload=payload.model_dump(mode="json"),
        source_service=source_service,
        schema_version="1.0",
        trace_id=trace_id,
    )