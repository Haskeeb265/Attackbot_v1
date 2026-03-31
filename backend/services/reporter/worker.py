import asyncio
import json
from typing import Any

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
