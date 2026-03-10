# backend/services/reporter/worker.py
from celery import Celery

from backend.shared.config import BaseServiceConfig
from backend.shared.logging import configure_logging, get_logger


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
    """M1 skeleton — logs receipt, does nothing. Full implementation in M4."""
    log.info(
        "task_received",
        queue="report.jobs",
        event_id=message.get("event_id"),
        event_type=message.get("event_type"),
    )