"""
AttackBot Scraper Service — main.py

Replaces the M1 skeleton. Wires together:
  - DB init
  - Redis distributed locking
  - Collector registry
  - ProgramRepository + ScraperPublisher
  - Reconciler
  - APScheduler (scrape + reconcile jobs)
  - FastAPI routes (health, scrape/trigger, programs CRUD)

PITFALL: The collector uses synchronous `requests`. Always run via
`loop.run_in_executor(None, fn)` — never call directly in async context.
"""

import asyncio # this library is used for event loops, coroutines, and non-blocking I/O operations in Python. It allows for concurrent programming and is essential for the asynchronous operations in this scraper service.
from contextlib import asynccontextmanager # this libray is used for setting up an async context manager, which is utilized in the lifespan of the FastAPI application to manage resources like database connections, Redis clients, and schedulers. It ensures that these resources are properly initialized when the application starts and cleaned up when it shuts down.
from datetime import datetime, timezone # i know
from uuid import UUID # i know

import redis.asyncio as aioredis # this is used for async redis client. it lets the scraper service interact with Redis for distributed locking and other operations without blocking the event loop, which is crucial for maintaining responsiveness in an async application.
from apscheduler.schedulers.asyncio import AsyncIOScheduler # this library is used for scheduling tasks in an asynchronous context. In this scraper service, it is used to schedule periodic scraping of platforms and reconciliation tasks without blocking the main application thread, allowing for efficient background processing. Similar to a cron job scheduler but designed for async applications.
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query # this libraby is used for building the web API of the scraper service. FastAPI is a modern, fast web framework for building APIs with Python. BackgroundTasks allows for running tasks in the background without blocking the request-response cycle. HTTPException is used for handling errors and returning appropriate HTTP status codes. Query is used for parsing and validating query parameters in API endpoints.

from backend.services.scraper.collectors import hackerone  # noqa: F401 
from backend.services.scraper.collectors.base import CollectorRegistry
from backend.services.scraper.config import ScraperConfig
from backend.services.scraper.models import Program, ProgramScope
from backend.services.scraper.publisher import ScraperPublisher
from backend.services.scraper.reconciler import Reconciler
from backend.services.scraper.repository import ProgramRepository
from backend.services.scraper.scope_parser import ScopeParser
from backend.shared.db import check_db_health, init_db
from backend.shared.health import ComponentHealth, HealthResponse, HealthStatus
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import Queues, check_rabbitmq_health, ensure_queue_topology

settings = ScraperConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

# Module-level singletons — initialized in lifespan
_redis: aioredis.Redis | None = None
_scheduler: AsyncIOScheduler | None = None
_publisher: ScraperPublisher | None = None
_repository: ProgramRepository | None = None
_reconciler: Reconciler | None = None
_scope_parser: ScopeParser = ScopeParser()


# ---------------------------------------------------------------------------
# Core scrape logic
# ---------------------------------------------------------------------------

async def _run_platform_scrape(platform: str) -> dict:
    """
    Core scrape logic for one platform.
    Acquires Redis lock, runs collector (in executor), and upserts metadata.
    Does not publish scan jobs.
    Called by APScheduler and by POST /scrape/trigger.
    """
    lock_key = f"scraper:lock:{platform}"
    lock = _redis.lock(lock_key, timeout=settings.platform_lock_ttl_seconds)

    acquired = await lock.acquire(blocking=False)
    if not acquired:
        log.info("scrape_skipped_locked", platform=platform)
        return {"status": "skipped", "reason": "lock_held", "platform": platform}

    try:
        collector_cls = CollectorRegistry.get(platform)

        # Build collector with credentials
        if platform == "hackerone":
            collector = collector_cls(
                api_username=settings.hackerone_api_username,
                api_token=settings.hackerone_api_token,
                max_retries=settings.collector_max_retries,
                page_size=settings.collector_page_size,
            )
        else:
            raise ValueError(f"No credential setup for platform: {platform!r}")

        log.info("scrape_started", platform=platform)

        # Run in threadpool — collector uses sync requests library
        loop = asyncio.get_event_loop()
        raw_programs = await loop.run_in_executor(None, collector.fetch_listing)

        upserted = 0
        errors = 0

        for raw in raw_programs:
            try:
                # Fetch full details (scopes, policy) — sync, run in executor
                raw_detail = await loop.run_in_executor(
                    None, collector.fetch_details, raw.handle
                )
                program = collector.normalize(raw_detail)
                program.scopes = _scope_parser.parse(program.scopes)

                await _repository.upsert(program)
                upserted += 1

            except Exception as e:
                log.error("program_scrape_failed", handle=raw.handle, error=str(e))
                errors += 1
                continue

        log.info(
            "scrape_completed",
            platform=platform,
            upserted=upserted,
            errors=errors,
        )
        return {
            "status": "completed",
            "platform": platform,
            "upserted": upserted,
            # Startup/triggered scrape now performs metadata sync only.
            "published": 0,
            "errors": errors,
        }

    finally:
        await lock.release()


