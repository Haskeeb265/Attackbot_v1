# AttackBot â€” Project Progress

> Last updated: 2026-03-29
> Current state: **M3 is complete. M4 is in progress with ISS-009 fixed, migration `004_reporter` added, shared contracts updated, reporter API/worker pipeline active, sectioned PDF/DOCX renderers wired, and integration/e2e reporter test suites started.**
> Test inventory (repo): **unit and integration suites are expanded during M4 (reporter API/repository/parsing/reproduction/watchdog coverage added).** Skips still require dependency and environment availability such as `INTEGRATION_TARGET`, `DATABASE_URL`, and optional credentials.

---

## Milestone Status

| # | Name | Status | Completed |
|---|------|--------|-----------|
| M1 | Solid Ground | âœ… Complete | 2026-03-10 |
| M2 | Eyes Open | âœ… Complete | 2026-03-11 |
| M3 | First Strike | âœ… Complete | 2026-03-18 |
| M4 | Read the Room | In progress | — |
| M5 | Get Inside | ðŸ”² Not started | â€” |
| M6 | Break the Logic | ðŸ”² Not started | â€” |
| M7 | Prove It | ðŸ”² Not started | â€” |
| M8 | Connect the Dots | ðŸ”² Not started | â€” |
| M9 | Think Harder | ðŸ”² Not started | â€” |
| M10 | The Machine | ðŸ”² Not started | â€” |

---

## M1 â€” Solid Ground âœ…

**Purpose:** Project foundation, infrastructure, conventions, service skeletons.
**Outcome:** Infra compose defines 26 services with phased startup, healthchecks, named volumes, and resource limits.

### Infrastructure
- [x] `infra/docker-compose.yml` â€” 6-phase startup order, all healthchecks, named volumes, resource limits
- [x] `infra/prometheus/prometheus.yml` â€” scrape config for all service `/metrics` endpoints
- [x] `infra/grafana/provisioning/datasources/datasources.yml` â€” Prometheus + Loki + Tempo wired
- [x] `infra/grafana/provisioning/dashboards/dashboards.yml` â€” dashboard provider config
- [x] `infra/grafana/provisioning/dashboards/services_alive.json` â€” all-services health dashboard
- [x] `infra/loki/loki-config.yml` â€” log aggregation config
- [x] `infra/README.md` â€” bootstrap sequence, known constraints documented

### Shared Library (`backend/shared/`)
- [x] `config.py` â€” `BaseServiceConfig(BaseSettings)` â€” all services inherit this
- [x] `logging.py` â€” structlog JSON logger, `configure_logging()` + `get_logger()`
- [x] `db.py` â€” SQLAlchemy async engine factory, `init_db()`, `get_session()`, `check_db_health()`
- [x] `health.py` â€” `HealthResponse`, `ComponentHealth`, `HealthStatus` enum
- [x] `exceptions.py` â€” full exception hierarchy rooted at `AttackBotError`
- [x] `queue.py` â€” `Queues` constants, `QueuePublisher` with passive declare + publish
- [x] `vault.py` â€” `init_vault()`, `get_secret()`, `put_secret()` via hvac KV v2
- [x] `storage.py` â€” `init_storage()`, `upload_bytes()`, `download_bytes()`, `get_presigned_url()`
- [x] `schemas/envelope.py` â€” `MessageEnvelope`, `build_envelope()` factory
- [x] `schemas/scan_jobs.py` â€” `ScanJobsPayload`, `FeatureFlags`, `ScopeDefinition`, `build_scan_job_message()`
- [x] `schemas/report_jobs.py` â€” `ReportJobsPayload`, `SeverityBreakdown`, `build_report_job_message()`

### Database Migrations (`backend/migrations/`)
- [x] `alembic.ini` â€” Alembic config
- [x] `env.py` â€” async-aware, loads `DATABASE_URL` from environment
- [x] `script.py.mako` â€” migration file template
- [x] `versions/001_initial_schema.py` â€” `programs` + `scans` tables (proof of life)

