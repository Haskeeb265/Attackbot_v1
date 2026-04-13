# AttackBot — Codebase Defaults

> This document defines the conventions, patterns, and practices used across the AttackBot codebase.
> Every file added to this project should follow these defaults. When in doubt, look here first.

---

## 1. Project Structure

```
attackbot/
├── backend/
│   ├── shared/          ← shared library, imported by all services
│   ├── services/        ← one directory per service
│   │   ├── scraper/
│   │   ├── core_engine/
│   │   └── ...
│   └── migrations/      ← Alembic, standalone build context
├── infra/               ← docker-compose, prometheus, grafana, loki
├── scripts/             ← operational one-off scripts
└── tests/
    ├── unit/
    └── integration/
```

**Rules:**
- Service directories use `snake_case` — they are Python packages and must be importable
- Docker service names in `docker-compose.yml` use `kebab-case` — these are labels only
- No business logic in `backend/shared/` — only utilities that every service needs
- No cross-service imports — services communicate via REST APIs or message queues only

---

## 2. Naming Conventions

### Files and Directories
| Thing | Convention | Example |
|-------|-----------|---------|
| Python packages / directories | `snake_case` | `core_engine/`, `scope_filter.py` |
| Docker service names | `kebab-case` | `core-engine`, `api-fuzzer-worker` |
| YAML scenario files | `snake_case` | `login_basic.yaml`, `race_transfer.yaml` |
| Migration files | `NNN_description.py` | `002_scraper_full.py` |
| Test files | `test_{module}.py` | `test_scraper.py` |
| Config files (infra) | `kebab-case` or tool default | `loki-config.yml`, `prometheus.yml` |

### Python
| Thing | Convention | Example |
|-------|-----------|---------|
| Classes | `PascalCase` | `ScopeFilter`, `QueuePublisher` |
| Functions / methods | `snake_case` | `compute_dedup_hash()`, `get_session()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_PROMPT_TOKENS`, `SEVERITY_RANK` |
| Private methods | `_single_leading_underscore` | `_async_scan_task()` |
| Type aliases | `PascalCase` | `ScanResult = dict[str, Any]` |
| Pydantic models | `PascalCase` | `ScanJobsPayload`, `HealthResponse` |

### Database
| Thing | Convention | Example |
|-------|-----------|---------|
| Table names | `snake_case`, plural | `programs`, `scan_stages`, `finding_evidence` |
| Column names | `snake_case` | `program_id`, `queued_for_scan`, `created_at` |
| Primary keys | `{table_singular}_id` | `program_id`, `scan_id`, `finding_id` |
| Foreign keys | `{referenced_table_singular}_id` | `program_id UUID FK → programs` |
| Timestamp columns | `_at` suffix | `created_at`, `started_at`, `last_scraped_at` |
| Boolean columns | `is_` or verb prefix | `is_verified`, `is_active`, `queued_for_scan` |
| JSONB columns | singular noun | `feature_flags`, `severity_breakdown`, `parameters` |

### RabbitMQ Queues
| Thing | Convention | Example |
|-------|-----------|---------|
| Work queues | `{noun}.jobs` | `scan.jobs`, `report.jobs`, `verify.jobs` |
| DLQ | `{queue}.dlq` | `scan.jobs.dlq` |
| Event topics | `{noun}.{past_tense_verb}` | `reports.completed` |

---

## 3. Service Structure

Every FastAPI service follows this exact layout:

```
services/my_service/
├── __init__.py
├── Dockerfile
├── config.py          ← service-specific config (subclasses BaseServiceConfig)
├── main.py            ← FastAPI app, lifespan, health endpoint, routes
└── worker.py          ← Celery app (if service has a worker)
```

As a service grows in later milestones, add subdirectories:
```
services/core_engine/
├── pipeline/          ← one file per pipeline stage
├── repository.py      ← DB queries for this service
└── models.py          ← internal dataclasses (not DB models)
```

**Rules:**
- `main.py` owns the FastAPI `app` instance and the `lifespan` context manager
- `config.py` owns the `Settings` class for that service — never inline config in `main.py`
- Route handlers in `main.py` for small services; move to `routes/` only when file exceeds ~200 lines
- `worker.py` owns the Celery `app` instance — never import from `main.py` into `worker.py`

