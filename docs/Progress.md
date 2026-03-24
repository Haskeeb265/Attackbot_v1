# AttackBot — Project Progress

> Last updated: 2026-03-24
> Current state: **M3 complete and in repo. M4+ remains planned. Reporter worker validates `report.jobs` messages but report generation is not yet implemented.**
> Test inventory (repo): **unit: 161 (test_engine: 65, test_scraper: 52, test_shared: 35, test_reporter_worker: 5, test_scraper_scan_publish_flow: 4); integration: 29 (test_e2e_system_trace, test_m3_verification, test_scraper_pipeline, test_engine_pipeline, test_infra_startup).** Skips require `INTEGRATION_TARGET`, `DATABASE_URL`, and/or `HACKERONE_API_USERNAME`/`HACKERONE_API_TOKEN`.

---

## Milestone Status

| # | Name | Status | Completed |
|---|------|--------|-----------|
| M1 | Solid Ground | ✅ Complete | 2026-03-10 |
| M2 | Eyes Open | ✅ Complete | 2026-03-11 |
| M3 | First Strike | ✅ Complete | 2026-03-18 |
| M4 | Read the Room | 🔲 Not started | — |
| M5 | Get Inside | 🔲 Not started | — |
| M6 | Break the Logic | 🔲 Not started | — |
| M7 | Prove It | 🔲 Not started | — |
| M8 | Connect the Dots | 🔲 Not started | — |
| M9 | Think Harder | 🔲 Not started | — |
| M10 | The Machine | 🔲 Not started | — |

---

## M1 — Solid Ground ✅

**Purpose:** Project foundation, infrastructure, conventions, service skeletons.
**Outcome:** Infra compose defines 26 services with phased startup, healthchecks, named volumes, and resource limits.

### Infrastructure
- [x] `infra/docker-compose.yml` — 6-phase startup order, all healthchecks, named volumes, resource limits
- [x] `infra/prometheus/prometheus.yml` — scrape config for all service `/metrics` endpoints
- [x] `infra/grafana/provisioning/datasources/datasources.yml` — Prometheus + Loki + Tempo wired
- [x] `infra/grafana/provisioning/dashboards/dashboards.yml` — dashboard provider config
- [x] `infra/grafana/provisioning/dashboards/services_alive.json` — all-services health dashboard
- [x] `infra/loki/loki-config.yml` — log aggregation config
- [x] `infra/README.md` — bootstrap sequence, known constraints documented

### Shared Library (`backend/shared/`)
- [x] `config.py` — `BaseServiceConfig(BaseSettings)` — all services inherit this
- [x] `logging.py` — structlog JSON logger, `configure_logging()` + `get_logger()`
- [x] `db.py` — SQLAlchemy async engine factory, `init_db()`, `get_session()`, `check_db_health()`
- [x] `health.py` — `HealthResponse`, `ComponentHealth`, `HealthStatus` enum
- [x] `exceptions.py` — full exception hierarchy rooted at `AttackBotError`
- [x] `queue.py` — `Queues` constants, `QueuePublisher` with passive declare + publish
- [x] `vault.py` — `init_vault()`, `get_secret()`, `put_secret()` via hvac KV v2
- [x] `storage.py` — `init_storage()`, `upload_bytes()`, `download_bytes()`, `get_presigned_url()`
- [x] `schemas/envelope.py` — `MessageEnvelope`, `build_envelope()` factory
- [x] `schemas/scan_jobs.py` — `ScanJobsPayload`, `FeatureFlags`, `ScopeDefinition`, `build_scan_job_message()`
- [x] `schemas/report_jobs.py` — `ReportJobsPayload`, `SeverityBreakdown`, `build_report_job_message()`

### Database Migrations (`backend/migrations/`)
- [x] `alembic.ini` — Alembic config
- [x] `env.py` — async-aware, loads `DATABASE_URL` from environment
- [x] `script.py.mako` — migration file template
- [x] `versions/001_initial_schema.py` — `programs` + `scans` tables (proof of life)

### FastAPI Services (initial skeletons; some now implemented)
- [x] `backend/services/scraper/` — port 8001, `/api/v1/health` returning healthy ✅
- [x] `backend/services/core_engine/` — port 8002, `/api/v1/health` returning healthy ✅
- [x] `backend/services/reporter/` — port 8003, `/api/v1/health` returning healthy ✅
- [x] `backend/services/attack_graph_engine/` — port 8006, `/api/v1/health` returning healthy ✅
- [x] `backend/services/api_gateway/` — port 8000, `/api/v1/health` returning healthy ✅