### FastAPI Services (initial skeletons; some now implemented)
- [x] `backend/services/scraper/` â€” port 8001, `/api/v1/health` returning healthy âœ…
- [x] `backend/services/core_engine/` â€” port 8002, `/api/v1/health` returning healthy âœ…
- [x] `backend/services/reporter/` â€” port 8003, `/api/v1/health` returning healthy âœ…
- [x] `backend/services/attack_graph_engine/` â€” port 8006, `/api/v1/health` returning healthy âœ…
- [x] `backend/services/api_gateway/` â€” port 8000, `/api/v1/health` returning healthy âœ…

### Celery Workers (initial skeletons; core-engine and reporter now implemented)
Note: `backend/services/core_engine/worker.py` is fully implemented. `backend/services/reporter/worker.py` validates and logs `report.jobs` messages but does not yet generate reports. Others remain boundary validators/skeletons until their milestones.
- [x] `backend/services/core_engine/worker.py` â€” consumes `scan.jobs` âœ… fully implemented
- [x] `backend/services/reporter/worker.py` â€” consumes `report.jobs` (validates + logs, generation stub)
- [x] `backend/services/browser_worker/worker.py` â€” consumes `browser.jobs` (skeleton)
- [x] `backend/services/api_fuzzer_worker/worker.py` â€” consumes `api.fuzz.jobs` (skeleton)
- [x] `backend/services/js_analysis_worker/worker.py` â€” consumes `js.analysis.jobs` (skeleton)
- [x] `backend/services/scenario_runner/worker.py` â€” consumes `scenario.jobs` (skeleton)
- [x] `backend/services/exploit_verifier/worker.py` â€” consumes `verify.jobs` (skeleton)
- [x] `backend/services/ai_analysis_worker/worker.py` â€” consumes `ai.analysis.jobs` (skeleton)

### Tests
- [x] `tests/unit/test_shared.py` â€” 35 tests (exceptions, health, envelope, scan_jobs, report_jobs)
- [x] `tests/integrations/test_infra_startup.py` â€” 4 tests (DB health, query execution, programs table, scans table)
- [x] `tests/conftest.py` â€” singleton reset fixture

### CI
- [x] `.github/workflows/ci.yml` â€” lint (ruff), typecheck (mypy), test (pytest), docker build

### Bugs Fixed During M1
| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `attack-graph-engine` crash | `structlog.stdlib.add_logger_name` incompatible with `PrintLogger` | Removed from processor chain in `shared/logging.py` |
| `scraper` crash loop | Stale Docker image from pre-M1 code expecting `S3_ACCESS_KEY` | Force rebuilt with `--no-cache` |
| `reporter` RabbitMQ error | Queue previously created without `x-dead-letter-exchange`; arg mismatch on redeclare | Wiped `rabbitmq_data` volume, queues recreated cleanly |

---

## M2 â€” Eyes Open âœ…

**Purpose:** Build the Scraper. Real HackerOne programs flow into the database on a schedule.
**Target outcome:** `POST /scrape/trigger` â†’ rows in `programs` + `program_scopes` â†’ message on `scan.jobs`.
**Outcome:** Scraper service implemented with scheduler, reconciler, and Redis locking; 52 unit tests in repo.

### Files created
- [x] `backend/migrations/versions/002_scraper_full.py` â€” full `programs`, `program_scopes`, `program_policies` schema
- [x] `backend/services/scraper/collectors/__init__.py`
- [x] `backend/services/scraper/collectors/base.py` â€” `BaseCollector` abstract class + `CollectorRegistry`
- [x] `backend/services/scraper/collectors/hackerone.py` â€” HackerOne API v1, 429 retry, structured_scopes
- [x] `backend/services/scraper/scope_parser.py` â€” typed `ProgramScope` objects, all asset types
- [x] `backend/services/scraper/repository.py` â€” `ProgramRepository.upsert()`, preserve `queued_for_scan`
- [x] `backend/services/scraper/publisher.py` â€” `QueuePublisher` wrapper, sets flag on publish failure
- [x] `backend/services/scraper/reconciler.py` â€” APScheduler job, republishes `queued_for_scan=True` programs
- [x] `backend/services/scraper/config.py` â€” scraper-specific config (HackerOne credentials, intervals)
- [x] `backend/services/scraper/models.py`
- [x] `backend/services/scraper/main.py` â€” **replaced skeleton** with full implementation (APIs + scheduler)
- [x] `tests/unit/test_scraper.py` â€” 52 tests defined
- [x] `tests/integrations/test_scraper_pipeline.py` â€” scrape â†’ DB â†’ queue publish flow

