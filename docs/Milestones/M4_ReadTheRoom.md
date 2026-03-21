AttackBot — M4 Low-Level Implementation Plan
Version: 1.5 | Date: 2026-03-21 Picks up directly from M3 completion state. Every step produces something testable. Read the full step before writing any code.

Pre-flight Checklist
Before writing any M4 code, confirm the M3 baseline is intact:

# All containers healthy
docker compose -f infra/docker-compose.yml --env-file .env ps

# Migration at 003
docker compose -f infra/docker-compose.yml --env-file .env run --rm migrate `
  alembic -c /app/backend/migrations/alembic.ini current
# Expected: "003 (head)"

# Scraper healthy
curl http://localhost:8001/api/v1/health

# Core Engine healthy
curl http://localhost:8002/api/v1/health

# Reporter skeleton healthy
curl http://localhost:8003/api/v1/health

# At least one completed or partial scan exists
curl http://localhost:8002/api/v1/scans
If any of these fail, fix M3 before starting M4.

File Map
Files you will create or replace in M4 (in implementation order):

backend/
├── migrations/versions/
│   └── 004_reporter.py                         ← NEW — reports + reproduction_packs
├── shared/
│   ├── schemas/
│   │   ├── report_jobs.py                      ← UPDATE — keep v1 shape, add optional report_ids
│   │   └── reports_completed.py                ← NEW — reports.completed payload schema
│   └── queue.py                                ← UPDATE — active declare helper for reports.completed
├── services/core_engine/
│   └── main.py                                 ← UPDATE — add evidence read API for reporter
├── services/reporter/
│   ├── requirements.txt                        ← NEW — reporter-only dependencies
│   ├── Dockerfile                              ← REPLACE — repo-root build context safe
│   ├── config.py                               ← NEW — replaces skeleton config
│   ├── models.py                               ← NEW — internal dataclasses
│   ├── repository.py                           ← NEW — ReportRepository
│   ├── clients/
│   │   ├── __init__.py                         ← NEW
│   │   ├── core_engine.py                      ← NEW — scan + findings + evidence fetch
│   │   ├── scraper.py                          ← NEW — program + scope fetch
│   │   └── attack_graph.py                     ← NEW — stubbed graceful fallback until M8
│   ├── parsing.py                              ← NEW — ParsedScan normalization
│   ├── reproduction.py                         ← NEW — deterministic repro packs
│   ├── evidence.py                             ← NEW — evidence fetch + embed logic
│   ├── renderers/
│   │   ├── __init__.py                         ← NEW
│   │   ├── base.py                             ← NEW — shared render model
│   │   ├── theme.py                            ← NEW — severity colours, fonts, spacing
│   │   ├── sections.py                         ← NEW — reusable section planners
│   │   ├── pdf.py                              ← NEW — PDF generator
│   │   └── docx.py                             ← NEW — DOCX generator
│   ├── storage.py                              ← NEW — MinIO upload + presign wrapper
│   ├── publisher.py                            ← NEW — reports.completed publisher
│   ├── metrics.py                              ← NEW — Prometheus metrics
│   ├── watchdog.py                             ← NEW — stale report recovery
│   ├── report_task.py                          ← NEW — Celery task entry
│   ├── worker.py                               ← REPLACE skeleton
│   └── main.py                                 ← REPLACE skeleton
tests/
├── fixtures/
│   └── reporter/
│       ├── scan_with_findings.json             ← NEW
│       ├── scan_zero_findings.json             ← NEW
│       ├── findings_verified.json              ← NEW
│       ├── findings_zero.json                  ← NEW
│       ├── finding_evidence.json               ← NEW
│       ├── program_detail.json                 ← NEW
│       ├── program_scope.json                  ← NEW
│       ├── exploit_chains.json                 ← NEW
│       └── golden/
│           ├── no_findings_summary.txt         ← NEW
│           ├── repro_pack_xss.txt              ← NEW
│           ├── report_outline_pdf.txt          ← NEW
│           └── report_outline_docx.txt         ← NEW
├── unit/
│   └── test_reporter.py                        ← NEW — 80%+ coverage target
├── integration/
│   └── test_reporter_pipeline.py               ← NEW — queue → DB → MinIO → API
└── e2e/
    └── test_report_download_flow.py            ← NEW — full chain + regenerate chain
Note: backend/services/core_engine/pipeline/aggregator.py does not require a code change in M4. The organic producer remains valid because report_ids is optional in the updated shared schema. Rebuilding the Core Engine image is still required so it picks up the updated shared schema package.

Step 4.1 — Database Migration: 004_reporter
File: backend/migrations/versions/004_reporter.py

This migration introduces only the reporter domain:

reports
reproduction_packs
"""
Reporter schema: reports, reproduction_packs

Revision ID: 004
Revises: 003
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("report_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("scan_id", UUID(as_uuid=True), sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", UUID(as_uuid=True), sa.ForeignKey("programs.program_id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.VARCHAR(), nullable=False),      # pdf | docx
        sa.Column("status", sa.VARCHAR(), nullable=False),      # generating | completed | partial | failed
        sa.Column("storage_path", sa.VARCHAR(), nullable=True),
        sa.Column("file_size_bytes", sa.INTEGER(), nullable=True),
        sa.Column("error_detail", sa.TEXT(), nullable=True),
        sa.Column("generated_at", sa.TIMESTAMPTZ(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMPTZ(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_reports_scan_id", "reports", ["scan_id"])
    op.create_index("ix_reports_program_id", "reports", ["program_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_format", "reports", ["format"])
    op.create_unique_constraint("uq_reports_scan_format", "reports", ["scan_id", "format"])

    op.create_table(
        "reproduction_packs",
        sa.Column("pack_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("finding_id", UUID(as_uuid=True), sa.ForeignKey("findings.finding_id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_id", UUID(as_uuid=True), sa.ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False),
        sa.Column("curl_command", sa.TEXT(), nullable=True),
        sa.Column("http_request_raw", sa.TEXT(), nullable=True),
        sa.Column("browser_steps", sa.TEXT(), nullable=True),
        sa.Column("notes", sa.TEXT(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMPTZ(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_reproduction_packs_report_id", "reproduction_packs", ["report_id"])
    op.create_index("ix_reproduction_packs_finding_id", "reproduction_packs", ["finding_id"])
    op.create_unique_constraint("uq_reproduction_packs_report_finding", "reproduction_packs", ["report_id", "finding_id"])


def downgrade() -> None:
    pass
Step 4.2 — Queue Contracts and Schema Compatibility
Files:

backend/shared/schemas/report_jobs.py
backend/shared/schemas/reports_completed.py
backend/shared/queue.py
Reporter consumes report.jobs and publishes reports.completed.

Critical schema decisions
Keep exploit_chains as a list of objects, not UUID strings
Add report_ids as an optional field
Support two valid producers:
Core Engine organic pipeline path: report_ids absent
Reporter regenerate API path: report_ids present
report.jobs payload contract for M4
{
  "event_type": "scan.completed",
  "scan_id": "uuid",
  "program_id": "uuid",
  "status": "completed",
  "partial": false,
  "has_findings": true,
  "finding_count": 12,
  "verified_count": 9,
  "severity_breakdown": {
    "critical": 1,
    "high": 3,
    "medium": 5,
    "low": 0,
    "info": 0
  },
  "exploit_chains": [
    {
      "chain_id": "uuid",
      "chain_name": "Stored XSS to Admin Takeover",
      "combined_severity": "critical",
      "step_count": 3
    }
  ],
  "formats_requested": ["pdf", "docx"],
  "report_ids": {
    "pdf": "uuid",
    "docx": "uuid"
  },
  "include_evidence_screenshots": true,
  "timestamp": "2026-03-21T11:30:00Z"
}
report_ids rules
optional overall
if present, keys must exactly match requested formats
values must be UUID strings
if absent, worker allocates rows itself using create_or_reset_report()
if present, worker must reuse those exact IDs and must not allocate replacements
Worker branching rule
if payload.report_ids is present:
    use provided report_id for each format
    call mark_generating(report_id)
else:
    allocate or reset row with create_or_reset_report(scan_id, program_id, format)
This preserves both the organic scan path and the regenerate path.

reports.completed payload contract
{
  "event_type": "report.generated",
  "report_id": "uuid",
  "scan_id": "uuid",
  "program_id": "uuid",
  "format": "pdf",
  "status": "completed",
  "storage_path": "reports/uuid/report.pdf",
  "file_size_bytes": 124882,
  "generated_at": "2026-03-21T11:31:22Z",
  "timestamp": "2026-03-21T11:31:22Z"
}
Queue behavior rules
report.jobs is consumed with task_acks_late=True
exhausted retries land in report.jobs.dlq
one reports.completed event per terminal artifact
formats_requested empty => default to ["pdf", "docx"]
partial scans still generate reports
has_findings=false still generates reports
Critical: reports.completed queue declaration
Add an active declaration helper to backend/shared/queue.py:

async def ensure_queue(self, queue_name: str, durable: bool = True) -> None:
    if self._channel is None:
        raise QueueConnectionError("Publisher not connected.")
    await self._channel.declare_queue(queue_name, durable=durable)
Reporter startup must call:

await publisher.ensure_queue(Queues.REPORTS_COMPLETED)
Step 4.3 — Reporter-Specific Dependencies and Dockerfile
Files:

backend/services/reporter/requirements.txt
backend/services/reporter/Dockerfile
Use reporter-only dependencies. Do not put PDF/DOCX libraries in requirements/base.txt.

requirements.txt
-r /app/requirements/base.txt
python-docx==1.1.2
reportlab==4.2.2
minio==7.2.7
Pillow==10.4.0
prometheus-client==0.20.0
Dockerfile
This Dockerfile assumes the build context is the repo root, matching repo conventions.

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements/base.txt /app/requirements/base.txt
COPY backend/services/reporter/requirements.txt /app/backend/services/reporter/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/services/reporter/requirements.txt

COPY backend/shared /app/backend/shared
COPY backend/services/reporter /app/backend/services/reporter

RUN mkdir -p /tmp/attackbot-reports

EXPOSE 8003
CMD ["uvicorn", "backend.services.reporter.main:app", "--host", "0.0.0.0", "--port", "8003"]
Worker image note
reporter-worker uses this same image. docker-compose.yml overrides the container command to run Celery instead of Uvicorn. There is no separate worker Dockerfile.

Critical temp directory rule
Enforce temp directory existence twice:

Dockerfile: RUN mkdir -p /tmp/attackbot-reports
service startup: Path(settings.temp_output_dir).mkdir(parents=True, exist_ok=True)
Step 4.4 — Reporter Config: config.py
File: backend/services/reporter/config.py

from backend.shared.config import BaseServiceConfig


class ReporterConfig(BaseServiceConfig):
    service_name: str = "reporter"
    port: int = 8003

    core_engine_api_url: str = "http://core-engine:8002"
    scraper_api_url: str = "http://scraper:8001"
    attack_graph_api_url: str = "http://attack-graph-engine:8006"

    upstream_timeout_seconds: int = 30
    upstream_connect_timeout_seconds: int = 5

    default_formats: list[str] = ["pdf", "docx"]

    reports_bucket: str = "reports"
    evidence_bucket: str = "evidence"
    report_presign_expiry_seconds: int = 900

    report_watchdog_interval_seconds: int = 300
    report_watchdog_stale_minutes: int = 30

    max_inline_evidence_images_per_finding: int = 2
    include_raw_http_appendix: bool = True
    temp_output_dir: str = "/tmp/attackbot-reports"

    report_task_max_retries: int = 3
    report_task_retry_backoff_seconds: list[int] = [60, 300, 600]
Step 4.5 — Core Engine Evidence API Addition
File: backend/services/core_engine/main.py

Reporter cannot query finding_evidence directly. Add this read-only nested endpoint:

GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence
Why this path
It stays consistent with the existing Core Engine scan-scoped API pattern.

Response
{
  "finding_id": "uuid",
  "scan_id": "uuid",
  "items": [
    {
      "evidence_id": "uuid",
      "artifact_type": "screenshot",
      "storage_path": "evidence/finding_uuid/screenshot.png",
      "description": "Browser screenshot",
      "captured_at": "2026-03-21T09:10:11Z"
    }
  ]
}
Rules:

empty list if no evidence exists
404 only if finding does not exist for the given scan
Reporter calls this only when include_evidence_screenshots=true
Step 4.6 — Internal Models: models.py
File: backend/services/reporter/models.py

from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID


Severity = Literal["critical", "high", "medium", "low", "info"]


@dataclass
class ProgramInfo:
    program_id: UUID
    platform: str
    handle: str
    name: str
    url: str | None
    bounty_type: str | None
    max_bounty: int | None
    is_active: bool


@dataclass
class ScopeEntry:
    scope_type: str
    asset_type: str
    value: str
    notes: str | None = None


@dataclass
class EvidenceArtifact:
    artifact_type: str
    storage_path: str | None
    description: str | None = None
    exists: bool = False
    local_tmp_path: str | None = None


@dataclass
class ParsedFinding:
    finding_id: UUID
    title: str
    vulnerability_type: str
    severity: Severity
    cvss_score: float | None
    cvss_vector: str | None
    affected_url: str
    affected_parameter: str | None
    description: str
    reproduction_steps: str | None
    source: str | None
    raw_output: dict | None
    evidence: list[EvidenceArtifact] = field(default_factory=list)


@dataclass
class ExploitChain:
    chain_id: UUID
    chain_name: str
    combined_severity: str
    step_count: int
    description: str | None = None


@dataclass
class ReproductionPackDraft:
    finding_id: UUID
    curl_command: str
    http_request_raw: str
    browser_steps: str
    notes: str | None = None
    is_fallback: bool = False


@dataclass
class ParsedScan:
    scan_id: UUID
    status: str
    partial: bool
    finding_count: int
    verified_count: int
    severity_breakdown: dict[str, int]
    include_evidence_screenshots: bool
    program: ProgramInfo
    scope: list[ScopeEntry]
    findings: list[ParsedFinding]
    exploit_chains: list[ExploitChain] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.findings) == 0
Step 4.7 — Repository: repository.py
File: backend/services/reporter/repository.py

Critical UPSERT for create_or_reset_report()
Because uq_reports_scan_format exists, this method must use INSERT ... ON CONFLICT directly.

async def create_or_reset_report(self, scan_id: str, program_id: str, format: str) -> str:
    result = await self.session.execute(text("""
        INSERT INTO reports (
            report_id, scan_id, program_id, format, status,
            storage_path, file_size_bytes, error_detail, generated_at, created_at
        ) VALUES (
            :report_id, :scan_id, :program_id, :format, 'generating',
            NULL, NULL, NULL, NULL, NOW()
        )
        ON CONFLICT (scan_id, format) DO UPDATE SET
            program_id = EXCLUDED.program_id,
            status = 'generating',
            storage_path = NULL,
            file_size_bytes = NULL,
            error_detail = NULL,
            generated_at = NULL
        RETURNING report_id
    """), {
        "report_id": str(uuid.uuid4()),
        "scan_id": scan_id,
        "program_id": program_id,
        "format": format,
    })
    row = result.fetchone()
    await self.session.commit()
    return str(row[0])
Explicit mark_generating() behavior
This method is required for the regenerate path where stable report_ids were already allocated before enqueue.

async def mark_generating(self, report_id: str) -> None:
    await self.session.execute(text("""
        UPDATE reports
        SET status = 'generating',
            error_detail = NULL
        WHERE report_id = :report_id
    """), {"report_id": report_id})
    await self.session.commit()
Do not replace this with create_or_reset_report() inside the worker when report_ids are already known.

Required methods
create_or_reset_report()
mark_generating()
mark_completed()
mark_partial()
mark_failed()
replace_reproduction_packs()
list_reports()
get_report()
get_reports_by_scan()
get_stale_generating_reports()
mark_partial() rule
Partial reports are downloadable, so set generated_at=NOW().

Ownership rule
API or producer side may call create_or_reset_report()
worker may call create_or_reset_report() only when processing organic messages without report_ids
worker uses mark_generating(report_id) when report_ids are present
Step 4.8 — Upstream API Clients: clients/
Files:

clients/core_engine.py
clients/scraper.py
clients/attack_graph.py
Core Engine client
Fetch:

GET /api/v1/scans/{scan_id}
GET /api/v1/scans/{scan_id}/findings?verified=true
GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence
Scraper client
Fetch:

GET /api/v1/programs/{program_id}
GET /api/v1/programs/{program_id}/scope
Attack Graph client
Planned endpoint:

GET /api/v1/chains/{chain_id}
Critical M4 note
This endpoint does not exist yet. In M4:

exploit_chains objects from report.jobs may be used for lightweight summary text only
no deep chain fetch is expected to succeed
if fetch fails, omit detailed chain sections and add appendix note: Exploit chain detail service not yet available in this milestone.
Step 4.9 — ParsedScan Normalization: parsing.py
File: backend/services/reporter/parsing.py

Builder contract
class ParsedScanBuilder:
    def build(
        self,
        scan_payload: dict,
        findings_payload: list[dict],
        program_payload: dict,
        scope_payload: dict,
        exploit_chain_refs: list[dict],
        include_evidence_screenshots: bool,
    ) -> ParsedScan:
        ...
Rules
include only is_verified=True findings
normalize severities to lowercase canonical values
sort findings by severity, then title, then URL
keep exploit_chain_refs object shape from queue contract
if no findings, return clean report mode
if no findings, ignore exploit chains and log inconsistency if present
Step 4.10 — Reproduction Packs: reproduction.py
File: backend/services/reporter/reproduction.py

Deterministic formatting rules
sort headers
sort query parameters
sort JSON body keys
stable browser step wording
redact secrets
never include temp paths or MinIO URLs
Per-finding failure handling
Do not let one failure break the whole loop:

packs = []
pack_errors = []

for finding in findings:
    try:
        packs.append(build_pack(finding))
    except Exception as exc:
        pack_errors.append(f"{finding.finding_id}:pack_generation_failed")
        packs.append(build_fallback_pack(finding, str(exc)))
Status rule
If any fallback pack is used:

mark report partial
record a machine-readable reason such as repro_pack_fallback
Step 4.11 — Evidence Fetch and Temp File Cleanup: evidence.py
File: backend/services/reporter/evidence.py

Data source
Evidence metadata comes only from:

GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence
Respect include_evidence_screenshots
If false:

do not call evidence API
do not download evidence
do not render screenshot sections
Temp file cleanup
Downloaded evidence files must always be removed after embed attempt. Use try/finally:

tmp_path = await storage.download_temp_object(...)
try:
    embed_image(tmp_path)
finally:
    if tmp_path and os.path.exists(tmp_path):
        os.unlink(tmp_path)
Missing artifact rules
Condition	Result
metadata exists, object exists	embed
metadata exists, object missing	note + partial
API empty list	continue
API unavailable and screenshots enabled	continue + partial
Step 4.12 — Rendering Architecture and Temp File Cleanup
Files:

renderers/sections.py
renderers/pdf.py
renderers/docx.py
Shared section order
For finding reports:

Cover
Executive Summary
Scope Overview
Findings Table
Per-Finding Detail
Exploit Chains or Chain Availability Note
Appendix — Reproduction Packs
Appendix — Evidence Notes
For clean reports:

Cover
Executive Summary
Scope Overview
No Findings Statement
Coverage Notes
Appendix — Scan Metadata
include_evidence_screenshots wiring
Renderers must check ParsedScan.include_evidence_screenshots before any image section creation.

Render artifact cleanup
Local rendered files must be deleted after upload attempt. Use:

output_path = build_output_path(...)
try:
    await generator.generate(..., output_path=output_path)
    storage_path, file_size = await storage.upload_report(...)
finally:
    if os.path.exists(output_path):
        os.unlink(output_path)
Step 4.13 — PDF Generator: renderers/pdf.py
Use reportlab.platypus.

Validation after render
file exists
size > 0
first bytes are %PDF
Screenshot failure rule
If image load fails:

insert note
continue render
return partial reason
Step 4.14 — DOCX Generator: renderers/docx.py
Use python-docx.

Validation after render
file exists
size > 0
archive opens as zip
word/document.xml exists
DOCX golden-file normalization
Use a test utility that:

opens DOCX with python-docx
concatenates paragraph text in order
appends table rows as |-joined cells
normalizes whitespace
compares resulting text to report_outline_docx.txt
Do not compare binary .docx files.

Step 4.15 — Storage and Presigned Download Flow: storage.py
Required methods
upload_report()
object_exists()
download_temp_object()
get_presigned_download_url()
Storage path rules
reports/{report_id}/report.pdf
reports/{report_id}/report.docx
Security rules
no public buckets
no anonymous download
presigned GET only
do not log full presigned URLs
Step 4.16 — Completion Publisher: publisher.py
Required behavior
ensure reports.completed exists at startup
publish one event per terminal artifact
keep report terminal even if publish fails
never delete artifact because publish failed
Step 4.17 — Metrics and Logging: metrics.py
Prefix all custom metrics with attackbot_reporter_ to avoid collisions with FastAPI instrumentator metrics.

Required metrics
attackbot_reporter_generation_total
attackbot_reporter_generation_duration_seconds
attackbot_reporter_generation_failures_total
attackbot_reporter_download_requests_total
attackbot_reporter_presign_duration_seconds
attackbot_reporter_evidence_missing_total
attackbot_reporter_zero_findings_total
attackbot_reporter_partial_generation_total
Step 4.18 — Task Entry, Retry Backoff, and Failure Taxonomy: report_task.py
File: backend/services/reporter/report_task.py

High-level flow
receive report.jobs
→ validate envelope + payload
→ determine formats
→ for each format:
    if payload.report_ids contains format:
        use existing report_id
        mark report row generating
    else:
        allocate/reset row with create_or_reset_report()
    fetch scan + findings + program + scope
    optionally fetch evidence metadata
    optionally attempt attack graph detail
    build ParsedScan
    build reproduction packs with fallback
    render artifact
    upload artifact
    update report row
    publish reports.completed
Critical dual-producer rule
The worker must support both:

organic Core Engine messages with no report_ids
regenerate API messages with stable report_ids
Example per-format orchestration
for format_name in formats:
    if payload.report_ids and format_name in payload.report_ids:
        report_id = payload.report_ids[format_name]
        await repository.mark_generating(report_id)
    else:
        report_id = await repository.create_or_reset_report(
            scan_id=payload.scan_id,
            program_id=payload.program_id,
            format=format_name,
        )

    result = await _generate_single_format_report(
        report_id=report_id,
        format_name=format_name,
        payload=payload,
    )
Critical retry backoff wiring
The configured backoff list must be used explicitly with self.retry():

def _retry_countdown(retries: int, backoff: list[int]) -> int:
    return backoff[min(retries, len(backoff) - 1)]

try:
    ...
except RetryableReportError as exc:
    countdown = _retry_countdown(
        self.request.retries,
        settings.report_task_retry_backoff_seconds,
    )
    raise self.retry(exc=exc, countdown=countdown)
Terminal status mapping
Failure	Status
Core Engine fetch fails	failed
Scraper fetch fails	failed
evidence fetch fails and screenshots enabled	partial
attack graph detail unavailable	partial
repro pack fallback used	partial
render fails	failed
upload fails	failed
publish after upload fails	keep completed/partial
Step 4.19 — Worker: worker.py
Replace the skeleton entirely.

Celery config
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_queue="report.jobs",
)
DLQ behavior
If retries exhaust:

message lands in report.jobs.dlq
report row should already be failed
watchdog remains secondary cleanup only
Compose startup order note
Keep the existing compose pattern where reporter-worker depends on reporter: condition: service_healthy. Do not remove that dependency in M4. Reporter startup is responsible for queue declaration before the worker begins steady-state processing.

Step 4.20 — Reporter API: main.py
Required endpoints
GET  /api/v1/reports
GET  /api/v1/reports/{report_id}
GET  /api/v1/reports/{report_id}/download
GET  /api/v1/scans/{scan_id}/reports
POST /api/v1/reports/generate
GET  /api/v1/health
POST /api/v1/reports/generate
This endpoint is mandatory because Flow says reports can be regenerated without rerunning a scan.

Request
{
  "scan_id": "uuid",
  "formats_requested": ["pdf", "docx"],
  "include_evidence_screenshots": true
}
Behavior
verify scan exists and is completed or partial
for each requested format, call create_or_reset_report() and collect the returned report_id
build report.jobs payload including report_ids
enqueue report.jobs
return 202 Accepted
Response body
{
  "scan_id": "uuid",
  "enqueued": true,
  "report_ids": {
    "pdf": "uuid",
    "docx": "uuid"
  }
}
GET /api/v1/reports/{report_id}/download
404 if missing
409 if generating
409 if failed
valid for completed and partial
Do not use 422 here.

GET /api/v1/health
Check:

Postgres
RabbitMQ
MinIO
Core Engine reachability
Scraper reachability
scheduler running
Attack Graph health visibility
Do not fail health because Attack Graph detail is not available in M4. Instead include an explicit component:

"attack_graph_engine": {
  "status": "degraded",
  "detail": "not_available_until_m8"
}
Step 4.21 — Watchdog: watchdog.py
Query
SELECT report_id, scan_id, format
FROM reports
WHERE status = 'generating'
  AND created_at < NOW() - INTERVAL '30 minutes'
ORDER BY created_at ASC
Action
For each stale row:

set status='failed'
set error_detail='watchdog_timeout'
increment failure metrics
log structured event
Recovery path:

POST /api/v1/reports/generate
Step 4.22 — No Findings Report Path
A zero-findings report must:

generate PDF and DOCX normally
not include empty findings tables
not include exploit chains
include program metadata and scope
upload to MinIO
be downloadable via presigned URL only
Suggested wording:

No verified findings were produced for this scan. This report reflects the completed scan state and the scope reviewed at generation time. It should not be interpreted as proof of absence of vulnerabilities beyond the tested coverage captured below.
Step 4.23 — Tests: tests/unit/test_reporter.py
Must-have unit tests
test_parsed_scan_filters_unverified_findings
test_zero_findings_returns_clean_mode
test_include_evidence_flag_false_skips_evidence_fetch
test_reproduction_pack_generation_uses_fallback_per_finding
test_create_or_reset_report_upserts_on_scan_id_format
test_mark_generating_updates_status_only
test_mark_partial_sets_generated_at
test_attack_graph_client_returns_chain_availability_note_until_m8
test_clean_mode_ignores_exploit_chains
test_docx_outline_extraction_is_text_based
test_reports_completed_queue_is_declared_before_publish
test_rendered_temp_file_deleted_after_upload
test_evidence_temp_file_deleted_after_embed
test_retry_backoff_uses_configured_countdown
test_generate_endpoint_returns_stable_report_ids_in_payload
test_worker_accepts_organic_message_without_report_ids
test_worker_reuses_provided_report_ids_when_present
Temp file cleanup test strategy
Keep these as unit tests by mocking filesystem side effects:

mock os.path.exists
mock os.unlink
optionally use tmp_path only to construct fake file paths
do not depend on real /tmp/attackbot-reports existing in CI
Golden-file approach
Only compare normalized text:

reproduction pack text
PDF section outline
DOCX extracted text outline
no-findings summary text
Step 4.24 — Integration Tests: tests/integration/test_reporter_pipeline.py
Required scenarios
Scenario A — normal findings report
report.jobs consumed
PDF + DOCX rows created
repro packs persisted
artifacts uploaded
two reports.completed events published
Scenario B — zero-findings report
verified findings endpoint returns []
artifact generated
content contains no-findings statement
Scenario C — missing screenshot object
Core Engine evidence API returns screenshot metadata
MinIO object missing
generation finishes partial
artifact still downloadable
Scenario D — evidence disabled by flag
include_evidence_screenshots=false
reporter does not call evidence API
report completes without screenshot sections
Scenario E — Attack Graph unavailable
chain refs present in queue payload
fallback path activates
report finishes partial
appendix note present
Scenario F — upload failure
MinIO upload fails
report row marked failed
no completion event emitted
Scenario G — retries exhausted to DLQ
force deterministic render failure
Celery exhausts retries
row ends failed
message visible in report.jobs.dlq
Scenario H — generate API returns pollable IDs
call POST /api/v1/reports/generate
assert report_ids returned
assert worker updates those same row IDs, not replacement rows
Scenario I — organic Core Engine message without report_ids
publish a valid Core Engine-style report.jobs message with no report_ids
assert worker allocates report rows
assert report generation still completes successfully
Step 4.25 — End-to-End Tests: tests/e2e/test_report_download_flow.py
M4 needs two e2e paths.

Path 1 — canonical organic flow
This path satisfies the Milestone DoD requirement: scrape -> scan -> report -> download

trigger scrape
→ scraper publishes scan.jobs
→ core engine completes scan
→ core engine publishes report.jobs without report_ids
→ reporter generates report rows and artifacts
→ call GET /api/v1/scans/{scan_id}/reports
→ choose report_id
→ call GET /api/v1/reports/{report_id}/download
→ fetch returned presigned URL
→ validate file bytes
Path 2 — regenerate flow
POST /api/v1/reports/generate
→ receive stable report_ids
→ wait for those exact report rows to reach terminal state
→ call GET /api/v1/reports/{report_id}/download
→ fetch returned presigned URL
→ validate file bytes
Required assertions
PDF starts with %PDF
DOCX is a valid zip archive
returned URL expires
no direct anonymous bucket access works
returned report_id from generate endpoint remains the same terminal artifact ID
organic Core Engine-generated reports succeed even without report_ids
Step 4.26 — Verification Commands
Rebuild images
docker compose -f infra/docker-compose.yml --env-file .env `
  build --no-cache migrate core-engine reporter reporter-worker
