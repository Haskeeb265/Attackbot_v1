# AttackBot — How the System Works (End-to-End Flow)

> Version: 3.0 | Last updated: 2026-04-13
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
6. REPORT     → Generate PDF/DOCX reports with evidence and reproduction steps
7. SUBMIT     → You manually submit the report to the platform
```

**What's implemented today (through M4):** Steps 1–6 are fully working. The reporter now generates complete PDF and DOCX reports with embedded evidence screenshots, reproduction packs, and exploit chain analysis. Step 7 is always manual.

### Key Concepts You'll See Throughout

Before we go further, let's define some terms that appear everywhere in the codebase:

- **Program:** A bug bounty program hosted on a platform like HackerOne. For example, "Shopify" runs a bug bounty program on HackerOne where they pay for security vulnerabilities found in their systems.

- **Scope:** The list of domains, URLs, and IP ranges that a program says you're allowed to test. For example, Shopify might say "you can test `*.shopify.com` but NOT `admin.shopify.com`." This is critical — scanning anything outside scope is a violation of the program's rules.

- **Asset:** A live web host discovered during scanning. When we find that `api.shopify.com` is running an HTTP server, that becomes an asset in our database.

- **Endpoint:** A specific URL path on an asset. If `api.shopify.com` has `/api/v1/users` and `/api/v1/orders`, those are two separate endpoints.

- **Finding (or Finding Candidate):** A potential vulnerability discovered by a scanner. At this stage it's unverified — we think we found an XSS, but haven't confirmed it actually works yet.

- **Queue (`scan.jobs`, `report.jobs`, etc.):** Services in AttackBot don't call each other directly for heavy work. Instead, they drop messages onto RabbitMQ queues (think of them as conveyor belts). One service puts a message on the belt, and another service picks it up when it's ready. This means if a service crashes, the message isn't lost — it stays on the belt until someone processes it.

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

The collector authenticates with HackerOne using credentials stored in HashiCorp Vault, then calls their GraphQL API to get:
- Program name, handle, and status (is it currently accepting submissions?)
- Scope list (what domains and assets are in scope)
- Policy details (disclosure timeline, reward structure)

**Code:** `backend/services/scraper/collectors/hackerone.py` → `HackerOneCollector.collect()`.

#### Step 2 — Normalizing the Data

Each platform returns data in its own format. HackerOne's JSON structure is different from BugCrowd's, which is different from Intigriti's. The collector normalizes this into a standard `RawProgram` object with these fields:
- `platform`, `program_handle`, `program_name`, `url`
- `scope` (list of domains/IP ranges/URLs)
- `out_of_scope` (list of what NOT to test)
- `policy` (rewards, rules, disclosure timeline)

**Code:** `backend/services/scraper/models.py` → `RawProgram`, `ProgramScope`, `ProgramPolicy`.

#### Step 3 — Saving to the Database

The normalized data gets saved to three Postgres tables:
- `programs` — one row per program
- `program_scopes` — one row per scope rule (allows for complex multi-entry scopes)
- `program_policies` — one row per program with policy metadata

**Why separate tables?** Because one program can have dozens of scope rules. Storing them in a separate table means you can query "show me all scope rules for this program" without parsing a giant JSON blob.

**Code:** `backend/services/scraper/repository.py` → `save_program()`, `save_program_scope()`.

#### Step 4 — Publishing Scan Jobs

Once a program is saved, the Scraper's job scheduler checks if it's time to scan it. If yes, it publishes a message to the `scan.jobs` RabbitMQ queue. This message contains:
- `program_id` (UUID of the program in our database)
- `scan_id` (UUID for this specific scan run)
- `retry_attempt` (0 for first run, increments on failures)

**Code:** `backend/services/scraper/publisher.py` → `publish_scan_job()`.

---

## 4. Phase 2 — Receiving and Starting the Scan (Core Engine)

**Service:** `core_engine` (port 8002 for API, separate Celery worker)
**What it does:** Receives scan job messages from the queue, fetches program details from the Scraper, and kicks off the vulnerability scanning pipeline.

### Why does this service exist?

The Core Engine is the orchestrator. It's responsible for:
1. Taking the high-level instruction "scan this program"
2. Breaking that down into specific tasks (recon, fingerprinting, scanning, etc.)
3. Running those tasks in order
4. Handling errors and retries
5. Saving all results to the database

It's the "brain" of the scanning operation.

### How it works, step by step

#### Step 1 — The Worker Picks Up the Message

A Celery worker process is always listening on the `scan.jobs` queue. When a message arrives, the worker:
1. Validates the message format
2. Checks if a Redis lock exists for this program (prevents duplicate scans)
3. Creates a lock if none exists
4. Calls the main scan task

**Code:** `backend/services/core_engine/worker.py` → Celery task listener.

#### Step 2 — Fetching Program Details

Before the scan can start, we need to know what to scan. The worker makes an HTTP call to the Scraper's API:
- `GET /api/v1/programs/{program_id}/scope`
- This returns the full scope definition: domains, wildcards, exclusions, etc.

**Why call the Scraper?** The Core Engine doesn't have its own copy of program data. Keeping scope data centralized in the Scraper means only one service needs to stay in sync with HackerOne.

**Code:** `backend/services/core_engine/scan_task.py` → calls Scraper API during setup.

#### Step 3 — Building the Scan Context

The scan context is a big in-memory object that holds:
- Program metadata (name, platform, handle)
- Scope definition (parsed into a queryable `ScopeFilter`)
- Feature flags (which scanning modules are enabled)
- Configuration (rate limits, timeouts, tool paths)

This context gets passed to every pipeline stage. It's the "state" that flows through the entire scan.

**Code:** `backend/services/core_engine/pipeline/context.py` → `ScanContext` class.

#### Step 4 — Creating a Scan Record

Before running any actual scanning, the worker creates a `scans` row in Postgres with status `running`. This gives us an audit trail: even if the scan crashes, we have a record that it was attempted.

**Code:** `backend/services/core_engine/repository.py` → `create_scan()`.

#### Step 5 — Running the Pipeline

Now the actual work begins. The scan task calls each pipeline stage in order:
1. **Stage 0:** Scope filtering (is there anything to scan?)
2. **Stage 1:** Asset discovery (find live hosts)
3. **Stage 2:** Fingerprinting (what tech stack is running?)
4. **Stage 3:** Enumeration (find endpoints and JS files)
5. **Stage 4:** Nuclei scanning (template-based vulnerability tests)
6. **Stage 5:** Custom web vulnerability tests (XSS, CORS, CRLF)
7. **Stage 6:** JavaScript secrets analysis (find hardcoded API keys)
8. **Stage 10:** Aggregation (deduplicate and save findings)

Each stage is isolated — if Stage 3 crashes, Stages 1–2 have already saved their results to the database.

**Code:** `backend/services/core_engine/scan_task.py` → `run_scan_pipeline()`.

---

## 5. Phase 3 — Running the Scanning Pipeline (Stages 0–6, 10)

This is where the actual vulnerability hunting happens. Each stage is a separate Python module that does one specific job.

### Stage 0 — Scope Filter (Safety Check)

**File:** `backend/services/core_engine/pipeline/scope_filter.py`
**Purpose:** Build an in-memory scope checker to ensure we never scan anything outside the program's allowed targets.

**What it does:**
1. Parses the scope rules from the Scraper (e.g., `*.example.com`, `198.51.100.0/24`)
2. Builds a `ScopeFilter` object with methods like `is_in_scope(domain)` and `is_in_scope_ip(ip_address)`
3. Validates that there's at least one in-scope target (if the scope is empty, the scan aborts immediately)

**Why this matters:** Scanning out-of-scope targets is a serious violation of bug bounty program rules and could get you banned. This stage acts as a safety guard before any network traffic happens.

**Example:**
```python
scope_filter = ScopeFilter(in_scope=["*.shopify.com"], out_of_scope=["admin.shopify.com"])
scope_filter.is_in_scope("api.shopify.com")  # True
scope_filter.is_in_scope("admin.shopify.com")  # False (excluded)
scope_filter.is_in_scope("google.com")  # False (not in scope)
```

### Stage 1 — Asset Discovery (Find Live Hosts)

**File:** `backend/services/core_engine/pipeline/asset_discovery.py`
**Purpose:** Find all live web servers within the program's scope.

**What it does (in order):**
1. **Subdomain enumeration (subfinder):** Takes the in-scope domains and finds subdomains. For `*.example.com`, this might discover `api.example.com`, `blog.example.com`, `staging.example.com`, etc.
2. **Domain permutation (alterx):** Generates variations like `api-dev.example.com`, `api-staging.example.com` to catch hosts that subfinder missed.
3. **DNS resolution (dnsx):** Converts all discovered subdomains into IP addresses.
4. **Scope validation:** Checks every discovered host against `ScopeFilter`. Anything out of scope gets dropped.
5. **HTTP probing (httpx):** For each in-scope host, sends HTTP/HTTPS requests to see if there's a web server running.

**What gets saved:** Every live web server becomes an `assets` row in Postgres with:
- `url` (e.g., `https://api.example.com`)
- `ip_address`
- `status_code` (e.g., 200, 403)
- `discovery_method` (e.g., "subfinder+dnsx+httpx")

