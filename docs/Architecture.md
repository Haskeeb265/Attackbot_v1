# 🤖 AttackBot — Production-Level Low-Level Architecture

> **Version:** 1.1 &nbsp;|&nbsp; **Date:** 2026-03-24 &nbsp;|&nbsp; **Scope:** Full backend platform for automated bug bounty discovery and reporting

---

## 📋 Table of Contents

1. [System Philosophy](#1-system-philosophy)
2. [High-Level Architecture Overview](#2-high-level-architecture-overview)
3. [Service Inventory](#3-service-inventory)
4. [Infrastructure Layer](#4-infrastructure-layer)
5. [Database Schema](#5-database-schema)
6. [Message Queue Topology](#6-message-queue-topology)
7. [Service Internals — Deep Dive](#7-service-internals--deep-dive)
8. [Expanded Pipeline Stages](#8-expanded-pipeline-stages)
9. [Attack Graph Data Model](#9-attack-graph-data-model)
10. [Security Safeguards](#10-security-safeguards)
11. [Observability Stack](#11-observability-stack)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Startup & Bootstrap Order](#13-startup--bootstrap-order)
14. [Failure & Retry Strategy](#14-failure--retry-strategy)
15. [Data Flow Summary](#15-data-flow-summary)

---

## 1. 🧠 System Philosophy

AttackBot is designed around **four core principles**:

---

### 🔹 1. Separation of Concerns

- Every capability lives in its own service with a single, well-defined responsibility
- No service knows the internals of another
- All cross-service communication happens through:
  - Queue contracts
  - REST APIs

---

### 🔹 2. Queue-First Resilience

- All long-running work is **asynchronous and queue-driven**
- No direct synchronous service calls are used for scanning or analysis work
- If a worker fails:
  - The job is **not lost**
  - The message goes to a **DLQ** (Dead Letter Queue)

---

### 🔹 3. Defense-in-Depth for Scope

Scope enforcement is applied **multiple times** across layers:

| Layer | Location |
|---|---|
| Stage 0 | Scan entry |
| Asset Stages | Every asset-producing stage |
| Browser Worker | Before session initiation |
| Post-run | Audit validation |

> ⚠️ Out-of-scope work results in a **hard failure**, not a warning.

---

### 🔹 4. Evidence-First Reporting

- A vulnerability **does not exist** without evidence
- Every finding must include a verified evidence bundle:
  - 📸 Screenshot
  - 💉 Payload
  - 🌐 HTTP request / response
  - 📡 OOB callback
- Unverified candidates are stored separately and **never reported**

---

## 2. 🗺️ High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                              │
│                                                                     │
│   HackerOne ─┐                                                      │
│   BugCrowd  ─┤──► Scraper Service (:8001) ──► scan.jobs             │
│   Intigriti ─┘                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                            │
│                                                                     │
│              Core Engine (:8002) ◄── scan.jobs                      │
│              └── Runs Pipeline Stages 0–10                          │
│                                                                     │
│                  Stage 3.5 ──► browser.jobs ──► Browser Worker      │
│                  Stage 4.5 ──► api.fuzz.jobs ──► API Fuzzer         │
│                  Stage 6   ──► js.analysis.jobs ──► JS Analyzer     │
│                  Stage 7   ──► scenario.jobs ──► Scenario Runner    │
│                  Stage 8   ──► verify.jobs ──► Exploit Verifier     │
│                  Stage 9   ──► ai.analysis.jobs ──► AI Engine       │
│                                                                     │
│              └── Publishes ──► report.jobs                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CORRELATION LAYER                               │
│                                                                     │
│              Attack Graph Engine (:8006)                            │
│              └── Builds Neo4j graph                                 │
│              └── Detects exploit chains                             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      REPORTING LAYER                                │
│                                                                     │
│              Reporter Service (:8003) ◄── report.jobs               │
│                                                                     │
│              └── PDF / DOCX generation                              │
│              └── Exploit reproduction packs                         │
│              └── Publishes reports.completed                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                     Manual Submission (You)
```

---

## 3. 📦 Service Inventory

| # | Service | Port | Type | Responsibility |
|---|---|---|---|---|
| 1 | `api-gateway` | 8000 | FastAPI | External entry point, routing, auth |
| 2 | `scraper` | 8001 | FastAPI + APScheduler | Platform scraping and scan publishing |
| 3 | `core-engine` | 8002 | FastAPI + Celery | Scan orchestration |
| 4 | `core-worker` | internal | Celery Worker | Pipeline execution |
| 5 | `reporter` | 8003 | FastAPI + Celery | Report generation |
| 6 | `reporter-worker` | internal | Celery Worker | PDF/DOCX generation |
| 7 | `browser-worker` | internal | Celery + Playwright | Headless browser automation |
| 8 | `api-fuzzer-worker` | internal | Celery | API fuzzing |
| 9 | `js-analysis-worker` | internal | Celery + Semgrep | Static JS security analysis |
| 10 | `scenario-runner` | internal | Celery | Behavioral attack scenarios |
| 11 | `exploit-verifier` | internal | Celery + Playwright | PoC verification |
| 12 | `attack-graph-engine` | 8006 | FastAPI | Neo4j graph correlation |
| 13 | `ai-analysis-worker` | internal | Celery | LLM hypothesis generation |
| 14 | `migrate` | none | One-shot | Database migrations |

---

## 4. 🏗️ Infrastructure Layer

### 4.1 Component Summary

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Primary DB | PostgreSQL | 16 | Relational data |
| Cache / Locks | Redis | 7 | Distributed locking |
| Message Broker | RabbitMQ | 3 | Async messaging |
| Graph DB | Neo4j | 5 | Exploit chain graph |
| Object Storage | MinIO | latest | Artifacts and evidence |
| Secrets | Vault | 1.x | Credentials and API keys |
| Metrics | Prometheus | latest | Monitoring |
| Dashboards | Grafana | latest | Visualization |
| Logs | Loki | latest | Centralized logs |
| Tracing | Tempo | latest | Distributed tracing |

---

### 4.2 Network Topology

- All services run inside a Docker internal network: **`attackbot-net`**
- Only one service is exposed publicly in production: **`api-gateway :8000`**
- Local development exposes additional ports for convenience (see `infra/docker-compose.prod.yml` for the production overlay)
- Internal management UIs:

| Service | Port |
|---|---|
| RabbitMQ | 15672 |
| MinIO | internal UI |

---

### 4.3 Storage Allocation Strategy

| Data Type | Storage | Reason |
|---|---|---|
| Program metadata | PostgreSQL | Relational queries |
| Scan findings | PostgreSQL | Transactional |
| Reports | MinIO | Binary storage |
| Screenshots | MinIO | Large artifacts |
| JS files | MinIO + hash in Postgres | Deduplicated |
| Attack graph | Neo4j | Graph traversal |
| Session tokens | Postgres (encrypted) | ACID guarantees |

---

## 5. 🗄️ Database Schema

### 5.1 Scraper Domain

#### `programs`
```
program_id          UUID        PK
platform            VARCHAR
handle              VARCHAR     UNIQUE
name                VARCHAR
url                 VARCHAR
bounty_type         VARCHAR
max_bounty          INTEGER
is_active           BOOLEAN
summary_file        VARCHAR
raw_policy          JSONB
queued_for_scan     BOOLEAN
last_scraped_at     TIMESTAMPTZ
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

#### `program_scopes`
```
scope_id            UUID        PK
program_id          UUID        FK
scope_type          VARCHAR
asset_type          VARCHAR
value               VARCHAR
notes               TEXT
created_at          TIMESTAMPTZ
```

#### `program_policies`
```
policy_id           UUID        PK
program_id          UUID        FK
disclosure_policy   TEXT
testing_restrictions TEXT[]
safe_harbor         BOOLEAN
created_at          TIMESTAMPTZ
```

---

### 5.2 Engine Domain

#### `scans`
```
scan_id             UUID        PK
program_id          UUID        FK
status              VARCHAR
priority            INTEGER
feature_flags       JSONB
partial_detail      JSONB
error_detail        TEXT
finding_count       INTEGER
severity_breakdown  JSONB
retry_count         INTEGER
started_at          TIMESTAMPTZ
completed_at        TIMESTAMPTZ
created_at          TIMESTAMPTZ
```

#### `scan_stages`
```
stage_id            UUID        PK
scan_id             UUID        FK
stage_number        FLOAT
stage_name          VARCHAR
status              VARCHAR
started_at          TIMESTAMPTZ
completed_at        TIMESTAMPTZ
error_detail        TEXT
output_summary      JSONB
```

#### `assets`
```
asset_id            UUID        PK
scan_id             UUID        FK
asset_type          VARCHAR
value               VARCHAR
is_in_scope         BOOLEAN
technology_stack    JSONB
waf_detected        VARCHAR
http_status         INTEGER
discovered_at       TIMESTAMPTZ
```

#### `endpoints`
```
endpoint_id         UUID        PK
asset_id            UUID        FK
scan_id             UUID        FK
method              VARCHAR
path                VARCHAR
full_url            VARCHAR
content_type        VARCHAR
response_code       INTEGER
parameters          JSONB
headers             JSONB
requires_auth       BOOLEAN
discovered_at       TIMESTAMPTZ
```

#### `api_schemas` *(planned: M6)*
```
schema_id           UUID        PK
asset_id            UUID        FK
scan_id             UUID        FK
schema_type         VARCHAR
raw_schema          JSONB
parsed_at           TIMESTAMPTZ
```

#### `js_assets`
```
js_asset_id         UUID        PK
scan_id             UUID        FK
url                 VARCHAR
content_hash        VARCHAR     UNIQUE (nullable)
storage_path        VARCHAR
size_bytes          INTEGER
analyzed            BOOLEAN
discovered_at       TIMESTAMPTZ
```

#### `browser_sessions` *(planned: M5)*
```
session_id          UUID        PK
scan_id             UUID        FK
program_id          UUID        FK
cookies             JSONB
local_storage       JSONB
session_headers     JSONB
csrf_token          VARCHAR
login_url           VARCHAR
scenario_used       VARCHAR
is_valid            BOOLEAN
expires_at          TIMESTAMPTZ
created_at          TIMESTAMPTZ
```

#### `findings`
```
finding_id          UUID        PK
scan_id             UUID        FK
program_id          UUID        FK
title               VARCHAR
vulnerability_type  VARCHAR
severity            VARCHAR
cvss_score          FLOAT
cvss_vector         VARCHAR
affected_url        VARCHAR
affected_parameter  VARCHAR
description         TEXT
reproduction_steps  TEXT
is_verified         BOOLEAN
is_false_positive   BOOLEAN
false_positive_reason TEXT
deduplication_hash  VARCHAR
source              VARCHAR
raw_output          JSONB
created_at          TIMESTAMPTZ
```

#### `finding_evidence`
```
evidence_id         UUID        PK
finding_id          UUID        FK
artifact_type       VARCHAR
storage_path        VARCHAR
description         TEXT
captured_at         TIMESTAMPTZ
```

#### `vulnerability_groups`
```
group_id            UUID        PK
scan_id             UUID        FK
vulnerability_type  VARCHAR
affected_count      INTEGER
max_severity        VARCHAR
finding_ids         UUID[]
created_at          TIMESTAMPTZ
```

#### `exploit_chains` *(planned: M8)*
```
chain_id            UUID        PK
scan_id             UUID        FK
chain_name          VARCHAR
description         TEXT
combined_severity   VARCHAR
step_count          INTEGER
finding_ids         UUID[]
graph_path_ids      VARCHAR[]
created_at          TIMESTAMPTZ
```

---

### 5.3 Reporter Domain

#### `reports` *(planned: M4)*
```
report_id           UUID        PK
scan_id             UUID        FK
program_id          UUID        FK
format              VARCHAR
status              VARCHAR
storage_path        VARCHAR
file_size_bytes     INTEGER
error_detail        TEXT
generated_at        TIMESTAMPTZ
created_at          TIMESTAMPTZ
```

#### `reproduction_packs` *(planned: M4)*
```
pack_id             UUID        PK
finding_id          UUID        FK
report_id           UUID        FK
curl_command        TEXT
http_request_raw    TEXT
browser_steps       TEXT
notes               TEXT
created_at          TIMESTAMPTZ
```

---

## 6. 📨 Message Queue Topology

### 6.1 Queue Map

| Queue | Producer | Consumer | Event | DLQ |
|---|---|---|---|---|
| `scan.jobs` | Scraper | Core Worker | `program.scraped` | `scan.jobs.dlq` |
| `browser.jobs` | Core Engine | Browser Worker | `session.request` | `browser.jobs.dlq` |
| `api.fuzz.jobs` | Core Engine | API Fuzzer | `fuzz.request` | `api.fuzz.jobs.dlq` |
| `js.analysis.jobs` | Core Engine | JS Worker | `js.analysis.request` | `js.analysis.jobs.dlq` |
| `scenario.jobs` | Core Engine | Scenario Runner | `scenario.request` | `scenario.jobs.dlq` |
| `verify.jobs` | Core Engine | Exploit Verifier | `verify.request` | `verify.jobs.dlq` |
| `ai.analysis.jobs` | Core Engine | AI Worker | `ai.hypothesis.request` | `ai.analysis.jobs.dlq` |
| `report.jobs` | Core Engine | Reporter Worker | `scan.completed` | `report.jobs.dlq` |
| `reports.completed` | Reporter | External | `report.generated` | — |

---

### 6.2 `scan.jobs` Contract

```json
{
  "event_type": "program.scraped",
  "program_id": "uuid",
  "summary_file": "minio://path",
  "repositories": [],
  "scope": {
    "in_scope": ["*.example.com", "api.example.com"],
    "out_of_scope": ["admin.example.com"]
  },
  "feature_flags": {
    "sqli": false,
    "ssrf": true,
    "takeover": true,
    "browser_session": true,
    "api_fuzzing": true,
    "ai_hypothesis": false
  },
  "priority": 1,
  "timestamp": "ISO8601"
}
```

---

### 6.3 `verify.jobs` Contract

```json
{
  "event_type": "verify.request",
  "finding_id": "uuid",
  "scan_id": "uuid",
  "vulnerability_type": "xss",
  "affected_url": "https://target/path",
  "payload": "<script>alert(1)</script>",
  "parameter": "q",
  "verification_strategy": "headless_browser",
  "session_id": "uuid or null",
  "timestamp": "ISO8601"
}
```

---

### 6.4 `report.jobs` Contract

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
    "low": 3
  },
  "exploit_chains": ["chain_uuid_1"],
  "formats_requested": ["pdf", "docx"],
  "timestamp": "ISO8601"
}
```

---

## 7. 🔬 Service Internals — Deep Dive

### 7.1 Scraper Service

**Startup flow:**

```
1. Load config from Vault
2. Initialize Postgres
3. Connect Redis
4. Initialize QueuePublisher
5. Connect RabbitMQ
6. Start APScheduler jobs
```

**Collector architecture:**

```
BaseCollector
├── HackerOneCollector
├── BugCrowdCollector
├── IntigritiCollector
└── YesWeHackCollector
```

**Key APIs:**

```
POST /api/v1/scrape/trigger
GET  /api/v1/programs
GET  /api/v1/programs/{program_id}
GET  /api/v1/programs/{program_id}/scope
GET  /api/v1/health
```

---

### 7.2 Core Engine Service

**Startup checks:**
- DB schema
- Scanner binaries
- Nuclei templates
- RabbitMQ queues

**Task entry:**

```
scan_task() -> Celery
   -> _async_scan_task()
   -> run_pipeline()
   -> finalize_scan()
```

**Pipeline result states:**

| State | Meaning |
|---|---|
| `completed` | All stages succeeded |
| `partial` | Some stages failed but findings exist |
| `failed_scope` | Scope resolution failed |
| `failed_internal` | Aggregation failure |
| `failed_auth` | Browser auth failure |

**APIs:**

```
POST /api/v1/scans/start
GET  /api/v1/scans
GET  /api/v1/scans/{scan_id}
GET  /api/v1/scans/{scan_id}/findings
GET  /api/v1/queue/dlq/inspect
GET  /api/v1/health
```

---

### 7.3 Browser Worker

**Responsibilities:**
- Playwright browser automation
- Session capture
- Cookie extraction
- CSRF capture

**Isolation model:** Each job runs inside a **fresh Playwright context**.

**Example scenario:**

```yaml
steps:
  - visit: /register
  - fill: [email, random_email()]
  - fill: [password, random_password()]
  - submit
  - visit: /login
  - fill: [email, prev_email]
  - fill: [password, prev_password]
  - submit
  - capture_cookies
  - capture_headers
  - capture_local_storage
```

**Safety limits:**

| Constraint | Limit |
|---|---|
| Max page load | 30s |
| Max scenario | 120s |

---

## 8. 🔄 Expanded Pipeline Stages

```
Stage 0    Scope Filter                    ✅ implemented (M3)
Stage 1    Asset Discovery                 ✅ implemented (M3)
Stage 2    Fingerprinting                  ✅ implemented (M3)
Stage 3    Enumeration                     ✅ implemented (M3)
Stage 3.5  Browser Session Bootstrap       🔲 planned (M5)
Stage 4    Nuclei Scanning                 ✅ implemented (M3)
Stage 4.5  API Fuzzing                     🔲 planned (M6)
Stage 5    Web Vulnerability Tests         ✅ implemented (M3)
Stage 6    JS Secret Scanning              ✅ implemented (M3)
Stage 7    Behavioral Scenario Execution   🔲 planned (M9)
Stage 8    Exploit Verification            🔲 planned (M7)
Stage 9    AI Hypothesis                   🔲 planned (M10)
Stage 10   Aggregation + Graph             ✅ implemented (M3) — graph ingestion planned (M8)
```

**Parallelism model (current M3 implementation):**

| Group | Stages |
|---|---|
| Group A | 4, 5 |

**Current sequential execution (`scan_task._execute_pipeline`):**

```
Stage 0 → Stage 1 → Stage 2 → Stage 3 → (Stage 4 ∥ Stage 5) → Stage 6 → Stage 10
```

**Future parallelism (M6+):**

| Group | Stages |
|---|---|
| Group A | 4, 4.5 |
| Group B | 5, 6 |
| Group C | 7 |

**Future sequential:**

```
Stage 8 → Stage 9 → Stage 10
```

---

## 9. 🕸️ Attack Graph Data Model *(planned: M8 — not yet implemented)*

### Node Types

| Label | Properties |
|---|---|
| `Asset` | `asset_id`, `type`, `value` |
| `Endpoint` | `endpoint_id`, `method` |
| `Finding` | `finding_id`, `severity` |
| `Credential` | `session_id` |
| `Cookie` | `name`, `domain` |
| `JSFile` | `js_asset_id` |

---

### Edge Types

| Edge | Meaning |
|---|---|
| `EXPOSES` | Asset hosts endpoint |
| `HAS_FINDING` | Endpoint has vulnerability |
| `USES` | Endpoint uses credential |
| `LEAKS` | JS file leaks secret |
| `CONTROLS` | Takeover controls cookie |
| `AFFECTS_AUTH` | Cookie grants auth |
| `CHAINS_TO` | Finding enables next |

---

### Example Chain Query

```cypher
MATCH path = (f1:Finding {type: 'subdomain_takeover'})
  -[:CONTROLS]->(c:Cookie)
  -[:AFFECTS_AUTH]->(ep:Endpoint)
  -[:HAS_FINDING]->(f2:Finding)
WHERE f2.type IN ['idor', 'privilege_escalation']
RETURN path
```

---

## 10. 🛡️ Security Safeguards

### Multi-Layer Scope Enforcement

| Layer | Location |
|---|---|
| 1 | Stage 0 |
| 2 | Asset stages |
| 3 | Browser worker |
| 4 | Scenario runner |
| 5 | Post-run audit |

---

### Rate Limiting

- Redis token bucket
- Per-program config
- Worker concurrency caps
- RabbitMQ prefetch limits

---

### Sandboxing

- Workers run in **isolated containers**
- Playwright sandbox
- JS analyzer has **no outbound internet**

---

### Credential Security

- AES-256 encryption in Postgres
- API keys from Vault
- Dynamic credential rotation

---

## 11. 📊 Observability Stack

### Metrics (Prometheus)

Collected metrics include:
- Scan duration per stage
- Severity counts
- Queue depth
- False positive rate
- Worker errors
- API latency (p50/p95/p99)

---

### Logging (Loki)

**Example structured log:**

```json
{
  "service": "core-engine",
  "scan_id": "uuid",
  "stage": 4,
  "event": "nuclei_scan_completed",
  "finding_count": 3,
  "duration_ms": 4821
}
```

---

### Distributed Tracing (Tempo)

**Trace path:**

```
Scraper
   → RabbitMQ
   → Core Engine
   → Workers
   → Reporter
```

---

### Alerting Rules

| Alert | Condition |
|---|---|
| Scan stuck | Running > 2h |
| DLQ growing | > 10 messages |
| False positives | > 40% |
| Worker down | No heartbeat |
| Scope violation | Out-of-scope finding |

---

## 12. 🚀 Deployment Architecture

### Resource Allocation

| Service | CPU | RAM | Replicas |
|---|---|---|---|
| `api-gateway` | 0.5 | 256MB | 1 |
| `scraper` | 0.5 | 512MB | 1 |
| `core-engine` | 0.5 | 512MB | 1 |
| `core-worker` | 2 | 2GB | 2 |
| `browser-worker` | 2 | 2GB | 2 |
| `api-fuzzer` | 1 | 1GB | 1 |
| `js-analysis` | 1 | 1GB | 1 |
| `scenario-runner` | 1 | 1GB | 1 |
| `exploit-verifier` | 2 | 2GB | 2 |
| `attack-graph` | 0.5 | 512MB | 1 |
| `ai-worker` | 1 | 1GB | 1 |
| `reporter` | 0.5 | 512MB | 1 |
| `reporter-worker` | 1 | 1GB | 1 |

---

### Migration Plan

| Revision | File in Repo | Tables | Status |
|---|---|---|---|
| 001 | `001_initial_schema.py` | programs, scans (proof of life) | ✅ Applied |
| 002 | `002_scraper_full.py` | programs (full), program_scopes, program_policies | ✅ Applied |
| 003 | `003_engine.py` | scans (extended), scan_stages, assets, endpoints, js_assets, findings, finding_evidence, vulnerability_groups | ✅ Applied |
| 004 | — | reports, reproduction_packs | 🔲 Planned (M4) |
| 005 | — | browser_sessions | 🔲 Planned (M5) |
| 006 | — | api_schemas | 🔲 Planned (M6) |
| 007 | — | finding_evidence (extended) | 🔲 Planned (M7) |
| 008 | — | exploit_chains | 🔲 Planned (M8) |

---

## 13. ⚡ Startup & Bootstrap Order

```
Phase 1 — Infrastructure
  postgres  redis  rabbitmq  neo4j  minio  vault

Phase 2 — Migrations
  alembic upgrade head

Phase 3 — Core Services
  scraper  core-engine  reporter  attack-graph-engine

Phase 4 — Workers
  core-worker  reporter-worker

Phase 5 — Specialized Workers
  browser  api-fuzzer  js-analysis  scenario  exploit-verifier  ai-worker

Phase 6 — Gateway
  api-gateway
```

---

## 14. 🔁 Failure & Retry Strategy

### Retry Policy

| Worker | Retries | Backoff |
|---|---|---|
| `core-worker` | 3 | 60s → 300s → 900s |
| `browser-worker` | 2 | 30s → 60s |
| `api-fuzzer` | 2 | 30s → 120s |
| `exploit-verifier` | 3 | 15s → 60s → 180s |
| `reporter-worker` | 3 | 60s → 300s → 600s |

---

### DLQ Handling

**Engine APIs:**

```
GET  /api/v1/queue/dlq/inspect
POST /api/v1/queue/dlq/replay
```

> DLQ alerts triggered after **10 messages**.

---

### Watchdog

**Detects stuck jobs when:**
- `status = running`
- TTL exceeded

**Actions:**
- Mark as failed
- Publish recovery job

---

## 15. 📡 Data Flow Summary

```
Bug Bounty Platforms
      │
      ▼
Scraper
Collect + Normalize + Upsert
      │
      ▼
scan.jobs
      │
      ▼
Core Worker Pipeline

  Stages 1–3    → assets + endpoints
  Stage 3.5     → browser_sessions
  Stage 4.5     → api_schemas
  Stage 6       → js_assets → MinIO
  Stages 4–9    → candidate findings
  Stage 8       → verification + evidence
  Stage 10      → aggregation + exploit chains
      │
      ▼
report.jobs
      │
      ▼
Reporter Worker
Generate PDF/DOCX
      │
      ▼
reports.completed
      │
      ▼
Manual Submission
```

---

## 📈 System Totals

| Component | Count | Notes |
|---|---|---|
| Postgres Tables (in repo) | 11 | programs, program_scopes, program_policies, scans, scan_stages, assets, endpoints, js_assets, findings, finding_evidence, vulnerability_groups |
| Postgres Tables (planned) | 7 | reports, reproduction_packs, browser_sessions, api_schemas, exploit_chains (+ extensions) |
| Neo4j Node Labels | 6 | planned (M8) |
| Neo4j Edge Types | 7 | planned (M8) |
| Queues | 9 | |
| DLQs | 8 | |
| Total Queues | 17 | |
| Services (defined in compose) | 14 | |
| Pipeline Stages (implemented) | 8 | Stages 0, 1, 2, 3, 4, 5, 6, 10 |
| Pipeline Stages (planned) | 4 | Stages 3.5, 4.5, 7, 8, 9 |

---

> 💡 **Engineering Truth:** If you're building something like this alone, the hard part is not writing scanners — it is maintaining a coherent data model across asynchronous services. Once queues, schemas, and evidence flows are disciplined, the scanners become almost interchangeable pieces in a much larger machine. That architectural discipline is what turns a collection of scripts into a system.
