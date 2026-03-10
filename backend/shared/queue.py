"""
AttackBot shared RabbitMQ queue utilities.
Provides queue name constants and an async publisher with passive declare.
"""
import json
import asyncio
from typing import Any
import aio_pika
from aio_pika import ExchangeType
from shared.logging import get_logger

log = get_logger(__name__)


class Queues:
    """Canonical queue name constants. Every queue has a paired DLQ."""
    SCAN_JOBS = "scan.jobs"
    SCAN_JOBS_DLQ = "scan.jobs.dlq"

    BROWSER_JOBS = "browser.jobs"
    BROWSER_JOBS_DLQ = "browser.jobs.dlq"

    API_FUZZ_JOBS = "api.fuzz.jobs"
    API_FUZZ_JOBS_DLQ = "api.fuzz.jobs.dlq"

    JS_ANALYSIS_JOBS = "js.analysis.jobs"
    JS_ANALYSIS_JOBS_DLQ = "js.analysis.jobs.dlq"

    SCENARIO_JOBS = "scenario.jobs"
    SCENARIO_JOBS_DLQ = "scenario.jobs.dlq"

    VERIFY_JOBS = "verify.jobs"
    VERIFY_JOBS_DLQ = "verify.jobs.dlq"

    AI_ANALYSIS_JOBS = "ai.analysis.jobs"
    AI_ANALYSIS_JOBS_DLQ = "ai.analysis.jobs.dlq"

    REPORT_JOBS = "report.jobs"
    REPORT_JOBS_DLQ = "report.jobs.dlq"

    REPORTS_COMPLETED = "reports.completed"


class QueuePublisher:
    """
    Async RabbitMQ publisher.

    Uses passive queue declaration to avoid argument mismatch errors
    when queues were previously created with different arguments.

    On publish failure, returns False rather than raising — callers
    must handle this and set queued_for_scan=True or equivalent.
    """

    def __init__(self, rabbitmq_url: str):
        self._url = rabbitmq_url
        self._connection: aio_pika.Connection | None = None
        self._channel: aio_pika.Channel | None = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ. Retries on failure."""
        retries = 0
        max_retries = 10
        while retries < max_retries:
            try:
                self._connection = await aio_pika.connect_robust(self._url)
                self._channel = await self._connection.channel()
                log.info("queue_publisher_connected", url=self._url)
                return
            except Exception as e:
                retries += 1
                wait = min(5 * retries, 30)
                log.warning("queue_publisher_connect_failed",
                            attempt=retries, wait=wait, error=str(e))
                await asyncio.sleep(wait)
        raise ConnectionError(f"Failed to connect to RabbitMQ after {max_retries} attempts")

    async def publish(self, queue_name: str, message: dict[str, Any]) -> bool:
        """
        Publish a message to the specified queue.
        Returns True on success, False on failure.
        Never raises — callers must check the return value.
        """
        try:
            if self._channel is None or self._channel.is_closed:
                await self.connect()

            body = json.dumps(message, default=str).encode()
            await self._channel.default_exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type="application/json",
                ),
                routing_key=queue_name,
            )
            log.info("message_published", queue=queue_name,
                     event_type=message.get("event_type", "unknown"))
            return True
        except Exception as e:
            log.error("message_publish_failed", queue=queue_name, error=str(e))
            return False

    async def close(self) -> None:
        """Close the RabbitMQ connection gracefully."""
        try:
            if self._channel and not self._channel.is_closed:
                await self._channel.close()
            if self._connection and not self._connection.is_closed:
                await self._connection.close()
        except Exception as e:
            log.warning("queue_publisher_close_error", error=str(e))
