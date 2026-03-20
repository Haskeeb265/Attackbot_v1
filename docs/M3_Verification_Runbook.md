# M3 Verification Runbook

## Prerequisites
- Docker Desktop is running.
- Local Postgres service is stopped so Docker Postgres can bind `5432`.
- `.env` has valid scraper credentials when real scrape refresh is needed:
  - `HACKERONE_API_USERNAME`
  - `HACKERONE_API_TOKEN`
- Services are up:
  - `docker compose -f infra/docker-compose.yml up -d postgres redis rabbitmq scraper core-engine core-worker`
- Migrations are applied:
  - `docker compose -f infra/docker-compose.yml run --rm migrate`

## Commands
- Unit sanity:
  - `python -m pytest tests\unit -v`
- M3 remaining verification:
  - `python -m pytest tests\integrations\test_m3_verification.py -v`
- Existing integration regression:
  - `python -m pytest tests\integrations -v`

## Expected Outputs
- `test_waybackurls_available_in_core_worker` passes (`waybackurls` executable in `core-worker`).
- `test_full_scan_fetches_scope_from_scraper` passes with non-`failed_scope` terminal status and stage rows present.
- `test_watchdog_republish_and_retry_increment` passes with:
  - stale scan `status='failed_internal'`
  - stale scan `retry_count=1`
  - republish evidence (new scan activity for same `program_id`)
- `test_empty_scope_program_transitions_failed_scope` passes with:
  - terminal `status='failed_scope'`
  - `error_detail` showing missing `in_scope`
  - zero downstream `scan_stages` for that scan

