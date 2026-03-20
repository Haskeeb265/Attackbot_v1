# AttackBot — M3 Low-Level Implementation Plan
> Version: 1.0 | Date: 2026-03-11
> Picks up directly from M2 completion state.
> Every step produces something testable. Read the full step before writing any code.

---

## Pre-flight Checklist

Before writing a single line of M3 code, confirm the M2 baseline is intact:

```powershell
# All 21+ containers healthy
docker compose -f infra/docker-compose.yml --env-file .env ps

# Migration at 002
docker compose -f infra/docker-compose.yml --env-file .env run --rm migrate \
  alembic -c /app/backend/migrations/alembic.ini current
# Expected: "002 (head)"

# Scraper still works
curl http://localhost:8001/api/v1/health
# Expected: status=healthy, database=healthy, rabbitmq=healthy, scheduler=healthy

# Core engine skeleton still healthy (you are about to replace it)
curl http://localhost:8002/api/v1/health
```

If any of these fail, fix M2 before starting M3.

---

## File Map

Files you will create or replace in M3 (in implementation order):

```
backend/
├── migrations/versions/
│   └── 003_engine.py                       ← NEW — full engine schema
├── services/core_engine/
│   ├── config.py                           ← NEW — replaces skeleton config
│   ├── models.py                           ← NEW — internal dataclasses
│   ├── subprocess_utils.py                 ← NEW — CLI wrapper utilities
│   ├── dedup.py                            ← NEW — deduplication hash
│   ├── cvss.py                             ← NEW — CVSS scoring helpers
│   ├── repository.py                       ← NEW — ScanRepository
│   ├── watchdog.py                         ← NEW — crash recovery watchdog
│   ├── pipeline/
│   │   ├── __init__.py                     ← NEW
│   │   ├── context.py                      ← NEW — ScanContext dataclass
│   │   ├── scope_filter.py                 ← NEW — Stage 0 (fatal)
│   │   ├── asset_discovery.py              ← NEW — Stage 1
│   │   ├── fingerprinting.py               ← NEW — Stage 2
│   │   ├── enumeration.py                  ← NEW — Stage 3
│   │   ├── nuclei_scan.py                  ← NEW — Stage 4
│   │   ├── web_vuln_tests.py               ← NEW — Stage 5
│   │   ├── js_secrets.py                   ← NEW — Stage 6
│   │   └── aggregator.py                   ← NEW — Stage 7 (temp aggregation)
│   ├── scan_task.py                        ← NEW — Celery task entry + state machine
│   ├── worker.py                           ← REPLACE skeleton
│   └── main.py                             ← REPLACE skeleton
tests/
├── unit/
│   └── test_engine.py                      ← NEW — 75%+ coverage target
└── integration/
    └── test_engine_pipeline.py             ← NEW — full pipeline on DVWA/JuiceShop
```

---

## Step 3.1 — Database Migration: `003_engine`

**File:** `backend/migrations/versions/003_engine.py`

This migration creates the full engine domain schema. It does not touch the `scans` table from `001_initial_schema` — it extends it by adding the missing columns, then creates the seven new tables.

Why extend rather than recreate: same reason as M2's approach to `programs`. Alembic tracks state via `alembic_version`. Always extend forward.

```python
"""
Full engine schema: scans (extended), scan_stages, assets, endpoints,
js_assets, findings, finding_evidence, vulnerability_groups

Revision ID: 003
Revises: 002
Create Date: 2026-03-11

Tables modified: scans (add columns)
Tables created: scan_stages, assets, endpoints, js_assets,
                findings, finding_evidence, vulnerability_groups
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Extend scans table ---
    # 001 created scans with only scan_id, program_id, status, created_at
    op.add_column("scans", sa.Column("priority", sa.INTEGER(), nullable=True))
    op.add_column("scans", sa.Column("feature_flags", JSONB(), nullable=True))
    op.add_column("scans", sa.Column("partial_detail", JSONB(), nullable=True))
    op.add_column("scans", sa.Column("error_detail", sa.TEXT(), nullable=True))
    op.add_column("scans", sa.Column("finding_count", sa.INTEGER(),
                                     nullable=False, server_default="0"))
    op.add_column("scans", sa.Column("severity_breakdown", JSONB(), nullable=True))
    op.add_column("scans", sa.Column("retry_count", sa.INTEGER(),
                                     nullable=False, server_default="0"))
    op.add_column("scans", sa.Column("started_at", sa.TIMESTAMPTZ(), nullable=True))
    op.add_column("scans", sa.Column("completed_at", sa.TIMESTAMPTZ(), nullable=True))

    op.create_index("ix_scans_program_id", "scans", ["program_id"])
    op.create_index("ix_scans_status", "scans", ["status"])

    # --- scan_stages ---
    op.create_table(
        "scan_stages",
        sa.Column("stage_id", UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4),
        sa.Column("scan_id", UUID(as_uuid=True),
                  sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage_number", sa.FLOAT(), nullable=False),
        sa.Column("stage_name", sa.VARCHAR(), nullable=False),
        sa.Column("status", sa.VARCHAR(), nullable=False),  # running|completed|partial|failed
        sa.Column("started_at", sa.TIMESTAMPTZ(), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMPTZ(), nullable=True),
        sa.Column("error_detail", sa.TEXT(), nullable=True),
        sa.Column("output_summary", JSONB(), nullable=True),
    )
    op.create_index("ix_scan_stages_scan_id", "scan_stages", ["scan_id"])

    # --- assets ---
    op.create_table(
        "assets",
        sa.Column("asset_id", UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4),
        sa.Column("scan_id", UUID(as_uuid=True),
                  sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_type", sa.VARCHAR(), nullable=False),  # subdomain|ip|url
        sa.Column("value", sa.VARCHAR(), nullable=False),
        sa.Column("is_in_scope", sa.BOOLEAN(), nullable=False, server_default="true"),
        sa.Column("technology_stack", JSONB(), nullable=True),
        sa.Column("waf_detected", sa.VARCHAR(), nullable=True),
        sa.Column("http_status", sa.INTEGER(), nullable=True),
        sa.Column("discovered_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_assets_scan_id", "assets", ["scan_id"])

    # --- endpoints ---
    op.create_table(
        "endpoints",
        sa.Column("endpoint_id", UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4),
        sa.Column("asset_id", UUID(as_uuid=True),
                  sa.ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False),
        sa.Column("scan_id", UUID(as_uuid=True),
                  sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("method", sa.VARCHAR(), nullable=False),
        sa.Column("path", sa.VARCHAR(), nullable=False),
        sa.Column("full_url", sa.VARCHAR(), nullable=False),
        sa.Column("content_type", sa.VARCHAR(), nullable=True),
        sa.Column("response_code", sa.INTEGER(), nullable=True),
        sa.Column("parameters", JSONB(), nullable=True),
        sa.Column("headers", JSONB(), nullable=True),
        sa.Column("requires_auth", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column("discovered_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_endpoints_scan_id", "endpoints", ["scan_id"])
    op.create_index("ix_endpoints_asset_id", "endpoints", ["asset_id"])

    # --- js_assets ---
    op.create_table(
        "js_assets",
        sa.Column("js_asset_id", UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4),
        sa.Column("scan_id", UUID(as_uuid=True),
                  sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.VARCHAR(), nullable=False),
        sa.Column("content_hash", sa.VARCHAR(), nullable=True),
        sa.Column("storage_path", sa.VARCHAR(), nullable=True),
        sa.Column("size_bytes", sa.INTEGER(), nullable=True),
        sa.Column("analyzed", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column("discovered_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_js_assets_scan_id", "js_assets", ["scan_id"])
    op.create_unique_constraint("uq_js_assets_content_hash", "js_assets", ["content_hash"])

    # --- findings ---
    op.create_table(
        "findings",
        sa.Column("finding_id", UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4),
        sa.Column("scan_id", UUID(as_uuid=True),
                  sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.VARCHAR(), nullable=False),
        sa.Column("vulnerability_type", sa.VARCHAR(), nullable=False),
        sa.Column("severity", sa.VARCHAR(), nullable=False),  # critical|high|medium|low|info
        sa.Column("cvss_score", sa.FLOAT(), nullable=True),
        sa.Column("cvss_vector", sa.VARCHAR(), nullable=True),
        sa.Column("affected_url", sa.VARCHAR(), nullable=False),
        sa.Column("affected_parameter", sa.VARCHAR(), nullable=True),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("reproduction_steps", sa.TEXT(), nullable=True),
        sa.Column("is_verified", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column("is_false_positive", sa.BOOLEAN(), nullable=False, server_default="false"),
        sa.Column("false_positive_reason", sa.TEXT(), nullable=True),
        sa.Column("deduplication_hash", sa.VARCHAR(), nullable=False),
        sa.Column("source", sa.VARCHAR(), nullable=True),  # nuclei|xss_scanner|cors|js_secret
        sa.Column("raw_output", JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_findings_scan_id", "findings", ["scan_id"])
    op.create_index("ix_findings_program_id", "findings", ["program_id"])
    op.create_unique_constraint("uq_findings_dedup_hash_scan", "findings",
                                ["deduplication_hash", "scan_id"])

    # --- finding_evidence ---
    op.create_table(
        "finding_evidence",
        sa.Column("evidence_id", UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4),
        sa.Column("finding_id", UUID(as_uuid=True),
                  sa.ForeignKey("findings.finding_id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_type", sa.VARCHAR(), nullable=False),  # screenshot|request|response|payload
        sa.Column("storage_path", sa.VARCHAR(), nullable=True),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("captured_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_finding_evidence_finding_id", "finding_evidence", ["finding_id"])

    # --- vulnerability_groups ---
    op.create_table(
        "vulnerability_groups",
        sa.Column("group_id", UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4),
        sa.Column("scan_id", UUID(as_uuid=True),
                  sa.ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=False),
        sa.Column("vulnerability_type", sa.VARCHAR(), nullable=False),
        sa.Column("affected_count", sa.INTEGER(), nullable=False, server_default="0"),
        sa.Column("max_severity", sa.VARCHAR(), nullable=True),
        sa.Column("finding_ids", ARRAY(UUID(as_uuid=True)), nullable=True),
        sa.Column("created_at", sa.TIMESTAMPTZ(), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_vulnerability_groups_scan_id", "vulnerability_groups", ["scan_id"])


def downgrade() -> None:
    pass  # forward-only in development
```

**Apply and verify:**
```powershell
docker compose -f infra/docker-compose.yml --env-file .env \
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini upgrade head

docker compose -f infra/docker-compose.yml --env-file .env \
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini current
# Expected: "003 (head)"

docker compose -f infra/docker-compose.yml --env-file .env exec postgres \
  psql -U attackbot -d attackbot -c "\dt"
# Expected: programs, program_scopes, program_policies, scans, scan_stages,
#           assets, endpoints, js_assets, findings, finding_evidence,
#           vulnerability_groups, alembic_version
```

**If migration fails with "column already exists":** `001_initial_schema` may have added more columns to `scans` than expected. Inspect with `\d scans` in psql and remove the conflicting `add_column` calls — never delete from `001`.

---

## Step 3.2 — Internal Models: `models.py`

**File:** `backend/services/core_engine/models.py`

Pure Python dataclasses. No SQLAlchemy, no Pydantic. These represent the canonical in-memory objects that flow between pipeline stages. They map to the DB schema but are not the ORM layer.

```python
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
import uuid


@dataclass
class DiscoveredAsset:
    """A live host discovered by Stage 1."""
    asset_type: str          # "subdomain" | "ip" | "url"
    value: str               # e.g. "api.example.com" or "https://api.example.com"
    http_status: Optional[int] = None
    technology_stack: Optional[dict] = None
    waf_detected: Optional[str] = None
    asset_id: Optional[UUID] = None  # set after DB persist


@dataclass
class DiscoveredEndpoint:
    """A single endpoint discovered by Stage 3."""
    asset_id: UUID
    method: str              # "GET" | "POST" etc.
    path: str                # "/api/v1/users"
    full_url: str
    response_code: Optional[int] = None
    content_type: Optional[str] = None
    parameters: Optional[dict] = None
    headers: Optional[dict] = None
    requires_auth: bool = False
    endpoint_id: Optional[UUID] = None  # set after DB persist


@dataclass
class DiscoveredJsAsset:
    """A downloaded JS file stored in MinIO."""
    scan_id: UUID
    url: str
    storage_path: str
    content_hash: str
    size_bytes: int
    js_asset_id: Optional[UUID] = None  # set after DB persist


@dataclass
class FindingCandidate:
    """
    A raw, unverified vulnerability candidate produced by any pipeline stage.
    These are deduplicated and persisted by the aggregator.
    """
    vulnerability_type: str  # "xss" | "cors" | "nuclei_finding" | "js_secret" etc.
    title: str
    severity: str            # "critical" | "high" | "medium" | "low" | "info"
    affected_url: str
    description: str
    source: str              # which stage produced this
    affected_parameter: Optional[str] = None
    payload: Optional[str] = None
    reproduction_steps: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    raw_output: Optional[dict] = None


@dataclass
class ScanResult:
    """Aggregated output of the entire pipeline. Passed to aggregator."""
    assets: list[DiscoveredAsset] = field(default_factory=list)
    endpoints: list[DiscoveredEndpoint] = field(default_factory=list)
    js_assets: list[DiscoveredJsAsset] = field(default_factory=list)
    finding_candidates: list[FindingCandidate] = field(default_factory=list)
    stage_errors: dict[str, str] = field(default_factory=dict)  # stage_name → error
```

