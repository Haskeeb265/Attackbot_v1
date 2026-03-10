"""
AttackBot scraper scheduler.

Runs two recurring jobs inside the scraper process:
  1. HackerOne full scrape — configurable interval (default 60 min)
  2. Reconciler — every 5 minutes

Redis locks prevent overlapping runs on the same platform.
Lock key format: scraper:lock:{platform}
"""
import asyncio
from datetime import datetime

import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from shared.logging import get_logger
from .collectors.hackerone import HackerOneCollector
from .repository import ProgramRepository
from .publisher import ScanJobPublisher
from .reconciler import Reconciler

log   = get_logger(__name__)
_repo = ProgramRepository()

LOCK_TTL_SECONDS = 3600  # 1 hour — max time a scrape job may hold the lock


class ScraperScheduler:
    """
    APScheduler wrapper for the scraper service.
    Both jobs are registered on start() and the scheduler is shut down on stop().
    """

    def __init__(
        self,
        redis_url:                  str,
        publisher:                  ScanJobPublisher,
        hackerone_username:         str,
        hackerone_token:            str,
        scrape_interval_minutes:    int = 60,
        reconciler_interval_minutes:int = 5,
        stale_days:                 int = 7,
    ) -> None:
        self._redis_url              = redis_url
        self._publisher              = publisher
        self._hackerone_username     = hackerone_username
        self._hackerone_token        = hackerone_token
        self._scrape_interval        = scrape_interval_minutes
        self._reconciler_interval    = reconciler_interval_minutes
        self._stale_days             = stale_days
        self._scheduler              = AsyncIOScheduler()
        self._redis: aioredis.Redis | None = None

    async def start(self) -> None:
        """Connect to Redis, register jobs, and start the scheduler."""
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)

        # Run the HackerOne scrape immediately on startup and then on interval
        self._scheduler.add_job(
            self._scrape_hackerone,
            trigger          = IntervalTrigger(minutes=self._scrape_interval),
            id               = "scrape_hackerone",
            name             = "HackerOne full scrape",
            replace_existing = True,
            next_run_time    = datetime.now(),  # run immediately on first start
        )

        self._scheduler.add_job(
            self._run_reconciler,
            trigger          = IntervalTrigger(minutes=self._reconciler_interval),
            id               = "reconciler",
            name             = "Publish failure reconciler",
            replace_existing = True,
        )

        self._scheduler.start()
        log.info(
            "scheduler_started",
            scrape_interval_min      = self._scrape_interval,
            reconciler_interval_min  = self._reconciler_interval,
        )

    async def stop(self) -> None:
        """Shut down the scheduler and close Redis connection."""
        self._scheduler.shutdown(wait=False)
        if self._redis:
            await self._redis.aclose()
        log.info("scheduler_stopped")

    def get_scheduler(self) -> AsyncIOScheduler:
        """Return the underlying APScheduler instance (used by routes to trigger jobs)."""
        return self._scheduler

    # ── Scheduled job implementations ─────────────────────────────

    async def _scrape_hackerone(self) -> None:
        """
        Full HackerOne scrape job.
        Redis lock prevents overlapping runs.
        Lock is released in the finally block even on failure.
        """
        lock_key = "scraper:lock:hackerone"
        locked   = await self._redis.set(lock_key, "1", nx=True, ex=LOCK_TTL_SECONDS)

        if not locked:
            log.info("scrape_skipped_lock_held", platform="hackerone")
            return

        log.info("scrape_starting", platform="hackerone")
        collector = HackerOneCollector(
            api_username = self._hackerone_username,
            api_token    = self._hackerone_token,
        )

        published = 0
        failed    = 0

        try:
            programs = await collector.fetch_listing()

            for raw in programs:
                try:
                    normalized    = collector.normalize(raw)
                    program_id, _ = await _repo.upsert(raw, normalized)
                    full_program  = await _repo.get_program_with_scopes(program_id)

                    if not full_program or not full_program.scopes:
                        log.warning("scrape_no_scopes_skip", handle=raw.handle)
                        continue

                    ok = await self._publisher.publish_scan_job(
                        program = full_program,
                        scopes  = list(full_program.scopes),
                    )
                    if ok:
                        published += 1
                    else:
                        failed += 1

                except Exception as exc:
                    log.error("scrape_program_error",
                              handle=raw.handle, error=str(exc))
                    failed += 1

            log.info(
                "scrape_complete",
                platform  = "hackerone",
                total     = len(programs),
                published = published,
                failed    = failed,
            )

        except Exception as exc:
            log.error("scrape_job_failed", platform="hackerone", error=str(exc))
        finally:
            await collector.close()
            await self._redis.delete(lock_key)

    async def _run_reconciler(self) -> None:
        """Reconciler job — retries failed publishes."""
        reconciler = Reconciler(self._publisher, stale_days=self._stale_days)
        try:
            await reconciler.reconcile()
        except Exception as exc:
            log.error("reconciler_job_failed", error=str(exc))