### Scraper API Routes (implemented)
```
POST /api/v1/scrape/trigger         â€” trigger immediate scrape for a platform
POST /api/v1/scrape/publish-batch   â€” trigger bounded background publish batch for due programs
GET  /api/v1/programs               â€” paginated program listing with filters
GET  /api/v1/programs/{program_id}  â€” single program detail
GET  /api/v1/programs/{program_id}/scope â€” scope entries for a program
GET  /api/v1/health                 â€” health check
```

### Definition of Done
- [x] `POST /scrape/trigger` produces rows in `programs` and `program_scopes`
- [x] Message appears on `scan.jobs` in RabbitMQ management UI
- [x] Simulated publish failure sets `queued_for_scan=True`; reconciler clears it next cycle
- [x] Simulated 429 triggers retry with `Retry-After` delay
- [x] Coverage â‰¥ 80% (86% hackerone.py, 93% scope_parser.py, 100% models/base/reconciler)

### Bugs Fixed During M2
| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `ModuleNotFoundError: hackerone` | `hackerone.py` delivered as a directory instead of a file | Deleted directory, recreated as `.py` file |
| `SyntaxError: utf-8 codec can't decode 0xff` | `echo $null >` on PowerShell writes UTF-16 BOM | Used `[System.IO.File]::WriteAllText()` instead |
| `ImportError: QueueConnectionError` | M2 `exceptions.py` replaced M1 version without auditing existing imports | Added `QueueConnectionError` back as subclass of `QueueError` |
| `TypeError: build_scan_job_message() unexpected keyword argument` | Called shared function with wrong signature â€” assumed flat kwargs | Read actual M1 source; refactored call to pass `ScanJobsPayload` object |
| Redis version conflict in Docker build | `m2_additions.txt` specified `redis==5.0.1` but `base.txt` already had `redis==5.0.4` | Removed duplicate â€” existing version already includes asyncio support |

---

## M3 â€” First Strike âœ…

**Purpose:** Core Engine unauthenticated scanning pipeline â€” Stages 0 through 6 + Stage 10 (aggregation).
**Target outcome:** Scan job consumed, pipeline executed, findings deduplicated and persisted in database, report.jobs published.
**Completed:** 2026-03-18. Verification suite documented in `docs/M3_Verification_Runbook.md`.
**Note:** Integration suite requires Docker Postgres bound to host `5432` (local Postgres must be stopped to avoid conflicts).

### Pipeline Files (`backend/services/core_engine/pipeline/`)
- [x] `context.py` â€” `ScanContext`, `ScopeDefinition`, `FeatureFlags` dataclasses
- [x] `scope_filter.py` â€” Stage 0: `ScopeFilter` class with domain, wildcard, CIDR, URL matching
- [x] `asset_discovery.py` â€” Stage 1: subfinder â†’ alterx â†’ dnsx â†’ httpx chain
- [x] `fingerprinting.py` â€” Stage 2: httpx tech-detect + WAF detection
- [x] `enumeration.py` â€” Stage 3: ffuf + waybackurls + JS download to MinIO
- [x] `nuclei_scan.py` â€” Stage 4: nuclei scanning with template exclusion and exit-code handling
- [x] `web_vuln_tests.py` â€” Stage 5: XSS, CORS, CRLF scanning + passive sensitive path detection
- [x] `js_secrets.py` â€” Stage 6: regex-based secret detection in downloaded JS files (12 patterns)
- [x] `aggregator.py` â€” Stage 10: deduplication, persistence, vulnerability grouping, report.jobs publish
- [x] `waf_utils.py` â€” WAF technology detection helper