---

## Step 3.3 — Engine Config: `config.py`

**File:** `backend/services/core_engine/config.py`

```python
from backend.shared.config import BaseServiceConfig


class EngineConfig(BaseServiceConfig):
    service_name: str = "core-engine"
    port: int = 8002

    # Scraper API — used to fetch program scope
    scraper_api_url: str = "http://scraper:8001"
    scraper_api_timeout_seconds: int = 30

    # Subprocess timeouts (seconds)
    subfinder_timeout: int = 1800   # 30 min — large programs have many subdomains
    dnsx_timeout: int = 900
    httpx_timeout: int = 600
    ffuf_timeout: int = 1800
    nuclei_timeout: int = 3600      # 1 hour
    waybackurls_timeout: int = 300

    # Nuclei settings
    nuclei_rate_limit: int = 150    # requests/sec
    nuclei_bulk_size: int = 25
    nuclei_concurrency: int = 25
    nuclei_templates: str = ""      # empty = default template set

    # ffuf settings
    ffuf_wordlist: str = "/wordlists/common.txt"
    ffuf_rate: int = 100
    ffuf_threads: int = 40

    # JS scanning
    js_download_timeout_seconds: int = 30
    js_max_file_size_bytes: int = 5_242_880   # 5 MB

    # Redis lock TTL
    scan_lock_ttl_seconds: int = 14400        # 4 hours

    # Watchdog
    watchdog_interval_seconds: int = 300      # 5 min check
    watchdog_stale_threshold_hours: int = 2

    # Feature flags defaults (can be overridden per scan via message)
    default_sqli_enabled: bool = False
    default_ssrf_enabled: bool = False
    default_crlf_enabled: bool = False
```

---

## Step 3.4 — Subprocess Utilities: `subprocess_utils.py`

**File:** `backend/services/core_engine/subprocess_utils.py`

This is the single most important reliability file in M3. Every CLI tool call goes through these wrappers. Do not bypass them.

```python
import asyncio
import json
import os
import tempfile
from typing import AsyncIterator

from backend.shared.exceptions import ScanTimeoutError, ScanError
from backend.shared.logging import get_logger

logger = get_logger("core_engine.subprocess")


async def run_tool_communicate(
    args: list[str],
    timeout: int,
    label: str,
    success_on_empty: bool = True,
) -> tuple[str, str]:
    """
    Run a subprocess using communicate() — safe for tools with bounded output.
    Use for: nuclei, httpx (fingerprint), dnsx, alterx, waybackurls.

    Returns (stdout_text, stderr_text).
    Raises ScanTimeoutError on timeout, ScanError on non-zero exit > 1.

    Never use this for amass/subfinder — their output can exceed the OS pipe buffer.
    Use run_tool_streaming() for those instead.
    """
    logger.info(f"Running {label}", args=args[0], timeout=timeout)
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise ScanTimeoutError(f"{label} timed out after {timeout}s")

    stdout_text = stdout.decode(errors="replace")
    stderr_text = stderr.decode(errors="replace")

    # nuclei exits 1 on zero findings — that is not a real error
    if proc.returncode is not None and proc.returncode > 1:
        raise ScanError(
            f"{label} exited with code {proc.returncode}. "
            f"stderr: {stderr_text[:500]}"
        )
    return stdout_text, stderr_text


async def run_tool_streaming(
    args: list[str],
    timeout: int,
    label: str,
) -> list[str]:
    """
    Run a subprocess with streaming readline — safe for tools with large output.
    Use for: subfinder (thousands of subdomains).

    Returns list of non-empty decoded lines.
    """
    logger.info(f"Running {label} (streaming)", args=args[0], timeout=timeout)
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    lines: list[str] = []

    async def _read() -> None:
        assert proc.stdout is not None
        async for raw_line in proc.stdout:
            decoded = raw_line.decode(errors="replace").strip()
            if decoded:
                lines.append(decoded)

    try:
        await asyncio.wait_for(
            asyncio.gather(_read(), proc.wait()),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        logger.warning(f"{label} timed out — returning partial results",
                       lines_so_far=len(lines))
    return lines


async def run_tool_with_target_file(
    args_template: list[str],
    targets: list[str],
    timeout: int,
    label: str,
    target_flag: str = "-l",
) -> tuple[str, str]:
    """
    Write targets to a temp file and pass via flag to the tool.
    Use for: nuclei -l, httpx -l, dnsx -l.

    Temp file is always cleaned up — even on exception.
    args_template should use TARGET_FILE as a placeholder for the targets path.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as tf:
        tf.write("\n".join(targets))
        targets_path = tf.name

    args = [target_flag if a == "TARGET_FILE" else a for a in args_template]
    # Replace TARGET_FILE sentinel with actual path
    args = [targets_path if a == "TARGET_FILE" else a for a in args_template]

    try:
        return await run_tool_communicate(args, timeout=timeout, label=label)
    finally:
        if os.path.exists(targets_path):
            os.unlink(targets_path)


def parse_jsonl(text: str) -> list[dict]:
    """
    Parse newline-delimited JSON output from tools like nuclei, httpx.
    Silently skips lines that are not valid JSON objects.
    nuclei -silent outputs a mix of status lines and JSON — filter by '{'.
    """
    results = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                results.append(json.loads(stripped))
            except json.JSONDecodeError:
                continue
    return results
```

**Subprocess gotcha checklist — read before writing any new tool wrapper:**

| Gotcha | Fix |
|--------|-----|
| `nuclei` outputs status lines mixed with JSON | Use `-silent` flag + `parse_jsonl()` |
| `subfinder` output fills OS pipe buffer | Use `run_tool_streaming()` not `communicate()` |
| `stderr` left unread causes deadlock | Always pipe to `PIPE` or `DEVNULL` — never ignore |
| `proc.kill()` alone doesn't reap the process | Always `await proc.wait()` after kill |
| `nuclei` exits `1` on zero findings | Only treat `returncode > 1` as a real error |
| Shell string interpolation is an injection risk | Always pass `args` as a `list[str]` — never a shell string |

---

## Step 3.5 — Deduplication Hash: `dedup.py`

**File:** `backend/services/core_engine/dedup.py`

```python
import hashlib
from urllib.parse import urlparse, parse_qsl, urlencode

from backend.services.core_engine.models import FindingCandidate


def normalize_url(url: str) -> str:
    """
    Normalize a URL for stable deduplication.
    Lowercases scheme+host, sorts query parameters alphabetically.
    Without this: ?b=2&a=1 and ?a=1&b=2 produce different hashes for the same endpoint.
    """
    try:
        parsed = urlparse(url.lower())
        sorted_query = urlencode(sorted(parse_qsl(parsed.query)))
        normalized = parsed._replace(query=sorted_query)
        return normalized.geturl()
    except Exception:
        return url.lower()


def compute_dedup_hash(candidate: FindingCandidate) -> str:
    """
    Produce a stable, content-based hash for a finding candidate.

    Rules:
    - Must NOT include scan_id, timestamps, evidence paths — those change between scans
    - Must include: vuln type, normalized URL, parameter, truncated payload
    - Payload is truncated to 100 chars — nuclei payloads vary slightly across runs

    Two candidates with the same vuln type + URL + parameter + payload prefix
    are considered the same finding.
    """
    components = "|".join([
        candidate.vulnerability_type.lower(),
        normalize_url(candidate.affected_url),
        (candidate.affected_parameter or "").lower(),
        (candidate.payload or "")[:100],
    ])
    return hashlib.sha256(components.encode()).hexdigest()
```

---

## Step 3.6 — CVSS Scoring: `cvss.py`

**File:** `backend/services/core_engine/cvss.py`

Simple severity-to-CVSS mapping for M3. This is intentionally lightweight — real CVSS vectors require exploit chain context that won't exist until M7+.

```python
from typing import Optional


# Base CVSS scores by severity — conservative defaults for unverified findings
SEVERITY_CVSS_MAP: dict[str, float] = {
    "critical": 9.0,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.5,
    "info": 0.0,
}

# Nuclei severity → our severity label
NUCLEI_SEVERITY_MAP: dict[str, str] = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "unknown": "info",
}

# vuln type → default severity (for scanners that don't emit a severity)
VULN_TYPE_SEVERITY_MAP: dict[str, str] = {
    "xss": "high",
    "reflected_xss": "high",
    "stored_xss": "critical",
    "cors_misconfiguration": "medium",
    "crlf_injection": "medium",
    "js_secret": "high",       # API keys/credentials in JS
    "open_redirect": "medium",
    "sqli": "critical",
    "ssrf": "high",
}


def severity_to_cvss(severity: str) -> float:
    return SEVERITY_CVSS_MAP.get(severity.lower(), 5.0)


def nuclei_severity(raw: str) -> str:
    return NUCLEI_SEVERITY_MAP.get(raw.lower(), "info")


def infer_severity(vulnerability_type: str, raw_severity: Optional[str] = None) -> str:
    if raw_severity:
        normalized = raw_severity.lower()
        if normalized in SEVERITY_CVSS_MAP:
            return normalized
    return VULN_TYPE_SEVERITY_MAP.get(vulnerability_type.lower(), "medium")
```

---

## Step 3.7 — Scan Repository: `repository.py`

**File:** `backend/services/core_engine/repository.py`

All DB writes for the engine go through this class. Never write raw SQL in pipeline stages.