---

## 4. Dockerfile Pattern

Every service Dockerfile follows this exact structure — no variations:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py
COPY backend/services/my_service /app/backend/services/my_service

ENV PYTHONPATH=/app

EXPOSE 800X

CMD ["uvicorn", "backend.services.my_service.main:app", "--host", "0.0.0.0", "--port", "800X"]
```

**Rules:**
- Build context is always the repo root (`context: ..` in compose) — never the service directory
- `backend/shared` is always copied — it is the shared library, not a package installed via pip
- `PYTHONPATH=/app` is always set — this makes `from backend.shared.x import y` work
- Python version is always `3.12-slim` — no exceptions, no `-alpine` (Playwright needs glibc)
- Celery worker CMD: `["celery", "-A", "backend.services.X.worker", "worker", "-Q", "queue.name", "-c", "N", "--loglevel=info"]`

---

## 5. Configuration Pattern

Every service defines its own config class that subclasses `BaseServiceConfig`:

```python
# backend/services/my_service/config.py
from backend.shared.config import BaseServiceConfig

class MyServiceConfig(BaseServiceConfig):
    service_name: str = "my-service"
    port: int = 800X
    # service-specific fields with defaults
    some_timeout: int = 30
```

**Rules:**
- `BaseServiceConfig` provides: `database_url`, `redis_url`, `rabbitmq_url`, `vault_url`, `minio_*`, `log_level`, `db_pool_size`, `db_max_overflow`
- All config values come from environment variables — Pydantic Settings handles this automatically
- Never hardcode credentials, URLs, or secrets anywhere in Python files
- Service-specific config fields always have sensible defaults — the service must start with only the base `.env` values
- Instantiate config at module level in `main.py`: `settings = MyServiceConfig()`

---

## 6. Logging Pattern

```python
from backend.shared.logging import configure_logging, get_logger

# At module level in main.py, after settings are instantiated:
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

# Usage — always keyword arguments for context, never f-strings:
log.info("scan_started", scan_id=str(scan_id), program=handle)
log.warning("rate_limited", platform="hackerone", retry_after=60)
log.error("stage_failed", stage=4, error=str(e), scan_id=str(scan_id))
```

**Rules:**
- `configure_logging()` is called exactly once per process, at startup in `main.py` or `worker.py`
- Every log call uses an `event` string as the first positional argument — short, `snake_case`, past tense
- Context goes as keyword arguments — never interpolate into the event string itself
- Never use `print()` anywhere in application code
- Never use `logging.basicConfig()` directly — always go through `configure_logging()`
- Log levels: `debug` = internal state; `info` = lifecycle events; `warning` = degraded but continuing; `error` = failed but recoverable; `critical` = cannot start/continue

---

## 7. Health Endpoint Pattern

Every FastAPI service exposes exactly this endpoint at exactly this path:

```python
@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_ok = await check_db_health()
    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        )
    }
    overall = (
        HealthStatus.HEALTHY
        if all(c.status == HealthStatus.HEALTHY for c in components.values())
        else HealthStatus.UNHEALTHY
    )
    return HealthResponse(
        status=overall,
        service=settings.service_name,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )
```

**Rules:**
- Path is always `/api/v1/health` — never `/health`, `/healthz`, or `/status`
- Always check real dependencies — never return hardcoded `healthy`
- Add a component per dependency (database, rabbitmq, neo4j, etc.) as the service grows
- Docker healthcheck always hits this endpoint: `curl -f http://localhost:800X/api/v1/health`

---

## 8. Message Queue Pattern

### Publishing
```python
from backend.shared.queue import QueuePublisher
from backend.shared.schemas.scan_jobs import build_scan_job_message

publisher = QueuePublisher(settings.rabbitmq_url)

message = build_scan_job_message(
    program_id=str(program.program_id),
    platform=program.platform,
    # ...
)

success = await publisher.publish(Queues.SCAN_JOBS, message)
if not success:
    # Always handle publish failure — set queued_for_scan=True or equivalent
    await repository.mark_queued(program.program_id)
```

