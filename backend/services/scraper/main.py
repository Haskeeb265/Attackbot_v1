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

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Query

from backend.shared.db import init_db, check_db_health
from backend.shared.health import HealthResponse, ComponentHealth, HealthStatus
from backend.shared.logging import configure_logging, get_logger

from backend.services.scraper.config import ScraperConfig
from backend.services.scraper.collectors.base import CollectorRegistry
from backend.services.scraper.collectors import hackerone  # noqa: F401 — triggers registration
from backend.services.scraper.scope_parser import ScopeParser
from backend.services.scraper.repository import ProgramRepository
from backend.services.scraper.publisher import ScraperPublisher
from backend.services.scraper.reconciler import Reconciler

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
    Acquires Redis lock, runs collector (in executor), upserts, publishes.
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
        published = 0
        errors = 0

        for raw in raw_programs:
            try:
                # Fetch full details (scopes, policy) — sync, run in executor
                raw_detail = await loop.run_in_executor(
                    None, collector.fetch_details, raw.handle
                )
                program = collector.normalize(raw_detail)
                program.scopes = _scope_parser.parse(program.scopes)

                program_id = await _repository.upsert(program)
                upserted += 1

                success = await _publisher.publish_scan_job(program_id, program)
                if success:
                    published += 1

            except Exception as e:
                log.error("program_scrape_failed", handle=raw.handle, error=str(e))
                errors += 1
                continue

        log.info(
            "scrape_completed",
            platform=platform,
            upserted=upserted,
            published=published,
            errors=errors,
        )
        return {
            "status": "completed",
            "platform": platform,
            "upserted": upserted,
            "published": published,
            "errors": errors,
        }

    finally:
        await lock.release()


# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis, _scheduler, _publisher, _repository, _reconciler

    # Init DB
    init_db(settings.database_url, settings.db_pool_size, settings.db_max_overflow)

    # Init Redis
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    # Init repository and publisher
    _repository = ProgramRepository()
    _publisher = ScraperPublisher(settings.rabbitmq_url, _repository)
    await _publisher.connect()

    # Init reconciler
    _reconciler = Reconciler(_repository, _publisher, settings.reconciler_max_age_days)

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
    rabbitmq_ok = _publisher is not None  # TODO: add real RabbitMQ ping in M3
    scheduler_ok = _scheduler is not None and _scheduler.running

    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        ),
        "rabbitmq": ComponentHealth(
            status=HealthStatus.HEALTHY if rabbitmq_ok else HealthStatus.UNHEALTHY
        ),
        "scheduler": ComponentHealth(
            status=HealthStatus.HEALTHY if scheduler_ok else HealthStatus.UNHEALTHY
        ),
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


# ---------------------------------------------------------------------------
# Scrape trigger
# ---------------------------------------------------------------------------

@app.post("/api/v1/scrape/trigger")
async def trigger_scrape(platform: str = "hackerone") -> dict:
    """Trigger an immediate scrape for a platform, outside the normal schedule."""
    if platform not in CollectorRegistry.all_platforms():
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform!r}")
    result = await _run_platform_scrape(platform)
    return result


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