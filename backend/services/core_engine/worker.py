import json
from celery import Celery

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.scan_task import run_scan_task
from backend.shared.logging import configure_logging, get_logger
from backend.shared.schemas.envelope import MessageEnvelope

config = EngineConfig()
configure_logging(config.service_name)
logger = get_logger("core_engine.worker")

app = Celery(
    "core_worker",
    broker=config.rabbitmq_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,          # ack only after task completes — prevents loss on crash
    task_reject_on_worker_lost=True,  # NACK on worker death — message goes to DLQ
    worker_prefetch_multiplier=1, # one task at a time per worker — scans are heavy
)


@app.task(
    name="core_engine.scan_task",
    queue="scan.jobs",
    bind=True,
    max_retries=0,  # Watchdog handles retry logic — do not let Celery auto-retry
)
def scan_task(self, message: dict) -> None:
    """
    Celery task entry. Deserializes the MessageEnvelope and delegates to scan pipeline.
    """
    try:
        envelope = MessageEnvelope(**message)
        payload = envelope.payload
        logger.info("Scan task received",
                    program_id=payload.get("program_id"),
                    event_type=envelope.event_type)
        run_scan_task(payload)
    except Exception as e:
        logger.error("Scan task fatal error", error=str(e))
        raise  # Let Celery mark as failure — watchdog handles stuck scans