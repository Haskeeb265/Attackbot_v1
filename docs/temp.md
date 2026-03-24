# AttackBot V1 — Engineering Session Context

**Project path:** `C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1`
**Session span:** Multi-day debugging, architecture, and E2E validation session
**Document purpose:** Comprehensive record of what was built, what broke, what was fixed, and what is currently in progress

---

## 1. Project Overview

AttackBot is an automated security scanner that ingests bug bounty programmes from HackerOne, scans them through a multi-stage pipeline, and produces structured vulnerability reports.

### Stack

| Layer | Technology |
|---|---|
| Orchestration | Docker Compose |
| API services | FastAPI (Python) |
| Task workers | Celery |
| Message broker | RabbitMQ |
| Database | PostgreSQL 16 |
| Cache / locks | Redis |
| Object storage | MinIO |
| Graph database | Neo4j |
| Secrets | HashiCorp Vault |
| Observability | Loki, Tempo, Prometheus, Grafana |

### Services

| Service | Port | Role |
|---|---|---|
| `scraper` | 8001 | HackerOne programme sync, scope management, reconciler |
| `core-engine` | 8002 | Scan orchestration API, watchdog scheduler |
| `core-worker` | — | Celery worker, executes scan pipeline stages 1–10 |
| `reporter` | 8003 | Report service API |
| `reporter-worker` | — | Celery worker, consumes `report.jobs` |
| `api-gateway` | 8000 | Gateway (persistent unhealthy healthcheck — known issue) |
| `tempo` | — | Distributed tracing — crash-looping throughout (known issue) |

### Scan Pipeline Stages

| Stage | Name | Description |
|---|---|---|
| 0 | Scope validation | Build `ScopeFilter`, fatal if empty |
| 1 | Asset discovery | Seed domains → subfinder → alterx → dnsx → httpx |
| 2 | Fingerprinting | Enrich assets with tech stack and WAF info |
| 3 | Enumeration | ffuf directory brute-force, waybackurls, JS download |
| 4 | Nuclei scan | Unauthenticated template scanning |
| 5–10 | Later stages | Browser, API fuzzing, scenario runner, AI analysis, verification |

---

## 2. Where We Started

The session began with a failing E2E test (`tests/integrations/test_e2e_system_trace.py`) that produced a report at `E2E_SYSTEM_FINDINGS.md`. The first run revealed several interconnected bugs that made every scan either silent or incomplete.

The E2E test was designed to:
1. Bring up the full Docker Compose stack
2. Trigger a HackerOne scrape to populate the programme inventory
3. Select a programme and trigger a scan via `core-engine`
4. Poll for scan completion and collect a structured findings report

---

## 3. Bugs Found and Fixed (Chronological)

### Bug 1 — Queue Flooding on Startup

**Symptom:** Run 2 showed `scan.jobs: 1611 messages` immediately after stack startup.

**Root cause:** The scraper published raw AMQP `program.scraped` envelopes to `scan.jobs` for all ~180 eligible programmes during its initial HackerOne sync. This flooded the queue before any E2E scan could get a worker turn.

**Fix:** Decoupled metadata sync from job publishing entirely. Introduced a `Reconciler` class on a 5-minute APScheduler interval and a separate `scan_publish_batch` scheduler job. Targeted scans now bypass the scheduler entirely. The scraper's sync path sets `published: 0` and never touches `scan.jobs`.

**Files changed:** `publisher.py`, `reconciler.py`, `main.py` (scraper), `test_scraper.py`

**Evidence:** Run 3 — `scan.jobs: 2 messages` vs Run 2 — `scan.jobs: 1611 messages`

---

### Bug 2 — Reporter Worker Silent Message Drop

**Symptom:** Scans completed but no report processing occurred. RabbitMQ logs showed "Received and deleted unknown message. Wrong destination?!?"

**Root cause:** The `reporter-worker` had no registered handler for messages arriving on `report.jobs`. Celery silently ACKed and discarded them.

**Fix:** Registered a Kombu raw consumer (`ReportJobsConsumerStep`) on `report.jobs`. Handler deserialises the `MessageEnvelope`, validates event type and schema version, logs structured events: `report_job_received`, `report_job_formats_requested`, `report_generation_not_yet_implemented`.

**Evidence:** Run 3+ — three structured log lines per completed scan, no wrong-destination warnings.

---

