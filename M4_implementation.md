Project State

As of March 29, 2026, AttackBot is at M3 complete and M4 Reporter is not yet implemented.
Existing Reporter worker currently consumes report.jobs and logs report_generation_not_yet_implemented.
Your latest E2E evidence (known-vuln flow) confirmed M3 stability and showed real findings are currently mostly is_verified=false.
What We Decided

Keep M4 rollout incremental and gate-driven, not “big bang.”
Preserve the existing raw-envelope report.jobs ingestion path (no producer-side Celery contract refactor).
Use additive-only compatibility:
004_reporter migration adds only reports and reproduction_packs.
report.jobs gets optional report_ids.
New reports.completed contract is added.
Adopt the policy change for M4 reports:
Include all findings (not verified-only), and surface is_verified in output.
Add an executive summary caveat when unverified findings are present.
Milestone Doc Updates Applied

Updated docs/Milestones/M4_ReadTheRoom.md to v2.1 (2026-03-29).
Added explicit execution gates:
Gate 0: M3 baseline locked.
Gate 1: ISS-009 complete (/scrape/trigger async 202 + polling test update).
Gate 2: Reporter plumbing alive.
Gate 3: First downloadable real PDF.
Updated M4 sections to align with all-findings policy:
Core client fetches /findings (not ?verified=true).
Parsing rules preserve is_verified.
Findings table includes verification status.
No-findings wording now says “No findings” (not “No verified findings”).
Added/updated unit/integration test expectations to match this policy.
Incremental Delivery Plan (for your coding assistant)

Implement in verifiable chunks:
Baseline lock + test/path hygiene.
ISS-009 scraper async trigger + polling test update.
Shared schemas + queue declaration safety.
Core evidence endpoint.
004_reporter migration + repository status lifecycle.
Reporter API skeleton (generate, download, list/detail/health).
Worker/task core pipeline (organic + regenerate ID stability).
Rendering + repro packs + partial semantics.
Evidence concurrency/retries/watchdog/DLQ.
Full integration (A–J) + E2E Path 1/2 + gate closure.
Rule for progression: each chunk must pass its own checks before the next chunk starts.


M4 Incremental Delivery Plan (Verifiable Chunks)
Summary
Implement M4 in gated vertical slices so each slice is independently runnable and testable before moving on. Keep M3 stable by isolatig high-risk changes early (ISS-009), then layering contracts, schema, reporter internals, and finally full integration/E2E. Use Gate 0-3 as hard stop points.

