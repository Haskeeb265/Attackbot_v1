import asyncio
import json
import time
from typing import Any, Optional

from celery import Celery, bootsteps
from kombu import Consumer

from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.report_task import process_report_envelope_sync
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import QueuePublisher, Queues, passive_queue_binding
from backend.shared.schemas.envelope import MessageEnvelope
from backend.shared.schemas.report_jobs import ReportJobsPayload

settings = ReporterConfig(service_name="reporter-worker")
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

app = Celery(
    "reporter-worker",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    # Keep Celery task transport available for task execution while report.jobs
    # is consumed by the raw consumer below.
    task_default_queue="reporter.worker.tasks",
)


class ReportWorker:
    """
    Reporter worker that processes report generation jobs.
    Supports both v1 (HTTP-based) and v2 (embedded data) payloads.
    """
    
    def __init__(self):
        self.core_engine_client = None
        self._legacy_http_calls = 0
    
    async def _generate_report(self, payload: ReportJobsPayload) -> dict:
        """
        Generate report from embedded data (v2 payload).
        This method uses the data embedded in the payload instead of making HTTP calls.
        """
        # Simulate report generation - in reality this would use the embedded data
        # to generate PDF/DOCX reports without calling Core Engine
        start = time.time()
        
        # Access embedded data directly
        scan_summary = payload.scan_summary
        findings = payload.findings
        evidence = payload.evidence
        
        # Simulate report generation processing
        # In a real implementation, this would:
        # 1. Use scan_summary for executive summary
        # 2. Use findings list for finding sections
        # 3. Use evidence list for evidence sections
        # 4. Generate PDF/DOCX without HTTP calls
        
        elapsed = time.time() - start
        log.info(
            "Report generated from embedded data",
            scan_id=str(payload.scan_id),
            finding_count=len(findings),
            evidence_count=len(evidence),
            duration_seconds=elapsed
        )
        
        return {
            "scan_id": str(payload.scan_id),
            "status": "generated",
            "finding_count": len(findings),
            "evidence_count": len(evidence),
            "duration_seconds": elapsed
        }
    
    async def _legacy_fetch_data(self, payload: ReportJobsPayload) -> ReportJobsPayload:
        """
        Legacy method: Fetch data from Core Engine via HTTP.
        Used for v1 payloads without embedded data.
        """
        from backend.services.reporter.clients.core_engine import get_scan_data
        self._legacy_http_calls += 1
        
        # In a real implementation, this would:
        # 1. Call Core Engine to get scan details
        # 2. Call Core Engine to get findings
        # 3. Call Core Engine to get evidence
        # 4. Return a v2-style payload with embedded data
        
        data = await get_scan_data(str(payload.scan_id))
        scan = data.get("scan") or {}
        findings = data.get("findings") or []

        # For now, return a v2 payload (embedded data) built from fetched data.
        return ReportJobsPayload(
            scan_id=payload.scan_id,
            program_id=payload.program_id,
            payload_version=2,
            formats_requested=payload.formats_requested or ["pdf"],
            has_findings=payload.has_findings,
            finding_count=payload.finding_count,
            # Mock embedded data
            scan_summary={
                "scan_id": str(payload.scan_id),
                "program_id": str(payload.program_id),
                "status": scan.get("status") or "completed"
            },
            findings=findings,
            evidence=[],
        )
    
    async def process_report_job(self, envelope: Optional[MessageEnvelope], payload_dict: dict) -> dict:
        """
        Process a report job from the queue.
        
        Args:
            envelope: Optional MessageEnvelope (for trace context)
            payload_dict: The payload dictionary from the message
            
        Returns:
            Dictionary with report generation results
        """
        # Parse payload
        if isinstance(payload_dict, dict):
            payload = ReportJobsPayload.model_validate(payload_dict)
        else:
            raise ValueError(f"Invalid payload type: {type(payload_dict)}")
        
        # Check if this is a v2 payload with embedded data
        if payload.has_embedded_data():
            # Use embedded data - no HTTP calls
            result = await self._generate_report(payload)
        elif payload.is_legacy():
            # Fallback to HTTP for legacy v1 payloads
            v2_payload = await self._legacy_fetch_data(payload)
            result = await self._generate_report(v2_payload)
        else:
            # Default to v2 processing
            result = await self._generate_report(payload)
        
        return result


def _retry_countdown(attempt_number: int, backoff: list[int]) -> int:
    return backoff[min(attempt_number, len(backoff) - 1)]


def _serialize_raw_body(raw_body: Any) -> str:
    if isinstance(raw_body, (bytes, bytearray)):
        return raw_body.decode("utf-8", errors="replace")
    if isinstance(raw_body, str):
        return raw_body
    try:
        return json.dumps(raw_body, default=str)
    except Exception:
        return repr(raw_body)


def _coerce_body_to_dict(raw_body: Any) -> dict[str, Any]:
    if isinstance(raw_body, dict):
        return raw_body
    if isinstance(raw_body, (bytes, bytearray)):
        raw_body = raw_body.decode("utf-8", errors="replace")
    if isinstance(raw_body, str):
        parsed = json.loads(raw_body)
        if not isinstance(parsed, dict):
            raise ValueError("Envelope body must be a JSON object.")
        return parsed
    raise ValueError(f"Unsupported message body type: {type(raw_body).__name__}")