### Orchestration & Support
- [x] `scan_task.py` â€” `run_scan_task()` â†’ `_async_scan_pipeline()` â†’ `_execute_pipeline()` with scope fetch from Scraper API
- [x] `worker.py` â€” Celery task entry, envelope validation, `scan.jobs` consumer
- [x] `main.py` â€” **replaced skeleton** with full FastAPI app: scan APIs, watchdog scheduler, health
- [x] `repository.py` â€” `ScanRepository`: create/resume scan, save assets/endpoints/js_assets/findings, mark complete, record stages
- [x] `models.py` â€” `DiscoveredAsset`, `DiscoveredEndpoint`, `DiscoveredJsAsset`, `FindingCandidate`, `ScanResult`
- [x] `dedup.py` â€” `compute_dedup_hash()`: SHA-256 of vulnerability_type | url | parameter | payload
- [x] `cvss.py` â€” `severity_to_cvss()`, `nuclei_severity()` mapping functions
- [x] `subprocess_utils.py` â€” `run_tool_communicate()`, `parse_jsonl()` for external tool execution
- [x] `watchdog.py` â€” APScheduler job detecting stuck scans (running > 2h)
- [x] `startup_checks.py` â€” `StartupCheck` dataclass, `collect_toolchain_checks()` for nuclei binary validation
- [x] `config.py` â€” `EngineConfig(BaseServiceConfig)` with nuclei, httpx, ffuf tuning knobs
- [x] `Dockerfile` â€” core-engine/core-worker image with subfinder, alterx, dnsx, httpx, ffuf, nuclei, waybackurls
- [x] `backend/migrations/versions/003_engine.py` â€” engine schema (assets, endpoints, js_assets, findings, finding_evidence, vulnerability_groups, scan_stages)

### Core Engine API Routes (implemented)
```
POST /api/v1/scans/start             â€” start a scan for a program (fetches program from Scraper)
GET  /api/v1/scans                   â€” list all scans with status
GET  /api/v1/scans/{scan_id}         â€” single scan detail with stage breakdown
GET  /api/v1/scans/{scan_id}/findings â€” findings for a scan (filterable by verified)
GET  /api/v1/queue/dlq/inspect       â€” inspect dead letter queue messages
GET  /api/v1/health                  â€” health check (DB, RabbitMQ, Redis, Scraper, toolchain)
```

### Tests
- [x] `tests/unit/test_engine.py` â€” 65 tests (scope filter, asset discovery, fingerprinting, enumeration, nuclei, web_vuln_tests, js_secrets, aggregator, dedup, cvss, models, scan_task, pipeline execution)
- [x] `tests/unit/test_reporter_worker.py` â€” 5 tests (reporter worker message handling)
- [x] `tests/unit/test_scraper_scan_publish_flow.py` â€” 4 tests (scraper-to-scan publish flow)
- [x] `tests/integrations/test_engine_pipeline.py` â€” engine pipeline integration
- [x] `tests/integrations/test_m3_verification.py` â€” M3 verification suite
- [x] `tests/integrations/test_e2e_system_trace.py` â€” end-to-end system trace (scraper â†’ engine â†’ reporter)

### Verification Completed
- [x] Re-run unit tests (`python -m pytest tests\unit -v`)
- [x] Re-run integration tests (scraper suite) with Docker infra up (`python -m pytest tests\integrations -v`)
- [x] Bind Docker Postgres to host `5432` for integration tests (`infra/docker-compose.yml`)
- [x] Rebuild core-engine/core-worker image and verify `waybackurls` availability in-container
- [x] Run a full scan and confirm scope is fetched from Scraper API
- [x] Simulate stuck scan and confirm watchdog republishes and increments `retry_count`
- [x] Confirm `failed_scope` status on empty/invalid scope

---

## M4 â€” Read the Room ðŸ”²

**Purpose:** Build the Reporter. Findings become a downloadable PDF/DOCX report.
**Target outcome:** Full chain â€” scrape â†’ scan â†’ report â†’ `GET /reports/{id}/download` returns real PDF.

