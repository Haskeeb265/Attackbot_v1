from celery import Celery

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.scan_task import run_scan_task
from backend.services.core_engine.startup_checks import StartupCheck, collect_toolchain_checks
from backend.shared.exceptions import MessageSchemaError
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import Queues, passive_queue_binding
from backend.shared.schemas.envelope import MessageEnvelope
from backend.shared.schemas.scan_jobs import ScanJobsPayload

config = EngineConfig()
configure_logging(config.service_name)
logger = get_logger("core_engine.worker")


def _run_worker_startup_checks() -> list[StartupCheck]:
    """
    Worker startup should remain non-blocking.

    We only log check status for nuclei binary/templates here so operators can
    diagnose Stage 4 failures early without preventing worker boot.
    """
    try:
        checks = collect_toolchain_checks(required_tools=("nuclei",))
    except Exception as exc:
        logger.warning(
            "worker_toolchain_checks_failed_unexpectedly",
            error=str(exc),
        )
        return []

    for check in checks:
        if check.name not in {"nuclei", "nuclei_templates"}:
            continue
        if check.ok:
            logger.info(
                "worker_toolchain_check_ok",
                check=check.name,
                detail=check.detail,
            )
        else:
            logger.warning(
                "worker_toolchain_check_failed",
                check=check.name,
                detail=check.detail,
            )
    return checks


_WORKER_STARTUP_CHECKS = _run_worker_startup_checks()


app = Celery(
    "core_worker",
    broker=config.rabbitmq_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,  # ack only after task completes; prevents loss on crash
    task_reject_on_worker_lost=True,  # NACK on worker death; message goes to DLQ
    worker_prefetch_multiplier=1,  # one task at a time per worker; scans are heavy
    broker_connection_retry_on_startup=True,
    task_default_queue=Queues.SCAN_JOBS,
    task_queues=(
        passive_queue_binding(Queues.SCAN_JOBS),
    ),
)


@app.task(
    name="core_engine.scan_task",
    queue=Queues.SCAN_JOBS,
    bind=True,
    max_retries=0,  # Watchdog handles retry logic; do not let Celery auto-retry.
)
def scan_task(self, message: dict) -> None:
    """
    Celery task entry. Deserializes MessageEnvelope and delegates to scan pipeline.
    """
    try:
        envelope = MessageEnvelope(**message)
        if envelope.event_type != "program.scraped":
            raise MessageSchemaError(f"Unsupported event_type: {envelope.event_type}")
        if envelope.get_major_version() != 1:
            raise MessageSchemaError(
                f"Unsupported scan.jobs schema version: {envelope.schema_version}"
            )
        payload = ScanJobsPayload.model_validate(envelope.payload)
        logger.info(
            "Scan task received",
            program_id=str(payload.program_id),
            event_type=envelope.event_type,
        )
        run_scan_task(payload)
    except Exception as exc:
        logger.error("Scan task fatal error", error=str(exc))
        raise  # Let Celery mark as failure; watchdog handles stuck scans.
