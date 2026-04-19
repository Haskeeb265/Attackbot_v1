# Attackbot_v1 — Complete Codebase Deep Dive

> **Branch:** `M4_ReadTheRoom`
> **Language:** Python 3.12
> **Framework:** FastAPI + Celery + SQLAlchemy (async) + Pydantic v2
> **Architecture:** Event-driven microservices with RabbitMQ message bus

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Infrastructure Layer](#3-infrastructure-layer)
4. [The Scraper Service](#4-the-scraper-service)
5. [The Core Engine Service](#5-the-core-engine-service)
6. [The Scanning Pipeline (Stages 0–10)](#6-the-scanning-pipeline-stages-010)
7. [The Reporter Service](#7-the-reporter-service)
8. [The API Gateway](#8-the-api-gateway)
9. [Attack Graph Engine](#9-attack-graph-engine)
10. [Specialist Workers (Future)](#10-specialist-workers-future)
11. [Shared Infrastructure Code](#11-shared-infrastructure-code)
12. [Message Contracts & Queue Topology](#12-message-contracts--queue-topology)
13. [Database Schema](#13-database-schema)
14. [Exception Hierarchy](#14-exception-hierarchy)
15. [Configuration System](#15-configuration-system)
16. [Observability Stack](#16-observability-stack)
17. [Startup Sequence](#17-startup-sequence)
18. [M4 Implementation Plan](#18-m4-implementation-plan)
19. [Key Design Decisions](#19-key-design-decisions)
20. [File Index](#20-file-index)

---

## 1. Executive Summary

**Attackbot_v1** is an automated security scanning platform that:

1. **Scrapes** bug bounty programs from HackerOne (and eventually other platforms)
2. **Scans** each program's in-scope assets through a multi-stage vulnerability pipeline
3. **Reports** findings as downloadable PDF/DOCX documents

The system is designed to run autonomously: it periodically scrapes program metadata, queues scan jobs for programs due for rescan, runs a 10-stage scanning pipeline using industry-standard tools (subfinder, nuclei, ffuf, etc.), deduplicates findings, persists them to PostgreSQL, and generates downloadable reports stored in MinIO.

### What makes it interesting

- **Scope-first safety**: The pipeline refuses to scan without a defined scope and validates every discovered URL against it. Out-of-scope always wins.
- **Graceful degradation**: Most pipeline stages are non-fatal. If nuclei fails, the scan still produces results from other stages and is marked `partial` instead of failed.
- **Event-driven decoupling**: Services communicate exclusively through RabbitMQ queues with a versioned envelope schema. No service calls another service's database directly.
- **Dead-letter queues (DLQ)**: Every queue has a paired DLQ. Failed messages are routed there automatically for operator inspection.

---

## 2. Architecture Overview

```
                         +------------------+
                         |   API Gateway    |  :8000
                         | (M1 skeleton)    |
                         +--------+---------+
                                  |
                    probes health of all services
                                  |
         +------------+-----------+-----------+------------+
         |            |                       |            |
+--------v---+  +-----v------+  +-------------v--+  +-----v-----------+
|  Scraper   |  | Core Engine|  |   Reporter     |  | Attack Graph    |
|  :8001     |  |   :8002    |  |   :8003        |  | Engine :8006    |
+-----+------+  +-----+------+  +-------+--------+  +-----------------+
      |               |                 |
      | publish       | publish         | consume
      | scan.jobs     | report.jobs     | report.jobs
      v               v                 v
+-----+---------------+--+--------------+---------+
|                  RabbitMQ                        |
|  scan.jobs | report.jobs | reports.completed     |
|  + 7 more queues for specialist workers          |
+---------+-------------------+--------------------+
          |                   |
   +------v------+    +------v---------+
   | Core Worker |    | Reporter Worker|
   | (Celery)    |    | (Celery)       |
   +------+------+    +------+---------+
          |                   |
     runs 10-stage       generates PDF/DOCX
     scan pipeline       uploads to MinIO
          |                   |
  +-------v---+  +-----------v---+  +--------+  +-------+  +------+
  | PostgreSQL|  |    MinIO      |  | Redis  |  | Neo4j |  | Vault|
  |  (data)   |  | (artifacts)  |  | (locks)|  |(graph)|  |(keys)|
  +-----------+  +---------------+  +--------+  +-------+  +------+
```

### Service Inventory

| Service | Port | Role | Status |
|---------|------|------|--------|
| `api-gateway` | 8000 | Reverse proxy / health aggregator | M1 skeleton (health only) |
| `scraper` | 8001 | Scrapes HackerOne programs, publishes scan jobs | Fully implemented |
| `core-engine` | 8002 | Scan orchestration API, watchdog | Fully implemented |
| `core-worker` | — | Celery worker executing 10-stage pipeline | Fully implemented |
| `reporter` | 8003 | Report listing, download, generation trigger | Fully implemented (M4) |
| `reporter-worker` | — | Celery worker generating PDF/DOCX reports | Fully implemented (M4) |
| `attack-graph-engine` | 8006 | Neo4j-backed exploit chain analysis | Skeleton |
| `browser-worker` | — | Headless browser-based scanning | Skeleton (M5) |
| `api-fuzzer-worker` | — | API endpoint fuzzing | Skeleton |
| `js-analysis-worker` | — | Deep JS static analysis | Skeleton |
| `scenario-runner` | — | Multi-step attack scenarios | Skeleton |
| `exploit-verifier` | — | Automated exploit verification | Skeleton |
| `ai-analysis-worker` | — | AI-powered vulnerability analysis | Skeleton |

---

## 3. Infrastructure Layer

All infrastructure runs via Docker Compose (`infra/docker-compose.yml`), organized in 6 startup phases.

### Phase 1 — Stateful Infrastructure (no dependencies)

| Component | Image | Purpose | Resource Limits |
|-----------|-------|---------|-----------------|
| **PostgreSQL 16** | `postgres:16` | Primary relational database. All programs, scans, findings, reports | 1 CPU, 1 GB |
| **Redis 7** | `redis:7-alpine` | Distributed locking (scan concurrency, scrape locks) | 0.5 CPU, 256 MB |
| **RabbitMQ 3** | `rabbitmq:3-management` | Message bus for all inter-service communication | 1 CPU, 512 MB |
| **Neo4j 5** | `neo4j:5-community` | Graph database for attack chains (exploit chain modeling) | 1 CPU, 1 GB |
| **MinIO** | `minio/minio` | S3-compatible object storage for reports, evidence, JS assets | 0.5 CPU, 512 MB |
| **Vault 1.15** | `hashicorp/vault:1.15` | Secrets management (dev mode — **non-persistent** across restarts) | 0.5 CPU, 256 MB |

### Phase 2 — One-Shot Init Services

| Service | Purpose |
|---------|---------|
| `migrate` | Runs Alembic migrations against PostgreSQL |
| `minio-init` | Creates buckets: `reports`, `evidence`, `js-assets`, `summaries` |
| `vault-init` | Seeds placeholder secrets in Vault KV store |

**Critical security note:** `minio-init` intentionally does NOT set `mc anonymous set download`. All file access MUST go through pre-signed URLs via the Reporter API.

### Phase 3–6 — Application Services & Workers

Services start in dependency order. Each service has a health check that must pass before dependent services start.

---

## 4. The Scraper Service

**File:** `backend/services/scraper/main.py` (430 lines)
**Port:** 8001

The Scraper is responsible for discovering bug bounty programs and making them available for scanning.

### What it does

1. **Scrapes HackerOne** via their API v1 (HTTP Basic Auth, paginated)
2. **Normalizes** program metadata into a canonical `Program` model
3. **Parses scopes** (domains, wildcards, URLs, IPs) into structured `ProgramScope` objects
4. **Upserts** programs into PostgreSQL
5. **Publishes scan jobs** for programs due for rescan

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/health` | Health check (DB, Redis, RabbitMQ, scheduler, credentials) |
| `POST` | `/api/v1/scrape/trigger` | Trigger immediate scrape for a platform (background task) |
| `POST` | `/api/v1/scan-jobs/trigger` | Trigger immediate scan job publish batch |
| `GET` | `/api/v1/programs` | List programs (paginated, filterable by platform/active status) |
| `GET` | `/api/v1/programs/{id}` | Get single program details |
| `GET` | `/api/v1/programs/{id}/scope` | Get program scope (in_scope / out_of_scope) |

### The HackerOne Collector

**File:** `backend/services/scraper/collectors/hackerone.py` (228 lines)

The collector is **intentionally synchronous** (uses `requests` library). It's always invoked via `loop.run_in_executor()` to avoid blocking the async event loop.

Key behaviors:
- **Auto-retry on 429**: Respects `Retry-After` header, retries up to `max_retries` times
- **Auth failure detection**: Raises `CollectorAuthError` on 401/403
- **Pagination**: Fetches all pages from paginated endpoints
- **Scope mapping**: Maps HackerOne asset types (URL, WILDCARD, DOMAIN, IP_ADDRESS, etc.) to canonical types

```
HackerOne API types → Canonical types:
  URL         → url
  WILDCARD    → wildcard_domain
  DOMAIN      → domain
  IP_ADDRESS  → ip_range
  CIDR        → ip_range
  ANDROID/IOS → mobile_app
  API         → api
  SOURCE_CODE → api
  OTHER       → url
```

### Scheduled Jobs (APScheduler)

| Job | Interval | Purpose |
|-----|----------|---------|
| `scrape_hackerone` | Configurable (env) | Scrape HackerOne program listing + details |
| `reconciler` | Every 5 min | Re-attempt failed scan job publishes |
| `scan_publish_batch` | Configurable | Publish bounded batch of scan jobs for due programs |

### The Reconciler

**File:** `backend/services/scraper/reconciler.py` (102 lines)

The Reconciler is the **recovery path** for publish failures. If RabbitMQ was down when a scan job should have been published, the program's `queued_for_scan` flag remains `True`. The Reconciler:

1. Queries for programs with `queued_for_scan=True`
2. Fetches their full scope
3. Re-attempts publish to `scan.jobs`
4. On success, calls `clear_queued()` — the **only** component allowed to clear this flag

### Concurrency Control

The scraper uses **Redis distributed locks** per platform to prevent concurrent scrapes:
```
Lock key: scraper:lock:{platform}
TTL: platform_lock_ttl_seconds (configurable)
Behavior: Non-blocking acquire — if lock held, scrape is skipped
```

---

## 5. The Core Engine Service

**File:** `backend/services/core_engine/main.py` (472 lines)
**Port:** 8002

The Core Engine is the brain of the scanning system. It provides the scan management API and orchestrates the Celery worker.

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/health` | Health (DB, Redis, RabbitMQ, MinIO, toolchain, scheduler) |
| `POST` | `/api/v1/scans/start` | Start a new scan (fetches program from Scraper API) |
| `GET` | `/api/v1/scans` | List recent scans |
| `GET` | `/api/v1/scans/{scan_id}` | Get scan details |
| `GET` | `/api/v1/scans/{scan_id}/findings` | Get findings for a scan |
| `GET` | `/api/v1/scans/{scan_id}/findings/{id}/evidence` | Get evidence for a finding (used by Reporter) |
| `GET` | `/api/v1/queue/dlq/inspect` | Inspect dead-letter queue messages |

### Scan Lifecycle

```
User/Scraper triggers scan
        │
        ▼
  _build_payload_from_scraper()
  ─ Fetches program + scope from Scraper API
        │
        ▼
  _reserve_scan_id()
  ─ Creates scan row in DB (status: pending)
        │
        ▼
  _enqueue_scan()
  ─ Builds MessageEnvelope
  ─ Publishes to scan.jobs queue
        │
        ▼
  Core Worker picks up message
  ─ Deserializes envelope
  ─ Validates schema version
  ─ Calls run_scan_task()
        │
        ▼
  10-stage pipeline executes
  (see next section)
```

### The Watchdog

An APScheduler job (`recover_stuck_scans`) runs every 5 minutes and:
- Finds scans with `status='running'` that have been running longer than `stale_threshold` (2 hours)
- Marks them as `failed_internal` so they can be retried

### The Celery Worker

**File:** `backend/services/core_engine/worker.py` (102 lines)

```python
# Key configuration:
worker_prefetch_multiplier = 1   # One task at a time
max_retries = 0                  # Watchdog handles retries, not Celery
broker = RabbitMQ
queue = scan.jobs
```

The worker deserializes the `MessageEnvelope`, validates the schema version (rejects unknown major versions), extracts the `ScanJobsPayload`, and calls `run_scan_task()`.

---

## 6. The Scanning Pipeline (Stages 0–10)

**File:** `backend/services/core_engine/scan_task.py` (384 lines)

This is the heart of Attackbot. The pipeline runs 10 stages with intelligent parallelism and graceful degradation.

### Pipeline Flow

```
              Stage 0: Scope Filter (FATAL)
                        │
                        ▼
              Stage 1: Asset Discovery
              (subfinder → alterx → dnsx → httpx)
                        │
                        ▼
              Stage 2: Fingerprinting
              (httpx tech-detect enrichment)
                        │
                ┌───────┴───────┐
                ▼               ▼
         Stage 3:          Stage 4:
         Enumeration       Nuclei Scan
         (ffuf + wayback)  (template vuln scan)
                │
          ┌─────┴─────┐
          ▼           ▼
     Stage 5:     Stage 6:
     Web Vuln     JS Secrets
     Tests        (regex scan)
     (XSS, CORS)
                        │
                        ▼
              Stage 10: Aggregation
              (dedup, persist, publish report.jobs)
```

### Concurrency Control

Before the pipeline starts, it acquires a **Redis distributed lock** per scan:
```
Lock key: scan:{scan_id}
TTL: 14,400 seconds (4 hours)
Purpose: Prevents duplicate execution if a message is redelivered
```

### Stage Details

#### Stage 0 — Scope Filter (FATAL)

**File:** `backend/services/core_engine/pipeline/scope_filter.py` (196 lines)

The `ScopeFilter` class is built from the scan message's scope definition. It evaluates whether a URL, domain, or IP is within scope.

**Fatal contract:** If scope is empty, raises `ScanError` and aborts. The system will NEVER scan without a defined scope.

Matching rules:
- **Exact match**: `example.com` matches `example.com` only
- **Wildcard**: `*.example.com` matches `sub.example.com` but NOT `example.com`
- **Domain root** (from API): `example.com` matches both `example.com` AND `sub.example.com`
- **Out-of-scope always wins**: If a target matches both in-scope and out-of-scope rules, it's excluded
- **CIDR support**: IP ranges can be specified as scope rules

#### Stage 1 — Asset Discovery

**File:** `backend/services/core_engine/pipeline/asset_discovery.py` (483 lines)

Discovers live web assets within scope using a 4-step tool chain:

```
Step 1: subfinder
  ─ Passive subdomain enumeration
  ─ Uses provider config at /app/subfinder-config/provider-config.yaml
  ─ Timeout: 600s (configurable)
  ─ Non-fatal: if subfinder fails, seed domain is still probed

Step 2: alterx
  ─ Permutation-based subdomain generation
  ─ Only runs when subfinder produced results
  ─ Generates variations like dev.example.com, staging.example.com
  ─ Timeout: 300s

Step 3: dnsx
  ─ DNS resolution of all candidate subdomains
  ─ Filters to only live (resolvable) domains
  ─ Timeout: 900s

Step 4: httpx
  ─ HTTP probing of live domains
  ─ Detects technologies, status codes, page titles
  ─ Timeout: 600s
```

**Seed-first behavior:**
- Domain and wildcard_domain rules are always seed candidates
- URL rules are seed candidates only when HTTP(S) and domain-led by in-scope domain rules
- Explicit in-scope targets are also probed directly (so narrow scope entries aren't lost when passive enumeration is sparse)

**Deduplication:** Assets are deduped by canonical origin key (`scheme://host:port`). First-seen wins for all fields; later duplicates only fill missing/null fields.

**Output:** `list[DiscoveredAsset]` — each has `asset_type`, `value` (URL), `http_status`, `technology_stack`, `waf_detected`

#### Stage 2 — Fingerprinting

**File:** `backend/services/core_engine/pipeline/fingerprinting.py` (123 lines)

Enriches Stage 1 assets with detailed tech stack and WAF info. Runs httpx again with extended fingerprinting options.

- Updates `technology_stack` with: technologies, title, content_type, server
- Detects WAF presence using keyword matching (Cloudflare, Akamai, F5, Sucuri, Imperva, Barracuda, Fortiweb)

**WAF Detection Keywords** (from `waf_utils.py`):
```
waf, cloudflare, akamai, f5, sucuri, imperva, barracuda, fortiweb
```

**Output:** Same `list[DiscoveredAsset]` objects, now enriched in-place

#### Stage 3 — Enumeration (runs in parallel with Stage 4)

**File:** `backend/services/core_engine/pipeline/enumeration.py` (311 lines)

Discovers endpoints and JavaScript files for each asset.

**ffuf — Directory/Path Discovery:**
- Fuzzes `{base_url}/FUZZ` with wordlist
- Matches status codes: 200, 201, 204, 301, 302, 307, 401, 403
- 50 threads, 10s timeout per request
- Wordlist: `/wordlists/common.txt` (overridable via `E2E_FFUF_WORDLIST`)

**waybackurls — Historical URL Discovery:**
- Fetches historical URLs from Wayback Machine for each domain
- Scope-filtered: only in-scope URLs are kept
- Skippable via `E2E_SKIP_WAYBACKURLS` env var

**JS Download & Storage:**
- Discovers `.js` files from enumerated endpoints
- Downloads each (with redirect following, scope validation on final URL)
- Max file size: 5 MB
- Hashes content (SHA-256) and uploads to MinIO `js-assets` bucket
- Best-effort: download/upload failures are non-fatal

**Output:** `(list[DiscoveredEndpoint], list[DiscoveredJsAsset])`

#### Stage 4 — Nuclei Scan (runs in parallel with Stage 3)

**File:** `backend/services/core_engine/pipeline/nuclei_scan.py` (155 lines)

Runs Nuclei template-based vulnerability scanning against all in-scope assets.

Configuration:
- Rate limit: 150 req/s
- Bulk size: 25
- Concurrency: 25
- Timeout: 3600s (1 hour)
- Excludes `headless` tagged templates (browser-based scanning is M5)

**Exit code handling:**
- Exit code 2: Classified as startup failure (templates missing, target resolution, empty target list)
- Other codes: Logged as subprocess failure

**Output:** `list[FindingCandidate]` with severity mapped from nuclei's severity levels

**CVSS mapping** (from `cvss.py`):
```
critical → 9.8
high     → 7.5
medium   → 5.3
low      → 3.1
info     → 0.0
```

#### Stage 5 — Web Vulnerability Tests (runs after Stage 3)

**File:** `backend/services/core_engine/pipeline/web_vuln_tests.py` (222 lines)

Targeted vulnerability tests on discovered endpoints.

**Always enabled:**
- **Reflected XSS**: Injects 3 payloads into each query parameter (up to 10 params per endpoint). Checks if payload is reflected verbatim in response.
- **CORS Misconfiguration**: Tests with 3 evil origins (`https://evil.com`, `null`, `https://attacker.example.com`). Flags when server reflects origin AND sets `Access-Control-Allow-Credentials: true`.
- **Sensitive Path Detection** (passive): Checks discovered paths against known sensitive paths (`.env`, `.git/HEAD`, `.git/config`).

**Feature-flagged (disabled by default):**
- **CRLF Injection**: Tests for header injection via `%0d%0a`
- **SQLi**: Planned for M6+
- **SSRF**: Planned for M6+

**Output:** `list[FindingCandidate]`

#### Stage 6 — JS Secrets Scanning (runs after Stage 3)

**File:** `backend/services/core_engine/pipeline/js_secrets.py` (95 lines)

Regex-based secret detection in downloaded JavaScript files. Downloads each JS file from MinIO and scans with 13 patterns:

| Pattern | Label | Severity |
|---------|-------|----------|
| `AIza[0-9A-Za-z\-_]{35}` | Google API Key | High |
| `AAAA[A-Za-z0-9_\-]{7}:...` | Firebase Server Key | High |
| `sk-[a-zA-Z0-9]{48}` | OpenAI API Key | Critical |
| `xox[baprs]-...` | Slack Token | High |
| `api[_-]?key=...` | Generic API Key | Medium |
| `password=...` | Hardcoded Password | High |
| `secret[_-]?key=...` | Hardcoded Secret Key | High |
| `eyJ...` (JWT format) | JWT Token | Medium |
| `-----BEGIN ... PRIVATE KEY-----` | Private Key | Critical |
| `ghp_[A-Za-z0-9]{36}` | GitHub PAT | Critical |
| `AKIA[0-9A-Z]{16}` | AWS Access Key ID | Critical |
| AWS Secret Access Key pattern | AWS Secret Access Key | Critical |

**Output:** `list[FindingCandidate]` — one finding per pattern per JS file (first match only)

#### Stage 10 — Aggregation (FATAL)

**File:** `backend/services/core_engine/pipeline/aggregator.py` (134 lines)

The final stage that wraps up the scan:

1. **Deduplication**: Computes SHA-256 hash of `vulnerability_type|normalized_url|parameter|payload[:100]` for each finding. Removes duplicates.
2. **Persistence**: Saves deduplicated findings to PostgreSQL via `ScanRepository.save_findings()`
3. **Severity breakdown**: Counts findings by severity (critical, high, medium, low, info)
4. **Status determination**: `completed` if no stage errors, `partial` if any non-fatal stage failed
5. **Scan finalization**: Updates scan row with final status, finding count, severity breakdown
6. **Report handoff**: Publishes `scan.completed` message to `report.jobs` queue

**Output:** Severity breakdown dict

---

## 7. The Reporter Service

**File:** `backend/services/reporter/main.py` (373 lines)
**Port:** 8003

The Reporter generates downloadable PDF/DOCX vulnerability reports.

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/health` | Health (DB, RabbitMQ, MinIO, upstream services, scheduler) |
| `GET` | `/api/v1/reports` | List reports (paginated, filterable by scan_id/status) |
| `GET` | `/api/v1/reports/{id}` | Get report details |
| `GET` | `/api/v1/scans/{scan_id}/reports` | Get all reports for a scan |
| `GET` | `/api/v1/reports/{id}/download` | Get pre-signed download URL |
| `POST` | `/api/v1/reports/generate` | Manually trigger report generation |

### Report Download Flow

```
Client requests download
        │
        ▼
  Check report exists (404 if not)
        │
        ▼
  Check status is terminal (409 if generating/failed)
        │
        ▼
  Check storage_path exists (409 if missing)
        │
        ▼
  Generate MinIO pre-signed URL
  (expires in report_presign_expiry_seconds, default 900s)
        │
        ▼
  Return { download_url, expires_in_seconds }
```

### Report Generation Flow

```
POST /reports/generate { scan_id, formats_requested }
        │
        ▼
  Fetch scan from Core Engine API
  ─ Must be completed or partial
        │
        ▼
  Create/reset report rows in DB
  (one per format: pdf, docx)
        │
        ▼
  Build ReportJobsPayload
  ─ Include severity breakdown, report_ids, formats
        │
        ▼
  Publish to report.jobs queue
        │
        ▼
  Reporter Worker picks up
  ─ Validates envelope (event_type, schema_version)
  ─ Enqueues Celery task
        │
        ▼
  process_report_envelope_sync()
  ─ Generates PDF/DOCX
  ─ Uploads to MinIO
  ─ Updates report status in DB
```

### The Reporter Worker

**File:** `backend/services/reporter/worker.py` (230 lines)

A Celery worker that consumes from `report.jobs` via a **raw Kombu consumer** (not Celery's native task routing). This is because the Core Engine publishes plain JSON envelopes, not Celery task messages.

The worker:
1. Receives raw message from `report.jobs`
2. Validates the envelope (event_type must be `scan.completed`, major version must be 1)
3. Parses the `ReportJobsPayload`
4. Enqueues a Celery task on `reporter.worker.tasks` queue
5. The Celery task calls `process_report_envelope_sync()`

**Retry strategy:** Configurable backoff (default: 60s, 300s, 600s). After `max_retries` (3), the message is published to `report.jobs.dlq`.

### Report Watchdog

Recovers stale reports (stuck in `generating` status for > 30 minutes) every 5 minutes.

### Prometheus Metrics

The Reporter exposes metrics via `prometheus_fastapi_instrumentator`:
- `download_requests_total` (labeled by status: success, not_found, not_ready, etc.)
- `presign_duration_seconds` (histogram of pre-signed URL generation time)

---

## 8. The API Gateway

**File:** `backend/services/api_gateway/main.py` (75 lines)
**Port:** 8000

Currently an M1 skeleton. Only provides a health aggregation endpoint that probes all upstream services.

### Health Aggregation

```python
# Probes:
scraper    → http://scraper:8001/api/v1/health
core-engine → http://core-engine:8002/api/v1/health
reporter   → http://reporter:8003/api/v1/health
attack-graph-engine → http://attack-graph-engine:8006/api/v1/health
```

Full reverse proxy routing is planned for M10.

---

## 9. Attack Graph Engine

**Port:** 8006

Uses Neo4j to model exploit chains — sequences of vulnerabilities that, when combined, create higher-impact attack paths. Currently a skeleton with health endpoint only.

---

## 10. Specialist Workers (Future)

These workers are defined in docker-compose but are currently skeletons:

| Worker | Queue | Purpose | Milestone |
|--------|-------|---------|-----------|
| `browser-worker` | `browser.jobs` | Headless Chrome-based scanning (login forms, SPAs) | M5 |
| `api-fuzzer-worker` | `api.fuzz.jobs` | OpenAPI/GraphQL endpoint fuzzing | Future |
| `js-analysis-worker` | `js.analysis.jobs` | Deep static analysis of JavaScript (AST parsing, taint tracking) | Future |
| `scenario-runner` | `scenario.jobs` | Multi-step attack scenario execution | Future |
| `exploit-verifier` | `verify.jobs` | Automated exploit verification / proof-of-concept | Future |
| `ai-analysis-worker` | `ai.analysis.jobs` | AI-powered vulnerability analysis and hypothesis generation | Future |

---

## 11. Shared Infrastructure Code

All shared code lives in `backend/shared/`.

### `db.py` — Database Layer

- Uses SQLAlchemy async engine with connection pooling (`pool_size=10`, `max_overflow=20`)
- `pool_pre_ping=True` for detecting stale connections
- `get_session()` is an async context manager that auto-commits on success, rolls back on exception
- `check_db_health()` pings DB with `SELECT 1`

### `queue.py` — Message Queue Layer (330 lines)

Central management of RabbitMQ queues.

**`Queues` class:** Registry of all queue names. Never hardcode queue strings.

**`QueuePublisher`:** Persistent publisher with reconnect support.
- Passive queue declaration (avoids argument mismatch errors)
- Returns `True`/`False` on publish (caller handles failure)
- Auto-reconnects via `aio_pika.connect_robust`

**`ensure_queue_topology()`:** Declares all queues and their DLQs at startup. Handles backward compatibility for already-declared queues with mismatched arguments.

**`inspect_queue_states()`:** Used by health checks and DLQ inspection endpoint.

### `storage.py` — Object Storage Layer

MinIO client wrapper with:
- `init_storage()`: Initialize client (call once at startup)
- `upload_bytes()`: Upload raw bytes
- `download_bytes()`: Download object as bytes
- `get_presigned_url()`: Generate time-limited download URLs
- `check_storage_health()`: Ping by listing buckets

### `logging.py` — Structured Logging

Uses `structlog` for JSON-formatted structured logging:
- ISO timestamps
- Log level, stack info, exception formatting
- Service name bound to all log calls via contextvars
- All services call `configure_logging(service_name, log_level)` at startup

### `health.py` — Health Check Models

Pydantic models for standardized health responses:
```python
HealthStatus: healthy | degraded | unhealthy
ComponentHealth: { status, latency_ms, detail }
HealthResponse: { status, service, timestamp, version, components }
```

### `exceptions.py` — Exception Hierarchy

```
AttackBotError (root)
├── DatabaseError
├── QueueError
│   └── QueueConnectionError
├── StorageError
├── VaultError
├── CollectorError
│   ├── CollectorRateLimitError (429 exhausted)
│   ├── CollectorAuthError (401/403)
│   └── CollectorNotFoundError
├── ScanError
│   ├── ScanTimeoutError
│   ├── ScopeViolationError (hard failure)
│   ├── ScopeFatalError (Stage 0)
│   └── StageError
├── ReportError
├── ValidationError
└── SchemaError
    └── MessageSchemaError
```

---

## 12. Message Contracts & Queue Topology

### The Envelope Pattern

**File:** `backend/shared/schemas/envelope.py` (92 lines)

Every queue message is wrapped in a `MessageEnvelope`:

```json
{
  "event_id": "uuid",           // Globally unique, for dedup + DLQ tracing
  "event_type": "noun.verb",    // e.g. "scan.completed", "program.scraped"
  "schema_version": "1.0",      // Breaking changes bump major
  "timestamp": "2026-04-06T...",
  "trace_id": "optional-uuid",  // From originating HTTP request
  "source_service": "core-engine",
  "payload": { ... }            // Event-specific data
}
```

**Versioning rules:**
- Field addition → minor bump (backward compatible)
- Field removal/rename/type change → major bump (breaking)
- Consumers check `get_major_version()` and reject unknown major versions to DLQ

### Queue Topology

```
Main Queues          Dead-Letter Queues
─────────────        ──────────────────
scan.jobs        →   scan.jobs.dlq
browser.jobs     →   browser.jobs.dlq
api.fuzz.jobs    →   api.fuzz.jobs.dlq
js.analysis.jobs →   js.analysis.jobs.dlq
scenario.jobs    →   scenario.jobs.dlq
verify.jobs      →   verify.jobs.dlq
ai.analysis.jobs →   ai.analysis.jobs.dlq
report.jobs      →   report.jobs.dlq
reports.completed    (no DLQ)
```

All queues are durable. Main queues are configured with `x-dead-letter-exchange` and `x-dead-letter-routing-key` arguments for automatic DLQ routing.

### Key Message Flows

```
Scraper → scan.jobs → Core Worker
  Event: program.scraped
  Payload: ScanJobsPayload (program_id, scope, feature_flags, priority)

Core Worker → report.jobs → Reporter Worker
  Event: scan.completed
  Payload: ReportJobsPayload (scan_id, status, finding_count, severity_breakdown)

Reporter Worker → reports.completed
  Event: report.generated
```

### `ReportJobsPayload` Schema

**File:** `backend/shared/schemas/report_jobs.py` (129 lines)

```python
class ReportJobsPayload:
    scan_id: UUID
    program_id: UUID
    status: "completed" | "partial"
    partial_stages: list[str]           # Names of failed stages
    has_findings: bool
    finding_count: int                  # >= 0, validated against has_findings
    verified_count: int                 # Always 0 until verification milestone
    severity_breakdown: SeverityBreakdown  # critical, high, medium, low, informational
    exploit_chains: list[ExploitChainRef]  # Empty until attack graph milestone
    formats_requested: list["pdf"|"docx"]  # Defaults to ["pdf", "docx"]
    report_ids: dict | None             # Pre-created report IDs per format
    include_evidence_screenshots: bool   # Default True
```

Validators enforce:
- `has_findings=True` requires `finding_count > 0` (and vice versa)
- Empty `formats_requested` defaults to `["pdf", "docx"]`
- `report_ids` keys must exactly match `formats_requested`

---

## 13. Database Schema

The schema is currently represented by 4 Alembic migrations in this repo:

| Migration | Milestone | Tables |
|-----------|-----------|--------|
| 001 | M1 | `programs`, `scans` |
| 002 | M2 | `programs` (extended), `program_scopes`, `program_policies` |
| 003 | M3 | `scans` (extended), `scan_stages`, `assets`, `endpoints`, `js_assets`, `findings`, `finding_evidence`, `vulnerability_groups` |
| 004 | M4 | `reports`, `reproduction_packs` |

### Key Tables

**`programs`**: Bug bounty programs scraped from HackerOne
- `program_id` (UUID PK), `platform`, `handle` (unique), `name`, `is_active`, `queued_for_scan`, `last_scraped_at`

**`scans`**: Individual scan runs
- `scan_id` (UUID PK), `program_id` (FK), `status`, `priority`, `feature_flags` (JSONB), `retry_count`, `finding_count`, `severity_breakdown` (JSONB), `partial_detail` (JSONB), `error_detail`

**`scan_stages`**: Execution log for each pipeline stage
- `stage_id`, `scan_id`, `stage_number` (float — allows sub-stages like 10.1), `stage_name`, `status`, `started_at`, `completed_at`, `output_summary` (JSONB), `error_detail`

**`assets`**: Discovered web assets
- `asset_id`, `scan_id`, `asset_type`, `value`, `is_in_scope`, `technology_stack` (JSONB), `waf_detected`, `http_status`

**`endpoints`**: Discovered URL endpoints
- `endpoint_id`, `asset_id` (FK), `scan_id`, `method`, `path`, `full_url`, `content_type`, `response_code`, `parameters` (JSONB), `headers` (JSONB), `requires_auth`

**`js_assets`**: Downloaded JavaScript files
- `js_asset_id`, `scan_id`, `url`, `content_hash` (unique), `storage_path`, `size_bytes`, `analyzed`

**`findings`**: Vulnerability findings
- `finding_id`, `scan_id`, `program_id`, `title`, `vulnerability_type`, `severity`, `cvss_score`, `cvss_vector`, `affected_url`, `affected_parameter`, `description`, `reproduction_steps`, `is_verified`, `is_false_positive`, `deduplication_hash`, `source`, `raw_output` (JSONB)
- Unique constraint: `(deduplication_hash, scan_id)` — prevents duplicate findings per scan

**`reports`**: Generated report files
- `report_id`, `scan_id`, `program_id`, `format`, `status`, `storage_path`

---

## 14. Exception Hierarchy

The codebase has a clean, centralized exception hierarchy in `backend/shared/exceptions.py`. Key design:

- **All exceptions root at `AttackBotError`** — never raise bare `Exception`
- **Infrastructure errors** (Database, Queue, Storage, Vault) are separate from application errors
- **Collector errors** distinguish between rate limits (retryable), auth failures (not retryable), and not-found
- **Scan errors** distinguish between non-fatal stage failures, timeouts, scope violations (hard failure), and scope fatal (abort scan)
- **Report errors** are separate from scan errors

---

## 15. Configuration System

Each service has a `Config` class extending `BaseServiceConfig` (Pydantic BaseSettings with env var loading).

### Core Engine Config (`backend/services/core_engine/config.py`)

| Setting | Default | Purpose |
|---------|---------|---------|
| `scraper_api_url` | `http://scraper:8001` | Scraper service URL |
| `subfinder_timeout` | 600s | Subfinder execution timeout |
| `dnsx_timeout` | 900s | DNS resolution timeout |
| `nuclei_timeout` | 3600s | Nuclei scan timeout |
| `ffuf_timeout` | 1800s | ffuf enumeration timeout |
| `nuclei_rate_limit` | 150 | Requests per second |
| `nuclei_bulk_size` | 25 | Templates per host |
| `nuclei_concurrency` | 25 | Concurrent template executions |
| `ffuf_wordlist` | `/wordlists/common.txt` | Path to fuzzing wordlist |
| `ffuf_rate` | 100 | Requests per second |
| `ffuf_threads` | 40 | Concurrent threads |
| `js_download_timeout` | 30s | JS file download timeout |
| `js_max_file_size` | 5 MB | Max JS file size |
| `redis_lock_ttl` | 14400s (4h) | Scan lock timeout |
| `watchdog_interval` | 300s (5m) | Stale scan check interval |
| `watchdog_stale_threshold` | 7200s (2h) | When to mark scan as stuck |

### Reporter Config (`backend/services/reporter/config.py`)

| Setting | Default | Purpose |
|---------|---------|---------|
| `core_engine_api_url` | `http://core-engine:8002` | Core Engine URL |
| `scraper_api_url` | `http://scraper:8001` | Scraper URL |
| `reports_bucket` | `reports` | MinIO bucket for reports |
| `evidence_bucket` | `evidence` | MinIO bucket for evidence |
| `report_presign_expiry_seconds` | 900 (15m) | Download URL expiry |
| `report_watchdog_interval_seconds` | 300 (5m) | Stale report check interval |
| `report_watchdog_stale_minutes` | 30 | When to mark report as stuck |
| `report_task_max_retries` | 3 | Max generation attempts |
| `report_task_retry_backoff` | 60, 300, 600 | Retry delays (seconds) |
| `max_inline_evidence_images` | 2 | Per finding in report |
| `evidence_download_concurrency` | 10 | Parallel evidence downloads |

### E2E Test Controls

Several env vars control behavior for end-to-end testing:
- `E2E_PAUSE_RECONCILER`: Pauses reconciler and background scan publishing
- `E2E_TOOL_TIMEOUT_SCALE`: Multiplier for all tool timeouts
- `E2E_TOOL_TIMEOUT_FLOOR_SECONDS`: Minimum timeout (prevents scaling to 0)
- `E2E_FFUF_WORDLIST`: Override wordlist path for testing
- `E2E_SKIP_WAYBACKURLS`: Skip waybackurls (slow in test environments)
- `FORCE_UPLOAD_FAILURE_REPORT_IDS_STR`: Force report upload failures (chaos testing)

---

## 16. Observability Stack

The `infra/` directory includes a full observability stack:

| Component | Purpose |
|-----------|---------|
| **Prometheus** | Metrics collection from all services |
| **Grafana** | Dashboards and alerting |
| **Loki** | Log aggregation |

All FastAPI services expose metrics via `prometheus_fastapi_instrumentator` (request latency, status codes, etc.).

---

## 17. Startup Sequence

The system boots in 6 phases with dependency ordering:

```
Phase 1: Infrastructure (parallel)
  postgres, redis, rabbitmq, neo4j, minio, vault
  ─ All have healthchecks; services wait until healthy

Phase 2: Init (one-shot, exit when done)
  migrate          → waits for postgres
  minio-init       → waits for minio (creates buckets)
  vault-init       → waits for vault (seeds placeholders)

Phase 3: Core Services
  scraper          → waits for postgres, redis, rabbitmq, migrate, minio-init
  core-engine      → waits for postgres, redis, rabbitmq, migrate, minio-init
  reporter         → waits for postgres, redis, rabbitmq, migrate, minio-init
  attack-graph-engine → waits for neo4j, migrate

Phase 4: Core Workers
  core-worker      → waits for core-engine healthy
  reporter-worker  → waits for reporter healthy

Phase 5: Specialist Workers (skeletons)
  browser-worker, api-fuzzer-worker, js-analysis-worker,
  scenario-runner, exploit-verifier, ai-analysis-worker

Phase 6: API Gateway + Observability
  api-gateway      → waits for scraper, core-engine, reporter healthy
  prometheus, grafana, loki
```

**Cold boot time:** 3–4 minutes (primarily Neo4j at 30–60s and PostgreSQL init).

---

## 18. M4 Implementation Plan

**File:** `M4_implementation.md` (184 lines)

M4 is the "Reporter Rollout" milestone. It introduces report generation with 10 gated implementation chunks:

| Gate | Name | Purpose |
|------|------|---------|
| 0 | M3 Baseline Locked | Ensure all M3 features are stable |
| 1 | ISS-009 | Async scraper trigger (decouple scrape from scan publish) |
| 2 | Reporter Plumbing | Queue topology, envelope schema, worker skeleton |
| 3 | First PDF | Generate first real downloadable PDF report |
| 4 | Evidence Integration | Include screenshots and raw HTTP in reports |
| 5 | DOCX Support | Add Word document format |
| 6 | Report Watchdog | Recover stuck report generation |
| 7 | Download API | Pre-signed URL download flow |
| 8 | Prometheus Metrics | download_requests_total, presign_duration_seconds |
| 9 | E2E Testing | End-to-end test with vulnerability target |
| 10 | Hardening | Error handling, retry logic, DLQ routing |

**Key M4 design decisions:**
- **All-findings policy**: Reports include ALL findings (not just verified ones). Verification is a future milestone.
- **Additive-only migrations**: No destructive schema changes. New tables only.
- **Formats**: PDF and DOCX generated for every scan.

---

## 19. Key Design Decisions

### 1. Scope Safety is Non-Negotiable
The `ScopeFilter` is built at Stage 0 and threaded through every stage. If scope is empty, the scan aborts immediately. Every URL discovered by any tool is validated against scope before being used. Out-of-scope always wins over in-scope.

### 2. Graceful Degradation Over Hard Failure
Only Stage 0 (scope) and Stage 10 (aggregation) are fatal. All other stages (1–6) can fail without aborting the scan. The scan is marked `partial` with details about which stages failed.

### 3. Event-Driven Architecture
Services never call each other's databases. All inter-service communication goes through RabbitMQ with versioned envelopes. This enables independent scaling and deployment.

### 4. Deduplication at Multiple Levels
- Asset deduplication by canonical origin (Stage 1)
- Endpoint deduplication by (asset_id, method, path) (Stage 3)
- Finding deduplication by content hash (Stage 10)
- Database-level dedup via `ON CONFLICT (dedup_hash, scan_id) DO NOTHING`

### 5. Synchronous Collectors in Async Services
The HackerOne collector uses synchronous `requests` and is always called via `loop.run_in_executor()`. This is intentional — it keeps the collector simple and testable while the async wrapper handles concurrency.

### 6. Redis for Distributed Locking Only
Redis is used exclusively for distributed locks (scan concurrency, scrape locks). All persistent state lives in PostgreSQL. This keeps the data model simple and avoids Redis persistence concerns.

### 7. Watchdog Recovery Over Retry Loops
Instead of complex retry logic in workers, stuck scans and reports are recovered by periodic watchdog jobs. This is simpler and handles more failure modes (OOM kills, network partitions, etc.).

---

## 20. File Index

### Core Engine (`backend/services/core_engine/`)
| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 472 | FastAPI app, scan API, health, DLQ inspection |
| `worker.py` | 102 | Celery worker definition, message deserialization |
| `scan_task.py` | 384 | Pipeline orchestration (10 stages) |
| `repository.py` | 312 | PostgreSQL operations (scans, assets, findings) |
| `models.py` | 72 | Dataclasses: DiscoveredAsset, Endpoint, JsAsset, FindingCandidate, ScanResult |
| `config.py` | 48 | EngineConfig (timeouts, rate limits, paths) |
| `dedup.py` | 41 | Finding deduplication hash computation |
| `cvss.py` | — | Severity to CVSS score mapping |
| `subprocess_utils.py` | — | Tool execution (run_tool_communicate, parse_jsonl) |

### Pipeline Stages (`backend/services/core_engine/pipeline/`)
| File | Lines | Stage | Purpose |
|------|-------|-------|---------|
| `context.py` | 67 | — | ScanContext, ScopeDefinition, FeatureFlags dataclasses |
| `scope_filter.py` | 196 | 0 | Scope validation (domain, wildcard, IP/CIDR matching) |
| `asset_discovery.py` | 483 | 1 | subfinder → alterx → dnsx → httpx |
| `fingerprinting.py` | 123 | 2 | httpx tech-detect enrichment |
| `enumeration.py` | 311 | 3 | ffuf + waybackurls + JS download |
| `nuclei_scan.py` | 155 | 4 | Nuclei template-based scanning |
| `web_vuln_tests.py` | 222 | 5 | XSS, CORS, CRLF, sensitive paths |
| `js_secrets.py` | 95 | 6 | Regex-based secret detection in JS |
| `aggregator.py` | 134 | 10 | Dedup, persist, finalize, publish |
| `waf_utils.py` | 23 | — | WAF detection keyword matching |

### Scraper (`backend/services/scraper/`)
| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 430 | FastAPI app, scrape logic, scheduler, scan publish |
| `collectors/hackerone.py` | 228 | HackerOne API v1 collector |
| `collectors/base.py` | — | BaseCollector interface, CollectorRegistry |
| `reconciler.py` | 102 | Recovery for failed scan job publishes |
| `publisher.py` | — | ScraperPublisher (builds envelopes for scan.jobs) |
| `repository.py` | — | ProgramRepository (upsert, query programs) |
| `models.py` | — | Program, ProgramScope, ProgramPolicy, RawProgram |
| `config.py` | — | ScraperConfig |
| `scope_parser.py` | — | ScopeParser (normalize raw scope data) |

### Reporter (`backend/services/reporter/`)
| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 373 | FastAPI app, report CRUD, download, generation trigger |
| `worker.py` | 230 | Celery worker, raw Kombu consumer for report.jobs |
| `config.py` | 52 | ReporterConfig (buckets, timeouts, retry backoff) |
| `repository.py` | — | ReportRepository (create, query, update reports) |
| `report_task.py` | — | Actual PDF/DOCX generation logic |
| `storage.py` | — | ReporterStorage (upload/download reports from MinIO) |
| `watchdog.py` | — | Recover stale reports |
| `metrics.py` | — | Prometheus counters and histograms |

### Shared (`backend/shared/`)
| File | Lines | Purpose |
|------|-------|---------|
| `db.py` | 82 | SQLAlchemy async engine, session factory, health check |
| `queue.py` | 330 | RabbitMQ management, topology, publisher, DLQ |
| `storage.py` | 83 | MinIO client (upload, download, presigned URLs) |
| `logging.py` | 47 | structlog configuration |
| `health.py` | 29 | Health check Pydantic models |
| `exceptions.py` | 109 | Exception hierarchy |
| `config.py` | — | BaseServiceConfig |
| `schemas/envelope.py` | 92 | MessageEnvelope + build_envelope() |
| `schemas/report_jobs.py` | 129 | ReportJobsPayload + SeverityBreakdown |
| `schemas/scan_jobs.py` | — | ScanJobsPayload + FeatureFlags + ScopeDefinition |

### Infrastructure (`infra/`)
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Full infrastructure (644 lines, 6 phases) |
| `docker-compose.prod.yml` | Production overrides |
| `grafana/` | Grafana dashboards and provisioning |
| `prometheus/` | Prometheus configuration |
| `loki/` | Loki log aggregation config |

### Root
| File | Purpose |
|------|---------|
| `README.md` | Startup instructions, ports, operational notes |
| `AGENTS.md` | GitNexus code intelligence integration |
| `M4_implementation.md` | M4 Reporter rollout plan (10 chunks) |
| `pyproject.toml` | Tool config (ruff, mypy, pytest, coverage) |

---

*Generated by manual codebase analysis of the M4_ReadTheRoom branch (commit `5005938`).*