### Bug 3 — Scraper→core-worker Message Format Mismatch

**Symptom:** After Bug 1 fix, messages were being published to `scan.jobs` but the core-worker silently dropped them.

**Root cause:** The scraper's `Reconciler` was publishing raw AMQP envelopes directly to `scan.jobs`. The `core-worker` expects Celery task frames (with task name `core_engine.scan_task`). Raw envelopes triggered "wrong destination" and were discarded.

**Fix:** Changed `publisher.py` to use `Celery.send_task('core_engine.scan_task', ...)` instead of raw AMQP publish. The `ScraperPublisher` now holds a Celery dispatcher instance constructed from `rabbitmq_url`.

**Evidence:** Run 5 — no "wrong destination" warnings; clean scan lifecycle confirmed.

---

### Bug 4 — Stage 1 Seed-Asset Gap (False Empty Scans)

**Symptom:** Weblate scans (scope: `hosted.weblate.org` domain + 5 GitHub URLs) produced `assets_count: 0` and skipped stages 2–10 entirely.

**Root cause:** Stage 1 treated "no subfinder discoveries" as "no targets". When subfinder returned nothing for `hosted.weblate.org`, the pipeline skipped all subsequent stages — even though the seed domain itself was a valid HTTP target. The 5 GitHub URLs were being incorrectly admitted as seeds, causing GitHub's servers to be probed out-of-scope.

**Fix:** V3 seed-first Stage 1 rewrite:
- Domain and wildcard_domain rules are always seed candidates
- URL rules are seeds only if HTTP(S) AND the hostname is domain-led by in-scope domain/wildcard rules (domain-led URL policy)
- `mobile_app`, `api`, `ip_range` are excluded from web probing with logged counts
- Per-domain: run subfinder → skip alterx only for that domain if subfinder empty → always continue dnsx/httpx against the seed domain itself
- Post-httpx deduplication by canonical origin key `{scheme}://{lower(host)}:{effective_port}`

Also introduced `scope_filter.py`'s `is_host_in_domain_scope()` helper, reused for URL seed admission.

**Evidence:** Run 9 — `seed_domains=1, assets_found=1`, Stage 2 fingerprinting completed, `assets_count: 2`. Weblate's 5 GitHub URLs logged as `url_host_not_domain_led: 5` — correctly excluded.

---

## 4. Code Review Passes and Fixes Applied

After the initial bug fixes, a systematic review pass was conducted across the pipeline files. The following issues were identified and fixed:

### Blocking items (fixed before next E2E run)

| Item | File | Issue | Fix |
|---|---|---|---|
| Silent timeout scaling failure | `core_engine/main.py` | `_enqueue_scan` used fragile `callable()` guard that could silently fail | Direct method call with explicit skip diagnostic log |
| DLQ routing gap | `shared/queue.py` | Main queues declared without `x-dead-letter-exchange` args — DLQs existed but were never populated by real dead letters | Added DLQ routing arguments with safe fallback logging for pre-existing queue argument conflicts |
| Nuclei exit-code extraction | `nuclei_scan.py` | `_extract_return_code` only handled `ScanError` — non-ScanError exceptions (TimeoutError, etc.) returned `None` | Added `returncode`/`exit_code`/`code` attribute inspection plus regex fallback |
| Wildcard matching edge case | `scope_filter.py` | `wildcard_domain` entries without `*.` prefix fell through to root-domain matching, granting broader access than intended | Explicit `asset_type == "wildcard_domain"` check independent of prefix |
| Reconciler log parity | `reconciler.py` | `reconciler_finished` log missing `checked` field | Added `checked=len(queued)` |
| Celery compat path visibility | `reporter/worker.py` | Compatibility Celery task had no signal if accidentally invoked | Added `invocation_source: "celery_compat"` warning log |
| Publisher mock safety | `scraper/publisher.py` | `_scan_timeout_seconds` lookup could fail in test/mock construction | Added safe fallback |

### Non-blocking cleanup (completed in subsequent pass)

