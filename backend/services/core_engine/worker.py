# backend/services/core_engine/worker.py
from celery import Celery

from backend.shared.config import BaseServiceConfig
from backend.shared.logging import configure_logging, get_logger


class WorkerConfig(BaseServiceConfig):
    service_name: str = "core-worker"


settings = WorkerConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

app = Celery(
    "core-worker",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,           # ack only after task completes
    worker_prefetch_multiplier=1,  # don't prefetch — tasks are long-running
    task_reject_on_worker_lost=True,
    task_default_queue="scan.jobs",
)


@app.task(name="core_worker_task", bind=True, max_retries=3)
def core_worker_task(self, message: dict) -> None:  # type: ignore[misc]
    """M1 skeleton — logs receipt, does nothing. Full implementation in M3."""
    log.info(
        "task_received",
        queue="scan.jobs",
        event_id=message.get("event_id"),
        event_type=message.get("event_type"),
    )