**Code:** `backend/services/core_engine/pipeline/asset_discovery.py` → `run_asset_discovery()`.

### Stage 2 — Fingerprinting (Identify Technology Stack)

**File:** `backend/services/core_engine/pipeline/fingerprinting.py`
**Purpose:** Figure out what technologies each asset is using.

**What it does:**
1. Runs `httpx` again, this time with technology detection enabled
2. Identifies web servers (nginx, Apache), frameworks (React, Django), CDNs (Cloudflare, Akamai), and WAFs (ModSecurity, Cloudflare WAF)
3. Updates the `assets` rows with `tech_stack` (JSON array like `["nginx", "React", "Cloudflare WAF"]`)

**Why this matters:** Knowing the tech stack helps later stages make smarter decisions. For example, if Cloudflare WAF is detected, we might adjust scan intensity to avoid rate limiting.

**Code:** `backend/services/core_engine/pipeline/fingerprinting.py` → `run_fingerprinting()`.

### Stage 3 — Enumeration (Find Endpoints and JavaScript)

**File:** `backend/services/core_engine/pipeline/enumeration.py`
**Purpose:** Discover specific URL paths and JavaScript files on each asset.

**What it does:**
1. **Directory brute-forcing (ffuf):** Uses a wordlist to guess common paths like `/admin`, `/api/v1/users`, `/config.json`
2. **Wayback Machine lookup (waybackurls):** Queries the Internet Archive for historically known URLs on this domain
3. **JavaScript file discovery:** Finds `.js` files in both ffuf results and Wayback data
4. **JS file download and deduplication:** Downloads each `.js` file, computes its SHA-256 hash, and uploads it to MinIO (S3-compatible storage). If two endpoints serve the same file (same hash), we only store it once.

