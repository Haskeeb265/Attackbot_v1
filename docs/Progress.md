# AttackBot — Project Progress

> Last updated: 2026-03-10
> Current state: **M1 complete. All 21 containers healthy. Ready for M2.**

---

## Milestone Status

| # | Name | Status | Completed |
|---|------|--------|-----------|
| M1 | Solid Ground | ✅ Complete | 2026-03-10 |
| M2 | Eyes Open | 🔲 Not started | — |
| M3 | First Strike | 🔲 Not started | — |
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
**Outcome:** All 21 containers running healthy from cold boot with zero manual intervention.

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

### FastAPI Services (skeletons)
- [x] `services/scraper/` — port 8001, `/api/v1/health` returning healthy ✅
- [x] `services/core_engine/` — port 8002, `/api/v1/health` returning healthy ✅
- [x] `services/reporter/` — port 8003, `/api/v1/health` returning healthy ✅
- [x] `services/attack_graph_engine/` — port 8006, `/api/v1/health` returning healthy ✅
- [x] `services/api_gateway/` — port 8000, `/api/v1/health` returning healthy ✅

### Celery Workers (skeletons)
- [x] `services/core_engine/worker.py` — consumes `scan.jobs`
- [x] `services/reporter/worker.py` — consumes `report.jobs`
- [x] `services/browser_worker/worker.py` — consumes `browser.jobs`
- [x] `services/api_fuzzer_worker/worker.py` — consumes `api.fuzz.jobs`
- [x] `services/js_analysis_worker/worker.py` — consumes `js.analysis.jobs`
- [x] `services/scenario_runner/worker.py` — consumes `scenario.jobs`
- [x] `services/exploit_verifier/worker.py` — consumes `verify.jobs`
- [x] `services/ai_analysis_worker/worker.py` — consumes `ai.analysis.jobs`

### Tests
- [x] `tests/unit/test_shared.py` — 35 unit tests, all passing
- [x] `tests/integration/test_infra_startup.py` — DB connectivity + table existence
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

## M2 — Eyes Open 🔲

**Purpose:** Build the Scraper. Real HackerOne programs flow into the database on a schedule.
**Target outcome:** `POST /scrape/trigger` → rows in `programs` + `program_scopes` → message on `scan.jobs`.

### Files to create
- [ ] `backend/migrations/versions/002_scraper_full.py` — full `programs`, `program_scopes`, `program_policies` schema
- [ ] `backend/services/scraper/collectors/__init__.py`
- [ ] `backend/services/scraper/collectors/base.py` — `BaseCollector` abstract class + `CollectorRegistry`
- [ ] `backend/services/scraper/collectors/hackerone.py` — HackerOne API v1, 429 retry, structured_scopes
- [ ] `backend/services/scraper/scope_parser.py` — typed `ProgramScope` objects, all asset types
- [ ] `backend/services/scraper/repository.py` — `ProgramRepository.upsert()`, preserve `queued_for_scan`
- [ ] `backend/services/scraper/publisher.py` — `QueuePublisher` wrapper, sets flag on publish failure
- [ ] `backend/services/scraper/reconciler.py` — APScheduler job, republishes `queued_for_scan=True` programs
- [ ] `backend/services/scraper/config.py` — scraper-specific config (HackerOne credentials, intervals)
- [ ] `backend/services/scraper/main.py` — **replace skeleton** with full implementation (APIs + scheduler)
- [ ] `tests/unit/test_scraper.py` — collector normalization, scope parser, upsert, 429 retry, reconciler
- [ ] `tests/integration/test_scraper_pipeline.py` — scrape → DB → queue publish flow

### Definition of Done
- [ ] `POST /scrape/trigger` produces rows in `programs` and `program_scopes`
- [ ] Message appears on `scan.jobs` in RabbitMQ management UI
- [ ] Simulated publish failure sets `queued_for_scan=True`; reconciler clears it next cycle
- [ ] Simulated 429 triggers retry with `Retry-After` delay
- [ ] Coverage ≥ 80%

---

## M3 — First Strike 🔲

**Purpose:** Core Engine unauthenticated scanning pipeline — Stages 0 through 6.
**Target outcome:** Scan job consumed, pipeline executed, findings in database.

