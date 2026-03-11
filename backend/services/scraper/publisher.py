"""
Scraper publisher — wraps the shared QueuePublisher with scraper-specific failure handling.

Failure path:
    publish() returns False → mark_queued(program_id) is called → reconciler retries later.

This decouples the publish outcome from the scrape loop — a RabbitMQ outage
doesn't lose scan jobs, it queues them for retry.
"""

from uuid import UUID
from backend.shared.queue import QueuePublisher, Queues
from backend.shared.schemas.scan_jobs import build_scan_job_message, ScanJobsPayload, ScopeDefinition, ScopeEntry
from backend.shared.logging import get_logger
from backend.services.scraper.models import Program
from backend.services.scraper.repository import ProgramRepository

log = get_logger(__name__)


class ScraperPublisher:

    def __init__(self, rabbitmq_url: str, repository: ProgramRepository):
        self._publisher = QueuePublisher(rabbitmq_url)
        self._repository = repository

    async def connect(self) -> None:
        await self._publisher.connect()

    async def publish_scan_job(self, program_id: UUID, program: Program) -> bool:
        """
        Publish a scan.jobs message for a program.

        On success: returns True.
        On failure: sets queued_for_scan=True in DB and returns False.
        The reconciler will retry on its next cycle.

        Programs with no in-scope entries are skipped (cannot be scanned).
        """
        in_scope = [s.value for s in program.scopes if s.scope_type == "in_scope"]
        out_of_scope = [s.value for s in program.scopes if s.scope_type == "out_of_scope"]

        if not in_scope:
            log.warning(
                "publish_skipped_no_scope",
                handle=program.handle,
                program_id=str(program_id),
            )
            # Don't queue programs with no in-scope entries — they can't be scanned
            return False

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

        success = await self._publisher.publish(Queues.SCAN_JOBS, message)

        if not success:
            log.warning(
                "publish_failed_queuing",
                handle=program.handle,
                program_id=str(program_id),
            )
            await self._repository.mark_queued(program_id)
            return False

        log.info(
            "scan_job_published",
            handle=program.handle,
            program_id=str(program_id),
            in_scope_count=len(in_scope),
        )
        return True