**What gets saved:**
- `endpoints` table: one row per discovered path (e.g., `/api/v1/users`)
- MinIO bucket `js-files`: deduplicated JavaScript files stored by their hash

**Code:** `backend/services/core_engine/pipeline/enumeration.py` → `run_enumeration()`.

### Stage 4 — Nuclei Scan (Template-Based Vulnerability Tests)

**File:** `backend/services/core_engine/pipeline/nuclei_scan.py`
**Purpose:** Run automated vulnerability tests using Nuclei's template library.

**What Nuclei is:** Nuclei is an open-source tool with thousands of pre-written "templates" that test for known vulnerabilities (like unpatched CVEs, exposed admin panels, misconfigurations). Each template is a YAML file that says "send this HTTP request, and if you get this response, it's vulnerable."

**What this stage does:**
1. Builds a target list (every endpoint discovered in Stage 3)
2. Runs Nuclei with severity filters (by default: critical + high + medium only)
3. Parses Nuclei's JSON output into `FindingCandidate` objects
4. Holds them in memory (they're not saved to the database yet)

**Why not save immediately?** Because findings from multiple stages need to be deduplicated before saving. That happens in Stage 10.

**Code:** `backend/services/core_engine/pipeline/nuclei_scan.py` → `run_nuclei_scan()`.

### Stage 5 — Custom Web Vulnerability Tests

**File:** `backend/services/core_engine/pipeline/web_vuln_tests.py`
**Purpose:** Run custom-built scanners for vulnerabilities that Nuclei doesn't cover well.

**What it tests:**
- **Reflected XSS:** Injects test payloads into query parameters and checks if they appear unescaped in the response
- **CORS misconfigurations:** Sends requests with malicious `Origin` headers and checks if the server allows cross-origin requests
- **CRLF injection:** Tests if the server can be tricked into injecting HTTP headers
- **Sensitive paths:** Checks for exposed files like `.git/config`, `web.config`, `.env`

**Feature flags:** These tests are gated behind feature flags. If `enable_xss_testing` is false, the XSS scanner doesn't run.

**Code:** `backend/services/core_engine/pipeline/web_vuln_tests.py` → `run_web_vuln_tests()`.

### Stage 6 — JavaScript Secrets Analysis

**File:** `backend/services/core_engine/pipeline/js_secrets.py`
**Purpose:** Find hardcoded secrets (API keys, passwords, tokens) in JavaScript files.

**What it does:**
1. Fetches the JS files from MinIO (the ones we uploaded in Stage 3)
2. Uses regex patterns to search for:
   - API keys (AWS, Google Cloud, Stripe, etc.)
   - Private keys (RSA, SSH)
   - Passwords and auth tokens
   - Internal URLs and endpoints
3. Each match becomes a `FindingCandidate` with type `secrets_exposure`

**Code:** `backend/services/core_engine/pipeline/js_secrets.py` → `run_js_secrets_scan()`.

### Stage 10 — Aggregation (Deduplicate and Save)

**File:** `backend/services/core_engine/pipeline/aggregator.py`
**Purpose:** Take all the finding candidates from Stages 4–6, deduplicate them, and save the unique ones to Postgres.

**What it does:**
1. Collects all finding candidates from memory
2. Computes a hash for each finding (based on vulnerability type, URL, and evidence)
3. Removes duplicates (same vulnerability found by multiple scanners)
4. Saves the unique findings to the `findings` table
5. Updates the scan status to `completed`
6. Publishes a message to the `report.jobs` queue

**Why deduplication matters:** If Nuclei and our custom XSS scanner both find the same XSS vulnerability on the same endpoint, we only want to report it once.

**Code:** `backend/services/core_engine/pipeline/aggregator.py` → `run_aggregation()`.

---

## 6. Phase 4 — Browser Session Bootstrap (Stage 3.5)

**Status:** Planned for M5 (not yet implemented)

**Purpose:** Automate login flows to test authenticated parts of web applications.

**Planned behavior:**
- Launch a headless browser (Playwright)
- Navigate to the target login page
- Fill in credentials (from Vault)
- Solve CAPTCHAs (using a CAPTCHA-solving service)
- Save the authenticated session (cookies + local storage) to Postgres, encrypted
- Pass the session to later stages so they can scan authenticated endpoints

**Why this is hard:** Every website has a different login flow. Some use OAuth, some use two-factor auth, some have bot detection. The plan is to support "login recipes" — configuration files that describe how to log in to specific platforms.

---

## 7. Phase 5 — API Fuzzing + Enhanced JS Analysis (Stages 4.5 + 6)

**Status:** Planned for M6 (skeletons exist, full implementation pending)

### Stage 4.5 — API Fuzzing

**Worker:** `api_fuzzer_worker` (listens on `api.fuzz.jobs` queue)
**Purpose:** Test API endpoints with malformed inputs to find parsing errors, injection vulnerabilities, and authentication bypasses.

**Planned behavior:**
- For each discovered API endpoint (identified by patterns like `/api/*` or `Content-Type: application/json`)
- Generate test cases: invalid JSON, SQL injection payloads, oversized inputs, type confusion attacks
- Send requests and analyze responses for errors, stack traces, or unexpected behavior
- Report findings back to the Core Engine

**Why separate worker?** API fuzzing can generate thousands of requests per endpoint. Running it in a separate worker pool prevents it from blocking the main scan pipeline.

### Stage 6 — Enhanced JS Analysis

**Worker:** `js_analysis_worker` (listens on `js.analysis.jobs` queue)
**Purpose:** Deep analysis of JavaScript code beyond simple regex pattern matching.

**Planned enhancements:**
- Parse JS into an AST (Abstract Syntax Tree) to understand code structure
- Find sources (user input points) and sinks (dangerous functions like `eval()`, `innerHTML`)
- Trace data flow to detect potential DOM-based XSS
- Identify client-side encryption/decryption routines
- Extract API endpoint definitions from JS routing libraries

---

## 8. Phase 6 — Behavioral Scenarios (Stage 7)

**Status:** Planned for M9 (skeleton exists)

**Worker:** `scenario_runner` (listens on `scenario.jobs` queue)
**Purpose:** Test complex, multi-step attack scenarios that require state and user interaction.

**Example scenarios:**
- **CSRF chains:** Can an attacker trick a user into deleting their account by visiting a malicious website?
- **Logic flaws:** Can you add items to your cart, delete them, but still get charged for them?
- **Race conditions:** Can two simultaneous requests bypass a "one coupon per user" limit?

**Why this is hard:** These attacks require scripting entire user workflows. The plan is to use Playwright for browser automation and define scenarios as YAML configuration files.

---

## 9. Phase 7 — Exploit Verification (Stage 8)

**Status:** Planned for M7 (skeleton exists)

**Worker:** `exploit_verifier` (listens on `verify.jobs` queue)
**Purpose:** Attempt to actually exploit findings to confirm they're not false positives.

**Planned behavior:**
- For each finding, generate an exploit payload
- Execute the payload in a sandboxed environment
- Check if the exploit succeeded (e.g., for XSS, did the JavaScript actually execute?)
- Upgrade the finding's confidence level from "potential" to "confirmed" if the exploit works

**Why this matters:** Automated scanners have false positive rates. If we can prove a vulnerability is exploitable, it's much more valuable to a bug bounty program.

---

## 10. Phase 8 — AI Hypothesis (Stage 9)

**Status:** Planned for M10 (skeleton exists)

**Worker:** `ai_analysis_worker` (listens on `ai.analysis.jobs` queue)
**Purpose:** Use large language models to generate creative attack hypotheses that traditional scanners miss.

**Planned behavior:**
- Send scan context (tech stack, endpoints, findings so far) to an LLM
- Ask: "What vulnerabilities might exist here that automated tools wouldn't find?"
- Get back hypotheses like "This GraphQL endpoint might have an introspection leak" or "This file upload accepts SVG, which could enable stored XSS"
- Queue those hypotheses for manual or automated testing

**Why this is experimental:** LLMs are non-deterministic and can hallucinate. This is a research feature, not production-critical.

---

## 11. Phase 9 — Aggregation: Cleaning Up and Saving Results (Stage 10)

Already covered in Section 5 (Stage 10). This is the final stage of the core scanning pipeline.

**Key point:** Once aggregation completes, the scan is marked `completed` and a message is published to `report.jobs` queue, triggering the report generation process.

---

## 12. Phase 10 — Report Generation (Reporter)

**Service:** `reporter` (port 8003 for API, separate Celery worker)
**Status:** Fully implemented in M4

**What it does:** Receives scan completion messages, fetches all findings and evidence, generates professional PDF and DOCX reports, uploads them to MinIO, and provides download URLs.

### Why does this service exist?

Bug bounty programs want detailed, well-formatted reports. A raw database dump of findings isn't useful. The Reporter's job is to:
1. Package findings into a readable narrative
2. Include evidence (screenshots, HTTP requests/responses)
3. Provide reproduction steps so researchers can verify the vulnerability
4. Format everything professionally (cover page, table of contents, severity color-coding)

### Architecture

The Reporter has two components:

1. **FastAPI application (main.py):** Provides REST APIs for listing reports, getting report details, and triggering downloads
2. **Celery worker (worker.py):** Consumes `report.jobs` messages and orchestrates the full report generation pipeline

### How report generation works, step by step

#### Step 1 — Message Arrives on `report.jobs` Queue

When the Core Engine completes a scan, it publishes a message to `report.jobs` with:
- `scan_id` (UUID)
- `program_id` (UUID)
- `formats_requested` (list like `["pdf", "docx"]`)
- `include_evidence_screenshots` (boolean)
- `exploit_chains` (optional list of exploit chain references)

**Code:** `backend/services/reporter/worker.py` → Celery task listener.

#### Step 2 — Create Report Record

The worker creates a `reports` row in Postgres with:
- `scan_id`, `program_id`
- `status = "generating"`
- `formats_requested`
- Timestamps for tracking generation time

**Code:** `backend/services/reporter/repository.py` → `create_report()`.

#### Step 3 — Fetch Scan Data

The worker makes HTTP calls to upstream services to gather all necessary data:
- **Core Engine API:** Fetch scan details, findings, assets, endpoints
- **Scraper API:** Fetch program metadata (name, platform, scope)
- **Attack Graph Engine API:** Fetch exploit chain details (if requested)

**Code:** 
- `backend/services/reporter/clients/core_engine.py`
- `backend/services/reporter/clients/scraper.py`
- `backend/services/reporter/clients/attack_graph.py`

#### Step 4 — Build Parsed Scan Object

Raw API payloads are transformed into rich domain objects:
- `ParsedScan` — high-level scan metadata
- `ParsedFinding` — each finding with structured evidence, severity, reproduction steps
- `ProgramInfo` — program name, platform, scope summary
- `EvidenceArtifact` — screenshots and evidence attachments
- `ExploitChain` — multi-step attack chains showing how vulnerabilities can be combined

**Code:** `backend/services/reporter/parsing.py` → `ParsedScanBuilder`.

#### Step 5 — Download Evidence Screenshots

If `include_evidence_screenshots` is true:
1. For each finding with evidence attachments, download screenshot files from MinIO
2. Attach them to the `ParsedFinding` objects
3. Handle missing artifacts gracefully (log warning, continue without that screenshot)

**Code:** `backend/services/reporter/evidence.py` → `download_evidence_for_findings()`.

#### Step 6 — Generate Reproduction Packs

For each finding, the reporter generates reproduction materials:
- **cURL command:** A copy-pasteable command to reproduce the finding
- **Raw HTTP request:** The full HTTP request including headers
- **Browser steps:** Human-readable instructions for manual verification

These are stored in the `reproduction_packs` table and referenced in the report.

**Code:** `backend/services/reporter/reproduction.py` → `generate_reproduction_pack()`.

#### Step 7 — Build Render Plan

The render plan defines the structure of the report:
1. **Cover page:** Report title, program name, scan date, severity summary
2. **Executive summary:** High-level overview of findings
3. **Scope overview:** What was tested (domains, endpoints)
4. **Findings table:** Quick reference table with severity, title, affected URL
5. **Per-finding details:** One section per finding with:
   - Description
   - Severity and CVSS score
   - Affected endpoint
   - Evidence (screenshots if available)
   - Reproduction steps (cURL, raw HTTP, browser steps)
   - Remediation recommendations
6. **Exploit chains section:** How vulnerabilities can be chained together
7. **Reproduction packs appendix:** Full reproduction materials
8. **Evidence notes:** Explanations of evidence collection methodology
9. **Raw HTTP appendix:** Full HTTP request/response dumps

**Code:** `backend/services/reporter/renderers/sections.py` → `build_render_plan()`.

#### Step 8 — Render Reports

For each requested format:

**PDF rendering:**
- Uses ReportLab library
- Creates a cover page with program logo area and metadata
- Generates table of contents with page numbers
- Applies severity color coding (critical=red, high=orange, medium=yellow, low=blue)
- Embeds evidence screenshots as images
- Formats code blocks with monospace font
- Exports to PDF file

**DOCX rendering:**
- Uses python-docx library
- Creates structured headings (Heading 1, Heading 2, etc.)
- Applies severity color to headings
- Embeds evidence images
- Formats reproduction steps in code blocks
- Exports to DOCX file

**Code:**
- `backend/services/reporter/renderers/pdf.py` → `PDFRenderer`
- `backend/services/reporter/renderers/docx.py` → `DOCXRenderer`

#### Step 9 — Upload to MinIO

The generated report files are uploaded to MinIO bucket `reports` with paths like:
- `reports/{scan_id}/report.pdf`
- `reports/{scan_id}/report.docx`

**Code:** `backend/services/reporter/storage.py` → `upload_report_artifact()`.

#### Step 10 — Update Report Status

The `reports` row is updated:
- `status = "completed"` (or `"partial"` if some formats failed, or `"failed"` if all failed)
- `artifact_paths` (JSON mapping format → MinIO path)
- `generated_at` timestamp
- `generation_duration_seconds`

If evidence screenshots were requested but some were missing, status is `"partial"` with `partial_reason = "evidence_missing"`.

**Code:** `backend/services/reporter/repository.py` → `mark_report_completed()`.

#### Step 11 — Publish Completion Event

A message is published to the `reports.completed` queue:
- `report_id`
- `scan_id`
- `program_id`
- `status`
- `formats_available`
- `download_urls` (pre-signed MinIO URLs, valid for 24 hours)

This allows downstream services (like a notification system) to react to report completion.

**Code:** `backend/services/reporter/publisher.py` → `publish_report_generated()`.

### Reporter REST APIs

The Reporter service exposes these endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/reports` | List all reports with pagination and filters |
| GET | `/api/v1/reports/{report_id}` | Get details for a specific report |
| GET | `/api/v1/scans/{scan_id}/reports` | List all reports for a specific scan |
| GET | `/api/v1/reports/{report_id}/download` | Get pre-signed download URLs for report files |
| POST | `/api/v1/reports/generate` | Manually trigger report generation (enqueues to `report.jobs`) |
| GET | `/api/v1/health` | Health check endpoint |

**Code:** `backend/services/reporter/main.py` → FastAPI route definitions.

### Error Handling and Recovery

**Retry logic:** If report generation fails due to transient errors (network timeouts, MinIO unavailable), the Celery task retries with exponential backoff:
- First retry: 60 seconds
- Second retry: 300 seconds (5 minutes)
- Third retry: 600 seconds (10 minutes)
- After exhaustion: message is published to `report.jobs.dlq` (dead letter queue)

**Watchdog:** A background job runs periodically to detect "stuck" reports:
- If a report has been in `status = "generating"` for longer than `watchdog_timeout` (default 30 minutes)
- Mark it as `status = "failed"` with `failure_reason = "watchdog_timeout"`
- This prevents reports from being stuck in "generating" forever if the worker crashes mid-generation

**Code:** `backend/services/reporter/watchdog.py` → `mark_stale_reports_as_failed()`.

### Metrics and Observability

The Reporter exports Prometheus metrics:
- `reporter_generation_duration_seconds` — histogram of report generation times
- `reporter_failures_total` — counter of failed report generations by reason
- `reporter_partial_reports_total` — counter of partial reports by reason
- `reporter_evidence_missing_total` — counter of findings with missing evidence

**Code:** `backend/services/reporter/metrics.py`.

---

## 13. Phase 11 — Manual Submission

**Status:** Always manual (no automation planned)

**Why manual?** Bug bounty programs have strict rules about automated submissions. They want to review each report with a human before it's submitted. Automating submission would:
1. Violate most programs' terms of service
2. Create spam if the system has false positives
3. Remove the human judgment call of "is this worth submitting?"

**How you submit:**
1. Download the generated PDF or DOCX report
2. Review it manually to ensure it's accurate and high-quality
3. Log in to the bug bounty platform (HackerOne, BugCrowd, etc.)
4. Use their web interface to submit the report
5. Attach the PDF/DOCX as supporting documentation

---

## 14. What Happens When Things Go Wrong

AttackBot has comprehensive error handling at every layer.

### Pipeline Stage Errors

**Non-fatal errors (stage continues):**
- Can't download a JavaScript file → log warning, skip that file, continue to next file
- Nuclei finds zero vulnerabilities → not an error, just means this stage produced no findings
- HTTP request times out → log warning, mark that endpoint as unreachable, continue

**Fatal errors (scan aborts):**
- Scope is empty (no in-scope targets) → mark scan `failed_scope`, publish to DLQ
- Aggregation stage crashes → mark scan `failed_internal`, publish to DLQ
- Redis is unreachable → abort scan startup (can't acquire lock)

**Code:** Each pipeline stage has try/except blocks. Errors are logged to `stage_errors` JSON array on the `scans` row.

### Queue Message Errors

If a worker crashes while processing a message:
- RabbitMQ does NOT acknowledge the message
- After a timeout, RabbitMQ re-queues the message
- Another worker picks it up and tries again
- After max retries, the message goes to a dead letter queue (DLQ)

**DLQs exist for:**
- `scan.jobs.dlq`
- `report.jobs.dlq`
- `browser.jobs.dlq`
- `api.fuzz.jobs.dlq`
- `js.analysis.jobs.dlq`
- `scenario.jobs.dlq`
- `verify.jobs.dlq`
- `ai.analysis.jobs.dlq`

**Code:** `backend/shared/queue.py` → DLQ setup in `RabbitMQPublisher`.

### Watchdog Recovery

The Core Engine runs a background watchdog job that checks for scans stuck in `running` status:
- If a scan has been running for > 2 hours → mark it `failed_internal`
- Check if the program has failed < max retries → if yes, publish a new scan job to retry

**Code:** `backend/services/core_engine/watchdog.py` → `scan_watchdog_job()`.

The Reporter also has a watchdog for stuck report generation:
- If a report has been in `generating` status for > 30 minutes → mark it `failed`
- No automatic retry (report generation failures are usually permanent issues like missing scan data)

**Code:** `backend/services/reporter/watchdog.py` → `mark_stale_reports_as_failed()`.

### Database Errors

All database operations use async SQLAlchemy with connection pooling. If a database query fails:
- The worker logs the error
- If it's a transient error (connection timeout), Celery retries the entire task
- If it's a permanent error (constraint violation), the task fails and goes to DLQ

### External Tool Errors

When running external tools (nuclei, httpx, etc.), the system checks exit codes:
- Exit code 0 = success
- Exit code 1 (for nuclei) = "no findings" (not an error)
- Exit code 2 = tool startup failure → log detailed error, raise exception
- Timeout = kill the process, log warning, continue

**Code:** `backend/services/core_engine/subprocess_utils.py` → `run_subprocess_with_timeout()`.

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
  → Reporter worker picks up message
  → Reporter: creates reports row (status = generating)
  → Reporter: fetches scan data from Core Engine, Scraper, Attack Graph Engine
  → Reporter: downloads evidence screenshots from MinIO
  → Reporter: generates reproduction packs → saved to reproduction_packs table
  → Reporter: renders PDF and DOCX files
  → Reporter: uploads reports to MinIO
  → Reporter: updates reports row (status = completed)
  → reports.completed message published to RabbitMQ
```

**What's implemented now vs planned:**

| Data | Where | Implemented? |
|------|-------|-------------|
| Bug bounty programs + scope | Postgres | ✅ M2 |
| Scans + findings + assets + endpoints | Postgres | ✅ M3 |
| JS files (deduplicated by hash) | MinIO | ✅ M3 |
| Distributed locks | Redis | ✅ M2 |
| Reports metadata | Postgres (`reports` table) | ✅ M4 |
| Reproduction packs | Postgres (`reproduction_packs` table) | ✅ M4 |
| Report files (PDF, DOCX) | MinIO | ✅ M4 |
| Evidence screenshots | MinIO | ✅ M4 (partial) |
| Browser sessions (encrypted) | Postgres | 🔲 M5 |
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
| Watchdog checks (scan) | Scan running > 2 hours? | Mark `failed_internal`, retry if under retry cap |
| Watchdog checks (report) | Report generating > 30 minutes? | Mark `failed`, no automatic retry |
| Reporter receives message | Validation fails? | Log error, acknowledge message (don't crash worker) |
| Report generation | Evidence screenshot missing? | Mark report `partial` with reason `evidence_missing`, continue |
| Report generation | All formats fail to render? | Mark report `failed`, publish to DLQ |
| Report generation | Some formats succeed? | Mark report `partial`, save successful formats |

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
| `schemas/report_jobs.py` | Data models for `report.jobs` queue messages (includes formats, evidence flags, exploit chains) |
| `schemas/reports_completed.py` | Data models for `reports.completed` queue messages |

### API Gateway (`backend/services/api_gateway/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application on port 8000 — health check endpoint that probes all backend services (scraper, core-engine, reporter, attack-graph-engine) |

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
| `models.py` | Data classes: `RawProgram`, `ProgramScope`, `ProgramPolicy`, `Program` |
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
| `main.py` | FastAPI app with full REST APIs: list reports, get report details, download reports, trigger generation |
| `worker.py` | Celery worker that consumes `report.jobs` messages and orchestrates full report generation pipeline |
| `report_task.py` | Full async pipeline: fetch scan data, build parsed scan, render artifacts, upload to MinIO, publish completion events |
| `repository.py` | Full CRUD for `reports` and `reproduction_packs` tables (create, mark_generating, mark_completed, mark_partial, mark_failed, list, get, stale detection) |
| `models.py` | Rich domain models: `ParsedScan`, `ParsedFinding`, `ProgramInfo`, `ScopeEntry`, `EvidenceArtifact`, `ExploitChain`, `ReproductionPackDraft` |
| `parsing.py` | `ParsedScanBuilder` — transforms raw API payloads into structured report domain objects |
| `evidence.py` | Downloads evidence screenshots from MinIO, attaches to findings, handles missing artifacts gracefully |
| `reproduction.py` | Generates reproduction packs per finding: curl commands, raw HTTP requests, browser steps |
| `publisher.py` | Publishes `report.generated` events to `reports.completed` queue |
| `storage.py` | MinIO upload/download for report artifacts and evidence |
| `watchdog.py` | Marks stale generating reports as failed (watchdog_timeout) |
| `config.py` | Full config: upstream URLs, evidence concurrency, retry backoff, temp dirs, presign expiry |
| `metrics.py` | Prometheus metrics for generation duration, failures, partial reasons, evidence missing |
| `clients/core_engine.py` | HTTP client to fetch scan details and findings |
| `clients/scraper.py` | HTTP client to fetch program metadata and scope |
| `clients/attack_graph.py` | HTTP client to fetch exploit chain details |
| `renderers/base.py` | Base data classes (`RenderPlan`, `EvidenceImageEntry`) |
| `renderers/theme.py` | Severity color mapping for reports |
| `renderers/sections.py` | Shared render plan builder — executive summary, scope overview, findings table, per-finding detail, exploit chains section, reproduction packs appendix, evidence notes, raw HTTP appendix |
| `renderers/pdf.py` | Working PDF renderer using ReportLab — cover page, headings, severity-colored findings, embedded evidence screenshots |
| `renderers/docx.py` | Working DOCX renderer using python-docx — headings, findings, embedded evidence images |

### Attack Graph Engine (`backend/services/attack_graph_engine/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application on port 8006 with Neo4j config — M1 skeleton (health endpoint only, graph operations planned for M8) |

### Browser Worker (`backend/services/browser_worker/`)

| File | Purpose |
|------|---------|
| `worker.py` | Celery worker on `browser.jobs` queue — M1 skeleton (planned for M5) |

### API Fuzzer Worker (`backend/services/api_fuzzer_worker/`)

| File | Purpose |
|------|---------|
| `worker.py` | Celery worker on `api.fuzz.jobs` queue — M1 skeleton (planned for M6) |

### JS Analysis Worker (`backend/services/js_analysis_worker/`)

| File | Purpose |
|------|---------|
| `worker.py` | Celery worker on `js.analysis.jobs` queue — M1 skeleton (planned for M6) |

### Scenario Runner (`backend/services/scenario_runner/`)

| File | Purpose |
|------|---------|
| `worker.py` | Celery worker on `scenario.jobs` queue — M1 skeleton (planned for M9) |

### Exploit Verifier (`backend/services/exploit_verifier/`)

| File | Purpose |
|------|---------|
| `worker.py` | Celery worker on `verify.jobs` queue — M1 skeleton (planned for M7) |

### AI Analysis Worker (`backend/services/ai_analysis_worker/`)

| File | Purpose |
|------|---------|
| `worker.py` | Celery worker on `ai.analysis.jobs` queue — M1 skeleton (planned for M10) |

---

## Queue Reference

**Implemented and Active:**
- `scan.jobs` / `scan.jobs.dlq` — consumed by `core_engine` worker
- `report.jobs` / `report.jobs.dlq` — consumed by `reporter` worker
- `reports.completed` (no DLQ) — publish-only queue for downstream notification

**Implemented as Skeletons (consumers exist but don't do real work yet):**
- `browser.jobs` / `browser.jobs.dlq` — will be consumed by `browser_worker` (M5)
- `api.fuzz.jobs` / `api.fuzz.jobs.dlq` — will be consumed by `api_fuzzer_worker` (M6)
- `js.analysis.jobs` / `js.analysis.jobs.dlq` — will be consumed by `js_analysis_worker` (M6)
- `scenario.jobs` / `scenario.jobs.dlq` — will be consumed by `scenario_runner` (M9)
- `verify.jobs` / `verify.jobs.dlq` — will be consumed by `exploit_verifier` (M7)
- `ai.analysis.jobs` / `ai.analysis.jobs.dlq` — will be consumed by `ai_analysis_worker` (M10)

**Code:** `backend/shared/queue.py` — defines all queue names and DLQ setup.

---

## Infrastructure and Observability

**Status:** Fully deployed in M1

AttackBot includes a complete observability stack defined in `infra/docker-compose.yml`:

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Primary data store |
| RabbitMQ | 5672, 15672 | Message queue + management UI |
| Redis | 6379 | Distributed locks and caching |
| MinIO | 9000, 9001 | Object storage (S3-compatible) |
| Neo4j | 7474, 7687 | Graph database for attack chains (M8) |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Metrics visualization and dashboards |
| Loki | 3100 | Log aggregation |
| Tempo | 3200 | Distributed tracing |

**How they connect:**
- All services export Prometheus metrics
- Logs are sent to Loki in JSON format
- Traces use OpenTelemetry standard and are collected by Tempo
- Grafana provides unified dashboards combining metrics, logs, and traces

---

## Database Migrations Reference

| Migration | Tables Created | Purpose |
|-----------|---------------|---------|
| `001_programs.py` | `programs`, `program_scopes`, `program_policies` | Store bug bounty program metadata (M2) |
| `002_scans.py` | `scans`, `findings`, `assets`, `endpoints` | Store scan results and discoveries (M3) |
| `003_browser_sessions.py` | `browser_sessions` | Store encrypted authenticated sessions (M5, planned) |
| `004_reporter.py` | `reports`, `reproduction_packs` | Store report generation metadata and reproduction materials (M4) |

---

**End of Document**