"""
Reconciler — runs on APScheduler every 5 minutes.

Finds programs with queued_for_scan=True and re-attempts publish.
This is the recovery path for publish failures — RabbitMQ outages,
transient network errors, or any other failure that left the flag set.

The reconciler is the ONLY component allowed to call clear_queued().
The upsert path never touches queued_for_scan on conflict updates.
"""

from backend.shared.logging import get_logger
from backend.services.scraper.repository import ProgramRepository
from backend.services.scraper.publisher import ScraperPublisher
from backend.services.scraper.models import Program, ProgramScope

log = get_logger(__name__)


class Reconciler:

    def __init__(
        self,
        repository: ProgramRepository,
        publisher: ScraperPublisher,
        max_age_days: int = 7,
        paused: bool = False,
    ):
        self._repo = repository
        self._publisher = publisher
        self._max_age_days = max_age_days
        self._paused = paused

    async def reconcile(self) -> dict:
        """
        Query for queued programs, attempt republish.
        Returns summary: {"checked": N, "published": N, "failed": N}
        """
        if self._paused:
            log.info(
                "reconciler_paused",
                reason="E2E_PAUSE_RECONCILER is enabled",
            )
            return {"checked": 0, "published": 0, "failed": 0}

        queued = await self._repo.get_queued_programs(self._max_age_days)
        log.info("reconciler_started", queued_count=len(queued))

        published = 0
        failed = 0

        for row in queued:
            program_id = row["program_id"]
            handle = row["handle"]
            platform = row["platform"]

            # Fetch full scope to rebuild the scan message
            scope_rows = await self._repo.get_scope(program_id)
            scopes = [
                ProgramScope(
                    scope_type=s["scope_type"],
                    asset_type=s["asset_type"],
                    value=s["value"],
                    notes=s.get("notes"),
                )
                for s in scope_rows
            ]

            # Reconstruct minimal Program for publish
            program = Program(
                platform=platform,
                handle=handle,
                name=row.get("name", handle),
                scopes=scopes,
            )

            success = await self._publisher.publish_scan_job(program_id, program)

            if success:
                await self._repo.clear_queued(program_id)
                published += 1
                log.info(
                    "reconciler_published",
                    handle=handle,
                    program_id=str(program_id),
                )
            else:
                failed += 1
                log.warning(
                    "reconciler_publish_failed",
                    handle=handle,
                    program_id=str(program_id),
                )

        log.info(
            "reconciler_finished",
            checked=len(queued),
            published=published,
            failed=failed,
        )
        return {"checked": len(queued), "published": published, "failed": failed}