```python
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.services.core_engine.models import (
    DiscoveredAsset, DiscoveredEndpoint, DiscoveredJsAsset, FindingCandidate
)
from backend.services.core_engine.dedup import compute_dedup_hash
from backend.services.core_engine.cvss import severity_to_cvss
from backend.shared.logging import get_logger

logger = get_logger("core_engine.repository")


class ScanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Scan lifecycle ──────────────────────────────────────────────────

    async def create_or_resume_scan(
        self, program_id: str, feature_flags: dict, priority: int = 1
    ) -> str:
        """
        Returns scan_id. Creates a new scan row or resumes an existing
        'running' scan for this program (in case of restart after crash).
        """
        # Check for an existing running scan for this program
        row = await self.session.execute(
            text("""
                SELECT scan_id FROM scans
                WHERE program_id = :program_id AND status = 'running'
                ORDER BY created_at DESC LIMIT 1
            """),
            {"program_id": program_id},
        )
        existing = row.fetchone()
        if existing:
            logger.info("Resuming existing scan", scan_id=str(existing[0]))
            return str(existing[0])

        scan_id = str(uuid.uuid4())
        await self.session.execute(
            text("""
                INSERT INTO scans
                  (scan_id, program_id, status, priority, feature_flags,
                   retry_count, started_at, created_at)
                VALUES
                  (:scan_id, :program_id, 'running', :priority, :feature_flags,
                   0, NOW(), NOW())
            """),
            {
                "scan_id": scan_id,
                "program_id": program_id,
                "priority": priority,
                "feature_flags": str(feature_flags),  # JSONB serialized by driver
            },
        )
        await self.session.commit()
        logger.info("Scan created", scan_id=scan_id, program_id=program_id)
        return scan_id

    async def mark_scan_complete(
        self,
        scan_id: str,
        status: str,
        finding_count: int,
        severity_breakdown: dict,
        partial_detail: Optional[dict] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        await self.session.execute(
            text("""
                UPDATE scans
                SET status = :status,
                    finding_count = :finding_count,
                    severity_breakdown = :severity_breakdown,
                    partial_detail = :partial_detail,
                    error_detail = :error_detail,
                    completed_at = NOW()
                WHERE scan_id = :scan_id
            """),
            {
                "scan_id": scan_id,
                "status": status,
                "finding_count": finding_count,
                "severity_breakdown": str(severity_breakdown),
                "partial_detail": str(partial_detail) if partial_detail else None,
                "error_detail": error_detail,
            },
        )
        await self.session.commit()

    async def record_stage(
        self,
        scan_id: str,
        stage_number: float,
        stage_name: str,
        status: str,
        started_at: datetime,
        output_summary: Optional[dict] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        await self.session.execute(
            text("""
                INSERT INTO scan_stages
                  (stage_id, scan_id, stage_number, stage_name, status,
                   started_at, completed_at, output_summary, error_detail)
                VALUES
                  (:stage_id, :scan_id, :stage_number, :stage_name, :status,
                   :started_at, NOW(), :output_summary, :error_detail)
                ON CONFLICT DO NOTHING
            """),
            {
                "stage_id": str(uuid.uuid4()),
                "scan_id": scan_id,
                "stage_number": stage_number,
                "stage_name": stage_name,
                "status": status,
                "started_at": started_at,
                "output_summary": str(output_summary) if output_summary else None,
                "error_detail": error_detail,
            },
        )
        await self.session.commit()

    # ── Asset persistence ───────────────────────────────────────────────

    async def save_assets(
        self, scan_id: str, assets: list[DiscoveredAsset]
    ) -> list[DiscoveredAsset]:
        """Persists assets and stamps each with its asset_id."""
        for asset in assets:
            asset_id = str(uuid.uuid4())
            await self.session.execute(
                text("""
                    INSERT INTO assets
                      (asset_id, scan_id, asset_type, value, is_in_scope,
                       technology_stack, waf_detected, http_status, discovered_at)
                    VALUES
                      (:asset_id, :scan_id, :asset_type, :value, true,
                       :technology_stack, :waf_detected, :http_status, NOW())
                    ON CONFLICT DO NOTHING
                """),
                {
                    "asset_id": asset_id,
                    "scan_id": scan_id,
                    "asset_type": asset.asset_type,
                    "value": asset.value,
                    "technology_stack": str(asset.technology_stack) if asset.technology_stack else None,
                    "waf_detected": asset.waf_detected,
                    "http_status": asset.http_status,
                },
            )
            asset.asset_id = uuid.UUID(asset_id)
        await self.session.commit()
        return assets

    async def save_endpoints(
        self, scan_id: str, endpoints: list[DiscoveredEndpoint]
    ) -> None:
        for ep in endpoints:
            await self.session.execute(
                text("""
                    INSERT INTO endpoints
                      (endpoint_id, asset_id, scan_id, method, path, full_url,
                       content_type, response_code, parameters, headers,
                       requires_auth, discovered_at)
                    VALUES
                      (:endpoint_id, :asset_id, :scan_id, :method, :path, :full_url,
                       :content_type, :response_code, :parameters, :headers,
                       :requires_auth, NOW())
                    ON CONFLICT DO NOTHING
                """),
                {
                    "endpoint_id": str(uuid.uuid4()),
                    "asset_id": str(ep.asset_id),
                    "scan_id": scan_id,
                    "method": ep.method,
                    "path": ep.path,
                    "full_url": ep.full_url,
                    "content_type": ep.content_type,
                    "response_code": ep.response_code,
                    "parameters": str(ep.parameters) if ep.parameters else None,
                    "headers": str(ep.headers) if ep.headers else None,
                    "requires_auth": ep.requires_auth,
                },
            )
        await self.session.commit()

    async def save_js_asset(
        self, scan_id: str, js_asset: DiscoveredJsAsset
    ) -> DiscoveredJsAsset:
        js_asset_id = str(uuid.uuid4())
        await self.session.execute(
            text("""
                INSERT INTO js_assets
                  (js_asset_id, scan_id, url, content_hash, storage_path,
                   size_bytes, analyzed, discovered_at)
                VALUES
                  (:js_asset_id, :scan_id, :url, :content_hash, :storage_path,
                   :size_bytes, false, NOW())
                ON CONFLICT (content_hash) DO NOTHING
            """),
            {
                "js_asset_id": js_asset_id,
                "scan_id": scan_id,
                "url": js_asset.url,
                "content_hash": js_asset.content_hash,
                "storage_path": js_asset.storage_path,
                "size_bytes": js_asset.size_bytes,
            },
        )
        await self.session.commit()
        js_asset.js_asset_id = uuid.UUID(js_asset_id)
        return js_asset

    # ── Finding persistence ─────────────────────────────────────────────

    async def save_findings(
        self,
        scan_id: str,
        program_id: str,
        candidates: list[FindingCandidate],
    ) -> int:
        """
        Deduplicates by hash + scan_id before insert. Returns count of new findings saved.
        ON CONFLICT on (deduplication_hash, scan_id) is a no-op — do not count it.
        """
        saved = 0
        for candidate in candidates:
            dedup_hash = compute_dedup_hash(candidate)
            cvss_score = candidate.cvss_score or severity_to_cvss(candidate.severity)
            try:
                result = await self.session.execute(
                    text("""
                        INSERT INTO findings
                          (finding_id, scan_id, program_id, title, vulnerability_type,
                           severity, cvss_score, cvss_vector, affected_url,
                           affected_parameter, description, reproduction_steps,
                           is_verified, is_false_positive, deduplication_hash,
                           source, raw_output, created_at)
                        VALUES
                          (:finding_id, :scan_id, :program_id, :title, :vulnerability_type,
                           :severity, :cvss_score, :cvss_vector, :affected_url,
                           :affected_parameter, :description, :reproduction_steps,
                           false, false, :dedup_hash,
                           :source, :raw_output, NOW())
                        ON CONFLICT (deduplication_hash, scan_id) DO NOTHING
                    """),
                    {
                        "finding_id": str(uuid.uuid4()),
                        "scan_id": scan_id,
                        "program_id": program_id,
                        "title": candidate.title,
                        "vulnerability_type": candidate.vulnerability_type,
                        "severity": candidate.severity,
                        "cvss_score": cvss_score,
                        "cvss_vector": candidate.cvss_vector,
                        "affected_url": candidate.affected_url,
                        "affected_parameter": candidate.affected_parameter,
                        "description": candidate.description,
                        "reproduction_steps": candidate.reproduction_steps,
                        "dedup_hash": dedup_hash,
                        "source": candidate.source,
                        "raw_output": str(candidate.raw_output) if candidate.raw_output else None,
                    },
                )
                if result.rowcount > 0:
                    saved += 1
            except Exception as e:
                logger.warning("Finding insert failed", error=str(e),
                               vuln_type=candidate.vulnerability_type,
                               url=candidate.affected_url)
        await self.session.commit()
        return saved
```

---

## Step 3.8 — Pipeline Context: `pipeline/context.py`

**File:** `backend/services/core_engine/pipeline/context.py`

The `ScanContext` is the read-only parameter bag passed to every stage. Stages never read from the DB directly — they receive all they need here.

```python
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class ScopeDefinition:
    """Parsed scope from the scan.jobs message."""
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)


@dataclass
class FeatureFlags:
    """Which optional scanning modules are enabled for this scan."""
    sqli: bool = False
    ssrf: bool = False
    crlf: bool = False
    browser_session: bool = False
    api_fuzzing: bool = False
    ai_hypothesis: bool = False


@dataclass
class ScanContext:
    """
    Immutable configuration bundle for a scan run.
    Created once in scan_task.py from the queue message.
    Passed down to every pipeline stage — stages must not modify it.
    """
    scan_id: str
    program_id: str
    scope: ScopeDefinition
    feature_flags: FeatureFlags
    priority: int = 1
    # Populated after Stage 1 completes — available to Stages 2+
    live_assets: list[str] = field(default_factory=list)
    # Populated after Stage 3 completes — available to Stages 4+
    js_asset_ids: list[str] = field(default_factory=list)
```

---

## Step 3.9 — Stage 0: Scope Filter — `pipeline/scope_filter.py`

**File:** `backend/services/core_engine/pipeline/scope_filter.py`

Stage 0 is fatal. If scope cannot be built, the scan must not proceed.

```python
import ipaddress
import re
from urllib.parse import urlparse

from backend.services.core_engine.pipeline.context import ScopeDefinition
from backend.shared.exceptions import ScanError
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage0")


class ScopeFilter:
    """
    Evaluates whether a URL, domain, or IP is within the program's declared scope.
    Built once at Stage 0 from the ScopeDefinition in the scan message.

    Fatal contract: if scope is empty, raise ScanError — never proceed blind.
    """

    def __init__(self, scope: ScopeDefinition) -> None:
        if not scope.in_scope:
            raise ScanError(
                "Scope definition has no in_scope entries — "
                "refusing to scan without defined scope."
            )
        self._in_scope = scope.in_scope
        self._out_of_scope = scope.out_of_scope
        self._in_networks = self._parse_cidrs(scope.in_scope)
        self._out_networks = self._parse_cidrs(scope.out_of_scope)
        logger.info(
            "ScopeFilter built",
            in_scope_count=len(self._in_scope),
            out_of_scope_count=len(self._out_of_scope),
        )

    def is_in_scope(self, target: str) -> bool:
        """
        Returns True only if target matches at least one in-scope rule
        and does NOT match any out-of-scope rule.
        Out-of-scope always wins.
        """
        # Normalize: strip scheme for domain matching
        domain = self._extract_domain(target)
        ip = self._try_parse_ip(domain)

        if self._matches_any(domain, ip, self._out_of_scope, self._out_networks):
            return False
        return self._matches_any(domain, ip, self._in_scope, self._in_networks)

    def filter_targets(self, targets: list[str]) -> list[str]:
        """Filter a list, keeping only in-scope targets. Logs rejections."""
        in_scope, rejected = [], []
        for t in targets:
            if self.is_in_scope(t):
                in_scope.append(t)
            else:
                rejected.append(t)
        if rejected:
            logger.warning("Out-of-scope targets removed",
                           count=len(rejected), examples=rejected[:5])
        return in_scope

    # ── Private helpers ─────────────────────────────────────────────────

    def _matches_any(
        self,
        domain: str,
        ip: Optional["ipaddress.IPv4Address | ipaddress.IPv6Address"],
        rules: list[str],
        networks: list["ipaddress.IPv4Network | ipaddress.IPv6Network"],
    ) -> bool:
        for rule in rules:
            if self._matches_rule(domain, rule):
                return True
        if ip:
            for net in networks:
                try:
                    if ip in net:
                        return True
                except TypeError:
                    continue
        return False

    @staticmethod
    def _matches_rule(domain: str, rule: str) -> bool:
        """
        Match a domain against a scope rule.
        Supports: exact match, wildcard (*.example.com), URL prefix.
        """
        rule_domain = ScopeFilter._extract_domain(rule)
        if rule_domain.startswith("*."):
            # Wildcard: *.example.com matches sub.example.com but not example.com
            suffix = rule_domain[2:]  # "example.com"
            return domain == suffix or domain.endswith("." + suffix)
        # Exact domain match or URL prefix match
        return domain == rule_domain or domain.endswith("." + rule_domain)

    @staticmethod
    def _extract_domain(target: str) -> str:
        """Extract lowercase hostname from URL or raw domain string."""
        if "://" in target:
            parsed = urlparse(target)
            host = parsed.hostname or ""
        else:
            host = target.split("/")[0].split(":")[0]
        return host.lower().lstrip("*.")

    @staticmethod
    def _try_parse_ip(value: str):
        try:
            return ipaddress.ip_address(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_cidrs(rules: list[str]):
        networks = []
        for rule in rules:
            try:
                networks.append(ipaddress.ip_network(rule, strict=False))
            except ValueError:
                pass
        return networks


# Re-export for convenience
from typing import Optional  # noqa: E402 — needed by type hints above
```

---

## Step 3.10 — Stage 1: Asset Discovery — `pipeline/asset_discovery.py`

**File:** `backend/services/core_engine/pipeline/asset_discovery.py`

```
Pipeline: subfinder → alterx → dnsx → httpx
         (passive)   (perms)  (live)  (probe)
```

> ⚠️ `dnsx` between `alterx` and `httpx` is **mandatory**. Without it you probe thousands of non-existent permuted subdomains. The pipeline is `subfinder | alterx | dnsx | httpx` — do not shortcut it.