### Files to create
- [ ] `backend/migrations/versions/004_reporter.py` â€” `reports`, `reproduction_packs`
- [ ] `backend/services/reporter/models.py` â€” `ParsedScan` dataclass, zero-finding guard
- [ ] `backend/services/reporter/reproduction.py` â€” curl + raw HTTP + browser steps per finding
- [ ] `backend/services/reporter/generators/pdf.py` â€” reportlab/weasyprint PDF generator
- [ ] `backend/services/reporter/generators/docx.py` â€” python-docx DOCX generator
- [ ] `backend/services/reporter/report_task.py` â€” Celery task, fetch â†’ assemble â†’ generate â†’ upload
- [ ] `backend/services/reporter/watchdog.py` â€” APScheduler stale report recovery
- [ ] `backend/services/reporter/main.py` â€” **replace skeleton** with report APIs
- [ ] `backend/services/reporter/worker.py` â€” **replace message-logging stub** with real report_task
- [ ] `tests/unit/test_reporter.py`
- [ ] `tests/integrations/test_report_pipeline.py` â€” `report.jobs` â†’ MinIO file â†’ download API

### Definition of Done
- [ ] Full chain produces downloadable PDF with findings table + reproduction steps
- [ ] Zero-finding scan produces valid "No Findings" report, not a crash
- [ ] MinIO contains report at expected path
- [ ] Coverage â‰¥ 80%

---

## M5 â€” Get Inside ðŸ”²

**Purpose:** Authenticated scanning via Playwright browser sessions.

### Key files to create
- [ ] `backend/services/browser_worker/playwright_context.py` â€” scoped context, route intercept
- [ ] `backend/services/browser_worker/session_store.py` â€” AES-256 encrypt/decrypt, storage_state
- [ ] `backend/services/browser_worker/scenario_engine.py` â€” YAML loader, step interpreter
- [ ] `backend/services/browser_worker/scenarios/login_basic.yaml`
- [ ] `backend/services/browser_worker/scenarios/login_totp.yaml`
- [ ] `backend/services/browser_worker/worker.py` â€” **replace skeleton**
- [ ] `backend/migrations/versions/005_browser_sessions.py` â€” `browser_sessions` table

---

## M6 â€” Break the Logic ðŸ”²

**Purpose:** API fuzzing + enhanced JS analysis.

### Key files to create
- [ ] `backend/services/api_fuzzer_worker/fuzzer.py` â€” Schemathesis + RESTler + ffuf mutator
- [ ] `backend/services/api_fuzzer_worker/anomaly_detector.py`
- [ ] `backend/services/api_fuzzer_worker/worker.py` â€” **replace skeleton**
- [ ] `backend/services/js_analysis_worker/semgrep_runner.py`
- [ ] `backend/services/js_analysis_worker/ast_analyzer.py` â€” DOM XSS, postMessage, prototype pollution
- [ ] `backend/services/js_analysis_worker/secret_patterns.py`
- [ ] `backend/services/js_analysis_worker/worker.py` â€” **replace skeleton**
- [ ] `backend/migrations/versions/006_api_schemas.py` â€” `api_schemas` table

---

## M7 â€” Prove It ðŸ”²

**Purpose:** Exploit Verifier â€” evidence-first findings, zero unverified in reports.

### Key files to create
- [ ] `backend/services/exploit_verifier/verifiers/xss.py` â€” CDP session detection
- [ ] `backend/services/exploit_verifier/verifiers/ssrf.py` â€” Interactsh OOB
- [ ] `backend/services/exploit_verifier/verifiers/idor.py` â€” cross-session access
- [ ] `backend/services/exploit_verifier/verifiers/cors.py`
- [ ] `backend/services/exploit_verifier/verifiers/sqli.py` â€” time-based blind
- [ ] `backend/services/exploit_verifier/verifiers/secret.py` â€” live key authentication
- [ ] `backend/services/exploit_verifier/evidence.py` â€” MinIO evidence bundle assembly
- [ ] `backend/services/exploit_verifier/interactsh.py` â€” OOB registration + polling
- [ ] `backend/services/exploit_verifier/worker.py` â€” **replace skeleton**
- [ ] `backend/migrations/versions/007_finding_evidence.py` â€” `finding_evidence` table

