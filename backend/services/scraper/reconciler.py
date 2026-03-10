"""
AttackBot scraper reconciler.

Retries programs where queued_for_scan = True.
This is the ONLY component that reads queued_for_scan=True rows and clears them.

The reconciler runs every 5 minutes via APScheduler.
It only processes programs scraped within the last N days — stale programs
may have changed scope and should be re-scraped before being queued.
"""
from shared.logging import get_logger
from .repository import ProgramRepository
from .publisher import ScanJobPublisher

log   = get_logger(__name__)
_repo = ProgramRepository()


class Reconciler:
    """
    Retries scan-job publishing for programs that failed their initial publish.

    Per cycle:
      1. Query programs WHERE queued_for_scan=True AND last_scraped_at > N days ago
      2. For each: republish via ScanJobPublisher
      3. Success → ScanJobPublisher clears the flag
      4. Failure → flag stays set; retried next cycle
    """

    def __init__(
        self,
        publisher: ScanJobPublisher,
        stale_days: int = 7,
    ) -> None:
        self._publisher  = publisher
        self._stale_days = stale_days

    async def reconcile(self) -> dict:
        """
        Run one reconciliation cycle.
        Returns a summary dict: {attempted, succeeded, failed}.
        """
        programs = await _repo.get_programs_pending_reconcile(self._stale_days)

        if not programs:
            log.info("reconciler_nothing_to_reconcile")
            return {"attempted": 0, "succeeded": 0, "failed": 0}

        log.info("reconciler_starting", pending=len(programs))

        succeeded = 0
        failed    = 0

        for program in programs:
            # Re-fetch with scopes eager-loaded
            full_program = await _repo.get_program_with_scopes(program.program_id)
            if not full_program:
                log.warning("reconciler_program_not_found",
                            program_id=str(program.program_id))
                failed += 1
                continue

            if not full_program.scopes:
                log.warning("reconciler_no_scopes_skip",
                            program_id=str(program.program_id),
                            handle=full_program.handle)
                failed += 1
                continue

            ok = await self._publisher.publish_scan_job(
                program = full_program,
                scopes  = list(full_program.scopes),
            )

            if ok:
                succeeded += 1
            else:
                failed += 1

        summary = {
            "attempted": len(programs),
            "succeeded": succeeded,
            "failed":    failed,
        }
        log.info("reconciler_complete", **summary)
        return summary