### Celery Workers (initial skeletons; core-engine and reporter now implemented)
Note: `backend/services/core_engine/worker.py` is fully implemented. `backend/services/reporter/worker.py` validates and logs `report.jobs` messages but does not yet generate reports. Others remain boundary validators/skeletons until their milestones.
- [x] `backend/services/core_engine/worker.py` — consumes `scan.jobs` ✅ fully implemented
- [x] `backend/services/reporter/worker.py` — consumes `report.jobs` (validates + logs, generation stub)
- [x] `backend/services/browser_worker/worker.py` — consumes `browser.jobs` (skeleton)
- [x] `backend/services/api_fuzzer_worker/worker.py` — consumes `api.fuzz.jobs` (skeleton)
- [x] `backend/services/js_analysis_worker/worker.py` — consumes `js.analysis.jobs` (skeleton)
- [x] `backend/services/scenario_runner/worker.py` — consumes `scenario.jobs` (skeleton)
- [x] `backend/services/exploit_verifier/worker.py` — consumes `verify.jobs` (skeleton)
- [x] `backend/services/ai_analysis_worker/worker.py` — consumes `ai.analysis.jobs` (skeleton)

### Tests
- [x] `tests/unit/test_shared.py` — 35 tests (exceptions, health, envelope, scan_jobs, report_jobs)
- [x] `tests/integrations/test_infra_startup.py` — 4 tests (DB health, query execution, programs table, scans table)
- [x] `tests/conftest.py` — singleton reset fixture

### CI
- [x] `.github/workflows/ci.yml` — lint (ruff), typecheck (mypy), test (pytest), docker build

### Bugs Fixed During M1
| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `attack-graph-engine` crash | `structlog.stdlib.add_logger_name` incompatible with `PrintLogger` | Removed from processor chain in `shared/logging.py` |
| `scraper` crash loop | Stale Docker image from pre-M1 code expecting `S3_ACCESS_KEY` | Force rebuilt with `--no-cache` |
| `reporter` RabbitMQ error | Queue previously created without `x-dead-letter-exchange`; arg mismatch on redeclare | Wiped `rabbitmq_data` volume, queues recreated cleanly |

---

## M2 — Eyes Open ✅

**Purpose:** Build the Scraper. Real HackerOne programs flow into the database on a schedule.
**Target outcome:** `POST /scrape/trigger` → rows in `programs` + `program_scopes` → message on `scan.jobs`.
**Outcome:** Scraper service implemented with scheduler, reconciler, and Redis locking; 52 unit tests in repo.

### Files created
- [x] `backend/migrations/versions/002_scraper_full.py` — full `programs`, `program_scopes`, `program_policies` schema
- [x] `backend/services/scraper/collectors/__init__.py`
- [x] `backend/services/scraper/collectors/base.py` — `BaseCollector` abstract class + `CollectorRegistry`
- [x] `backend/services/scraper/collectors/hackerone.py` — HackerOne API v1, 429 retry, structured_scopes
- [x] `backend/services/scraper/scope_parser.py` — typed `ProgramScope` objects, all asset types
- [x] `backend/services/scraper/repository.py` — `ProgramRepository.upsert()`, preserve `queued_for_scan`
- [x] `backend/services/scraper/publisher.py` — `QueuePublisher` wrapper, sets flag on publish failure
- [x] `backend/services/scraper/reconciler.py` — APScheduler job, republishes `queued_for_scan=True` programs
- [x] `backend/services/scraper/config.py` — scraper-specific config (HackerOne credentials, intervals)
- [x] `backend/services/scraper/models.py`
- [x] `backend/services/scraper/main.py` — **replaced skeleton** with full implementation (APIs + scheduler)
- [x] `tests/unit/test_scraper.py` — 52 tests defined
- [x] `tests/integrations/test_scraper_pipeline.py` — scrape → DB → queue publish flow

### Scraper API Routes (implemented)
```
POST /api/v1/scrape/trigger         — trigger immediate scrape for a platform
POST /api/v1/scrape/publish-batch   — trigger bounded background publish batch for due programs
GET  /api/v1/programs               — paginated program listing with filters
GET  /api/v1/programs/{program_id}  — single program detail
GET  /api/v1/programs/{program_id}/scope — scope entries for a program
GET  /api/v1/health                 — health check
```