| Item | Files | Change |
|---|---|---|
| `scaled_timeout` deduplication | `shared/config.py` | Moved `scaled_timeout` and `scaled_scan_timeout_seconds` from `EngineConfig` and `ScraperConfig` into `BaseServiceConfig` — single implementation, inherited by all services |
| Fingerprint URL normalisation | `fingerprinting.py` | Lookup now normalises keys (trailing slash strip, lowercase host) and indexes by both httpx `input` and `url` fields — fixes redirect chain misses |
| Unified WAF keyword list | `waf_utils.py`, `asset_discovery.py`, `fingerprinting.py` | Extracted shared WAF keyword constant; Stage 1 and Stage 2 now reference the same list including `cloudflare`, `akamai`, `waf`, `f5`, `sucuri`, `imperva`, `barracuda`, `fortiweb` |
| Reporter compat counter | `reporter/worker.py` | `invocation_source: "celery_compat"` structured field for grep-ability |

---

## 5. Architecture Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| URL scope admission policy | Domain-led URLs only | Prevents scanning third-party hosts (e.g. GitHub); extracts hostname and checks against in-scope domain/wildcard rules |
| Nuclei failure guard mode | Warn and continue | Partial scan > no scan; worker stays up, stage marked failed honestly |
| Alterx skip policy | Skip only for domains with empty subfinder results | Multi-domain scopes: domains with results run full path; empty ones skip alterx but still run dnsx/httpx |
| Dedup key format | `scheme + lower(host) + effective_port` | Standard ports normalised (80/http, 443/https omitted); http and https treated as distinct |
| Merge rule for duplicates | First-seen wins all fields | Deterministic; later entries only backfill null/missing fields |
| Reconciler pause | Flag-based at construction time (`paused=True`) | Pause state set once at startup; no runtime coordination needed |
| Background publish decoupling | Separate `scan_publish_batch` scheduler job | Reconciler handles failure-retry; publish batch handles due-for-rescan scheduling; scraper sync handles metadata only |

---

## 6. E2E Test Infrastructure

### Programme pinning

The E2E test supports programme pinning to avoid non-deterministic programme selection:

| Env var | Purpose |
|---|---|
| `E2E_PINNED_PROGRAM_HANDLE` | Pin by HackerOne handle (e.g. `weblate`) |
| `E2E_PINNED_PROGRAM_ID` | Pin by internal UUID |

Eligibility checks (active, non-empty in-scope) are still enforced even when pinned.

### E2E control flags

| Env var | Default | Effect |
|---|---|---|
| `E2E_PAUSE_RECONCILER` | `false` | Pauses the Reconciler and `scan_publish_batch` scheduler to prevent background scan contention |
| `E2E_ENFORCE_QUEUE_BASELINE` | `false` | Waits for `scan.jobs` to reach 0 ready messages before triggering target scan |
| `E2E_QUEUE_PURGE_BEFORE_BASELINE` | `false` | Actively purges `scan.jobs` via RabbitMQ management API before baseline wait |
| `E2E_TOOL_TIMEOUT_SCALE` | `1.0` | Multiplier applied to all per-tool timeouts for faster E2E runs (e.g. `0.3`) |
| `E2E_TOOL_TIMEOUT_FLOOR_SECONDS` | `30` | Minimum timeout after scaling — prevents over-aggressive truncation |

### Pinned test targets

| Handle | ID | Scope | Notes |
|---|---|---|---|
| `codeigniter` | `0f488d5a-...` | `www.codeigniter.com` (domain) | Shallow scope, completes in ~8–13 min; baseline target |
| `weblate` | `2715b22b-...` | `hosted.weblate.org` (domain) + 5 GitHub URLs (excluded) | V3 validation target; confirmed seed-first works |

---

## 7. E2E Run History

| Run | Target | Outcome | Key Signal |
|---|---|---|---|
| 1 | Seeded/example.com | Completed (shallow) | dnsx timeout on example.com; nuclei exit code 2 |
| 2 | Live (no pin) | Timeout | `scan.jobs: 1611 messages`; scan ID never captured |
| 3 | Live (Costco) | Timeout (running) | Bug 1 + 2 fixed; scan got ID and ran |
| 4 | Live (CodeIgniter pin) | Completed | Bug 1 + 2 confirmed; format mismatch (Bug 3) visible |
| 5 | Live (CodeIgniter pin) | Completed | Bug 3 fixed; clean run |
| 6 | Live (Weblate, no pin) | Completed | V3 not in image; `assets_count=0`; stages 2–6 skipped |
| 7 | Live (Weblate, pinned) | Timeout | V3 not in image (stale build); scan running but no seed fix |
| 8 | Live (CodeIgniter pin) | Completed | V3 confirmed in image; clean baseline |
| 9 | Live (Weblate, pinned) | Timeout | V3 working: `seed_domains=1, assets_found=1`, Stage 2 completed; timeout from ffuf + background Reconciler contention |
| 10 | Live (Weblate, pinned) | Failed — queue baseline not reached | `scan.jobs: 47 ready` — Reconciler pause env var not reaching scraper container |
| 11 | Live (Weblate, pinned) | Timeout — scan never appeared in DB | Purge worked, baseline reached, scan queued; but `scraper-1 Running` (not Recreated) — `E2E_PAUSE_RECONCILER` still not injected into container |