---

## M8 â€” Connect the Dots ðŸ”²

**Purpose:** Attack Graph Engine â€” Neo4j correlation, exploit chains.

### Key files to create
- [ ] `backend/services/attack_graph_engine/graph.py` â€” Neo4j driver, MERGE ingestion
- [ ] `backend/services/attack_graph_engine/indexes.py` â€” index creation on startup
- [ ] `backend/services/attack_graph_engine/edge_inference.py` â€” CONTROLS, CHAINS_TO rules
- [ ] `backend/services/attack_graph_engine/chain_detector.py` â€” Cypher queries
- [ ] `backend/services/attack_graph_engine/severity.py` â€” chain severity escalation
- [ ] `backend/services/attack_graph_engine/main.py` â€” **replace skeleton** with graph APIs
- [ ] `backend/migrations/versions/008_exploit_chains.py` â€” `exploit_chains` table

---

## M9 â€” Think Harder ðŸ”²

**Purpose:** Scenario Runner â€” race conditions, privilege escalation, workflow bypass.

### Key files to create
- [ ] `backend/services/scenario_runner/race/nuclei_race.py` â€” primary path via nuclei `-race`
- [ ] `backend/services/scenario_runner/race/h2spacex_attack.py` â€” secondary path for varied bodies
- [ ] `backend/services/scenario_runner/race/outcome_detector.py` â€” three-signal detector
- [ ] `backend/services/scenario_runner/race/warmup.py` â€” connection warming helper
- [ ] `backend/services/scenario_runner/scenarios/race_transfer.yaml`
- [ ] `backend/services/scenario_runner/scenarios/priv_escalation_role.yaml`
- [ ] `backend/services/scenario_runner/scenarios/workflow_skip_payment.yaml`
- [ ] `backend/services/scenario_runner/worker.py` â€” **replace skeleton**

---

## M10 â€” The Machine ðŸ”²

**Purpose:** AI Hypothesis Engine + full hardening + production readiness.