### Definition of Done
- [x] `POST /scrape/trigger` produces rows in `programs` and `program_scopes`
- [x] Message appears on `scan.jobs` in RabbitMQ management UI
- [x] Simulated publish failure sets `queued_for_scan=True`; reconciler clears it next cycle
- [x] Simulated 429 triggers retry with `Retry-After` delay
- [x] Coverage ≥ 80% (86% hackerone.py, 93% scope_parser.py, 100% models/base/reconciler)

### Bugs Fixed During M2
| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `ModuleNotFoundError: hackerone` | `hackerone.py` delivered as a directory instead of a file | Deleted directory, recreated as `.py` file |
| `SyntaxError: utf-8 codec can't decode 0xff` | `echo $null >` on PowerShell writes UTF-16 BOM | Used `[System.IO.File]::WriteAllText()` instead |
| `ImportError: QueueConnectionError` | M2 `exceptions.py` replaced M1 version without auditing existing imports | Added `QueueConnectionError` back as subclass of `QueueError` |
| `TypeError: build_scan_job_message() unexpected keyword argument` | Called shared function with wrong signature — assumed flat kwargs | Read actual M1 source; refactored call to pass `ScanJobsPayload` object |
| Redis version conflict in Docker build | `m2_additions.txt` specified `redis==5.0.1` but `base.txt` already had `redis==5.0.4` | Removed duplicate — existing version already includes asyncio support |

---

## M3 — First Strike ✅

**Purpose:** Core Engine unauthenticated scanning pipeline — Stages 0 through 6 + Stage 10 (aggregation).
**Target outcome:** Scan job consumed, pipeline executed, findings deduplicated and persisted in database, report.jobs published.
**Completed:** 2026-03-18. Verification suite documented in `docs/M3_Verification_Runbook.md`.
**Note:** Integration suite requires Docker Postgres bound to host `5432` (local Postgres must be stopped to avoid conflicts).

### Pipeline Files (`backend/services/core_engine/pipeline/`)
- [x] `context.py` — `ScanContext`, `ScopeDefinition`, `FeatureFlags` dataclasses
- [x] `scope_filter.py` — Stage 0: `ScopeFilter` class with domain, wildcard, CIDR, URL matching
- [x] `asset_discovery.py` — Stage 1: subfinder → alterx → dnsx → httpx chain
- [x] `fingerprinting.py` — Stage 2: httpx tech-detect + WAF detection
- [x] `enumeration.py` — Stage 3: ffuf + waybackurls + JS download to MinIO
- [x] `nuclei_scan.py` — Stage 4: nuclei scanning with template exclusion and exit-code handling
- [x] `web_vuln_tests.py` — Stage 5: XSS, CORS, CRLF scanning + passive sensitive path detection
- [x] `js_secrets.py` — Stage 6: regex-based secret detection in downloaded JS files (12 patterns)
- [x] `aggregator.py` — Stage 10: deduplication, persistence, vulnerability grouping, report.jobs publish
- [x] `waf_utils.py` — WAF technology detection helper

### Orchestration & Support
- [x] `scan_task.py` — `run_scan_task()` → `_async_scan_pipeline()` → `_execute_pipeline()` with scope fetch from Scraper API
- [x] `worker.py` — Celery task entry, envelope validation, `scan.jobs` consumer
- [x] `main.py` — **replaced skeleton** with full FastAPI app: scan APIs, watchdog scheduler, health
- [x] `repository.py` — `ScanRepository`: create/resume scan, save assets/endpoints/js_assets/findings, mark complete, record stages
- [x] `models.py` — `DiscoveredAsset`, `DiscoveredEndpoint`, `DiscoveredJsAsset`, `FindingCandidate`, `ScanResult`
- [x] `dedup.py` — `compute_dedup_hash()`: SHA-256 of vulnerability_type | url | parameter | payload
- [x] `cvss.py` — `severity_to_cvss()`, `nuclei_severity()` mapping functions
- [x] `subprocess_utils.py` — `run_tool_communicate()`, `parse_jsonl()` for external tool execution
- [x] `watchdog.py` — APScheduler job detecting stuck scans (running > 2h)
- [x] `startup_checks.py` — `StartupCheck` dataclass, `collect_toolchain_checks()` for nuclei binary validation
- [x] `config.py` — `EngineConfig(BaseServiceConfig)` with nuclei, httpx, ffuf tuning knobs
- [x] `Dockerfile` — core-engine/core-worker image with subfinder, alterx, dnsx, httpx, ffuf, nuclei, waybackurls
- [x] `backend/migrations/versions/003_engine.py` — engine schema (assets, endpoints, js_assets, findings, finding_evidence, vulnerability_groups, scan_stages)