### Files to create
- [ ] `backend/migrations/versions/003_engine.py` — `scans`, `scan_stages`, `assets`, `endpoints`, `js_assets`, `findings`, `finding_evidence`, `vulnerability_groups`
- [ ] `backend/services/core_engine/pipeline/scope_filter.py` — Stage 0, fatal on failure
- [ ] `backend/services/core_engine/pipeline/asset_discovery.py` — Stage 1, subfinder → alterx → dnsx → httpx
- [ ] `backend/services/core_engine/pipeline/fingerprinting.py` — Stage 2, httpx tech detection
- [ ] `backend/services/core_engine/pipeline/enumeration.py` — Stage 3, ffuf + waybackurls + JS download
- [ ] `backend/services/core_engine/pipeline/nuclei_scan.py` — Stage 4, nuclei CLI wrapper
- [ ] `backend/services/core_engine/pipeline/web_vuln_tests.py` — Stage 5, XSS + CORS + gated scanners
- [ ] `backend/services/core_engine/pipeline/js_secrets.py` — Stage 6, regex secret detection
- [ ] `backend/services/core_engine/pipeline/aggregator.py` — Stage 7 (temp), dedup + persist + publish
- [ ] `backend/services/core_engine/subprocess.py` — CLI wrapper utilities (communicate pattern, streaming)
- [ ] `backend/services/core_engine/dedup.py` — `compute_dedup_hash()` with URL normalization
- [ ] `backend/services/core_engine/watchdog.py` — APScheduler crash recovery for stuck scans
- [ ] `backend/services/core_engine/scan_task.py` — Celery task entry, Redis lock, state machine
- [ ] `backend/services/core_engine/main.py` — **replace skeleton** with scan APIs
- [ ] `backend/services/core_engine/worker.py` — **replace skeleton** with real scan_task
- [ ] `tests/unit/test_core_engine.py`
- [ ] `tests/integration/test_scan_pipeline.py` — against DVWA or Juice Shop

### Definition of Done
- [ ] Scan job on `scan.jobs` produces populated `assets`, `endpoints`, `findings` in DB
- [ ] `scan.completed` message appears on `report.jobs`
- [ ] Watchdog marks crashed scans `failed_internal` and republishes if `retry_count < 2`
- [ ] Dedup hash correctly collapses duplicate findings
- [ ] Coverage ≥ 75%

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
- [ ] `backend/services/reporter/worker.py` — **replace skeleton** with real report_task
- [ ] `tests/unit/test_reporter.py`
- [ ] `tests/integration/test_report_pipeline.py` — `report.jobs` → MinIO file → download API

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

### Containers (as of M1)
| Container | Port | Status |
|-----------|------|--------|
| postgres | 5432 | ✅ Healthy |
| redis | 6379 | ✅ Healthy |
| rabbitmq | 5672 / 15672 | ✅ Healthy |
| neo4j | 7474 / 7687 | ✅ Healthy |
| minio | 9000 / 9001 | ✅ Healthy |
| vault | 8200 | ✅ Healthy |
| migrate | — | ✅ Exited 0 |
| minio-init | — | ✅ Exited 0 |
| vault-init | — | ✅ Exited 0 |
| scraper | 8001 | ✅ Healthy |
| core-engine | 8002 | ✅ Healthy |
| reporter | 8003 | ✅ Healthy |
| attack-graph-engine | 8006 | ✅ Healthy |
| api-gateway | 8000 | ✅ Healthy |
| core-worker | — | ✅ Running |
| reporter-worker | — | ✅ Running |
| browser-worker | — | ✅ Running |
| api-fuzzer-worker | — | ✅ Running |
| js-analysis-worker | — | ✅ Running |
| scenario-runner | — | ✅ Running |
| exploit-verifier | — | ✅ Running |
| ai-analysis-worker | — | ✅ Running |

### Database Migrations Applied
| Revision | Contents | Applied |
|----------|----------|---------|
| 001_initial_schema | `programs`, `scans` | ✅ |
| 002_scraper_full | Full scraper schema | 🔲 M2 |
| 003_engine | Engine scan data | 🔲 M3 |
| 004_findings | Findings + evidence | 🔲 M3 |
| 005_browser_sessions | Auth sessions | 🔲 M5 |
| 006_api_schemas | API fuzzing schema | 🔲 M6 |
| 007_finding_evidence | Evidence bundles | 🔲 M7 |
| 008_exploit_chains | Chain correlation | 🔲 M8 |

### MinIO Buckets
| Bucket | Status |
|--------|--------|
| reports | ✅ Created |
| evidence | ✅ Created |
| js-assets | ✅ Created |
| summaries | ✅ Created |

---

## Known Issues / Technical Debt

| # | Issue | Severity | Milestone to fix |
|---|-------|----------|-----------------|
| 1 | `api-gateway` is a skeleton — no routing, no auth, no rate limiting | Low | M10 |
| 2 | All Celery workers are skeletons — log receipt only | Low | M3–M10 per worker |
| 3 | RabbitMQ queues declared lazily at worker startup — DLQ topology not verified | Low | M3 |
| 4 | `vault-init` one-shot populates placeholder secrets only | Low | M2 (real HackerOne credentials) |
| 5 | `001_initial_schema` programs/scans tables are minimal proof-of-life only | Low | M2 (replaced by 002) |