Apply migration
docker compose -f infra/docker-compose.yml --env-file .env `
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini upgrade head
Start reporter before worker
Keep startup order explicit during verification so queue declaration and health are ready first:

docker compose -f infra/docker-compose.yml --env-file .env up -d core-engine reporter
docker compose -f infra/docker-compose.yml --env-file .env up -d reporter-worker
Check logs
docker compose -f infra/docker-compose.yml --env-file .env logs -f reporter
docker compose -f infra/docker-compose.yml --env-file .env logs -f reporter-worker
Run tests
pytest tests/unit/test_reporter.py -q --cov=backend/services/reporter --cov-report=term-missing
pytest tests/integration/test_reporter_pipeline.py -q
pytest tests/e2e/test_report_download_flow.py -q
Trigger regenerate flow via API
curl -X POST http://localhost:8003/api/v1/reports/generate `
  -H "Content-Type: application/json" `
  -d "{\"scan_id\":\"<SCAN_ID>\",\"formats_requested\":[\"pdf\",\"docx\"],\"include_evidence_screenshots\":true}"
Trigger organic full chain
curl -X POST "http://localhost:8001/api/v1/scrape/trigger?platform=hackerone"
Then watch scan completion, report.jobs publication, report creation, and final download flow.

Common Pitfalls and Critical Gotchas
1. Docker build context matters
Use repo-root-safe COPY paths only. Never use ../../ in Dockerfile COPY.

2. Do not break report.jobs schema shape in M4
Keep exploit_chains as object refs unless you intentionally bump to schema 2.0.

3. report_ids is optional, not required
Organic Core Engine messages will not have it. Regenerate API messages will.

4. Stable report_id ownership must be single-source per message
If report_ids are present, worker updates those rows. If absent, worker allocates rows.

5. Evidence needs an API
Do not query finding_evidence directly from Reporter.

6. include_evidence_screenshots must actually control behavior
If false, skip evidence fetch and rendering completely.

7. Use UPSERT, not SELECT-then-INSERT
uq_reports_scan_format requires it.

8. Clean up temp files
Delete rendered artifacts and downloaded evidence files in finally blocks.

9. Use explicit retry countdowns
Config backoff lists do nothing until wired into self.retry(countdown=...).

10. POST /api/v1/reports/generate should return report IDs
Otherwise clients cannot poll deterministically.

11. Attack Graph is intentionally degraded in M4
Surface that in health and report notes so operators are not confused.

12. Use 409 for failed/generating download conflicts
Do not use 422 for resource state errors.

13. Declare reports.completed before publishing
Passive declare alone is not safe on cold boot.

14. Set PYTHONPATH=/app
Without it, backend.* imports inside the container will fail.

15. Test the organic path, not just regenerate
Milestone DoD requires the real scrape -> scan -> report -> download chain.

Definition of Done Checklist
M4 is done only when all of the following are true:

004_reporter migration applies cleanly
reports and reproduction_packs tables exist
report.jobs keeps schema-compatible exploit_chains object refs
report_ids is optional and supports both organic and regenerate producers
GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence exists in Core Engine
POST /api/v1/reports/generate exists and returns stable report_ids
report rows are created or reset before enqueue for regenerate requests
worker updates existing report rows when report_ids are present
worker creates or resets report rows when organic messages omit report_ids
create_or_reset_report() is implemented as true UPSERT on (scan_id, format)
mark_generating() is implemented as explicit targeted update
partial reports set generated_at
reproduction packs are deterministic and have per-finding fallback behavior
zero-findings scans produce valid "No Findings" PDF and DOCX artifacts
renderers respect include_evidence_screenshots
evidence embedding degrades gracefully when objects are missing
rendered report temp files are deleted after upload attempt
downloaded evidence temp files are deleted after embed attempt
Attack Graph fallback is documented, visible in health, and tested
artifacts upload to reports/{report_id}/report.{format}
downloads use presigned URLs only
reports bucket is not public
reports.completed queue is declared before first publish
configured retry backoff is actually used by Celery retry calls
one reports.completed message is published per terminal artifact
stale generating rows are marked failed by watchdog
report.jobs exhausted retries land in report.jobs.dlq
GET /api/v1/reports/{report_id}/download returns 409 for generating and failed
/api/v1/reports, /api/v1/reports/{id}, /api/v1/reports/{id}/download, /api/v1/scans/{scan_id}/reports, /api/v1/reports/generate, and /api/v1/health all work
reporter-worker still depends on healthy reporter startup in compose
reporter image sets PYTHONPATH=/app
unit, integration, and e2e tests pass
reporter coverage is at least 80%
generation latency and failure metrics are visible in Prometheus/Grafana
canonical e2e flow works: scrape -> scan -> report -> download
regenerate flow also works with stable returned report_ids
At the end of M4, AttackBot has a real reporting layer that stays aligned with the architecture: queue-driven, API-boundary safe, evidence-aware, zero-finding safe, temp-file disciplined, stable-ID preserving when available, backward-compatible with organic queue producers, and explicitly human-in-the-loop for final submission.