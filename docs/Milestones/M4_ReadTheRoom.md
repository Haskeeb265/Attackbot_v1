# AttackBot — M4 Low-Level Implementation Plan
> Version: 2.1 | Date: 2026-03-29
> Picks up directly from M3 completion state. Every step produces something testable. Read the full step before writing any code.
> Changes from v1.5: fourteen issues resolved — see "Changes from v1.5" section at the bottom.

---

> Changes from v2.0: execution gates added, finding inclusion policy aligned with M3 reality, and ISS-009 test update made explicit.

## Pre-flight Checklist

Before writing any M4 code, confirm the M3 baseline is intact:

```powershell
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
```

If any of these fail, fix M3 before starting M4.

---

## Execution Gates (Must Not Be Skipped)

Use these as hard pass/fail checkpoints throughout implementation:

### Gate 0 - M3 Baseline Locked

- `alembic current` shows `003 (head)` before any M4 schema work
- Existing M3 unit + integration suites are green
- Latest known-vuln E2E trace still reaches a terminal scan state and publishes `report.jobs`

### Gate 1 - ISS-009 Complete

- `POST /api/v1/scrape/trigger` returns `202 Accepted` immediately
- Caller behavior is polling-based (no blocking-on-completion assumption)
- `tests/integrations/test_scraper_pipeline.py::test_trigger_produces_programs_in_db` is updated to poll rather than assert `body["status"] == "completed"`

### Gate 2 - Reporter Plumbing Alive

- Migration `004_reporter` applied cleanly
- Reporter health endpoint green with DB/RabbitMQ/MinIO components healthy
- `report.jobs` messages are consumed without worker crash loops

### Gate 3 - First End-to-End Artifact

- At least one real PDF artifact is generated from a completed/partial scan
- `GET /api/v1/reports/{report_id}/download` returns a valid presigned URL
- Downloaded bytes validate as `%PDF`

Only move to the next gate when the previous gate is fully green.

---

## File Map

Files you will create or replace in M4 (in implementation order):

```
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
│                                                           + ISS-009 async scraper trigger fix
├── services/scraper/
│   └── main.py                                 ← UPDATE — ISS-009 fix: async background trigger
├── services/reporter/
│   ├── requirements.txt                        ← NEW — reporter-only dependencies
│   ├── Dockerfile                              ← REPLACE — repo-root build context + __init__ fix
│   ├── config.py                               ← NEW — replaces skeleton config
│   ├── models.py                               ← NEW — internal dataclasses
│   ├── repository.py                           ← NEW — ReportRepository
│   ├── clients/
│   │   ├── __init__.py                         ← NEW (empty)
│   │   ├── core_engine.py                      ← NEW — scan + findings + evidence fetch
│   │   ├── scraper.py                          ← NEW — program + scope fetch
│   │   └── attack_graph.py                     ← NEW — stubbed graceful fallback until M8
│   ├── parsing.py                              ← NEW — ParsedScan normalization
│   ├── reproduction.py                         ← NEW — deterministic repro packs
│   ├── evidence.py                             ← NEW — evidence fetch + embed logic
│   ├── renderers/
│   │   ├── __init__.py                         ← NEW (empty)
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
│       ├── findings_mixed_verification.json    ← NEW
│       ├── findings_zero.json                  ← NEW
│       ├── finding_evidence.json               ← NEW
│       ├── program_detail.json                 ← NEW
│       ├── program_scope.json                  ← NEW
│       ├── exploit_chains.json                 ← NEW
│       └── golden/
│           ├── no_findings_summary.txt         ← NEW
│           ├── repro_pack_xss.txt              ← NEW
│           ├── repro_pack_fallback.txt         ← NEW
│           ├── report_outline_pdf.txt          ← NEW
│           └── report_outline_docx.txt         ← NEW
├── unit/
│   └── test_reporter.py                        ← NEW — 80%+ coverage target
├── integration/
│   └── test_reporter_pipeline.py               ← NEW — queue → DB → MinIO → API
└── e2e/
    └── test_report_download_flow.py            ← NEW — known_vuln_target chain + regenerate chain
```

**Note:** `backend/services/core_engine/pipeline/aggregator.py` does not require a code change in M4. The organic producer remains valid because `report_ids` is optional in the updated shared schema. Rebuilding the Core Engine image is still required so it picks up the updated shared schema package.

**Note on `__init__.py` files:** Every `__init__.py` listed above is an empty file. Per `Default.md` rule, `__init__.py` files are empty unless there is an explicit documented reason to put something in them. Do not import from them. Create them with `[System.IO.File]::WriteAllText("path\to\__init__.py", "")` on Windows — never with `echo` or `>` (UTF-16 BOM issue, see Default.md Mistake #5).

---

## Step 4.0 — ISS-009 Fix: Async Scraper Trigger

**Files:** `backend/services/scraper/main.py`

This step must be completed before Step 4.25 (e2e tests). ISS-009 is listed as Open in `Issues.md` with resolution target M4. The canonical DoD e2e chain (scrape → scan → report → download) cannot be tested reliably until this is fixed.

**Root cause:** `POST /api/v1/scrape/trigger` currently blocks while running the full platform scrape synchronously inside the request handler. For large programs or slow API responses, this times out before returning, leaving the caller with a network error and no way to know if work started.

**Fix:** Change the trigger endpoint to fire the scrape as a background task and return `202 Accepted` immediately. The caller polls for results via existing APIs rather than waiting.

```python
# backend/services/scraper/main.py — updated trigger endpoint
from fastapi import BackgroundTasks

@app.post("/api/v1/scrape/trigger", status_code=202)
async def trigger_scrape(
    platform: str = "hackerone",
    background_tasks: BackgroundTasks = None,
) -> dict:
    """
    Immediately returns 202. Scrape runs as a background task.
    Use GET /api/v1/programs to poll for new results.
    """
    if platform not in CollectorRegistry.all_platforms():
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform!r}")

    background_tasks.add_task(_run_platform_scrape, platform)
    return {"status": "accepted", "platform": platform, "message": "Scrape started in background"}
```

**Response change:**

```json
{
  "status": "accepted",
  "platform": "hackerone",
  "message": "Scrape started in background"
}
```

**Callers must be updated:** Any test or script that previously awaited a `completed` status from this endpoint must switch to polling `GET /api/v1/programs` for new rows. The E2E test in Step 4.25 uses the `known_vuln_target` mode which bypasses the scraper trigger entirely — this fix only affects the manual trigger endpoint and the M2 integration tests.

**Also update** `tests/integrations/test_scraper_pipeline.py` `test_trigger_produces_programs_in_db` to poll rather than assert `body["status"] == "completed"`.

---

## Step 4.1 — Database Migration: `004_reporter`

**File:** `backend/migrations/versions/004_reporter.py`

This migration introduces only the reporter domain tables. It does not touch any existing tables.

```python
"""
Reporter schema: reports, reproduction_packs

Revision ID: 004
Revises: 003
Create Date: 2026-03-28

Tables created: reports, reproduction_packs
Tables modified: —
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
        sa.Column("scan_id", UUID(as_uuid=True),
                  sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", UUID(as_uuid=True),
                  sa.ForeignKey("programs.program_id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.VARCHAR(), nullable=False),      # pdf | docx
        sa.Column("status", sa.VARCHAR(), nullable=False),      # generating | completed | partial | failed
        sa.Column("storage_path", sa.VARCHAR(), nullable=True),
        sa.Column("file_size_bytes", sa.INTEGER(), nullable=True),
        sa.Column("error_detail", sa.TEXT(), nullable=True),
        sa.Column("generated_at", sa.TIMESTAMPTZ(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_reports_scan_id", "reports", ["scan_id"])
    op.create_index("ix_reports_program_id", "reports", ["program_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_format", "reports", ["format"])
    op.create_unique_constraint("uq_reports_scan_format", "reports", ["scan_id", "format"])

    op.create_table(
        "reproduction_packs",
        sa.Column("pack_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("finding_id", UUID(as_uuid=True),
                  sa.ForeignKey("findings.finding_id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_id", UUID(as_uuid=True),
                  sa.ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False),
        sa.Column("curl_command", sa.TEXT(), nullable=True),
        sa.Column("http_request_raw", sa.TEXT(), nullable=True),
        sa.Column("browser_steps", sa.TEXT(), nullable=True),
        sa.Column("notes", sa.TEXT(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_reproduction_packs_report_id", "reproduction_packs", ["report_id"])
    op.create_index("ix_reproduction_packs_finding_id", "reproduction_packs", ["finding_id"])
    op.create_unique_constraint("uq_reproduction_packs_report_finding", "reproduction_packs",
                                ["report_id", "finding_id"])


def downgrade() -> None:
    pass  # forward-only in development
```

**Apply and verify:**

```powershell
docker compose -f infra/docker-compose.yml --env-file .env `
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini upgrade head

docker compose -f infra/docker-compose.yml --env-file .env `
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini current
# Expected: "004 (head)"

docker compose -f infra/docker-compose.yml --env-file .env exec postgres `
  psql -U attackbot -d attackbot -c "\dt"
# Expected: reports, reproduction_packs visible alongside prior tables
```

---

## Step 4.2 — Queue Contracts and Schema Compatibility

**Files:**
- `backend/shared/schemas/report_jobs.py`
- `backend/shared/schemas/reports_completed.py`
- `backend/shared/queue.py`

Reporter consumes `report.jobs` and publishes `reports.completed`.

### Critical schema decisions

- Keep `exploit_chains` as a list of objects, not UUID strings
- Add `report_ids` as an optional field
- Support two valid producers:
  - Core Engine organic pipeline path: `report_ids` absent
  - Reporter regenerate API path: `report_ids` present

### `report.jobs` payload contract for M4

The queue wire format uses `"informational"` (not `"info"`) for the lowest severity in the `severity_breakdown`, because that is what the M3 aggregator emits. However, the Core Engine database stores `"info"`. `parsing.py` must normalize both — see Step 4.9.

```json
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
    "informational": 0
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
  "timestamp": "2026-03-28T11:30:00Z"
}
```

### `report_ids` rules

- Optional overall
- If present, keys must exactly match entries in `formats_requested`
- Values must be UUID strings
- If absent, worker allocates rows itself using `create_or_reset_report()`
- If present, worker must reuse those exact IDs and must not allocate replacements

### Worker branching rule

```python
if payload.report_ids is present:
    use provided report_id for each format
    call mark_generating(report_id)