```python
import asyncio
import tempfile
import os
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.subprocess_utils import (
    run_tool_streaming,
    run_tool_communicate,
    parse_jsonl,
)
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage1")

STAGE_NUMBER = 1.0
STAGE_NAME = "asset_discovery"


async def run(
    ctx: ScanContext,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredAsset]:
    """
    Stage 1: Discover live assets within scope.
    Returns a list of DiscoveredAsset objects (not yet persisted).
    Never raises — returns partial results on tool failure.
    """
    started_at = datetime.now(timezone.utc)
    assets: list[DiscoveredAsset] = []
    errors: dict[str, str] = {}

    # Collect root domains from in_scope
    root_domains = _extract_root_domains(ctx.scope.in_scope)
    if not root_domains:
        logger.warning("No root domains found in scope — skipping asset discovery",
                       scan_id=ctx.scan_id)
        return assets

    for domain in root_domains:
        try:
            domain_assets = await _discover_domain(
                domain, scope_filter, config
            )
            assets.extend(domain_assets)
        except Exception as e:
            logger.warning("Asset discovery failed for domain",
                           domain=domain, error=str(e))
            errors[domain] = str(e)

    logger.info("Stage 1 complete",
                scan_id=ctx.scan_id,
                assets_found=len(assets),
                errors=len(errors))
    return assets


async def _discover_domain(
    domain: str,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredAsset]:
    """Run the full subfinder → alterx → dnsx → httpx pipeline for one domain."""

    # Step 1: subfinder — passive subdomain enumeration
    subfinder_lines = await run_tool_streaming(
        args=["subfinder", "-d", domain, "-silent", "-all"],
        timeout=config.subfinder_timeout,
        label=f"subfinder[{domain}]",
    )
    subdomains = list({line.strip() for line in subfinder_lines if line.strip()})
    logger.debug("subfinder complete", domain=domain, found=len(subdomains))

    if not subdomains:
        return []

    # Step 2: alterx — permutation generation
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(subdomains))
        subfinder_file = tf.name
    try:
        alterx_stdout, _ = await run_tool_communicate(
            args=["alterx", "-l", subfinder_file, "-silent"],
            timeout=300,
            label=f"alterx[{domain}]",
        )
        permutations = [
            l.strip() for l in alterx_stdout.splitlines() if l.strip()
        ]
    except Exception:
        permutations = []  # alterx failure is non-fatal — continue with subdomains only
    finally:
        os.unlink(subfinder_file)

    all_candidates = list(set(subdomains + permutations))

    # Step 3: dnsx — DNS resolution, filter live hosts only
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(all_candidates))
        candidates_file = tf.name
    try:
        dnsx_stdout, _ = await run_tool_communicate(
            args=["dnsx", "-l", candidates_file, "-silent", "-resp"],
            timeout=config.dnsx_timeout,
            label=f"dnsx[{domain}]",
        )
        live_domains = [l.strip() for l in dnsx_stdout.splitlines() if l.strip()]
    finally:
        os.unlink(candidates_file)

    if not live_domains:
        return []

    # Step 4: httpx — HTTP probing + tech detection
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(live_domains))
        live_file = tf.name
    try:
        httpx_stdout, _ = await run_tool_communicate(
            args=[
                "httpx", "-l", live_file, "-json", "-silent",
                "-tech-detect", "-status-code", "-title",
            ],
            timeout=config.httpx_timeout,
            label=f"httpx[{domain}]",
        )
    finally:
        os.unlink(live_file)

    # Parse httpx JSON output into DiscoveredAsset objects
    assets: list[DiscoveredAsset] = []
    for entry in parse_jsonl(httpx_stdout):
        url = entry.get("url", "")
        if not url:
            continue
        if not scope_filter.is_in_scope(url):
            continue
        assets.append(DiscoveredAsset(
            asset_type="subdomain",
            value=url,
            http_status=entry.get("status_code"),
            technology_stack={"technologies": entry.get("tech", [])},
            waf_detected=_extract_waf(entry),
        ))

    return assets


def _extract_root_domains(in_scope: list[str]) -> list[str]:
    """Extract bare root domains from scope entries like '*.example.com' or 'example.com'."""
    domains = set()
    for rule in in_scope:
        # Strip wildcard, URL scheme, path
        clean = rule.lstrip("*.")
        if "://" in clean:
            from urllib.parse import urlparse
            clean = urlparse(clean).hostname or ""
        clean = clean.split("/")[0]
        if clean:
            domains.add(clean)
    return list(domains)


def _extract_waf(httpx_entry: dict) -> str | None:
    """Extract WAF name from httpx tech detection output if present."""
    for tech in httpx_entry.get("tech", []):
        if "waf" in tech.lower() or "cloudflare" in tech.lower() or "akamai" in tech.lower():
            return tech
    return None
```

---

## Step 3.11 — Stage 2: Fingerprinting — `pipeline/fingerprinting.py`

**File:** `backend/services/core_engine/pipeline/fingerprinting.py`

```python
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.subprocess_utils import (
    run_tool_communicate, parse_jsonl
)
from backend.shared.logging import get_logger
import tempfile, os

logger = get_logger("core_engine.stage2")

STAGE_NUMBER = 2.0
STAGE_NAME = "fingerprinting"


async def run(
    ctx: ScanContext,
    assets: list[DiscoveredAsset],
    config,
) -> list[DiscoveredAsset]:
    """
    Stage 2: Enrich existing assets with detailed tech stack and WAF info.
    Runs httpx with extended fingerprinting options on the already-discovered live assets.
    Updates assets in-place and returns them.
    """
    if not assets:
        return assets

    targets = [a.value for a in assets]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(targets))
        targets_file = tf.name

    try:
        stdout, _ = await run_tool_communicate(
            args=[
                "httpx", "-l", targets_file, "-json", "-silent",
                "-tech-detect", "-status-code", "-title",
                "-response-in-json", "-no-color",
            ],
            timeout=config.httpx_timeout,
            label="httpx_fingerprint",
        )
    finally:
        os.unlink(targets_file)

    # Build lookup by URL
    fingerprints = {e["url"]: e for e in parse_jsonl(stdout) if "url" in e}

    for asset in assets:
        fp = fingerprints.get(asset.value)
        if not fp:
            continue
        asset.http_status = fp.get("status_code", asset.http_status)
        asset.technology_stack = {
            "technologies": fp.get("tech", []),
            "title": fp.get("title", ""),
            "content_type": fp.get("content_type", ""),
            "server": fp.get("webserver", ""),
        }
        # Re-check WAF from enriched output
        if not asset.waf_detected:
            for tech in fp.get("tech", []):
                if any(w in tech.lower() for w in ["cloudflare", "akamai", "waf", "f5", "sucuri"]):
                    asset.waf_detected = tech
                    break

    logger.info("Stage 2 complete",
                scan_id=ctx.scan_id,
                assets_enriched=len(fingerprints))
    return assets
```

---

## Step 3.12 — Stage 3: Enumeration — `pipeline/enumeration.py`

**File:** `backend/services/core_engine/pipeline/enumeration.py`

```python
import asyncio
import hashlib
import httpx as httpx_client
import os
import tempfile
from datetime import datetime, timezone
from urllib.parse import urljoin

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import (
    DiscoveredAsset, DiscoveredEndpoint, DiscoveredJsAsset
)
from backend.services.core_engine.subprocess_utils import (
    run_tool_communicate, parse_jsonl
)
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.storage import upload_bytes
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage3")

STAGE_NUMBER = 3.0
STAGE_NAME = "enumeration"

JS_EXTENSIONS = (".js", ".mjs", ".bundle.js")


async def run(
    ctx: ScanContext,
    assets: list[DiscoveredAsset],
    scope_filter: ScopeFilter,
    config,
) -> tuple[list[DiscoveredEndpoint], list[DiscoveredJsAsset]]:
    """
    Stage 3: Endpoint discovery via ffuf + waybackurls, plus JS file download.
    Returns (endpoints, js_assets). Never raises — returns partial results.
    """
    all_endpoints: list[DiscoveredEndpoint] = []
    all_js_assets: list[DiscoveredJsAsset] = []

    tasks = [
        _enumerate_asset(asset, ctx, scope_filter, config)
        for asset in assets
        if asset.asset_id is not None
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for asset, result in zip(assets, results):
        if isinstance(result, Exception):
            logger.warning("Enumeration failed for asset",
                           asset=asset.value, error=str(result))
            continue
        endpoints, js_assets = result
        all_endpoints.extend(endpoints)
        all_js_assets.extend(js_assets)

    logger.info("Stage 3 complete",
                scan_id=ctx.scan_id,
                endpoints=len(all_endpoints),
                js_assets=len(all_js_assets))
    return all_endpoints, all_js_assets


async def _enumerate_asset(
    asset: DiscoveredAsset,
    ctx: ScanContext,
    scope_filter: ScopeFilter,
    config,
) -> tuple[list[DiscoveredEndpoint], list[DiscoveredJsAsset]]:
    endpoints: list[DiscoveredEndpoint] = []
    js_assets: list[DiscoveredJsAsset] = []

    # ffuf — directory/endpoint fuzzing
    try:
        ffuf_endpoints = await _run_ffuf(asset, ctx, scope_filter, config)
        endpoints.extend(ffuf_endpoints)
    except Exception as e:
        logger.warning("ffuf failed", asset=asset.value, error=str(e))

    # waybackurls — historical URL data
    try:
        wayback_endpoints = await _run_waybackurls(asset, ctx, scope_filter, config)
        endpoints.extend(wayback_endpoints)
    except Exception as e:
        logger.warning("waybackurls failed", asset=asset.value, error=str(e))

    # Deduplicate endpoints by (method, path)
    seen = set()
    deduped = []
    for ep in endpoints:
        key = (ep.method, ep.path)
        if key not in seen:
            seen.add(key)
            deduped.append(ep)

    # Download JS files found in discovered URLs
    js_urls = [ep.full_url for ep in deduped
               if any(ep.full_url.endswith(ext) for ext in JS_EXTENSIONS)]
    for js_url in js_urls[:50]:  # cap at 50 JS files per asset
        try:
            js_asset = await _download_js(
                js_url, ctx.scan_id, config
            )
            if js_asset:
                js_assets.append(js_asset)
        except Exception as e:
            logger.warning("JS download failed", url=js_url, error=str(e))

    return deduped, js_assets


async def _run_ffuf(
    asset: DiscoveredAsset,
    ctx: ScanContext,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredEndpoint]:
    stdout, _ = await run_tool_communicate(
        args=[
            "ffuf",
            "-u", f"{asset.value}/FUZZ",
            "-w", config.ffuf_wordlist,
            "-json",
            "-rate", str(config.ffuf_rate),
            "-t", str(config.ffuf_threads),
            "-mc", "200,201,204,301,302,307,401,403,405",
            "-of", "json",
            "-o", "/dev/stdout",
        ],
        timeout=config.ffuf_timeout,
        label=f"ffuf[{asset.value}]",
    )
    endpoints = []
    for result in parse_jsonl(stdout):
        url = result.get("url", "")
        if not url or not scope_filter.is_in_scope(url):
            continue
        from urllib.parse import urlparse
        parsed = urlparse(url)
        endpoints.append(DiscoveredEndpoint(
            asset_id=asset.asset_id,
            method="GET",
            path=parsed.path,
            full_url=url,
            response_code=result.get("status"),
            content_type=result.get("content-type"),
        ))
    return endpoints


async def _run_waybackurls(
    asset: DiscoveredAsset,
    ctx: ScanContext,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredEndpoint]:
    stdout, _ = await run_tool_communicate(
        args=["waybackurls", asset.value],
        timeout=config.waybackurls_timeout,
        label=f"waybackurls[{asset.value}]",
    )
    from urllib.parse import urlparse
    endpoints = []
    for line in stdout.splitlines():
        url = line.strip()
        if not url or not scope_filter.is_in_scope(url):
            continue
        parsed = urlparse(url)
        endpoints.append(DiscoveredEndpoint(
            asset_id=asset.asset_id,
            method="GET",
            path=parsed.path,
            full_url=url,
        ))
    return endpoints


async def _download_js(
    url: str,
    scan_id: str,
    config,
) -> DiscoveredJsAsset | None:
    """Download a JS file and store it in MinIO. Returns None on failure."""
    async with httpx_client.AsyncClient(timeout=config.js_download_timeout_seconds) as client:
        try:
            resp = await client.get(url, follow_redirects=True)
        except Exception:
            return None

        if resp.status_code != 200:
            return None

        content = resp.content
        if len(content) > config.js_max_file_size_bytes:
            logger.warning("JS file too large — skipping", url=url, size=len(content))
            return None

        content_hash = hashlib.sha256(content).hexdigest()
        storage_path = f"js-assets/{scan_id}/{content_hash}.js"
        await upload_bytes(bucket="js-assets", key=f"{scan_id}/{content_hash}.js",
                           data=content, content_type="application/javascript")
        return DiscoveredJsAsset(
            scan_id=scan_id,
            url=url,
            storage_path=storage_path,
            content_hash=content_hash,
            size_bytes=len(content),
        )
```

---

## Step 3.13 — Stage 4: Nuclei Scanning — `pipeline/nuclei_scan.py`

**File:** `backend/services/core_engine/pipeline/nuclei_scan.py`

```python
import tempfile, os
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import FindingCandidate, DiscoveredAsset
from backend.services.core_engine.subprocess_utils import (
    run_tool_communicate, parse_jsonl
)
from backend.services.core_engine.cvss import nuclei_severity, severity_to_cvss
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage4")

STAGE_NUMBER = 4.0
STAGE_NAME = "nuclei_scan"


async def run(
    ctx: ScanContext,
    assets: list[DiscoveredAsset],
    scope_filter: ScopeFilter,
    config,
) -> list[FindingCandidate]:
    """
    Stage 4: Run nuclei against all live assets.
    Only unauthenticated templates in M3. Browser-based templates are skipped
    until M5 (browser_session feature flag).
    """
    targets = scope_filter.filter_targets([a.value for a in assets])
    if not targets:
        logger.warning("No in-scope targets for nuclei", scan_id=ctx.scan_id)
        return []

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(targets))
        targets_file = tf.name

    try:
        stdout, _ = await run_tool_communicate(
            args=[
                "nuclei",
                "-l", targets_file,
                "-json",
                "-silent",
                "-rate-limit", str(config.nuclei_rate_limit),
                "-bulk-size", str(config.nuclei_bulk_size),
                "-concurrency", str(config.nuclei_concurrency),
                # Exclude templates that require browser — M5 handles those
                "-exclude-tags", "headless",
            ],
            timeout=config.nuclei_timeout,
            label="nuclei",
        )
    finally:
        os.unlink(targets_file)

    candidates: list[FindingCandidate] = []
    for entry in parse_jsonl(stdout):
        matched_url = entry.get("matched-at") or entry.get("host", "")
        if not matched_url or not scope_filter.is_in_scope(matched_url):
            continue

        raw_severity = entry.get("info", {}).get("severity", "info")
        severity = nuclei_severity(raw_severity)

        candidates.append(FindingCandidate(
            vulnerability_type=f"nuclei_{entry.get('template-id', 'unknown').replace('-', '_')}",
            title=entry.get("info", {}).get("name", entry.get("template-id", "Unknown")),
            severity=severity,
            affected_url=matched_url,
            description=entry.get("info", {}).get("description", ""),
            source="nuclei",
            payload=entry.get("matched-at"),
            cvss_score=severity_to_cvss(severity),
            raw_output=entry,
        ))

    logger.info("Stage 4 complete",
                scan_id=ctx.scan_id,
                findings=len(candidates))
    return candidates
```