---

## 8. Current Blocker

### What is happening

The `E2E_PAUSE_RECONCILER=true` environment variable is set in the host shell before running the E2E test, but the scraper container is not being recreated with this value. In the `docker compose up -d` output, `attackbot-scraper-1` shows `Running` rather than `Recreated`. This means the scraper inside the container has `e2e_pause_reconciler=False` and its scheduled jobs — `Reconciler.reconcile()` every 5 minutes and `scan_publish_batch` every 60 minutes — continue publishing background scan jobs throughout the test window.

The evidence: during Run 11, a Vueling scan (`program_id: 61230f7b`) completed at `09:43:49` and triggered a `report_job_received` log — a background scan that should never have been running during the E2E window. The Weblate scan was queued behind at least 8 other jobs that accumulated during the 2400-second test window and never got a worker turn.

### Root cause

The E2E environment variables (`E2E_PAUSE_RECONCILER`, `E2E_TOOL_TIMEOUT_SCALE`, `E2E_TOOL_TIMEOUT_FLOOR_SECONDS`) were added to the application configs and the application logic respects them, but they were **never declared as passthrough entries in `infra/docker-compose.yml`**. Docker Compose does not automatically pass host environment variables into containers — they must be explicitly declared in the service's `environment` block.

### The fix (pending implementation)

Add the following to `infra/docker-compose.yml`:

```yaml
scraper:
  environment:
    - E2E_PAUSE_RECONCILER=${E2E_PAUSE_RECONCILER:-false}
    - E2E_TOOL_TIMEOUT_SCALE=${E2E_TOOL_TIMEOUT_SCALE:-1.0}
    - E2E_TOOL_TIMEOUT_FLOOR_SECONDS=${E2E_TOOL_TIMEOUT_FLOOR_SECONDS:-30}

core-worker:
  environment:
    - E2E_TOOL_TIMEOUT_SCALE=${E2E_TOOL_TIMEOUT_SCALE:-1.0}
    - E2E_TOOL_TIMEOUT_FLOOR_SECONDS=${E2E_TOOL_TIMEOUT_FLOOR_SECONDS:-30}
```

The `${VAR:-default}` syntax means production deployments where these vars are absent get the safe defaults (`pause=false`, `scale=1.0`). When the vars are present in the host environment, Docker Compose detects the change and recreates the affected containers — the `docker compose up -d` output should show `scraper-1 Recreated` and `core-worker-1 Recreated` when the fix is applied.

### Verification signal

After applying the fix, re-run with:

```powershell
$env:E2E_PINNED_PROGRAM_HANDLE='weblate'
$env:E2E_PINNED_PROGRAM_ID='2715b22b-3506-4fb1-bece-95cad2eec341'
$env:E2E_PAUSE_RECONCILER='true'
$env:E2E_ENFORCE_QUEUE_BASELINE='true'
$env:E2E_QUEUE_PURGE_BEFORE_BASELINE='true'
$env:E2E_TOOL_TIMEOUT_SCALE='0.3'
python -m pytest tests/integrations/test_e2e_system_trace.py -q
```

Confirm in the report:
- `docker compose up -d` output shows `scraper-1 Recreated` and `core-worker-1 Recreated`
- Scraper logs at startup show `e2e_reconciler_pause_enabled` log event
- Queue baseline reaches 0 immediately after purge
- No background scans accumulate in `scan.jobs` during the test window
- Weblate scan row appears in DB within ~60–120 seconds of trigger
- Stage timeline shows `asset_discovery`, `fingerprinting`, at minimum

---

## 9. Persistent Known Issues (Not Yet Fixed)