Chunk Sequence
Chunk 0: Baseline Lock + Harness Hygiene
Freeze baseline: confirm M3 health, queues, and current test status.
Fix verification command/path drift so all chunk commands use real repo layout (tests/integrations, not tests/integration).
Verification: docker compose ... ps, alembic current == 003, pytest tests/unit -q, pytest tests/integrations/test_m3_verification.py -q.
Chunk 1: ISS-009 Only (Scraper Async Trigger)
Change POST /api/v1/scrape/trigger to immediate 202 Accepted + background execution.
Update tests/integrations/test_scraper_pipeline.py::test_trigger_produces_programs_in_db to polling behavior.
Verification: endpoint response contract check, scraper integration test(s), no regressions in scraper unit tests.
Chunk 2: Shared Contracts + Queue Declaration Safety
Add optional report_ids to report.jobs schema.
Add reports.completed schema.
Add QueuePublisher.ensure_queue() active declaration helper for reporter publish path.
Verification: pytest tests/unit/test_shared.py -q; new schema compatibility tests (organic message without report_ids + regenerate shape with report_ids).
Chunk 3: Core Engine Reporter Read API
Add GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence.
Keep existing scan/findings responses backward compatible.
Verification: targeted core-engine API tests + integration check returning empty items for no evidence, 404 only on scan/finding mismatch.
Chunk 4: DB Migration + Reporter Persistence Layer
Add migration 004_reporter (reports, reproduction_packs) with constraints/indexes only.
Implement reporter repository methods with explicit UPSERT and status transitions (mark_partial sets generated_at).
Verification: migrate up/current checks, DB table/constraint assertions, repository unit tests for upsert/id stability/status mapping.
Chunk 5: Reporter Service API Skeleton (Read/Generate/Download Paths)
Replace reporter skeleton API with list/detail/by-scan/download/generate/health endpoints.
Implement scan-state gating for POST /reports/generate and status gating for download.
Wire upstream health caching + attack-graph degraded behavior.
Verification: API unit/integration tests for 202/409/404 matrix and download status matrix.
Chunk 6: Worker/Task Pipeline Core (No Evidence/Repro Complexity Yet)
Replace reporter worker stub to process report.jobs raw envelopes and call report task.
Implement dual producer branching (report_ids present vs absent), sequential per-format processing, row lifecycle, storage upload, and reports.completed publish.
Implement all-findings policy with is_verified preserved in parsed model.
Verification: integration scenarios for organic + regenerate ID stability, row transitions, artifact presence, publish events.
Chunk 7: Rendering + Reproduction Packs + Partial Semantics
Implement PDF/DOCX renderers with required section order and validation checks.
Add findings table verification-status display and executive summary unverified caveat.
Implement deterministic reproduction packs and fallback packs; fallback triggers partial.
Verification: golden-text tests (PDF/DOCX outlines, fallback pack), status transition tests (completed vs partial).
Chunk 8: Evidence Handling + Resilience + Watchdog + DLQ
Implement evidence fetch/download with concurrency cap and temp cleanup.
Implement retry taxonomy/backoff wiring and watchdog stale-generation failover.
Ensure publish failure after successful upload does not downgrade report status.
Verification: integration scenarios C/D/E/F/G and metrics assertions.
Chunk 9: End-to-End Completion + Gate Closure
Implement/finish tests/integrations/test_reporter_pipeline.py scenarios A-J.
Implement/finish tests/e2e/test_report_download_flow.py Path 1 + Path 2.
Run final verification matrix and close Gate 2 and Gate 3.
Verification: full unit/integration/e2e pass, artifact byte checks, presigned download checks, coverage target >= 80% for reporter.
Public API / Interface Changes
POST /api/v1/scrape/trigger returns 202 Accepted and async semantics.
New Core endpoint: GET /api/v1/scans/{scan_id}/findings/{finding_id}/evidence.
New Reporter endpoints: list/detail/by-scan/download/generate.
Queue/interface updates:
report.jobs: optional report_ids.
New reports.completed contract and queue publish path.
Internal type update: parsed finding includes is_verified and reporting keeps all findings.
Test Plan by Gate
Gate 0: M3 regression suite green before any M4 code merge.
Gate 1: ISS-009 endpoint + updated scraper integration polling test green.
Gate 2: migration + reporter health + report.jobs consumption without crash loop.
Gate 3: first downloadable real PDF from presigned URL with %PDF validation.
Assumptions and Defaults
M4 reports include all findings; is_verified is displayed but not used as a filter.
Worker ingest remains raw-envelope on report.jobs (no producer-side Celery protocol migration).
Migration strategy is additive-only and forward-only.
Chunk merges are sequential; each chunk must pass its own verification before next chunk starts.

## M4 Implementation Plan: Stable Reporter Rollout on Top of M3

### Summary
Implement M4 in phased, test-gated slices so M3 behavior remains intact while adding full report generation and download. We will keep the current `report.jobs` raw-envelope contract, add only backward-compatible schema changes, and introduce Reporter capabilities behind deterministic integration and E2E checks.

### Key Changes
1. **Stability-first sequencing and hard gates**
- Gate 0: lock M3 baseline (`alembic` at `003`, current integration suite green, queue topology healthy).
- Gate 1: ship ISS-009 (`POST /api/v1/scrape/trigger` becomes async `202 Accepted`) and update existing scraper integration tests to polling behavior.
- Gate 2+: proceed only after Gate 1 passes in CI and local compose.