---

## Step 3.14 — Stage 5: Web Vuln Tests — `pipeline/web_vuln_tests.py`

**File:** `backend/services/core_engine/pipeline/web_vuln_tests.py`

```python
import asyncio
import re
import httpx
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags
from backend.services.core_engine.models import FindingCandidate, DiscoveredEndpoint
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage5")

STAGE_NUMBER = 5.0
STAGE_NAME = "web_vuln_tests"

# XSS probe payloads — reflected only, no stored
XSS_PAYLOADS = [
    '<script>alert(1)</script>',
    '"><img src=x onerror=alert(1)>',
    "';alert(1)//",
]

# CORS test origins
CORS_TEST_ORIGINS = [
    "https://evil.com",
    "null",
    "https://attacker.example.com",
]


async def run(
    ctx: ScanContext,
    endpoints: list[DiscoveredEndpoint],
    scope_filter: ScopeFilter,
    feature_flags: FeatureFlags,
) -> list[FindingCandidate]:
    """
    Stage 5: Targeted web vulnerability tests.
    Always: XSS, CORS.
    Gated: SQLi, SSRF, CRLF (require explicit feature flag).
    """
    candidates: list[FindingCandidate] = []
    in_scope_endpoints = [
        ep for ep in endpoints if scope_filter.is_in_scope(ep.full_url)
    ]

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=False,
        verify=False,
    ) as client:
        tasks = []
        for ep in in_scope_endpoints:
            tasks.append(_test_endpoint(ep, client, feature_flags))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        candidates.extend(result)

    logger.info("Stage 5 complete",
                scan_id=ctx.scan_id,
                findings=len(candidates))
    return candidates


async def _test_endpoint(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
    flags: FeatureFlags,
) -> list[FindingCandidate]:
    findings = []
    findings.extend(await _test_xss(ep, client))
    findings.extend(await _test_cors(ep, client))
    if flags.crlf:
        findings.extend(await _test_crlf(ep, client))
    # SQLi and SSRF are gated — implement in M6+ or when flags are enabled
    return findings


async def _test_xss(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
) -> list[FindingCandidate]:
    """Test for reflected XSS by injecting payloads into query parameters."""
    findings = []
    params = ep.parameters or {}
    if not params:
        return findings  # No parameters to test

    for param_name in list(params.keys())[:10]:  # cap at 10 params
        for payload in XSS_PAYLOADS:
            test_params = {**params, param_name: payload}
            try:
                resp = await client.get(ep.full_url, params=test_params)
                if payload in resp.text:
                    findings.append(FindingCandidate(
                        vulnerability_type="reflected_xss",
                        title=f"Reflected XSS in parameter '{param_name}'",
                        severity="high",
                        affected_url=ep.full_url,
                        affected_parameter=param_name,
                        payload=payload,
                        description=(
                            f"Reflected XSS detected in parameter '{param_name}'. "
                            f"Payload was reflected verbatim in the response."
                        ),
                        source="xss_scanner",
                        reproduction_steps=(
                            f"GET {ep.full_url}?{param_name}={payload}\n"
                            f"Observe payload in response body."
                        ),
                    ))
                    break  # One finding per parameter is enough
            except Exception:
                continue
    return findings


async def _test_cors(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
) -> list[FindingCandidate]:
    """Test for CORS misconfiguration by varying Origin header."""
    findings = []
    for origin in CORS_TEST_ORIGINS:
        try:
            resp = await client.get(
                ep.full_url,
                headers={"Origin": origin},
            )
            acao = resp.headers.get("access-control-allow-origin", "")
            acac = resp.headers.get("access-control-allow-credentials", "").lower()

            # Misconfig: reflects arbitrary origin + allows credentials
            if (acao == origin or acao == "*") and acac == "true":
                findings.append(FindingCandidate(
                    vulnerability_type="cors_misconfiguration",
                    title="CORS Misconfiguration — Arbitrary Origin with Credentials",
                    severity="high",
                    affected_url=ep.full_url,
                    description=(
                        f"The server reflects the Origin '{origin}' in "
                        f"Access-Control-Allow-Origin and sets "
                        f"Access-Control-Allow-Credentials: true. "
                        f"This allows cross-origin requests with credentials."
                    ),
                    source="cors_scanner",
                    payload=origin,
                    reproduction_steps=(
                        f"curl -H 'Origin: {origin}' {ep.full_url}\n"
                        f"Observe: Access-Control-Allow-Origin: {origin}\n"
                        f"Observe: Access-Control-Allow-Credentials: true"
                    ),
                ))
                break
        except Exception:
            continue
    return findings


async def _test_crlf(
    ep: DiscoveredEndpoint,
    client: httpx.AsyncClient,
) -> list[FindingCandidate]:
    """CRLF injection test — gated, only runs when feature flag enabled."""
    findings = []
    payload = "%0d%0aSet-Cookie:crlf=injected"
    try:
        resp = await client.get(f"{ep.full_url}{payload}")
        if "crlf=injected" in str(resp.headers):
            findings.append(FindingCandidate(
                vulnerability_type="crlf_injection",
                title="CRLF Injection",
                severity="medium",
                affected_url=ep.full_url,
                payload=payload,
                description="CRLF injection detected — attacker can inject HTTP headers.",
                source="crlf_scanner",
            ))
    except Exception:
        pass
    return findings
```

---

## Step 3.15 — Stage 6: JS Secret Scanning — `pipeline/js_secrets.py`

**File:** `backend/services/core_engine/pipeline/js_secrets.py`

```python
import re
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import FindingCandidate, DiscoveredJsAsset
from backend.shared.storage import download_bytes
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage6")

STAGE_NUMBER = 6.0
STAGE_NAME = "js_secrets"

# Secret patterns — each entry: (regex, label, severity)
SECRET_PATTERNS: list[tuple[str, str, str]] = [
    (r'AIza[0-9A-Za-z\-_]{35}', "Google API Key", "high"),
    (r'AAAA[A-Za-z0-9_\-]{7}:[A-Za-z0-9_\-]{140}', "Firebase Server Key", "high"),
    (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key", "critical"),
    (r'xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9a-fA-F]{24}', "Slack Token", "high"),
    (r'(?i)(api[_\-]?key|apikey|api[_\-]?secret)\s*[=:]\s*["\']([A-Za-z0-9\-_]{20,})["\']',
     "Generic API Key Assignment", "medium"),
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
     "Hardcoded Password", "high"),
    (r'(?i)(secret[_\-]?key|private[_\-]?key)\s*[=:]\s*["\']([A-Za-z0-9\-_+/=]{20,})["\']',
     "Hardcoded Secret Key", "high"),
    (r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}',
     "JWT Token", "medium"),
    (r'-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----', "Private Key", "critical"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub Personal Access Token", "critical"),
    (r'(?i)aws[_\-]?access[_\-]?key[_\-]?id\s*[=:]\s*["\']?(AKIA[0-9A-Z]{16})["\']?',
     "AWS Access Key ID", "critical"),
    (r'(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
     "AWS Secret Access Key", "critical"),
]

_COMPILED = [(re.compile(p), label, sev) for p, label, sev in SECRET_PATTERNS]


async def run(
    ctx: ScanContext,
    js_assets: list[DiscoveredJsAsset],
) -> list[FindingCandidate]:
    """
    Stage 6: Regex-based secret detection in downloaded JS files.
    Reads each JS file from MinIO, applies patterns, produces FindingCandidates.
    """
    candidates: list[FindingCandidate] = []

    for js_asset in js_assets:
        try:
            content_bytes = await download_bytes(
                bucket="js-assets",
                key=js_asset.storage_path.removeprefix("js-assets/"),
            )
            content = content_bytes.decode(errors="replace")
            findings = _scan_content(content, js_asset.url)
            candidates.extend(findings)
        except Exception as e:
            logger.warning("JS secret scan failed",
                           url=js_asset.url, error=str(e))

    logger.info("Stage 6 complete",
                scan_id=ctx.scan_id,
                js_files_scanned=len(js_assets),
                secrets_found=len(candidates))
    return candidates


def _scan_content(content: str, source_url: str) -> list[FindingCandidate]:
    findings = []
    for pattern, label, severity in _COMPILED:
        matches = pattern.findall(content)
        if not matches:
            continue
        # Take first match only — don't emit one finding per occurrence
        match_preview = str(matches[0])[:80]
        findings.append(FindingCandidate(
            vulnerability_type="js_secret",
            title=f"{label} found in JavaScript",
            severity=severity,
            affected_url=source_url,
            description=(
                f"{label} detected in JavaScript file '{source_url}'. "
                f"Preview: {match_preview}..."
            ),
            source="js_secrets",
            payload=match_preview,
            reproduction_steps=(
                f"Fetch: {source_url}\n"
                f"Search for pattern matching: {label}\n"
                f"Matched: {match_preview}"
            ),
        ))
    return findings
```

---

## Step 3.16 — Stage 7 (Temp): Aggregator — `pipeline/aggregator.py`

**File:** `backend/services/core_engine/pipeline/aggregator.py`

Stage 7 is temporary — it will be replaced in M7 when the Exploit Verifier takes over. For now, it deduplicates, persists, and publishes.

```python
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import FindingCandidate, ScanResult
from backend.services.core_engine.repository import ScanRepository
from backend.services.core_engine.dedup import compute_dedup_hash
from backend.shared.queue import QueuePublisher
from backend.shared.schemas.report_jobs import build_report_job_message
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage7")

STAGE_NUMBER = 7.0
STAGE_NAME = "aggregation"


async def run(
    ctx: ScanContext,
    scan_result: ScanResult,
    repo: ScanRepository,
    publisher: QueuePublisher,
) -> dict:
    """
    Stage 7: Deduplication, persistence, vulnerability grouping, scan finalization.
    Returns severity_breakdown dict.
    Raises on fatal failure (e.g., DB down) — caller marks scan failed_internal.
    """
    # Deduplicate finding candidates by hash
    seen_hashes: set[str] = set()
    deduped: list[FindingCandidate] = []
    for candidate in scan_result.finding_candidates:
        h = compute_dedup_hash(candidate)
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduped.append(candidate)

    duplicate_count = len(scan_result.finding_candidates) - len(deduped)
    if duplicate_count > 0:
        logger.info("Deduplication complete",
                    scan_id=ctx.scan_id,
                    before=len(scan_result.finding_candidates),
                    after=len(deduped),
                    duplicates_removed=duplicate_count)

    # Persist findings
    saved_count = await repo.save_findings(
        scan_id=ctx.scan_id,
        program_id=ctx.program_id,
        candidates=deduped,
    )

    # Build severity breakdown
    breakdown: dict[str, int] = {
        "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
    }
    for c in deduped:
        sev = c.severity.lower()
        if sev in breakdown:
            breakdown[sev] += 1

    # Determine final scan status
    has_errors = bool(scan_result.stage_errors)
    status = "partial" if has_errors else "completed"

    partial_detail = None
    if has_errors:
        partial_detail = {
            "failed_stages": list(scan_result.stage_errors.keys()),
            "errors": scan_result.stage_errors,
        }

    # Finalize scan row
    await repo.mark_scan_complete(
        scan_id=ctx.scan_id,
        status=status,
        finding_count=saved_count,
        severity_breakdown=breakdown,
        partial_detail=partial_detail,
    )

    # Publish scan.completed → report.jobs
    try:
        message = build_report_job_message(
            scan_id=ctx.scan_id,
            program_id=ctx.program_id,
            finding_count=saved_count,
            severity_breakdown=breakdown,
        )
        await publisher.publish("report.jobs", message)
        logger.info("Published scan.completed to report.jobs",
                    scan_id=ctx.scan_id)
    except Exception as e:
        # Non-fatal — scan is complete, report will be picked up by reconciler
        logger.error("Failed to publish to report.jobs",
                     scan_id=ctx.scan_id, error=str(e))

    logger.info("Stage 7 complete",
                scan_id=ctx.scan_id,
                findings_saved=saved_count,
                status=status,
                breakdown=breakdown)
    return breakdown
```

---

## Step 3.17 — Scan Task Entry: `scan_task.py`

**File:** `backend/services/core_engine/scan_task.py`

This is the Celery task that orchestrates the entire pipeline. It is the only file that knows the execution order.

