# AttackBot — Business Flow Document
> Version: 1.0 | Last updated: 2026-03-10
> Purpose: End-to-end description of how every piece of data, every trigger, and every decision flows through the system — from the moment a bug bounty program is discovered to the moment a report is ready for manual submission.

---

## Table of Contents
1. [System Entry Points](#1-system-entry-points)
2. [Phase 1 — Program Ingestion (Scraper)](#2-phase-1--program-ingestion-scraper)
3. [Phase 2 — Scan Orchestration (Core Engine)](#3-phase-2--scan-orchestration-core-engine)
4. [Phase 3 — Pipeline Stages 0–6 (Unauthenticated)](#4-phase-3--pipeline-stages-06-unauthenticated)
5. [Phase 4 — Browser Session Bootstrap (Stage 3.5)](#5-phase-4--browser-session-bootstrap-stage-35)
6. [Phase 5 — API Fuzzing + JS Analysis (Stages 4.5 + 6)](#6-phase-5--api-fuzzing--js-analysis-stages-45--6)
7. [Phase 6 — Behavioral Scenarios (Stage 7)](#7-phase-6--behavioral-scenarios-stage-7)
8. [Phase 7 — Exploit Verification (Stage 8)](#8-phase-7--exploit-verification-stage-8)
9. [Phase 8 — AI Hypothesis (Stage 9)](#9-phase-8--ai-hypothesis-stage-9)
10. [Phase 9 — Aggregation + Graph (Stage 10)](#10-phase-9--aggregation--graph-stage-10)
11. [Phase 10 — Report Generation (Reporter)](#11-phase-10--report-generation-reporter)
12. [Phase 11 — Manual Submission](#12-phase-11--manual-submission)
13. [Failure Flows](#13-failure-flows)
14. [Data Lifecycle Summary](#14-data-lifecycle-summary)
15. [Decision Points and Guards](#15-decision-points-and-guards)

---

## 1. System Entry Points

There are two ways a scan begins. Both converge on the same queue.

### Entry Point A — Scheduled Scrape (Automatic)
1. APScheduler in the Scraper fires a per-platform job on a configured interval (e.g., every 6 hours for HackerOne).
2. The Scraper fetches the program list from the platform API.
3. Each program is normalized and upserted into the `programs` table.
4. If the program is new or has scope changes, a `scan.jobs` message is published.
5. The Core Worker picks up the message and begins the scan.

### Entry Point B — Manual Trigger (On-Demand)
1. A `POST /api/v1/scrape/trigger` request is sent to the Scraper service (via the API Gateway at `:8000`).
2. The Scraper runs the collection pipeline immediately, outside the scheduler.
3. Everything from step 3 onward is identical to Entry Point A.

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

### Step-by-step

**2.1 — Platform authentication**
The Scraper loads platform credentials from Vault (`secret/platforms/hackerone/api_token`). For HackerOne: HTTP Basic Auth using API username + token. Credentials are never stored in config files.

**2.2 — Paginated program listing**
The HackerOne collector calls `GET /v1/hackers/programs` with pagination (`page[number]`, `page[size]=100`). It iterates until the API returns an empty `data` array. Each page is processed immediately — the full list is never held in memory at once.

**2.3 — 429 handling**
On every API request: if `HTTP 429` is returned, the collector reads the `Retry-After` header and sleeps for that duration, then retries. After `max_retries=3` consecutive 429s, `CollectorRateLimitError` is raised and the scrape job is marked failed for that platform. The scheduler will retry on the next cycle.

**2.4 — Per-program detail fetch**
For each program in the listing, the collector calls `GET /v1/hackers/programs/{handle}` for full details and `GET /v1/hackers/programs/{handle}/structured_scopes` for parsed scope entries. Raw markdown scope parsing is never used — structured scopes are always preferred.

**2.5 — Normalization**
The raw platform response is passed through the platform-specific normalizer, which maps it to the canonical `Program` dataclass:
- `platform` (hackerone, bugcrowd, etc.)
- `handle` (unique identifier on the platform)
- `bounty_type` (bug_bounty or vdp)
- `max_bounty`
- `is_active`
- Nested: `in_scope` and `out_of_scope` scope entries with typed `asset_type` (url, domain, wildcard_domain, ip_range, mobile_app, api)

**2.6 — Scope parsing**
The `ScopeParser` converts raw scope entries into typed `ProgramScope` objects. It handles:
- `*.example.com` → wildcard domain, stored as `wildcard_domain` asset type
- `192.168.1.0/24` → CIDR range, stored as `ip_range`
- `https://example.com/api/` → URL with path prefix
- `com.example.app` → mobile app bundle identifier

Each scope entry is stored in `program_scopes` with a `scope_type` (in_scope or out_of_scope).

**2.7 — Upsert**
`ProgramRepository.upsert()` performs an INSERT ON CONFLICT DO UPDATE. Critical rule: if the program already exists with `queued_for_scan=True`, that flag is NOT overwritten during re-scrape. This prevents the reconciler from losing track of programs that failed to publish.

**2.8 — Queue publish**
`QueuePublisher.publish()` sends a `scan.jobs` message containing:
- `program_id`, `platform`, `handle`
- Full `scope` (in_scope list, out_of_scope list)
- `feature_flags` (which scanners to enable — loaded from environment defaults)
- `priority` (1–10)
- `scan_timeout_seconds`

On publish success: `queued_for_scan` is cleared.
On publish failure: `queued_for_scan` is set to `True` and the reconciler handles retry.

**2.9 — Reconciler**
An APScheduler job runs every 5 minutes. It queries `programs WHERE queued_for_scan = True AND last_scraped_at > NOW() - INTERVAL '7 days'`. For each: it republishes to `scan.jobs`. On success, clears the flag. On failure, leaves the flag for the next cycle. Programs older than 7 days are not auto-retried — they require a new scrape.

**2.10 — Redis lock**
A per-platform Redis lock (`scraper:lock:{platform}`) prevents two scrape jobs for the same platform from running simultaneously. Lock TTL is set to 2x the expected scrape duration. If the lock cannot be acquired, the job is skipped for that cycle.

---

## 3. Phase 2 — Scan Orchestration (Core Engine)

**Service:** `core-engine` (:8002) + `core-worker` (Celery)
**Queue consumed:** `scan.jobs`
**Queue produced:** `report.jobs`, plus sub-queues per stage

### Step-by-step

**3.1 — Message receipt**
The `core-worker` Celery process receives a message from `scan.jobs`. `task_acks_late=True` means the message is NOT acknowledged until the task function returns or explicitly acks. A worker crash will cause RabbitMQ to redeliver the message.

**3.2 — Redis scan lock**
Before doing any work, the worker acquires `scan:lock:{program_id}`. If the lock is already held (a previous scan of this program is still running), the task returns immediately without creating a scan record. The message is acknowledged (not requeued) — the assumption is the existing scan will produce results.

**3.3 — Scan record creation**
A row is inserted into `scans` with `status=pending`. If a scan for this program already exists with `status=failed_internal` and `retry_count < 2`, that record is reused with `retry_count` incremented. Otherwise a new record is created.

**3.4 — Scope loading**
The engine calls `GET /api/v1/programs/{program_id}/scope` on the Scraper service. This returns the canonical scope from `program_scopes`. The `ScopeFilter` object is built from this data. If the scope API returns an empty in-scope list, a `ScopeFatalError` is raised immediately — the scan transitions to `failed_scope` and the task exits.

**3.5 — Feature flag resolution**
Feature flags from the `scan.jobs` message override environment defaults. This allows per-program scanner profiles (e.g., enable SSRF scanning only for programs that explicitly allow it in their testing policy).

**3.6 — Pipeline execution**
`run_pipeline(scan_context)` is called. It executes stages in order, with the parallelism groups described in Section 4. Each stage writes its results into `scan_context` (an in-memory object) and to the database. Stage failures are classified as fatal (abort scan) or non-fatal (record in `partial_detail`, continue).

**3.7 — Watchdog**
An APScheduler job in `core-engine` runs every 15 minutes. It queries `scans WHERE status='running' AND started_at < NOW() - INTERVAL '2 hours'`. For each stuck scan:
- Status is updated to `failed_internal`, `error_detail='watchdog_timeout'`
- If `retry_count < 2`, the scan is republished to `scan.jobs`
- The Redis lock is released

This ensures no scan can block a program's queue slot indefinitely.

---

## 4. Phase 3 — Pipeline Stages 0–6 (Unauthenticated)

All stages run inside the `core-worker` process. Sub-stages that require heavy computation are offloaded to specialist workers via queues, but stages 0–3 run locally.

### Stage 0 — Scope Filter (FATAL)
- `ScopeFilter` is built from `program_scopes` entries.
- Every URL, domain, and IP is tested against the filter before any tool is invoked.
- If the scope cannot be resolved (empty in-scope, parse error), `ScopeFatalError` is raised and the scan is terminated immediately with `status=failed_scope`.
- No scan work is ever performed on an undefined scope.

### Stage 1 — Asset Discovery
- `subfinder` runs passive subdomain enumeration for each in-scope domain. Uses streaming readline (large output).
- `alterx` generates permuted subdomain variants from the subfinder output.
- `dnsx` resolves the permuted list and filters to live hosts. **This step is mandatory** — skipping it sends thousands of non-existent hosts to httpx.
- `httpx` probes all resolved hosts for live HTTP services, collecting status codes, titles, and technology hints.
- Every discovered asset is tested against `ScopeFilter` before being written to `assets`.
- Out-of-scope assets are dropped. In-scope assets are persisted with `is_in_scope=True`.

### Stage 2 — Fingerprinting
- `httpx` (projectdiscovery) probes each asset for technology stack, WAF presence, and response header anomalies.
- Results written to `assets.technology_stack` (JSONB) and `assets.waf_detected`.
- WAF presence is noted but does not block any subsequent stages — all scanners still run.

### Stage 3 — Enumeration
- `ffuf` performs directory and path discovery against each in-scope asset.
- `waybackurls` pulls historical URL data from the Wayback Machine and Common Crawl.
- Discovered endpoints are merged, deduplicated, and written to `endpoints`.
- JavaScript files found during enumeration are downloaded and uploaded to MinIO (`js-assets/` bucket). Their content hash is stored in `js_assets`. If the same JS content was seen before (matching `content_hash`), the MinIO upload is skipped and the existing record is reused.

**Parallelism starts here:** After Stage 3 completes:
- Stage 3.5 (Browser Session) is triggered if `ENABLE_BROWSER_SESSION=True`
- While waiting for Stage 3.5, Stages 4 + 4.5 begin in parallel Group A

### Stage 4 — Nuclei Scanning
- Target list built from all in-scope assets + endpoints. Each target is validated through `ScopeFilter` again.
- `nuclei` runs with the full community template set against the target list. `-silent` flag prevents status lines from mixing with JSON output.
- Output is parsed: only lines starting with `{` are treated as JSON findings. `returncode==1` is not an error — it means zero findings.
- Each nuclei result is converted to a candidate `Finding` with CVSS scoring. `is_verified=False`.
- `deduplication_hash` is computed and checked before persistence. Duplicates are dropped.

### Stage 5 — Web Vulnerability Tests
Runs in parallel with Stage 4 (Group A).
- **XSS scanner:** Injects reflection payloads into discovered parameters. Checks for unescaped output in response body.
- **CORS scanner:** Sends crafted `Origin` headers. Flags misconfigured CORS if `Access-Control-Allow-Origin` reflects the attacker origin with `Access-Control-Allow-Credentials: true`.
- **CRLF scanner:** Disabled by default (feature flag). Injects CRLF sequences into headers.
- **SQLi scanner:** Disabled by default. Error-based detection only at this stage (time-based runs in Stage 8 verification).
- **SSRF scanner:** Disabled by default. OOB detection via Interactsh at Stage 8.
All candidates written as `is_verified=False` findings.

### Stage 6 — JS Secret Scanning
Runs after Stage 3 (needs JS files) and in parallel with Stage 5 (Group B).
- Reads each JS asset from MinIO by `js_asset_id`.
- Applies regex patterns for: AWS access keys, GCP service account keys, Stripe API keys, Twilio tokens, JWT secrets, PEM private keys, bearer tokens, generic high-entropy strings.
- Each match produces a candidate `Finding` with `vulnerability_type=secret_exposure`.
- Full JS analysis (Semgrep + AST) is offloaded to the `js-analysis-worker` in M6. In M3, only regex runs here.

---

## 5. Phase 4 — Browser Session Bootstrap (Stage 3.5)

**Worker:** `browser-worker` (Celery)
**Queue:** `browser.jobs`
**Triggered:** After Stage 3 completes, if `ENABLE_BROWSER_SESSION=True`

### Step-by-step

**5.1 — Job dispatch**
Core Engine publishes a `session.request` message to `browser.jobs` containing the `program_id`, the login scenario to use, and whether IDOR verification is enabled (which requires two sessions).

**5.2 — Browser context creation**
The `browser-worker` launches a fresh Playwright Chromium browser context per job. `service_workers='block'` is set on every context — without this, Service Workers intercept requests before Playwright's route handler sees them.

**5.3 — Scope enforcement**
`browser_context.route("**/*", enforce_scope)` is registered before any navigation. The route handler checks every request URL against the program's in-scope domain list. Out-of-scope requests are hard-blocked (`.abort()`). Internal scheme requests (`data:`, `blob:`, `chrome-extension:`) are always allowed.

**5.4 — Scenario execution**
The YAML login scenario is loaded and executed step by step:
- `visit` → `page.goto(url)`
- `fill` → `page.fill(selector, value)`
- `submit` → `page.click(submit_selector)`
- `wait` → `asyncio.sleep(seconds)`
- `handle_totp` → reads `$TOTP_SECRET` variable from Vault, generates current TOTP code with pyotp, fills the MFA field
- `capture_cookies` → `context.storage_state()` is called

**5.5 — TOTP secret resolution**
If a scenario step references `$TOTP_SECRET`, the browser worker calls Vault: `secret/programs/{program_id}/totp_secret`. The secret is never stored in the YAML file. If the Vault key doesn't exist, the step raises `CollectorAuthError` and the session bootstrap fails.

**5.6 — Session bundle encryption**
After a successful login, `context.storage_state()` returns a dict with `cookies` and `origins` (localStorage). This is encrypted with AES-256 and written to `browser_sessions`:
- `cookies` (encrypted JSON)
- `local_storage` (encrypted JSON)
- `session_headers` (encrypted JSON, captured Auth headers if any)
- `csrf_token` (encrypted)
- `is_valid=True`
- `expires_at` = now + 24h

**5.7 — Two-session bootstrap for IDOR**
If `feature_flags.idor_verification=True`, the bootstrap is run twice: once with `account_slot="primary"` and once with `account_slot="secondary"`. The credentials for each slot are stored in Vault under `secret/programs/{program_id}/account_primary` and `secret/programs/{program_id}/account_secondary`. The result is two separate `browser_sessions` rows. Both `session_id`s are attached to the `scan_context`.

**5.8 — Session return to engine**
The browser worker publishes the `session_id` back to the Core Engine via Redis result backend. The engine awaits with a timeout (120s). If the session bootstrap times out, scan proceeds with `sessions=None` and a warning is logged. Authenticated scanning is skipped but unauthenticated scanning continues.

**5.9 — Session reuse in downstream stages**
Once attached to `scan_context`:
- Nuclei appends `-H "Cookie: {cookie_string}"` to all requests for that target
- XSS and CORS scanners attach the session cookies to every request
- The Exploit Verifier loads the session via `storage_state` to verify IDOR candidates

---

## 6. Phase 5 — API Fuzzing + JS Analysis (Stages 4.5 + 6)

### Stage 4.5 — API Fuzzing
**Worker:** `api-fuzzer-worker` (Celery)
**Queue:** `api.fuzz.jobs`
**Triggered:** After Stage 4 completes, runs in parallel with Stage 5

**6.1 — Schema discovery**
During Stage 3 enumeration, the engine attempts to fetch API schemas from well-known paths: `/openapi.json`, `/swagger.json`, `/api-docs`, `/graphql` (introspection query). Raw schemas are stored in `api_schemas`.

**6.2 — Fuzzing strategy**
For endpoints with schemas: Schemathesis runs property-based testing, generating inputs that satisfy and violate the schema contract simultaneously. RESTler runs stateful fuzzing — it chains API calls to reach states that single-request testing cannot reach.

For endpoints without schemas: A custom ffuf-based mutator runs path and parameter fuzzing using mutation tables:
- Integer fields → 0, -1, max_int, type confusion strings
- String fields → empty, null, SQLi patterns, SSTI payloads
- Required fields → omitted entirely
- Amount/price fields → negative, fractional, integer overflow
- UUID fields → own user's ID, another user's ID, null UUID

**6.3 — Anomaly detection**
Response analysis looks for:
- HTTP 500 where HTTP 400 was expected (server error on invalid input = logic flaw)
- Response body containing data belonging to a different user (state confusion)
- Authorization degradation (action succeeds without a required role)
- Inconsistent state after parallel requests (race condition signal)

Each anomaly produces a candidate `Finding` with `vulnerability_type=business_logic`.

### Stage 6 — Enhanced JS Analysis (M6+)
**Worker:** `js-analysis-worker` (Celery)
**Queue:** `js.analysis.jobs`

**6.4 — Static analysis pipeline**
- Downloads each JS file from MinIO.
- Runs Semgrep with a custom security ruleset targeting web app patterns.
- Builds AST using esprima or tree-sitter.
- AST traversal checks for:
  - DOM XSS sinks: `innerHTML=`, `document.write()`, `eval()`, `setTimeout(string_var)`
  - Prototype pollution: `__proto__` assignment, `constructor[prototype]`
  - Unsafe `postMessage`: origin check missing in message event handlers
- Regex secret scanning runs here (moved from Stage 6 baseline in M3).

---

## 7. Phase 6 — Behavioral Scenarios (Stage 7)

**Worker:** `scenario-runner` (Celery)
**Queue:** `scenario.jobs`
**Triggered:** After Stages 5 + 6 complete (Group B), runs as Group C
**Feature flag:** `ENABLE_SCENARIO_RUNNER` (off by default)

**7.1 — Scenario selection**
The Core Engine selects scenarios from the built-in library based on the target's technology stack fingerprint. A payment endpoint → `race_transfer.yaml`. An admin panel → `priv_escalation_role.yaml`. A multi-step checkout → `workflow_skip_payment.yaml`.

**7.2 — Race condition testing**
Primary path (identical request bodies): nuclei race templates with `-race -race_count 20`. The nuclei engine implements the gate mechanism internally — all request bodies are held until the last byte can be sent simultaneously.

Secondary path (different request bodies): `h2spacex` is used. It:
1. Opens an H2 TLS connection to the target
2. Sends all request headers and bodies for all slots EXCEPT the final DATA frame
3. Releases all final DATA frames simultaneously in a single TCP write

**Connection warming** runs before every burst:
- 3 warmup requests are sent to the exact target endpoint
- 100ms sleep after warmup
- This stabilizes TCP slow-start before the burst window

**7.3 — Three-signal outcome detection**
After the burst:
- **Signal 1 — State divergence:** GET the resource before and after the burst. If the state changed in a way inconsistent with a single operation (e.g., balance decreased by more than one debit), the race fired.
- **Signal 2 — Response divergence:** If the burst of N identical requests returns N-1 identical responses and 1 different one, the minority response indicates a race.
- **Signal 3 — Timing outlier:** If one response in the burst took > 3 standard deviations longer than the others, this indicates lock contention — a signal that the server noticed and handled (or failed to handle) a concurrent access.

Any signal firing produces a candidate `Finding` with `vulnerability_type=race_condition`.

**7.4 — Privilege escalation scenarios**
The scenario runner loads the secondary browser session via `storage_state`. It navigates to endpoints that require an elevated role (e.g., admin-only). If access is granted to the secondary (unprivileged) account, a `privilege_escalation` candidate is produced.

**7.5 — Workflow bypass scenarios**
Multi-step flows (register → verify email → pay → get product) are navigated by skipping intermediate steps and going directly to the final step. If the final step succeeds without the prior steps, a `workflow_bypass` candidate is produced.

---

## 8. Phase 7 — Exploit Verification (Stage 8)

**Worker:** `exploit-verifier` (Celery)
**Queue:** `verify.jobs`
**Triggered:** After all candidate-producing stages complete
**This is the most important quality gate. Nothing reaches the Reporter without passing here.**

All candidates from Stages 4, 4.5, 5, 6, 7, and 9 flow through this stage.

### XSS Verification
1. A unique `payload_marker` string is embedded in the payload (e.g., `alert('xss-{uuid}')`)
2. A headless Chromium browser (CDP session — Chromium only) navigates to the target URL with the payload
3. A `Runtime.consoleAPICalled` event listener watches for the marker in console output
4. If the marker fires within 10 seconds: `is_verified=True`, screenshot captured
5. If the marker does not fire: `is_false_positive=True`, `false_positive_reason='payload_did_not_execute'`

### SSRF Verification
1. Register an OOB URL with the self-hosted Interactsh server. Get back a `correlation_id` (exactly 33 lowercase alphanumeric characters)
2. Start the polling loop **before** injecting the payload
3. 500ms delay, then inject the OOB URL as the SSRF payload into the target parameter
4. Poll Interactsh every 3 seconds for 45 seconds, looking for `data` containing the `correlation_id`
5. If an interaction is received (DNS, HTTP, or LDAP): `is_verified=True`, `oob_interaction.json` stored in MinIO
6. If no interaction received: `is_false_positive=True`, `false_positive_reason='no_oob_callback'`

**Why DNS detection matters:** Many WAFs block outbound HTTP while allowing DNS. DNS-only callbacks confirm SSRF even when HTTP callbacks are blocked.

### IDOR Verification
1. Load the secondary browser session from `browser_sessions` via `storage_state`
2. Use that context to make a request to the resource owned by the primary user
3. Parse the response — check if it contains the primary user's data (by comparing against known primary-user identifiers captured during session bootstrap)
4. If cross-user data is returned: `is_verified=True`
5. If access is denied (401/403 or no cross-user data): `is_false_positive=True`

### CORS Verification
1. Send a request to the affected endpoint with `Origin: https://attacker.example.com`
2. Check `Access-Control-Allow-Origin` header — must reflect the attacker's exact origin (not `*`)
3. If credentialed requests are implicated: also check `Access-Control-Allow-Credentials: true`
4. Both conditions must be true for `is_verified=True`

### SQLi Verification
1. **Error-based:** Inject known error-triggering payloads, check response body for DB error strings (MySQL, PostgreSQL, MSSQL patterns)
2. **Time-based blind:** Inject known sleep payloads (`SLEEP(5)`, `pg_sleep(5)`, `WAITFOR DELAY`), measure response time. If delta > 4 seconds: `is_verified=True`

### Secret Verification
1. Take the discovered API key/token
2. Make an actual authentication request to the relevant API (AWS STS `GetCallerIdentity`, Stripe `/v1/balance`, etc.)
3. If authentication succeeds: `is_verified=True`, `false_positive_reason` stays null
4. If authentication fails (key inactive, revoked): `is_verified=False`, `is_false_positive=True`, `false_positive_reason='key_inactive'`

### Evidence Bundle Assembly
For every `is_verified=True` finding, the verifier stores in MinIO under `evidence/{finding_id}/`:
- `screenshot.png` — headless browser screenshot at the moment of exploitation
- `request_response.txt` — raw HTTP request + full response
- `payload.txt` — exact payload used
- `oob_interaction.json` — Interactsh callback receipt (SSRF/blind cases only)

Each file path is recorded in `finding_evidence`.

### False Positive Handling
- `is_false_positive=True` findings are retained in the database but excluded from reports
- `false_positive_reason` records why (e.g., `no_oob_callback`, `payload_did_not_execute`, `key_inactive`)
- A Prometheus counter tracks `attackbot_false_positive_rate = unverified_count / candidate_count` per scan
- A Grafana panel displays rolling FP rate — alerting fires if it exceeds 40%

---

## 9. Phase 8 — AI Hypothesis (Stage 9)

**Worker:** `ai-analysis-worker` (Celery)
**Queue:** `ai.analysis.jobs`
**Feature flag:** `ENABLE_AI_HYPOTHESIS` (off by default)
**Triggered:** After Stage 8 (needs verified findings as context)

**9.1 — Context bundle construction**
The AI worker builds a prompt from scan artifacts, respecting a `MAX_PROMPT_TOKENS=6000` budget. It includes:
- Endpoint list with methods, paths, and parameter names
- Response code anomalies (all 500s, unexpected 200s on privileged paths)
- Technology stack fingerprint
- Short JS snippets containing sinks or secrets
- Summary of already-verified findings

It excludes:
- Full response bodies
- Binary/image content
- Out-of-scope assets
- Full JS files
- Duplicate endpoint variants

**9.2 — Structured hypothesis generation**
The LLM (llama3.1:8b via Ollama) is prompted with a schema constraint. Output must match:
```json
{
  "hypotheses": [
    {
      "hypothesis": "string",
      "reasoning": "string",
      "affected_endpoint": "string",
      "suggested_method": "GET|POST|PUT|DELETE|PATCH",
      "suggested_payload": {},
      "confidence": 0.0–1.0,
      "vulnerability_class": "idor|xss|ssrf|sqli|auth_bypass|business_logic|..."
    }
  ]
}
```

**9.3 — Three-layer reliability**
1. Schema-constrained generation (`format=schema, temperature=0`)
2. Markdown fence stripping (leaked fences stripped with regex)
3. Pydantic validation (malformed output caught, retried up to 3 times)

On exhausted retries: returns empty list (fail open — no crash, scan continues).

**9.4 — Confidence threshold**
Only hypotheses with `confidence >= 0.6` proceed. Low-confidence generic suggestions (e.g., "check for XSS" with no specific endpoint) are filtered out here.

**9.5 — Hypothesis-to-verification pipeline**
Each hypothesis that passes the threshold is converted into a `verify.jobs` message — it goes through the same Exploit Verifier as all other candidates. If the verifier confirms it: `is_verified=True`, `source='ai_hypothesis'` recorded in `findings`. AI never writes directly to findings.

---

## 10. Phase 9 — Aggregation + Graph (Stage 10)

**Stage 10 is the only FATAL stage besides Stage 0.** If aggregation fails, the scan is marked `failed_internal`.

### Finding Deduplication
Before persistence, every candidate finding's `deduplication_hash` is computed:
```
SHA256( vulnerability_type | normalize_url(affected_url) | affected_parameter | payload[:100] )
```
URL normalization sorts query parameters so `?b=2&a=1` and `?a=1&b=2` produce the same hash. Duplicates produced by overlapping stages (e.g., nuclei and web_vuln_tests both find the same XSS) are collapsed to the first instance.

### Vulnerability Groups
Findings are grouped by `vulnerability_type` and domain. `vulnerability_groups` rows summarize the count and max severity per type. These are used by the Reporter for the Executive Summary table.

### Attack Graph Ingestion
All `is_verified=True` findings are ingested into Neo4j:
1. Each finding becomes a `Finding` node (`MERGE` on `finding_id`)
2. Each asset becomes an `Asset` node
3. Each endpoint becomes an `Endpoint` node
4. Edges are created: `Asset -[:EXPOSES]-> Endpoint -[:HAS_FINDING]-> Finding`
5. Session/credential nodes are created for browser sessions
6. Edge inference rules run:
   - `Finding {type: subdomain_takeover} -[:CONTROLS]-> Cookie {domain endsWith affected_domain}`
   - `Finding -[:CHAINS_TO]-> Finding` only when connected through a shared asset — never inferred between unrelated findings

### Exploit Chain Detection
Cypher queries detect multi-hop chains:
- **Chain 1:** Subdomain Takeover → Cookie Control → Auth Bypass → IDOR/Privilege Escalation
- **Chain 2:** JS Secret Leak → Credential → Endpoint → Auth Bypass

For each detected chain:
- Combined severity is computed: max severity of all findings in chain; if ≥3 medium findings: escalated to high
- An `exploit_chains` row is written to Postgres
- The `graph_path_ids` column stores Neo4j node IDs for traceability

### Scan Finalization
- `scans.status` is updated: `completed`, `partial` (if non-fatal stage failures), `failed_scope`, or `failed_internal`
- `finding_count` and `severity_breakdown` are written
- If `partial`: `partial_detail` JSON records which stages failed and why

### Publication to Report Queue
A `scan.completed` message is published to `report.jobs` containing:
- `scan_id`, `program_id`
- `status`, `has_findings`, `finding_count`, `verified_count`
- `severity_breakdown`
- `exploit_chains` list (chain UUIDs)
- `formats_requested` (pdf, docx, or both)

---

## 11. Phase 10 — Report Generation (Reporter)

**Service:** `reporter` (:8003) + `reporter-worker` (Celery)
**Queue consumed:** `report.jobs`
**Outputs:** PDF and/or DOCX file in MinIO; row in `reports`

### Step-by-step

**11.1 — Data fetch**
The reporter-worker fetches:
- Full scan detail from `GET /api/v1/scans/{scan_id}` (Core Engine)
- All `is_verified=True` findings from `GET /api/v1/scans/{scan_id}/findings?verified=true` (Core Engine)
- Program metadata and scope from `GET /api/v1/programs/{program_id}` (Scraper)
- Exploit chain details from `GET /api/v1/chains/{chain_id}` (Attack Graph Engine)

**11.2 — ParsedScan construction**
All fetched data is normalized into a `ParsedScan` dataclass. The constructor checks `len(findings) > 0` and sets `has_findings`. All downstream generators check `get_report_mode()` first — a zero-finding scan produces a "No Findings" report without crashes or empty tables.

**11.3 — Reproduction pack generation**
For every finding, a `reproduction_packs` row is created with:
- `curl_command`: a complete, copy-pasteable curl one-liner with all headers, cookies, and payload
- `http_request_raw`: the raw HTTP request block (method, path, headers, body)
- `browser_steps`: numbered human-readable steps ("1. Navigate to ...", "2. Enter payload in ... field", etc.)

**11.4 — PDF generation**
Using reportlab or weasyprint:
- **Page 1:** Cover (program name, scan date, severity summary donut chart)
- **Executive Summary:** Total findings, severity breakdown table, key risk narrative
- **Scope Overview:** In-scope assets tested, assets discovered, coverage notes
- **Findings Table:** All findings sorted by severity, one row each
- **Per-Finding Detail** (one page per finding): title, severity badge (color-coded), CVSS score and vector, affected URL, description, reproduction steps, curl command, evidence screenshot thumbnail
- **Exploit Chains** (if any): step-by-step chain narrative with escalated severity callout
- **Appendix:** Full reproduction packs (curl, raw HTTP, browser steps) for all findings

Severity color coding: Critical = red (#FF0000), High = orange (#FF6600), Medium = yellow (#FFCC00), Low = blue (#0066CC), Informational = grey.

**11.5 — DOCX generation**
Using python-docx, same section structure. Tables for findings. Styled heading levels. Code blocks for curl and HTTP raw. Inline images for screenshots.

**11.6 — MinIO upload**
Files are uploaded to `reports/{report_id}/report.pdf` and `reports/{report_id}/report.docx`. Storage paths are written to `reports.storage_path`. No public access is set on the bucket — all downloads go through the Reporter API's pre-signed URL endpoint.

**11.7 — Watchdog**
An APScheduler job queries `reports WHERE status='generating' AND created_at < NOW() - INTERVAL '30 minutes'`. Stale rows are marked `failed`, `error_detail='watchdog_timeout'`. The report can be regenerated via `POST /api/v1/reports/generate`.

**11.8 — Completion event**
A `report.generated` message is published to `reports.completed` with the `report_id` and download URL template.

---

## 12. Phase 11 — Manual Submission

This is intentionally outside the automated pipeline.

**12.1 — Download**
`GET /api/v1/reports/{report_id}/download` on the Reporter service (via API Gateway) returns a temporary pre-signed MinIO URL valid for 15 minutes. The report is downloaded by the user.

**12.2 — Review**
The user reviews the report. The automated pipeline produces evidence-backed findings, but submission decisions require human judgment:
- Is the finding in scope for the current program bounty?
- Has this vulnerability class been reported before (duplicate check)?
- Is the CVSS score consistent with the platform's bounty table?
- Does the reproduction pack work end-to-end in a manual test?

**12.3 — Submission**
The user submits the report directly on the bug bounty platform. AttackBot does not perform automated submission — this is a deliberate safeguard against submitting unreviewed findings or duplicates.

---

## 13. Failure Flows

### Scan fails at Stage 0 (scope fatal)
- `scans.status = failed_scope`
- No assets, endpoints, or findings are created
- `report.jobs` message is NOT published — no report is generated
- The program's `queued_for_scan` flag is left as-is
- Human intervention required: check if scope entries in `program_scopes` are parseable

### Worker crashes mid-scan
- `task_acks_late=True` means the message is redelivered by RabbitMQ
- If `retry_count < 2`: the scan is retried automatically
- If `retry_count >= 2`: the scan is permanently marked `failed_internal`
- The watchdog catches any scans not recovered by this mechanism after 2 hours

### Publish failure (scan.jobs → Core Engine)
- `queued_for_scan=True` is set on the program
- Reconciler retries publish every 5 minutes
- Programs older than 7 days are not auto-retried

### Browser session bootstrap fails
- If timeout or auth error: scan continues with `sessions=None`
- Authenticated-only stages are skipped
- Unauthenticated findings are still produced and reported
- `scan.partial_detail` records the session failure reason

### Report generation fails
- Reporter watchdog marks the report `failed` after 30 minutes
- Report can be regenerated via API without re-running the scan
- Finding data is already in the database — generation only reads, never re-scans

### Interactsh server unreachable (during SSRF verification)
- SSRF candidates are marked `is_false_positive=True` with `false_positive_reason='interactsh_unavailable'`
- They are retained in the database but excluded from the report
- A warning is logged with the failed interaction attempt

---

## 14. Data Lifecycle Summary

```
Platform API
  → [Scraper normalizes] → programs, program_scopes, program_policies (Postgres)
  → [scan.jobs] → scan record created (Postgres)
  → [Stage 1] → assets (Postgres)
  → [Stage 2] → assets.technology_stack updated (Postgres)
  → [Stage 3] → endpoints (Postgres), JS files (MinIO + js_assets Postgres)
  → [Stage 3.5] → browser_sessions (Postgres, encrypted)
  → [Stages 4, 4.5, 5, 6, 7, 9] → findings [unverified candidates] (Postgres)
  → [Stage 8] → findings [is_verified=True] (Postgres)
              → finding_evidence (Postgres) + evidence files (MinIO)
              → findings [is_false_positive=True] (Postgres, excluded from reports)
  → [Stage 10] → vulnerability_groups (Postgres)
              → Neo4j graph nodes + edges
              → exploit_chains (Postgres)
  → [report.jobs] → reproduction_packs (Postgres)
                  → report file (MinIO)
                  → reports (Postgres)
  → [User] → downloads report → manual review → platform submission
```

**Storage by system:**
| Data | Where |
|------|-------|
| Program metadata | Postgres |
| Scan + findings | Postgres |
| Browser sessions (encrypted) | Postgres |
| Report files (PDF, DOCX) | MinIO |
| Screenshots + evidence | MinIO |
| JS files (deduplicated) | MinIO |
| Attack graph | Neo4j |
| Distributed locks | Redis |
| Task results | Redis |
| Secrets + credentials | Vault |

---

## 15. Decision Points and Guards

| Point | Condition | Action |
|-------|-----------|--------|
| Scan start | `scan:lock:{program_id}` held | Skip — existing scan in progress |
| Stage 0 | `in_scope` list is empty | FATAL — `status=failed_scope`, stop |
| Stage 1 | Asset fails `ScopeFilter` | Drop asset silently, continue |
| Every stage | Asset/endpoint fails `ScopeFilter` | Drop and log — never skip the check |
| Stage 3.5 | TOTP secret not in Vault | `CollectorAuthError`, session=None, scan continues |
| Stage 3.5 | Session bootstrap times out | session=None, scan continues without auth |
| Stage 8 | `retry_count >= 2` | Watchdog does NOT republish — permanent failure |
| Stage 8 | Interactsh unreachable | SSRF candidate → `is_false_positive=True` |
| Stage 9 | LLM retries exhausted | Return empty list — scan continues without hypotheses |
| Stage 10 | Aggregation fails | FATAL — `status=failed_internal` |
| Report generation | `has_findings=False` | Generate "No Findings" report — never skip or crash |
| MinIO upload | Any bucket | Never `mc anonymous set download` — all access via pre-signed URL |
| All queues | Passive declare only | Avoids RabbitMQ argument mismatch errors on restart |