async def _publish_due_scan_jobs(batch_size: int | None = None) -> dict:
    """
    Publish a bounded batch of background scan jobs for programs due for rescan.
    This path is intentionally decoupled from metadata scraping.
    """
    # Startup-time control flag: pause background autonomous publishing for
    # deterministic E2E runs. This value is read from env at process start.
    if settings.e2e_pause_reconciler:
        log.info(
            "scan_publish_batch_paused",
            reason="E2E_PAUSE_RECONCILER is enabled",
            queue=Queues.SCAN_JOBS,
        )
        return {
            "status": "paused",
            "queue": Queues.SCAN_JOBS,
            "attempted": 0,
            "published": 0,
            "failed": 0,
        }

    effective_batch_size = (
        settings.scraper_scan_publish_batch_size
        if batch_size is None
        else int(batch_size)
    )
    due_programs = await _repository.get_programs_due_for_scan(
        interval_minutes=settings.scraper_scan_publish_interval_minutes,
        batch_size=effective_batch_size,
    )

    published = 0
    failed = 0

    for row in due_programs:
        program_id = row["program_id"]
        scope_rows = await _repository.get_scope(program_id)
        scopes = [
            ProgramScope(
                scope_type=scope["scope_type"],
                asset_type=scope["asset_type"],
                value=scope["value"],
                notes=scope.get("notes"),
            )
            for scope in scope_rows
        ]
        program = Program(
            platform=row["platform"],
            handle=row["handle"],
            name=row.get("name") or row["handle"],
            scopes=scopes,
        )

        success = await _publisher.publish_scan_job(program_id, program)
        if success:
            published += 1
        else:
            failed += 1

    log.info(
        "scan_publish_batch_completed",
        attempted=len(due_programs),
        published=published,
        failed=failed,
        queue=Queues.SCAN_JOBS,
    )
    return {
        "status": "completed",
        "queue": Queues.SCAN_JOBS,
        "attempted": len(due_programs),
        "published": published,
        "failed": failed,
    }


# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis, _scheduler, _publisher, _repository, _reconciler
    settings.require_fields(["database_url", "redis_url", "rabbitmq_url"])

    # Init DB
    init_db(settings.database_url, settings.db_pool_size, settings.db_max_overflow)

    # Init Redis
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    # Init repository and publisher
    _repository = ProgramRepository()
    _publisher = ScraperPublisher(
        settings.rabbitmq_url,
        _repository,
        # Startup-time evaluation from env; changes require container restart.
        scan_timeout_seconds=settings.scaled_scan_timeout_seconds(14_400),
    )
    await ensure_queue_topology(settings.rabbitmq_url)
    await _publisher.connect()

    # Init reconciler
    _reconciler = Reconciler(
        _repository,
        _publisher,
        settings.reconciler_max_age_days,
        paused=settings.e2e_pause_reconciler,
    )
    if settings.e2e_pause_reconciler:
        log.info(
            "e2e_reconciler_pause_enabled",
            note="Reconciler and background scan publish batches are paused",
        )

    # Init scheduler
    _scheduler = AsyncIOScheduler()

    # HackerOne scheduled scrape job
    if settings.hackerone_api_username and settings.hackerone_api_token:
        _scheduler.add_job(
            _run_platform_scrape,
            "interval",
            args=["hackerone"],
            seconds=settings.hackerone_scrape_interval_seconds,
            id="scrape_hackerone",
            replace_existing=True,
        )
        log.info(
            "scheduler_job_added",
            platform="hackerone",
            interval_seconds=settings.hackerone_scrape_interval_seconds,
        )
    else:
        log.warning(
            "hackerone_credentials_missing",
            note="HackerOne scraping disabled — set HACKERONE_API_USERNAME and HACKERONE_API_TOKEN",
        )

    # Reconciler job — runs every 5 minutes regardless of credentials
    _scheduler.add_job(
        _reconciler.reconcile,
        "interval",
        seconds=settings.reconciler_interval_seconds,
        id="reconciler",
        replace_existing=True,
    )

    _scheduler.add_job(
        _publish_due_scan_jobs,
        "interval",
        minutes=settings.scraper_scan_publish_interval_minutes,
        id="scan_publish_batch",
        replace_existing=True,
        max_instances=1,
    )
    log.info(
        "scheduler_job_added",
        job="scan_publish_batch",
        interval_minutes=settings.scraper_scan_publish_interval_minutes,
        batch_size=settings.scraper_scan_publish_batch_size,
        queue=Queues.SCAN_JOBS,
    )

    _scheduler.start()
    log.info("scraper_started")
    yield

    _scheduler.shutdown(wait=False)
    await _redis.aclose()
    log.info("scraper_shutdown")


