# AttackBot — Session Context
> Last updated: 2026-03-15
> Purpose: Quick-load context for resuming work mid-session or across sessions.

---

## What Is AttackBot

AttackBot is an automated bug bounty discovery and reporting platform. It scrapes bug bounty
programs from HackerOne (and eventually BugCrowd, Intigriti), runs a multi-stage security
scanning pipeline against each program's scope, discovers vulnerabilities, and generates
reports — all without manual intervention.

---

## Milestone Map

| # | Name | Status |
|---|------|--------|
| M1 | Solid Ground — infrastructure, shared library, service skeletons | ✅ Done |
| M2 | Eyes Open — HackerOne scraper, DB schema, queue publishing | ✅ Done |
| M3 | First Strike — Core Engine scanning pipeline | 🔄 In Progress (testing) |
| M4–M10 | Browser sessions, auth, fuzzing, AI analysis, reporting | 🔲 Not started |

---

## Current State

| Component | Status |
|-----------|--------|
| core-engine `:8002/api/v1/health` | ✅ Healthy |
| core-worker Celery | ✅ Running |
| DB migration (003 head) | ✅ All 12 tables present |
| Scan job → DB row | ✅ Working |
| Stage 0 scope filter | ✅ Working |
| subfinder (`-o` file + `-pc` + `-timeout 30`) | ✅ 40+ subdomains found |
| alterx permutation generation | ✅ Working |
| dnsx DNS resolution | ✅ Working |
| dnsx output parsing | ✅ Fixed (bug #23 — strip `[ip]` suffix) |
| httpx HTTP probing | ⏳ In test with fix applied |
| Assets in DB | ⏳ Expected after current scan |
| Stage 7 → report.jobs | ✅ Confirmed publishing every scan |
| Scraper | ✅ Stopped (manual) — prevent queue flooding |
| RabbitMQ consumer timeout | ✅ Fixed — 6hr via `RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS` |

---

## All Bugs Fixed

| # | Bug | Fix |
|---|-----|-----|
| 1 | Migration duplicate index | Removed duplicate `create_index` from `003_engine.py` |
| 2 | Docker stale cache | Always `--no-cache` after file changes |
| 3 | Dockerfile wget exit code 8 | Pinned version direct URLs (no `/latest/` redirects) |
| 4 | `await init_db()` TypeError | `init_db()` is sync — remove `await` |
| 5 | Typo `database_ur` | Fixed to `database_url` |
| 6 | `HealthStatus.healthy` | Enum is UPPERCASE: `HEALTHY`, `DEGRADED`, `UNHEALTHY` |
| 7 | `HealthResponse` missing `timestamp` | Added `datetime.now(timezone.utc)` |
| 8 | `ScanTimeoutError` missing | Added to `shared/exceptions.py` |
| 9 | `rabbitmq_user` not on config | Use `config.rabbitmq_url` directly |
| 10 | `QueuePublisher` takes string not config | Pass `config.rabbitmq_url` not `config` |
| 11 | `publisher.disconnect()` missing | Method is `publisher.close()` |
| 12 | `str(dict)` invalid JSONB | All dict fields → `json.dumps(dict)` in `repository.py` |
| 13 | Celery "unknown message" | Use `scan_task.apply_async()` not raw publisher |
| 14 | `redis_host`/`redis_port` not on config | Use `config.redis_url` directly |
| 15 | `init_db()` not called in worker | Added `init_db(config.database_url)` in pipeline |
| 16 | `_extract_root_domains()` passing garbage | Filter by `asset_type` — only `domain` + `wildcard_domain` |
| 17 | subfinder ignoring API keys | Added `-pc /app/subfinder-config/provider-config.yaml` |
| 18 | `ports` nested inside `build` in compose | `ports` is sibling of `build`, not child |
| 19 | RabbitMQ ACK timeout (30 min) | `RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS` → 6hr timeout |
| 20 | Scraper flooding queue | Stop scraper during testing |
| 21 | subfinder stdout buffered in non-TTY | Use `-o <file>` output instead of stdout pipe |
| 22 | subfinder sources hanging indefinitely | Added `-timeout 30` per-source timeout flag |
| 23 | dnsx `-resp` output includes `[ip]` suffix | Parse with `.split()[0]` to strip IP portion |

---

## Current Test — dnsx Fix (#23)

dnsx with `-resp` outputs: `api.hackerone.com [1.2.3.4]`
The `[1.2.3.4]` was being passed to httpx as part of the hostname → httpx found nothing → 0 assets.

```python
# OLD (broken):
live_domains = [l.strip() for l in dnsx_stdout.splitlines() if l.strip()]

# NEW (fixed):
live_domains = [
    l.strip().split()[0]   # strip " [1.2.3.4]" suffix
    for l in dnsx_stdout.splitlines() if l.strip()
]
```

After this fix httpx should take 30-60s probing real hosts, and assets should appear in DB.

---

## Subfinder Invocation Pattern (correct)

Subfinder buffers stdout when not attached to a TTY — never use stdout pipe.
Always use `-o <file>` and read the file after completion:

```python
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
    subfinder_out = tf.name
try:
    await run_tool_communicate(
        args=["subfinder", "-d", domain, "-all",
              "-pc", "/app/subfinder-config/provider-config.yaml",
              "-timeout", "30",
              "-o", subfinder_out],
        timeout=config.subfinder_timeout,
        label=f"subfinder[{domain}]",
    )
    with open(subfinder_out) as f:
        subfinder_lines = f.read().splitlines()
finally:
    os.unlink(subfinder_out)
subdomains = list({line.strip() for line in subfinder_lines if line.strip()})
```

---

## Next Steps

1. Confirm assets appear in DB after current scan
2. Re-enable nuclei, web_vuln_tests, js_secrets one at a time
3. Verify findings in DB
4. Confirm report.jobs message on every completed scan
5. Restart scraper → let it queue real programs
6. M3 done → begin M4 (Reporter)

---

## Before Every Test Scan — Clean State

```powershell
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("USER:PASS"))
Invoke-WebRequest -Method DELETE "http://localhost:15672/api/queues/%2F/scan.jobs/contents" -Headers @{Authorization="Basic $cred"} -UseBasicParsing
docker compose -f infra/docker-compose.yml --env-file .env exec redis redis-cli FLUSHDB
docker compose -f infra/docker-compose.yml --env-file .env exec postgres psql -U attackbot -d attackbot -c "UPDATE scans SET status = 'cancelled' WHERE status = 'running';"
```

## Trigger Test Scan (minimal flags)

```powershell
Invoke-WebRequest -Method POST http://localhost:8002/api/v1/scans/start `
  -ContentType "application/json" -UseBasicParsing `
  -Body '{"program_id":"6976c79f-23d5-4d8a-a098-402e9ce565ad","platform":"hackerone","handle":"security","scope":{"in_scope":[{"asset_type":"domain","value":"hackerone.com"}],"out_of_scope":[]},"feature_flags":{"sqli":false,"ssrf":false,"crlf":false,"nuclei":false,"browser_session":false,"api_fuzzing":false}}'
```

## Docker Commands

```powershell
docker compose -f infra/docker-compose.yml --env-file .env build core-worker
docker compose -f infra/docker-compose.yml --env-file .env up -d core-worker
docker compose -f infra/docker-compose.yml --env-file .env logs core-worker -f
.\inspect_scan.ps1
```

## Test Program Reference

| Field | Value |
|-------|-------|
| program_id | `6976c79f-23d5-4d8a-a098-402e9ce565ad` |
| handle | `security` (HackerOne's own program) |
| platform | `hackerone` |
| test scope | `{"asset_type": "domain", "value": "hackerone.com"}` |