### Message contracts
- Always use `build_*_message()` factory functions — never construct envelope dicts manually
- `MessageEnvelope` fields are auto-populated: `event_id` (UUID), `timestamp` (UTC), `schema_version`
- Payload models use `model_config = ConfigDict(extra="ignore")` — forward compatibility

**Rules:**
- Always declare queues passively (`passive=True`) — avoids argument mismatch errors on redeclare
- Always handle publish failure at the call site — the publisher returns `bool`, never raises
- Publish failure path must set a flag (e.g. `queued_for_scan=True`) for the reconciler to retry
- Never publish to a queue that doesn't have a corresponding DLQ defined in `Queues`

---

## 9. Database Pattern

```python
from backend.shared.db import get_session

async def my_repository_function(program_id: UUID) -> Program | None:
    async with get_session() as session:
        result = await session.execute(
            select(Program).where(Program.program_id == program_id)
        )
        return result.scalar_one_or_none()
```

**Rules:**
- Always use `async with get_session()` — never manage engine/session lifecycle manually
- `get_session()` auto-commits on success, auto-rolls back on exception
- Use `insert(...).on_conflict_do_update(...)` for upserts — never SELECT then INSERT
- Never use `session.add()` for bulk operations — use `execute(insert(...))` with `values()`
- UUID primary keys everywhere — never integer sequences for cross-service entities
- All timestamps stored as `TIMESTAMPTZ` — always use `datetime.now(timezone.utc)` in Python

---

## 10. Exception Handling Pattern

```python
from backend.shared.exceptions import ScanError, ScopeFatalError, CollectorRateLimitError

# Fatal errors (stop the pipeline):
raise ScopeFatalError("Scope resolution failed — no in-scope assets found")

# Recoverable errors (log + continue):
try:
    result = await run_stage(scan_ctx)
except ScanError as e:
    log.warning("stage_failed_non_fatal", stage=stage_num, error=str(e))
    scan_ctx.partial_failures.append(stage_num)
    # continue to next stage

# Always use the hierarchy — never raise bare Exception in application code
```

**Exception hierarchy:**
```
AttackBotError
├── ScanError
│   ├── ScanTimeoutError
│   └── ScanInternalError
├── ScopeFatalError          ← always fatal, stops the scan
├── QueueError
│   ├── QueueConnectionError
│   └── QueuePublishError
├── StorageError
├── CollectorError
│   ├── CollectorRateLimitError
│   └── CollectorAuthError
└── MessageSchemaError
```

**Rules:**
- Never catch `Exception` broadly without re-raising or logging at `error` level
- Fatal pipeline errors (`ScopeFatalError`, `ScanInternalError`) always transition scan state before raising
- `CollectorRateLimitError` must always trigger retry with `Retry-After` delay — never ignore 429s

---

## 11. Subprocess / CLI Tool Pattern

For short-output tools (nuclei, ffuf):
```python
async def run_tool(targets: list[str], scan_id: str, timeout: int = 3600) -> list[dict]:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
        tf.write('\n'.join(targets))
        targets_path = tf.name
    try:
        proc = await asyncio.create_subprocess_exec(
            "tool", "-l", targets_path, "-j",  # always list, never shell string
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()  # always wait after kill
            raise ScanTimeoutError(f"tool timed out after {timeout}s")
        return [json.loads(l) for l in stdout.decode().splitlines() if l.strip().startswith("{")]
    finally:
        os.unlink(targets_path)
```

For large-output tools (subfinder, amass):
```python
# Use streaming readline — never communicate() for large output
async for line in proc.stdout:
    results.append(json.loads(line.decode().strip()))
```

**Rules:**
- Always `create_subprocess_exec` with args as a list — never `shell=True`
- Always use `communicate()` for bounded output — it prevents pipe buffer deadlocks
- Always `proc.kill()` then `await proc.wait()` on timeout — kill alone leaks the process
- Always clean up temp files in `finally` blocks
- `nuclei` exits 1 on zero findings — only treat `returncode > 1` as an error
- Always pipe `stderr` — never leave it unread (causes deadlocks on stderr-heavy tools)

---

## 12. Celery Worker Pattern