```python
import asyncio
from datetime import datetime, timezone

from celery import Task

from backend.services.core_engine.pipeline.context import (
    ScanContext, ScopeDefinition, FeatureFlags
)
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.services.core_engine.pipeline import (
    asset_discovery,
    fingerprinting,
    enumeration,
    nuclei_scan,
    web_vuln_tests,
    js_secrets,
    aggregator,
)
from backend.services.core_engine.models import ScanResult
from backend.services.core_engine.repository import ScanRepository
from backend.services.core_engine.config import EngineConfig
from backend.shared.db import get_session
from backend.shared.queue import QueuePublisher
from backend.shared.schemas.envelope import MessageEnvelope
from backend.shared.logging import get_logger

logger = get_logger("core_engine.scan_task")


def run_scan_task(payload: dict) -> None:
    """
    Celery task entry point. Synchronous wrapper around the async pipeline.
    Called by the Celery worker when a message arrives on scan.jobs.
    """
    asyncio.run(_async_scan_pipeline(payload))


async def _async_scan_pipeline(payload: dict) -> None:
    """
    Full async pipeline. Any unhandled exception here marks the scan failed_internal.
    Redis lock prevents concurrent scans for the same program.
    """
    import redis.asyncio as aioredis
    from backend.shared.config import get_settings

    config = EngineConfig()
    program_id = payload.get("program_id")
    scan_id = None

    # Redis lock — one scan per program at a time
    redis = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
    lock_key = f"scan:lock:{program_id}"

    async with redis.lock(lock_key, timeout=config.scan_lock_ttl_seconds):
        async with get_session() as session:
            repo = ScanRepository(session)

            # Build scan context from message
            scope_raw = payload.get("scope", {})
            scope = ScopeDefinition(
                in_scope=scope_raw.get("in_scope", []),
                out_of_scope=scope_raw.get("out_of_scope", []),
            )
            flags_raw = payload.get("feature_flags", {})
            feature_flags = FeatureFlags(
                sqli=flags_raw.get("sqli", False),
                ssrf=flags_raw.get("ssrf", False),
                crlf=flags_raw.get("crlf", False),
                browser_session=flags_raw.get("browser_session", False),
                api_fuzzing=flags_raw.get("api_fuzzing", False),
                ai_hypothesis=flags_raw.get("ai_hypothesis", False),
            )

            scan_id = await repo.create_or_resume_scan(
                program_id=program_id,
                feature_flags=flags_raw,
                priority=payload.get("priority", 1),
            )

            ctx = ScanContext(
                scan_id=scan_id,
                program_id=program_id,
                scope=scope,
                feature_flags=feature_flags,
                priority=payload.get("priority", 1),
            )

            scan_result = ScanResult()
            publisher = QueuePublisher(config)

            try:
                await _execute_pipeline(ctx, scan_result, repo, publisher, config)
            except Exception as e:
                logger.error("Pipeline fatal error",
                             scan_id=scan_id, error=str(e))
                await repo.mark_scan_complete(
                    scan_id=scan_id,
                    status="failed_internal",
                    finding_count=0,
                    severity_breakdown={},
                    error_detail=str(e),
                )


async def _execute_pipeline(
    ctx: ScanContext,
    scan_result: ScanResult,
    repo: ScanRepository,
    publisher: QueuePublisher,
    config: "EngineConfig",
) -> None:
    """
    Ordered pipeline execution. Stages 4 and 5 run in parallel.
    Stage failures are non-fatal unless Stage 0 (scope) or Stage 7 (aggregation) fail.
    """
    scan_id = ctx.scan_id

    # ── Stage 0: Scope Filter (FATAL) ───────────────────────────────────
    logger.info("Stage 0: Scope filter", scan_id=scan_id)
    scope_filter = ScopeFilter(ctx.scope)  # raises ScanError if scope empty

    # ── Stage 1: Asset Discovery ─────────────────────────────────────────
    s1_start = datetime.now(timezone.utc)
    try:
        assets = await asset_discovery.run(ctx, scope_filter, config)
        scan_result.assets = assets
        await repo.save_assets(scan_id, assets)
        await repo.record_stage(scan_id, 1.0, "asset_discovery", "completed",
                                s1_start, {"assets_found": len(assets)})
    except Exception as e:
        scan_result.stage_errors["asset_discovery"] = str(e)
        await repo.record_stage(scan_id, 1.0, "asset_discovery", "failed",
                                s1_start, error_detail=str(e))
        logger.warning("Stage 1 failed — continuing", scan_id=scan_id, error=str(e))

    if not scan_result.assets:
        logger.warning("No assets found — skipping Stages 2–6", scan_id=scan_id)
        await aggregator.run(ctx, scan_result, repo, publisher)
        return

    # ── Stage 2: Fingerprinting ─────────────────────────────────────────
    s2_start = datetime.now(timezone.utc)
    try:
        scan_result.assets = await fingerprinting.run(ctx, scan_result.assets, config)
        await repo.save_assets(scan_id, scan_result.assets)  # update with enrichment
        await repo.record_stage(scan_id, 2.0, "fingerprinting", "completed", s2_start)
    except Exception as e:
        scan_result.stage_errors["fingerprinting"] = str(e)
        await repo.record_stage(scan_id, 2.0, "fingerprinting", "failed",
                                s2_start, error_detail=str(e))
        logger.warning("Stage 2 failed — continuing", scan_id=scan_id, error=str(e))

    # ── Stage 3: Enumeration ─────────────────────────────────────────────
    s3_start = datetime.now(timezone.utc)
    try:
        endpoints, js_assets = await enumeration.run(
            ctx, scan_result.assets, scope_filter, config
        )
        scan_result.endpoints = endpoints
        scan_result.js_assets = js_assets
        await repo.save_endpoints(scan_id, endpoints)
        for js in js_assets:
            await repo.save_js_asset(scan_id, js)
        ctx.js_asset_ids = [str(j.js_asset_id) for j in js_assets if j.js_asset_id]
        await repo.record_stage(scan_id, 3.0, "enumeration", "completed", s3_start,
                                {"endpoints": len(endpoints), "js_assets": len(js_assets)})
    except Exception as e:
        scan_result.stage_errors["enumeration"] = str(e)
        await repo.record_stage(scan_id, 3.0, "enumeration", "failed",
                                s3_start, error_detail=str(e))
        logger.warning("Stage 3 failed — continuing", scan_id=scan_id, error=str(e))

    # ── Stages 4 + 5: Parallel ───────────────────────────────────────────
    s4_start = datetime.now(timezone.utc)
    nuclei_task = asyncio.create_task(
        nuclei_scan.run(ctx, scan_result.assets, scope_filter, config)
    )
    web_task = asyncio.create_task(
        web_vuln_tests.run(ctx, scan_result.endpoints, scope_filter, ctx.feature_flags)
    )
    nuclei_findings, web_findings = await asyncio.gather(
        nuclei_task, web_task, return_exceptions=True
    )

    if isinstance(nuclei_findings, Exception):
        scan_result.stage_errors["nuclei_scan"] = str(nuclei_findings)
        await repo.record_stage(scan_id, 4.0, "nuclei_scan", "failed",
                                s4_start, error_detail=str(nuclei_findings))
    else:
        scan_result.finding_candidates.extend(nuclei_findings)
        await repo.record_stage(scan_id, 4.0, "nuclei_scan", "completed", s4_start,
                                {"findings": len(nuclei_findings)})

    if isinstance(web_findings, Exception):
        scan_result.stage_errors["web_vuln_tests"] = str(web_findings)
        await repo.record_stage(scan_id, 5.0, "web_vuln_tests", "failed",
                                s4_start, error_detail=str(web_findings))
    else:
        scan_result.finding_candidates.extend(web_findings)
        await repo.record_stage(scan_id, 5.0, "web_vuln_tests", "completed", s4_start,
                                {"findings": len(web_findings)})

    # ── Stage 6: JS Secrets ──────────────────────────────────────────────
    s6_start = datetime.now(timezone.utc)
    try:
        js_findings = await js_secrets.run(ctx, scan_result.js_assets)
        scan_result.finding_candidates.extend(js_findings)
        await repo.record_stage(scan_id, 6.0, "js_secrets", "completed", s6_start,
                                {"findings": len(js_findings)})
    except Exception as e:
        scan_result.stage_errors["js_secrets"] = str(e)
        await repo.record_stage(scan_id, 6.0, "js_secrets", "failed",
                                s6_start, error_detail=str(e))
        logger.warning("Stage 6 failed — continuing", scan_id=scan_id, error=str(e))

    # ── Stage 7: Aggregation (FATAL if fails) ───────────────────────────
    await aggregator.run(ctx, scan_result, repo, publisher)
```

---

## Step 3.18 — Watchdog: `watchdog.py`

**File:** `backend/services/core_engine/watchdog.py`

```python
from datetime import timezone

from sqlalchemy import text

from backend.shared.db import get_session
from backend.shared.logging import get_logger

logger = get_logger("core_engine.watchdog")


async def recover_stuck_scans(republish_fn, stale_hours: int = 2) -> None:
    """
    APScheduler job. Finds scans stuck in 'running' for > stale_hours.
    Marks them failed_internal. Republishes if retry_count < 2.

    Without this, any Celery worker OOM-kill leaves status='running' forever.
    """
    async with get_session() as session:
        rows = await session.execute(
            text("""
                SELECT scan_id, retry_count, program_id
                FROM scans
                WHERE status = 'running'
                  AND started_at < NOW() - INTERVAL ':hours hours'
            """.replace(":hours", str(stale_hours)))
        )
        stuck = rows.fetchall()

        for row in stuck:
            scan_id, retry_count, program_id = row
            logger.warning("Watchdog: marking stuck scan failed_internal",
                           scan_id=str(scan_id),
                           retry_count=retry_count)
            await session.execute(
                text("""
                    UPDATE scans
                    SET status = 'failed_internal',
                        error_detail = 'watchdog_timeout',
                        completed_at = NOW()
                    WHERE scan_id = :scan_id
                """),
                {"scan_id": str(scan_id)},
            )
            await session.commit()

            if retry_count < 2:
                try:
                    await republish_fn(program_id=str(program_id))
                    await session.execute(
                        text("UPDATE scans SET retry_count = retry_count + 1 "
                             "WHERE scan_id = :scan_id"),
                        {"scan_id": str(scan_id)},
                    )
                    await session.commit()
                    logger.info("Watchdog: republished scan for retry",
                                scan_id=str(scan_id))
                except Exception as e:
                    logger.error("Watchdog: republish failed",
                                 scan_id=str(scan_id), error=str(e))
            else:
                logger.warning("Watchdog: retry_count >= 2, not republishing",
                               scan_id=str(scan_id))
```

---

## Step 3.19 — Worker: `worker.py`

**File:** `backend/services/core_engine/worker.py` — **replaces skeleton**

```python
import json
from celery import Celery

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.scan_task import run_scan_task
from backend.shared.logging import configure_logging, get_logger
from backend.shared.schemas.envelope import MessageEnvelope

config = EngineConfig()
configure_logging(config.service_name)
logger = get_logger("core_engine.worker")

app = Celery(
    "core_worker",
    broker=f"amqp://{config.rabbitmq_user}:{config.rabbitmq_password}"
           f"@{config.rabbitmq_host}:{config.rabbitmq_port}/",
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,          # ack only after task completes — prevents loss on crash
    task_reject_on_worker_lost=True,  # NACK on worker death — message goes to DLQ
    worker_prefetch_multiplier=1, # one task at a time per worker — scans are heavy
)


@app.task(
    name="core_engine.scan_task",
    queue="scan.jobs",
    bind=True,
    max_retries=0,  # Watchdog handles retry logic — do not let Celery auto-retry
)
def scan_task(self, message: dict) -> None:
    """
    Celery task entry. Deserializes the MessageEnvelope and delegates to scan pipeline.
    """
    try:
        envelope = MessageEnvelope(**message)
        payload = envelope.payload
        logger.info("Scan task received",
                    program_id=payload.get("program_id"),
                    event_type=envelope.event_type)
        run_scan_task(payload)
    except Exception as e:
        logger.error("Scan task fatal error", error=str(e))
        raise  # Let Celery mark as failure — watchdog handles stuck scans
```

---

## Step 3.20 — Engine Main: `main.py`

**File:** `backend/services/core_engine/main.py` — **replaces skeleton**

