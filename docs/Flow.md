# AttackBot — Comprehensive System Flow

> Version: 2.0 | Last updated: 2026-03-24
> Purpose: Low-level, implementation-grounded walkthrough of how every piece of data, every trigger, every function call, and every decision flows through the AttackBot system — from bug bounty program discovery to report generation.
> Scope: This document maps directly to the code in `backend/`. Every function, file, and queue referenced here exists in the current codebase. Planned-only features are explicitly marked.

---

## Table of Contents
1. [System Entry Points](#1-system-entry-points)
2. [Phase 1 — Program Ingestion (Scraper)](#2-phase-1--program-ingestion-scraper)
3. [Phase 2 — Scan Orchestration (Core Engine)](#3-phase-2--scan-orchestration-core-engine)
4. [Phase 3 — Pipeline Execution (Stages 0–6, 10)](#4-phase-3--pipeline-execution-stages-06-10)
5. [Phase 4 — Browser Session Bootstrap (Stage 3.5)](#5-phase-4--browser-session-bootstrap-stage-35) *(planned: M5)*
6. [Phase 5 — API Fuzzing + JS Analysis (Stages 4.5 + 6)](#6-phase-5--api-fuzzing--js-analysis-stages-45--6) *(planned: M6)*
7. [Phase 6 — Behavioral Scenarios (Stage 7)](#7-phase-6--behavioral-scenarios-stage-7) *(planned: M9)*
8. [Phase 7 — Exploit Verification (Stage 8)](#8-phase-7--exploit-verification-stage-8) *(planned: M7)*
9. [Phase 8 — AI Hypothesis (Stage 9)](#9-phase-8--ai-hypothesis-stage-9) *(planned: M10)*
10. [Phase 9 — Aggregation (Stage 10)](#10-phase-9--aggregation-stage-10)
11. [Phase 10 — Report Generation (Reporter)](#11-phase-10--report-generation-reporter)
12. [Phase 11 — Manual Submission](#12-phase-11--manual-submission)
13. [Failure Flows](#13-failure-flows)
14. [Data Lifecycle Summary](#14-data-lifecycle-summary)
15. [Decision Points and Guards](#15-decision-points-and-guards)
16. [Code-to-Flow Reference Map](#16-code-to-flow-reference-map)

---

## 1. System Entry Points

There are two ways a scan begins. Both converge on the same queue (`scan.jobs`).

### Entry Point A — Scheduled Scrape (Automatic)

**File:** `backend/services/scraper/main.py` → `lifespan()` → APScheduler

1. On startup, the Scraper's `lifespan()` function registers two APScheduler jobs:
   - `_run_platform_scrape("hackerone")` — runs on a configurable interval (e.g., every 6h)
   - `_publish_due_scan_jobs()` — runs on a configurable interval, publishes scan messages for programs due for rescan
2. When the scrape job fires, `_run_platform_scrape(platform)` acquires a Redis lock (`scraper:lock:{platform}`) to prevent concurrent scrapes of the same platform.
3. The platform collector (e.g., `HackerOneCollector`) fetches programs from the platform API.
4. Each program is normalized and upserted into `programs`, `program_scopes`, and `program_policies`.
5. Separately, the `_publish_due_scan_jobs()` scheduler finds programs that need scanning and publishes `scan.jobs` messages.
6. The Core Worker picks up the message and begins the scan.

### Entry Point B — Manual Trigger (On-Demand)

1. A `POST /api/v1/scrape/trigger?platform=hackerone` request arrives at the Scraper service.
   - **File:** `backend/services/scraper/main.py` → `trigger_scrape()`
   - Calls `_run_platform_scrape(platform)` directly, outside the scheduler.
2. A `POST /api/v1/scrape/publish-batch?batch_size=N` request triggers immediate scan job publishing.
   - **File:** `backend/services/scraper/main.py` → `trigger_scan_publish_batch()`
   - Calls `_publish_due_scan_jobs(batch_size)` immediately.
3. Alternatively, a scan can be started directly via the Core Engine:
   - `POST /api/v1/scans/start` with `{"program_id": "uuid"}` on the Core Engine (:8002).
   - **File:** `backend/services/core_engine/main.py` → `start_scan()`
   - This fetches the program and scope from the Scraper API, builds a `ScanJobsPayload`, and enqueues it to `scan.jobs`.

### Entry Point C — Core Engine Direct Dispatch

**File:** `backend/services/core_engine/main.py` → `start_scan()` → `_build_payload_from_scraper()` → `_enqueue_scan()`

1. `_build_payload_from_scraper()` calls the Scraper's `GET /api/v1/programs/{program_id}` and `GET /api/v1/programs/{program_id}/scope` APIs.
2. The scope entries are parsed into `ScopeDefinition` format.
3. A `ScanJobsPayload` is constructed with program metadata, scope, feature flags, and priority.
4. `_enqueue_scan()` wraps the payload in a `MessageEnvelope` via `build_scan_job_message()` and calls `QueuePublisher.publish("scan.jobs", message)`.
5. On success, returns the scan ID. On publish failure, raises `HTTPException(503)`.

### What never triggers a scan
- A program already in-progress (`scan:lock:{program_id}` Redis lock held).
- A program that failed scope resolution in its last scan (until re-scraped and re-evaluated).
- A program that has hit `retry_count >= 2` on internal failures.

---

## 2. Phase 1 — Program Ingestion (Scraper)

**Service:** `scraper` (:8001)
**Workers:** None (APScheduler runs inside the FastAPI process)
**Inputs:** Platform API (HackerOne, BugCrowd, Intigriti, YesWeHack)
**Outputs:** Rows in `programs`, `program_scopes`, `program_policies`; message on `scan.jobs`

### Internal Module Map

| Module | File | Responsibility |
|--------|------|----------------|
| Config | `config.py` | `ScraperConfig(BaseServiceConfig)` — HackerOne credentials, intervals |
| Collectors | `collectors/base.py` | `BaseCollector` ABC + `CollectorRegistry` |
| HackerOne | `collectors/hackerone.py` | `HackerOneCollector` — API v1, 429 retry, structured_scopes |
| Scope | `scope_parser.py` | `ScopeParser` — typed `ProgramScope` objects |
| Repository | `repository.py` | `ProgramRepository` — upsert, scope/policy persistence |
| Publisher | `publisher.py` | `ScraperPublisher` — `QueuePublisher` wrapper with flag management |
| Reconciler | `reconciler.py` | APScheduler job — republishes failed-to-queue programs |
| Models | `models.py` | Pydantic models for programs |
| Main | `main.py` | FastAPI app, scheduler, all API routes |

### Step-by-step

**2.1 — Platform authentication**
- **File:** `collectors/hackerone.py` → `HackerOneCollector.__init__()`
- The collector loads platform credentials from environment config (`ScraperConfig`).
- For HackerOne: HTTP Basic Auth using API username + token.
- These come from environment variables `HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN`.

**2.2 — Paginated program listing**
- **File:** `collectors/hackerone.py` → `HackerOneCollector.collect()`
- The collector calls `GET /v1/hackers/programs` with pagination (`page[number]`, `page[size]=100`).
- It iterates until the API returns an empty `data` array.
- Each page is processed immediately — the full list is never held in memory at once.

**2.3 — 429 handling**
- **File:** `collectors/hackerone.py`
- On every API request: if `HTTP 429` is returned, the collector reads the `Retry-After` header and sleeps for that duration, then retries.
- After `max_retries=3` consecutive 429s, `CollectorRateLimitError` is raised and the scrape job is marked failed for that platform.
- The scheduler will retry on the next cycle.

**2.4 — Per-program detail fetch**
- **File:** `collectors/hackerone.py`
- For each program in the listing, the collector calls:
  - `GET /v1/hackers/programs/{handle}` for full details
  - `GET /v1/hackers/programs/{handle}/structured_scopes` for parsed scope entries
- Raw markdown scope parsing is never used — structured scopes are always preferred.

**2.5 — Normalization**
- **File:** `collectors/hackerone.py` → normalizer logic
- The raw platform response is mapped to the canonical program structure:
  - `platform` (hackerone, bugcrowd, etc.)
  - `handle` (unique identifier on the platform)
  - `bounty_type` (bug_bounty or vdp)
  - `max_bounty`
  - `is_active`
  - Nested: `in_scope` and `out_of_scope` scope entries

**2.6 — Scope parsing**
- **File:** `scope_parser.py` → `ScopeParser`
- Converts raw scope entries into typed `ProgramScope` objects. Handles:
  - `*.example.com` → wildcard domain, stored as `wildcard_domain` asset type
  - `192.168.1.0/24` → CIDR range, stored as `ip_range`
  - `https://example.com/api/` → URL with path prefix
  - `com.example.app` → mobile app bundle identifier
- Each scope entry is stored in `program_scopes` with a `scope_type` (in_scope or out_of_scope).

**2.7 — Upsert**
- **File:** `repository.py` → `ProgramRepository.upsert()`
- Performs an `INSERT ... ON CONFLICT DO UPDATE`.
- Critical rule: if the program already exists with `queued_for_scan=True`, that flag is NOT overwritten during re-scrape.
- This prevents the reconciler from losing track of programs that failed to publish.

**2.8 — Queue publish**
- **File:** `main.py` → `_publish_due_scan_jobs()`
- Queries programs due for rescan (based on last_scraped_at and configurable interval).
- For each eligible program, calls `ScraperPublisher.publish_scan_job()`.
- The `ScraperPublisher` uses `backend/shared/schemas/scan_jobs.py` → `build_scan_job_message()` to construct the `MessageEnvelope`, then `QueuePublisher.publish("scan.jobs", message)`.
- **Envelope structure:**
  - `event_type`: `"program.scraped"`
  - `schema_version`: `"1.0"`
  - `payload`: `ScanJobsPayload` containing `program_id`, `scope`, `feature_flags`, `priority`
- On publish success: `queued_for_scan` is cleared.
- On publish failure: `queued_for_scan` is set to `True` and the reconciler handles retry.

**2.9 — Reconciler**
- **File:** `reconciler.py`
- An APScheduler job runs on a configurable interval (default: every 5 minutes).
- Queries `programs WHERE queued_for_scan = True AND last_scraped_at > NOW() - INTERVAL '7 days'`.
- For each: republishes to `scan.jobs`. On success, clears the flag. On failure, leaves it.
- Programs older than 7 days are not auto-retried — they require a new scrape.

**2.10 — Redis lock**
- **File:** `main.py` → `_run_platform_scrape()`
- A per-platform Redis lock (`scraper:lock:{platform}`) prevents two scrape jobs for the same platform from running simultaneously.
- Lock TTL is set to 2x the expected scrape duration.
- If the lock cannot be acquired, the job is skipped for that cycle.

---

## 3. Phase 2 — Scan Orchestration (Core Engine)

**Service:** `core-engine` (:8002) + `core-worker` (Celery)
**Queue consumed:** `scan.jobs`
**Queue produced:** `report.jobs`

### Internal Module Map

| Module | File | Responsibility |
|--------|------|----------------|
| Worker | `worker.py` | Celery app, `scan_task()` entry point |
| Scan Task | `scan_task.py` | `run_scan_task()`, `_async_scan_pipeline()`, `_execute_pipeline()` |
| Repository | `repository.py` | `ScanRepository` — DB operations for scans, assets, endpoints, findings |
| Models | `models.py` | `DiscoveredAsset`, `DiscoveredEndpoint`, `DiscoveredJsAsset`, `FindingCandidate`, `ScanResult` |
| Config | `config.py` | `EngineConfig` — nuclei/httpx/ffuf tuning, timeouts |
| Dedup | `dedup.py` | `compute_dedup_hash()` — SHA-256 deduplication |
| CVSS | `cvss.py` | `severity_to_cvss()`, `nuclei_severity()` |
| Subprocess | `subprocess_utils.py` | `run_tool_communicate()`, `parse_jsonl()` |
| Watchdog | `watchdog.py` | Stuck scan detection |
| Startup | `startup_checks.py` | `collect_toolchain_checks()` — nuclei binary validation |
| Main | `main.py` | FastAPI app, scan APIs, watchdog scheduler |

### Step-by-step

**3.1 — Message receipt (worker.py)**
- **File:** `worker.py` → `scan_task()`
- The `core-worker` Celery process receives a message from `scan.jobs`.
- The Celery task is configured with:
  - `task_acks_late=True` — message is NOT acknowledged until the task function returns
  - `task_reject_on_worker_lost=True` — NACK on worker death; message goes to DLQ
  - `worker_prefetch_multiplier=1` — one task at a time per worker
  - `max_retries=0` — no Celery auto-retry; watchdog handles retry logic
- On receipt, the task:
  1. Deserializes `raw message dict` → `MessageEnvelope`
  2. Validates `event_type == "program.scraped"` and `schema_version == "1.x"`
  3. Extracts `ScanJobsPayload` from `envelope.payload`
  4. Calls `run_scan_task(payload)`

**3.2 — Scan task entry (scan_task.py → run_scan_task)**
- **File:** `scan_task.py` → `run_scan_task(payload)`
- This is a **synchronous wrapper** that runs `asyncio.run(_async_scan_pipeline(payload))`.
- If the payload is a `dict` (not yet a Pydantic model), it's validated into `ScanJobsPayload` first.

**3.3 — Async pipeline (scan_task.py → _async_scan_pipeline)**
- **File:** `scan_task.py` → `_async_scan_pipeline(payload)`
- This is the core pipeline orchestrator. Steps:

  **a. Initialize infrastructure:**
  - Load `EngineConfig()`
  - Initialize DB via `init_db()`
  - Initialize MinIO storage via `init_storage()`

  **b. Fetch scope from Scraper API:**
  - Calls `_fetch_scope_from_scraper(program_id, config)`
  - Makes `GET /api/v1/programs/{program_id}/scope` on the Scraper service
  - If scope is empty or the API returns an error: `ScanError` is raised → scan marked `failed_scope`

  **c. Build ScanContext:**
  - `ScopeDefinition.from_shared()` converts the shared schema to the pipeline's internal dataclass
  - `FeatureFlags.from_shared()` converts feature flags
  - `ScanContext` bundles: `scan_id`, `program_id`, `scope`, `feature_flags`, `priority`
  - `ScanContext` is immutable — stages must not modify it

  **d. Create or resume scan record:**
  - `ScanRepository.create_or_resume_scan()` is called within a DB session
  - If a `running` scan already exists for this program: it is reused (prevents duplicates after crash)
  - If a `failed_internal` scan exists with `retry_count < 2`: it is reused and `retry_count` is incremented
  - Otherwise: a new row in `scans` with `status=pending`

  **e. Acquire Redis scan lock:**
  - Redis lock key: `scan:lock:{program_id}`
  - If the lock is already held: task returns immediately without running
  - The message is acknowledged (not requeued) — the existing scan will produce results

  **f. Execute pipeline:**
  - Calls `_execute_pipeline(ctx, scan_result, repo, publisher, config)`
  - On unhandled exception: scan is marked `failed_internal`

**3.4 — Watchdog (main.py + watchdog.py)**
- **File:** `main.py` → `lifespan()` registers APScheduler job, `watchdog.py` → `check_stuck_scans()`
- Runs every 15 minutes.
- Queries `scans WHERE status='running' AND started_at < NOW() - INTERVAL '2 hours'`.
- For each stuck scan:
  - Status is updated to `failed_internal`, `error_detail='watchdog_timeout'`
  - If `retry_count < 2`: the scan is republished to `scan.jobs` with a fresh `MessageEnvelope`
  - The Redis lock is released

---

## 4. Phase 3 — Pipeline Execution (Stages 0–6, 10)

All stages run inside the `core-worker` process via `_execute_pipeline()` in `scan_task.py`.

**File:** `scan_task.py` → `_execute_pipeline(ctx, scan_result, repo, publisher, config)`

The pipeline runs stages in this exact order:

```
Stage 0 (scope_filter)     → builds ScopeFilter [FATAL on failure]
Stage 1 (asset_discovery)   → discovers live assets
Stage 2 (fingerprinting)    → enriches assets with tech stack
Stage 3 (enumeration)       → path/directory discovery + JS download
Stage 4 (nuclei_scan)      ┐
                             ├── run in PARALLEL (asyncio.gather)
Stage 5 (web_vuln_tests)   ┘
Stage 6 (js_secrets)        → regex secret scanning on JS files
Stage 10 (aggregator)       → dedup, persist, group, publish to report.jobs [FATAL on failure]
```

Each stage is wrapped in try/except. Non-fatal stages log errors to `scan_result.stage_errors[stage_name]` and continue. Fatal stages (`0` and `10`) cause the pipeline to abort.

### Stage 0 — Scope Filter (FATAL)

**File:** `pipeline/scope_filter.py` → `ScopeFilter.__init__()`
**Called from:** `_execute_pipeline()` — first thing

- `ScopeFilter` is constructed from the `ScopeDefinition` in `ScanContext`.
- The constructor checks: `if not scope.in_scope: raise ScanError(...)` — this is the fatal guard.
- The `ScopeFilter` stores:
  - `_in_scope`: list of scope rules (strings or dicts with `asset_type` + `value`)
  - `_out_of_scope`: list of exclusion rules
  - `_in_networks`: list of parsed `ipaddress.IPv4Network`/`IPv6Network` objects (for CIDR matching)
  - `_out_networks`: same for exclusions

**How scope matching works (`ScopeFilter.is_in_scope(target)`):**
1. Extract the hostname from the target URL/string via `_extract_domain()`
2. Attempt to parse it as an IP address via `_try_parse_ip()`
3. Check out-of-scope first: if the target matches ANY out-of-scope rule → **reject** (out-of-scope always wins)
4. Check in-scope: target must match at least one in-scope rule → **accept**
5. Rule matching (`_matches_rule`) handles three cases:
   - `asset_type == "wildcard_domain"` or rule starts with `*.` → subdomain-only match (e.g., `*.example.com` matches `sub.example.com` but NOT `example.com`)
   - `asset_type == "domain"` → root domain + all subdomains
   - Plain string → exact host match

### Stage 1 — Asset Discovery

**File:** `pipeline/asset_discovery.py` → `run(ctx, scope_filter, config)`

**Purpose:** Discover live HTTP hosts within scope using subdomain enumeration + DNS resolution + HTTP probing.

**Step-by-step:**

1. **Seed extraction** — `_extract_seed_domains(in_scope, scope_filter)`:
   - Domain and wildcard_domain scope rules are always seed candidates
   - URL rules are seed candidates only when HTTP(S) and their hostname is covered by in-scope domain/wildcard rules
   - Non-web scope types (mobile_app, api, ip_range) are skipped
   - Result: a deduplicated list of seed domains

2. **Per-domain discovery pipeline** — `_discover_domain(domain, scope_filter, config)`:
   - Run each tool via `subprocess_utils.run_tool_communicate()` — this creates an `asyncio.subprocess`, captures stdout/stderr, enforces a timeout, and raises on non-zero exit codes

   **a. subfinder** — passive subdomain enumeration:
   ```
   subfinder -d {domain} -all -silent
   ```
   - Reads stdout line-by-line (streaming — large output)
   - Output: list of subdomains like `api.example.com`, `dev.example.com`

   **b. alterx** — permuted subdomain generation:
   ```
   alterx -silent
   ```
   - Takes subfinder output as stdin
   - Generates permutations: `api-dev.example.com`, `staging.api.example.com`, etc.
   - Output: expanded subdomain list

   **c. dnsx** — DNS resolution:
   ```
   dnsx -l {targets_file} -a -resp -silent
   ```
   - Resolves each permuted subdomain to check if it actually exists
   - **This step is mandatory** — skipping it sends thousands of non-existent hosts to httpx

   **d. httpx** — HTTP probing:
   ```
   httpx -l {targets_file} -json -silent -status-code -title -tech-detect -no-color
   ```
   - Probes all resolved hosts for live HTTP services
   - Collects: status code, title, technology hints, content_type, webserver
   - Output: JSONL with one JSON object per live asset

3. **Scope filtering** — `scope_filter.filter_targets()`:
   - Every discovered asset is tested against `ScopeFilter` before being recorded
   - Out-of-scope assets are dropped and logged
   - In-scope assets become `DiscoveredAsset` objects

4. **Deduplication** — `_dedupe_assets_by_origin(assets)`:
   - Canonical origin key: `{scheme}://{host}:{port}` (default ports omitted)
   - First-seen wins for all fields; later duplicates only fill null fields

5. **Persistence:**
   - `ScanRepository.save_assets()` persists each `DiscoveredAsset` to the `assets` table
   - Each asset gets an `asset_id` (UUID) stamped after DB insert
   - The list of asset URLs is stored in `ctx.live_assets` for downstream stages

### Stage 2 — Fingerprinting

**File:** `pipeline/fingerprinting.py` → `run(ctx, assets, config)`

**Purpose:** Enrich already-discovered assets with detailed technology stack and WAF information.

**Step-by-step:**

1. Write all asset URLs to a temp file
2. Run **httpx** with extended fingerprinting:
   ```
   httpx -l {targets_file} -json -silent -tech-detect -status-code -title -no-color
   ```
3. Parse JSONL output into a lookup dict keyed by `_normalize_url_for_lookup()`:
   - URL normalization: lowercase scheme + host, strip default ports (80/443), strip trailing slashes
   - Both `input` and `url` keys from httpx output are registered (handles redirects)
4. For each existing asset, look up the fingerprint and update:
   - `asset.http_status` = httpx status code
   - `asset.technology_stack` = `{"technologies": [...], "title": "...", "content_type": "...", "server": "..."}`
   - `asset.waf_detected` = result of `waf_utils.detect_waf_technology(tech_list)` — checks for known WAF technology names in the detected tech list
5. WAF presence is noted but does NOT block subsequent stages — all scanners still run.

### Stage 3 — Enumeration

**File:** `pipeline/enumeration.py` → `run(ctx, assets, scope_filter, config)`

**Purpose:** Directory/path discovery, historical URL fetch, and JavaScript file download.

**Step-by-step:**

1. For each in-scope asset, call `_enumerate_asset()`:

   **a. ffuf** — directory/path discovery — `_run_ffuf(asset, base_url, config)`:
   ```
   ffuf -u {base_url}/FUZZ -w {wordlist} -o {output_file} -of json -mc all -fc 404 -t {threads} -timeout {timeout}
   ```
   - The output JSON contains discovered paths with response codes
   - Each valid path becomes a `DiscoveredEndpoint`:
     - `method`: "GET"
     - `path`: the discovered path
     - `full_url`: base_url + path
     - `response_code`: HTTP status from ffuf
     - `asset_id`: from the parent asset

   **b. waybackurls** — historical URL discovery — `_run_waybackurls(asset, base_url, scope_filter, config)`:
   ```
   waybackurls {domain}
   ```
   - Pulls historical URL data from the Wayback Machine and Common Crawl
   - Each discovered URL is scope-filtered (`scope_filter.is_in_scope()`)
   - Valid URLs become `DiscoveredEndpoint` objects

2. **Endpoint deduplication** — `_dedupe_endpoints()`:
   - Key: `(method, host, path)` — duplicates are collapsed

3. **JavaScript file download** — `_download_and_store_js(ctx, js_url, scope_filter, config)`:
   - During enumeration, `.js` URLs are identified
   - Each JS file is downloaded via `httpx` (the Python HTTP client, not the CLI tool)
   - Content hash (SHA-256) is computed
   - If a JS asset with the same hash already exists in `js_assets` → skip (deduplication by content)
   - Otherwise: upload to MinIO bucket `js-assets/` via `upload_bytes()`
   - Create `DiscoveredJsAsset` with: `scan_id`, `url`, `storage_path`, `content_hash`, `size_bytes`
   - `ScanRepository.save_js_asset()` persists to `js_assets` table (INSERT ON CONFLICT on content_hash is a no-op)
   - JS asset IDs are stored in `ctx.js_asset_ids` for Stage 6

4. **Persistence:**
   - All endpoints are persisted via `ScanRepository.save_endpoints()`

### Stages 4 + 5 — Parallel Execution

**File:** `scan_task.py` → `_execute_pipeline()` — uses `asyncio.gather()`

```python
results = await asyncio.gather(
    nuclei_scan.run(ctx, assets, scope_filter, config),
    web_vuln_tests.run(ctx, endpoints, scope_filter, feature_flags),
    return_exceptions=True,
)
```

Both stages produce `list[FindingCandidate]` which are collected in `scan_result.finding_candidates`.

### Stage 4 — Nuclei Scanning

**File:** `pipeline/nuclei_scan.py` → `run(ctx, assets, scope_filter, config)`

**Purpose:** Run nuclei template-based vulnerability scanning against all live assets.

**Step-by-step:**

1. **Target list construction:**
   - Extract asset URLs: `[asset.value for asset in assets]`
   - Filter through `scope_filter.filter_targets()` — second scope check
   - Write targets to a temp file

2. **Nuclei execution:**
   ```
   nuclei -l {targets_file} -json -silent -rate-limit {config.nuclei_rate_limit}
          -bulk-size {config.nuclei_bulk_size} -concurrency {config.nuclei_concurrency}
          -exclude-tags headless
   ```
   - `-exclude-tags headless` — exclude browser-based templates (M5 handles those)
   - `-json -silent` — prevents status lines from mixing with JSON output
   - Timeout: `config.nuclei_timeout` (default 3600s), scaled by `config.scaled_timeout()` if available

3. **Exit code handling:**
   - `returncode==0`: normal completion (with or without findings)
   - `returncode==1`: zero findings (NOT an error)
   - `returncode==2`: startup failure — classified by `_classify_exit_code_2_reason()`:
     - `templates_configured_verify_path_or_contents`
     - `templates_missing_or_unreadable`
     - `target_resolution_or_parsing`
     - `empty_target_list`
     - `nuclei_startup_initialization_failure`

4. **Finding conversion:**
   - Parse stdout via `parse_jsonl()` — only lines starting with `{` are treated as JSON
   - For each nuclei result:
     - Extract `matched-at` URL and verify it's in scope
     - Map severity via `nuclei_severity()` (maps nuclei's severity strings to canonical values)
     - Create `FindingCandidate`:
       ```python
       FindingCandidate(
           vulnerability_type=f"nuclei_{template_id}",
           title=entry["info"]["name"],
           severity=severity,
           affected_url=matched_url,
           source="nuclei",
           cvss_score=severity_to_cvss(severity),
           raw_output=entry,  # full nuclei JSON preserved
       )
       ```
   - All candidates have `is_verified=False` (set during Stage 10 persistence)

### Stage 5 — Web Vulnerability Tests

**File:** `pipeline/web_vuln_tests.py` → `run(ctx, endpoints, scope_filter, feature_flags)`

**Purpose:** Active web vulnerability scanning against discovered endpoints.

**Step-by-step:**

1. Filter endpoints to in-scope only
2. For each endpoint, run `_test_endpoint()` via `asyncio.gather()` (parallelized):

   **a. Passive sensitive path detection** — `_passive_sensitive_path_findings(ep)`:
   - No HTTP requests needed — checks enumerated endpoint paths
   - Checks against `SENSITIVE_PATHS` dict:
     - `/.env` → "Exposed environment file" (critical)
     - `/.git/HEAD` → "Exposed Git metadata" (critical)
     - `/.git/config` → "Exposed Git config" (critical)
   - Only triggers if `ep.response_code` is one of: 200, 204, 301, 302, 307, 401, 403

   **b. XSS scanning** — `_test_xss(ep, client)`:
   - Three probe payloads:
     - `<script>alert(1)</script>`
     - `"><img src=x onerror=alert(1)>`
     - `';alert(1)//`
   - For each parameter (capped at 10 per endpoint):
     - Inject payload as parameter value
     - `GET {ep.full_url}?{param}={payload}`
     - If payload appears verbatim in response body → candidate finding
     - Break after first finding per parameter
   - `vulnerability_type="reflected_xss"`, `severity="high"`

   **c. CORS scanning** — `_test_cors(ep, client)`:
   - Three test origins:
     - `https://evil.com`
     - `null`
     - `https://attacker.example.com`
   - For each origin:
     - `GET {ep.full_url}` with `Origin: {origin}` header
     - Check: `Access-Control-Allow-Origin` reflects origin OR is `*`
     - AND: `Access-Control-Allow-Credentials: true`
     - Both conditions → candidate finding
   - `vulnerability_type="cors_misconfiguration"`, `severity="high"`

   **d. CRLF scanning** — `_test_crlf(ep, client)` *(gated by `feature_flags.crlf`)*:
   - Payload: `%0d%0aSet-Cookie:crlf=injected`
   - Appended to full URL
   - If `crlf=injected` appears in response headers → candidate finding
   - `vulnerability_type="crlf_injection"`, `severity="medium"`

   **e. SQLi, SSRF** — not yet implemented (placeholder comments; gated by feature flags, will be implemented in M6+)

3. All candidates are collected and returned. HTTP client is configured with:
   - `timeout=10.0`
   - `follow_redirects=False`
   - `verify=False` (TLS cert validation off — scanning targets may have invalid certs)

### Stage 6 — JS Secret Scanning

**File:** `pipeline/js_secrets.py` → `run(ctx, js_assets)`

**Purpose:** Regex-based secret detection in JavaScript files downloaded during Stage 3.

**Step-by-step:**

1. For each `DiscoveredJsAsset` in the list:
   - Download JS content from MinIO: `download_bytes(bucket="js-assets", object_name=...)`
   - Decode bytes to string (with error replacement)
   - Run `_scan_content(content, source_url)`

2. **Pattern matching** — `_scan_content()`:
   - 12 compiled regex patterns (compiled once at module load):

     | Pattern | Label | Severity |
     |---------|-------|----------|
     | `AIza[0-9A-Za-z\-_]{35}` | Google API Key | high |
     | `AAAA[A-Za-z0-9_\-]{7}:[A-Za-z0-9_\-]{140}` | Firebase Server Key | high |
     | `sk-[a-zA-Z0-9]{48}` | OpenAI API Key | critical |
     | `xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9a-fA-F]{24}` | Slack Token | high |
     | Generic API key assignment pattern | Generic API Key Assignment | medium |
     | Hardcoded password assignment | Hardcoded Password | high |
     | Secret/private key assignment | Hardcoded Secret Key | high |
     | JWT token pattern (`eyJ...`) | JWT Token | medium |
     | PEM private key header | Private Key | critical |
     | `ghp_[A-Za-z0-9]{36}` | GitHub Personal Access Token | critical |
     | AWS Access Key ID (`AKIA...`) | AWS Access Key ID | critical |
     | AWS Secret Access Key | AWS Secret Access Key | critical |

   - For each pattern that matches:
     - Take first match only (don't emit one finding per occurrence)
     - Create `FindingCandidate`:
       ```python
       FindingCandidate(
           vulnerability_type="js_secret",
           title=f"{label} found in JavaScript",
           severity=severity,
           affected_url=js_url,
           source="js_secrets",
           payload=match_preview[:80],
       )
       ```

3. Failures to download or parse individual JS files are logged as warnings but don't crash the stage.

---

## 5. Phase 4 — Browser Session Bootstrap (Stage 3.5) *(planned: M5 — not yet implemented)*

**Worker:** `browser-worker` (Celery)
**Queue:** `browser.jobs`
**Triggered:** After Stage 3 completes, if `ENABLE_BROWSER_SESSION=True`

> The `browser_worker/worker.py` currently exists as a skeleton with queue consumption setup. Stage 3.5 logic will be implemented in M5.

### Designed behavior (from Architecture):

- Core Engine publishes `session.request` to `browser.jobs`
- Browser Worker launches fresh Playwright Chromium context per job
- Scope enforcement via `browser_context.route("**/*", enforce_scope)` — out-of-scope requests are hard-blocked
- YAML login scenario executed step-by-step (visit, fill, submit, wait, capture_cookies)
- TOTP support via Vault secret resolution
- Session bundle (cookies, localStorage, headers, CSRF) encrypted with AES-256 and stored in `browser_sessions`
- Two-session bootstrap for IDOR verification (`primary` + `secondary` accounts)
- Session ID returned to Core Engine via Redis result backend

---

## 6. Phase 5 — API Fuzzing + JS Analysis (Stages 4.5 + 6) *(planned: M6)*

> The `api_fuzzer_worker/worker.py` and `js_analysis_worker/worker.py` currently exist as skeletons. Stage 4.5 and enhanced Stage 6 will be implemented in M6.

### Stage 4.5 — API Fuzzing (designed)
- Schema discovery from `/openapi.json`, `/swagger.json`, `/graphql`
- Schemathesis property-based + RESTler stateful fuzzing
- Custom ffuf-based mutation for endpoints without schemas
- Anomaly detection: 500s where 400s expected, cross-user data, authorization degradation

### Stage 6 Enhanced — JS Analysis (designed)
- Semgrep with custom security ruleset
- AST analysis: DOM XSS sinks, prototype pollution, unsafe postMessage
- Current M3 implementation only runs regex patterns (already in `js_secrets.py`)

---

## 7. Phase 6 — Behavioral Scenarios (Stage 7) *(planned: M9)*

> The `scenario_runner/worker.py` currently exists as a skeleton. Stage 7 will be implemented in M9.

Designed behavior includes race condition testing (nuclei `-race` + h2spacex), privilege escalation scenarios, and workflow bypass testing.

---

## 8. Phase 7 — Exploit Verification (Stage 8) *(planned: M7)*

> The `exploit_verifier/worker.py` currently exists as a skeleton. Stage 8 will be implemented in M7.

Designed behavior includes verification strategies for XSS (CDP session), SSRF (Interactsh OOB), IDOR (cross-session), CORS, SQLi (time-based blind), and secrets (live key auth), plus evidence bundle assembly in MinIO.

---

## 9. Phase 8 — AI Hypothesis (Stage 9) *(planned: M10)*

> The `ai_analysis_worker/worker.py` currently exists as a skeleton. Stage 9 will be implemented in M10.

Designed behavior: Ollama (llama3.1:8b), structured hypothesis generation with schema constraint, three-layer reliability, confidence threshold filtering, and routing hypotheses through the Exploit Verifier.

---

## 10. Phase 9 — Aggregation (Stage 10)

**File:** `pipeline/aggregator.py` → `run(ctx, scan_result, repo, publisher)`

**Purpose:** Deduplicate findings, persist to database, group vulnerabilities, finalize scan status, and publish to `report.jobs`.

> Stage 10 is the only FATAL stage besides Stage 0. If aggregation fails, the scan is marked `failed_internal`.

### Step-by-step:

**10.1 — Finding deduplication:**
- `dedup.py` → `compute_dedup_hash(candidate)`:
  ```
  SHA256( vulnerability_type | normalize_url(affected_url) | affected_parameter | payload[:100] )
  ```
- URL normalization: sorts query parameters so `?b=2&a=1` and `?a=1&b=2` produce the same hash
- Duplicates produced by overlapping stages (e.g., nuclei and web_vuln_tests both find the same XSS) are collapsed
- Stats logged: before count, after count, duplicates removed

**10.2 — Finding persistence:**
- `ScanRepository.save_findings(scan_id, program_id, candidates)`:
  - For each `FindingCandidate`:
    - Compute `deduplication_hash`
    - INSERT into `findings` with ON CONFLICT (deduplication_hash, scan_id) — do nothing
    - Set `is_verified=False`, `is_false_positive=False`
    - Assign `finding_id` UUID
  - Returns count of new findings saved (excluding duplicates)

**10.3 — Severity breakdown:**
```python
breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
for candidate in deduped:
    breakdown[candidate.severity.lower()] += 1
```

**10.4 — Scan status determination:**
- If `scan_result.stage_errors` has any entries → `status = "partial"`
- Otherwise → `status = "completed"`
- If partial: `partial_detail = {"failed_stages": [...], "errors": {...}}`

**10.5 — Scan finalization:**
- `ScanRepository.mark_scan_complete()`:
  - Updates `scans` row: `status`, `finding_count`, `severity_breakdown`, `partial_detail`, `error_detail`
  - Sets `completed_at = NOW()`

**10.6 — Report queue publish:**
- Constructs `ReportJobsPayload`:
  ```python
  ReportJobsPayload(
      scan_id=ctx.scan_id,
      program_id=ctx.program_id,
      status=status,
      partial_stages=list(scan_result.stage_errors.keys()),
      has_findings=saved_count > 0,
      finding_count=saved_count,
      verified_count=0,  # verification not yet implemented (M7)
      severity_breakdown=SeverityBreakdown(...),
  )
  ```
- Wraps in `MessageEnvelope` via `build_report_job_message(payload)`
- Publishes to `report.jobs` via `QueuePublisher.publish()`
- Records a `scan_stages` row for stage 10.1 (`report_handoff`)
- On publish failure: logs error, records failed stage, but scan is still marked complete

---

## 11. Phase 10 — Report Generation (Reporter)

**Service:** `reporter` (:8003) + `reporter-worker` (Celery)
**Queue consumed:** `report.jobs`
**Current state:** Reporter worker validates and logs messages but generation is NOT implemented.

### Current Implementation

**File:** `reporter/worker.py`

The reporter worker uses a raw Kombu consumer (not a Celery task) to consume `report.jobs`:

1. `ReportJobsConsumerStep` (Celery bootstep) creates a `Consumer` on the `report.jobs` queue
2. On message receipt → `_on_report_jobs_message(body, message)`:
   - The raw body is coerced to a dict (handles bytes, str, or dict)
   - Parsed into `MessageEnvelope`
   - Validated: `event_type == "scan.completed"`, `schema_version == "1.x"`
   - Payload extracted as `ReportJobsPayload`
   - All details logged: scan_id, program_id, finding_count, severity_breakdown, formats_requested
   - **Then:** `log.warning("report_generation_not_yet_implemented")` — this is where M4 will add actual generation
   - Message is always acknowledged (prevents redelivery loops)
3. A compatibility task (`reporter_worker_task`) exists for messages sent as Celery tasks rather than raw messages

**File:** `reporter/main.py`

The reporter FastAPI app provides:
- Health endpoint at `GET /api/v1/health` (checks DB, RabbitMQ, MinIO)
- Prometheus instrumentation
- No report APIs yet (download, regenerate, etc. — these come in M4)

### M4 Planned Implementation
- Fetch scan + findings + program from Core Engine + Scraper APIs
- Build `ParsedScan` dataclass with zero-finding guard
- Generate PDF (reportlab/weasyprint) and DOCX (python-docx)
- Upload to MinIO `reports/{report_id}/`
- Curl command + raw HTTP + browser steps per finding
- Watchdog for stale report recovery
- `GET /api/v1/reports/{report_id}/download` → pre-signed MinIO URL

---

## 12. Phase 11 — Manual Submission

This is intentionally outside the automated pipeline.

1. **Download:** `GET /api/v1/reports/{report_id}/download` returns a temporary pre-signed MinIO URL (M4).
2. **Review:** User reviews the report — checks scope, duplicate status, CVSS accuracy.
3. **Submission:** User submits directly on the bug bounty platform. AttackBot never auto-submits.

---

## 13. Failure Flows

### Scan fails at Stage 0 (scope fatal)
- **Code path:** `_async_scan_pipeline()` catches `ScanError` or empty scope from `_fetch_scope_from_scraper()`
- `scans.status = failed_scope`
- No assets, endpoints, or findings are created
- `report.jobs` message is NOT published
- The Redis lock is released

### Worker crashes mid-scan
- `task_acks_late=True` means RabbitMQ redelivers the message
- `task_reject_on_worker_lost=True` sends to DLQ on worker death
- On redelivery: `ScanRepository.create_or_resume_scan()` resumes the existing scan row (prevents duplicate scan records)
- If `retry_count >= 2`: watchdog marks permanently `failed_internal`

### Publish failure (scan.jobs → Core Engine)
- **Scraper path:** `queued_for_scan=True` set on the program. Reconciler retries every 5 minutes.
- **Core Engine path:** `_enqueue_scan()` raises `HTTPException(503)`.

### Browser session bootstrap fails *(planned: M5)*
- Scan continues with `sessions=None`
- Authenticated-only stages are skipped
- `scan.partial_detail` records the session failure reason

### Report generation fails *(planned: M4)*
- Reporter watchdog marks the report `failed` after 30 minutes
- Report can be regenerated via API without re-running the scan

### Individual pipeline stage fails (non-fatal)
- **Code path:** `_execute_pipeline()` catches exceptions per-stage
- Error message stored in `scan_result.stage_errors[stage_name]`
- `ScanRepository.record_stage()` records the failure with `status="failed"` and `error_detail`
- Pipeline continues to next stage
- Final scan status becomes `"partial"` instead of `"completed"`

---

## 14. Data Lifecycle Summary

```
Platform API
  → [Scraper: collectors/hackerone.py] → programs, program_scopes, program_policies (Postgres)
  → [Scraper: publisher.py] → scan.jobs (RabbitMQ)
  → [Core Worker: worker.py → scan_task.py] → scan record created (Postgres)
  → [Stage 0: scope_filter.py] → ScopeFilter built in-memory (fatal guard)
  → [Stage 1: asset_discovery.py] → assets (Postgres)
  → [Stage 2: fingerprinting.py] → assets.technology_stack + waf_detected updated (Postgres)
  → [Stage 3: enumeration.py] → endpoints (Postgres), JS files (MinIO js-assets/ + js_assets Postgres)
  → [Stage 3.5: planned M5] → browser_sessions (Postgres, encrypted)
  → [Stages 4, 4.5, 5, 6, 7, 9] → finding_candidates (in-memory, is_verified=False)
  → [Stage 8: planned M7] → findings updated (is_verified=True/is_false_positive=True)
  → [Stage 10: aggregator.py] → findings (Postgres, deduplicated)
                               → vulnerability_groups (Postgres) [planned]
                               → Neo4j graph nodes + edges [planned M8]
                               → exploit_chains (Postgres) [planned M8]
  → [aggregator.py → report.jobs] → reporter-worker receives message
  → [reporter: planned M4] → reproduction_packs (Postgres)
                            → report file (MinIO reports/)
                            → reports (Postgres)
  → [User] → downloads report → manual review → platform submission
```

**What is implemented now (M3):**

```
Scraper → scan.jobs → Core Worker → Stage 0 → 1 → 2 → 3 → (4 ∥ 5) → 6 → 10 → report.jobs → Reporter (logs only)
```

**Storage by system:**
| Data | Where | Implemented? |
|------|-------|--------------|
| Program metadata | Postgres | ✅ M2 |
| Scan + findings | Postgres | ✅ M3 |
| Assets + endpoints | Postgres | ✅ M3 |
| JS files (deduplicated) | MinIO | ✅ M3 |
| Browser sessions (encrypted) | Postgres | 🔲 M5 |
| Report files (PDF, DOCX) | MinIO | 🔲 M4 |
| Screenshots + evidence | MinIO | 🔲 M7 |
| Attack graph | Neo4j | 🔲 M8 |
| Distributed locks | Redis | ✅ M2 |
| Task results | Redis | ✅ M3 |
| Secrets + credentials | Vault | ✅ M1 (placeholder) |

---

## 15. Decision Points and Guards

| Point | Condition | Action | Code Location |
|-------|-----------|--------|---------------|
| Scan start | `scan:lock:{program_id}` held | Skip — existing scan in progress | `scan_task.py` → `_async_scan_pipeline()` |
| Stage 0 | `in_scope` list is empty | FATAL — `status=failed_scope`, stop | `scope_filter.py` → `ScopeFilter.__init__()` |
| Stage 0 | Scope API returns error | FATAL — `status=failed_scope`, stop | `scan_task.py` → `_fetch_scope_from_scraper()` |
| Stage 1 | Asset fails `ScopeFilter` | Drop asset silently, continue | `asset_discovery.py` → `scope_filter.filter_targets()` |
| Stage 3 | JS download fails | Log warning, continue | `enumeration.py` → `_download_and_store_js()` |
| Stage 4 | nuclei exits with code 1 | Not an error — zero findings | `nuclei_scan.py` → `run()` |
| Stage 4 | nuclei exits with code 2 | Log with classified reason, raise | `nuclei_scan.py` → `_classify_exit_code_2_reason()` |
| Stage 5 | SQLi/SSRF feature flags off | Skip those tests | `web_vuln_tests.py` → `_test_endpoint()` |
| Stage 5 | CRLF feature flag off | Skip CRLF test | `web_vuln_tests.py` → `_test_endpoint()` |
| Stage 6 | JS file download from MinIO fails | Log warning, skip file | `js_secrets.py` → `run()` |
| Stage 10 | Aggregation fails | FATAL — `status=failed_internal` | `scan_task.py` → `_execute_pipeline()` |
| Stage 10 | report.jobs publish fails | Log error, record failed stage, scan still marked complete | `aggregator.py` → `run()` |
| Any non-fatal stage | Stage raises exception | Log to `stage_errors`, continue | `scan_task.py` → `_execute_pipeline()` |
| Watchdog | Scan running > 2h | Mark `failed_internal`, republish if retries < 2 | `watchdog.py` + `main.py` |
| Report queue | Message validation fails | Log error, ack message, do not crash | `reporter/worker.py` → `_handle_report_job_message()` |

---

## 16. Code-to-Flow Reference Map

This table maps every major code file to its role in the system flow.

### Shared Library (`backend/shared/`)

| File | What It Does |
|------|-------------|
| `config.py` | `BaseServiceConfig` — all services inherit environment variable loading |
| `logging.py` | structlog JSON logger — `configure_logging()` + `get_logger()` |
| `db.py` | SQLAlchemy async engine — `init_db()`, `get_session()`, `check_db_health()` |
| `health.py` | `HealthResponse` + `HealthStatus` enum for `/api/v1/health` endpoints |
| `exceptions.py` | Exception hierarchy: `AttackBotError` → `ScanError`, `ScopeFatalError`, `QueueError`, etc. |
| `queue.py` | `QueuePublisher` (passive declare + publish), `Queues` constants, DLQ arguments |
| `vault.py` | HashiCorp Vault client — `init_vault()`, `get_secret()`, `put_secret()` |
| `storage.py` | MinIO client — `init_storage()`, `upload_bytes()`, `download_bytes()`, `get_presigned_url()` |
| `schemas/envelope.py` | `MessageEnvelope` Pydantic model + `build_envelope()` factory |
| `schemas/scan_jobs.py` | `ScanJobsPayload`, `FeatureFlags`, `ScopeDefinition`, `ScopeEntry` + builder |
| `schemas/report_jobs.py` | `ReportJobsPayload`, `SeverityBreakdown` + builder |

### Scraper Service (`backend/services/scraper/`)

| File | What It Does |
|------|-------------|
| `main.py` | FastAPI app: scrape trigger, program APIs, scheduler setup, Redis locking |
| `collectors/base.py` | `BaseCollector` ABC, `CollectorRegistry` |
| `collectors/hackerone.py` | HackerOne API v1 client — pagination, 429 retry, structured scopes |
| `scope_parser.py` | `ScopeParser` — converts raw scope entries to typed `ProgramScope` objects |
| `repository.py` | `ProgramRepository` — upsert programs/scopes/policies with flag preservation |
| `publisher.py` | `ScraperPublisher` — wraps `QueuePublisher` with `queued_for_scan` flag management |
| `reconciler.py` | APScheduler job — republishes programs stuck with `queued_for_scan=True` |
| `config.py` | `ScraperConfig` — platform credentials, scrape intervals |
| `models.py` | Pydantic program models |

### Core Engine (`backend/services/core_engine/`)

| File | What It Does |
|------|-------------|
| `worker.py` | Celery app + `scan_task()` — entry point from `scan.jobs` queue |
| `scan_task.py` | `run_scan_task()` → `_async_scan_pipeline()` → `_execute_pipeline()` |
| `main.py` | FastAPI app: scan start/list/detail/findings APIs, watchdog, health |
| `repository.py` | `ScanRepository` — all DB operations (scans, assets, endpoints, JS assets, findings, stages) |
| `models.py` | `DiscoveredAsset`, `DiscoveredEndpoint`, `DiscoveredJsAsset`, `FindingCandidate`, `ScanResult` |
| `dedup.py` | `compute_dedup_hash()` — SHA-256 finding deduplication |
| `cvss.py` | `severity_to_cvss()` + `nuclei_severity()` — severity scoring |
| `subprocess_utils.py` | `run_tool_communicate()` + `parse_jsonl()` — external tool execution |
| `watchdog.py` | `check_stuck_scans()` — stuck scan detection and republish |
| `startup_checks.py` | `collect_toolchain_checks()` — validates nuclei binary at worker startup |
| `config.py` | `EngineConfig` — nuclei/httpx/ffuf rates, timeouts, template paths |

### Pipeline Stages (`backend/services/core_engine/pipeline/`)

| File | Stage | What It Does |
|------|-------|-------------|
| `context.py` | — | `ScanContext`, `ScopeDefinition`, `FeatureFlags` dataclasses |
| `scope_filter.py` | 0 | `ScopeFilter` class — domain/wildcard/CIDR/IP matching |
| `asset_discovery.py` | 1 | subfinder → alterx → dnsx → httpx discovery chain |
| `fingerprinting.py` | 2 | httpx tech-detect + WAF detection enrichment |
| `enumeration.py` | 3 | ffuf + waybackurls + JS download to MinIO |
| `nuclei_scan.py` | 4 | nuclei template scanning with exit-code handling |
| `web_vuln_tests.py` | 5 | XSS, CORS, CRLF scanning + passive path detection |
| `js_secrets.py` | 6 | Regex-based secret detection (12 patterns) |
| `aggregator.py` | 10 | Dedup, persist, severity breakdown, report.jobs publish |
| `waf_utils.py` | — | WAF technology detection helper |

### Reporter Service (`backend/services/reporter/`)

| File | What It Does |
|------|-------------|
| `main.py` | FastAPI skeleton — health endpoint only |
| `worker.py` | Raw Kombu consumer — validates report.jobs messages, logs, generation not yet implemented |