# AttackBot — Current Issues

> Last updated: 2026-03-20
> Scope: Issues identified during milestone audit against M1–M3, `docs/Flow.md`, and `docs/Architecture.md`.

| ID | Issue | Impact | Status | Location | Suggested Fix | Milestone |
|---|---|---|---|---|---|---|
| ISS-001 | Watchdog republish is a stub (logs only) | Stuck scans are marked failed but never requeued; M3 DoD #9 not met | Closed | `backend/services/core_engine/main.py`, `backend/services/core_engine/watchdog.py` | Implement republish to `scan.jobs`, increment `retry_count`, and use a real payload | M3 |
| ISS-002 | Core engine does not fetch scope from Scraper API | Flow mismatch; scan relies on payload scope only | Closed | `backend/services/core_engine/scan_task.py` | Call Scraper `GET /api/v1/programs/{program_id}/scope`; fail as `failed_scope` if empty | M3 |
| ISS-003 | `failed_internal` retry semantics not implemented | `retry_count` unused; scans are not resumed per Flow | Closed | `backend/services/core_engine/repository.py` | Reuse last `failed_internal` scan when `retry_count < 2`; increment on retry | M3 |
| ISS-004 | Scope failures do not set `failed_scope` | Incorrect status classification vs Architecture/Flow | Closed | `backend/services/core_engine/scan_task.py`, `backend/services/core_engine/pipeline/scope_filter.py` | Catch scope errors and mark scan `failed_scope` | M3 |
| ISS-005 | `waybackurls` missing from core engine image | Stage 3 enumeration is reduced | Closed | `backend/services/core_engine/Dockerfile`, `backend/services/core_engine/pipeline/enumeration.py` | Install `waybackurls` or update docs to reflect intentional skip | M3 |
| ISS-006 | Manual scan API payload mismatches M3 docs | `POST /api/v1/scans/start` returns 422 unless full `ScanJobsPayload` is provided | Closed | `backend/services/core_engine/main.py`, `docs/Milestones/M3_FirstStrike.md` | Align docs with current schema or accept a minimal body and build payload server-side | M3 |
| ISS-007 | Integration test path mismatch | Docs reference `tests/integration`, but repo uses `tests/integrations` | Fixed | `tests/integrations/test_engine_pipeline.py`, `docs/Milestones/M3_FirstStrike.md` | Rename folder or update docs/commands | M3 |
| ISS-008 | Architecture says only `api-gateway` is public, compose exposes more | Documentation drift for deployment model | Closed | `docs/Architecture.md`, `infra/docker-compose.yml` | Document dev exposure or add a prod-only compose profile | M1 / M10 |
