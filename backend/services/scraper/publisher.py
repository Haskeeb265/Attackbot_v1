"""
AttackBot scraper scan-job publisher.

Wraps the shared QueuePublisher with scraper-specific logic:
  - Builds ScanJobsPayload from Program + ProgramScope rows
  - Sets queued_for_scan = True on publish failure
  - Clears queued_for_scan = False on publish success
"""
import uuid
from shared.queue import QueuePublisher, Queues
from shared.schemas.scan_jobs import (
    ScanJobsPayload,
    ScopeDefinition,
    ScopeEntry,
    FeatureFlags,
    build_scan_job_message,
)
from shared.logging import get_logger
from .models import Program, ProgramScope
from .repository import ProgramRepository

log   = get_logger(__name__)
_repo = ProgramRepository()


class ScanJobPublisher:
    """
    Publishes scan.jobs messages for scraped programs.

    On publish success: clears queued_for_scan flag.
    On publish failure: sets queued_for_scan = True for reconciler retry.
    Skips programs with no in-scope entries (logs warning, does NOT flag).
    """

    def __init__(self, queue_publisher: QueuePublisher) -> None:
        self._publisher = queue_publisher

    async def publish_scan_job(
        self,
        program: Program,
        scopes: list[ProgramScope],
        trace_id: str | None = None,
    ) -> bool:
        """
        Build and publish a scan.jobs message.
        Returns True on success, False on failure.
        """
        # ── Separate in/out scope entries ──────────────────────────
        in_scope_entries  = [s for s in scopes if s.scope_type == "in_scope"]
        out_scope_entries = [s for s in scopes if s.scope_type == "out_of_scope"]

        if not in_scope_entries:
            log.error(
                "publish_skipped_no_in_scope",
                program_id = str(program.program_id),
                handle     = program.handle,
            )
            return False

        # ── Build payload ──────────────────────────────────────────
        scope_def = ScopeDefinition(
            in_scope=[
                ScopeEntry(
                    asset_type = s.asset_type,
                    value      = s.value,
                    notes      = s.notes or "",
                )
                for s in in_scope_entries
            ],
            out_of_scope=[
                ScopeEntry(
                    asset_type = s.asset_type,
                    value      = s.value,
                    notes      = s.notes or "",
                )
                for s in out_scope_entries
            ],
        )

        payload = ScanJobsPayload(
            program_id    = program.program_id,
            platform      = program.platform,
            handle        = program.handle,
            scope         = scope_def,
            summary_file  = program.summary_file,
            feature_flags = FeatureFlags(),
            priority      = 1,
        )

        message = build_scan_job_message(
            payload        = payload,
            source_service = "scraper",
            trace_id       = trace_id,
        )

        # ── Publish ────────────────────────────────────────────────
        success = await self._publisher.publish(Queues.SCAN_JOBS, message)

        if success:
            await _repo.set_queued_for_scan(program.program_id, queued=False)
            log.info(
                "scan_job_published",
                handle     = program.handle,
                program_id = str(program.program_id),
                in_scope   = len(in_scope_entries),
            )
        else:
            await _repo.set_queued_for_scan(program.program_id, queued=True)
            log.warning(
                "scan_job_publish_failed_flagged",
                handle     = program.handle,
                program_id = str(program.program_id),
            )

        return success