### Core Engine API Routes (implemented)
```
POST /api/v1/scans/start             — start a scan for a program (fetches program from Scraper)
GET  /api/v1/scans                   — list all scans with status
GET  /api/v1/scans/{scan_id}         — single scan detail with stage breakdown
GET  /api/v1/scans/{scan_id}/findings — findings for a scan (filterable by verified)
GET  /api/v1/queue/dlq/inspect       — inspect dead letter queue messages
GET  /api/v1/health                  — health check (DB, RabbitMQ, Redis, Scraper, toolchain)
```

### Tests
- [x] `tests/unit/test_engine.py` — 65 tests (scope filter, asset discovery, fingerprinting, enumeration, nuclei, web_vuln_tests, js_secrets, aggregator, dedup, cvss, models, scan_task, pipeline execution)
- [x] `tests/unit/test_reporter_worker.py` — 5 tests (reporter worker message handling)
- [x] `tests/unit/test_scraper_scan_publish_flow.py` — 4 tests (scraper-to-scan publish flow)
- [x] `tests/integrations/test_engine_pipeline.py` — engine pipeline integration
- [x] `tests/integrations/test_m3_verification.py` — M3 verification suite
- [x] `tests/integrations/test_e2e_system_trace.py` — end-to-end system trace (scraper → engine → reporter)

### Verification Completed
- [x] Re-run unit tests (`python -m pytest tests\unit -v`)
- [x] Re-run integration tests (scraper suite) with Docker infra up (`python -m pytest tests\integrations -v`)
- [x] Bind Docker Postgres to host `5432` for integration tests (`infra/docker-compose.yml`)
- [x] Rebuild core-engine/core-worker image and verify `waybackurls` availability in-container
- [x] Run a full scan and confirm scope is fetched from Scraper API
- [x] Simulate stuck scan and confirm watchdog republishes and increments `retry_count`
- [x] Confirm `failed_scope` status on empty/invalid scope

---

## M4 — Read the Room 🔲

**Purpose:** Build the Reporter. Findings become a downloadable PDF/DOCX report.
**Target outcome:** Full chain — scrape → scan → report → `GET /reports/{id}/download` returns real PDF.

### Files to create
- [ ] `backend/migrations/versions/004_reporter.py` — `reports`, `reproduction_packs`
- [ ] `backend/services/reporter/models.py` — `ParsedScan` dataclass, zero-finding guard
- [ ] `backend/services/reporter/reproduction.py` — curl + raw HTTP + browser steps per finding
- [ ] `backend/services/reporter/generators/pdf.py` — reportlab/weasyprint PDF generator
- [ ] `backend/services/reporter/generators/docx.py` — python-docx DOCX generator
- [ ] `backend/services/reporter/report_task.py` — Celery task, fetch → assemble → generate → upload
- [ ] `backend/services/reporter/watchdog.py` — APScheduler stale report recovery
- [ ] `backend/services/reporter/main.py` — **replace skeleton** with report APIs
- [ ] `backend/services/reporter/worker.py` — **replace message-logging stub** with real report_task
- [ ] `tests/unit/test_reporter.py`
- [ ] `tests/integrations/test_report_pipeline.py` — `report.jobs` → MinIO file → download API

### Definition of Done
- [ ] Full chain produces downloadable PDF with findings table + reproduction steps
- [ ] Zero-finding scan produces valid "No Findings" report, not a crash
- [ ] MinIO contains report at expected path
- [ ] Coverage ≥ 80%

---

## M5 — Get Inside 🔲

**Purpose:** Authenticated scanning via Playwright browser sessions.

