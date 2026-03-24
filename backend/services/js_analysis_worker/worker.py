# backend/services/js_analysis_worker/worker.py
from celery import Celery
from kombu import Queue

from backend.shared.config import BaseServiceConfig
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import Queues, dead_letter_arguments


class WorkerConfig(BaseServiceConfig):
    service_name: str = "js-analysis-worker"


settings = WorkerConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

app = Celery(
    "js-analysis-worker",
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
    task_default_queue=Queues.JS_ANALYSIS_JOBS,
    task_queues=(
        Queue(
            Queues.JS_ANALYSIS_JOBS,
            durable=True,
            queue_arguments=dead_letter_arguments(Queues.JS_ANALYSIS_JOBS),
        ),
    ),
)


@app.task(name="js_analysis_worker_task", bind=True, max_retries=2)
def js_analysis_worker_task(self, message: dict) -> None:  # type: ignore[misc]
    """M1 skeleton — logs receipt, does nothing. Full implementation in M6."""
    log.info(
        "task_received",
        queue=Queues.JS_ANALYSIS_JOBS,
        event_id=message.get("event_id"),
        event_type=message.get("event_type"),
    )
