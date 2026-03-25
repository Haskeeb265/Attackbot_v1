# backend/services/reporter/worker.py
import json
from typing import Any

from celery import Celery, bootsteps
from kombu import Consumer

from backend.shared.config import BaseServiceConfig
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import Queues, passive_queue_binding
from backend.shared.schemas.envelope import MessageEnvelope
from backend.shared.schemas.report_jobs import ReportJobsPayload


class WorkerConfig(BaseServiceConfig):
    service_name: str = "reporter-worker"


settings = WorkerConfig()
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
    # Keep Celery task transport available for future use, but report.jobs
    # is consumed by the raw consumer below.
    task_default_queue="reporter.worker.tasks",
)


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

    log.warning(
        "report_generation_not_yet_implemented",
        scan_id=str(payload.scan_id),
        program_id=str(payload.program_id),
    )


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
                queues=[
                    passive_queue_binding(Queues.REPORT_JOBS)
                ],
                callbacks=[_on_report_jobs_message],
                # Core currently publishes envelopes with content_type=None.
                # Keep accept=None so raw bodies are still delivered, then parse explicitly.
                accept=None,
            )
        ]


app.steps["consumer"].add(ReportJobsConsumerStep)


@app.task(name="reporter_worker_task", bind=True, max_retries=0)
def reporter_worker_task(self, message: dict) -> None:  # type: ignore[misc]
    """
    Compatibility task entrypoint in case report jobs are sent as Celery tasks.
    """
    log.warning(
        "report_job_received_via_celery_task_path",
        queue=app.conf.task_default_queue,
        invocation_source="celery_compat",
        note="Expected path is raw kombu consumer on report.jobs",
    )
    _handle_report_job_message(message)