### Key files to create
- [ ] `backend/services/browser_worker/playwright_context.py` — scoped context, route intercept
- [ ] `backend/services/browser_worker/session_store.py` — AES-256 encrypt/decrypt, storage_state
- [ ] `backend/services/browser_worker/scenario_engine.py` — YAML loader, step interpreter
- [ ] `backend/services/browser_worker/scenarios/login_basic.yaml`
- [ ] `backend/services/browser_worker/scenarios/login_totp.yaml`
- [ ] `backend/services/browser_worker/worker.py` — **replace skeleton**
- [ ] `backend/migrations/versions/005_browser_sessions.py` — `browser_sessions` table

---

## M6 — Break the Logic 🔲

**Purpose:** API fuzzing + enhanced JS analysis.

### Key files to create
- [ ] `backend/services/api_fuzzer_worker/fuzzer.py` — Schemathesis + RESTler + ffuf mutator
- [ ] `backend/services/api_fuzzer_worker/anomaly_detector.py`
- [ ] `backend/services/api_fuzzer_worker/worker.py` — **replace skeleton**
- [ ] `backend/services/js_analysis_worker/semgrep_runner.py`
- [ ] `backend/services/js_analysis_worker/ast_analyzer.py` — DOM XSS, postMessage, prototype pollution
- [ ] `backend/services/js_analysis_worker/secret_patterns.py`
- [ ] `backend/services/js_analysis_worker/worker.py` — **replace skeleton**
- [ ] `backend/migrations/versions/006_api_schemas.py` — `api_schemas` table

---

## M7 — Prove It 🔲

**Purpose:** Exploit Verifier — evidence-first findings, zero unverified in reports.

### Key files to create
- [ ] `backend/services/exploit_verifier/verifiers/xss.py` — CDP session detection
- [ ] `backend/services/exploit_verifier/verifiers/ssrf.py` — Interactsh OOB
- [ ] `backend/services/exploit_verifier/verifiers/idor.py` — cross-session access
- [ ] `backend/services/exploit_verifier/verifiers/cors.py`
- [ ] `backend/services/exploit_verifier/verifiers/sqli.py` — time-based blind
- [ ] `backend/services/exploit_verifier/verifiers/secret.py` — live key authentication
- [ ] `backend/services/exploit_verifier/evidence.py` — MinIO evidence bundle assembly
- [ ] `backend/services/exploit_verifier/interactsh.py` — OOB registration + polling
- [ ] `backend/services/exploit_verifier/worker.py` — **replace skeleton**
- [ ] `backend/migrations/versions/007_finding_evidence.py` — `finding_evidence` table

---

## M8 — Connect the Dots 🔲

**Purpose:** Attack Graph Engine — Neo4j correlation, exploit chains.

### Key files to create
- [ ] `backend/services/attack_graph_engine/graph.py` — Neo4j driver, MERGE ingestion
- [ ] `backend/services/attack_graph_engine/indexes.py` — index creation on startup
- [ ] `backend/services/attack_graph_engine/edge_inference.py` — CONTROLS, CHAINS_TO rules
- [ ] `backend/services/attack_graph_engine/chain_detector.py` — Cypher queries
- [ ] `backend/services/attack_graph_engine/severity.py` — chain severity escalation
- [ ] `backend/services/attack_graph_engine/main.py` — **replace skeleton** with graph APIs
- [ ] `backend/migrations/versions/008_exploit_chains.py` — `exploit_chains` table

---

## M9 — Think Harder 🔲

**Purpose:** Scenario Runner — race conditions, privilege escalation, workflow bypass.

### Key files to create
- [ ] `backend/services/scenario_runner/race/nuclei_race.py` — primary path via nuclei `-race`
- [ ] `backend/services/scenario_runner/race/h2spacex_attack.py` — secondary path for varied bodies
- [ ] `backend/services/scenario_runner/race/outcome_detector.py` — three-signal detector
- [ ] `backend/services/scenario_runner/race/warmup.py` — connection warming helper
- [ ] `backend/services/scenario_runner/scenarios/race_transfer.yaml`
- [ ] `backend/services/scenario_runner/scenarios/priv_escalation_role.yaml`
- [ ] `backend/services/scenario_runner/scenarios/workflow_skip_payment.yaml`
- [ ] `backend/services/scenario_runner/worker.py` — **replace skeleton**

---

## M10 — The Machine 🔲

**Purpose:** AI Hypothesis Engine + full hardening + production readiness.