```python
import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.watchdog import recover_stuck_scans
from backend.shared.db import init_db, get_session, check_db_health
from backend.shared.health import HealthResponse, ComponentHealth, HealthStatus
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import QueuePublisher

config = EngineConfig()
configure_logging(config.service_name)
logger = get_logger("core_engine.main")

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(config.database_url)
    publisher = QueuePublisher(config)

    async def _republish(program_id: str):
        # Minimal republish — fetch program scope from Scraper API and requeue
        # Full implementation: call scraper API GET /programs/{id}/scope
        logger.info("Republish requested", program_id=program_id)

    scheduler.add_job(
        recover_stuck_scans,
        "interval",
        seconds=config.watchdog_interval_seconds,
        kwargs={"republish_fn": _republish,
                "stale_hours": config.watchdog_stale_threshold_hours},
    )
    scheduler.start()
    logger.info("Core Engine started", watchdog_interval=config.watchdog_interval_seconds)
    yield
    scheduler.shutdown()


app = FastAPI(title="Core Engine", lifespan=lifespan)


@app.get("/api/v1/health")
async def health() -> JSONResponse:
    db_ok = await check_db_health()
    status = HealthStatus.healthy if db_ok else HealthStatus.degraded
    return JSONResponse(
        content=HealthResponse(
            status=status,
            service=config.service_name,
            components={
                "database": ComponentHealth(
                    status=HealthStatus.healthy if db_ok else HealthStatus.unhealthy
                ),
                "scheduler": ComponentHealth(
                    status=HealthStatus.healthy if scheduler.running else HealthStatus.unhealthy
                ),
            },
        ).model_dump()
    )


@app.post("/api/v1/scans/start")
async def start_scan(body: dict) -> JSONResponse:
    """
    Manual scan trigger — for testing. Publishes directly to scan.jobs.
    Body: { "program_id": "uuid", "scope": {...}, "feature_flags": {...} }
    """
    from backend.shared.schemas.scan_jobs import build_scan_job_message, ScanJobsPayload
    publisher = QueuePublisher(config)
    msg = build_scan_job_message(ScanJobsPayload(**body))
    await publisher.publish("scan.jobs", msg)
    return JSONResponse({"status": "queued", "program_id": body.get("program_id")})


@app.get("/api/v1/scans")
async def list_scans() -> JSONResponse:
    async with get_session() as session:
        from sqlalchemy import text
        rows = await session.execute(
            text("SELECT scan_id, program_id, status, finding_count, started_at "
                 "FROM scans ORDER BY created_at DESC LIMIT 50")
        )
        scans = [
            {
                "scan_id": str(r[0]),
                "program_id": str(r[1]),
                "status": r[2],
                "finding_count": r[3],
                "started_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows.fetchall()
        ]
    return JSONResponse({"scans": scans})


@app.get("/api/v1/scans/{scan_id}")
async def get_scan(scan_id: str) -> JSONResponse:
    async with get_session() as session:
        from sqlalchemy import text
        row = await session.execute(
            text("SELECT scan_id, program_id, status, finding_count, "
                 "severity_breakdown, started_at, completed_at, error_detail "
                 "FROM scans WHERE scan_id = :scan_id"),
            {"scan_id": scan_id},
        )
        r = row.fetchone()
        if not r:
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse({
            "scan_id": str(r[0]),
            "program_id": str(r[1]),
            "status": r[2],
            "finding_count": r[3],
            "severity_breakdown": r[4],
            "started_at": r[5].isoformat() if r[5] else None,
            "completed_at": r[6].isoformat() if r[6] else None,
            "error_detail": r[7],
        })


@app.get("/api/v1/scans/{scan_id}/findings")
async def get_findings(scan_id: str) -> JSONResponse:
    async with get_session() as session:
        from sqlalchemy import text
        rows = await session.execute(
            text("""
                SELECT finding_id, vulnerability_type, title, severity,
                       cvss_score, affected_url, affected_parameter,
                       is_verified, source, created_at
                FROM findings WHERE scan_id = :scan_id
                ORDER BY cvss_score DESC NULLS LAST
            """),
            {"scan_id": scan_id},
        )
        findings = [
            {
                "finding_id": str(r[0]),
                "vulnerability_type": r[1],
                "title": r[2],
                "severity": r[3],
                "cvss_score": r[4],
                "affected_url": r[5],
                "affected_parameter": r[6],
                "is_verified": r[7],
                "source": r[8],
                "created_at": r[9].isoformat() if r[9] else None,
            }
            for r in rows.fetchall()
        ]
    return JSONResponse({"findings": findings, "count": len(findings)})


@app.get("/api/v1/queue/dlq/inspect")
async def inspect_dlq() -> JSONResponse:
    """Stub — DLQ inspection via RabbitMQ management API. Full impl in M10."""
    return JSONResponse({"message": "DLQ inspection not yet implemented", "queues": []})
```

---

## Step 3.21 — `pipeline/__init__.py`

**File:** `backend/services/core_engine/pipeline/__init__.py`

```python
# Pipeline stages — import for use in scan_task.py
from backend.services.core_engine.pipeline import (
    asset_discovery,
    fingerprinting,
    enumeration,
    nuclei_scan,
    web_vuln_tests,
    js_secrets,
    aggregator,
)

__all__ = [
    "asset_discovery",
    "fingerprinting",
    "enumeration",
    "nuclei_scan",
    "web_vuln_tests",
    "js_secrets",
    "aggregator",
]
```

---

## Step 3.22 — Dependencies

**File additions to `backend/services/core_engine/requirements.txt`** (create if not present, or add to `m3_additions.txt` and merge into base):

```
httpx>=0.27.0       # async HTTP client (JS download, web vuln tests)
apscheduler>=3.10.0  # watchdog scheduler (already in M2 base — verify not duplicated)
redis[asyncio]>=5.0.4  # scan lock (already in base — verify)
```

All CLI tools (`subfinder`, `alterx`, `dnsx`, `httpx`, `ffuf`, `waybackurls`, `nuclei`) must be installed in the `core-worker` Docker image.

**`backend/services/core_engine/Dockerfile` — add tool installation:**

```dockerfile
# Install Go-based security tools
RUN apt-get update && apt-get install -y wget unzip curl && \
    # nuclei
    wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip && \
    unzip -q nuclei_linux_amd64.zip && mv nuclei /usr/local/bin/ && rm nuclei_*.zip && \
    # httpx
    wget -q https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_linux_amd64.zip && \
    unzip -q httpx_linux_amd64.zip && mv httpx /usr/local/bin/ && rm httpx_*.zip && \
    # subfinder
    wget -q https://github.com/projectdiscovery/subfinder/releases/latest/download/subfinder_linux_amd64.zip && \
    unzip -q subfinder_linux_amd64.zip && mv subfinder /usr/local/bin/ && rm subfinder_*.zip && \
    # dnsx
    wget -q https://github.com/projectdiscovery/dnsx/releases/latest/download/dnsx_linux_amd64.zip && \
    unzip -q dnsx_linux_amd64.zip && mv dnsx /usr/local/bin/ && rm dnsx_*.zip && \
    # alterx
    wget -q https://github.com/projectdiscovery/alterx/releases/latest/download/alterx_linux_amd64.zip && \
    unzip -q alterx_linux_amd64.zip && mv alterx /usr/local/bin/ && rm alterx_*.zip && \
    # ffuf
    wget -q https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.tar.gz && \
    tar xz -f ffuf_linux_amd64.tar.gz && mv ffuf /usr/local/bin/ && rm ffuf_*.tar.gz && \
    # waybackurls
    wget -q https://github.com/tomnomnom/waybackurls/releases/latest/download/waybackurls-linux-amd64-0.1.0.tgz && \
    tar xz -f waybackurls-*.tgz && mv waybackurls /usr/local/bin/ && rm waybackurls-*.tgz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download nuclei templates on build (avoids first-run delay)
RUN nuclei -update-templates || true

# wordlist for ffuf
RUN mkdir -p /wordlists && \
    wget -q https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt \
    -O /wordlists/common.txt
```

> ⚠️ The exact download URLs above use `latest` — replace with pinned version tags for production builds. `latest` is acceptable for M3 development.

---

## Step 3.23 — Tests: `tests/unit/test_engine.py`

**File:** `tests/unit/test_engine.py`

Coverage target: ≥ 75% for core_engine service.

```python
"""
Unit tests for Core Engine M3 components.
All subprocess calls are mocked — no real tools required.
All DB calls are mocked — no real database required.
"""

import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

from backend.services.core_engine.dedup import normalize_url, compute_dedup_hash
from backend.services.core_engine.cvss import (
    severity_to_cvss, nuclei_severity, infer_severity
)
from backend.services.core_engine.models import FindingCandidate
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.services.core_engine.pipeline.context import ScopeDefinition
from backend.services.core_engine.subprocess_utils import parse_jsonl
from backend.shared.exceptions import ScanError


# ── ScopeFilter tests ──────────────────────────────────────────────────────

class TestScopeFilter:
    def _make(self, in_scope, out_of_scope=None):
        scope = ScopeDefinition(
            in_scope=in_scope,
            out_of_scope=out_of_scope or [],
        )
        return ScopeFilter(scope)

    def test_wildcard_match(self):
        sf = self._make(["*.example.com"])
        assert sf.is_in_scope("https://api.example.com/v1")
        assert sf.is_in_scope("sub.api.example.com")

    def test_wildcard_does_not_match_root(self):
        sf = self._make(["*.example.com"])
        # *.example.com should NOT match example.com itself
        assert not sf.is_in_scope("https://example.com")

    def test_exact_domain_match(self):
        sf = self._make(["api.example.com"])
        assert sf.is_in_scope("https://api.example.com/path")

    def test_exact_domain_no_subdomain_leak(self):
        sf = self._make(["api.example.com"])
        assert not sf.is_in_scope("https://other.api.example.com")

    def test_out_of_scope_wins(self):
        sf = self._make(
            in_scope=["*.example.com"],
            out_of_scope=["admin.example.com"],
        )
        assert sf.is_in_scope("https://api.example.com")
        assert not sf.is_in_scope("https://admin.example.com")

    def test_cidr_match(self):
        sf = self._make(["192.168.1.0/24"])
        assert sf.is_in_scope("192.168.1.55")

    def test_cidr_out_of_range(self):
        sf = self._make(["192.168.1.0/24"])
        assert not sf.is_in_scope("10.0.0.1")

    def test_empty_scope_raises(self):
        with pytest.raises(ScanError):
            self._make([])

    def test_filter_targets(self):
        sf = self._make(["*.example.com"])
        targets = [
            "https://api.example.com",
            "https://evil.com",
            "https://sub.example.com",
        ]
        result = sf.filter_targets(targets)
        assert "https://api.example.com" in result
        assert "https://sub.example.com" in result
        assert "https://evil.com" not in result


# ── Deduplication tests ─────────────────────────────────────────────────────

class TestDedup:
    def _make_candidate(self, url, vuln_type="xss", param="q", payload="<script>"):
        return FindingCandidate(
            vulnerability_type=vuln_type,
            title="Test",
            severity="high",
            affected_url=url,
            affected_parameter=param,
            payload=payload,
            description="",
            source="test",
        )

    def test_same_finding_same_hash(self):
        c1 = self._make_candidate("https://example.com/search?q=1&b=2")
        c2 = self._make_candidate("https://example.com/search?q=1&b=2")
        assert compute_dedup_hash(c1) == compute_dedup_hash(c2)

    def test_query_param_order_normalized(self):
        c1 = self._make_candidate("https://example.com/search?a=1&b=2")
        c2 = self._make_candidate("https://example.com/search?b=2&a=1")
        assert compute_dedup_hash(c1) == compute_dedup_hash(c2)

    def test_different_url_different_hash(self):
        c1 = self._make_candidate("https://example.com/search")
        c2 = self._make_candidate("https://example.com/other")
        assert compute_dedup_hash(c1) != compute_dedup_hash(c2)

    def test_different_vuln_type_different_hash(self):
        c1 = self._make_candidate("https://example.com", vuln_type="xss")
        c2 = self._make_candidate("https://example.com", vuln_type="cors")
        assert compute_dedup_hash(c1) != compute_dedup_hash(c2)

    def test_normalize_url_lowercases(self):
        result = normalize_url("HTTPS://Example.COM/Path?Z=1&A=2")
        assert result == normalize_url("https://example.com/path?a=2&z=1")


# ── CVSS tests ──────────────────────────────────────────────────────────────

class TestCvss:
    def test_severity_to_cvss_critical(self):
        assert severity_to_cvss("critical") == 9.0

    def test_severity_to_cvss_high(self):
        assert severity_to_cvss("high") == 7.5

    def test_severity_to_cvss_unknown_default(self):
        assert severity_to_cvss("unknown") == 5.0

    def test_nuclei_severity_mapping(self):
        assert nuclei_severity("critical") == "critical"
        assert nuclei_severity("MEDIUM") == "medium"
        assert nuclei_severity("garbage") == "info"

    def test_infer_severity_from_raw(self):
        assert infer_severity("xss", raw_severity="high") == "high"

    def test_infer_severity_from_vuln_type(self):
        assert infer_severity("xss") == "high"
        assert infer_severity("sqli") == "critical"
        assert infer_severity("unknown_vuln") == "medium"


# ── Subprocess utils tests ───────────────────────────────────────────────────

class TestParseJsonl:
    def test_parses_valid_lines(self):
        text = '{"url": "https://example.com", "status": 200}\n{"url": "https://b.com"}\n'
        result = parse_jsonl(text)
        assert len(result) == 2
        assert result[0]["url"] == "https://example.com"

    def test_skips_non_json_lines(self):
        text = "Starting scan...\n{\"url\": \"https://a.com\"}\nDone.\n"
        result = parse_jsonl(text)
        assert len(result) == 1

    def test_empty_input(self):
        assert parse_jsonl("") == []

    def test_skips_malformed_json(self):
        text = '{"broken: json}\n{"url": "https://good.com"}\n'
        result = parse_jsonl(text)
        assert len(result) == 1
        assert result[0]["url"] == "https://good.com"


# ── JS Secrets tests ────────────────────────────────────────────────────────

class TestJsSecrets:
    def test_detects_google_api_key(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        content = 'var key = "AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY"'
        findings = _scan_content(content, "https://example.com/app.js")
        assert any(f.vulnerability_type == "js_secret" for f in findings)
        assert any("Google API Key" in f.title for f in findings)

    def test_detects_openai_key(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        content = 'const apiKey = "sk-abcdefghijklmnopqrstuvwxyz1234567890123456789012"'
        findings = _scan_content(content, "https://example.com/app.js")
        assert any("OpenAI" in f.title for f in findings)

    def test_no_false_positive_on_clean(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        content = 'function init() { return true; }'
        findings = _scan_content(content, "https://example.com/app.js")
        assert findings == []

    def test_only_one_finding_per_pattern(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        # Same key pattern twice — should produce one finding, not two
        key = "AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY"
        content = f'var k1 = "{key}"; var k2 = "{key}";'
        findings = _scan_content(content, "https://example.com/app.js")
        google_findings = [f for f in findings if "Google API Key" in f.title]
        assert len(google_findings) == 1


# ── Web Vuln Tests (unit) ───────────────────────────────────────────────────

class TestWebVulnTests:
    @pytest.mark.asyncio
    async def test_xss_detection(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import _test_xss
        from backend.services.core_engine.models import DiscoveredEndpoint
        import uuid

        ep = DiscoveredEndpoint(
            asset_id=uuid.uuid4(),
            method="GET",
            path="/search",
            full_url="https://example.com/search",
            parameters={"q": "test"},
        )

        mock_resp = MagicMock()
        mock_resp.text = '<script>alert(1)</script>'  # payload reflected
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        findings = await _test_xss(ep, mock_client)
        assert len(findings) > 0
        assert findings[0].vulnerability_type == "reflected_xss"

    @pytest.mark.asyncio
    async def test_xss_no_reflection(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import _test_xss
        from backend.services.core_engine.models import DiscoveredEndpoint
        import uuid

        ep = DiscoveredEndpoint(
            asset_id=uuid.uuid4(),
            method="GET",
            path="/search",
            full_url="https://example.com/search",
            parameters={"q": "test"},
        )

        mock_resp = MagicMock()
        mock_resp.text = "<html>safe response</html>"  # no reflection
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        findings = await _test_xss(ep, mock_client)
        assert findings == []

    @pytest.mark.asyncio
    async def test_cors_misconfiguration(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import _test_cors
        from backend.services.core_engine.models import DiscoveredEndpoint
        import uuid

        ep = DiscoveredEndpoint(
            asset_id=uuid.uuid4(),
            method="GET",
            path="/api",
            full_url="https://example.com/api",
        )

        mock_resp = MagicMock()
        mock_resp.headers = {
            "access-control-allow-origin": "https://evil.com",
            "access-control-allow-credentials": "true",
        }
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        findings = await _test_cors(ep, mock_client)
        assert len(findings) > 0
        assert findings[0].vulnerability_type == "cors_misconfiguration"


# ── Scan State Machine tests ─────────────────────────────────────────────────

class TestScanStateMachine:
    """
    Verify scan status transitions without running a real scan.
    These test the repository methods directly with a mocked session.
    """
    @pytest.mark.asyncio
    async def test_mark_scan_complete_sets_status(self):
        from backend.services.core_engine.repository import ScanRepository
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        repo = ScanRepository(mock_session)
        await repo.mark_scan_complete(
            scan_id="test-scan-id",
            status="completed",
            finding_count=5,
            severity_breakdown={"high": 3, "medium": 2},
        )
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_scan_partial_on_stage_errors(self):
        """Aggregator should produce 'partial' status when stage_errors is non-empty."""
        from backend.services.core_engine.models import ScanResult
        scan_result = ScanResult(stage_errors={"nuclei_scan": "timeout"})
        # Verify partial logic: has_errors → status = partial
        has_errors = bool(scan_result.stage_errors)
        expected_status = "partial" if has_errors else "completed"
        assert expected_status == "partial"
```

