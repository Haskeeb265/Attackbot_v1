"""
AttackBot Scraper Service — main entry point.

Replaces the M1 skeleton with a fully wired lifespan:
  1. DB initialisation
  2. Vault connection + credential loading
  3. RabbitMQ publisher
  4. APScheduler (scrape + reconcile jobs)

External entry point: uvicorn backend.services.scraper.main:app
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from shared.db import init_db, check_db_health
from shared.health import ComponentHealth, HealthResponse, HealthStatus
from shared.logging import configure_logging, get_logger
from shared.queue import QueuePublisher
from shared.vault import get_secret, init_vault

from .config import ScraperConfig
from .publisher import ScanJobPublisher
from .routes import router
from .scheduler import ScraperScheduler

# ── Module-level singletons ────────────────────────────────────────────
settings = ScraperConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

_scraper_scheduler: ScraperScheduler | None = None
_queue_publisher:   QueuePublisher   | None = None


def get_scheduler() -> AsyncIOScheduler:
    """
    Return the running APScheduler instance.
    Used by routes.py to trigger jobs on demand.
    Raises RuntimeError if called before lifespan initialises the scheduler.
    """
    if _scraper_scheduler is None:
        raise RuntimeError("Scheduler not initialised — lifespan not yet complete")
    return _scraper_scheduler.get_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scraper_scheduler, _queue_publisher

    log.info("scraper_starting")

    # ── 1. Database ────────────────────────────────────────────────
    init_db(
        settings.database_url,
        settings.db_pool_size,
        settings.db_max_overflow,
    )
    log.info("scraper_db_ready")

    # ── 2. Vault ───────────────────────────────────────────────────
    init_vault(settings.vault_url, settings.vault_token)

    # Load HackerOne credentials from Vault; fall back to env vars for dev
    try:
        h1_username = get_secret("attackbot/platform/hackerone", "api_username")
        h1_token    = get_secret("attackbot/platform/hackerone", "api_token")
        log.info("vault_creds_loaded", platform="hackerone")
    except Exception as exc:
        log.warning("vault_creds_not_found_using_env", error=str(exc))
        h1_username = settings.hackerone_api_username
        h1_token    = settings.hackerone_api_token

    # ── 3. RabbitMQ publisher ──────────────────────────────────────
    _queue_publisher = QueuePublisher(settings.rabbitmq_url)
    await _queue_publisher.connect()
    log.info("scraper_queue_publisher_ready")

    # ── 4. Scan job publisher ──────────────────────────────────────
    scan_publisher = ScanJobPublisher(_queue_publisher)

    # ── 5. Scheduler ───────────────────────────────────────────────
    _scraper_scheduler = ScraperScheduler(
        redis_url                    = settings.redis_url,
        publisher                    = scan_publisher,
        hackerone_username           = h1_username,
        hackerone_token              = h1_token,
        scrape_interval_minutes      = settings.hackerone_scrape_interval_minutes,
        reconciler_interval_minutes  = settings.reconciler_interval_minutes,
        stale_days                   = settings.reconciler_stale_days,
    )
    await _scraper_scheduler.start()
    log.info("scraper_scheduler_ready")
    log.info("scraper_ready")

    yield  # ← service runs here

    # ── Shutdown ───────────────────────────────────────────────────
    log.info("scraper_stopping")
    await _scraper_scheduler.stop()
    if _queue_publisher:
        await _queue_publisher.close()
    log.info("scraper_stopped")


# ── FastAPI application ────────────────────────────────────────────────
app = FastAPI(
    title       = "AttackBot Scraper",
    description = "Bug bounty platform scraper and scan-job publisher",
    version     = "1.0.0",
    lifespan    = lifespan,
)

Instrumentator().instrument(app).expose(app)
app.include_router(router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint.
    Checks: database, RabbitMQ (publisher state), scheduler.
    """
    db_ok = await check_db_health()

    # RabbitMQ: publisher reconnects automatically — report its connection state
    rmq_ok = (
        _queue_publisher is not None
        and _queue_publisher._connection is not None
        and not _queue_publisher._connection.is_closed
    )

    sched_ok = (
        _scraper_scheduler is not None
        and _scraper_scheduler.get_scheduler().running
    )

    components = {
        "database":  ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok    else HealthStatus.UNHEALTHY
        ),
        "rabbitmq":  ComponentHealth(
            status=HealthStatus.HEALTHY if rmq_ok   else HealthStatus.UNHEALTHY
        ),
        "scheduler": ComponentHealth(
            status=HealthStatus.HEALTHY if sched_ok else HealthStatus.UNHEALTHY
        ),
    }

    overall = (
        HealthStatus.HEALTHY
        if all(c.status == HealthStatus.HEALTHY for c in components.values())
        else HealthStatus.UNHEALTHY
    )

    return HealthResponse(
        status     = overall,
        service    = settings.service_name,
        timestamp  = datetime.now(timezone.utc),
        components = components,
    )