### Key files to create
- [ ] `backend/services/ai_analysis_worker/hypotheses.py` — Ollama structured output, three-layer reliability
- [ ] `backend/services/ai_analysis_worker/prompt_builder.py` — token budget management
- [ ] `backend/services/ai_analysis_worker/worker.py` — **replace skeleton**
- [ ] `backend/services/api_gateway/main.py` — **replace skeleton** with routing + rate limiting + auth
- [ ] `infra/docker-compose.yml` — add Ollama service
- [ ] `scripts/smoke_test.py` — end-to-end CI smoke test
- [ ] `docs/runbook.md` — operational runbook

---

## Infrastructure State

### Compose Services (infra/docker-compose.yml)
Defined services: `postgres`, `redis`, `rabbitmq`, `neo4j`, `minio`, `vault`, `migrate`, `minio-init`, `vault-init`, `scraper`, `core-engine`, `reporter`, `attack-graph-engine`, `core-worker`, `reporter-worker`, `browser-worker`, `api-fuzzer-worker`, `js-analysis-worker`, `scenario-runner`, `exploit-verifier`, `ai-analysis-worker`, `api-gateway`, `prometheus`, `grafana`, `loki`, `tempo`.

### Database Migrations in Repo
| Revision | File | Contents |
|----------|------|----------|
| 001_initial_schema | `001_initial_schema.py` (2966 bytes) | `programs`, `scans` (proof of life) |
| 002_scraper_full | `002_scraper_full.py` (5418 bytes) | `programs`, `program_scopes`, `program_policies` |
| 003_engine | `003_engine.py` (9646 bytes) | scan pipeline schema incl. `assets`, `endpoints`, `js_assets`, `findings`, `finding_evidence`, `vulnerability_groups`, `scan_stages` |

### MinIO Buckets (from `minio-init` entrypoint)
| Bucket | Source |
|--------|--------|
| reports | `mc mb --ignore-existing` |
| evidence | `mc mb --ignore-existing` |
| js-assets | `mc mb --ignore-existing` |
| summaries | `mc mb --ignore-existing` |

### Backend File Inventory by Service

| Service | Files | Implementation Status |
|---------|-------|-----------------------|
| `shared/` | 9 modules + `schemas/` (3 schema files) | ✅ Complete (M1) |
| `scraper/` | 10 files + `collectors/` (3 files) | ✅ Complete (M2) |
| `core_engine/` | 13 files + `pipeline/` (11 files) + Dockerfile | ✅ Complete (M3) |
| `reporter/` | main.py + worker.py + Dockerfile | ⚠️ Skeleton (worker validates messages, generation stub) |
| `attack_graph_engine/` | 3 files (skeleton) | 🔲 Skeleton (M1) |
| `browser_worker/` | 3 files (skeleton) | 🔲 Skeleton (M1) |
| `api_fuzzer_worker/` | 3 files (skeleton) | 🔲 Skeleton (M1) |
| `js_analysis_worker/` | 3 files (skeleton) | 🔲 Skeleton (M1) |
| `scenario_runner/` | 3 files (skeleton) | 🔲 Skeleton (M1) |
| `exploit_verifier/` | 3 files (skeleton) | 🔲 Skeleton (M1) |
| `ai_analysis_worker/` | 3 files (skeleton) | 🔲 Skeleton (M1) |
| `api_gateway/` | 3 files (skeleton) | 🔲 Skeleton (M1) |

---

## Known Issues / Technical Debt

See `docs/Issues.md` for the current, prioritized gap list.

| # | Issue | Severity | Status | Milestone to fix |
|---|-------|----------|--------|-----------------|
| 1 | `api-gateway` is a skeleton — no routing, no auth, no rate limiting | Low | Open | M10 |
| 2 | Most Celery workers are boundary validators/skeletons; core-engine worker is the only fully implemented one | Low | Open | M4-M10 per worker |
| 3 | `vault-init` one-shot populates placeholder secrets only | Low | Open | M10 |
| 4 | Tempo runs with default config; no custom tracing or alerting rules | Low | Open | M10 |
| 5 | Reporter worker validates `report.jobs` messages but emits `report_generation_not_yet_implemented` | Medium | Open | M4 |
| 6 | Scraper `/api/v1/scrape/trigger` repeatedly times out during E2E runs (ISS-009) | Medium | Open | M4 |