else:
    allocate or reset row with create_or_reset_report(scan_id, program_id, format)
```

### `reports.completed` payload contract

```json
{
  "event_type": "report.generated",
  "report_id": "uuid",
  "scan_id": "uuid",
  "program_id": "uuid",
  "format": "pdf",
  "status": "completed",
  "storage_path": "reports/uuid/report.pdf",
  "file_size_bytes": 124882,
  "generated_at": "2026-03-28T11:31:22Z",
  "timestamp": "2026-03-28T11:31:22Z"
}
```

### Queue behavior rules

- `report.jobs` is consumed with `task_acks_late=True`
- Exhausted retries land in `report.jobs.dlq`
- One `reports.completed` event per terminal artifact
- `formats_requested` empty → default to `["pdf", "docx"]`
- Partial scans still generate reports
- `has_findings=false` still generates reports

### Critical: `reports.completed` queue declaration

Add an active declaration helper to `backend/shared/queue.py`:

```python
async def ensure_queue(self, queue_name: str, durable: bool = True) -> None:
    """
    Actively declare a queue — safe to call if queue already exists.
    Use this for queues the reporter publishes to (reports.completed)
    because passive declare alone is not safe on cold boot.
    """
    if self._channel is None:
        raise QueueConnectionError("Publisher not connected.")
    await self._channel.declare_queue(queue_name, durable=durable)
```

Reporter startup must call:

```python
await publisher.ensure_queue(Queues.REPORTS_COMPLETED)
```

---

## Step 4.3 — Reporter-Specific Dependencies and Dockerfile

**Files:**
- `backend/services/reporter/requirements.txt`
- `backend/services/reporter/Dockerfile`

Use reporter-only dependencies. Do not put PDF/DOCX or `pdfplumber` libraries in `requirements/base.txt`.

### `requirements.txt`

```
-r /app/requirements/base.txt
python-docx==1.1.2
reportlab==4.2.2
minio==7.2.7
Pillow==10.4.0
prometheus-client==0.20.0
pdfplumber==0.11.0
```

> **Why `pdfplumber`:** It is used exclusively in tests to extract normalized text from generated PDFs for golden-file comparison (see Step 4.13). Including it in the service image keeps the test environment consistent with the runtime image. It has no runtime cost when not called.

### `Dockerfile`

> ⚠️ **Critical:** This Dockerfile includes `backend/__init__.py` and `backend/services/__init__.py` COPY lines. Without these, `from backend.shared.x import y` raises `ModuleNotFoundError` at container startup. This was the root cause of the M2 container crash loop (Default.md Mistake #6). Do not remove these two lines.

```dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements/base.txt /app/requirements/base.txt
COPY backend/services/reporter/requirements.txt /app/backend/services/reporter/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/services/reporter/requirements.txt

# These two lines are mandatory — without them backend.* imports fail at runtime
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py

COPY backend/shared /app/backend/shared
COPY backend/services/reporter /app/backend/services/reporter

# Temp directory must exist in the image — enforced again at service startup
RUN mkdir -p /tmp/attackbot-reports