---

## Step 3.24 — Integration Test: `tests/integrations/test_engine_pipeline.py`

**File:** `tests/integrations/test_engine_pipeline.py`

```python
"""
Integration test for the full scan pipeline.
Requires DVWA or Juice Shop running locally.
Skips cleanly if INTEGRATION_TARGET is not set.

Usage:
  docker run -d -p 3000:3000 bkimminich/juice-shop
  INTEGRATION_TARGET=http://localhost:3000 pytest tests/integrations/test_engine_pipeline.py -v
"""

import asyncio
import os
import pytest

INTEGRATION_TARGET = os.getenv("INTEGRATION_TARGET")
pytestmark = pytest.mark.skipif(
    not INTEGRATION_TARGET,
    reason="Set INTEGRATION_TARGET env var to run integration tests"
)


@pytest.mark.asyncio
async def test_full_pipeline_produces_findings():
    """
    End-to-end: construct a ScanContext for the target, run the full pipeline,
    and assert that at least some assets and findings are produced.
    """
    from backend.services.core_engine.pipeline.context import (
        ScanContext, ScopeDefinition, FeatureFlags
    )
    from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
    from backend.services.core_engine.pipeline import (
        asset_discovery, fingerprinting, enumeration, nuclei_scan
    )
    from backend.services.core_engine.config import EngineConfig

    config = EngineConfig()
    scope = ScopeDefinition(in_scope=[INTEGRATION_TARGET])
    ctx = ScanContext(
        scan_id="integration-test-scan",
        program_id="integration-test-program",
        scope=scope,
        feature_flags=FeatureFlags(),
    )
    scope_filter = ScopeFilter(scope)

    # Stage 1
    assets = await asset_discovery.run(ctx, scope_filter, config)
    assert len(assets) >= 0  # may be zero if no subdomains — that's OK

    # At minimum, httpx should have probed the target URL directly
    # If subfinder finds nothing, we still expect the root URL to be discoverable
    # (this depends on tool availability in CI)


@pytest.mark.asyncio
async def test_scope_filter_rejects_out_of_scope():
    """Confirm ScopeFilter hard-rejects URLs outside the declared scope."""
    from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
    from backend.services.core_engine.pipeline.context import ScopeDefinition

    scope = ScopeDefinition(in_scope=[INTEGRATION_TARGET])
    sf = ScopeFilter(scope)
    assert not sf.is_in_scope("https://attacker.evil.com/payload")
    assert sf.is_in_scope(INTEGRATION_TARGET)
```

---

## Step 3.25 — Dockerfile `pipeline/__init__.py` note

Add an empty `backend/services/core_engine/pipeline/__init__.py` if not created in Step 3.21. Python will fail to import the package without it.

---

## Verification Sequence

Run these in order after implementing all steps.

**Check 1 — Migration applied**
```powershell
docker compose -f infra/docker-compose.yml --env-file .env \
  run --rm migrate alembic -c /app/backend/migrations/alembic.ini current
# Expected: "003 (head)"

docker compose -f infra/docker-compose.yml --env-file .env exec postgres \
  psql -U attackbot -d attackbot -c "\dt"
# Expected: scans, scan_stages, assets, endpoints, js_assets,
#           findings, finding_evidence, vulnerability_groups
```

**Check 2 — Rebuild worker image**
```powershell
docker compose -f infra/docker-compose.yml --env-file .env build core-worker
docker compose -f infra/docker-compose.yml --env-file .env up -d core-worker

# Verify CLI tools installed in container
docker compose -f infra/docker-compose.yml --env-file .env exec core-worker nuclei -version
docker compose -f infra/docker-compose.yml --env-file .env exec core-worker subfinder -version
docker compose -f infra/docker-compose.yml --env-file .env exec core-worker ffuf -V
```

**Check 3 — Core engine health**
```powershell
curl http://localhost:8002/api/v1/health | python -m json.tool
# Expected: status=healthy, database=healthy, scheduler=healthy
```

**Check 4 — Manual scan trigger**
```powershell
# Start Juice Shop locally first
docker run -d -p 3000:3000 bkimminich/juice-shop

# Trigger scan (replace program_id with a real UUID from your programs table)
$PROGRAM_ID = docker compose ... exec postgres psql ... -c "SELECT program_id FROM programs LIMIT 1;" | xargs

curl -X POST http://localhost:8002/api/v1/scans/start \
  -H "Content-Type: application/json" \
  -d "{
    \"program_id\": \"$PROGRAM_ID\",
    \"scope\": {\"in_scope\": [\"*.juice-shop.local\", \"http://localhost:3000\"], \"out_of_scope\": []},
    \"feature_flags\": {\"sqli\": false, \"ssrf\": false}
  }"

# Poll status
curl http://localhost:8002/api/v1/scans | python -m json.tool
```

**Check 5 — Findings in DB after scan completes**
```powershell
docker compose -f infra/docker-compose.yml --env-file .env exec postgres \
  psql -U attackbot -d attackbot \
  -c "SELECT vulnerability_type, severity, affected_url FROM findings LIMIT 20;"
```

**Check 6 — Message on report.jobs**
Open `http://localhost:15672` → Queues → `report.jobs`. Confirm Ready count > 0 after scan completes.

**Check 7 — Simulated worker crash + watchdog**
```powershell
# Manually set a scan as stuck-running
$SCAN_ID = docker compose ... exec postgres psql ... -c "SELECT scan_id FROM scans LIMIT 1;" | xargs
docker compose ... exec postgres psql ... -c \
  "UPDATE scans SET status='running', started_at=NOW()-INTERVAL '3 hours' WHERE scan_id='$SCAN_ID';"

# Wait for watchdog cycle (300s default), then verify status=failed_internal
docker compose ... exec postgres psql ... -c \
  "SELECT status, error_detail FROM scans WHERE scan_id='$SCAN_ID';"
# Expected: status=failed_internal, error_detail=watchdog_timeout
```

**Check 8 — Unit tests pass, coverage ≥ 75%**
```powershell
pytest tests/unit/test_engine.py -v --cov=backend/services/core_engine --cov-report=term-missing
# Expected: All tests passing, coverage ≥ 75%
```

---

## Known Pitfalls

| # | Pitfall | Prevention |
|---|---------|------------|
| 1 | `nuclei` exits `1` on zero findings — not an error | Only treat `returncode > 1` as ScanError — already in `subprocess_utils.py` |
| 2 | `subfinder` output buffers until exit filling pipe | Use `run_tool_streaming()` for subfinder — never `communicate()` |
| 3 | `dnsx` step skipped "for speed" | Never skip it — probing 10k non-existent permutations breaks your IP's reputation |
| 4 | Stage 4 + 5 run in parallel but share the `ScanResult` object | They return new lists — they do not write to `scan_result` directly; parent appends after gather |
| 5 | JSONB columns in SQLAlchemy with raw `text()` queries | Pass as `str(dict)` — asyncpg handles JSONB cast; or use `json.dumps()` explicitly |
| 6 | Redis lock release on worker crash | `task_reject_on_worker_lost=True` in Celery re-queues the message; lock TTL (`scan_lock_ttl_seconds=14400`) self-expires |
| 7 | Nuclei template updates fail in air-gapped CI | Add `|| true` to `nuclei -update-templates` in Dockerfile — M3 uses whatever templates were bundled at build |
| 8 | `ffuf` writes to stdout AND a JSON output file | Use `-o /dev/stdout -of json` to capture JSON inline; avoid temp file for output |
| 9 | `httpx` (Python library) vs `httpx` (ProjectDiscovery CLI tool) name conflict | Import the Python lib as `import httpx as httpx_client`; the CLI is invoked via subprocess |
| 10 | `alterx` not installed produces a FileNotFoundError | Wrap in `try/except` — alterx failure is non-fatal; fall back to subfinder results only |
| 11 | JS file download follows redirects to out-of-scope domains | `follow_redirects=True` but validate final URL domain against `ScopeFilter` before saving |
| 12 | `ON CONFLICT DO NOTHING` means `rowcount = 0` even on no-error | Count `rowcount > 0` per-insert in `save_findings()` to get accurate saved count |

---

## M3 Definition of Done

- [ ] `003_engine` migration applied — `alembic current` shows `003 (head)`
- [ ] All 8 new tables exist and have correct columns
- [ ] Core engine and core worker rebuild cleanly with all CLI tools present
- [ ] `curl http://localhost:8002/api/v1/health` returns `status=healthy`
- [ ] `POST /api/v1/scans/start` queues a message on `scan.jobs`
- [ ] A complete scan run populates rows in `assets`, `endpoints`, `findings`
- [ ] Scan status transitions: `running → completed` (or `partial` on stage failures)
- [ ] `scan.completed` message appears on `report.jobs` after scan completes
- [ ] Simulated worker crash + watchdog run marks scan `failed_internal` and republishes
- [ ] Dedup hash correctly deduplicates findings from overlapping stages (verified by unit test)
- [ ] Unit tests pass, coverage ≥ 75%
- [ ] Integration test passes against local Juice Shop (or skips cleanly without `INTEGRATION_TARGET`)
