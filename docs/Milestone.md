# 🏗️ AttackBot — Implementation Milestones

> A production roadmap for building an automated bug bounty discovery and reporting platform — from project skeleton to fully autonomous pipeline.

---

## 📋 Table of Contents

- [Milestone 1 — Solid Ground](#-milestone-1--solid-ground)
- [Milestone 2 — Eyes Open](#-milestone-2--eyes-open)
- [Milestone 3 — First Strike](#-milestone-3--first-strike)
- [Milestone 4 — Read the Room](#-milestone-4--read-the-room)
- [Milestone 5 — Get Inside](#-milestone-5--get-inside)
- [Milestone 6 — Break the Logic](#-milestone-6--break-the-logic)
- [Milestone 7 — Prove It](#-milestone-7--prove-it)
- [Milestone 8 — Connect the Dots](#-milestone-8--connect-the-dots)
- [Milestone 9 — Think Harder](#-milestone-9--think-harder)
- [Milestone 10 — The Machine](#-milestone-10--the-machine)
- [Summary Timeline](#-summary-timeline)
- [Key Principles](#-key-principles)

---

## 🪨 Milestone 1 — Solid Ground

**Purpose:** Build and validate the complete infrastructure foundation before writing a single line of application logic.

### ✅ Definition of Done

- `docker compose up` brings everything healthy with zero manual intervention on a cold boot
- `alembic upgrade head` runs cleanly from the migrate container
- All required MinIO buckets exist after `minio-init` completes
- All service skeletons return `200` on `/api/v1/health`
- CI passes on a clean push
- Grafana shows all services in the "alive" dashboard

### 🎯 Target Outcome

- Database migration system in place and verified
- Shared conventions established across all future services
- Project repository structure defined
- Basic CI pipeline running

---

### 📁 Step 1.1 — Repository Structure

- Define monorepo layout: `backend/services/`, `backend/shared/`, `infra/`, `scripts/`, `tests/`
- Establish naming conventions for services, modules, and files
- Set up `.gitignore`, `pyproject.toml`, `shared requirements/base.txt`

---

### 🐳 Step 1.2 — Docker Compose Infrastructure

Write `docker-compose.yml` with: PostgreSQL 16, Redis 7, RabbitMQ 3 (management plugin enabled), MinIO, Neo4j Community, Prometheus, Grafana, Loki, Tempo, Vault (dev mode), and two one-shot init services (`migrate`, `minio-init`).

Define `attackbot-net` internal network. Configure named volumes for all persistent services. Set explicit resource limits per container.

#### 🔴 Critical: Healthcheck Commands Per Service

| Service | Healthcheck Command |
|---|---|
| PostgreSQL | `["CMD-SHELL", "pg_isready -U $POSTGRES_USER && psql -U $POSTGRES_USER -c 'SELECT 1'"]` |
| Redis | `["CMD", "redis-cli", "--raw", "incr", "ping"]` |
| RabbitMQ | `["CMD", "rabbitmq-diagnostics", "check_port_connectivity"]` |
| Neo4j | `["CMD-SHELL", "wget -q --spider http://localhost:7474 \|\| exit 1"]` |
| MinIO | `["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]` |
| Vault | `["CMD", "vault", "status", "-address=http://localhost:8200"]` |
| FastAPI services | `["CMD", "curl", "-f", "http://localhost:800X/api/v1/health"]` |

#### 🔴 Critical: Healthcheck Tuning Parameters

Every service must define all four parameters:

```yaml
healthcheck:
  test: [...]
  interval: 10s
  timeout: 5s
  retries: 10
  start_period: 60s   # Neo4j and Vault need this — they take 30-60s to boot
```

> ⚠️ Without `start_period`, Docker counts failures from the first second. Neo4j and Vault will be marked unhealthy before they've had a chance to start.

#### 🔴 Critical: `depends_on` Conditions

Use `condition: service_healthy` for all upstream services. Use `condition: service_completed_successfully` for one-shot containers (`migrate`, `minio-init`, `vault-init`). `depends_on` without a condition only waits for container start, not readiness.

```yaml
# Example: core-engine depends_on chain
core-engine:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
    migrate:
      condition: service_completed_successfully
    minio-init:
      condition: service_completed_successfully
```

#### 🚦 6-Phase Startup Order in Compose

| Phase | Services | Notes |
|---|---|---|
| Phase 1 — Infra | `postgres`, `redis`, `rabbitmq`, `neo4j`, `minio`, `vault` | No `depends_on` |
| Phase 2 — Init | `migrate`, `minio-init`, `vault-init` | Depend on respective infra healthy |
| Phase 3 — Core Services | `scraper`, `core-engine`, `reporter`, `attack-graph-engine` | Depend on all infra + init `completed_successfully` |
| Phase 4 — Core Workers | `core-worker`, `reporter-worker` | Depend on respective core service healthy |
| Phase 5 — Specialist Workers | `browser-worker`, `api-fuzzer-worker`, `js-analysis-worker`, `scenario-runner`, `exploit-verifier`, `ai-analysis-worker` | — |
| Phase 6 — Gateway | `api-gateway` | Depends on all Phase 3 services healthy — last to start |

---

### 🔐 Step 1.3 — Vault Dev Mode

```yaml
vault:
  image: hashicorp/vault:1.15
  command: vault server -dev -dev-root-token-id="dev-root-token"
  environment:
    VAULT_DEV_ROOT_TOKEN_ID: "dev-root-token"
    VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
  cap_add:
    - IPC_LOCK
  healthcheck:
    test: ["CMD", "vault", "status", "-address=http://localhost:8200"]
    interval: 5s
    timeout: 3s
    retries: 10
    start_period: 10s
```

> 💡 Dev mode is intentional for local development — it starts unsealed with a known root token. It does not persist secrets across restarts, which is acceptable locally. **Do not use dev mode in production.**

---

### 🪣 Step 1.4 — MinIO Bucket Initialization

```yaml
minio-init:
  image: minio/mc
  depends_on:
    minio:
      condition: service_healthy
  entrypoint: >
    /bin/sh -c "
    mc alias set local http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD &&
    mc mb --ignore-existing local/reports &&
    mc mb --ignore-existing local/evidence &&
    mc mb --ignore-existing local/js-assets &&
    mc mb --ignore-existing local/summaries
    "
```

> ⚠️ **Important:** Do NOT add `mc anonymous set download local/reports`. Reports contain vulnerability details about real targets. All report access must go through the Reporter API using pre-signed URLs — never via direct public bucket access.

---

### 🗄️ Step 1.5 — Database Migration System

- Set up Alembic in `backend/migrations/`
- Write `env.py` to load `DATABASE_URL` from environment
- Create `001_initial_schema.py` with `programs` and `scans` tables as proof of life
- Write `migrate` one-shot service: depends on postgres `service_healthy`, runs `alembic upgrade head`, exits `0` on success

---

### 📚 Step 1.6 — Shared Library (`backend/shared/`)

| File | Purpose |
|---|---|
| `config.py` | Pydantic Settings base class (all services inherit) |
| `logging.py` | Structured JSON logger with fields: timestamp, service, level, event + context kwargs |
| `db.py` | SQLAlchemy async engine factory |
| `health.py` | Base health check response model |
| `exceptions.py` | Common exception hierarchy |
| `queue.py` | RabbitMQ connection + publish/consume base classes |

---

### 🦴 Step 1.7 — Service Skeletons

- **FastAPI skeletons** for: `scraper`, `core-engine`, `reporter`, `attack-graph-engine` — each with `main.py`, `config.py`, `/api/v1/health` endpoint, `Dockerfile`
- **Celery worker skeletons** for: `core-worker`, `reporter-worker`, `browser-worker`, `api-fuzzer-worker`, `js-analysis-worker`, `scenario-runner`, `exploit-verifier`, `ai-analysis-worker`

---

### ⚙️ Step 1.8 — CI Pipeline

GitHub Actions workflow: lint (`ruff`), type check (`mypy`), run tests, build Docker images on every push. Coverage report generated (even if empty at this stage).

---

### 📊 Step 1.9 — Observability Baseline

- Prometheus scrape config pointing at all service `/metrics` endpoints
- Grafana provisioned with Prometheus + Loki + Tempo as data sources
- One dashboard: **"Services Alive"** — all health check statuses

---

### 🔎 Step 1.10 — Startup Order Validation & Operational Notes

- Confirm compose `depends_on` + healthcheck ordering works end-to-end on a cold boot from zero
- Document in `infra/README.md`:
  - Bootstrap sequence
  - Known constraint: `h2spacex` (used in M9) requires raw socket access — works in standard Docker but will fail in AWS Fargate and some GCP Cloud Run configurations

---

## 👀 Milestone 2 — Eyes Open

**Purpose:** Build the Scraper. Real bug bounty programs from real platforms should flow into your database on a schedule.

### ✅ Definition of Done

- `POST /scrape/trigger` results in rows in `programs` and `program_scopes`
- A message appears on `scan.jobs` in RabbitMQ management UI
- A simulated publish failure results in `queued_for_scan = true`; the reconciler clears it on next cycle
- A simulated 429 response triggers retry with `Retry-After` delay
- All tests pass, coverage ≥ 80%

### 🎯 Target Outcome

- Platform collector abstraction built and extensible
- HackerOne collector fully implemented with rate limit handling
- Program normalization pipeline working
- Scope parsing producing structured `program_scopes` entries
- Publish-to-queue pipeline working
- Reconciler handling publish failures correctly
- Full Scraper test coverage above 80%

---

### 📋 Step 2.1 — Full Scraper Database Schema

Alembic revision `002_scraper_full`: `programs`, `program_scopes`, `program_policies` with all fields from architecture doc.

---

### 🧩 Step 2.2 — Platform Collector Abstraction

Define `BaseCollector` abstract class:

```
BaseCollector
├── fetch_listing()  -> list[RawProgram]
├── fetch_details(handle) -> RawProgram
└── normalize(raw)   -> Program
```

`CollectorRegistry`: maps platform name → collector class.

---

### 🕵️ Step 2.3 — HackerOne Collector

**Authentication:** HTTP Basic Auth. API token identifier = username, token value = password. Tokens require Professional, Community, or Enterprise account.

```python
requests.get(url, auth=("<API_USERNAME>", "<API_TOKEN>"), headers={"Accept": "application/json"})
```

**Rate limits:** 600 req/min (read), 25 req/20s (write). Exceeding returns HTTP `429`.

#### 🔴 Critical: Always Handle 429 with Retry Logic

Without this, a mid-scrape rate limit will crash the collector and leave `queued_for_scan` in an inconsistent state:

```python
def get_with_retry(url, auth, params=None, max_retries=3):
    for attempt in range(max_retries):
        resp = requests.get(url, auth=auth, params=params)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            time.sleep(retry_after)
            continue
        resp.raise_for_status()
        return resp
    raise CollectorRateLimitError(f"Rate limited after {max_retries} retries")
```

**Key endpoints:**

```
GET /v1/hackers/programs             — paginated listing
GET /v1/hackers/programs/{handle}    — full program detail
GET /v1/hackers/programs/{handle}/structured_scopes
```

#### 🔴 Critical: Use `structured_scopes`, Not Raw Policy Markdown

It returns pre-parsed `asset_type` and `value` fields that map directly to your `program_scopes` table and eliminates the need for a complex markdown parser.

**Pagination pattern:**

```python
page = 1
while True:
    resp = get_with_retry(url, auth, params={"page[number]": page, "page[size]": 100})
    data = resp.json()["data"]
    if not data:
        break
    yield from data
    page += 1
```

---

### 🔭 Step 2.4 — Scope Parser

Write `ScopeParser` that takes raw scope entries and produces typed `ProgramScope` objects. Handle asset types: `url`, `domain`, `wildcard_domain`, `ip_range`, `mobile_app`, `api`. Unit tests covering: wildcard matching, CIDR notation, exact match, mobile app handles, out-of-scope entries.

---

### 🔄 Step 2.5 — Upsert Logic

`ProgramRepository.upsert()`: insert-on-conflict-update. Preserve `queued_for_scan` flag if program already exists — do not overwrite it during a rescrape. Track `last_scraped_at` on every run.

---

### 📤 Step 2.6 — Queue Publisher

`QueuePublisher`: RabbitMQ connect, passive queue check for `scan.jobs` (passive avoids argument mismatch failures), persistent message publish. Reconnect loop as background task. On publish failure: set `queued_for_scan = true`.

---

### ♻️ Step 2.7 — Reconciler

`Reconciler.reconcile()`: queries programs `WHERE queued_for_scan = true AND last_scraped_at > NOW() - INTERVAL '7 days'`. Republishes each; clears flag on success; leaves flag on failure for next cycle. Runs on APScheduler every 5 minutes.

---

### 🕐 Step 2.8 — APScheduler Integration

- Per-platform scheduled scrape jobs
- Redis lock per platform (`scraper:lock:{platform}`) prevents overlapping runs
- Configurable intervals per platform via environment variables

---

### 🌐 Step 2.9 — Scraper APIs

```
POST /api/v1/scrape/trigger
GET  /api/v1/programs                           (paginated, filterable)
GET  /api/v1/programs/{program_id}
GET  /api/v1/programs/{program_id}/scope
GET  /api/v1/health                             — surfaces DB, RabbitMQ, and scheduler state
```

---

### 🧪 Step 2.10 — Tests

- **Unit:** collector normalization (mocked API responses), scope parser edge cases, upsert logic, reconciler logic, 429 retry handler
- **Integration:** full scrape → DB → queue publish flow (RabbitMQ in test compose)
- **Coverage ≥ 80%**

---

## ⚡ Milestone 3 — First Strike

**Purpose:** Build the Core Engine's unauthenticated scanning pipeline — Stages 0 through 6, excluding browser sessions and API fuzzing.

### ✅ Definition of Done

- A scan job on `scan.jobs` results in populated `assets`, `endpoints`, `findings` in DB
- Scan state correctly transitions through `running → completed/partial`
- `scan.completed` message appears on `report.jobs`
- A simulated worker crash + watchdog run marks the scan `failed_internal` and republishes if `retry_count < 2`
- Dedup hash correctly de-duplicates findings from overlapping stages
- All tests pass, coverage ≥ 75%

### 🎯 Goals

- Full Engine database schema in place
- Pipeline stages 0–6 implemented
- CLI tool wrappers implemented safely (no deadlocks, no temp file leaks)
- Deduplication hash defined and implemented
- Findings persisted with CVSS scoring
- Scan state machine and watchdog working
- Engine test coverage above 75%

---

### 📋 Step 3.1 — Engine Database Schema

Alembic revision `003_engine`: `scans`, `scan_stages`, `assets`, `endpoints`, `js_assets`, `findings`, `finding_evidence`, `vulnerability_groups`.

---

### 🚀 Step 3.2 — Scan Task Entry

Celery `scan_task` on `scan.jobs` → delegates to `_async_scan_task()` via `asyncio.run()`. Redis lock per program (`scan:lock:{program_id}`). Creates/reuses `scans` row, marks `running`. Fetches program scope from Scraper API.

> 💡 Add `retry_count` column to `scans` table. Gate retry-on-recovery to `retry_count < 2` — a scan OOM-killed mid-pipeline will likely OOM again on the same target.

---

### 🐕 Step 3.3 — Celery Crash Recovery Watchdog

Add to `core-engine`'s APScheduler:

```python
async def recover_stuck_scans():
    stuck = await db.fetch("""
        SELECT scan_id, retry_count FROM scans
        WHERE status = 'running'
        AND started_at < NOW() - INTERVAL '2 hours'
    """)
    for scan in stuck:
        await db.execute("""
            UPDATE scans SET status='failed_internal',
            error_detail='watchdog_timeout'
            WHERE scan_id=$1
        """, scan["scan_id"])
        if scan["retry_count"] < 2:
            await republish_scan(scan["scan_id"])
```

> ⚠️ Without this, any worker crash leaves `status = running` forever with no recovery path.

---

### 🛡️ Step 3.4 — Stage 0 — Scope Filter (FATAL)

`ScopeFilter` built from `program_scopes` entries. Methods: `is_in_scope(url)`, `is_in_scope(domain)`, `is_in_scope(ip)`. Fatal if scope cannot be resolved — do not proceed with an undefined scope.

Unit tests: wildcard matching (`*.example.com`), CIDR matching, exact match, out-of-scope rejection.

---

### 🔧 Step 3.5 — CLI Subprocess Wrapper Pattern

**Golden rule:** Use `communicate()`, not direct stream reading. Direct stream reading causes deadlocks when child output fills the OS pipe buffer (64KB default).

Always use `create_subprocess_exec` with args as a list — **never shell string interpolation**.

```python
import tempfile, os

async def run_nuclei(targets: list[str], scan_id: str, timeout: int = 3600) -> list[dict]:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
        tf.write('\n'.join(targets))
        targets_path = tf.name

    output_file = f"/tmp/nuclei_output_{scan_id}.json"
    try:
        proc = await asyncio.create_subprocess_exec(
            "nuclei", "-l", targets_path, "-j", "-o", output_file, "-silent",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise ScanTimeoutError(f"nuclei timed out after {timeout}s")
        # nuclei exits 1 on zero findings — only treat > 1 as a real error
        if proc.returncode > 1:
            raise ScanError(f"nuclei exited {proc.returncode}")
        return [json.loads(l) for l in stdout.decode().splitlines() if l.strip().startswith("{")]
    finally:
        os.unlink(targets_path)
        if os.path.exists(output_file):
            os.unlink(output_file)
```

For large-output tools (`amass`, `subfinder`) — use streaming readline:

```python
async def run_subfinder_streaming(domain: str, timeout: int = 1800) -> list[str]:
    proc = await asyncio.create_subprocess_exec(
        "subfinder", "-d", domain, "-json", "-silent",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    results = []
    async def read_lines():
        async for line in proc.stdout:
            decoded = line.decode().strip()
            if decoded:
                results.append(json.loads(decoded))
    try:
        await asyncio.wait_for(
            asyncio.gather(read_lines(), proc.wait()),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
    return results
```

#### ☑️ Subprocess Gotcha Checklist

- `nuclei` outputs mixed JSON + status lines → use `-silent` flag + filter lines starting with `{`
- `amass`/`subfinder` buffer until exit → use streaming readline
- Always pipe `stderr` to `DEVNULL` or a separate reader — never leave it unread
- Always `proc.kill()` then `await proc.wait()` on timeout — kill alone is not enough
- `nuclei` exits `1` on zero findings — only treat `returncode > 1` as a real error

---

### 🌐 Step 3.6 — Stage 1 — Asset Discovery

> 💡 **Note on tooling:** `amass` is in maintenance-only mode. Replace with a modern pipeline:

```
subfinder  → passive subdomain enumeration
alterx     → permutation generation from subfinder output
dnsx       → DNS resolution + live host filtering  ← do not skip this step
httpx      → HTTP probing
```

> ⚠️ `dnsx` between `alterx` and `httpx` is **mandatory** — without it you probe thousands of non-existent permuted subdomains and get garbage results. The pipeline is: `subfinder | alterx | dnsx | httpx`.

Filter each discovered asset through `ScopeFilter` before persisting. Persist to `assets` table.

---

### 🔬 Step 3.7 — Stage 2 — Fingerprinting

Wrap `httpx` (projectdiscovery) for HTTP probing. Detect technology stack, WAF, response headers. Update `assets` with fingerprint data.

---

### 📂 Step 3.8 — Stage 3 — Enumeration

Wrap `ffuf` for directory/endpoint discovery. Integrate `waybackurls` for historical URL data. Persist discovered endpoints to `endpoints` table. Discover and download JS files; store in MinIO; record in `js_assets`.

---

### ☢️ Step 3.9 — Stage 4 — Nuclei Scanning

Wrap `nuclei` CLI with scope-filtered target list. Parse nuclei JSON output into `Finding` candidates. Apply CVSS scoring per finding. Persist as unverified findings (`is_verified = false`).

---

### 🕷️ Step 3.10 — Stage 5 — Web Vulnerability Tests

- **XSS scanner:** parameter reflection + payload injection
- **CORS scanner:** Origin header manipulation, response analysis
- **CRLF, SQLi, SSRF:** implemented but gated behind feature flags, disabled by default

Persist candidates as unverified findings.

---

### 🔑 Step 3.11 — Stage 6 — JS Secret Scanning

Regex-based API key, token, credential detection. Reads JS file content from MinIO by `js_asset_id`. Persist candidates as unverified findings.

---

### #️⃣ Step 3.12 — Deduplication Hash

Every finding must have a `deduplication_hash` computed before persistence. The composition must be stable (exclude timestamps, evidence paths, `scan_id`) and URL-normalized:

```python
from urllib.parse import urlparse, parse_qsl, urlencode
import hashlib

def normalize_url(url: str) -> str:
    parsed = urlparse(url.lower())
    sorted_query = urlencode(sorted(parse_qsl(parsed.query)))
    return parsed._replace(query=sorted_query).geturl()

def compute_dedup_hash(finding: dict) -> str:
    components = "|".join([
        finding["vulnerability_type"].lower(),
        normalize_url(finding["affected_url"]),
        finding.get("affected_parameter", "").lower(),
        finding.get("payload", "")[:100],  # truncated — payloads vary slightly
    ])
    return hashlib.sha256(components.encode()).hexdigest()
```

> ⚠️ Without URL normalization, `?b=2&a=1` and `?a=1&b=2` produce different hashes for the same endpoint, causing under-deduplication.

---

### 📦 Step 3.13 — Stage 7 (Temporary) — Aggregation + Persistence

`FindingAggregator`: deduplication by hash, severity aggregation. Populate `vulnerability_groups`. Finalize `scans` row. Publish `scan.completed` to `report.jobs`.

---

### ⚡ Step 3.14 — Pipeline Parallelism

```python
# Stages 4 + 5 in parallel group A
nuclei_task = asyncio.create_task(run_stage_4(scan_ctx))
web_vuln_task = asyncio.create_task(run_stage_5(scan_ctx))
nuclei_findings, web_findings = await asyncio.gather(nuclei_task, web_vuln_task)

# Stage 6 sequential after (needs JS files from Stage 3)
js_findings = await run_stage_6(scan_ctx)
```

---

### 🔄 Step 3.15 — Scan State Machine

| State | Trigger |
|---|---|
| `completed` | All stages succeeded |
| `partial` | Non-fatal stage failure(s), `partial_detail` recorded |
| `failed_scope` | Stage 0 fatal — scope unresolvable |
| `failed_internal` | Stage 10 fatal — aggregation failed |
| `failed_auth` | Browser session bootstrap critically failed (M5+) |

---

### 🌐 Step 3.16 — Engine APIs

```
POST /api/v1/scans/start
GET  /api/v1/scans
GET  /api/v1/scans/{scan_id}
GET  /api/v1/scans/{scan_id}/findings
GET  /api/v1/queue/dlq/inspect
GET  /api/v1/health
```

---

### 🧪 Step 3.17 — Tests

- **Unit:** ScopeFilter (wildcard, CIDR, exact, rejection), each stage in isolation (mocked subprocesses), state machine transitions, dedup hash with URL normalization cases, watchdog recovery logic
- **Integration:** full scan pipeline on a local intentionally vulnerable app (DVWA or Juice Shop)
- **Coverage ≥ 75%**

---

## 📄 Milestone 4 — Read the Room

**Purpose:** Build the Reporter. Findings from a real scan become a structured, submittable PDF/DOCX report with reproduction steps.

### ✅ Definition of Done

- Full chain: trigger scrape → scan → report → `GET /reports/{id}/download` returns real PDF
- Report contains findings table + per-finding reproduction steps with curl commands
- A scan with zero findings produces a valid "No Findings" report, not a crash
- MinIO contains the report file at the expected path
- All tests pass, coverage ≥ 80%

### 🎯 Goals

- Reporter database schema in place
- PDF and DOCX report generation working
- Reproduction packs generated per finding
- Zero-finding scans handled gracefully
- Report files stored in MinIO
- Full end-to-end chain working

---

### 📋 Step 4.1 — Reporter Database Schema

Alembic revision `004_reporter`: `reports`, `reproduction_packs`.

---

### 🚀 Step 4.2 — Report Task Entry

Celery `generate_report_task` on `report.jobs`. Creates one `reports` row per format with `status = generating`. Fetches scan detail + findings from Engine API. Fetches program metadata + scope from Scraper API.

---

### 🗂️ Step 4.3 — ParsedScan Model

Internal `ParsedScan` dataclass that normalizes all fetched data. Decouples generation logic from API shapes.

#### 🔴 Critical: Guard Zero-Finding Scans at Construction Time

```python
@dataclass
class ParsedScan:
    scan_id: str
    program: Program
    findings: list[Finding]
    has_findings: bool

    def __post_init__(self):
        self.has_findings = len(self.findings) > 0

    def get_report_mode(self) -> Literal["findings", "clean"]:
        return "findings" if self.has_findings else "clean"
```

Both PDF and DOCX generators check `get_report_mode()` first. A clean scan produces a minimal "No Findings" report rather than empty tables or a crash.

---

### 📋 Step 4.4 — Reproduction Pack Assembly

Per finding, generate and persist to `reproduction_packs`: `curl_command`, `http_request_raw`, `browser_steps`.

Example curl output:

```bash
# Finding: Reflected XSS in search parameter
# Severity: High | CVSS: 7.2
curl -X GET "https://target.com/search?q=<script>alert(1)</script>" \
  -H "Cookie: session=abc123"
```

---

### 📑 Step 4.5 — PDF Generator

Use `reportlab` or `weasyprint`. Sections: Executive Summary, Scope Overview, Findings Table, Per-Finding Detail with repro steps, Appendix with reproduction packs.

**Severity colour coding:**

| Severity | Colour |
|---|---|
| Critical | 🔴 Red |
| High | 🟠 Orange |
| Medium | 🟡 Yellow |
| Low | 🔵 Blue |

---

### 📝 Step 4.6 — DOCX Generator

Use `python-docx`. Same section structure. Formatted tables for findings. Code blocks for reproduction commands.

---

### ☁️ Step 4.7 — MinIO Upload

Upload to `reports/{report_id}/report.{format}`. Store MinIO path in `reports.storage_path`. All download access via pre-signed URLs through the Reporter API — **never direct bucket access**.

---

### 📡 Step 4.8 — Completion Event

Publish `report.generated` to `reports.completed` after successful generation.

---

### 🐕 Step 4.9 — Watchdog

APScheduler queries `reports WHERE status = 'generating' AND created_at < NOW() - INTERVAL '30 minutes'`. Marks stale rows `failed` with `error_detail = watchdog_timeout`.

---

### 🌐 Step 4.10 — Reporter APIs

```
GET /api/v1/reports
GET /api/v1/reports/{report_id}
GET /api/v1/reports/{report_id}/download    — streams via pre-signed MinIO URL
GET /api/v1/scans/{scan_id}/reports
GET /api/v1/health
```

---

### 🧪 Step 4.11 — Tests

- **Unit:** ParsedScan normalization, zero-finding path, reproduction pack generation, PDF/DOCX structure
- **Integration:** full chain from `report.jobs` message → MinIO file → download API
- **Coverage ≥ 80%**

---

> 🎉 **--- YOU NOW HAVE A WORKING PRODUCT ---**
> Milestones 1–4 give you a real, functional bug bounty pipeline. Everything from here is capability expansion.

---

## 🔐 Milestone 5 — Get Inside

**Purpose:** Add the Browser Worker for authenticated scanning. The biggest single capability jump — most interesting vulnerabilities live behind a login wall.

### ✅ Definition of Done

- A scan against a login-protected local test app produces session cookies in `browser_sessions`
- Nuclei and XSS stages use the session and discover findings they couldn't unauthenticated
- Out-of-scope navigation is hard-blocked by route intercept
- Session data is encrypted at rest and correctly restored via `storage_state`
- Two sessions created when IDOR flag is enabled
- TOTP secret resolved from Vault, not YAML

### 🎯 Goals

- Browser Worker service fully operational with scope enforcement
- YAML scenario system implemented and extensible
- Session bundles persisted (encrypted) and correctly shareable via `storage_state`
- Two sessions bootstrapped per scan when IDOR verification is enabled
- TOTP/MFA support implemented with secrets resolved from Vault at runtime
- Stage 3.5 integrated into pipeline

---

### 🎭 Step 5.1 — Browser Worker Setup

Playwright installed in isolated Docker container. `service_workers='block'` is **mandatory** — `browser_context.route()` does not intercept requests handled by Service Workers without this setting.

Celery worker consuming `browser.jobs`. One fresh Playwright browser context per job — no shared state between jobs.

---

### 🛡️ Step 5.2 — Scope Enforcement via Route Interception

> ⚠️ Use `browser_context.route()`, **not** `page.route()`. Context-level interception applies to every page in the context. Page-level interception only applies to that one page.

```python
from playwright.async_api import async_playwright
from urllib.parse import urlparse

async def create_scoped_context(browser, in_scope_domains: list[str]):
    context = await browser.new_context(
        service_workers="block",  # critical — see above
    )

    async def enforce_scope(route):
        url = route.request.url
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        is_in_scope = any(
            hostname == d or hostname.endswith(f".{d}")
            for d in in_scope_domains
        )
        is_internal = parsed.scheme in ("data", "about", "chrome-extension", "blob")
        if is_in_scope or is_internal:
            await route.continue_()
        else:
            await route.abort()  # hard block, log for audit

    await context.route("**/*", enforce_scope)
    return context
```

---

### 💾 Step 5.3 — Session Storage and Reuse (`storage_state`)

This is the mechanism that allows session data to be shared between workers. Without it, browser sessions cannot be loaded into a new context and the entire authenticated scanning capability is broken.

**Saving a session after login:**

```python
storage = await context.storage_state()
# storage = {"cookies": [...], "origins": [{"localStorage": [...]}]}
# Encrypt and store in browser_sessions.cookies + local_storage
```

**Restoring a session in a new context:**

```python
context = await browser.new_context(
    storage_state={
        "cookies": decrypted_cookies,
        "origins": decrypted_origins
    }
)
```

---

### 🔒 Step 5.4 — Session Bundle Encryption

AES-256 encryption for all session data (cookies, `localStorage`, headers) before DB write. Store encrypted bytes in `browser_sessions`. Decryption utility available to any downstream worker that holds a `session_id`.

---

### 👥 Step 5.5 — Two-Session Bootstrap for IDOR

IDOR verification requires two distinct authenticated sessions. Stage 3.5 must bootstrap two when IDOR verification is enabled:

```python
async def bootstrap_sessions(scan_context):
    if scan_context.feature_flags.get("idor_verification"):
        session_a = await trigger_browser_session(scan_context, account_slot="primary")
        session_b = await trigger_browser_session(scan_context, account_slot="secondary")
        scan_context.sessions = {"primary": session_a, "secondary": session_b}
    else:
        session_a = await trigger_browser_session(scan_context, account_slot="primary")
        scan_context.sessions = {"primary": session_a}
```

> ⚠️ Without two sessions, your IDOR verifier (M7) has nothing to compare against and either skips verification silently or crashes.

---

### 🎬 Step 5.6 — Scenario Engine

YAML scenario loader and validator. Step interpreter: `visit`, `fill`, `submit`, `wait`, `capture_cookies`, `capture_headers`, `capture_local_storage`. 30s page timeout, 120s total scenario timeout.

---

### 🔐 Step 5.7 — TOTP/MFA Support

Many bug bounty targets enforce 2FA on test accounts. A missing `handle_totp` step produces invalid sessions silently.

```yaml
# scenarios/login_totp.yaml
steps:
  - visit: /login
  - fill: [email, $EMAIL]
  - fill: [password, $PASSWORD]
  - submit
  - handle_totp:
      secret: $TOTP_SECRET   # variable reference — resolved from Vault at runtime
  - capture_cookies
```

#### 🔴 Critical: TOTP Secret Handling

`$TOTP_SECRET` is a variable reference, not a literal value. TOTP secrets must **never** be stored in YAML files — they belong in Vault under `secret/programs/{program_id}/totp_secret`.

```python
import pyotp

def handle_totp_step(step: dict, vault_client, program_id: str) -> str:
    secret_ref = step["secret"]
    if secret_ref.startswith("$"):
        secret = vault_client.secrets.kv.read_secret(
            path=f"programs/{program_id}/totp_secret"
        )["data"]["value"]
    else:
        secret = secret_ref
    return pyotp.TOTP(secret).now()
```

---

### 🧪 Step 5.8 — Account Creation + Login Scenario

Built-in `login_basic.yaml` scenario. Random credential generation for account creation. Login flow with credential reuse. CSRF token extraction from forms.

---

### 🔗 Step 5.9 — Stage 3.5 Pipeline Integration

- Engine publishes `session.request` to `browser.jobs` after Stage 3
- Engine awaits `session_id` return via Redis result backend (with timeout)
- Session ID attached to scan context for Stages 4 and 5
- Feature flag `ENABLE_BROWSER_SESSION` gates this stage

---

### 📡 Step 5.10 — Downstream Session Usage

- **Nuclei:** passes session cookies via `-H "Cookie: {cookie_string}"` flag
- **XSS/CORS scanner:** attaches session headers to all requests

---

### 🧪 Step 5.11 — Tests

- **Unit:** scenario step interpreter, YAML validator, scope enforcement (assert out-of-scope requests are aborted), `storage_state` round-trip, TOTP code generation
- **Integration:** full session bootstrap against DVWA or Juice Shop
- Verify encrypted session data decrypts correctly
- Verify two sessions are created when `idor_verification = true`

---

## 🧠 Milestone 6 — Break the Logic

**Purpose:** Add API fuzzing and enhanced JS analysis. These two capabilities find the class of bugs that rule-based scanners completely miss.

### ✅ Definition of Done

- A negative-amount transfer on a test API is detected as a business logic flaw
- A hardcoded AWS key in a JS file surfaces as a secret finding
- DOM XSS sink in JS is detected via AST analysis
- Schemathesis produces at least one anomaly finding on crAPI

---

### 🔍 Step 6.1 — API Schema Discovery

During Stage 3 enumeration, attempt discovery of: `/openapi.json`, `/swagger.json`, `/api-docs`, `/graphql` (introspection query). Persist raw schemas to `api_schemas`.

---

### 🤖 Step 6.2 — API Fuzzer Worker

Celery worker consuming `api.fuzz.jobs`. Schemathesis (schema-driven property testing), RESTler (stateful REST fuzzing), custom `ffuf`-based mutator for endpoints without schemas.

---

### 🔀 Step 6.3 — Mutation Strategy

| Input Type | Mutations |
|---|---|
| Integer field | `0`, `-1`, `max_int`, type confusion (`"string"`) |
| String field | empty, null, SQLi patterns, SSTI payloads |
| Required field | omit entirely |
| Amount/price field | negative, fractional, overflow |
| UUID field | own ID, other user IDs, null UUID |

---

### 🚨 Step 6.4 — Anomaly Detection

- `500` responses where `400` expected
- Response body contains data belonging to a different user
- Authorization degradation (action succeeds without required role)
- State changes inconsistent with expected workflow

---

### 🔗 Step 6.5 — Stage 4.5 Pipeline Integration

Engine publishes `fuzz.request` to `api.fuzz.jobs` after Stage 4. Runs in parallel with Stage 5. Results merged into findings pool at Stage 10.

---

### 🧬 Step 6.6 — Enhanced JS Analysis Worker

Celery worker consuming `js.analysis.jobs`. Semgrep with custom security ruleset. AST traversal using `esprima` or `tree-sitter`:

- **DOM XSS sinks:** `innerHTML`, `document.write`, `eval`, `setTimeout(string)`
- **Prototype pollution:** `__proto__`, `constructor[prototype]`
- **Unsafe postMessage:** missing origin validation
- **Regex-based secrets:** AWS keys, GCP credentials, Stripe, Twilio, JWT secrets, private keys, bearer tokens

---

### 🔧 Step 6.7 — Stage 6 Enhancement

Existing `secret_js` scanner from M3 Stage 6 moves into JS Analysis Worker. All JS analysis now flows through `js.analysis.jobs` queue for unified handling.

---

### 🧪 Step 6.8 — Tests

- **Unit:** each mutation type generator, anomaly detectors, each AST rule
- **Integration:** fuzz crAPI (intentionally vulnerable API) and assert business logic findings are produced
- **Coverage ≥ 75%**

---

## ✅ Milestone 7 — Prove It

**Purpose:** Add the Exploit Verifier. The most important quality gate in the system — nothing unverified reaches a report.

### ✅ Definition of Done

- A known XSS finding has a screenshot in MinIO and appears embedded in the report
- A nuclei false positive is filtered and does not appear in the report
- A known SSRF finding triggers and receives an Interactsh callback
- False positive rate metric visible in Grafana

### 🎯 Goals

- All verifier modules implemented
- Interactsh self-hosted for OOB detection
- Evidence bundles stored in MinIO
- False positive rate measurable in Grafana

---

### 🏗️ Step 7.1 — Exploit Verifier Worker Setup

Celery worker consuming `verify.jobs`. Playwright available. Interactsh client for OOB detection.

---

### 📡 Step 7.2 — Interactsh for OOB Callbacks

> ⚠️ Do not build a custom HTTP listener. Use Interactsh (ProjectDiscovery) — it detects DNS, HTTP(S), SMTP, and LDAP callbacks simultaneously. DNS detection is critical because many WAFs block outbound HTTP while still allowing DNS.

**Self-hosting setup:** Requires a VPS with public IP, a domain, and NS delegation to your VPS IP. Run `interactsh-server -domain <YOUR_DOMAIN> -wildcard -token <TOKEN>`. Needs ports 80, 443, 53, 389, 587, 25 open.

#### 🔴 Critical: Correlation ID Format

Interactsh requires exactly **33 characters** of lowercase alphanumeric:

```python
import random, string

def generate_correlation_id() -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=33))
```

#### 🔴 Critical: Register OOB URL BEFORE Injecting Payload

```python
async def verify_ssrf(affected_url: str, parameter: str) -> bool:
    # Step 1: Register FIRST
    oob_url, correlation_id = await register_oob_url()

    # Step 2: Start listener BEFORE injection
    listener_task = asyncio.create_task(
        poll_for_interaction(correlation_id, timeout=45)
    )

    # Step 3: Small buffer for poll to initialize, THEN inject
    await asyncio.sleep(0.5)
    await inject_payload(affected_url, parameter, oob_url)

    # Step 4: Await result
    interaction = await listener_task
    return interaction is not None

async def poll_for_interaction(correlation_id: str, timeout: int = 45) -> dict | None:
    deadline = asyncio.get_event_loop().time() + timeout
    await asyncio.sleep(1.5)  # initial delay before first poll
    async with httpx.AsyncClient() as client:
        while asyncio.get_event_loop().time() < deadline:
            resp = await client.get(
                f"{INTERACTSH_SERVER}/poll",
                params={"id": correlation_id},
                headers={"Authorization": f"Bearer {INTERACTSH_TOKEN}"}
            )
            interactions = resp.json().get("data", [])
            if interactions:
                return interactions[0]
            await asyncio.sleep(3)
    return None
```

---

### 💻 Step 7.3 — XSS Verifier

> 💡 CDP sessions are Chromium-only — always use `p.chromium.launch()` in the verifier.

```python
async def verify_xss_via_cdp(page, payload_marker: str) -> bool:
    cdp_session = await page.context.new_cdp_session(page)
    xss_fired = asyncio.Event()

    async def on_console(event):
        if payload_marker in str(event.get("args", [])):
            xss_fired.set()

    await cdp_session.send("Runtime.enable")
    cdp_session.on("Runtime.consoleAPICalled", on_console)
    await page.goto(target_url_with_payload)

    try:
        await asyncio.wait_for(xss_fired.wait(), timeout=10.0)
        return True
    except asyncio.TimeoutError:
        return False
    finally:
        await cdp_session.detach()
```

---

### 🌐 Step 7.4 — CORS Verifier

Send crafted `Origin: https://attacker.example.com`. Assert `Access-Control-Allow-Origin` reflects attacker origin AND `Access-Control-Allow-Credentials: true` if the finding involves credentialed requests.

---

### 🔁 Step 7.5 — SSRF Verifier

See Step 7.2 above (Interactsh pattern).

---

### 👤 Step 7.6 — IDOR Verifier

Load `session_b` (secondary session from M5 Step 5.5) via `storage_state`. Attempt to access a resource owned by `session_a`. Confirm unauthorized data is returned.

```python
async def verify_idor(finding, sessions: dict) -> bool:
    context = await browser.new_context(
        storage_state={
            "cookies": decrypt(sessions["secondary"].cookies),
            "origins": decrypt(sessions["secondary"].local_storage),
        }
    )
    page = await context.new_page()
    resp = await page.request.get(finding["affected_url"])
    return contains_cross_user_data(resp, sessions["primary"])
```

---

### 💉 Step 7.7 — SQLi Verifier

- **Time-based blind:** inject known delay payload, measure response time delta (> 4s = confirmed)
- **Error-based:** detect database error strings in response body

---

### 🔑 Step 7.8 — Secret Verifier

Attempt actual authentication using the discovered key/token against the relevant API. Mark `is_verified = true` only if authentication succeeds. Mark `is_false_positive = true` if key is inactive.

---

### 🗂️ Step 7.9 — Evidence Storage

Per verified finding, store in MinIO under `evidence/{finding_id}/`:

| File | Content |
|---|---|
| `screenshot.png` | Headless browser screenshot |
| `request_response.txt` | Raw HTTP request + response |
| `oob_interaction.json` | Interactsh callback receipt (SSRF findings) |
| `payload.txt` | Exact payload used |

Record all paths in `finding_evidence`.

---

### 🔗 Step 7.10 — Pipeline Integration

Stage 8 in Engine pipeline. All candidates from Stages 4, 4.5, 5, 6 flow through `verify.jobs`. Only `verified = true` findings promoted to final pool. `is_false_positive = true` with reason set for unverified candidates.

---

### 📄 Step 7.11 — Reporter Integration

- Reporter fetches only `is_verified = true` findings
- Evidence paths included in per-finding sections
- Screenshot thumbnails embedded in DOCX/PDF

---

### 📊 Step 7.12 — False Positive Rate Metric

Prometheus: `attackbot_false_positive_rate = unverified_count / candidate_count` per scan. Grafana panel on main dashboard.

---

### 🧪 Step 7.13 — Tests

- **Unit:** each verifier module against mock responses, OOB registration and polling, IDOR cross-session logic, correlation ID format validation
- **Integration:** verify known XSS on Juice Shop produces screenshot in MinIO; verify known SSRF callback is received via Interactsh
- **Coverage ≥ 80%**

---

## 🕸️ Milestone 8 — Connect the Dots

**Purpose:** Build the Attack Graph Engine. Correlate individual findings into exploit chains with escalated severity.

### ✅ Definition of Done

- A subdomain takeover + session fixation on a shared asset detected as a chain
- A subdomain takeover and unrelated IDOR do **NOT** produce a chain
- Chain appears in report with escalated severity
- Neo4j browser shows connected graph for the scan

---

### 🏗️ Step 8.1 — Attack Graph Engine Service

FastAPI service on `:8006`. Neo4j Python driver. Health check validates Neo4j connectivity.

---

### ⚡ Step 8.2 — Indexes First (Critical for Performance)

Create before any query work:

```cypher
CREATE INDEX finding_type IF NOT EXISTS FOR (f:Finding) ON (f.type);
CREATE INDEX finding_scan IF NOT EXISTS FOR (f:Finding) ON (f.scan_id);
CREATE INDEX finding_verified IF NOT EXISTS FOR (f:Finding) ON (f.is_verified);
CREATE INDEX asset_value IF NOT EXISTS FOR (a:Asset) ON (a.value);
CREATE INDEX cookie_domain IF NOT EXISTS FOR (c:Cookie) ON (c.domain);
```

---

### 📥 Step 8.3 — Graph Ingestion

Use `MERGE` for all node and relationship creation (upsert semantics — safe to re-run):

```python
async def ingest_finding(session, finding: dict):
    affected_domain = urlparse(finding["affected_url"]).hostname
    await session.run("""
        MERGE (f:Finding {finding_id: $finding_id})
        SET f.type = $type,
            f.severity = $severity,
            f.is_verified = $is_verified,
            f.scan_id = $scan_id,
            f.affected_domain = $affected_domain
        WITH f
        MATCH (ep:Endpoint {endpoint_id: $endpoint_id})
        MERGE (ep)-[:HAS_FINDING]->(f)
    """, **finding, affected_domain=affected_domain)
```

---

### 🔗 Step 8.4 — Edge Inference Rules

```cypher
-- CONTROLS: takeover finding controls cookie domain
MATCH (f:Finding {type: 'subdomain_takeover', scan_id: $scan_id})
MATCH (c:Cookie)
WHERE c.domain ENDS WITH f.affected_domain
MERGE (f)-[:CONTROLS]->(c);

-- CHAINS_TO: only infer between findings sharing an asset
MATCH (f1:Finding {scan_id: $scan_id, type: 'subdomain_takeover'})
      -[:HAS_FINDING]-(ep1:Endpoint)-[:EXPOSES]-(a:Asset)
      -[:EXPOSES]-(ep2:Endpoint)-[:HAS_FINDING]-
      (f2:Finding {scan_id: $scan_id})
WHERE f2.type IN ['idor', 'privilege_escalation']
  AND f1 <> f2
MERGE (f1)-[:CHAINS_TO]->(f2);
```

> ⚠️ **Important:** Chain edges must only be inferred when findings are connected through shared assets, cookies, or credentials. Blanket `CHAINS_TO` between any takeover and any IDOR creates spurious chains.

---

### 🔍 Step 8.5 — Chain Detection Queries

```cypher
-- Chain 1: Subdomain Takeover → Cookie Hijack → Auth Bypass
MATCH path = (f1:Finding {type: 'subdomain_takeover', is_verified: true})
  -[:CONTROLS]->(c:Cookie)
  -[:AFFECTS_AUTH]->(ep:Endpoint)
  -[:HAS_FINDING]->(f2:Finding {is_verified: true})
WHERE f2.type IN ['idor', 'privilege_escalation', 'auth_bypass']
  AND f1.scan_id = $scan_id
RETURN path, f1.finding_id AS takeover_id, f2.finding_id AS impact_id,
       c.domain AS controlled_domain, ep.path AS affected_endpoint

-- Chain 2: JS Secret Leak → Account Takeover
MATCH path = (js:JSFile {has_secrets: true})
  -[:LEAKS]->(cred:Credential)
  -[:USES]->(ep:Endpoint)
  -[:HAS_FINDING]->(f:Finding {is_verified: true, scan_id: $scan_id})
RETURN path, js.url, cred.type, f.finding_id, f.severity
```

---

### 📈 Step 8.6 — Severity Escalation (Python-side)

```python
SEVERITY_RANK = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

def compute_chain_severity(finding_severities: list[str]) -> str:
    max_sev = max(finding_severities, key=lambda s: SEVERITY_RANK.get(s, 0))
    # A chain of 3+ medium findings escalates to high
    if SEVERITY_RANK[max_sev] < 3 and len(finding_severities) >= 3:
        return "high"
    return max_sev
```

---

### 💾 Step 8.7 — Chain Persistence

Detected chains written to `exploit_chains` in Postgres. `graph_path_ids` stores Neo4j node IDs for traceability. Combined severity computed per chain.

---

### 📄 Step 8.8 — Reporter Integration

`report.jobs` message includes `exploit_chains` list. Reporter fetches chain details from Attack Graph Engine API. New report section: **"Exploit Chains"** with step-by-step narrative.

---

### 🧪 Step 8.9 — Tests

- **Unit:** each edge inference rule with asset-connection requirement, severity escalation logic, domain extraction
- **Integration:** seed Neo4j with known finding data (subdomain takeover + shared asset + IDOR), verify chain is detected; verify unrelated findings do NOT produce a chain
- **Coverage ≥ 75%**

---

## 🏎️ Milestone 9 — Think Harder

**Purpose:** Add the Scenario Runner for multi-step behavioral testing — race conditions, privilege escalation, workflow bypass.

### ✅ Definition of Done

- Race condition on a local crAPI endpoint detected via state divergence signal
- Privilege escalation via role manipulation is flagged
- Workflow bypass correctly flags missing step enforcement
- `asyncio.gather()` approach confirmed as replaced — nuclei race or h2spacex used for all burst testing

### 🎯 Goals

- Single-packet attack implemented for genuine simultaneity
- Three-signal race outcome detection
- Connection warming before every burst
- Nuclei race templates as primary implementation path
- `h2spacex` for custom multi-body races

---

### 🔴 Step 9.1 — Why `asyncio.gather()` Is Not Enough

`asyncio.gather()` fires coroutines concurrently at the Python level, but each coroutine still opens and sends its own TCP connection independently. By the time all connections reach the server they're spread across tens to hundreds of milliseconds. **Most race condition windows are under 10ms.**

The correct technique is the **single-packet attack**: all request bytes are sent simultaneously except the final frame of each, which are all released together in a single TCP packet.

---

### 🎯 Step 9.2 — Primary Path: Nuclei Race Templates

ProjectDiscovery implemented the gate mechanism directly in nuclei's engine:

```yaml
# templates/race/transfer_double_spend.yaml
id: race-transfer-double-spend
info:
  name: Race Condition - Transfer Double Spend
  severity: high

http:
  - raw:
      - |
        POST /api/transfer HTTP/1.1
        Host: {{Hostname}}
        Cookie: {{session}}
        Content-Type: application/json

        {"amount": 100, "to": "{{target_account}}"}

    race: true
    race_count: 20

    matchers:
      - type: status
        status: [200]
```

**Session injection into nuclei race templates:**

```python
async def run_nuclei_race(
    template_path: str,
    target: str,
    session: BrowserSession | None,
    race_vars: dict,
) -> list[dict]:
    vars_args = []
    if session:
        cookie_str = format_cookies_for_nuclei(decrypt(session.cookies))
        vars_args += ["-var", f"session={cookie_str}"]
    for k, v in race_vars.items():
        vars_args += ["-var", f"{k}={v}"]

    proc = await asyncio.create_subprocess_exec(
        "nuclei", "-t", template_path, "-u", target,
        "-race", "-j", *vars_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
    return [json.loads(l) for l in stdout.decode().splitlines() if l.strip().startswith("{")]

def format_cookies_for_nuclei(cookies: list[dict]) -> str:
    # nuclei expects exactly: "name1=value1; name2=value2"
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)
```

---

### ⚔️ Step 9.3 — Secondary Path: `h2spacex` for Custom Multi-Body Races

Use when you need different request bodies per concurrent slot:

```python
from h2spacex import H2OnTlsConnection

async def single_packet_attack(
    hostname: str, port: int, requests: list[str]
) -> list[dict]:
    conn = H2OnTlsConnection(hostname=hostname, port_number=port)
    conn.setup_connection()
    conn.send_ping_frame()  # warm the connection

    stream_ids = []
    for req in requests:
        stream_id = conn.send_request(req, end_stream=False)
        stream_ids.append(stream_id)

    for stream_id in stream_ids:
        conn.send_end_stream(stream_id)

    return conn.read_responses(stream_ids)
```

> ⚠️ `h2spacex` requires raw socket access. Works in standard Docker. Will silently fail in AWS Fargate and some GCP Cloud Run configurations — documented in `infra/README.md`.

---

### 🔥 Step 9.4 — Connection Warming

Always warm the connection before any burst:

```python
async def warm_connection(client: httpx.AsyncClient, target_url: str, count: int = 3):
    for _ in range(count):
        try:
            await client.get(target_url, timeout=5.0)
        except Exception:
            pass
    await asyncio.sleep(0.1)  # 100ms settle — matches Turbo Intruder default
```

> ⚠️ Do not use `target_url.rsplit("/", 1)[0]` as the warmup target — a different endpoint may have side effects (rate limit consumption, WAF rule triggers, logging anomalies).

---

### 🔎 Step 9.5 — Three-Signal Race Outcome Detector

```python
import statistics
from collections import Counter

class RaceOutcomeDetector:
    def detect(self, pre_state: dict, responses: list, post_state: dict) -> RaceResult:

        # Signal 1: State divergence
        if pre_state != post_state:
            delta = self._compute_delta(pre_state, post_state)
            if delta.is_anomalous():
                return RaceResult(fired=True, signal="state_divergence", detail=delta)

        # Signal 2: Response anomaly — minority response indicates race fired
        status_counts = Counter(r.status_code for r in responses)
        if len(status_counts) > 1:
            minority = min(status_counts, key=status_counts.get)
            return RaceResult(fired=True, signal="response_divergence",
                              detail=f"minority status: {minority}")

        # Signal 3: Timing outlier — > 3 sigma indicates lock contention
        times = [r.elapsed.total_seconds() for r in responses]
        if len(times) > 2:
            mean, std = statistics.mean(times), statistics.stdev(times)
            outliers = [t for t in times if t > mean + 3 * std]
            if outliers:
                return RaceResult(fired=True, signal="timing_outlier",
                                  detail=f"outlier times: {outliers}")

        return RaceResult(fired=False)
```

---

### 📋 Step 9.6 — Updated Scenario YAML Schema

```yaml
name: wallet_double_spend
description: Test for race condition on transfer endpoint
requires_auth: true
race_strategy: single_packet    # "single_packet" | "last_byte_sync" | "parallel"
connection_warmup: true
warmup_count: 3

steps:
  - action: observe
    endpoint: GET /api/balance
    capture_as: pre_balance

  - action: concurrent_http
    count: 20
    race_strategy: "{{race_strategy}}"
    request:
      method: POST
      path: /api/transfer
      body:
        amount: 100
        to: user_b

  - action: observe
    endpoint: GET /api/balance
    capture_as: post_balance

  - action: assert_race_outcome
    pre_state: pre_balance
    post_state: post_balance
    responses: "{{burst_responses}}"
    signals: [state_divergence, response_divergence, timing_outlier]
```

---

### 👑 Step 9.7 — Privilege Escalation Scenarios

`switch_user` step: load secondary browser session via `storage_state`. Access resource requiring higher privilege role. Assert access is denied; flag if granted.

---

### 🚧 Step 9.8 — Workflow Bypass Scenarios

Multi-step flows: skip intermediate steps, go directly to final step. Assert final step requires prior steps; flag if it doesn't.

---

### 🔗 Step 9.9 — Stage 7 Pipeline Integration

Engine publishes `scenario.request` to `scenario.jobs` after Stage 6. Results flow into verification queue (Stage 8). Feature flag `ENABLE_SCENARIO_RUNNER` gates this stage.

---

### 📚 Step 9.10 — Built-in Scenario Library

| Scenario | Description |
|---|---|
| `race_transfer.yaml` | Double spend on financial endpoints |
| `priv_escalation_role.yaml` | Role parameter manipulation |
| `workflow_skip_payment.yaml` | Checkout step skipping |

---

### 🧪 Step 9.11 — Tests

- **Unit:** scenario YAML parser with new fields, warmup helper, race outcome detector (all three signals), cookie format function for nuclei
- **Integration:** run race scenario against crAPI; assert state divergence is detected
- **Coverage ≥ 75%**

---

## 🤖 Milestone 10 — The Machine

**Purpose:** Add the AI Hypothesis Engine and complete all final integration, hardening, and production-readiness work.

### ✅ Definition of Done

- AI worker produces at least one hypothesis that passes verification on a known-vulnerable test target
- Token budget prevents context overflow on a large scan (verified by log output)
- Full end-to-end smoke test passes in CI
- All services have ≥ 80% test coverage
- All 5 scope enforcement layers verified by automated test
- DLQ management API working and documented
- Operational runbook complete
- `mc anonymous set download` confirmed absent from all MinIO init scripts

### 🎯 Goals

- Ollama structured outputs with three-layer reliability
- Token budget management preventing context overflow
- Complete system hardening pass
- Full observability and alerting operational
- End-to-end smoke test in CI

---

### 🦙 Step 10.1 — Ollama Integration

```yaml
ollama:
  image: ollama/ollama
  volumes:
    - ollama_models:/root/.ollama
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
    interval: 10s
    timeout: 5s
    retries: 10
    start_period: 30s
```

Pull model at startup via init script. Configurable model via environment variable — default `llama3.1:8b`, alternatives: `mistral:7b`, `deepseek-coder-v2`.

---

### 🧱 Step 10.2 — Structured Output Strategy

Use schema-constrained generation with Pydantic validation:

```python
from pydantic import BaseModel, Field
from typing import Literal

class VulnerabilityHypothesis(BaseModel):
    hypothesis: str
    reasoning: str
    affected_endpoint: str
    suggested_method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    suggested_payload: dict
    confidence: float = Field(ge=0.0, le=1.0)
    vulnerability_class: Literal[
        "idor", "privilege_escalation", "ssrf", "xss",
        "sqli", "auth_bypass", "business_logic", "other"
    ]

class HypothesisList(BaseModel):
    hypotheses: list[VulnerabilityHypothesis]
```

---

### 🔒 Step 10.3 — Three-Layer Reliability Stack

Even schema-constrained output fails 2–6% of the time. At scan volume this matters:

```python
async def generate_hypotheses(context: ScanContext, max_retries: int = 3):
    schema = HypothesisList.model_json_schema()
    prompt = build_hypothesis_prompt(context)

    for attempt in range(max_retries):
        try:
            # Layer 1: Schema-constrained generation + temperature=0 for determinism
            response = ollama.chat(
                model="llama3.1:8b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                format=schema,
                options={"temperature": 0},
            )
            raw = response["message"]["content"]

            # Layer 2: Strip markdown fences that leaked through
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())

            # Layer 3: Pydantic validation
            result = HypothesisList.model_validate_json(raw)
            return [h for h in result.hypotheses if h.confidence >= 0.6]

        except (ValidationError, json.JSONDecodeError) as e:
            logger.warning(f"AI output validation failed (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                logger.error("AI worker exhausted retries — returning empty list")
                return []  # Fail open: no hypotheses, not a crash
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return []
```

> 💡 **Alternative:** use the `instructor` library — it wraps Ollama with `response_model`, automatic retries, and backoff in one line:

```python
import instructor
client = instructor.from_provider("ollama/llama3.1:8b", mode=instructor.Mode.JSON, async_client=True)

result = await client.create(
    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
    response_model=HypothesisList,
    max_retries=3,
    timeout=60.0,
)
```

Use `instructor` as the default — only use the manual loop if you want to avoid the dependency.

---

### 💰 Step 10.4 — Token Budget Management

`llama3.1:8b` default context window is 8k tokens. Without budget management, large scans silently overflow and produce garbage output.

```python
MAX_PROMPT_TOKENS = 6000  # reserve headroom for system prompt + response

def estimate_tokens(text: str, contains_code: bool = False) -> int:
    divisor = 3 if contains_code else 4
    return len(text) // divisor

def build_hypothesis_prompt(ctx: ScanContext) -> str:
    budget = MAX_PROMPT_TOKENS
    sections = []

    tech_section = f"TECH STACK: {json.dumps(ctx.tech_stack)}"
    budget -= estimate_tokens(tech_section, contains_code=True)
    sections.append(tech_section)

    endpoint_lines = []
    for ep in ctx.endpoints:
        line = format_endpoint(ep)
        cost = estimate_tokens(line, contains_code=True)
        if budget - cost < 500:  # reserve for findings + JS
            break
        endpoint_lines.append(line)
        budget -= cost
    sections.append("ENDPOINTS:\n" + "\n".join(endpoint_lines))

    return "\n\n".join(sections)
```

**What to include vs. exclude in context bundle:**

| ✅ Include | ❌ Exclude |
|---|---|
| Endpoint list with methods + params | Full response bodies |
| Response code anomalies (500s, unexpected 200s) | Binary/image content |
| Tech stack fingerprint | Out-of-scope assets |
| Existing verified findings summary | Full JS files |
| Short JS snippets with secrets/sinks | Duplicate endpoint variants |

---

### 📝 Step 10.5 — System Prompt Design

```
SYSTEM_PROMPT = """You are a security researcher analyzing web application scan artifacts.
Your task is to identify vulnerabilities that automated scanners may have missed.

Rules:
- Only propose hypotheses where you observe a specific signal
- A signal is: missing auth header, user-controlled parameters near privileged operations,
  inconsistent responses between similar endpoints, state-changing actions without CSRF protection
- Do NOT propose generic "check for XSS" hypotheses without a specific endpoint and parameter
- Set confidence below 0.5 if guessing; only above 0.7 if you see a clear signal
- If you cannot find at least one specific, well-reasoned hypothesis, return an empty list
- Respond ONLY with valid JSON matching the provided schema. No preamble, no explanation."""
```

---

### 🔗 Step 10.6 — Hypothesis-to-Verify Pipeline

The AI worker **never writes to findings directly**. Every hypothesis becomes a `verify.jobs` message. The Exploit Verifier confirms or rejects it deterministically. Verified hypotheses are attributed with `source = ai_hypothesis` in the findings table.

---

### 🌐 Step 10.7 — API Gateway

`api-gateway` on `:8000`. Routes: `/scraper/*`, `/engine/*`, `/reporter/*`, `/graph/*`. Redis-backed rate limiting. API key authentication (header: `X-API-Key`).

---

### 🛡️ Step 10.8 — Full Hardening Pass

Audit and verify all **five scope enforcement layers**:

| Layer | Description |
|---|---|
| 1 | Stage 0 `ScopeFilter` (fatal) |
| 2 | Every asset-producing stage validates against `ScopeFilter` |
| 3 | Browser Worker Playwright route intercept blocks out-of-scope navigation |
| 4 | Scenario Runner validates all HTTP targets pre-request |
| 5 | Post-run audit — findings with out-of-scope URLs quarantined |

Additional hardening: verify session data encrypted at rest, confirm all secret loading from Vault/env, add per-program concurrency caps (Redis semaphores), add per-target request rate limiting (Redis token bucket).

---

### 🚨 Step 10.9 — Alerting Rules

| Alert | Condition |
|---|---|
| Scan stuck | `scans.status = running AND started_at < NOW() - 2 hours` |
| DLQ growing | Any DLQ message count > 10 |
| False positive spike | Rolling FP rate > 40% |
| Worker down | No Celery heartbeat in 60s |
| Scope violation | Any finding quarantined for out-of-scope URL |

---

### 🔧 Step 10.10 — DLQ Operations

```
GET  /api/v1/queue/dlq/inspect     — view DLQ contents
POST /api/v1/queue/dlq/replay      — replay specific message
```

Grafana panel showing DLQ depth per queue.

---

### 🧪 Step 10.11 — Coverage Final Push

Audit all services. Reach **≥ 80% coverage** across the board. Add missing integration tests for cross-service flows.

---

### 🔬 Step 10.12 — End-to-End Smoke Test

Automated test in CI: trigger scrape → wait for scan → wait for report → download report → assert report contains at least one verified finding with evidence in MinIO. Runs on every push to `main`.

---

### 📖 Step 10.13 — Operational Runbook

Document:
- How to start the system from cold boot
- How to trigger a scan manually
- How to inspect and replay DLQ messages
- How to add a new platform collector
- How to write a new YAML scenario
- Known operational constraints (`h2spacex` raw socket, Vault dev mode limitations)
- How to rotate Vault secrets

---

## 📅 Summary Timeline

| Milestone | Rough Effort | What You'll Have |
|---|---|---|
| M1 — Solid Ground | 1–2 weeks | Running infra, project skeleton, CI |
| M2 — Eyes Open | 2–3 weeks | Real programs in DB from HackerOne |
| M3 — First Strike | 3–5 weeks | Real unauthenticated findings |
| M4 — Read the Room | 2–3 weeks | Downloadable PDF/DOCX reports |
| **M1–M4 checkpoint** | **~8–13 weeks** | **✅ Working product. Start scanning.** |
| M5 — Get Inside | 3–4 weeks | Authenticated scanning |
| M6 — Break the Logic | 3–4 weeks | API fuzzing + JS analysis |
| M7 — Prove It | 3–4 weeks | Evidence-verified findings only |
| M8 — Connect the Dots | 2–3 weeks | Exploit chains in reports |
| M9 — Think Harder | 3–4 weeks | Race conditions, workflow bypass |
| M10 — The Machine | 3–5 weeks | AI hypotheses, full hardening |
| **M5–M10 checkpoint** | **~17–24 weeks** | **🚀 Production-grade platform** |
| **Total (solo, learning-as-you-go)** | **6–9 months** | **The complete machine** |

---

## 💡 Key Principles

> **Never leave a milestone in a broken state.** At the end of every milestone you have a working system. If life interrupts at M6, you still have a real, useful tool from M1–M5.

> **Continued planning is itself a risk.** The remaining gaps after this document are the kind that only surface in code. The next thing you learn will come from running the system, not from reading about it.

> **Build horizontally before going deeper.** Reach a working state at each milestone before adding capability. A fully working M4 is worth more than a half-built M7.