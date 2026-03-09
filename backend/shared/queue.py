# backend/shared/queue.py
import json
from typing import Any

import aio_pika
import aio_pika.abc

from backend.shared.exceptions import QueueConnectionError
from backend.shared.logging import get_logger

log = get_logger(__name__)


class Queues:
    """
    Central registry of all queue names.
    Import this — never hardcode queue name strings.
    """

    SCAN_JOBS = "scan.jobs"
    SCAN_JOBS_DLQ = "scan.jobs.dlq"

    BROWSER_JOBS = "browser.jobs"
    BROWSER_JOBS_DLQ = "browser.jobs.dlq"

    API_FUZZ_JOBS = "api.fuzz.jobs"
    API_FUZZ_JOBS_DLQ = "api.fuzz.jobs.dlq"

    JS_ANALYSIS_JOBS = "js.analysis.jobs"
    JS_ANALYSIS_DLQ = "js.analysis.jobs.dlq"

    SCENARIO_JOBS = "scenario.jobs"
    SCENARIO_JOBS_DLQ = "scenario.jobs.dlq"

    VERIFY_JOBS = "verify.jobs"
    VERIFY_JOBS_DLQ = "verify.jobs.dlq"

    AI_ANALYSIS_JOBS = "ai.analysis.jobs"
    AI_ANALYSIS_DLQ = "ai.analysis.jobs.dlq"

    REPORT_JOBS = "report.jobs"
    REPORT_JOBS_DLQ = "report.jobs.dlq"

    REPORTS_COMPLETED = "reports.completed"


class QueuePublisher:
    """
    Persistent RabbitMQ publisher with reconnect support.

    Uses passive queue declaration to avoid argument mismatch errors — the
    queue must already exist (declared by the consumer) before publishing.

    Usage:
        publisher = QueuePublisher(rabbitmq_url)
        await publisher.connect()
        success = await publisher.publish(Queues.SCAN_JOBS, message_dict)
        # If success is False, caller must set queued_for_scan = True
    """

    def __init__(self, rabbitmq_url: str) -> None:
        self._url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        """
        Establish a robust connection that auto-reconnects on failure.
        Call once at service startup.
        """
        self._connection = await aio_pika.connect_robust(
            self._url,
            reconnect_interval=5,
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)
        log.info("queue_publisher_connected", url=self._url)

    async def publish(
        self,
        queue_name: str,
        message: dict[str, Any],
        priority: int = 0,
    ) -> bool:
        """
        Publish a persistent message to a queue.

        Returns True on success, False on failure.
        The caller is responsible for handling False (e.g. setting queued_for_scan=True).
        """
        if self._channel is None:
            raise QueueConnectionError("Publisher not connected. Call connect() first.")
        try:
            await self._channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    priority=priority,
                ),
                routing_key=queue_name,
            )
            log.info(
                "message_published",
                queue=queue_name,
                event_type=message.get("event_type"),
                event_id=message.get("event_id"),
            )
            return True
        except Exception as e:
            log.error("publish_failed", queue=queue_name, error=str(e))
            return False

    async def close(self) -> None:
        """Gracefully close the connection."""
        if self._connection:
            await self._connection.close()
            log.info("queue_publisher_closed")