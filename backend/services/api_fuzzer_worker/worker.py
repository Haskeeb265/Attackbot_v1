# backend/services/api_fuzzer_worker/worker.py
from celery import Celery
from kombu import Queue

from backend.shared.config import BaseServiceConfig
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import Queues, dead_letter_arguments


class WorkerConfig(BaseServiceConfig):
    service_name: str = "api-fuzzer-worker"


settings = WorkerConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

app = Celery(
    "api-fuzzer-worker",
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
    task_default_queue=Queues.API_FUZZ_JOBS,
    task_queues=(
        Queue(
            Queues.API_FUZZ_JOBS,
            durable=True,
            queue_arguments=dead_letter_arguments(Queues.API_FUZZ_JOBS),
        ),
    ),
)


@app.task(name="api_fuzzer_worker_task", bind=True, max_retries=2)
def api_fuzzer_worker_task(self, message: dict) -> None:  # type: ignore[misc]
    """M1 skeleton — logs receipt, does nothing. Full implementation in M6."""
    log.info(
        "task_received",
        queue=Queues.API_FUZZ_JOBS,
        event_id=message.get("event_id"),
        event_type=message.get("event_type"),
    )
