"""
Scraper publisher - dispatches scan jobs as Celery tasks.

Important:
    core-worker consumes Celery task frames from scan.jobs (task name:
    ``core_engine.scan_task``). Publishing a raw envelope to scan.jobs causes
    Celery to treat it as an unknown message and drop it.

Failure path:
    send_task() raises -> mark_queued(program_id) is called -> reconciler retries later.
"""

from uuid import UUID

from backend.shared.logging import get_logger
from backend.shared.queue import Queues
from backend.shared.schemas.scan_jobs import (
    ScanJobsPayload,
    ScopeDefinition,
    ScopeEntry,
    build_scan_job_message,
)
from backend.services.scraper.models import Program
from backend.services.scraper.repository import ProgramRepository

log = get_logger(__name__)


class ScraperPublisher:
    def __init__(
        self,
        rabbitmq_url: str,
        repository: ProgramRepository,
        scan_timeout_seconds: int = 14_400,
    ):
        from celery import Celery

        self._task_dispatcher = Celery("scraper_scan_dispatcher", broker=rabbitmq_url)
        self._task_dispatcher.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            # Retry is handled by queued_for_scan + reconciler, not by Celery publisher retries.
            task_publish_retry=False,
        )
        self._repository = repository
        self._scan_timeout_seconds = int(scan_timeout_seconds)

    async def connect(self) -> None:
        log.info(
            "scan_job_dispatcher_ready",
            queue=Queues.SCAN_JOBS,
            task_name="core_engine.scan_task",
        )

    async def publish_scan_job(self, program_id: UUID, program: Program) -> bool:
        in_scope_scopes = [s for s in program.scopes if s.scope_type == "in_scope"]
        out_of_scope_scopes = [s for s in program.scopes if s.scope_type == "out_of_scope"]
        scan_timeout_seconds = int(getattr(self, "_scan_timeout_seconds", 14_400))

        if not in_scope_scopes:
            log.warning(
                "publish_skipped_no_scope",
                handle=program.handle,
                program_id=str(program_id),
            )
            return False

        message = build_scan_job_message(
            ScanJobsPayload(
                program_id=program_id,
                platform=program.platform,
                handle=program.handle,
                scope=ScopeDefinition(
                    in_scope=[
                        ScopeEntry(
                            asset_type=getattr(s, "asset_type", "domain"),
                            value=getattr(s, "value", s),
                        )
                        for s in in_scope_scopes
                    ],
                    out_of_scope=[
                        ScopeEntry(
                            asset_type=getattr(s, "asset_type", "domain"),
                            value=getattr(s, "value", s),
                        )
                        for s in out_of_scope_scopes
                    ],
                ),
                scan_timeout_seconds=scan_timeout_seconds,
            )
        )

        try:
            self._task_dispatcher.send_task(
                "core_engine.scan_task",
                args=[message],
                queue=Queues.SCAN_JOBS,
                serializer="json",
            )

            log.info(
                "scan_job_published",
                handle=program.handle,
                program_id=str(program_id),
                in_scope_count=len(in_scope_scopes),
                queue=Queues.SCAN_JOBS,
                task_name="core_engine.scan_task",
            )

            return True

        except Exception as e:
            log.warning(
                "publish_failed_queuing",
                handle=program.handle,
                program_id=str(program_id),
                error=str(e),
            )

            await self._repository.mark_queued(program_id)
            return False