```python
app = Celery("service-name", broker=settings.rabbitmq_url, backend=settings.redis_url)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,           # ack only after task completes — prevents message loss on crash
    worker_prefetch_multiplier=1,  # one task at a time — tasks are long-running
    task_reject_on_worker_lost=True,
    task_default_queue="queue.name",
)

@app.task(name="task_name", bind=True, max_retries=3)
def my_task(self, message: dict) -> None:
    # For async work, delegate to asyncio:
    asyncio.run(_async_task(message))
```

**Rules:**
- `task_acks_late=True` is mandatory on all workers — this is what prevents dropped messages on crash
- `worker_prefetch_multiplier=1` is mandatory on scan/verify workers — tasks can run for hours
- Always `bind=True` on tasks that need retry access (`self.retry()`)
- Always delegate async work to `asyncio.run()` — Celery tasks are synchronous entry points
- Never share state between task invocations — each task is isolated

---

## 13. API Versioning

All API paths are prefixed with `/api/v1/`:

```
GET  /api/v1/health
GET  /api/v1/programs
GET  /api/v1/programs/{program_id}
POST /api/v1/scans/start
GET  /api/v1/scans/{scan_id}/findings
```

**Rules:**
- No unversioned paths — `/health` is wrong, `/api/v1/health` is correct
- No trailing slashes
- Resource names are plural nouns: `/programs`, `/scans`, `/findings`, `/reports`
- Sub-resources use nesting: `/scans/{scan_id}/findings` not `/findings?scan_id=...`
- Actions that aren't CRUD use a verb: `/scrape/trigger`, `/scan-jobs/trigger`

---

## 14. Test Conventions

```python
# Unit test class naming: Test{ThingBeingTested}
class TestScopeFilter:
    def test_wildcard_matches_subdomain(self): ...
    def test_exact_match_passes(self): ...
    def test_out_of_scope_rejected(self): ...

# Integration test class naming: Test{FlowBeingTested}
class TestScrapePipeline:
    async def test_full_scrape_produces_db_rows(self): ...
```

**Rules:**
- Unit tests mock all I/O — no real DB, network, or filesystem
- Integration tests use real infrastructure (Docker Compose test profile or the running stack)
- Integration tests are skipped if required env vars are not set — never fail on missing infra
- Test method names describe the scenario: `test_{condition}_{expected_result}`
- One assertion per test where practical — multiple assertions allowed when they test one logical thing
- Coverage targets: shared library ≥ 80%, FastAPI services ≥ 80%, Celery workers ≥ 75%

---

## 15. Alembic Migration Conventions

```python
# Migration file header always includes:
"""
{description}

Revision ID: {auto}
Revises: {parent}
Create Date: {auto}

Tables created: programs, program_scopes
Tables modified: —
"""
```

**Rules:**
- One migration per milestone's schema work — never one migration per table
- Migrations are always forward-only for now — `downgrade()` body is `pass` until production
- Never modify a previously applied migration file — always create a new revision
- Migration filenames: `NNN_description.py` where NNN is zero-padded (001, 002, 003...)
- Always use `op.create_index()` for foreign keys and commonly filtered columns in the same migration

---

## 16. Security Rules (Non-Negotiable)

- **Never** `mc anonymous set download` on any MinIO bucket — all access via pre-signed URLs
- **Never** store credentials in Python files, YAML files, or Docker compose env values — use Vault or environment variables loaded from `.env`
- **Never** commit `.env` — only `.env.example` is committed
- **Always** encrypt session data (cookies, tokens) before writing to database — AES-256 via `storage.py`
- **Always** validate scope at Stage 0 before any scan work begins — fatal on failure
- **Never** use `shell=True` in subprocess calls — always pass args as a list
- **Always** resolve TOTP secrets from Vault at runtime — never store in YAML scenario files
---

## 17. Lessons from M2 — Mistakes and How to Prevent Them

These are real errors that occurred during M2 implementation. They are recorded here so they never repeat.

---

### Mistake 1 — `__init__.py` files must always be empty unless explicitly required

**What happened:** `backend/services/scraper/__init__.py` was generated with an import inside it, which caused a circular import chain on test collection. Python tries to execute every `__init__.py` in the package path when resolving an import. An import inside a package `__init__.py` that itself imports from the same package creates a loop.

**Rule:** Every `__init__.py` in this project is empty unless there is an explicit, documented reason to put something in it. The one exception is `collectors/__init__.py` — but even that was cleared to empty once `main.py` was confirmed to handle the self-registration import directly.