| Issue | Status | Notes |
|---|---|---|
| `api-gateway` unhealthy in `docker ps` | Open | Docker Compose healthcheck misconfiguration; service returns 200 on health endpoint but Docker marks it unhealthy |
| `tempo` crash-looping (`Restarting (1)`) | Open | Distributed tracing broken; all other services unaffected |
| `core-engine` `/metrics` returns 404 | Open | Prometheus scraping broken for core-engine |
| `scraper` `/scrape/trigger` ReadTimeout | Open | Occurs occasionally during E2E when lock is held; tracked as separate follow-up |
| `report_generation_not_yet_implemented` | Expected | Reporter worker stub; `reports.completed` queue exists, 0 consumers — next milestone work |
| E2E timeout too tight for ffuf | Open | ffuf at default 1800s timeout consumes most of E2E window; `E2E_TOOL_TIMEOUT_SCALE=0.3` is the mitigation |
| `reporter` and `attack-graph-engine` health probe failures | Open | Both return `status_code=None` during E2E health checks; services appear healthy in `docker ps` |

---

## 10. Queue Topology Reference

All queues are durable with DLQ pairs. Healthy baseline state is 0 messages, 1 consumer on primary queues, 0 consumers on DLQs.

| Queue | DLQ | Expected Consumers |
|---|---|---|
| `scan.jobs` | `scan.jobs.dlq` | 1 (core-worker) |
| `browser.jobs` | `browser.jobs.dlq` | 1 (browser-worker) |
| `api.fuzz.jobs` | `api.fuzz.jobs.dlq` | 1 (api-fuzzer-worker) |
| `js.analysis.jobs` | `js.analysis.jobs.dlq` | 1 (js-analysis-worker) |
| `scenario.jobs` | `scenario.jobs.dlq` | 1 (scenario-runner) |
| `verify.jobs` | `verify.jobs.dlq` | 1 (exploit-verifier) |
| `ai.analysis.jobs` | `ai.analysis.jobs.dlq` | 1 (ai-analysis-worker) |
| `report.jobs` | `report.jobs.dlq` | 1 (reporter-worker Kombu consumer) |
| `reports.completed` | none | 0 (not yet implemented) |

---

## 11. Unit Test Coverage Added This Session

| Test file | What it covers |
|---|---|
| `tests/unit/test_scraper.py` | 52 tests — scraper logic, reconciler, publisher, scope parsing |
| `tests/unit/test_scraper_scan_publish_flow.py` | 2 tests — Reconciler pause behaviour, publish batch gating |
| `tests/unit/test_engine.py` | Stage 1 seed-first behaviour, nuclei diagnostics (exit code 2 for non-ScanError), fingerprint URL normalisation, shared WAF keyword detection |
| `tests/unit/test_shared.py` | `BaseServiceConfig` scaling — floor enforcement, scale guard |
| `tests/unit/test_reporter_worker.py` | Reporter worker envelope handling, Celery compat path `invocation_source` logging |

---

## 12. Toolchain Timeouts Reference

Production values (scale=1.0). All subject to `scaled_timeout()` in `BaseServiceConfig`.

| Tool | Default timeout | Notes |
|---|---|---|
| subfinder | 600s | 5 min; was 1800s — reduced for testing |
| alterx | 300s | Skipped if subfinder returns empty for that domain |
| dnsx | 900s | Can hit limit on large alterx candidate sets |
| httpx | 600s | Used in Stage 1 (discovery) and Stage 2 (fingerprinting) |
| ffuf | 1800s | Largest single-tool consumer of E2E window |
| nuclei | 3600s | 1 hour; exit code 2 = startup failure (templates/target issue) |
| waybackurls | 300s | Non-fatal if tool not installed |
| JS download | 30s | Per-file; best-effort, non-fatal |
| Scan-level watchdog | 2h threshold | `recover_stuck_scans` fires every 5 min |

---

## 13. Next Steps (After Current Blocker is Resolved)

1. Apply `docker-compose.yml` env var passthrough fix
2. Run E2E — confirm `scraper-1 Recreated`, pause active, Weblate scan completes
3. Collect per-tool elapsed times from the successful run to begin timeout calibration
4. Switch target to CodeIgniter for a fast deterministic baseline after Weblate validates
5. Implement report generation (move `report_generation_not_yet_implemented` stub to actual output)
6. Address `api-gateway` healthcheck misconfiguration
7. Fix `tempo` crash-loop (distributed tracing)
8. Add `E2E_TOOL_TIMEOUT_SCALE` and `E2E_PAUSE_RECONCILER` to CI environment if running automated E2E