EXPOSE 8003
CMD ["uvicorn", "backend.services.reporter.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Worker image note

`reporter-worker` uses this same image. `docker-compose.yml` overrides the container command to run Celery instead of Uvicorn. There is no separate worker Dockerfile.

### Critical temp directory rule

Enforce temp directory existence in two places — never rely on only one:

1. **Dockerfile:** `RUN mkdir -p /tmp/attackbot-reports`
2. **Service startup:** `Path(settings.temp_output_dir).mkdir(parents=True, exist_ok=True)`

---

## Step 4.4 — Reporter Config: `config.py`

**File:** `backend/services/reporter/config.py`

> ⚠️ **Critical:** Pydantic Settings cannot parse a JSON array from a plain environment variable string. `list[int]` and `list[str]` field types will raise `ValidationError` if anyone sets the corresponding env var to `60,300,600`. Use comma-separated string fields with explicit property accessors for any config that is overrideable via environment variable.

```python
from backend.shared.config import BaseServiceConfig


class ReporterConfig(BaseServiceConfig):
    service_name: str = "reporter"
    port: int = 8003

    core_engine_api_url: str = "http://core-engine:8002"
    scraper_api_url: str = "http://scraper:8001"
    attack_graph_api_url: str = "http://attack-graph-engine:8006"

    upstream_timeout_seconds: int = 30
    upstream_connect_timeout_seconds: int = 5

    # Comma-separated string — use get_default_formats() to consume as list
    # Override via env: REPORTER_DEFAULT_FORMATS=pdf,docx
    default_formats_str: str = "pdf,docx"

    reports_bucket: str = "reports"
    evidence_bucket: str = "evidence"
    report_presign_expiry_seconds: int = 900

    report_watchdog_interval_seconds: int = 300
    report_watchdog_stale_minutes: int = 30

    # Upstream health cache TTL — avoids making live HTTP calls on every /health hit
    upstream_health_cache_ttl_seconds: int = 30

    max_inline_evidence_images_per_finding: int = 2
    evidence_download_concurrency: int = 10   # asyncio.Semaphore cap for MinIO downloads
    include_raw_http_appendix: bool = True
    temp_output_dir: str = "/tmp/attackbot-reports"

    report_task_max_retries: int = 3

    # Comma-separated string — use get_retry_backoff() to consume as list[int]
    # Override via env: REPORTER_REPORT_TASK_RETRY_BACKOFF_SECONDS=60,300,600
    report_task_retry_backoff_seconds_str: str = "60,300,600"

    def get_default_formats(self) -> list[str]:
        return [f.strip() for f in self.default_formats_str.split(",") if f.strip()]

    def get_retry_backoff(self) -> list[int]:
        return [int(x.strip()) for x in self.report_task_retry_backoff_seconds_str.split(",")]
```

---

## Step 4.5 — Core Engine Evidence API Addition

**File:** `backend/services/core_engine/main.py`

Reporter cannot query `finding_evidence` directly — it must go through the Core Engine API. Add this read-only nested endpoint:

```
GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence
```

**Why this path:** Consistent with the existing Core Engine scan-scoped API pattern (`/scans/{scan_id}/findings`).

**Response:**

```json
{
  "finding_id": "uuid",
  "scan_id": "uuid",
  "items": [
    {
      "evidence_id": "uuid",
      "artifact_type": "screenshot",
      "storage_path": "evidence/finding_uuid/screenshot.png",
      "description": "Browser screenshot",
      "captured_at": "2026-03-28T09:10:11Z"
    }
  ]
}
```

**Rules:**

- Return empty `items` list if no evidence exists — never 404 for this case
- Return 404 only if the finding does not exist for the given scan (wrong `scan_id`)
- Reporter calls this endpoint only when `include_evidence_screenshots=true`

---

## Step 4.6 — Internal Models: `models.py`

**File:** `backend/services/reporter/models.py`

Pure Python dataclasses — no SQLAlchemy, no Pydantic. These represent the canonical in-memory objects flowing through the reporter pipeline.

```python
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
    is_verified: bool
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
```

---

## Step 4.7 — Repository: `repository.py`

**File:** `backend/services/reporter/repository.py`

### Critical UPSERT for `create_or_reset_report()`

Because `uq_reports_scan_format` exists, this method must use `INSERT ... ON CONFLICT` directly. Never SELECT-then-INSERT.

```python
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
```

### Explicit `mark_generating()` behavior

Required for the regenerate path where stable `report_ids` were allocated before enqueue. Do not replace with `create_or_reset_report()` inside the worker when `report_ids` are already known.

```python
async def mark_generating(self, report_id: str) -> None:
    await self.session.execute(text("""
        UPDATE reports
        SET status = 'generating',
            error_detail = NULL
        WHERE report_id = :report_id
    """), {"report_id": report_id})
    await self.session.commit()
```

> ⚠️ **Critical design rule — `mark_partial()` must set `generated_at`:**
>
> Partial reports are terminal and downloadable. The download endpoint allows access for both `completed` and `partial` statuses, and blocks on `generating` and `failed`. This means `mark_partial()` must set `generated_at = NOW()` — the same as `mark_completed()`. If `generated_at` is left NULL on a partial report, client polling logic that waits for a non-null `generated_at` will wait forever. This is not optional.
>
> ```python
> async def mark_partial(self, report_id: str, storage_path: str,
>                        file_size_bytes: int, reason: str) -> None:
>     await self.session.execute(text("""
>         UPDATE reports
>         SET status = 'partial',
>             storage_path = :storage_path,
>             file_size_bytes = :file_size_bytes,
>             error_detail = :reason,
>             generated_at = NOW()   -- mandatory: partial reports are downloadable
>         WHERE report_id = :report_id
>     """), {...})
> ```

### Required methods

- `create_or_reset_report(scan_id, program_id, format) → str`
- `mark_generating(report_id) → None`
- `mark_completed(report_id, storage_path, file_size_bytes) → None`
- `mark_partial(report_id, storage_path, file_size_bytes, reason) → None` — sets `generated_at`
- `mark_failed(report_id, error_detail) → None` — does NOT set `generated_at`
- `replace_reproduction_packs(report_id, packs: list[ReproductionPackDraft]) → None`
- `list_reports(page, page_size, scan_id_filter, status_filter) → dict`
- `get_report(report_id) → dict | None`
- `get_reports_by_scan(scan_id) → list[dict]`
- `get_stale_generating_reports(stale_minutes) → list[dict]`

### Ownership rule

- API or producer side may call `create_or_reset_report()`
- Worker may call `create_or_reset_report()` only when processing organic messages without `report_ids`
- Worker uses `mark_generating(report_id)` when `report_ids` are present in the payload

---

## Step 4.8 — Upstream API Clients: `clients/`

**Files:**
- `clients/__init__.py` — **empty file** (required for Python package resolution)
- `clients/core_engine.py`
- `clients/scraper.py`
- `clients/attack_graph.py`

> ⚠️ `clients/__init__.py` must exist as an empty file. Without it, `from backend.services.reporter.clients.core_engine import CoreEngineClient` raises `ModuleNotFoundError`. Create it with `[System.IO.File]::WriteAllText(...)` — not with `echo` or `>`.

### Core Engine client

Fetch:

```
GET /api/v1/scans/{scan_id}
GET /api/v1/scans/{scan_id}/findings
GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence
```

M4 policy: fetch all findings and preserve each finding's `is_verified` flag for rendering. Do not filter to verified-only at the client layer.

### Scraper client

Fetch:

```
GET /api/v1/programs/{program_id}
GET /api/v1/programs/{program_id}/scope
```

### Attack Graph client — M4 graceful fallback

The planned endpoint `GET /api/v1/chains/{chain_id}` does not exist until M8. In M4, the Attack Graph client must:

- Attempt the fetch (for forward compatibility)
- On connection error or 404, return `None` silently rather than raising
- Log at `debug` level — not `warning`, because unavailability is expected in M4

```python
async def get_chain_detail(self, chain_id: str) -> dict | None:
    try:
        resp = await self._client.get(f"/api/v1/chains/{chain_id}", timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None  # Expected in M4 — service not yet implemented
```

If fetch returns `None`, the renderer omits the detailed chain section and instead adds an appendix note:

> *Exploit chain detail is not yet available. Chain summary data is taken from the scan message.*

### Attack Graph: `degraded` vs `unhealthy` in health checks

In M4, the Attack Graph engine is expected to be running (it is in the compose stack) but its chain detail API is unimplemented. Define the distinction clearly:

| Health status | When to use |
|---|---|
| `healthy` | Service reachable, API responding |
| `degraded` | Service reachable but chain detail API returns 404 — expected in M4 |
| `unhealthy` | Service not reachable at all |

In M4, show `degraded` with `detail: "chain_detail_api_not_yet_available"` — never `unhealthy` just because the chain API returns 404. `unhealthy` should only fire if the health endpoint itself is unreachable.

---

## Step 4.9 — ParsedScan Normalization: `parsing.py`

**File:** `backend/services/reporter/parsing.py`

### Severity key normalization — critical

There is a key mismatch between the two data sources this builder reads from:

| Source | Key used for informational severity |
|---|---|
| `report.jobs` queue message (from M3 aggregator) | `"informational"` |
| `GET /api/v1/scans/{scan_id}` Core Engine API (from DB) | `"info"` |

Both sources must be normalized to a single canonical key before building `ParsedScan.severity_breakdown`. Use `"info"` as the internal canonical value — it matches the `Severity` type literal in `models.py`.

```python
_SEVERITY_ALIASES: dict[str, str] = {
    "informational": "info",
}

def _normalize_severity_key(key: str) -> str:
    """Normalize severity keys from all upstream sources to the canonical set."""
    return _SEVERITY_ALIASES.get(key.lower(), key.lower())

def _normalize_severity_breakdown(raw: dict) -> dict[str, int]:
    """
    Accept severity breakdowns with either 'info' or 'informational' keys.
    Always returns a dict with keys: critical, high, medium, low, info.
    """
    canonical = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for key, count in raw.items():
        normalized_key = _normalize_severity_key(key)
        if normalized_key in canonical:
            canonical[normalized_key] += count
    return canonical
```

Call `_normalize_severity_breakdown()` on every `severity_breakdown` dict from any source — queue payload, Core Engine API response, or DB row.

### Builder contract

```python
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
```

### Rules

- Include all findings returned by Core Engine in M4
- Preserve each finding's `is_verified` flag for renderer display (table column + badges/labels)
- Normalize all severity strings to lowercase canonical values using `_normalize_severity_key()`
- Normalize all `severity_breakdown` dicts using `_normalize_severity_breakdown()`
- Sort findings by severity rank descending, then title ascending, then URL ascending
- Severity rank: critical=4, high=3, medium=2, low=1, info=0
- Keep `exploit_chain_refs` object shape from the queue contract
- If no findings are returned, enter clean report mode — `is_clean()` returns `True`
- If no findings but `exploit_chains` is non-empty, log a warning and ignore the chains (data inconsistency, not a fatal error)

---

## Step 4.10 — Reproduction Packs: `reproduction.py`

**File:** `backend/services/reporter/reproduction.py`

### Deterministic formatting rules

- Sort headers alphabetically
- Sort query parameters alphabetically
- Sort JSON body keys alphabetically
- Use stable, literal browser step wording
- Redact known secret patterns (passwords, tokens) before writing
- Never include temp paths or MinIO URLs in any output field

### Per-finding failure handling

Do not let one pack failure break the whole loop. Every finding must produce a pack — either a real one or a specified fallback:

```python
packs: list[ReproductionPackDraft] = []
pack_errors: list[str] = []

for finding in findings:
    try:
        packs.append(build_pack(finding))
    except Exception as exc:
        pack_errors.append(f"{finding.finding_id}:pack_generation_failed:{exc}")
        packs.append(build_fallback_pack(finding, str(exc)))
```

### Fallback pack specification

`build_fallback_pack(finding, reason)` must produce a `ReproductionPackDraft` with `is_fallback=True` and the following exact field contents so golden-file tests can assert against it:

```
curl_command:
  # Reproduction steps could not be auto-generated.
  # Affected URL: {finding.affected_url}
  # Parameter: {finding.affected_parameter or "N/A"}
  # See manual steps below.

http_request_raw:
  [Not available — pack generation failed]
  Reason: {reason}

browser_steps:
  1. Navigate to: {finding.affected_url}
  2. Locate parameter: {finding.affected_parameter or "N/A"}
  3. Manually reproduce based on finding description.

notes:
  This reproduction pack was auto-generated as a fallback.
  The original pack builder encountered: {reason}
```

The `notes` field must always include the exact string `"auto-generated as a fallback"` so tests can assert its presence without brittle string matching.

### Status rule

If any fallback pack is used:

- Mark report `partial` via `mark_partial(reason="repro_pack_fallback")`
- Record the list of failing finding IDs in `error_detail`

---

## Step 4.11 — Evidence Fetch and Temp File Cleanup: `evidence.py`

**File:** `backend/services/reporter/evidence.py`

### Data source

Evidence metadata comes only from:

```
GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence
```

Never query `finding_evidence` directly.

### Respect `include_evidence_screenshots`

If `False`:

- Do not call the evidence API
- Do not download evidence
- Do not render screenshot sections
- Return an empty list for all findings

### Concurrency cap on MinIO downloads

When `include_evidence_screenshots=True`, the reporter may download many MinIO objects — one per artifact per finding. For large scans this can saturate the MinIO connection pool. Use a semaphore:

```python
async def fetch_all_evidence(
    findings: list[ParsedFinding],
    scan_id: str,
    settings: ReporterConfig,
) -> None:
    """Mutates each finding's .evidence list in place."""
    semaphore = asyncio.Semaphore(settings.evidence_download_concurrency)

    async def fetch_one(finding: ParsedFinding) -> None:
        async with semaphore:
            items = await _fetch_evidence_metadata(finding.finding_id, scan_id)
            for item in items[:settings.max_inline_evidence_images_per_finding]:
                artifact = await _download_artifact(item, settings)
                finding.evidence.append(artifact)

    await asyncio.gather(*[fetch_one(f) for f in findings], return_exceptions=True)
```

The default cap is 10 concurrent downloads (`evidence_download_concurrency` in config).

### Temp file cleanup

Downloaded evidence files must always be removed after the embed attempt, whether it succeeds or fails:

```python
tmp_path = await storage.download_temp_object(...)
try:
    embed_image(tmp_path)
finally:
    if tmp_path and os.path.exists(tmp_path):
        os.unlink(tmp_path)
```

### Missing artifact rules

| Condition | Result |
|---|---|
| Metadata exists, MinIO object exists | Embed normally |
| Metadata exists, MinIO object missing | Insert note in report, mark `partial` |
| Evidence API returns empty list | Continue silently |
| Evidence API unavailable and screenshots enabled | Continue, mark `partial` |
| `include_evidence_screenshots=false` | Skip all of the above |

---

## Step 4.12 — Rendering Architecture and Temp File Cleanup

**Files:**
- `renderers/__init__.py` — **empty file** (required for Python package resolution)
- `renderers/base.py`
- `renderers/theme.py`
- `renderers/sections.py`
- `renderers/pdf.py`
- `renderers/docx.py`

> ⚠️ `renderers/__init__.py` must exist as an empty file. Without it, `from backend.services.reporter.renderers.pdf import PdfRenderer` fails. Create with `[System.IO.File]::WriteAllText(...)`.

### Format rendering strategy — sequential in M4

PDF and DOCX rendering are I/O-heavy (MinIO downloads, upstream API calls) and are independent of each other. They could run in parallel via `asyncio.gather`. **In M4, render them sequentially** for two reasons:

1. The `ParsedScan` object (including downloaded evidence temp files) is shared across both renders; parallel access requires careful coordination
2. M4 has no observed latency problem that warrants the complexity

Document the deliberate choice with a comment in `report_task.py`:

```python
# Formats rendered sequentially — both renderers share the ParsedScan object
# including mutable evidence.local_tmp_path fields. Parallel rendering would
# require either deep-copying ParsedScan or coordinating temp file lifecycle.
# Revisit in M6+ if report generation latency becomes a problem.
for format_name in formats:
    ...
```

### Shared section order

**For finding reports:**

1. Cover
2. Executive Summary
3. Scope Overview
4. Findings Table (sorted by severity descending, includes Verification Status column)
5. Per-Finding Detail (one section per finding)
6. Exploit Chains section, or Chain Availability Note if M8 is not yet running
7. Appendix — Reproduction Packs
8. Appendix — Evidence Notes
9. Appendix — Raw HTTP Requests (only if `settings.include_raw_http_appendix=True`)

**For clean (zero-findings) reports:**

1. Cover
2. Executive Summary
3. Scope Overview
4. No Findings Statement
5. Coverage Notes
6. Appendix — Scan Metadata

### Executive Summary verification caveat

For M4, findings may include unverified items because M7 verification is not yet live. Include this caveat in the Executive Summary when any finding has `is_verified=False`:

> Verification note: This report may include unverified findings from the current scan pipeline. Evidence-backed verification gating is scheduled for M7.

### `include_raw_http_appendix` wiring

Renderers must check `settings.include_raw_http_appendix` before adding the raw HTTP request/response appendix section. Both the PDF and DOCX renderer must receive `settings` (or the boolean flag) and must not render the Raw HTTP appendix when the flag is `False`. This flag is not just config — it must actively gate a section.

```python
# In PdfRenderer.build() and DocxRenderer.build():
if settings.include_raw_http_appendix and not parsed_scan.is_clean():
    self._add_raw_http_appendix(packs)
```

### `include_evidence_screenshots` wiring

Renderers must check `parsed_scan.include_evidence_screenshots` before any image section creation. Do not check config — by the time the renderer runs, `ParsedScan.include_evidence_screenshots` is the authoritative value.

### Render artifact cleanup

Local rendered files must be deleted after upload attempt, whether it succeeds or fails:

```python
output_path = _build_output_path(settings.temp_output_dir, report_id, format_name)
try:
    await generator.generate(parsed_scan, packs, output_path=output_path, settings=settings)
    storage_path, file_size = await storage.upload_report(report_id, format_name, output_path)
    return storage_path, file_size
finally:
    if os.path.exists(output_path):
        os.unlink(output_path)
```

---

## Step 4.13 — PDF Generator: `renderers/pdf.py`

Use `reportlab.platypus`.

### Validation after render

After calling `doc.build()`, verify before uploading:

1. File exists at `output_path`
2. `os.path.getsize(output_path) > 0`
3. First 4 bytes of file are `b"%PDF"` — if not, treat as a failed render

### Screenshot failure rule

If a `Pillow` image load fails for an evidence artifact:

- Insert a text note: `[Evidence screenshot unavailable — {artifact.artifact_type}]`
- Continue rendering remaining sections
- Return `partial` reason `"evidence_image_load_failed"` to the caller

### Severity colour theme (from `renderers/theme.py`)

```python
SEVERITY_COLOURS = {
    "critical": (0.8, 0.1, 0.1),   # Red
    "high":     (0.9, 0.45, 0.0),  # Orange
    "medium":   (0.9, 0.75, 0.0),  # Yellow
    "low":      (0.2, 0.5, 0.8),   # Blue
    "info":     (0.5, 0.5, 0.5),   # Grey
}
```

### Golden file comparison using `pdfplumber`

The test utility in `test_reporter.py` extracts normalized text from a generated PDF for comparison against `golden/report_outline_pdf.txt`:

```python
import pdfplumber

def extract_pdf_outline(pdf_path: str) -> str:
    """
    Extract section headers and first-line content from a PDF.
    Returns normalized whitespace-stripped text for golden-file comparison.
    """
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    return "\n".join(lines)
```

Compare only this extracted outline against the golden file — never compare raw PDF bytes.

---

## Step 4.14 — DOCX Generator: `renderers/docx.py`

Use `python-docx`.

### Validation after render

After saving the document:

1. File exists at `output_path`
2. `os.path.getsize(output_path) > 0`
3. File opens as a valid zip archive (`zipfile.is_zipfile(output_path)`)
4. `word/document.xml` exists inside the archive

### DOCX golden-file normalization

Use a test utility that extracts normalized text from the DOCX for comparison against `golden/report_outline_docx.txt`. Do not compare binary `.docx` files — they contain timestamps and are never byte-identical across runs.

```python
from docx import Document

def extract_docx_outline(docx_path: str) -> str:
    """
    Extract paragraphs and table cell content from a DOCX in document order.
    Returns normalized whitespace-stripped text for golden-file comparison.
    """
    doc = Document(docx_path)
    lines = []
    for block in doc.element.body:
        from docx.oxml.ns import qn
        if block.tag == qn("w:p"):
            text = "".join(r.text for r in block.iter(qn("w:t"))).strip()
            if text:
                lines.append(text)
        elif block.tag == qn("w:tbl"):
            for row in block.iter(qn("w:tr")):
                cells = [
                    "".join(r.text for r in cell.iter(qn("w:t"))).strip()
                    for cell in row.iter(qn("w:tc"))
                ]
                lines.append("|".join(cells))
    return "\n".join(lines)
```

---

## Step 4.15 — Storage and Presigned Download Flow: `storage.py`

**File:** `backend/services/reporter/storage.py`

### Required methods

```python
async def upload_report(report_id: str, format: str, local_path: str) -> tuple[str, int]:
    """Upload rendered file to MinIO. Returns (storage_path, file_size_bytes)."""

async def object_exists(bucket: str, key: str) -> bool:
    """Return True if object exists in MinIO. Does not raise on missing."""

async def download_temp_object(bucket: str, key: str, tmp_dir: str) -> str:
    """Download object to a temp file in tmp_dir. Returns local path."""

async def get_presigned_download_url(storage_path: str, expiry_seconds: int) -> str:
    """Return a time-limited presigned GET URL. Never log this URL."""
```

### Storage path rules

```
reports/{report_id}/report.pdf
reports/{report_id}/report.docx
```

### Security rules

- No public buckets
- No anonymous download
- Presigned GET only, with configurable expiry (`report_presign_expiry_seconds` in config)
- Do not log full presigned URLs — they are effectively credentials

---

## Step 4.16 — Completion Publisher: `publisher.py`

**File:** `backend/services/reporter/publisher.py`

### Required behavior

- `ensure_queue(Queues.REPORTS_COMPLETED)` is called at startup before any publish
- Publish one `report.generated` event per terminal artifact (one per format per scan)
- If publish fails, keep the report row at its terminal status (`completed` or `partial`) — never downgrade
- Never delete an artifact because publishing the completion event failed

```python
async def publish_report_completed(self, report: dict) -> bool:
    """
    Publish report.generated to reports.completed.
    Returns True on success. On failure: logs error and returns False.
    The caller must NOT change the report's terminal status on False.
    """
    message = build_reports_completed_message(...)
    success = await self._publisher.publish(Queues.REPORTS_COMPLETED, message)
    if not success:
        log.error("publish_reports_completed_failed",
                  report_id=report["report_id"],
                  note="artifact is still available — publish failure is non-fatal")
    return success
```

---

## Step 4.17 — Metrics and Logging: `metrics.py`

**File:** `backend/services/reporter/metrics.py`

Prefix all custom metrics with `attackbot_reporter_` to avoid collisions with FastAPI Instrumentator auto-generated metrics.

### Required metrics

| Metric | Type | Labels | Purpose |
|---|---|---|---|
| `attackbot_reporter_generation_total` | Counter | `format`, `status` | Track generation outcomes by format and final status |
| `attackbot_reporter_generation_duration_seconds` | Histogram | `format` | Wall-clock time from task receipt to upload complete |
| `attackbot_reporter_generation_failures_total` | Counter | `format`, `reason` | Failed generation reasons |
| `attackbot_reporter_download_requests_total` | Counter | `status` | Count download endpoint hits by outcome |
| `attackbot_reporter_presign_duration_seconds` | Histogram | — | Time to generate presigned URL from MinIO |
| `attackbot_reporter_evidence_missing_total` | Counter | — | Evidence objects referenced but not found in MinIO |
| `attackbot_reporter_zero_findings_total` | Counter | — | Scans that produced a clean (no findings) report |
| `attackbot_reporter_partial_generation_total` | Counter | `reason` | Reports completed as partial and why |

---

## Step 4.18 — Task Entry, Retry Backoff, and Failure Taxonomy: `report_task.py`

**File:** `backend/services/reporter/report_task.py`

### High-level flow

```
receive report.jobs
→ validate envelope + payload
→ determine formats (default to ["pdf", "docx"] if empty)
→ for each format (sequential — see rendering strategy note in Step 4.12):
    if payload.report_ids contains format:
        use existing report_id
        mark report row generating
    else:
        allocate/reset row with create_or_reset_report()
    fetch scan + findings from Core Engine
    fetch program + scope from Scraper
    optionally fetch evidence metadata (if include_evidence_screenshots=true)
    optionally attempt attack graph chain detail (graceful fallback expected)
    build ParsedScan via ParsedScanBuilder
    build reproduction packs with per-finding fallback
    render artifact to temp file
    upload artifact to MinIO
    delete temp file
    update report row (completed / partial / failed)
    publish reports.completed (non-fatal if publish fails)
```

### Critical dual-producer rule

The worker must support both:

- Organic Core Engine messages with no `report_ids`
- Regenerate API messages with stable `report_ids`

```python
for format_name in formats:
    if payload.report_ids and format_name in payload.report_ids:
        report_id = payload.report_ids[format_name]
        await repository.mark_generating(report_id)
    else:
        report_id = await repository.create_or_reset_report(
            scan_id=str(payload.scan_id),
            program_id=str(payload.program_id),
            format=format_name,
        )

    result = await _generate_single_format(
        report_id=report_id,
        format_name=format_name,
        payload=payload,
    )
```

### Critical retry backoff wiring

The configured backoff list must be consumed using `get_retry_backoff()` and passed explicitly to `self.retry()`. This is what actually controls the countdown — without this wiring, the config values do nothing.

```python
def _retry_countdown(attempt_number: int, backoff: list[int]) -> int:
    """Return the backoff in seconds for this attempt. Clamps to last entry."""
    return backoff[min(attempt_number, len(backoff) - 1)]

# In the task:
except RetryableReportError as exc:
    countdown = _retry_countdown(
        self.request.retries,
        settings.get_retry_backoff(),
    )
    raise self.retry(exc=exc, countdown=countdown)
```

### Terminal status mapping

| Failure condition | Report row status |
|---|---|
| Core Engine fetch fails (scan/findings) | `failed` |
| Scraper fetch fails (program/scope) | `failed` |
| Evidence fetch fails, screenshots enabled | `partial` |
| Attack Graph detail unavailable | `partial` |
| Any repro pack fallback used | `partial` |
| Render fails (invalid PDF/DOCX output) | `failed` |
| Upload to MinIO fails | `failed` |
| `reports.completed` publish fails after upload | Keep `completed` or `partial` — never downgrade |

---

## Step 4.19 — Worker: `worker.py`

**File:** `backend/services/reporter/worker.py` — replaces skeleton entirely.

### Celery config

```python
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,               # ack only after task completes — prevents loss on crash
    worker_prefetch_multiplier=1,      # one task at a time — report generation is heavy
    task_reject_on_worker_lost=True,   # NACK on worker death — message goes to DLQ
    task_default_queue="report.jobs",
)
```

### DLQ behavior

If retries exhaust:

- Message lands in `report.jobs.dlq`
- Report row should already be `failed` from the last attempt
- Watchdog is a secondary cleanup only — do not rely on it as the primary failure handler

### Compose startup order note

Keep the existing compose pattern where `reporter-worker` depends on `reporter: condition: service_healthy`. Do not remove that dependency in M4. Reporter startup is responsible for queue declaration (`reports.completed`) before the worker begins steady-state processing.

---

## Step 4.20 — Reporter API: `main.py`

**File:** `backend/services/reporter/main.py` — replaces skeleton entirely.

### Required endpoints

```
GET  /api/v1/reports
GET  /api/v1/reports/{report_id}
GET  /api/v1/reports/{report_id}/download
GET  /api/v1/scans/{scan_id}/reports
POST /api/v1/reports/generate
GET  /api/v1/health
```

### `POST /api/v1/reports/generate`

This endpoint is mandatory. Flow.md specifies that reports can be regenerated without rerunning a scan.

**Scan state gate — behavior for all scan states:**

| Scan status | HTTP response | Reason |
|---|---|---|
| `completed` | 202 Accepted — proceed | Scan has final results |
| `partial` | 202 Accepted — proceed | Scan has partial results — still reportable |
| `running` | 409 Conflict | Results not final yet |
| `pending` | 409 Conflict | Scan has not started |
| `failed_internal` | 409 Conflict | No useful scan data to report |
| `failed_scope` | 409 Conflict | No scope was resolved — nothing to report |
| `failed_auth` | 409 Conflict | No authenticated results to report |
| Not found | 404 Not Found | Scan does not exist |

**Request:**

```json
{
  "scan_id": "uuid",
  "formats_requested": ["pdf", "docx"],
  "include_evidence_screenshots": true
}
```

**Behavior:**

1. Fetch scan from Core Engine — return 404 if missing
2. Check scan status against the table above — return 409 if blocked
3. For each requested format, call `create_or_reset_report()` and collect the returned `report_id`
4. Build `report.jobs` payload including `report_ids`
5. Enqueue to `report.jobs`
6. Return `202 Accepted`

**Response:**

```json
{
  "scan_id": "uuid",
  "enqueued": true,
  "report_ids": {
    "pdf": "uuid",
    "docx": "uuid"
  }
}
```

### `GET /api/v1/reports/{report_id}/download`

| Report status | HTTP response |
|---|---|
| `completed` | 200 with presigned URL |
| `partial` | 200 with presigned URL |
| `generating` | 409 Conflict |
| `failed` | 409 Conflict |
| Not found | 404 Not Found |

Do not use 422 for resource state errors.

### `GET /api/v1/health`

Check the following components:

- Postgres (`check_db_health()`)
- RabbitMQ (channel open check)
- MinIO (lightweight `stat_object` on the reports bucket)
- Core Engine reachability
- Scraper reachability
- Scheduler running (`scheduler.running` boolean)
- Attack Graph Engine reachability

**Upstream reachability caching:** Making live HTTP calls to Core Engine and Scraper on every `/health` hit adds 50–200ms of latency and creates cascading failure modes (reporter health depends on two other services being responsive). Cache the last-known reachability state with a TTL:

```python
_upstream_cache: dict[str, tuple[bool, float]] = {}  # service → (is_healthy, timestamp)

async def _check_upstream_cached(url: str, service_name: str, ttl: int) -> bool:
    cached = _upstream_cache.get(service_name)
    if cached and (time.monotonic() - cached[1]) < ttl:
        return cached[0]
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{url}/api/v1/health")
            healthy = resp.status_code == 200
    except Exception:
        healthy = False
    _upstream_cache[service_name] = (healthy, time.monotonic())
    return healthy
```

Call with `settings.upstream_health_cache_ttl_seconds` (default 30). This means health checks respond in < 5ms most of the time.

**Attack Graph component rule (M4):**

```json
"attack_graph_engine": {
  "status": "degraded",
  "detail": "chain_detail_api_not_yet_available"
}
```

In M4, always report `degraded` — never `unhealthy` — for the Attack Graph component, because its absence is expected and documented. Only upgrade to `unhealthy` in M8 when the chain detail API is expected to exist.

---

## Step 4.21 — Watchdog: `watchdog.py`

**File:** `backend/services/reporter/watchdog.py`

### Query

```sql
SELECT report_id, scan_id, format
FROM reports
WHERE status = 'generating'
  AND created_at < NOW() - INTERVAL ':minutes minutes'
ORDER BY created_at ASC
```

### Action

For each stale row:

1. Set `status = 'failed'`
2. Set `error_detail = 'watchdog_timeout'`
3. Increment `attackbot_reporter_generation_failures_total{reason="watchdog_timeout"}`
4. Log structured event at `warning` level

**Recovery path for operators:** `POST /api/v1/reports/generate` with the same `scan_id` will reset and re-enqueue.

---

## Step 4.22 — No Findings Report Path

A zero-findings report must:

- Generate PDF and DOCX normally
- Not include an empty findings table
- Not include exploit chain sections
- Include program metadata and scope overview
- Upload to MinIO at the standard path
- Be downloadable via presigned URL only

**Suggested wording in the No Findings Statement section:**

> No findings were produced for this scan. This report reflects the completed scan state and the scope reviewed at generation time. It should not be interpreted as proof of absence of vulnerabilities beyond the tested coverage captured below.

Because M4 includes all findings (not only verified), this clean-report path should be less common than in verified-only designs.

The `ParsedScan.is_clean()` method is the single gate for this path — renderers check it once and render the appropriate section set. Do not scatter `if findings:` checks throughout the render code.

---

## Step 4.23 — Tests: `tests/unit/test_reporter.py`

### Must-have unit tests

```
test_parsed_scan_includes_unverified_findings_with_flag
test_zero_findings_returns_clean_mode
test_findings_table_includes_verification_status_column
test_executive_summary_includes_unverified_caveat_when_needed
test_include_evidence_flag_false_skips_evidence_fetch
test_reproduction_pack_generation_uses_fallback_per_finding
test_fallback_pack_contains_required_marker_string
test_fallback_pack_is_flagged_as_fallback
test_create_or_reset_report_upserts_on_scan_id_format
test_mark_generating_updates_status_only
test_mark_partial_sets_generated_at                   ← validates the critical generated_at rule
test_mark_failed_does_not_set_generated_at            ← contrast with mark_partial
test_attack_graph_client_returns_none_on_unavailable
test_attack_graph_client_does_not_raise_on_404
test_attack_graph_health_is_degraded_not_unhealthy_in_m4
test_clean_mode_ignores_exploit_chains
test_severity_breakdown_normalizes_informational_to_info
test_severity_breakdown_normalizes_info_unchanged
test_severity_breakdown_normalizes_mixed_keys
test_include_raw_http_appendix_false_omits_section
test_include_raw_http_appendix_true_includes_section
test_evidence_download_respects_concurrency_cap
test_docx_outline_extraction_is_text_based
test_pdf_outline_extraction_uses_pdfplumber
test_reports_completed_queue_is_declared_before_publish
test_rendered_temp_file_deleted_after_upload
test_rendered_temp_file_deleted_after_failed_upload
test_evidence_temp_file_deleted_after_embed
test_evidence_temp_file_deleted_after_failed_embed
test_retry_backoff_uses_configured_countdown
test_retry_backoff_clamps_to_last_entry
test_generate_endpoint_returns_stable_report_ids_in_payload
test_generate_endpoint_rejects_running_scan_with_409
test_generate_endpoint_rejects_failed_internal_scan_with_409
test_generate_endpoint_rejects_pending_scan_with_409
test_worker_accepts_organic_message_without_report_ids
test_worker_reuses_provided_report_ids_when_present
test_download_endpoint_returns_200_for_partial_report
test_download_endpoint_returns_409_for_generating_report
test_upstream_health_check_returns_cached_result_within_ttl
test_upstream_health_check_refreshes_after_ttl_expires
```

### Temp file cleanup test strategy

Keep these as unit tests by mocking filesystem side effects — do not depend on real disk I/O:

```python
# Use pytest-mock to assert cleanup happens:
def test_rendered_temp_file_deleted_after_upload(mocker):
    mock_unlink = mocker.patch("os.unlink")
    mocker.patch("os.path.exists", return_value=True)
    # ... call the report generation function ...
    mock_unlink.assert_called_once_with("/tmp/attackbot-reports/test.pdf")
```

### Golden file approach

Only compare normalized text output — never binary files:

| Output type | Extraction method | Golden file |
|---|---|---|
| PDF section outline | `pdfplumber` text extraction (Step 4.13) | `golden/report_outline_pdf.txt` |
| DOCX content outline | `python-docx` paragraph/table extraction (Step 4.14) | `golden/report_outline_docx.txt` |
| Reproduction pack | String directly from `build_pack()` | `golden/repro_pack_xss.txt` |
| Fallback pack | String from `build_fallback_pack()` | `golden/repro_pack_fallback.txt` |
| No findings text | String from section builder | `golden/no_findings_summary.txt` |

---

## Step 4.24 — Integration Tests: `tests/integration/test_reporter_pipeline.py`

### Required scenarios

**Scenario A — normal findings report**
- `report.jobs` consumed
- PDF + DOCX rows created and reach `completed`
- Repro packs persisted in DB
- Both artifacts uploaded to MinIO
- Two `reports.completed` events published

**Scenario B — zero-findings report**
- Findings endpoint returns `[]`
- Artifact generated and uploaded
- PDF content (extracted with `pdfplumber`) contains the no-findings statement string
- Report row reaches `completed`

**Scenario C — missing screenshot MinIO object**
- Core Engine evidence API returns screenshot metadata
- MinIO object does not exist at the referenced path
- Generation finishes `partial`
- Artifact is still uploaded and downloadable
- `error_detail` contains `evidence_image_load_failed`

**Scenario D — evidence disabled by flag**
- `include_evidence_screenshots=false` in queue message
- Reporter does not call the evidence API (assert via mock or log inspection)
- Report completes without screenshot sections

**Scenario E — Attack Graph unavailable**
- Chain refs present in queue payload
- Fallback path activates
- Report finishes `partial`
- Appendix note present in extracted text

**Scenario F — upload failure**
- MinIO upload stubbed to raise
- Report row marked `failed`
- No `reports.completed` event emitted
- Temp file cleaned up

**Scenario G — retries exhausted to DLQ**
- Force deterministic render failure
- Celery exhausts `report_task_max_retries` attempts
- Row ends `failed`
- Message visible in `report.jobs.dlq`

**Scenario H — generate API returns pollable IDs**
- Call `POST /api/v1/reports/generate`
- Assert `report_ids` returned in response
- Worker updates those same row IDs — not replacement rows
- Same IDs visible via `GET /api/v1/reports/{id}`

**Scenario I — organic Core Engine message without `report_ids`**
- Publish a valid Core Engine-style `report.jobs` message with no `report_ids`
- Assert worker allocates report rows
- Assert report generation completes successfully

**Scenario J — generate API rejects running scan**
- Create a scan row with `status='running'`
- Call `POST /api/v1/reports/generate` with that scan ID
- Assert 409 response
- Assert no `report.jobs` message published

---

## Step 4.25 — End-to-End Tests: `tests/e2e/test_report_download_flow.py`

> ⚠️ **ISS-009 workaround:** The E2E test does not use `POST /api/v1/scrape/trigger` to start the chain. That endpoint is now async (returns 202, Step 4.0), but the scrape itself is non-deterministic in duration. Instead, Path 1 uses the `known_vuln_target` mode — the same approach as `test_e2e_system_trace.py` — to seed a program and trigger a scan directly against the local known-vulnerable target. This produces deterministic timing without depending on the HackerOne API or scrape duration.
>
> A separate, isolated test for the scraper trigger (Scenario A in `test_scraper_pipeline.py`) validates ISS-009's fix on its own. The e2e test validates the report chain only.

### Path 1 — canonical organic flow (using known-vuln-target)

```
1. Seed known_vuln_target program (or use one from a prior test run)
2. Trigger scan via POST /api/v1/scans/start with known_vuln_target scope
3. Poll scan status until completed or partial (max 600s)
4. Wait for report.jobs to be consumed and report rows to reach terminal state
5. Call GET /api/v1/scans/{scan_id}/reports
6. For each report_id in result:
   a. Call GET /api/v1/reports/{report_id}/download
   b. Follow the presigned URL
   c. Validate file bytes (see assertions below)
```

### Path 2 — regenerate flow

```
1. Use a scan_id from Path 1 (or seed a completed scan directly)
2. Call POST /api/v1/reports/generate with that scan_id
3. Assert 202 response and stable report_ids in body
4. Poll those exact report_id rows until terminal (max 120s)
5. Call GET /api/v1/reports/{report_id}/download for each
6. Follow the presigned URL
7. Validate file bytes
```

### Required assertions

- PDF starts with bytes `b"%PDF"`
- DOCX passes `zipfile.is_zipfile()` check
- Presigned URL contains an expiry parameter (`X-Amz-Expires` or `Expires`)
- Direct anonymous GET to `http://minio:9000/reports/...` returns 403 (bucket is not public)
- `report_id` returned from `POST /api/v1/reports/generate` matches the terminal artifact ID
- Organic Core Engine-generated reports (Path 1) succeed without `report_ids` in the payload

---

## Step 4.26 — Verification Commands

### Rebuild all images

```powershell
docker compose -f infra/docker-compose.yml --env-file .env `
  build --no-cache migrate core-engine reporter reporter-worker
```

### Verify Dockerfile contains the `__init__.py` COPY lines

Before rebuilding, confirm the fix is present:

```powershell
findstr "__init__" backend\services\reporter\Dockerfile
# Expected: two lines mentioning backend/__init__.py and backend/services/__init__.py
```

### Apply migration

```powershell
docker compose -f infra/docker-compose.yml --env-file .env `
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini upgrade head

docker compose -f infra/docker-compose.yml --env-file .env `
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini current
# Expected: "004 (head)"
```

### Start reporter before worker

Keep startup order explicit during verification so queue declaration and health are ready first:

```powershell
docker compose -f infra/docker-compose.yml --env-file .env up -d core-engine reporter
# Wait for reporter health to go green before starting the worker
docker compose -f infra/docker-compose.yml --env-file .env up -d reporter-worker
```

### Check logs

```powershell
docker compose -f infra/docker-compose.yml --env-file .env logs -f reporter
docker compose -f infra/docker-compose.yml --env-file .env logs -f reporter-worker
```

### Run tests

```powershell
pytest tests/unit/test_reporter.py -q --cov=backend/services/reporter --cov-report=term-missing
pytest tests/integration/test_reporter_pipeline.py -q
pytest tests/e2e/test_report_download_flow.py -q
```

### Trigger regenerate flow via API

```powershell
curl -X POST http://localhost:8003/api/v1/reports/generate `
  -H "Content-Type: application/json" `
  -d "{\"scan_id\":\"<SCAN_ID>\",\"formats_requested\":[\"pdf\",\"docx\"],\"include_evidence_screenshots\":true}"
```

### Trigger e2e organic chain (known-vuln-target mode)

```powershell
# Trigger scan against known-vuln-target (must be running on port 3001)
curl -X POST http://localhost:8002/api/v1/scans/start `
  -H "Content-Type: application/json" `
  -d "{\"program_id\":\"<KNOWN_VULN_PROGRAM_ID>\",\"scope\":{\"in_scope\":[\"http://host.docker.internal:3001\"],\"out_of_scope\":[]},\"feature_flags\":{}}"

# Then watch scan completion, report.jobs publication, report creation, and final download flow
```

---

## Common Pitfalls and Critical Gotchas

### 1. Dockerfile is missing `__init__.py` COPY lines

The two lines `COPY backend/__init__.py` and `COPY backend/services/__init__.py` are mandatory. Without them, all `from backend.shared.x import y` imports fail at container startup. This burned significant time in M2 (Default.md Mistake #6). Check with `findstr "__init__" Dockerfile` after writing the file.

### 2. `list[int]` and `list[str]` config fields fail to parse from env vars

Pydantic Settings cannot parse comma-separated env vars into `list[int]` or `list[str]` automatically. Use `str` fields with accessor methods (`get_retry_backoff()`, `get_default_formats()`). The defaults work fine in code — the problem only surfaces when someone tries to override via environment variable.

### 3. `"informational"` vs `"info"` — normalize everywhere

The M3 aggregator emits `"informational"` in the queue message. The Core Engine DB stores `"info"`. Call `_normalize_severity_breakdown()` on every `severity_breakdown` dict from any source. Do not assume either spelling.

### 4. ISS-009 — scraper trigger is now async

`POST /api/v1/scrape/trigger` returns 202 immediately. Any code that waited for `body["status"] == "completed"` is now broken. Update affected tests to poll `GET /api/v1/programs` instead. The e2e test uses `known_vuln_target` mode to avoid this path entirely.

### 5. `build_fallback_pack()` must produce the specified format

Golden-file tests assert against the exact fallback pack format defined in Step 4.10. If you invent a different format, the tests will fail. Keep the `"auto-generated as a fallback"` marker string — it is the assertion anchor.

### 6. `mark_partial()` must set `generated_at`

Partial reports are downloadable. The download endpoint allows access for `completed` and `partial`. If `generated_at` is NULL on a partial report, client polling logic that waits for `generated_at != null` hangs forever. This is called out in Step 4.7 — do not miss it.

### 7. `report_ids` is optional, not required

Organic Core Engine messages will not have it. Regenerate API messages will. Test both paths explicitly (Scenarios H and I in integration tests).

### 8. Stable `report_id` ownership must be single-source per message

If `report_ids` are present in the payload, the worker calls `mark_generating(report_id)`. If absent, the worker calls `create_or_reset_report()`. Never mix the two for the same message.

### 9. Sequential format rendering is intentional in M4

PDF and DOCX are rendered one after the other, not via `asyncio.gather`. This is a deliberate choice documented in Step 4.12. Do not parallelize them without addressing the shared `ParsedScan` object and temp file lifecycle.

### 10. Evidence concurrency cap prevents MinIO saturation

Always use `asyncio.Semaphore(settings.evidence_download_concurrency)` when downloading evidence artifacts. For large scans, uncapped concurrent MinIO downloads will exhaust the connection pool.

### 11. Clean up temp files in `finally` blocks — always

Both rendered report files and downloaded evidence files must be deleted in `finally` blocks whether the operation succeeds or fails. Missing a cleanup leads to disk accumulation in `/tmp/attackbot-reports`.

### 12. Use explicit retry countdowns

`settings.get_retry_backoff()` returns a list. Pass the correct entry to `self.retry(countdown=...)`. The configured values do nothing until they are wired into the Celery retry call.

### 13. `POST /api/v1/reports/generate` returns 409 for most non-terminal scan states

Only `completed` and `partial` scans can generate reports. All other states (`running`, `pending`, `failed_*`) return 409 Conflict. See the table in Step 4.20.

### 14. Upstream health checks use a cache

Do not make live HTTP calls to Core Engine and Scraper on every `/health` hit. The `_check_upstream_cached()` function caches results for `upstream_health_cache_ttl_seconds` (default 30s). Without caching, health checks add 100–400ms of latency and create cascading failure modes.

### 15. Attack Graph shows `degraded`, not `unhealthy`, in M4

The Attack Graph service is running but the chain detail API is unimplemented. `degraded` is the correct health status. `unhealthy` should only fire if the service is completely unreachable.

### 16. Declare `reports.completed` before publishing

`ensure_queue(Queues.REPORTS_COMPLETED)` must be called at startup, before any publish attempt. Passive declare alone is not safe on cold boot — if the queue does not exist yet, the publish will fail silently or raise.

### 17. Set `PYTHONPATH=/app`

Without this, `backend.*` imports inside any container fail immediately. It is set in the Dockerfile — verify it is present with `grep PYTHONPATH Dockerfile`.

### 18. Test the organic path, not just regenerate

The M4 DoD requires the canonical e2e chain: known-vuln-target scan → organic `report.jobs` message → report generation → presigned download. The regenerate path (Path 2) is a bonus test, not a substitute.

---

## Definition of Done Checklist

M4 is done only when all of the following are true:

**ISS-009:**
- [ ] `POST /api/v1/scrape/trigger` returns 202 immediately and runs scrape in background
- [ ] Affected scraper integration tests updated to poll rather than block

**Migration:**
- [ ] `004_reporter` migration applies cleanly — `alembic current` shows `004 (head)`
- [ ] `reports` and `reproduction_packs` tables exist with correct columns and constraints

**Schema:**
- [ ] `report.jobs` keeps schema-compatible `exploit_chains` object refs
- [ ] `report_ids` is optional and supports both organic and regenerate producers
- [ ] `reports.completed` schema defined and published correctly

**Dockerfile:**
- [ ] Reporter Dockerfile includes `COPY backend/__init__.py` and `COPY backend/services/__init__.py`
- [ ] `PYTHONPATH=/app` is set in Dockerfile
- [ ] `RUN mkdir -p /tmp/attackbot-reports` is in Dockerfile

**Config:**
- [ ] `default_formats_str` (not `list[str]`) with `get_default_formats()` accessor
- [ ] `report_task_retry_backoff_seconds_str` (not `list[int]`) with `get_retry_backoff()` accessor
- [ ] `upstream_health_cache_ttl_seconds` present
- [ ] `evidence_download_concurrency` present

**Core Engine:**
- [ ] `GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence` exists and returns correct shape

**Repository:**
- [ ] `create_or_reset_report()` implemented as true UPSERT on `(scan_id, format)`
- [ ] `mark_generating()` implemented as explicit targeted update
- [ ] `mark_partial()` sets `generated_at = NOW()`
- [ ] `mark_failed()` does NOT set `generated_at`

**Parsing:**
- [ ] `_normalize_severity_breakdown()` normalizes both `"info"` and `"informational"` to `"info"`
- [ ] `ParsedScanBuilder` calls normalization on every severity breakdown from any source

**Reproduction packs:**
- [ ] Packs are deterministic (sorted headers, params, body keys)
- [ ] `build_fallback_pack()` produces the exact format specified in Step 4.10
- [ ] Fallback packs contain `"auto-generated as a fallback"` marker string
- [ ] Any fallback pack usage marks report `partial`

**Evidence:**
- [ ] Evidence fetch is skipped entirely when `include_evidence_screenshots=false`
- [ ] Evidence downloads use `asyncio.Semaphore(settings.evidence_download_concurrency)`
- [ ] Downloaded evidence temp files are deleted in `finally` blocks

**Rendering:**
- [ ] Sequential rendering is the chosen approach with explanatory comment
- [ ] Both renderers check `include_raw_http_appendix` before adding Raw HTTP appendix
- [ ] Both renderers check `parsed_scan.include_evidence_screenshots` before image sections
- [ ] Rendered report temp files are deleted in `finally` blocks
- [ ] PDF validated by `%PDF` byte check before upload
- [ ] DOCX validated by zip archive check before upload

**API:**
- [ ] `POST /api/v1/reports/generate` exists and returns stable `report_ids`
- [ ] Generate endpoint returns 409 for all non-terminal scan states (running, pending, failed_*)
- [ ] Generate endpoint returns 202 for completed and partial scans
- [ ] `GET /api/v1/reports/{report_id}/download` returns 200 for completed and partial
- [ ] `GET /api/v1/reports/{report_id}/download` returns 409 for generating and failed
- [ ] Health endpoint shows Attack Graph as `degraded` (not `unhealthy`) with correct detail
- [ ] Health endpoint uses cached upstream reachability (TTL 30s default)

**Queues:**
- [ ] `reports.completed` is declared with `ensure_queue()` before any publish
- [ ] `report.jobs` consumed with `task_acks_late=True`
- [ ] Exhausted retries land in `report.jobs.dlq`
- [ ] Configured retry backoff is wired into `self.retry(countdown=...)`
- [ ] One `reports.completed` published per terminal artifact
- [ ] Publish failure after upload does not downgrade report status

**Storage:**
- [ ] Artifacts upload to `reports/{report_id}/report.{format}`
- [ ] Downloads use presigned URLs only — no public bucket access
- [ ] Presigned URLs are not logged

**Watchdog:**
- [ ] Stale `generating` rows are marked `failed` after `report_watchdog_stale_minutes`

**Compose:**
- [ ] `reporter-worker` still depends on `reporter: condition: service_healthy`

**Tests:**
- [ ] All unit tests pass (including new tests for severity normalization, health caching, `mark_partial`, fallback pack format, Raw HTTP appendix flag, `include_raw_http_appendix`)
- [ ] All integration tests pass (Scenarios A–J)
- [ ] E2E Path 1 passes using known-vuln-target mode
- [ ] E2E Path 2 passes using regenerate flow
- [ ] Reporter test coverage ≥ 80%
- [ ] Generation latency and failure metrics visible in Prometheus

---

## Changes from v1.5

| # | Severity | Change made |
|---|---|---|
| 1 | 🔴 Critical | Dockerfile now includes mandatory `COPY backend/__init__.py` and `COPY backend/services/__init__.py` lines |
| 2 | 🔴 Critical | `parsing.py` now specifies `_normalize_severity_breakdown()` to handle both `"info"` and `"informational"` keys from different sources |
| 3 | 🔴 Critical | Added Step 4.0 (ISS-009 fix: async scraper trigger). E2E test now uses `known_vuln_target` mode instead of `POST /api/v1/scrape/trigger` |
| 4 | 🔴 Critical | `list[int]` and `list[str]` config fields replaced with `str` fields and accessor methods to fix Pydantic Settings env var parsing |
| 5 | 🟡 Moderate | `build_fallback_pack()` exact output format specified with field-by-field content and required `"auto-generated as a fallback"` marker string |
| 6 | 🟡 Moderate | PDF golden-file comparison now specifies `pdfplumber` as the extraction library, with example extraction function |
| 7 | 🟡 Moderate | `include_raw_http_appendix` config field is now explicitly wired into both PDF and DOCX renderers with code example |
| 8 | 🟡 Moderate | `POST /api/v1/reports/generate` now has a complete table specifying the response for every possible scan state |
| 9 | 🟡 Moderate | `clients/__init__.py` and `renderers/__init__.py` called out explicitly as required empty files with creation instructions |
| 10 | 🔵 Minor | `asyncio.Semaphore(settings.evidence_download_concurrency)` added to evidence fetch, default cap of 10 |
| 11 | 🔵 Minor | Sequential format rendering documented as a deliberate choice with explanatory comment template |
| 12 | 🔵 Minor | Upstream health reachability now uses a 30-second cache with `_check_upstream_cached()` implementation |
| 13 | 🔵 Minor | `mark_partial()` `generated_at` rule promoted to a prominent callout box in Step 4.7 |
| 14 | 🔵 Minor | Attack Graph `degraded` vs `unhealthy` distinction defined clearly with a table in Step 4.8 |

---

## Changes from v2.0

| # | Severity | Change made |
|---|---|---|
| 1 | Critical | Added explicit execution gates (Gate 0-3) with hard progression criteria |
| 2 | Critical | Updated finding policy to include all findings in M4 and preserve `is_verified` for display |
| 3 | Moderate | Updated Core Engine client contract in M4 from verified-only fetch to full findings fetch |
| 4 | Moderate | Added renderer requirements for verification-status column and executive-summary caveat |
| 5 | Moderate | Made ISS-009 test migration explicit in Gate 1 (`test_trigger_produces_programs_in_db` polling update) |