**Prevention:** When creating a new `__init__.py`, default content is nothing. Zero bytes. If you find yourself putting an import in one, stop and ask why `main.py` or the caller can't do it instead.

---

### Mistake 2 — Always read the actual signature of shared functions before calling them

**What happened:** `publisher.py` called `build_scan_job_message()` with flat keyword arguments (`program_id=`, `platform=`, `handle=`, `in_scope=`, `out_of_scope=`). The actual M1 signature takes a single `ScanJobsPayload` object. This caused a `TypeError` at runtime that only surfaced during tests — not during writing.

**The correct call pattern:**
```python
from backend.shared.schemas.scan_jobs import build_scan_job_message, ScanJobsPayload, ScopeDefinition, ScopeEntry

message = build_scan_job_message(
    ScanJobsPayload(
        program_id=program_id,
        platform=program.platform,
        handle=program.handle,
        scope=ScopeDefinition(
            in_scope=[ScopeEntry(asset_type="domain", value=v) for v in in_scope],
            out_of_scope=[ScopeEntry(asset_type="domain", value=v) for v in out_of_scope],
        ),
    )
)
```

**Rule:** Before calling any function from `backend/shared/`, read its actual source file first. Never assume the signature from memory or from the spec doc — the implemented signature is the truth. This applies especially to: `build_scan_job_message()`, `build_report_job_message()`, `build_envelope()`, `get_session()`, `init_db()`.

---

### Mistake 3 — When replacing `shared/exceptions.py`, audit all existing imports first

**What happened:** M2 delivered a new `shared/exceptions.py` that was missing `QueueConnectionError`. The existing M1 `shared/queue.py` imported this name. The result was an `ImportError` that failed 8 tests — all of which were testing unrelated publisher/reconciler logic.

**Rule:** Before replacing or modifying any file in `backend/shared/`, grep for every name currently imported from it across the entire codebase:

```powershell
# Find everything imported from exceptions.py
grep -r "from backend.shared.exceptions import" backend/
```

Every name found in those imports must exist in the new version. Never remove an existing exception class — only add new ones.

---

### Mistake 4 — Check `requirements/base.txt` before adding dependencies

**What happened:** `m2_additions.txt` specified `redis[asyncio]==5.0.1` as a new dependency, but `base.txt` already had `redis[hiredis]==5.0.4`. Pip cannot install two versions of the same package — the build failed immediately.

**Rule:** Before specifying any new dependency for a milestone, run:

```powershell
grep "redis\|celery\|sqlalchemy\|pydantic\|fastapi" backend/requirements/base.txt
```

If the package already exists at any version, do not add it again. If the existing version lacks a feature you need (e.g. asyncio support), verify whether it's already included in the installed version rather than adding a duplicate pin.

---

### Mistake 5 — Never create files on Windows with `echo $null` or PowerShell redirection operators

**What happened:** `echo $null > file.py` on PowerShell writes a UTF-16 BOM header. Python's import system cannot decode this and raises `SyntaxError: (unicode error) 'utf-8' codec can't decode byte 0xff`.

**The only safe way to create an empty file on Windows PowerShell:**
```powershell
[System.IO.File]::WriteAllText("$PWD\path\to\file.py", "")
```

**Rule:** Never use `echo`, `>`, or `>>` to create Python files on Windows. Use `.WriteAllText()` for empty files, or write content directly in the editor.

---

### Mistake 6 — Verify delivered files landed as `.py` files, not directories

**What happened:** `hackerone.py` was delivered as a folder named `hackerone` instead of a file named `hackerone.py`. Python's import resolution found the directory but not the module inside it, producing `ModuleNotFoundError: No module named 'backend.services.scraper.collectors.hackerone'`.

**Diagnostic command — run this after receiving any file delivery:**
```powershell
docker run --rm -v "${PWD}/backend:/app/backend" python:3.12-slim find /app/backend/services -type d
```

Any unexpected directory name in the output (e.g. `hackerone` where `hackerone.py` was expected) means a file was created as a folder. Delete the folder and recreate the file.

**Rule:** After placing any new `.py` file into the project, confirm it is a file, not a directory, before running tests.