### Key files to create
- [ ] `backend/services/ai_analysis_worker/hypotheses.py` â€” Ollama structured output, three-layer reliability
- [ ] `backend/services/ai_analysis_worker/prompt_builder.py` â€” token budget management
- [ ] `backend/services/ai_analysis_worker/worker.py` â€” **replace skeleton**
- [ ] `backend/services/api_gateway/main.py` â€” **replace skeleton** with routing + rate limiting + auth
- [ ] `infra/docker-compose.yml` â€” add Ollama service
- [ ] `scripts/smoke_test.py` â€” end-to-end CI smoke test
- [ ] `docs/runbook.md` â€” operational runbook

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
| `shared/` | 9 modules + `schemas/` (3 schema files) | âœ… Complete (M1) |
| `scraper/` | 10 files + `collectors/` (3 files) | âœ… Complete (M2) |
| `core_engine/` | 13 files + `pipeline/` (11 files) + Dockerfile | âœ… Complete (M3) |
| `reporter/` | main.py + worker.py + Dockerfile | âš ï¸ Skeleton (worker validates messages, generation stub) |
| `attack_graph_engine/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |
| `browser_worker/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |
| `api_fuzzer_worker/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |
| `js_analysis_worker/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |
| `scenario_runner/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |
| `exploit_verifier/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |
| `ai_analysis_worker/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |
| `api_gateway/` | 3 files (skeleton) | ðŸ”² Skeleton (M1) |

---

## Known Issues / Technical Debt

See `docs/Issues.md` for the current, prioritized gap list.

| # | Issue | Severity | Status | Milestone to fix |
|---|-------|----------|--------|-----------------|
| 1 | `api-gateway` is a skeleton â€” no routing, no auth, no rate limiting | Low | Open | M10 |
| 2 | Most Celery workers are boundary validators/skeletons; core-engine worker is the only fully implemented one | Low | Open | M4-M10 per worker |
| 3 | `vault-init` one-shot populates placeholder secrets only | Low | Open | M10 |
| 4 | Tempo runs with default config; no custom tracing or alerting rules | Low | Open | M10 |
| 5 | Reporter generation was previously a stub; replaced with initial pipeline | Medium | In progress | M4 |
| 6 | Scraper `/api/v1/scrape/trigger` timeout behavior (ISS-009) | Medium | Closed | M4 |


---

## Progress Update (2026-03-29)

### M4 chunks completed so far
- ISS-009 completed: `POST /api/v1/scrape/trigger` now returns `202 Accepted` immediately and runs in background.
- Scraper integration expectations updated to polling behavior in `tests/integrations/test_scraper_pipeline.py`.
- Shared schema compatibility landed:
  `report.jobs` supports optional `report_ids`, and new `reports.completed` schema was added.
- Shared queue publisher now supports active queue declaration with `ensure_queue()`.
- Core Engine added reporter evidence read endpoint:
  `GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence`.
- Migration `004_reporter` created with additive tables:
  `reports`, `reproduction_packs`.

### Reporter implementation landed
- Replaced reporter skeleton API with:
  `GET /api/v1/reports`, `GET /api/v1/reports/{report_id}`,
  `GET /api/v1/reports/{report_id}/download`,
  `GET /api/v1/scans/{scan_id}/reports`,
  `POST /api/v1/reports/generate`,
  `GET /api/v1/health`.
- `POST /api/v1/reports/generate` now enforces scan-state gating (`202` only for `completed`/`partial`, `409` otherwise).
- Generate endpoint allocates stable report IDs and enqueues `report.jobs` with `report_ids`.
- Download endpoint enforces status matrix:
  `completed`/`partial` => 200 presigned URL,
  `generating`/`failed` => 409,
  missing row => 404.
- Reporter health now includes upstream checks with cache TTL and M4-specific attack graph `degraded` status.
- Reporter persistence layer implemented (`create_or_reset_report`, `mark_generating`, `mark_completed`, `mark_partial`, `mark_failed`, listing and lookup methods).
- Reporter worker now dispatches validated `report.jobs` envelopes into report generation tasks.
- Initial report task pipeline implemented:
  real upstream fetches (core/scraper), parsed scan model build (all findings + `is_verified` kept), deterministic reproduction pack generation with fallback behavior, per-format artifact generation, storage upload, row terminal updates, and `reports.completed` publish.
- Reporter watchdog recovery added for stale `generating` rows (`watchdog_timeout` failover path).
- Renderer package added and wired:
  `backend/services/reporter/renderers/{base,theme,sections,pdf,docx}.py`.
- Report generation now uses section-planned PDF/DOCX renderers (sequential format processing preserved with explicit comment in `report_task.py`).
- Executive summary caveat for unverified findings is now emitted, findings table includes verification status, and clean reports use the no-findings statement path.
- Raw HTTP appendix rendering is now gated by `settings.include_raw_http_appendix`.
- Evidence screenshot sections are now gated by `parsed_scan.include_evidence_screenshots`, with embed failures marked as partial reason `evidence_image_load_failed`.
- Reporter metrics module added (`backend/services/reporter/metrics.py`) and wired into:
  generation outcomes/duration/failures, partial-reason counters, zero-findings counter, evidence-missing counter, and download/presign endpoint metrics.
- Added controlled upload-failure injection hook for integration validation:
  `ReporterConfig.force_upload_failure_report_ids_str` (`*` or explicit report IDs).
- Reporter worker now publishes exhausted retries to `report.jobs.dlq` before surfacing terminal failure.
- Docker/ops wiring added for failure-path validation:
  `infra/docker-compose.yml` now passes `FORCE_UPLOAD_FAILURE_REPORT_IDS_STR` and `REPORT_TASK_RETRY_BACKOFF_SECONDS_STR` into reporter and reporter-worker.
- Added live-run automation script:
  `scripts/run_m4_live_validation.ps1` (baseline A-E/H/I/J + E2E + forced-failure F/G sequence).
- Added matching environment template keys in `.env.example` for reporter failure hooks, integration toggles, and RabbitMQ management API overrides.

### Tests added/updated
- Added:
  `tests/unit/test_core_engine_evidence_api.py`
  `tests/unit/test_reporter_evidence.py`
  `tests/unit/test_reporter_render_sections.py`
  `tests/unit/test_reporter_render_golden.py`
  `tests/unit/test_reporter_repository.py`
  `tests/unit/test_reporter_api.py`
  `tests/unit/test_reporter_parsing.py`
  `tests/unit/test_reporter_reproduction.py`
  `tests/unit/test_reporter_watchdog.py`
  `tests/unit/test_report_task_rendering.py`
  `tests/unit/test_report_task_pipeline.py`
  `tests/integrations/test_reporter_pipeline.py`
  `tests/e2e/test_report_download_flow.py`
  `tests/fixtures/reporter/golden/{report_outline_pdf.txt, report_outline_docx.txt, no_findings_summary.txt}`
- Updated:
  `tests/unit/test_reporter_api.py` (download metrics assertions)
  `tests/unit/test_reporter_evidence.py` (evidence-missing metric assertion)
  `tests/unit/test_reporter_worker.py` (retry-exhaustion DLQ publish path)
  `tests/unit/test_report_task_pipeline.py` (forced upload failure path)
  `tests/integrations/test_reporter_pipeline.py` (expanded with scenarios A/B/C/D/E/F/G + DB-backed setup/cleanup helpers and RabbitMQ mgmt checks)
  `tests/unit/test_scraper_scan_publish_flow.py`
  `tests/unit/test_shared.py`

### Verification run (local)
- Command:
  `python -m pytest tests/unit/test_shared.py tests/unit/test_scraper_scan_publish_flow.py tests/unit/test_core_engine_evidence_api.py tests/unit/test_reporter_parsing.py tests/unit/test_reporter_reproduction.py tests/unit/test_report_task_rendering.py tests/unit/test_report_task_pipeline.py tests/unit/test_reporter_evidence.py tests/unit/test_reporter_render_sections.py tests/unit/test_reporter_render_golden.py tests/unit/test_reporter_watchdog.py tests/unit/test_reporter_repository.py tests/unit/test_reporter_api.py tests/unit/test_reporter_worker.py tests/integrations/test_reporter_pipeline.py tests/e2e/test_report_download_flow.py -q`
- Result:
  `62 passed, 44 skipped`.
- Notes:
  skips are dependency/environment-gated in this local setup (for example kombu/celery-heavy paths, opt-in failure-scenario env flags, and local Docker services not running for integration/e2e scenarios).

### Verification run (live Docker stack)
- Commands:
  `powershell -ExecutionPolicy Bypass -File scripts/run_m4_live_validation.ps1`
  `python -m pytest tests/integrations/test_reporter_pipeline.py tests/e2e/test_report_download_flow.py -rs`
- Infra fixes applied during validation:
  `backend/migrations/versions/004_reporter.py` syntax fix (`branch_labels = None`).
  `infra/docker-compose.yml` reporter host port mapping added (`8003:8003`) so localhost integration tests can reach reporter.
  `scripts/run_m4_live_validation.ps1` now waits for `core-engine` and `reporter` health before running pytest, preventing false "all skipped" runs when services are still starting.
- Latest live result snapshot:
  baseline (A-E,H,I,J): `2 passed, 8 skipped`
  failure path (F/G): `1 passed, 1 skipped`
  e2e download flow: `2 skipped`
- Remaining skip reasons are now environment/data-specific (not Docker daemon availability), primarily:
  host-side DB mismatch for direct asyncpg inserts (`scans` / `finding_evidence` relation not found on host-local Postgres),
  missing local optional deps (`kombu`/`aio-pika`) for organic queue publishing tests,
  presigned MinIO host reachability from host runtime (`getaddrinfo failed` on download URL host).

### Remaining M4 work
- Final Chunk 9 closure: eliminate the remaining environment-gated skips and convert A-J + Path 1/2 into full pass in one consistent runtime.
- Active blockers are no longer Docker availability; they are host/runtime alignment issues (DB target, optional Python deps, and MinIO presigned URL host accessibility from test runner).



