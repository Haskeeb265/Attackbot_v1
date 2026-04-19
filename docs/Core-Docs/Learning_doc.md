# 🤖 Attackbot v1 — Complete End-to-End Pipeline Flow

> **Branch:** `M4_ReadTheRoom`  
> **Language:** Python 3.12  
> **Framework:** FastAPI + Celery + SQLAlchemy (async) + Pydantic v2  
> **Architecture:** Event-driven microservices with RabbitMQ message bus

---

## 📑 Table of Contents

- [🗺️ System Architecture](#️-system-architecture)
- [📥 Request Entry Points](#-request-entry-points)
- [🔍 Phase 1: Scraper Service](#-phase-1-scraper-service)
- [⚙️ Phase 2: Core Engine Service](#️-phase-2-core-engine-service)
- [🔥 Phase 3: Scanning Pipeline (Stages 0-10)](#-phase-3-scanning-pipeline-stages-0-10)
- [📄 Phase 4: Reporter Service](#-phase-4-reporter-service)
- [🎯 Final Outputs & Deliverables](#-final-outputs--deliverables)
- [⚠️ Error Handling & Failure Modes](#️-error-handling--failure-modes)
- [📈 E2E Test Flow Analysis](#-e2e-test-flow-analysis)
- [📋 Service & Function Inventory](#-service--function-inventory)
- [🎯 Complete Flow Summary](#-complete-flow-summary)

---

## 🗺️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL WORLD                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐  │
│  │  HackerOne API  │ ←── │  Scraper :8001  │     │ User/Client  │  │
│  └─────────────────┘     └────────┬────────┘     └──────┬───────┘  │
│                                   │                     │          │
│                                   ▼                     ▼          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    RABBITMQ (Message Bus)                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │  │
│  │  │scan.jobs │  │report.jobs│  │browser.jobs│ │reports.completed│ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │  │
│  └───────┼─────────────┼─────────────┼────────────────┼─────────┘  │
│          │             │             │                │            │
│          ▼             ▼             ▼                ▼            │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────┐ ┌────────────┐    │
│  │ Core Worker  │ │Reporter Worker│ │(Future) │ │  (Future)  │    │
│  │   (Celery)   │ │   (Celery)    │ │ Workers │ │  Workers   │    │
│  └──────┬───────┘ └──────┬───────┘ └─────────┘ └────────────┘    │
│         │                │                                         │
│         ▼                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              CORE ENGINE SERVICE (:8002)                    │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │ Stage 0 → Stage 1 → Stage 2 → ... → Stage 10        │   │  │
│  │  │ (Scope)   (Asset)   (Finger)        (Aggregation)   │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     DATA & STORAGE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │ PostgreSQL   │  │    Redis     │  │    MinIO     │  │  Neo4j  │ │
│  │   :5432      │  │    :6379     │  │    :9000     │  │  :7687  │ │
│  │ - programs   │  │ - Dist.locks │  │ - reports    │  │ - Graphs│ │
│  │ - scans      │  │ - scan locks │  │ - evidence   │  │(Future) │ │
│  │ - findings   │  │ - scraper    │  │ - js-assets  │  │         │ │
│  │ - assets     │  │   locks      │  │ - summaries  │  │         │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📥 Request Entry Points

Your system has **3 ways** a request can enter:

| # | Entry Point | Trigger | Service | Endpoint |
|---|------------|---------|---------|----------|
| 1 | Automated Scrape | APScheduler job | Scraper | Internal |
| 2 | Manual Scrape Trigger | HTTP POST | Scraper | `POST /api/v1/scrape/trigger` |
| 3 | Direct Scan Request | HTTP POST | Core Engine | `POST /api/v1/scans/start` |

---

## 🔍 Phase 1: Scraper Service

**Port:** 8001  
**File:** `backend/services/scraper/main.py`

### Purpose
Discovers bug bounty programs from HackerOne and queues scans.

### Step-by-Step Flow

#### **Step 1: Lock Acquisition**

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: LOCK ACQUISITION                                   │
├─────────────────────────────────────────────────────────────┤
│  • Redis Key:   scraper:lock:{platform}                     │
│  • TTL:         platform_lock_ttl_seconds (default: 300s)   │
│  • Type:        Non-blocking acquire                        │
│  • If held:     Return {"status": "skipped"}                │
│  • Purpose:     Prevent concurrent scrapes                  │
└─────────────────────────────────────────────────────────────┘
```

#### **Step 2: Collector Execution**

**File:** `backend/services/scraper/collectors/hackerone.py`

Runs **synchronously** in threadpool via `loop.run_in_executor()`:

**A. Initialize Collector:**
- API Username: From Vault KV (`hackerone_api_username`)
- API Token: From Vault KV (`hackerone_api_token`)
- Max Retries: `collector_max_retries` (default: 3)
- Page Size: `collector_page_size` (default: 100)
- Timeout: `collector_timeout_seconds` (default: 60s)

**B. `fetch_listing()`:**
- HTTP Method: GET
- Auth: Basic Auth (username:token)
- Pagination: Auto-fetch all pages
- Rate Limiting: Auto-retry on 429 with Retry-After header
- Exceptions: `CollectorAuthError` (401/403), `CollectorRateLimitError` (429)
- Output: `list[RawHackerOneProgram]`

**C. For EACH program:**
- `fetch_details(handle)`: Fetches scope, policy, metadata
- `normalize(raw_data)`: Transforms HackerOne JSON → canonical `Program` model

##### HackerOne → Canonical Asset Type Mapping

| HackerOne Type | Canonical Type | Example |
|---------------|----------------|---------|
| `URL` | `url` | `https://example.com/login` |
| `WILDCARD` | `wildcard_domain` | `*.example.com` |
| `DOMAIN` | `domain` | `example.com` |
| `IP_ADDRESS` | `ip_range` | `192.168.1.1` |
| `CIDR` | `ip_range` | `192.168.1.0/24` |
| `ANDROID` | `mobile_app` | `com.example.app` |
| `IOS` | `mobile_app` | `com.example.app` |
| `API` | `api` | API |
| `SOURCE_CODE` | `api` | Source Code |
| `OTHER` | `url` | Other |

#### **Step 3: Scope Parsing**

**File:** `backend/services/scraper/scope_parser.py`

- Input: Raw scope data from HackerOne
- `parse()`: Normalizes into structured `ProgramScope` objects
- Output: `ScopeDefinition` with:
  - `in_scope`: list of `ScopeEntry`
  - `out_of_scope`: list of `ScopeEntry`

#### **Step 4: Program Persistence**

**File:** `backend/services/scraper/repository.py`

**A. Upsert Program:**
- Table: `programs`
- SQL: `ON CONFLICT (handle) DO UPDATE`
- Fields: `program_id`, `platform`, `handle`, `name`, `is_active`, `metadata`, `last_scraped_at`

**B. Insert Scope Entries:**
- Table: `program_scopes`
- Fields: `scope_id`, `program_id`, `scope_type`, `value`, `is_positive`
- Note: `is_positive=True` for in_scope, `False` for out_of_scope

**C. Insert Policy (if exists):**
- Table: `program_policies`
- Fields: `policy_id`, `program_id`, `bounty`, `vuln_requirements`, `max_payout`

**Side Effect:** `Program.queued_for_scan = True` (if due for rescan)

#### **Step 5: Scan Job Publication**

**File:** `backend/services/scraper/publisher.py`

**A. Check if Program is Due for Scan:**
- Condition: `last_scanned_at < NOW() - rescan_interval`
- Default: Always queue new programs

**B. Build MessageEnvelope:**
```json
{
  "event_id": "uuid4()",
  "event_type": "program.scraped",
  "schema_version": "1.0",
  "timestamp": "ISO 8601 datetime",
  "source_service": "scraper",
  "payload": {
    "program_id": "uuid",
    "scope": { ... },
    "feature_flags": {
      "nuclei": true,
      "waybackurls": true,
      "ffuf": true,
      "browser": false
    },
    "priority": 5
  }
}
```

**C. Publish to RabbitMQ:**
- Queue: `scan.jobs`
- Persistent: `True`
- DLQ: `scan.jobs.dlq` (automatic on failure)

**D. On Success:**
- `ProgramRepository.clear_queued_for_scan()`
- **NOTE:** Only the Reconciler can call this method!

#### **Step 6: Reconciler (Background Recovery)**

**File:** `backend/services/scraper/reconciler.py`  
**Trigger:** APScheduler job every 5 minutes

**Purpose:** Recover failed scan job publishes

**A. Query for Stuck Programs:**
```sql
SELECT * FROM programs WHERE queued_for_scan = True
```

**B. For EACH stuck program:**
- Fetch full scope from DB
- Build `MessageEnvelope` (same as Step 5)
- Publish to `scan.jobs`
- On success: `ProgramRepository.clear_queued_for_scan()`

> 🔴 **CRITICAL:** This is the **ONLY** component allowed to clear the `queued_for_scan` flag!

---

## ⚙️ Phase 2: Core Engine Service

**Port:** 8002  
**File:** `backend/services/core_engine/main.py`

### API Endpoints

| Method | Path | Purpose | Triggered By |
|--------|------|---------|--------------|
| `GET` | `/api/v1/health` | Health check | All services |
| `POST` | `/api/v1/scans/start` | Start a new scan | User/Scraper |
| `GET` | `/api/v1/scans` | List recent scans | User/API |
| `GET` | `/api/v1/scans/{scan_id}` | Get scan details | Reporter/API |
| `GET` | `/api/v1/scans/{scan_id}/findings` | Get findings | Reporter |
| `GET` | `/api/v1/scans/{scan_id}/findings/{id}/evidence` | Get evidence | Reporter |
| `GET` | `/api/v1/queue/dlq/inspect` | Inspect DLQ messages | User |

### Scan Start Flow

```
┌─────────────────────────────────────────────────────────────┐
│  CORE ENGINE: SCAN START FLOW                               │
├─────────────────────────────────────────────────────────────┤
│  Trigger: POST /api/v1/scans/start                          │
│                                                              │
│  Step 1: _build_payload_from_scraper()                      │
│    • GET scraper:8001/api/v1/programs/{program_id}/scope    │
│    • Fetches: Program metadata + scope definition           │
│    • Output: ScanJobsPayload                                │
│                                                              │
│  Step 2: _reserve_scan_id()                                 │
│    • SQL: INSERT INTO scans (...)                           │
│    • Status: "pending"                                       │
│    • Output: scan_id (UUID)                                  │
│                                                              │
│  Step 3: _enqueue_scan()                                    │
│    • Builds: MessageEnvelope with ScanJobsPayload           │
│    • Publishes: To scan.jobs queue (RabbitMQ)               │
│    • Returns: scan_id, status="queued"                      │
└─────────────────────────────────────────────────────────────┘
```

### Watchdog (Background Recovery)

**File:** `backend/services/core_engine/watchdog.py`  
**Trigger:** APScheduler job every 5 minutes

**Purpose:** Recover stuck scans

**A. Query for Stuck Scans:**
```sql
SELECT scan_id FROM scans
WHERE status = 'running'
AND started_at < NOW() - watchdog_stale_threshold (7200s = 2 hours)
```

**B. For EACH stuck scan:**
```sql
UPDATE scans SET 
  status = 'failed_internal', 
  error_detail = 'watchdog recovery'
WHERE scan_id = :scan_id
```

> ⚠️ **NOTE:** Watchdog is INTENTIONALLY simple. No retries — just marks as failed so the system can recover.

---

## 🔥 Phase 3: Scanning Pipeline (Stages 0-10)

**File:** `backend/services/core_engine/scan_task.py`

### Worker Initialization

**File:** `backend/services/core_engine/worker.py`

```python
# Celery Worker Configuration
Broker:            RabbitMQ (amqp://guest:guest@rabbitmq:5672//)
Queue:             scan.jobs
Prefetch:          1 (one message at a time)
Max Retries:       0 (Watchdog handles retries, not Celery)
Task:              run_scan_task (in scan_task.py)
```

### Pipeline Entry Point

**Function:** `run_scan_task(payload: ScanJobsPayload | dict)`

```python
# Synchronous wrapper
asyncio.run(_async_scan_pipeline(payload))
```

### Pipeline Setup

```
┌─────────────────────────────────────────────────────────────┐
│  _async_scan_pipeline() - FULL PIPELINE ORCHESTRATOR       │
├─────────────────────────────────────────────────────────────┤
│  Step 1: Initialize Infrastructure                          │
│    • DB:       init_db(config.database_url)                 │
│    • Storage:  init_storage(minio_*)                        │
│    • Redis:    aioredis.from_url(config.redis_url)          │
│                                                              │
│  Step 2: Parse Payload                                      │
│    • ScanJobsPayload.model_validate(payload)                │
│    • Extract: program_id, feature_flags, priority           │
│                                                              │
│  Step 3: ACQUIRE SCAN LOCK                                  │
│    • Redis Key: scan:lock:{program_id}                      │
│    • TTL: 14400s (4 hours)                                  │
│    • If held: Skip execution (log warning and RETURN)       │
│                                                              │
│  Step 4: CREATE SCAN CONTEXT                                │
│    • create_or_resume_scan(program_id, ...)                 │
│    • _fetch_scope_from_scraper(program_id)                  │
│    • If scope fetch fails:                                  │
│        mark_scan_complete(status="failed_scope")            │
│        RETURN                                               │
│                                                              │
│  Step 5: INITIALIZE QUEUE PUBLISHER                         │
│    • publisher = QueuePublisher(config.rabbitmq_url)        │
│                                                              │
│  Step 6: EXECUTE PIPELINE                                   │
│    • _execute_pipeline(ctx, scan_result, repo, publisher)   │
│    • If exception:                                          │
│        mark_scan_complete(status="failed_internal")         │
│                                                              │
│  Step 7: CLEANUP                                            │
│    • await publisher.close()                                │
│    • await lock.release()                                   │
│    • await redis.aclose()                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Stages Breakdown

### 🟥 Stage 0: Scope Filter (FATAL)

**File:** `backend/services/core_engine/pipeline/scope_filter.py`

```
┌─────────────────────────────────────────────────────────────┐
│  ScopeFilter Initialization                                 │
├─────────────────────────────────────────────────────────────┤
│  Input: ScopeDefinition (in_scope, out_of_scope)            │
│                                                              │
│  Step 1: Validate Scope Not Empty                           │
│    • If len(in_scope) == 0 and len(out_of_scope) == 0:      │
│        raise ScanError("Scope is empty")                    │
│    • This is FATAL - scan ABORTS HERE                       │
│                                                              │
│  Step 2: Build Matching Structures                          │
│    • Exact domains: Store as-is                             │
│    • Wildcard domains: Store domain part                    │
│    • IP ranges: Parse CIDR notation                         │
│    • URLs: Parse into (scheme, host, port, path)            │
│                                                              │
│  Step 3: Matching Rules                                     │
│    ✓ Exact match: "example.com" matches "example.com" only  │
│    ✓ Wildcard: "*.example.com" matches "sub.example.com"    │
│      but NOT "example.com"                                  │
│    ✓ Domain root: "example.com" matches both                │
│      "example.com" AND "sub.example.com"                    │
│    ✓ Out-of-scope wins: If target matches BOTH in and out,  │
│      it's EXCLUDED                                          │
│    ✓ CIDR: IP range matching (e.g., 192.168.1.0/24)        │
│                                                              │
│  Output: ScopeFilter instance                               │
└─────────────────────────────────────────────────────────────┘
```

> 🔴 **CRITICAL:** This is the **SAFETY GUARD**. The system will **NEVER** scan without a defined scope.

---

### 🟨 Stage 1: Asset Discovery

**File:** `backend/services/core_engine/pipeline/asset_discovery.py`

```
┌─────────────────────────────────────────────────────────────┐
│  Asset Discovery Pipeline                                   │
├─────────────────────────────────────────────────────────────┤
│  Step 1: SEED COLLECTION                                    │
│    • Sources:                                               │
│      - Domain rules → Always seed candidates                │
│      - Wildcard_domain rules → Domain part as seed          │
│      - URL rules → Seed only if HTTP(S) and in-scope        │
│      - Explicit targets → ALSO probed directly              │
│                                                              │
│  Step 2: subfinder (Passive Subdomain Enumeration)          │
│    • Config: /app/subfinder-config/provider-config.yaml     │
│    • Timeout: 600s (10 min)                                 │
│    • Non-fatal: If fails, seed domain still probed          │
│    • Output: List of candidate subdomains                   │
│                                                              │
│  Step 3: alterx (Permutation-based Generation)              │
│    • Input: subfinder results                               │
│    • Generates: dev.{seed}, staging.{seed}, etc.            │
│    • Timeout: 300s (5 min)                                  │
│                                                              │
│  Step 4: dnsx (DNS Resolution)                              │
│    • Filters: Only live (resolvable) domains                │
│    • Handles: Wildcard DNS, CNAME records, multiple IPs     │
│    • Timeout: 900s (15 min)                                 │
│                                                              │
│  Step 5: httpx (HTTP Probing)                               │
│    • Detects: Technologies, status codes, page titles       │
│    • Filters: Only successful HTTP responses (2xx, 3xx)     │
│    • Timeout: 600s (10 min)                                 │
│                                                              │
│  Step 6: DEDUPLICATION                                      │
│    • Key: canonical origin = scheme://host:port             │
│    • Rule: First-seen wins for all fields                   │
│                                                              │
│  Step 7: SCOPE VALIDATION                                   │
│    • Every asset validated against ScopeFilter              │
│    • Out-of-scope assets are DROPPED                        │
│                                                              │
│  Output: list[DiscoveredAsset] (typically 50-1000)          │
│  Database: repo.save_assets(scan_id, assets)                │
│  ⚠️  NON-FATAL: If fails, scan continues with empty list   │
└─────────────────────────────────────────────────────────────┘
```

---

### 🟨 Stage 2: Fingerprinting

**File:** `backend/services/core_engine/pipeline/fingerprinting.py`

```
┌─────────────────────────────────────────────────────────────┐
│  Fingerprinting Pipeline                                    │
├─────────────────────────────────────────────────────────────┤
│  Input: list[DiscoveredAsset] from Stage 1                  │
│                                                              │
│  Step 1: httpx Tech-Detect Mode                             │
│    • Runs httpx with extended fingerprinting                │
│    • Detects:                                               │
│      - Technologies: ["React", "Node.js", "Nginx", ...]     │
│      - Title: Page <title> tag                              │
│      - Content-Type: e.g., "text/html"                      │
│      - Server: Server header (e.g., "nginx/1.18.0")         │
│                                                              │
│  Step 2: WAF Detection (waf_utils.py)                       │
│    • Keywords: ["waf", "cloudflare", "akamai", "f5", ...]   │
│    • Checks: Response headers and body for WAF signatures   │
│    • Sets: asset.waf_detected = True if match              │
│                                                              │
│  Output: Same list[DiscoveredAsset] (enriched in-place)     │
│  Database: repo.save_assets(scan_id, assets) → UPDATE       │
│  ⚠️  NON-FATAL: If fails, assets remain as-is from Stage 1 │
└─────────────────────────────────────────────────────────────┘
```

---

### 🟩 Parallel Stages: 3 + 4

> ⚡ **These run CONCURRENTLY after Stage 2 completes**

### 🟦 Stage 3: Enumeration

**File:** `backend/services/core_engine/pipeline/enumeration.py`

```
┌─────────────────────────────────────────────────────────────┐
│  Enumeration Pipeline                                       │
├─────────────────────────────────────────────────────────────┤
│  Input: list[DiscoveredAsset] from Stage 2                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SUB-STEP A: ffuf (Directory/Path Discovery)         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  • Target: {base_url}/FUZZ                           │   │
│  │  • Wordlist: /wordlists/common.txt                   │   │
│  │  • Match Status: 200, 201, 204, 301, 302, 307, 401,  │   │
│  │    403                                                │   │
│  │  • Threads: 40                                        │   │
│  │  • Rate: 100 req/s                                    │   │
│  │  • Timeout: 1800s (30 min)                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SUB-STEP B: waybackurls (Historical URL Discovery)  │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  • Fetches: Historical URLs from Wayback Machine     │   │
│  │  • Scope-filtered: Only in-scope URLs kept           │   │
│  │  • Skippable: Via E2E_SKIP_WAYBACKURLS env var       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SUB-STEP C: JS File Discovery & Download            │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  • Discovers: .js files from enumerated endpoints    │   │
│  │  • For EACH JS file:                                 │   │
│  │    1. Download with redirect following               │   │
│  │    2. Validate: Final URL is in-scope                │   │
│  │    3. Max size: 5 MB, Timeout: 30s                   │   │
│  │    4. Hash: SHA-256                                  │   │
│  │    5. Upload to MinIO: js-assets bucket              │   │
│  │  • Non-fatal: Individual failures don't fail stage   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Output: (list[DiscoveredEndpoint], list[DiscoveredJsAsset])│
│  Database: repo.save_endpoints() + repo.save_js_asset()     │
│  ⚠️  NON-FATAL: If fails, continues with empty lists       │
└─────────────────────────────────────────────────────────────┘
```

---

### 🟦 Stage 4: Nuclei Scan

**File:** `backend/services/core_engine/pipeline/nuclei_scan.py`

```
┌─────────────────────────────────────────────────────────────┐
│  Nuclei Scan Pipeline                                       │
├─────────────────────────────────────────────────────────────┤
│  Input: list[DiscoveredAsset] from Stage 2                  │
│  ⏭️  Runs IN PARALLEL with Stage 3                         │
│                                                              │
│  Configuration:                                              │
│    • Rate Limit:  150 req/s                                 │
│    • Bulk Size:   25 templates per host                     │
│    • Concurrency: 25                                        │
│    • Timeout:     3600s (1 hour)                            │
│    • Excludes:    Templates tagged "headless"               │
│    • Templates:   Default Nuclei templates (~1000+)         │
│                                                              │
│  Execution:                                                  │
│    nuclei -u {targets} -t {templates}                       │
│           --rate-limit {rate}                               │
│           --bulk-size {size}                                │
│           --concurrency {concurrency}                       │
│                                                              │
│  Exit Code Handling:                                         │
│    • Exit code 2: Startup failure → Stage failed            │
│    • Other codes: Subprocess failure → Stage failed         │
│                                                              │
│  CVSS Mapping:                                               │
│    • critical → 9.8                                          │
│    • high     → 7.5                                          │
│    • medium   → 5.3                                          │
│    • low      → 3.1                                          │
│    • info     → 0.0                                          │
│                                                              │
│  Output: list[FindingCandidate]                             │
│  ⚠️  NON-FATAL: If fails, scan continues without Nuclei    │
└─────────────────────────────────────────────────────────────┘
```

---

### 🟩 Parallel Stages: 5 + 6

> ⚡ **These run CONCURRENTLY after Stage 3 completes**

### 🟧 Stage 5: Web Vulnerability Tests

**File:** `backend/services/core_engine/pipeline/web_vuln_tests.py`

```
┌─────────────────────────────────────────────────────────────┐
│  Web Vulnerability Tests Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│  Input: list[DiscoveredEndpoint] from Stage 3 (max 500)     │
│  ⏭️  Runs IN PARALLEL with Stage 6                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ALWAYS ENABLED TESTS                                │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  TEST 1: Reflected XSS                               │   │
│  │    • Injects 3 payloads per query parameter          │   │
│  │    • Max params: 10 per endpoint                     │   │
│  │    • Payloads:                                       │   │
│  │      1. "<script>alert(1)</script>"                  │   │
│  │      2. "xss_test_123"                               │   │
│  │      3. "<img src=x onerror=alert(1)>"               │   │
│  │    • Checks: Payload reflected verbatim in response  │   │
│  │    • Severity: high                                  │   │
│  │                                                       │   │
│  │  TEST 2: CORS Misconfiguration                       │   │
│  │    • Tests with 3 evil origins:                      │   │
│  │      1. https://evil.com                             │   │
│  │      2. null                                          │   │
│  │      3. https://attacker.example.com                 │   │
│  │    • Flags: Server reflects origin AND sets          │   │
│  │      Access-Control-Allow-Credentials: true          │   │
│  │    • Severity: medium                                │   │
│  │                                                       │   │
│  │  TEST 3: Sensitive Path Detection (PASSIVE)          │   │
│  │    • Checks: .env, .git/HEAD, .git/config            │   │
│  │    • Severity: info                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Output: list[FindingCandidate]                             │
│  ⚠️  NON-FATAL: If fails, continues without web vulns      │
└─────────────────────────────────────────────────────────────┘
```

---

### 🟧 Stage 6: JS Secrets Scanning

**File:** `backend/services/core_engine/pipeline/js_secrets.py`

```
┌─────────────────────────────────────────────────────────────┐
│  JS Secrets Scanning Pipeline                              │
├─────────────────────────────────────────────────────────────┤
│  Input: list[DiscoveredJsAsset] from Stage 3                │
│  ⏭️  Runs IN PARALLEL with Stage 5                         │
│                                                              │
│  Step 1: For EACH JS Asset                                  │
│    • Download from MinIO (js-assets bucket)                 │
│    • Decode: UTF-8 text                                     │
│    • Scan with 13 regex patterns (first match per pattern)  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SECRET PATTERNS                                     │   │
│  ├────────────────────┬─────────────┬──────────────────┤   │
│  │ Pattern            │ Label       │ Severity         │   │
│  ├────────────────────┼─────────────┼──────────────────┤   │
│  │ AIza[0-9A-Za-z...] │ Google API  │ High             │   │
│  │ sk-[a-zA-Z0-9]{48} │ OpenAI API  │ Critical         │   │
│  │ xox[baprs]-...     │ Slack Token │ High             │   │
│  │ api[_-]?key=...    │ Generic API │ Medium           │   │
│  │ password=...       │ Password    │ High             │   │
│  │ eyJ...             │ JWT Token   │ Medium           │   │
│  │ -----BEGIN ...     │ Private Key │ Critical         │   │
│  │ ghp_[A-Za-z0-9]... │ GitHub PAT  │ Critical         │   │
│  │ AKIA[0-9A-Z]{16}   │ AWS Access  │ Critical         │   │
│  │ (AWS Secret regex) │ AWS Secret  │ Critical         │   │
│  └────────────────────┴─────────────┴──────────────────┘   │
│                                                              │
│  Output: list[FindingCandidate]                             │
│  ⚠️  NON-FATAL: If fails, continues without JS secrets     │
└─────────────────────────────────────────────────────────────┘
```

---

### 🟥 Stage 10: Aggregation (FATAL)

**File:** `backend/services/core_engine/pipeline/aggregator.py`

```
┌─────────────────────────────────────────────────────────────┐
│  Aggregation Pipeline (FINAL STAGE - FATAL IF FAILS)       │
├─────────────────────────────────────────────────────────────┤
│  Input:                                                      │
│    • ctx: ScanContext                                       │
│    • scan_result: ScanResult with all stage outputs        │
│                                                              │
│  Step 1: DEDUPLICATION                                      │
│    • For EACH finding_candidate:                            │
│      - Compute SHA-256 hash:                                │
│        hash_input = vulnerability_type | normalized_url |   │
│                     parameter | payload[:100]               │
│      - normalized_url: Lowercase, strip trailing slash      │
│    • Remove: Duplicates (keep first occurrence)             │
│                                                              │
│  Step 2: PERSIST FINDINGS TO POSTGRESQL                     │
│    • SQL: INSERT INTO findings (...)                        │
│           ON CONFLICT (deduplication_hash, scan_id)         │
│           DO NOTHING                                        │
│    • Unique constraint prevents duplicates per scan         │
│                                                              │
│  Step 3: SEVERITY BREAKDOWN                                 │
│    • Count findings by severity:                            │
│      - critical, high, medium, low, informational           │
│                                                              │
│  Step 4: DETERMINE SCAN STATUS                              │
│    • If NO stage_errors: status = "completed"               │
│    • If ANY stage_errors: status = "partial"                │
│      - partial_detail: JSONB with failed stage names        │
│                                                              │
│  Step 5: FINALIZE SCAN                                      │
│    • UPDATE scans SET                                       │
│        status = :status,                                    │
│        finding_count = :count,                              │
│        severity_breakdown = :breakdown,                     │
│        completed_at = NOW()                                 │
│                                                              │
│  Step 6: LOG STAGE 10                                       │
│    • repo.record_stage(scan_id, 10.0, "aggregation", ...)   │
│                                                              │
│  Step 7: REPORT HANDOFF - Publish to RabbitMQ               │
│    • Queue: report.jobs                                     │
│    • Event: scan.completed                                  │
│    • Payload: ReportJobsPayload with:                       │
│      - scan_id, program_id, status                          │
│      - finding_count, severity_breakdown                    │
│      - formats_requested: ["pdf", "docx"]                   │
│                                                              │
│  ⚠️  FATAL: If this stage fails, scan marked               │
│             "failed_internal"                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📄 Phase 4: Reporter Service

**Port:** 8003  
**File:** `backend/services/reporter/main.py`

### Report Generation Triggers

| # | Trigger | Source | Endpoint |
|---|---------|--------|----------|
| 1 | Automatic | Core Worker (Stage 10) | Publishes to `report.jobs` |
| 2 | Manual | User/API | `POST /api/v1/reports/generate` |

### Report Generation Flow

#### **Step 1: Reporter Worker - Message Consumption**

**File:** `backend/services/reporter/worker.py`

```
┌─────────────────────────────────────────────────────────────┐
│  REPORTER WORKER - MESSAGE CONSUMPTION                      │
├─────────────────────────────────────────────────────────────┤
│  • Worker Type: Celery worker consuming from RabbitMQ       │
│  • Queue: report.jobs                                       │
│  • Consumer: Raw Kombu consumer (NOT native Celery)         │
│                                                              │
│  Message Processing:                                         │
│    1. Receive raw message from report.jobs                  │
│    2. Validate MessageEnvelope:                             │
│       - event_type must be "scan.completed"                 │
│       - schema_version major must be 1                      │
│    3. Parse: ReportJobsPayload.model_validate()             │
│    4. Enqueue Celery task:                                  │
│       - Queue: reporter.worker.tasks                        │
│       - Task: process_report_envelope_sync()                │
│    5. Retry Strategy:                                       │
│       - Max retries: 3                                      │
│       - Backoff: [60, 300, 600] seconds                     │
│       - On exhaust: Publish to report.jobs.dlq              │
└─────────────────────────────────────────────────────────────┘
```

#### **Step 2: Report Generation Task**

**File:** `backend/services/reporter/report_task.py`  
**Function:** `process_report_envelope_sync()` (SYNCHRONOUS)

```
┌─────────────────────────────────────────────────────────────┐
│  REPORT GENERATION TASK                                     │
├─────────────────────────────────────────────────────────────┤
│  Step A: CREATE REPORT ROWS (PostgreSQL)                    │
│    • For EACH format in ["pdf", "docx"]:                    │
│      - INSERT INTO reports (...)                            │
│      - status: "generating"                                 │
│                                                              │
│  Step B: FETCH SCAN DATA FROM CORE ENGINE API               │
│    • GET core-engine:8002/api/v1/scans/{scan_id}            │
│    • GET core-engine:8002/api/v1/scans/{scan_id}/findings   │
│    • For EACH finding (if include_evidence_screenshots):    │
│      - GET .../findings/{id}/evidence                       │
│                                                              │
│  Step C: GENERATE REPORT FILES                              │
│    ┌──────────────────────────────────────────────────┐     │
│    │  PDF Generation (reportlab):                     │     │
│    │  • Cover page: Scan metadata                     │     │
│    │  • Executive summary: Severity breakdown         │     │
│    │  • Findings table: Title, Severity, CVSS, URL    │     │
│    │  • Details: Description, reproduction, evidence  │     │
│    │  • Output: Raw PDF bytes                         │     │
│    └──────────────────────────────────────────────────┘     │
│    ┌──────────────────────────────────────────────────┐     │
│    │  DOCX Generation (python-docx):                  │     │
│    │  • Similar content to PDF                        │     │
│    │  • Output: Raw DOCX bytes                        │     │
│    └──────────────────────────────────────────────────┘     │
│                                                              │
│  Step D: UPLOAD TO MINIO                                    │
│    • Bucket: reports                                        │
│    • Key: reports/{report_id}/report.{format}               │
│                                                              │
│  Step E: UPDATE REPORT STATUS                               │
│    • UPDATE reports SET                                     │
│        status = 'completed',                                │
│        storage_path = :path,                                │
│        file_size_bytes = :size,                             │
│        generated_at = NOW()                                 │
│                                                              │
│  Step F: PUBLISH REPORT COMPLETED (Optional)                │
│    • Queue: reports.completed                               │
│    • Event: report.generated                                │
└─────────────────────────────────────────────────────────────┘
```

---

### Manual Report Generation

**Endpoint:** `POST /api/v1/reports/generate`

```
┌─────────────────────────────────────────────────────────────┐
│  Manual Report Trigger Flow                                 │
├─────────────────────────────────────────────────────────────┤
│  Body:                                                       │
│  {                                                           │
│    "scan_id": "uuid",                                       │
│    "formats_requested": ["pdf", "docx"],                    │
│    "include_evidence_screenshots": true                     │
│  }                                                           │
│                                                              │
│  Step 1: Validate Request                                   │
│    • scan_id: Required UUID                                 │
│    • formats_requested: Defaults to ["pdf", "docx"]         │
│                                                              │
│  Step 2: Fetch Scan from Core Engine                        │
│    • GET core-engine:8002/api/v1/scans/{scan_id}            │
│    • If not found: 404                                      │
│    • If not terminal (running/pending): 400 Bad Request     │
│                                                              │
│  Step 3: Create Report Rows                                 │
│    • ReportRepository.create_or_reset_report()              │
│    • If report exists and completed: Reuse existing         │
│                                                              │
│  Step 4: Build and Publish Message                          │
│    • Build ReportJobsPayload                                │
│    • Build MessageEnvelope                                  │
│    • Publish to: report.jobs                                │
│                                                              │
│  Step 5: Return Response                                    │
│    • Status: 202 Accepted                                   │
│    • Body: {                                                │
│        "status": "queued",                                  │
│        "scan_id": "...",                                    │
│        "report_ids": {"pdf": "...", "docx": "..."}          │
│      }                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

### Report Download Flow

**Endpoint:** `GET /api/v1/reports/{report_id}/download`

```
┌─────────────────────────────────────────────────────────────┐
│  Report Download Flow                                       │
├─────────────────────────────────────────────────────────────┤
│  Step 1: Validate Report Exists                             │
│    • SQL: SELECT * FROM reports WHERE report_id = :id       │
│    • If not found: 404 Not Found                            │
│                                                              │
│  Step 2: Validate Status is Terminal                        │
│    • Terminal statuses: "completed", "failed"               │
│    • If status is "generating": 409 Conflict (not ready)    │
│                                                              │
│  Step 3: Validate Storage Path Exists                       │
│    • If storage_path is NULL: 409 Conflict (missing)        │
│                                                              │
│  Step 4: Generate Pre-signed URL (MinIO)                    │
│    • ReporterStorage.get_presigned_url()                    │
│    • Bucket: reports                                        │
│    • Key: storage_path                                      │
│    • Expiry: 900s (15 min)                                  │
│                                                              │
│  Step 5: Increment Metrics (Prometheus)                     │
│    • download_requests_total.labels(status="success").inc() │
│    • presign_duration_seconds.observe(duration)             │
│                                                              │
│  Step 6: Return Response                                    │
│    • Status: 200 OK                                         │
│    • Body: {                                                │
│        "download_url": "http://minio:9000/...",             │
│        "report_id": "...",                                  │
│        "format": "pdf" | "docx",                            │
│        "expires_in_seconds": 900,                           │
│        "file_size_bytes": 12997                             │
│      }                                                       │
│                                                              │
│  🔒 Security: MinIO anonymous download DISABLED             │
│     All access MUST go through pre-signed URLs              │
└─────────────────────────────────────────────────────────────┘
```

---

### 🐕 Reporter Watchdog

**File:** `backend/services/reporter/watchdog.py`  
**Trigger:** APScheduler job every 5 minutes

```sql
-- Query for stuck reports
SELECT * FROM reports
WHERE status = 'generating'
AND created_at < NOW() - report_watchdog_stale_minutes (30 min)

-- For EACH stuck report
UPDATE reports SET 
  status = 'failed', 
  error_detail = 'watchdog recovery'
WHERE report_id = :report_id
```

---

## 🎯 Final Outputs & Deliverables

### 📊 PostgreSQL Database Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `programs` | Bug bounty programs | `program_id`, `platform`, `handle`, `name`, `is_active`, `queued_for_scan` |
| `program_scopes` | Program scope entries | `scope_id`, `program_id`, `scope_type`, `value`, `is_positive` |
| `program_policies` | Program policies | `policy_id`, `program_id`, `bounty`, `vuln_requirements` |
| `scans` | Scan execution records | `scan_id`, `program_id`, `status`, `finding_count`, `severity_breakdown` |
| `scan_stages` | Stage execution logs | `stage_id`, `scan_id`, `stage_number`, `stage_name`, `status` |
| `assets` | Discovered web assets | `asset_id`, `scan_id`, `asset_type`, `value`, `technology_stack` |
| `endpoints` | Discovered URL endpoints | `endpoint_id`, `asset_id`, `scan_id`, `method`, `path`, `full_url` |
| `js_assets` | Downloaded JS files | `js_asset_id`, `scan_id`, `url`, `content_hash`, `storage_path` |
| `findings` | Vulnerability findings | `finding_id`, `scan_id`, `title`, `vulnerability_type`, `severity`, `cvss_score` |
| `reports` | Generated report files | `report_id`, `scan_id`, `format`, `status`, `storage_path` |

---

### 💾 MinIO Storage (S3-compatible)

| Bucket | Path Pattern | Content | Created By |
|--------|--------------|---------|------------|
| `reports` | `reports/{report_id}/report.pdf` | PDF report | Reporter Worker |
| `reports` | `reports/{report_id}/report.docx` | DOCX report | Reporter Worker |
| `js-assets` | `js-assets/{scan_id}/{hash}.js` | Downloaded JS files | Core Worker (Stage 3) |
| `evidence` | `evidence/{scan_id}/...` | Screenshots, HTTP logs | (Future - Reporter) |
| `summaries` | `summaries/{scan_id}/...` | Scan summaries | (Future) |

---

### 📡 RabbitMQ Queues

| Queue | Producer | Consumer | Message Type | Purpose |
|-------|----------|----------|--------------|---------|
| `scan.jobs` | Scraper, Core Engine | Core Worker | `program.scraped` | Trigger scan pipeline |
| `report.jobs` | Core Worker (Stage 10) | Reporter Worker | `scan.completed` | Trigger report generation |
| `reports.completed` | Reporter Worker | (Future) | `report.generated` | Notify report ready |
| `scan.jobs.dlq` | RabbitMQ (auto) | Manual inspection | Failed messages | Dead-letter queue |
| `report.jobs.dlq` | RabbitMQ (auto) | Manual inspection | Failed messages | Dead-letter queue |

---

## ⚠️ Error Handling & Failure Modes

### 🔴 FATAL ERRORS (Scan Aborts)

| Stage | Error Condition | Action |
|-------|----------------|--------|
| **Stage 0** | Scope is empty | `ScanError` raised, scan marked `failed_scope` |
| **Stage 10** | Aggregation fails | Scan marked `failed_internal` |

---

### 🟡 NON-FATAL ERRORS (Scan Continues)

| Stage | Error Condition | Action |
|-------|----------------|--------|
| **Stage 1** | Asset Discovery fails | Logged, scan continues with empty assets, skip to Stage 10 |
| **Stage 2** | Fingerprinting fails | Logged, scan continues with unenriched assets |
| **Stage 3** | Enumeration fails | Logged, scan continues without endpoints/JS files |
| **Stage 4** | Nuclei Scan fails | Logged, scan continues without Nuclei findings |
| **Stage 5** | Web Vuln Tests fail | Logged, scan continues without web vuln findings |
| **Stage 6** | JS Secrets fail | Logged, scan continues without JS secret findings |

---

### 🔴 Scan Status Values

| Status | Meaning | When Set |
|--------|---------|----------|
| `pending` | Scan queued but not started | On scan creation |
| `running` | Scan pipeline in progress | When Core Worker picks up message |
| `completed` | All stages succeeded | Stage 10 (no errors) |
| `partial` | Some non-fatal stages failed | Stage 10 (with errors) |
| `failed_scope` | Stage 0 failed (empty scope) | Stage 0 or scan_task |
| `failed_internal` | Fatal error in pipeline | Stage 10 or watchdog |
| `queued` | Scan job published but not picked up | Scraper/Core Engine |

---

### 🟡 Report Status Values

| Status | Meaning | When Set |
|--------|---------|----------|
| `generating` | Report generation in progress | On report row creation |
| `completed` | Report generated and uploaded | After successful upload |
| `failed` | Report generation failed | On exception or watchdog |

---

### 🔴 Exception Hierarchy

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

## 📈 E2E Test Flow Analysis

**Test:** `test_hackerone_scrape_scan_report_replay_e2e`  
**File:** `E2E_Runs/E2E_HACKERONE_M4_RUN_WITH_FIXES.json`

### Summary

```
Started:  2026-04-06T00:58:22.922599+00:00
Finished: 2026-04-06T01:04:04.745220+00:00
Duration: ~5m 42s
Result:   passed_with_fallback
```

### Key Observations

#### ✅ What Worked

1. **Service Health Checks Passed**
   - Scraper: ✅ healthy
   - Core Engine: ✅ healthy
   - Reporter: ⚠️ degraded (attack_graph_engine not available)

2. **Fallback Mechanism Activated**
   - Fresh scan `7ee68848` timed out after 5 minutes
   - System gracefully fell back to previous scan `a88c183e` from March 29
   - This is **KEY FEATURE**: Graceful degradation when fresh scan fails

3. **Report Generation Succeeded**
   - PDF: 12,997 bytes
   - DOCX: 38,715 bytes
   - Reports were NOT regenerated (returned existing artifacts from DB)

#### ⚠️ Issues Identified

1. **Watchdog Bug Detected**
   - Scan `7ee68848` started on `2026-04-05T12:57:45`
   - Still running after **12+ hours**
   - Watchdog should have marked it `failed_internal` after 2 hours
   - **Action:** Check `core_engine/watchdog.py` - watchdog may not be firing

2. **Phase 3 Fix Not Landed**
   - Wildcard DNS replay commands still **scheme-less**:
     ```bash
     curl -i -sS '3BbW9p14UnI5YWxkqrvGOC0S5ns-...nummus.robinhood.com'
     ```
   - Should be:
     ```bash
     curl -i -sS 'http://3BbW9p14UnI5YWxkqrvGOC0S5ns-...nummus.robinhood.com'
     ```
   - URL normalization (`_canonicalize_url`) not applied in E2E harness
   - Fix needed in test harness, not reporter

3. **Reports Not Regenerated**
   - Reporter returned existing artifacts (from March 29)
   - File sizes identical to previous run
   - To verify Phase 1 fixes, need to delete existing reports and regenerate

---

## 📋 Service & Function Inventory

### 🏗️ Services

| # | Service | Port | Status | Purpose | File |
|---|---------|------|--------|---------|------|
| 1 | API Gateway | 8000 | 🟡 Skeleton | Health aggregation, reverse proxy | `backend/services/api_gateway/main.py` |
| 2 | Scraper | 8001 | ✅ Active | Program discovery, scan job publishing | `backend/services/scraper/main.py` |
| 3 | Core Engine | 8002 | ✅ Active | Scan orchestration API | `backend/services/core_engine/main.py` |
| 4 | Core Worker | — | ✅ Active | Celery worker, 10-stage pipeline | `backend/services/core_engine/worker.py` |
| 5 | Reporter | 8003 | ✅ Active | Report generation & download API | `backend/services/reporter/main.py` |
| 6 | Reporter Worker | — | ✅ Active | Celery worker, report generation | `backend/services/reporter/worker.py` |
| 7 | Attack Graph Engine | 8006 | 🟡 Skeleton | Neo4j-backed exploit chain analysis | `backend/services/attack_graph_engine/main.py` |

---

### 👷 Workers

| Queue | Worker | Status | Purpose |
|-------|--------|--------|---------|
| `scan.jobs` | core-worker | ✅ Active | 10-stage scanning pipeline |
| `report.jobs` | reporter-worker | ✅ Active | PDF/DOCX report generation |
| `browser.jobs` | browser-worker | 🟡 Skeleton | Headless Chrome scanning |
| `api.fuzz.jobs` | api-fuzzer-worker | 🟡 Skeleton | API endpoint fuzzing |
| `js.analysis.jobs` | js-analysis-worker | 🟡 Skeleton | Deep JS static analysis |
| `scenario.jobs` | scenario-runner | 🟡 Skeleton | Multi-step attack scenarios |
| `verify.jobs` | exploit-verifier | 🟡 Skeleton | Automated exploit verification |
| `ai.analysis.jobs` | ai-analysis-worker | 🟡 Skeleton | AI-powered vulnerability analysis |

---

### 🗄️ Infrastructure Services

| Service | Port | Purpose | Data |
|---------|------|---------|------|
| PostgreSQL | 5432 | Primary relational DB | programs, scans, findings, reports, assets |
| Redis | 6379 | Distributed locking | scan locks, scraper locks |
| RabbitMQ | 5672 | Message bus | 9 queues + DLQs |
| MinIO | 9000 | Object storage | reports, evidence, js-assets, summaries |
| Neo4j | 7687 | Graph DB | Attack chains (future) |
| Vault | 8200 | Secrets management | API keys, credentials |

---

## 🎯 Complete Flow Summary

### From Request to Report

```
EXTERNAL TRIGGER (APScheduler/HTTP)
        ↓
SCRAPER (:8001)
  → Discovers programs from HackerOne
  → Publishes to scan.jobs
        ↓
CORE WORKER (Celery)
  → Consumes from scan.jobs
  → Runs 10-stage pipeline:
      Stage 0: Scope Filter (FATAL)
      Stage 1: Asset Discovery (subfinder→alterx→dnsx→httpx)
      Stage 2: Fingerprinting (httpx tech-detect)
      Stage 3: Enumeration (ffuf + waybackurls + JS download) ─┐
      Stage 4: Nuclei Scan (template vuln scanning) ───────────┘ parallel
      Stage 5: Web Vuln Tests (XSS, CORS, sensitive paths) ─┐
      Stage 6: JS Secrets (regex pattern matching) ─────────┘ parallel
      Stage 10: Aggregation (dedup + persist + publish)
        ↓
REPORTER WORKER (Celery)
  → Consumes from report.jobs
  → Generates PDF/DOCX
  → Uploads to MinIO
        ↓
REPORTER (:8003)
  → Provides download API
  → Returns pre-signed URLs
        ↓
CLIENT
  → Downloads reports via pre-signed URLs
```

---

### Execution Timeline (Normal Full Scan)

| Step | Phase | Service | Duration | What Happens |
|------|-------|---------|----------|--------------|
| 1 | Request Entry | Scraper | Instant | Scheduled scrape or manual trigger |
| 2 | Program Discovery | Scraper | 1-5 min | HackerOne API scraping, program upsert |
| 3 | Scan Job Publish | Scraper | Instant | Message published to scan.jobs |
| 4 | Scan Queueing | Core Engine | Instant | Scan row created, status="pending" |
| 5 | Worker Pickup | Core Worker | <1s | Celery worker picks up message |
| 6 | Stage 0 | Core Worker | <1s | Validate scope (FATAL if empty) |
| 7 | Stage 1 | Core Worker | 20-40 min | subfinder→alterx→dnsx→httpx |
| 8 | Stage 2 | Core Worker | 5-10 min | httpx tech-detect on all assets |
| 9 | Stage 3+4 (Parallel) | Core Worker | 30-60 min | ffuf + waybackurls + JS / Nuclei |
| 10 | Stage 5+6 (Parallel) | Core Worker | 5-10 min | XSS/CORS tests + JS secret scanning |
| 11 | Stage 10 | Core Worker | <1s | Dedup, persist findings, publish to report.jobs |
| 12 | Report Queueing | Reporter | Instant | Message published to report.jobs |
| 13 | Report Generation | Reporter Worker | 2-5 min | PDF + DOCX generation, upload to MinIO |
| 14 | Download Ready | Reporter | Instant | Pre-signed URLs generated |
| **Total** | | | **~65-135 min** | **Full scan + report generation** |

---

### All Services Triggered

| # | Service/Worker | Trigger | Purpose |
|---|---------------|---------|---------|
| 1 | Scraper | Scheduled/HTTP | Discover programs, queue scans |
| 2 | Core Engine API | HTTP | Scan management API |
| 3 | Core Worker | RabbitMQ (scan.jobs) | Execute 10-stage pipeline |
| 4 | Scraper (Reconciler) | APScheduler (5 min) | Recover failed scan publishes |
| 5 | Core Engine (Watchdog) | APScheduler (5 min) | Recover stuck scans |
| 6 | Reporter API | HTTP | Report management API |
| 7 | Reporter Worker | RabbitMQ (report.jobs) | Generate reports |
| 8 | Reporter (Watchdog) | APScheduler (5 min) | Recover stuck reports |

---

## 📚 Message Schemas

### MessageEnvelope

**File:** `backend/shared/schemas/envelope.py`

```json
{
  "event_id": "uuid4()",
  "event_type": "noun.verb",
  "schema_version": "1.0",
  "timestamp": "ISO 8601 datetime",
  "trace_id": "optional-uuid",
  "source_service": "scraper|core_engine|reporter",
  "payload": { ... }
}
```

### ScanJobsPayload

**File:** `backend/shared/schemas/scan_jobs.py`

```json
{
  "program_id": "uuid",
  "scope": {
    "in_scope": [
      {"type": "domain", "value": "example.com"},
      {"type": "wildcard_domain", "value": "*.example.com"}
    ],
    "out_of_scope": [
      {"type": "domain", "value": "internal.example.com"}
    ]
  },
  "feature_flags": {
    "nuclei": true,
    "waybackurls": true,
    "ffuf": true,
    "browser": false
  },
  "priority": 5
}
```

### ReportJobsPayload

**File:** `backend/shared/schemas/report_jobs.py`

```json
{
  "scan_id": "uuid",
  "program_id": "uuid",
  "status": "completed",
  "partial_stages": ["nuclei_scan"],
  "has_findings": true,
  "finding_count": 11,
  "verified_count": 0,
  "severity_breakdown": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "informational": 11
  },
  "exploit_chains": [],
  "formats_requested": ["pdf", "docx"],
  "report_ids": {
    "pdf": "uuid",
    "docx": "uuid"
  },
  "include_evidence_screenshots": true
}
```

---

## 🎓 Key Design Decisions

### 1. Scope Safety is Non-Negotiable
The `ScopeFilter` is built at Stage 0 and threaded through every stage. If scope is empty, the scan aborts immediately. Every URL discovered by any tool is validated against scope before being used. **Out-of-scope always wins over in-scope.**

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

## ✅ YOU NOW HAVE THE COMPLETE END-TO-END FLOW

This document covers every:

- ✅ Request entry point
- ✅ Step in the pipeline
- ✅ Service triggered
- ✅ Function called
- ✅ Side process running
- ✅ Database write
- ✅ Storage operation
- ✅ Message queue interaction
- ✅ Background process
- ✅ Error handling path

---

**Generated from:** Complete end-to-end pipeline documentation  
**Date:** 2026-04-19  
**Branch:** M4_ReadTheRoom  
**Architecture:** Event-driven microservices with RabbitMQ message bus