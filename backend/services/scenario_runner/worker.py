# backend/services/scenario_runner/worker.py
from celery import Celery

from backend.shared.config import BaseServiceConfig
from backend.shared.logging import configure_logging, get_logger


class WorkerConfig(BaseServiceConfig):
    service_name: str = "scenario-runner"


settings = WorkerConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

app = Celery(
    "scenario-runner",
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
    task_default_queue="scenario.jobs",
)


@app.task(name="scenario_runner_task", bind=True, max_retries=2)
def scenario_runner_task(self, message: dict) -> None:  # type: ignore[misc]
    """M1 skeleton — logs receipt, does nothing. Full implementation in M9."""
    log.info(
        "task_received",
        queue="scenario.jobs",
        event_id=message.get("event_id"),
        event_type=message.get("event_type"),
    )