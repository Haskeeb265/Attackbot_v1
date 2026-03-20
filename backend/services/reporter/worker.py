# backend/services/reporter/worker.py
from celery import Celery

from backend.shared.config import BaseServiceConfig
from backend.shared.exceptions import MessageSchemaError
from backend.shared.logging import configure_logging, get_logger
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
    task_default_queue="report.jobs",
)


@app.task(name="reporter_worker_task", bind=True, max_retries=3)
def reporter_worker_task(self, message: dict) -> None:  # type: ignore[misc]
    """Pre-M4 boundary validator for report.jobs. Full report generation lands in M4."""
    envelope = MessageEnvelope(**message)
    if envelope.event_type != "scan.completed":
        raise MessageSchemaError(f"Unsupported event_type: {envelope.event_type}")
    if envelope.get_major_version() != 1:
        raise MessageSchemaError(
            f"Unsupported report.jobs schema version: {envelope.schema_version}"
        )
    payload = ReportJobsPayload.model_validate(envelope.payload)
    log.info(
        "task_received",
        queue="report.jobs",
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        scan_id=str(payload.scan_id),
        has_findings=payload.has_findings,
    )