2. **Contracts and DB (backward compatible)**
- Add migration `004_reporter` with only new tables: `reports`, `reproduction_packs`; no edits to existing M1–M3 tables.
- Extend `report.jobs` schema with optional `report_ids` map; keep existing fields and envelope/event type unchanged.
- Add new `reports.completed` schema and publisher path.
- Maintain compatibility rule: organic Core Engine messages continue to work unchanged when `report_ids` is absent.

3. **Core/Scraper API additions required by Reporter**
- Scraper: async trigger endpoint (ISS-009), response shape updated to accepted/background semantics.
- Core Engine: add finding evidence read API for Reporter (`scan_id + finding_id` scoped evidence fetch).
- Core Engine findings API remains compatible; add reporter-needed fields in a non-breaking way (do not remove existing keys).

4. **Reporter service implementation (raw-envelope strategy preserved)**
- Keep raw `report.jobs` ingestion path in worker (per your selection), replacing stub logic with full pipeline execution.
- Implement Reporter modules for: config, parsing/normalization, reproduction pack generation, evidence fetch/embedding, PDF/DOCX renderers, storage upload/presign, completion publisher, watchdog, metrics.
- Generate both formats sequentially per message; update row status per artifact (`completed`/`partial`/`failed`) and preserve terminal states even if publish fails.
- Finding policy: include all scan findings in M4 reports and clearly label them as unverified until M7 verification is live.

5. **Reporter API surface**
- Add endpoints for list/detail/download, list-by-scan, and regenerate (`POST /reports/generate`) with stable `report_ids`.
- Enforce state rules: regenerate allowed for `completed`/`partial`; conflict for non-terminal states.
- Download allowed for `completed` and `partial` only; blocked for `generating`/`failed`.

6. **Runtime and packaging updates**
- Add reporter-specific requirements file and keep heavy report deps scoped to reporter image.
- Keep `PYTHONPATH=/app` and required package `__init__.py` copy behavior in Dockerfile.
- Preserve compose startup dependency `reporter-worker -> reporter:healthy`.

### Public API / Interface Changes
- `POST /api/v1/scrape/trigger` response semantics change to async `202`.
- New Core endpoint for finding evidence retrieval.
- New Reporter endpoints:
  - `GET /api/v1/reports`
  - `GET /api/v1/reports/{report_id}`
  - `GET /api/v1/reports/{report_id}/download`
  - `GET /api/v1/scans/{scan_id}/reports`
  - `POST /api/v1/reports/generate`
- Queue schema updates:
  - `report.jobs`: optional `report_ids`
  - new `reports.completed` payload contract

### Test Plan (must pass before M4 close)
- **Regression guardrail (pre/post M4):**
  - Existing shared, scraper, engine, and current E2E trace tests remain green (with ISS-009 test expectation updates).
- **Reporter unit tests:**
  - schema compatibility, report row lifecycle, severity normalization, fallback reproduction path, temp-file cleanup, renderer output validation, presign behavior.
- **Reporter integration tests:**
  - normal findings, zero-findings, missing evidence object -> partial, evidence-disabled path, upload failure, retries/DLQ behavior, regenerate with stable `report_ids`, organic message without `report_ids`.
- **M4 E2E tests:**
  - Path 1 organic chain (known-vuln-target): scan -> `report.jobs` -> artifacts -> presigned download.
  - Path 2 regenerate chain: stable IDs reused and downloadable artifacts validated by file signatures.

### Assumptions and Defaults
- Reports include all findings for M4, with explicit “unverified” labeling.
- `report.jobs` ingestion remains raw-envelope based (no producer contract refactor to Celery protocol).
- Migration strategy is additive-only; no destructive schema changes.
- Any schema additions are optional-first to avoid breaking M3 producers/consumers.