# AttackBot — How the System Works (End-to-End Flow)

> Version: 2.1 | Last updated: 2026-03-24
> Purpose: A teaching-first walkthrough of how AttackBot works, from the moment it discovers a bug bounty program to the moment it produces a vulnerability report. Every concept is explained before it's used. Every "why" comes before the "how."
> Scope: This document maps directly to the code in `backend/`. Planned-only features are explicitly marked.

---

## Table of Contents
1. [The Big Picture — What AttackBot Actually Does](#1-the-big-picture)
2. [How a Scan Starts](#2-how-a-scan-starts)
3. [Phase 1 — Finding Bug Bounty Programs (Scraper)](#3-phase-1--finding-bug-bounty-programs-scraper)
4. [Phase 2 — Receiving and Starting the Scan (Core Engine)](#4-phase-2--receiving-and-starting-the-scan-core-engine)
5. [Phase 3 — Running the Scanning Pipeline (Stages 0–6, 10)](#5-phase-3--running-the-scanning-pipeline-stages-06-10)
6. [Phase 4 — Browser Session Bootstrap (Stage 3.5)](#6-phase-4--browser-session-bootstrap-stage-35) *(planned: M5)*
7. [Phase 5 — API Fuzzing + Enhanced JS Analysis (Stages 4.5 + 6)](#7-phase-5--api-fuzzing--enhanced-js-analysis-stages-45--6) *(planned: M6)*
8. [Phase 6 — Behavioral Scenarios (Stage 7)](#8-phase-6--behavioral-scenarios-stage-7) *(planned: M9)*
9. [Phase 7 — Exploit Verification (Stage 8)](#9-phase-7--exploit-verification-stage-8) *(planned: M7)*
10. [Phase 8 — AI Hypothesis (Stage 9)](#10-phase-8--ai-hypothesis-stage-9) *(planned: M10)*
11. [Phase 9 — Aggregation: Cleaning Up and Saving Results (Stage 10)](#11-phase-9--aggregation-stage-10)
12. [Phase 10 — Report Generation (Reporter)](#12-phase-10--report-generation-reporter)
13. [Phase 11 — Manual Submission](#13-phase-11--manual-submission)
14. [What Happens When Things Go Wrong](#14-what-happens-when-things-go-wrong)
15. [Data Lifecycle Summary](#15-data-lifecycle-summary)
16. [Decision Points and Guards](#16-decision-points-and-guards)
17. [Code-to-Flow Reference Map](#17-code-to-flow-reference-map)

---

## 1. The Big Picture

Before diving into details, here's what AttackBot does at the highest level:

**AttackBot is an automated bug bounty hunting machine.** Companies like HackerOne and BugCrowd run programs where they pay hackers to find vulnerabilities in their customers' websites. AttackBot automates the "find vulnerabilities" part of that process — scanning websites for security issues, producing evidence-backed reports, and leaving the final human review and submission to you.

The system works in a pipeline:

```
1. DISCOVER   → Find bug bounty programs on platforms like HackerOne
2. SCOPE      → Learn what domains/URLs the program allows you to test
3. RECON      → Find live hosts, subdomains, endpoints, and JS files
4. SCAN       → Test those endpoints for known vulnerabilities (XSS, CORS, secrets, etc.)
5. AGGREGATE  → Deduplicate and save findings to the database
6. REPORT     → Generate a PDF/DOCX report (planned — M4)
7. SUBMIT     → You manually submit the report to the platform
```

**What's implemented today (through M3):** Steps 1–5 are fully working. Step 6 receives scan results but doesn't generate reports yet. Step 7 is always manual.

### Key Concepts You'll See Throughout

Before we go further, let's define some terms that appear everywhere in the codebase:

- **Program:** A bug bounty program hosted on a platform like HackerOne. For example, "Shopify" runs a bug bounty program on HackerOne where they pay for security vulnerabilities found in their systems.

- **Scope:** The list of domains, URLs, and IP ranges that a program says you're allowed to test. For example, Shopify might say "you can test `*.shopify.com` but NOT `admin.shopify.com`." This is critical — scanning anything outside scope is a violation of the program's rules.

- **Asset:** A live web host discovered during scanning. When we find that `api.shopify.com` is running an HTTP server, that becomes an asset in our database.

- **Endpoint:** A specific URL path on an asset. If `api.shopify.com` has `/api/v1/users` and `/api/v1/orders`, those are two separate endpoints.

- **Finding (or Finding Candidate):** A potential vulnerability discovered by a scanner. At this stage it's unverified — we think we found an XSS, but haven't confirmed it actually works yet.

- **Queue (`scan.jobs`, `report.jobs`):** Services in AttackBot don't call each other directly for heavy work. Instead, they drop messages onto RabbitMQ queues (think of them as conveyor belts). One service puts a message on the belt, and another service picks it up when it's ready. This means if a service crashes, the message isn't lost — it stays on the belt until someone processes it.

- **Redis Lock:** A distributed lock stored in Redis that prevents two workers from doing the same work at the same time. For example, if a scan for program X is already running, a Redis lock prevents a second scan for program X from starting.

---

## 2. How a Scan Starts

There are three ways to kick off a scan. All three end up putting a message on the `scan.jobs` queue, which the Core Engine picks up.

### Way 1 — Automatic (Scheduled Scrape)

This is the normal, hands-off mode.

When the Scraper service starts up, it registers two background jobs that run on timers (using a library called APScheduler):

**Job A: "Go scrape HackerOne for new programs"** — runs every few hours.
- This goes to HackerOne's API, downloads the list of all active bug bounty programs, and saves them to our database.
- It does NOT immediately start scanning anything. It just updates our local copy of "what programs exist."

**Job B: "Check if any saved programs need scanning"** — also runs on a timer.
- This looks through our database for programs that haven't been scanned recently. The logic is: "if we saved this program's data from HackerOne within the last 7 days, and we haven't scanned it yet (or it's been a while since the last scan), it's due for a scan."
- For each program that qualifies, it puts a message on the `scan.jobs` queue saying "hey Core Engine, please scan this program."

**Why are they separate?** Because scraping HackerOne (getting the program list) and deciding what to scan are two different concerns. You might want to scrape HackerOne every 6 hours but only publish scan jobs every hour. Separating them also means a scrape failure doesn't block scan job publishing, and vice versa.

**Code:** `backend/services/scraper/main.py` → `lifespan()` registers both APScheduler jobs.

### Way 2 — Manual Trigger (via Scraper API)

You can manually tell the Scraper to go fetch programs right now:
- `POST /api/v1/scrape/trigger?platform=hackerone` — immediately runs the HackerOne scrape, outside the normal schedule.
- `POST /api/v1/scrape/publish-batch?batch_size=10` — immediately checks for programs due for scanning and publishes up to 10 scan jobs.

**Code:** `backend/services/scraper/main.py` → `trigger_scrape()` and `trigger_scan_publish_batch()`.

### Way 3 — Direct Scan Start (via Core Engine API)

You can skip the Scraper entirely and tell the Core Engine to start a scan for a specific program:
- `POST /api/v1/scans/start` with `{"program_id": "uuid"}`
- The Core Engine will call back to the Scraper API to fetch the program details and scope, build the scan message itself, and put it on `scan.jobs`.

**Code:** `backend/services/core_engine/main.py` → `start_scan()`.

### What prevents duplicate scans?

A scan can be expensive (it runs for hours), so we have guards:
- **Redis lock:** If a scan for program X is already running, a lock key `scan:lock:{program_id}` exists in Redis. Any new scan attempt for program X sees the lock and backs off.
- **Retry cap:** If a program has failed with internal errors 2+ times, we stop auto-retrying. Something is fundamentally wrong and needs human investigation.

---

## 3. Phase 1 — Finding Bug Bounty Programs (Scraper)

**Service:** `scraper` (port 8001)
**What it does:** Goes to bug bounty platforms (like HackerOne), downloads the list of available programs and their scope rules, and saves everything to our database.

### Why does this service exist?

AttackBot can't scan anything without knowing (a) what programs exist, and (b) what those programs allow you to test. HackerOne has an API that provides this information. The Scraper's job is to periodically call that API, pull down the data, normalize it into a standard format, and store it locally so the rest of the system can use it.

### How it works, step by step

#### Step 1 — Connecting to HackerOne

The Scraper has a module called a **Collector**. A Collector is a class that knows how to talk to one specific platform's API. Right now we have one collector — `HackerOneCollector` — but the system is designed so you can add `BugCrowdCollector`, `IntigritiCollector`, etc. later.

All collectors inherit from `BaseCollector` (an abstract base class in `collectors/base.py`), which defines the interface: "you must implement a `collect()` method that returns a list of programs." The `CollectorRegistry` keeps track of which platforms have collectors.

When `HackerOneCollector` is created, it loads API credentials from environment variables (`HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN`). These are used for HTTP Basic Auth on every API call.

**Code:** `backend/services/scraper/collectors/hackerone.py` → `HackerOneCollector.__init__()`

#### Step 2 — Fetching the program list

`HackerOneCollector.collect()` calls `GET /v1/hackers/programs` on HackerOne's API. This returns pages of programs (100 per page). The collector loops through all pages until HackerOne returns an empty list, meaning we've fetched everything.

Each page is processed immediately rather than loading all programs into memory at once. This matters because HackerOne has thousands of programs.

**Rate limiting:** If HackerOne responds with `HTTP 429` (too many requests), the collector reads the `Retry-After` header (which tells us how many seconds to wait), sleeps for that duration, and retries. If it gets 3 consecutive 429s, it gives up on this scrape cycle and will try again at the next scheduled time.

**Code:** `backend/services/scraper/collectors/hackerone.py` → `HackerOneCollector.collect()`

#### Step 3 — Getting program details and scope

For each program in the listing, the collector makes two more API calls:
- `GET /v1/hackers/programs/{handle}` — full program details (name, bounty amounts, whether it's active, etc.)
- `GET /v1/hackers/programs/{handle}/structured_scopes` — the scope rules (what domains/URLs you're allowed to test)

The structured scopes call is critical because it returns machine-parseable scope data. HackerOne also has a "policy" field with markdown text, but we never parse that — structured scopes are always preferred because they're unambiguous.

#### Step 4 — Normalizing the data

Every platform (HackerOne, BugCrowd, etc.) formats their data differently. The collector normalizes everything into a standard format:
- `platform`: "hackerone" (or "bugcrowd", etc.)
- `handle`: the unique slug for this program on the platform (e.g., "shopify")
- `bounty_type`: either "bug_bounty" (pays money) or "vdp" (vulnerability disclosure program — no money, just recognition)
- `max_bounty`: highest possible payout
- `is_active`: whether the program is currently running
- `in_scope` / `out_of_scope`: the scope rules

#### Step 5 — Parsing scope rules

Raw scope entries from platforms come in various formats. The `ScopeParser` class (in `scope_parser.py`) converts them into typed objects:

| Raw Input | Parsed As | Stored Type |
|-----------|-----------|-------------|
| `*.example.com` | Wildcard domain (matches all subdomains) | `wildcard_domain` |
| `192.168.1.0/24` | IP range | `ip_range` |
| `https://example.com/api/` | URL with path prefix | `url` |
| `com.example.app` | Mobile app bundle | `mobile_app` |

Each entry is saved in the `program_scopes` database table with a `scope_type` of either `in_scope` or `out_of_scope`.

**Code:** `backend/services/scraper/scope_parser.py` → `ScopeParser`

#### Step 6 — Saving to the database

`ProgramRepository.upsert()` writes the program data to Postgres. It uses `INSERT ... ON CONFLICT DO UPDATE`, meaning:
- If this program doesn't exist yet → create it.
- If it already exists → update the fields with the latest data.

One important detail: if the program has a flag called `queued_for_scan=True` (meaning we tried to send a scan message but it failed, and we need to retry), the upsert will NOT overwrite that flag. This prevents us from losing track of programs that still need retrying.

**Code:** `backend/services/scraper/repository.py` → `ProgramRepository.upsert()`

#### Step 7 — Publishing scan jobs

This is where the **second scheduler job** (`_publish_due_scan_jobs()`) comes in. Remember, scraping and scan-publishing are separated.

This function queries the database for programs that are "due for scanning." A program is due for scanning when:
- It was scraped recently enough (within the last 7 days)
- It hasn't been scanned yet, or enough time has passed since its last scan

For each eligible program, it:
1. Builds a `ScanJobsPayload` (a Pydantic model containing the program ID, scope rules, feature flags, and priority)
2. Wraps it in a `MessageEnvelope` (a standard wrapper that adds event type, schema version, timestamp, and a unique event ID)
3. Publishes the envelope to the `scan.jobs` RabbitMQ queue

If publishing succeeds, the program's `queued_for_scan` flag is cleared. If it fails (e.g., RabbitMQ is down), the flag is set to `True`.

**Code:** `backend/services/scraper/main.py` → `_publish_due_scan_jobs()`, `backend/services/scraper/publisher.py` → `ScraperPublisher`

#### Step 8 — The Reconciler (safety net)

What if a scan job fails to publish and RabbitMQ comes back online later? The **Reconciler** handles this. It's another APScheduler job that runs every 5 minutes and looks for any programs where `queued_for_scan=True`. For each one, it tries to publish the scan job again. If it succeeds, it clears the flag. If it fails, it leaves the flag for the next cycle.

Programs with `last_scraped_at` older than 7 days are not retried automatically — they need a fresh scrape first, because their scope data might be outdated.

**Code:** `backend/services/scraper/reconciler.py`

#### Step 9 — Redis lock (preventing duplicate scrapes)

What if two scheduler cycles overlap and both try to scrape HackerOne at the same time? That would waste API quota and could cause data races. To prevent this, each scrape acquires a Redis lock (`scraper:lock:{platform}`) before starting. If the lock is already held by another scrape, the new one is skipped entirely — it'll try again next cycle.

**Code:** `backend/services/scraper/main.py` → `_run_platform_scrape()`

---

## 4. Phase 2 — Receiving and Starting the Scan (Core Engine)

**Service:** `core-engine` (port 8002) for the API, `core-worker` (Celery) for processing
**Receives from:** `scan.jobs` queue
**Sends to:** `report.jobs` queue

### Why are there two processes for one service?

The Core Engine is split into two processes:
- **`core-engine`** is a FastAPI web server that provides REST APIs (start a scan, list scans, view findings, check health).
- **`core-worker`** is a Celery worker that processes scan jobs from the queue. Scans are heavyweight (they run external tools, make thousands of HTTP requests, and take minutes to hours), so they can't run inside a web server request.

They share the same code (in `backend/services/core_engine/`) but run as separate containers.

### What happens when a scan job arrives

#### Step 1 — Message receipt

The `core-worker` Celery process is always listening on the `scan.jobs` queue. When a message arrives:

1. **Deserialization:** The raw JSON dict is parsed into a `MessageEnvelope` (our standard message wrapper). This contains the event type (`"program.scraped"`), schema version, and the actual payload.

2. **Validation:** We check that:
   - `event_type` is `"program.scraped"` (the only type we expect on `scan.jobs`)
   - `schema_version` starts with `"1."` (so we can add breaking changes in v2 later)
   - The payload is a valid `ScanJobsPayload` (has a program_id, scope, etc.)

3. **Delegation:** The validated payload is passed to `run_scan_task(payload)`.

**Important Celery configuration:**
- `task_acks_late=True`: the message is NOT removed from the queue until the scan finishes. If the worker crashes mid-scan, RabbitMQ redelivers the message.
- `worker_prefetch_multiplier=1`: each worker only grabs one scan at a time. Scans are heavy — we don't want to buffer multiple.
- `max_retries=0`: Celery won't auto-retry failed tasks. Our own watchdog handles retries.

**Code:** `backend/services/core_engine/worker.py` → `scan_task()`

#### Step 2 — Setup and scope fetching

`run_scan_task()` is a synchronous wrapper that launches the async pipeline. Inside `_async_scan_pipeline()`:

**a. Initialize connections:**
- Set up the database connection pool (`init_db()`)
- Set up the MinIO (object storage) client (`init_storage()`)

**b. Fetch the scope from the Scraper:**
The scan message contains the scope, but the pipeline also makes a fresh API call to the Scraper (`GET /api/v1/programs/{program_id}/scope`) to get the most up-to-date scope. If the scope is empty (no in-scope entries at all), the scan immediately fails with `status=failed_scope` — we refuse to scan anything without a clearly defined scope.

**c. Build the ScanContext:**
The `ScanContext` is a bundle of everything the pipeline stages need to know:
- `scan_id`: unique ID for this scan
- `program_id`: which program we're scanning
- `scope`: the in-scope and out-of-scope rules
- `feature_flags`: which scanners to enable (e.g., enable XSS scanning? CORS scanning? CRLF? SQLi is disabled by default because it's more risky)
- `priority`: how urgently this scan should run

This object is passed to every stage and is treated as **read-only** — stages can read it but must not modify it.

**Code:** `backend/services/core_engine/scan_task.py` → `_async_scan_pipeline()`

#### Step 3 — Create or resume the scan record

Before doing any work, we create a row in the `scans` database table. This is where we track the scan's status throughout its lifecycle.

Three scenarios:
1. **Normal case:** A new scan row is created with `status=pending`.
2. **After a crash restart:** If a `running` scan already exists for this program (maybe the worker crashed mid-scan), we reuse that row instead of creating a duplicate.
3. **After a previous failure:** If a `failed_internal` scan exists with `retry_count < 2`, we reuse it and bump the retry count. This gives each scan up to 2 automatic retries before giving up.

**Code:** `backend/services/core_engine/repository.py` → `ScanRepository.create_or_resume_scan()`

#### Step 4 — Acquire the Redis scan lock

We try to acquire `scan:lock:{program_id}`. If another scan for this program is already running (the lock is held), we exit immediately. The message is still acknowledged (removed from the queue) because the running scan will produce results — we don't want to pile up duplicate scans.

#### Step 5 — Run the pipeline

With everything set up, we call `_execute_pipeline()` which runs Stages 0 through 10. If anything goes fatally wrong, the scan is marked `failed_internal`.

### The Watchdog — catching stuck scans

Sometimes a scan gets stuck (the worker died without releasing the lock, the scan hit an infinite loop, etc.). The Core Engine's FastAPI process runs a **watchdog** job every 15 minutes that queries the database for scans that have been in `status=running` for more than 2 hours. For each stuck scan:
- It marks the scan as `failed_internal` with `error_detail='watchdog_timeout'`
- If the scan has been retried fewer than 2 times, it publishes a new scan job to `scan.jobs` so it can try again
- It releases the Redis lock

**Code:** `backend/services/core_engine/watchdog.py` + `main.py` → `lifespan()` scheduler

---

## 5. Phase 3 — Running the Scanning Pipeline (Stages 0–6, 10)

The pipeline is where the actual security scanning happens. It's a sequence of stages, each responsible for one specific task. All stages run inside the `core-worker` process.

**Code:** `backend/services/core_engine/scan_task.py` → `_execute_pipeline()`

Here's the order:

```
Stage 0  → Scope Filter:        Make sure we know what we're allowed to scan           [FATAL if fails]
Stage 1  → Asset Discovery:     Find live hosts/subdomains within scope
Stage 2  → Fingerprinting:      Identify what technology each host is running
Stage 3  → Enumeration:         Find specific URL paths, directories, and JS files
Stage 4  ┐                      
         ├→ Run in PARALLEL:    Stage 4 (Nuclei scanning) and Stage 5 (web vuln tests)
Stage 5  ┘                      
Stage 6  → JS Secret Scanning:  Look for hardcoded API keys and passwords in JS files
Stage 10 → Aggregation:         Deduplicate findings, save to DB, send to reporter     [FATAL if fails]
```

**Error handling:** Each stage is wrapped in try/except. If a non-fatal stage fails (say Stage 2 crashes), the error is logged and the pipeline continues with the next stage. The scan's final status will be `"partial"` instead of `"completed"` so you know something went wrong. Only two stages are FATAL — Stage 0 and Stage 10 — because without scope you can't scan anything, and without aggregation you can't save results.

### Stage 0 — Scope Filter (FATAL)

**File:** `backend/services/core_engine/pipeline/scope_filter.py`

**What it does:** Before scanning anything, we build a `ScopeFilter` object. This object knows how to answer one question: "is this URL/domain/IP within the program's declared scope?"

**Why it's the first stage:** Every subsequent stage uses the ScopeFilter to decide whether a discovered host or endpoint is allowed. Without it, we'd risk scanning things we're not authorized to scan — which could have legal consequences.

**How the ScopeFilter works:**

When you call `scope_filter.is_in_scope("https://api.example.com/users")`:

1. It extracts the hostname: `api.example.com`
2. It tries to parse it as an IP address (in case you gave it `192.168.1.1`; if it's a domain name, this step just returns None)
3. It checks the **out-of-scope** rules first. If the target matches ANY out-of-scope rule, it's immediately rejected. Out-of-scope always wins over in-scope.
4. It checks the **in-scope** rules. The target must match at least one in-scope rule to be accepted.

**How rule matching works:**

| Rule Type | Example | Matches |
|-----------|---------|---------|
| Wildcard domain (`*.example.com`) | `*.example.com` | `sub.example.com`, `deep.sub.example.com` — but NOT `example.com` itself |
| Root domain | `example.com` (asset_type: domain) | `example.com` AND all subdomains: `anything.example.com` |
| Exact match | `api.example.com` (plain string) | Only `api.example.com` |
| CIDR range | `192.168.1.0/24` | Any IP in that range |

**If the in-scope list is empty**, the constructor raises a `ScanError`. The pipeline catches this and marks the scan as `failed_scope` — we will never scan blindly.

### Stage 1 — Asset Discovery

**File:** `backend/services/core_engine/pipeline/asset_discovery.py`

**What it does:** Discovers all live web servers within scope by combining four external tools in sequence.

**Why it exists:** A bug bounty program might say "you can scan `*.example.com`" but that's just a wildcard — we need to find out what subdomains actually exist (like `api.example.com`, `staging.example.com`, `docs.example.com`) and which of those are running web servers.

**The discovery chain works like this:**

First, the stage figures out which domains to use as starting points ("seeds"). It looks at the in-scope rules:
- `*.example.com` → use `example.com` as a seed
- `https://api.example.com/v1` → extract `api.example.com` as a seed (but only if it's covered by an in-scope domain rule)
- `com.example.app` (mobile app) → skip (not a web domain)

Then, for each seed domain, it runs four tools in sequence:

**Tool 1: `subfinder`** — Passive subdomain enumeration
```
subfinder -d example.com -all -silent
```
This doesn't actually contact `example.com` — it queries public data sources (DNS records, certificate transparency logs, search engines) to find known subdomains. Output: `api.example.com`, `dev.example.com`, `staging.example.com`, etc.

**Tool 2: `alterx`** — Subdomain permutation
```
alterx -silent
```
Takes subfinder's output and generates variations. If subfinder found `api.example.com` and `dev.example.com`, alterx might generate `api-dev.example.com`, `staging.api.example.com`, `dev2.example.com`, etc. This catches subdomains that public data sources don't know about.

**Tool 3: `dnsx`** — DNS resolution
```
dnsx -l {targets_file} -a -resp -silent
```
Takes the expanded subdomain list and checks which ones actually resolve to an IP address via DNS. This step is mandatory — alterx can generate thousands of permutations, and most of them don't exist. Without DNS filtering, we'd send thousands of non-existent hosts to the next tool, wasting time and resources.

**Tool 4: `httpx`** — HTTP probing
```
httpx -l {targets_file} -json -silent -status-code -title -tech-detect -no-color
```
Takes the DNS-verified list and checks which hosts have a live web server. For each live host, it captures: HTTP status code, page title, detected technologies (like "nginx", "React", "WordPress"), content type, and server header. Output is JSON Lines format (one JSON object per line).

**All tools are run via** `subprocess_utils.run_tool_communicate()`, which wraps `asyncio.subprocess` with timeout enforcement and error handling.

**After discovery:** Each resulting live host becomes a `DiscoveredAsset` object. Example:
```python
DiscoveredAsset(
    asset_type="subdomain",
    value="https://api.example.com",
    http_status=200,
    technology_stack={"technologies": ["nginx", "React"]},
    waf_detected=None,
)
```

Every asset is checked against the ScopeFilter one more time before being saved. Assets are deduplicated (if `https://api.example.com` and `https://api.example.com/` both appear, they're collapsed into one), then persisted to the `assets` database table.

### Stage 2 — Fingerprinting

**File:** `backend/services/core_engine/pipeline/fingerprinting.py`

**What it does:** Enriches the assets from Stage 1 with more detailed technology information.

**Why it exists:** Stage 1 already got some tech info from httpx, but this stage runs httpx again with extended fingerprinting options to get a fuller picture. Knowing the technology stack helps later stages — for example, there's no point running SQL injection tests against a static file server.

It also detects **WAF (Web Application Firewall)** presence. A WAF is a security layer (like Cloudflare, AWS WAF, or Akamai) that sits in front of a web application and blocks suspicious requests. The `waf_utils.detect_waf_technology()` function checks if any of the detected technologies are known WAF products.

**Important design decision:** WAF presence is noted but does NOT block scanning. All scanners still run, because many WAFs have bypasses, and the finding itself is still valuable even if the WAF blocks the exploit.

### Stage 3 — Enumeration

**File:** `backend/services/core_engine/pipeline/enumeration.py`

**What it does:** Discovers specific URL paths and directories on each asset, plus downloads JavaScript files for analysis in Stage 6.

**Think of it this way:** Stage 1 found "api.example.com exists." Stage 3 finds "api.example.com has `/login`, `/api/v1/users`, `/api/v1/orders`, `/static/app.js`."

**Two discovery tools:**

**a. `ffuf`** (directory brute-forcing):
```
ffuf -u https://api.example.com/FUZZ -w {wordlist} -o {output} -of json -mc all -fc 404
```
Tries thousands of common path names (from a wordlist) against each asset. The word `FUZZ` in the URL is replaced with each word from the list. Responses with status 404 are filtered out (they mean "not found"). Everything else is recorded. Each discovered path becomes a `DiscoveredEndpoint` object.

**b. `waybackurls`** (historical URL discovery):
```
waybackurls example.com
```
Queries the Wayback Machine (Internet Archive) and Common Crawl for URLs that were historically associated with this domain. Websites change over time, but old endpoints often still work. Each URL is scope-filtered before being recorded.

**JavaScript file handling:** During enumeration, any URLs ending in `.js` are identified. Each JS file is:
1. Downloaded via HTTP
2. SHA-256 hashed (to detect duplicates — many pages load the same JS bundle)
3. Uploaded to MinIO (our object storage) under the `js-assets/` bucket
4. Recorded in the `js_assets` database table

If a JS file with the same content hash already exists (from a previous scan or stage), the upload is skipped and the existing record is reused. This prevents storing duplicate copies of `jQuery.min.js` a thousand times.

The JS asset IDs are saved in `ctx.js_asset_ids` so Stage 6 can retrieve and scan them later.

### Stages 4 + 5 — Parallel Scanning

After Stage 3 completes, Stage 4 and Stage 5 run **at the same time** (using `asyncio.gather()`). This saves time because they're independent — they both read from the discovered assets/endpoints but don't depend on each other's results.

```python
# From scan_task.py → _execute_pipeline():
results = await asyncio.gather(
    nuclei_scan.run(ctx, assets, scope_filter, config),
    web_vuln_tests.run(ctx, endpoints, scope_filter, feature_flags),
    return_exceptions=True,
)
```

### Stage 4 — Nuclei Scanning

**File:** `backend/services/core_engine/pipeline/nuclei_scan.py`

**What it does:** Runs [nuclei](https://github.com/projectdiscovery/nuclei) — an open-source vulnerability scanner that uses YAML templates — against all discovered assets.

**Why nuclei:** Nuclei has a massive community-maintained library of templates that check for thousands of known vulnerabilities: exposed admin panels, default credentials, CVEs, misconfigurations, etc. Instead of writing custom checks for each known vulnerability, we let nuclei's template engine handle it.

**How it works:**

1. Build a list of target URLs from all in-scope assets
2. Filter them through the ScopeFilter one more time (belt and suspenders — we never trust that a previous stage did the filtering correctly)
3. Write targets to a temp file and run nuclei:
   ```
   nuclei -l targets.txt -json -silent -rate-limit 150 -bulk-size 75
          -concurrency 25 -exclude-tags headless
   ```
   - `-exclude-tags headless`: skip templates that require a browser (those will be handled in M5)
   - `-json -silent`: output findings as JSON, don't print progress bars
   - Rate/concurrency settings come from `EngineConfig`

4. Parse the JSON output — each line is a potential finding
5. For each finding, verify the matched URL is in scope, then create a `FindingCandidate`

**Exit code handling:** Nuclei has quirky exit codes. Exit code 1 means "ran successfully but found nothing" (not an error!). Exit code 2 means "couldn't even start" — and the code classifies why (missing templates, bad targets, etc.) to help with debugging.

### Stage 5 — Web Vulnerability Tests

**File:** `backend/services/core_engine/pipeline/web_vuln_tests.py`

**What it does:** Our own custom vulnerability scanners targeting specific vulnerability classes. Unlike nuclei (which uses templates), these are hand-coded scanning functions.

**Currently implemented tests:**

**a. Passive Sensitive Path Detection** (no HTTP requests needed):
Before even sending traffic, the stage checks if any enumerated paths are sensitive files:
- `/.env` → environment file (may contain database passwords, API keys)
- `/.git/HEAD` → Git metadata (source code exposure)
- `/.git/config` → Git config (may reveal internal repository URLs)

If ffuf found one of these paths responding with HTTP 200, that's a critical finding.

**b. Reflected XSS Scanner:**
For each endpoint that has parameters (like `?search=hello`), the scanner injects XSS payloads:
- `<script>alert(1)</script>`
- `"><img src=x onerror=alert(1)>`
- `';alert(1)//`

It sends: `GET https://target.com/search?q=<script>alert(1)</script>` and checks if the payload appears **verbatim** in the response body. If it does, the application isn't sanitizing user input — that's a reflected XSS finding.

Only 10 parameters per endpoint are tested (to avoid being too aggressive), and only the first successful payload per parameter is recorded.

**c. CORS Misconfiguration Scanner:**
CORS (Cross-Origin Resource Sharing) controls which websites can make API calls to your server. A misconfigured CORS policy can let attackers steal data from your users.

The scanner sends requests with fake `Origin` headers (like `Origin: https://evil.com`) and checks if the server reflects that origin back in `Access-Control-Allow-Origin` AND sets `Access-Control-Allow-Credentials: true`. If both conditions are true, any website can make authenticated requests to this server — that's a serious misconfiguration.

**d. CRLF Injection Scanner** (gated by feature flag — off by default):
Tests whether the server is vulnerable to CRLF injection (injecting HTTP headers via `\r\n` characters in the URL). Only runs when `feature_flags.crlf=True`.

**e. SQLi, SSRF** — not yet implemented. The code has placeholder comments for these; they'll be added in M6+.

**HTTP client config:** The scanner uses Python's `httpx` library (not the command-line httpx tool from Stage 1) with `verify=False` (TLS cert validation disabled — scanning targets often have invalid certificates) and `follow_redirects=False` (we want to see the original response, not follow redirects).

### Stage 6 — JS Secret Scanning

**File:** `backend/services/core_engine/pipeline/js_secrets.py`

**What it does:** Downloads and scans JavaScript files (saved during Stage 3) for hardcoded secrets like API keys, passwords, and tokens.

**Why it exists:** Developers frequently accidentally leave secrets in their JavaScript code. A hardcoded AWS key in a JS file means anyone can access that AWS account. These are often easy-to-exploit, high-severity findings.

**How it works:**

1. For each JS asset saved in Stage 3, download the file content from MinIO
2. Run 12 regex patterns against the content:

   | What it looks for | Example match | Severity |
   |-------------------|---------------|----------|
   | Google API Key | `AIzaSyD-abc123...` | high |
   | Firebase Server Key | `AAAA...:...` | high |
   | OpenAI API Key | `sk-abc123...` (48 chars) | critical |
   | Slack Token | `xoxb-123-456-abc` | high |
   | Generic API key assignment | `api_key = "abc123..."` | medium |
   | Hardcoded password | `password = "mysecretpw"` | high |
   | Secret key assignment | `secret_key = "..."` | high |
   | JWT Token | `eyJhbGciOi...` (base64 dots) | medium |
   | PEM Private Key | `-----BEGIN RSA PRIVATE KEY-----` | critical |
   | GitHub Token | `ghp_abc123...` (36 chars) | critical |
   | AWS Access Key ID | `AKIA...` (20 chars) | critical |
   | AWS Secret Access Key | In assignment context, 40 chars | critical |

3. For each match, only the **first occurrence** is reported (we don't emit hundreds of findings if the same key appears 50 times in the file)
4. If a JS file can't be downloaded from MinIO (maybe it was deleted), the error is logged and the scanner moves on to the next file — it never crashes the whole stage

---

## 6. Phase 4 — Browser Session Bootstrap (Stage 3.5) *(planned: M5 — not yet implemented)*

**Worker:** `browser-worker` (Celery)
**Queue:** `browser.jobs`

> The `browser_worker/worker.py` currently exists as a skeleton. The actual browser automation logic will be implemented in M5.

**What it will do:** Some vulnerability scanning requires being logged in (for example, testing IDOR — "can user A see user B's data?"). Stage 3.5 will use Playwright (a headless browser automation library) to:
1. Navigate to the target's login page
2. Fill in credentials (retrieved from HashiCorp Vault, never stored in config files)
3. Capture session cookies and tokens
4. Pass those sessions to downstream scanning stages

---

## 7. Phase 5 — API Fuzzing + Enhanced JS Analysis (Stages 4.5 + 6) *(planned: M6)*

> Skeleton workers exist. Will add schema-aware API fuzzing (Schemathesis + RESTler) and deeper JS analysis (Semgrep + AST parsing for DOM XSS, prototype pollution, etc.).

---

## 8. Phase 6 — Behavioral Scenarios (Stage 7) *(planned: M9)*

> Skeleton worker exists. Will add race condition testing, privilege escalation detection, and workflow bypass scenarios.

---

## 9. Phase 7 — Exploit Verification (Stage 8) *(planned: M7)*

> Skeleton worker exists. This is the quality gate — it will verify that findings are real (not false positives) by replaying exploits in a headless browser and collecting evidence (screenshots, HTTP captures, OOB callbacks).

---

## 10. Phase 8 — AI Hypothesis (Stage 9) *(planned: M10)*

> Skeleton worker exists. Will use a local LLM (Ollama) to analyze scan results and suggest additional attack vectors to try.

---

## 11. Phase 9 — Aggregation: Cleaning Up and Saving Results (Stage 10)

**File:** `backend/services/core_engine/pipeline/aggregator.py`

**What it does:** This is the final step of the pipeline. It takes all the finding candidates from Stages 4, 5, and 6, deduplicates them, saves them to the database, and tells the Reporter service that the scan is done.

**This stage is FATAL** — if it fails, the scan is marked `failed_internal`. Why? Because if we can't save the results, the entire scan was wasted.

### Step-by-step:

#### 1. Deduplication

Different stages can find the same vulnerability. For example, nuclei might detect a reflected XSS on `/search?q=test`, and Stage 5's XSS scanner might find the same thing. We don't want two identical findings in the report.

Each finding gets a **deduplication hash** computed by:
```
SHA-256( vulnerability_type | normalized_url | parameter | first_100_chars_of_payload )
```

URL normalization sorts query parameters so `?b=2&a=1` and `?a=1&b=2` produce the same hash. If two findings have the same hash, only the first one is kept.

**Code:** `backend/services/core_engine/dedup.py` → `compute_dedup_hash()`

#### 2. Persistence

The deduplicated findings are written to the `findings` database table. Each finding gets a UUID, and the database has a uniqueness constraint on `(deduplication_hash, scan_id)` so duplicates are silently ignored even if they slip through.

All findings are saved with `is_verified=False` — Stage 8 (exploit verification, planned for M7) will later flip this to `True` for confirmed findings.

#### 3. Severity breakdown

The aggregator counts findings by severity level:
```python
{"critical": 1, "high": 3, "medium": 5, "low": 2, "info": 0}
```
This summary is stored on the scan record and included in the message to the Reporter.

#### 4. Scan finalization

The `scans` row is updated with:
- `status`: either `"completed"` (all stages ran) or `"partial"` (some stages failed)
- `finding_count`: total number of deduplicated findings saved
- `severity_breakdown`: the counts from step 3
- `completed_at`: timestamp

If any stages had errors, `partial_detail` records which stages failed and why.

#### 5. Publishing to report.jobs

Finally, the aggregator sends a message to the `report.jobs` queue telling the Reporter service: "scan X is done, here's the summary." The message contains the scan ID, program ID, finding count, severity breakdown, and whether there are any findings at all.

**Code:** `backend/services/core_engine/pipeline/aggregator.py`

---

## 12. Phase 10 — Report Generation (Reporter)

**Service:** `reporter` (port 8003) + `reporter-worker` (Celery)
**Receives from:** `report.jobs` queue

### Current state: message validation only (M4 will add actual generation)

Right now, the reporter worker receives the `scan.completed` message from the aggregator, validates it (deserializes the envelope, checks schema version, parses the payload), and logs all the details — scan ID, finding count, severity breakdown, etc. Then it logs a warning: `"report_generation_not_yet_implemented"`.

The reporter worker uses a raw Kombu consumer (a lower-level RabbitMQ consumer) rather than a Celery task decorator. This is because `report.jobs` messages are published as raw JSON by the Core Engine, not dispatched through Celery's task routing. There's also a compatibility Celery task that handles messages if they happen to arrive via Celery's routing.

Messages are always acknowledged after processing (even if validation fails) to prevent infinite redelivery loops.

**Code:** `backend/services/reporter/worker.py`

### What M4 will add

The full Reporter will:
1. Fetch detailed scan results from the Core Engine API
2. Fetch program metadata from the Scraper API
3. Generate a PDF with cover page, executive summary, per-finding detail pages, and reproduction steps
4. Generate a DOCX with the same content
5. Upload both files to MinIO and record them in a `reports` database table
6. Provide a download API: `GET /api/v1/reports/{report_id}/download` → pre-signed MinIO URL

---

## 13. Phase 11 — Manual Submission

This is intentionally NOT automated. After AttackBot produces a report:

1. You download the report.
2. You review it — checking that findings are actually in scope, haven't already been reported, and the severity is reasonable.
3. You submit it manually on the bug bounty platform.

**Why not auto-submit?** Because submitting duplicate or out-of-scope reports can get you banned from bug bounty platforms. Human judgment is required for the submission decision.

---

## 14. What Happens When Things Go Wrong

### A pipeline stage fails (non-fatal)

- The error is caught, logged, and stored in `scan_result.stage_errors[stage_name]`
- The pipeline moves on to the next stage
- The scan's final status becomes `"partial"` instead of `"completed"`
- You can see which stages failed and why by checking the scan's `partial_detail`

### Scope is empty or invalid (fatal)

- The scan immediately stops with `status=failed_scope`
- No assets, endpoints, or findings are created
- No report message is sent
- Something is wrong with the program's scope data — human investigation needed

### The worker crashes mid-scan

- Because `task_acks_late=True`, the message goes back to the queue
- When the worker comes back and picks up the message, `create_or_resume_scan()` finds the existing scan row and resumes from where it can
- If the scan has failed 2+ times, the watchdog stops retrying

### A scan job fails to publish to RabbitMQ

- The Scraper sets `queued_for_scan=True` on the program
- The Reconciler retries every 5 minutes until RabbitMQ is back

### A scan gets stuck (running for hours without progress)

- The watchdog catches it after 2 hours
- Marks the scan as `failed_internal` and releases the Redis lock
- If retries remain, publishes a fresh scan job to try again

---

## 15. Data Lifecycle Summary

Here's where every piece of data lives at each stage:

```
HackerOne API
  → Scraper fetches + normalizes
  → programs, program_scopes, program_policies saved to Postgres
  → scan.jobs message published to RabbitMQ
  → Core Worker picks up message
  → Stage 0: ScopeFilter built in-memory (safety check)
  → Stage 1: assets saved to Postgres
  → Stage 2: assets updated with tech stack in Postgres
  → Stage 3: endpoints saved to Postgres, JS files uploaded to MinIO
  → Stages 4+5: finding candidates held in-memory (not yet saved)
  → Stage 6: more finding candidates from JS analysis (in-memory)
  → Stage 10: findings deduplicated and saved to Postgres
  → report.jobs message published to RabbitMQ
  → Reporter worker receives and logs (generation not yet implemented)
```

**What's implemented now vs planned:**

| Data | Where | Implemented? |
|------|-------|-------------|
| Bug bounty programs + scope | Postgres | ✅ M2 |
| Scans + findings + assets + endpoints | Postgres | ✅ M3 |
| JS files (deduplicated by hash) | MinIO | ✅ M3 |
| Distributed locks | Redis | ✅ M2 |
| Browser sessions (encrypted) | Postgres | 🔲 M5 |
| Report files (PDF, DOCX) | MinIO | 🔲 M4 |
| Screenshots + evidence | MinIO | 🔲 M7 |
| Attack graph | Neo4j | 🔲 M8 |
| Secrets + credentials | Vault | ✅ M1 (placeholder) |

---

## 16. Decision Points and Guards

| Situation | What the system checks | What happens |
|-----------|----------------------|-------------|
| Scan starts for a program | Is `scan:lock:{program_id}` held? | If yes: skip scan — one is already running |
| Stage 0 runs | Is the in_scope list empty? | If yes: ABORT scan with `failed_scope` |
| Stage 0 runs | Does the Scraper API return scope? | If no: ABORT scan with `failed_scope` |
| Stage 1 finds a host | Does `ScopeFilter.is_in_scope()` pass? | If no: drop the host, log a warning, continue |
| Stage 3 finds a `.js` URL | Can we download it? | If no: log warning, skip this file, continue |
| Stage 4 runs nuclei | Exit code is 1? | That means "no findings" — NOT an error |
| Stage 4 runs nuclei | Exit code is 2? | Startup failure — log detailed reason, raise |
| Stage 5 tests endpoints | Are SQLi/SSRF feature flags on? | If no: skip those tests entirely |
| Stage 6 downloads JS from MinIO | Does the download fail? | Log warning, skip this file, continue |
| Stage 10 fails | Aggregation crashes? | FATAL — scan marked `failed_internal` |
| Stage 10 publishes to report.jobs | Does publish fail? | Log error, scan is still marked complete (findings are saved to DB regardless) |
| Any non-fatal stage | Unhandled exception? | Catch it, log to stage_errors, continue pipeline |
| Watchdog checks | Scan running > 2 hours? | Mark `failed_internal`, retry if under retry cap |
| Reporter receives message | Validation fails? | Log error, acknowledge message (don't crash worker) |

---

## 17. Code-to-Flow Reference Map

### Shared Library (`backend/shared/`)

| File | Purpose |
|------|---------|
| `config.py` | Base configuration class — all services inherit this to load settings from environment variables |
| `logging.py` | Sets up structured JSON logging for every service |
| `db.py` | Database connection management (PostgreSQL via SQLAlchemy async) |
| `health.py` | Standard health check response models used by every service's `/api/v1/health` endpoint |
| `exceptions.py` | All custom exceptions: `AttackBotError`, `ScanError`, `QueueError`, etc. |
| `queue.py` | RabbitMQ publisher class + queue name constants + dead letter queue setup |
| `vault.py` | HashiCorp Vault client for secrets management |
| `storage.py` | MinIO (S3-compatible) object storage client |
| `schemas/envelope.py` | `MessageEnvelope` — the standard wrapper for all queue messages |
| `schemas/scan_jobs.py` | Data models for `scan.jobs` queue messages |
| `schemas/report_jobs.py` | Data models for `report.jobs` queue messages |

### Scraper (`backend/services/scraper/`)

| File | Purpose |
|------|---------|
| `collectors/base.py` | Abstract base class for platform collectors + registry |
| `collectors/hackerone.py` | HackerOne API client — fetches programs and scope |
| `scope_parser.py` | Converts raw scope data into typed, queryable objects |
| `repository.py` | Database operations for programs, scopes, and policies |
| `publisher.py` | Publishes scan job messages to RabbitMQ with retry flag management |
| `reconciler.py` | Retries publishing for programs that previously failed |
| `config.py` | Scraper-specific settings (API credentials, intervals) |
| `main.py` | FastAPI app: APIs, scheduler setup, Redis locking |

### Core Engine (`backend/services/core_engine/`)

| File | Purpose |
|------|---------|
| `worker.py` | Celery worker that listens on `scan.jobs` and kicks off scans |
| `scan_task.py` | Pipeline orchestrator — sets up context, runs all stages in order |
| `main.py` | FastAPI app: scan start/list/details APIs, watchdog scheduler |
| `repository.py` | All database operations for scans, assets, endpoints, findings, stages |
| `models.py` | Data classes: `DiscoveredAsset`, `DiscoveredEndpoint`, `FindingCandidate`, etc. |
| `dedup.py` | Finding deduplication via SHA-256 hash |
| `cvss.py` | Maps severity labels to CVSS scores |
| `subprocess_utils.py` | Runs external tools (nuclei, httpx, etc.) as subprocesses with timeouts |
| `watchdog.py` | Detects and recovers stuck scans |
| `startup_checks.py` | Validates that external tools (nuclei) are installed when the worker starts |
| `config.py` | Tuning settings for nuclei, httpx, ffuf (rate limits, timeouts, etc.) |

### Pipeline Stages (`backend/services/core_engine/pipeline/`)

| File | Stage | Purpose |
|------|-------|---------|
| `context.py` | — | Data classes shared across all stages (`ScanContext`, `ScopeDefinition`, `FeatureFlags`) |
| `scope_filter.py` | 0 | Scope checking — "is this domain/URL allowed?" |
| `asset_discovery.py` | 1 | Find live hosts via subfinder → alterx → dnsx → httpx |
| `fingerprinting.py` | 2 | Identify technology stack + WAF on each host |
| `enumeration.py` | 3 | Find paths/directories via ffuf + waybackurls, download JS files |
| `nuclei_scan.py` | 4 | Template-based vulnerability scanning |
| `web_vuln_tests.py` | 5 | Custom XSS, CORS, CRLF scanners + sensitive path detection |
| `js_secrets.py` | 6 | Find API keys and passwords hardcoded in JavaScript |
| `aggregator.py` | 10 | Deduplicate findings, save to DB, publish scan results |
| `waf_utils.py` | — | Helper function to detect WAF technologies |

### Reporter (`backend/services/reporter/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — health endpoint only (report APIs coming in M4) |
| `worker.py` | Consumes `report.jobs` messages, validates them, logs details (generation not yet implemented) |