app = FastAPI(title="AttackBot Scraper", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_ok = await check_db_health()
    redis_ok = False
    if _redis is not None:
        try:
            redis_ok = bool(await _redis.ping())
        except Exception:
            redis_ok = False
    rabbitmq_ok = await check_rabbitmq_health(
        settings.rabbitmq_url,
        [Queues.SCAN_JOBS],
    )
    scheduler_ok = _scheduler is not None and _scheduler.running
    credentials_ok = bool(
        settings.hackerone_api_username
        and settings.hackerone_api_token
        and settings.hackerone_api_username.lower() != "placeholder"
        and settings.hackerone_api_token.lower() != "placeholder"
    )

    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        ),
        "redis": ComponentHealth(
            status=HealthStatus.HEALTHY if redis_ok else HealthStatus.UNHEALTHY
        ),
        "rabbitmq": ComponentHealth(
            status=HealthStatus.HEALTHY if rabbitmq_ok else HealthStatus.UNHEALTHY
        ),
        "scheduler": ComponentHealth(
            status=HealthStatus.HEALTHY if scheduler_ok else HealthStatus.UNHEALTHY
        ),
        "platform_credentials": ComponentHealth(
            status=HealthStatus.HEALTHY if credentials_ok else HealthStatus.DEGRADED,
            detail=(
                None if credentials_ok
                else "HackerOne credentials are not configured; live scraping is disabled."
            ),
        ),
    }
    statuses = [component.status for component in components.values()]
    if any(status == HealthStatus.UNHEALTHY for status in statuses):
        overall = HealthStatus.UNHEALTHY
    elif any(status == HealthStatus.DEGRADED for status in statuses):
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.HEALTHY
    return HealthResponse(
        status=overall,
        service=settings.service_name,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )


# ---------------------------------------------------------------------------
# Scrape trigger
# ---------------------------------------------------------------------------

@app.post("/api/v1/scrape/trigger", status_code=202)
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    platform: str = "hackerone",
) -> dict:
    """
    Trigger an immediate scrape for a platform in the background.
    Caller should poll /api/v1/programs for completion effects.
    """
    if platform not in CollectorRegistry.all_platforms():
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform!r}")
    background_tasks.add_task(_run_platform_scrape, platform)
    return {
        "status": "accepted",
        "platform": platform,
        "message": "Scrape started in background",
    }


@app.post("/api/v1/scan-jobs/trigger")
async def trigger_scan_publish_batch(
    batch_size: int | None = Query(default=None, ge=1, le=500),
) -> dict:
    """
    Trigger an immediate bounded background publish batch for due programs.
    """
    return await _publish_due_scan_jobs(batch_size=batch_size)


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------

@app.get("/api/v1/programs")
async def list_programs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    platform: str | None = None,
    is_active: bool | None = None,
) -> dict:
    return await _repository.list_programs(page, page_size, platform, is_active)


@app.get("/api/v1/programs/{program_id}")
async def get_program(program_id: UUID) -> dict:
    program = await _repository.get_by_id(program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@app.get("/api/v1/programs/{program_id}/scope")
async def get_program_scope(program_id: UUID) -> dict:
    scope = await _repository.get_scope(program_id)
    return {
        "program_id": str(program_id),
        "scope": scope,
        "in_scope": [s for s in scope if s["scope_type"] == "in_scope"],
        "out_of_scope": [s for s in scope if s["scope_type"] == "out_of_scope"],
    }