def _handle_report_job_message(raw_body: Any) -> None:
    raw_body_for_log = _serialize_raw_body(raw_body)

    try:
        envelope_dict = _coerce_body_to_dict(raw_body)
        envelope = MessageEnvelope(**envelope_dict)
    except Exception as exc:
        log.error(
            "report_job_malformed_envelope",
            queue=Queues.REPORT_JOBS,
            error=str(exc),
            raw_body=raw_body_for_log,
        )
        return

    if envelope.event_type != "scan.completed":
        log.error(
            "report_job_unsupported_event_type",
            queue=Queues.REPORT_JOBS,
            event_type=envelope.event_type,
            raw_body=raw_body_for_log,
        )
        return

    if envelope.get_major_version() != 1:
        log.error(
            "report_job_unsupported_schema_version",
            queue=Queues.REPORT_JOBS,
            schema_version=envelope.schema_version,
            raw_body=raw_body_for_log,
        )
        return

    try:
        payload = ReportJobsPayload.model_validate(envelope.payload)
    except Exception as exc:
        log.error(
            "report_job_malformed_payload",
            queue=Queues.REPORT_JOBS,
            error=str(exc),
            raw_body=raw_body_for_log,
        )
        return

    log.info(
        "report_job_received",
        queue=Queues.REPORT_JOBS,
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        scan_id=str(payload.scan_id),
        program_id=str(payload.program_id),
        finding_count=payload.finding_count,
        severity_breakdown=payload.severity_breakdown.model_dump(mode="json"),
    )

    if payload.formats_requested:
        log.info(
            "report_job_formats_requested",
            scan_id=str(payload.scan_id),
            formats_requested=payload.formats_requested,
            include_evidence_screenshots=payload.include_evidence_screenshots,
        )

    reporter_worker_task.apply_async(
        args=[envelope_dict],
        queue=app.conf.task_default_queue,
    )
    log.info(
        "report_generation_task_enqueued",
        queue=app.conf.task_default_queue,
        scan_id=str(payload.scan_id),
        program_id=str(payload.program_id),
        formats_requested=payload.formats_requested,
    )


async def _publish_to_report_jobs_dlq(message: dict[str, Any]) -> bool:
    publisher = QueuePublisher(settings.rabbitmq_url)
    await publisher.connect()
    try:
        await publisher.ensure_queue(Queues.REPORT_JOBS_DLQ)
        return await publisher.publish(Queues.REPORT_JOBS_DLQ, message)
    finally:
        await publisher.close()


def _publish_to_report_jobs_dlq_sync(message: dict[str, Any]) -> bool:
    try:
        return asyncio.run(_publish_to_report_jobs_dlq(message))
    except Exception as exc:
        log.error(
            "report_generation_dlq_publish_failed",
            queue=Queues.REPORT_JOBS_DLQ,
            error=str(exc),
        )
        return False


def _handle_task_exception(task: Any, message: dict[str, Any], exc: Exception) -> None:
    retries = int(getattr(task.request, "retries", 0))
    if retries < settings.report_task_max_retries:
        countdown = _retry_countdown(retries, settings.get_retry_backoff())
        raise task.retry(exc=exc, countdown=countdown)

    dlq_published = _publish_to_report_jobs_dlq_sync(message)
    log.error(
        "report_generation_retries_exhausted",
        retries=retries,
        max_retries=settings.report_task_max_retries,
        error=str(exc),
        dlq_published=dlq_published,
    )
    raise exc


def _on_report_jobs_message(body: Any, message: Any) -> None:
    try:
        _handle_report_job_message(body)
    except Exception as exc:
        # Safety net: never crash worker on one bad message.
        log.error(
            "report_job_handler_unexpected_error",
            queue=Queues.REPORT_JOBS,
            error=str(exc),
            raw_body=_serialize_raw_body(body),
        )
    finally:
        try:
            message.ack()
        except Exception as exc:
            log.error(
                "report_job_ack_failed",
                queue=Queues.REPORT_JOBS,
                error=str(exc),
            )


class ReportJobsConsumerStep(bootsteps.ConsumerStep):
    def get_consumers(self, channel: Any) -> list[Consumer]:
        return [
            Consumer(
                channel,
                queues=[passive_queue_binding(Queues.REPORT_JOBS)],
                callbacks=[_on_report_jobs_message],
                # Core currently publishes envelopes with content_type=None.
                # Keep accept=None so raw bodies are still delivered, then parse explicitly.
                accept=None,
            )
        ]


app.steps["consumer"].add(ReportJobsConsumerStep)


@app.task(name="reporter_worker_task", bind=True)
def reporter_worker_task(self, message: dict) -> None:  # type: ignore[misc]
    """
    Task entrypoint for actual report generation processing.
    """
    try:
        process_report_envelope_sync(message)
    except Exception as exc:
        _handle_task_exception(self, message, exc)
