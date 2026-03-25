# backend/shared/queue.py
import json
from dataclasses import dataclass
from typing import Any, Iterable

import aio_pika
import aio_pika.abc
from kombu import Queue as KombuQueue

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


@dataclass(frozen=True)
class QueueSpec:
    name: str
    dlq_name: str | None = None


QUEUE_SPECS: dict[str, QueueSpec] = {
    Queues.SCAN_JOBS: QueueSpec(Queues.SCAN_JOBS, Queues.SCAN_JOBS_DLQ),
    Queues.BROWSER_JOBS: QueueSpec(Queues.BROWSER_JOBS, Queues.BROWSER_JOBS_DLQ),
    Queues.API_FUZZ_JOBS: QueueSpec(Queues.API_FUZZ_JOBS, Queues.API_FUZZ_JOBS_DLQ),
    Queues.JS_ANALYSIS_JOBS: QueueSpec(Queues.JS_ANALYSIS_JOBS, Queues.JS_ANALYSIS_DLQ),
    Queues.SCENARIO_JOBS: QueueSpec(Queues.SCENARIO_JOBS, Queues.SCENARIO_JOBS_DLQ),
    Queues.VERIFY_JOBS: QueueSpec(Queues.VERIFY_JOBS, Queues.VERIFY_JOBS_DLQ),
    Queues.AI_ANALYSIS_JOBS: QueueSpec(Queues.AI_ANALYSIS_JOBS, Queues.AI_ANALYSIS_DLQ),
    Queues.REPORT_JOBS: QueueSpec(Queues.REPORT_JOBS, Queues.REPORT_JOBS_DLQ),
    Queues.REPORTS_COMPLETED: QueueSpec(Queues.REPORTS_COMPLETED),
}


def dead_letter_arguments(queue_name: str) -> dict[str, str] | None:
    """
    Return RabbitMQ queue declaration arguments for the given queue.

    Main queues are configured to dead-letter directly into their paired DLQ.
    Queues without DLQ pairing return None.
    """
    spec = QUEUE_SPECS.get(queue_name)
    if spec is None or spec.dlq_name is None:
        return None
    return {
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": spec.dlq_name,
    }


def passive_queue_binding(queue_name: str) -> KombuQueue:
    """
    Return a durable Kombu queue bound to existing broker state without redeclare.

    Queue topology is created elsewhere in the stack. In this Kombu version,
    ``passive=True`` is not preserved on Queue instances, so ``no_declare=True``
    is the reliable way to avoid 406 PRECONDITION_FAILED errors when consumers
    encounter queues that were already created with persisted arguments.
    """
    return KombuQueue(queue_name, durable=True, no_declare=True)


def _resolve_queue_specs(queue_names: Iterable[str] | None = None) -> list[QueueSpec]:
    names = list(queue_names) if queue_names is not None else list(QUEUE_SPECS.keys())
    specs: list[QueueSpec] = []
    for name in names:
        spec = QUEUE_SPECS.get(name)
        if spec is None:
            specs.append(QueueSpec(name))
        else:
            specs.append(spec)
    return specs


async def ensure_queue_topology(
    rabbitmq_url: str,
    queue_names: Iterable[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Declare durable queues and DLQs for the requested queue names.

    Main queues use the default exchange and dead-letter directly into their
    paired ``*.dlq`` queue. This keeps the topology simple while making worker
    loss and reject paths visible to operators.
    """
    connection = await aio_pika.connect_robust(
        rabbitmq_url,
        reconnect_interval=5,
    )
    channel: aio_pika.abc.AbstractChannel | None = None
    try:
        channel = await connection.channel()
        topology: dict[str, dict[str, Any]] = {}
        for spec in _resolve_queue_specs(queue_names):
            dlq_routing_configured = False
            if spec.dlq_name:
                await channel.declare_queue(spec.dlq_name, durable=True)
                queue_arguments = dead_letter_arguments(spec.name)
                try:
                    await channel.declare_queue(
                        spec.name,
                        durable=True,
                        arguments=queue_arguments,
                    )
                    dlq_routing_configured = True
                except Exception as exc:
                    # Backward compatibility for already-declared queues with
                    # mismatched arguments in long-lived RabbitMQ volumes.
                    err_text = str(exc)
                    if "PRECONDITION_FAILED" in err_text or "inequivalent arg" in err_text:
                        await channel.declare_queue(spec.name, passive=True)
                        log.warning(
                            "queue_dead_letter_args_mismatch",
                            queue=spec.name,
                            dlq=spec.dlq_name,
                            error=err_text,
                            note="Delete/recreate queue to apply DLQ routing args",
                        )
                    else:
                        raise
            else:
                await channel.declare_queue(spec.name, durable=True)
            topology[spec.name] = {
                "queue": spec.name,
                "dlq": spec.dlq_name,
                "durable": True,
                "dlq_routing_configured": dlq_routing_configured,
            }
        log.info("queue_topology_ready", queues=list(topology.keys()))
        return topology
    finally:
        if channel is not None:
            await channel.close()
        await connection.close()


async def inspect_queue_states(
    rabbitmq_url: str,
    queue_names: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Inspect queue existence and message counts using passive declarations.
    """
    connection = await aio_pika.connect_robust(
        rabbitmq_url,
        reconnect_interval=5,
    )
    channel: aio_pika.abc.AbstractChannel | None = None
    try:
        channel = await connection.channel()
        states: list[dict[str, Any]] = []
        seen: set[str] = set()
        for spec in _resolve_queue_specs(queue_names):
            names = [spec.name]
            if spec.dlq_name:
                names.append(spec.dlq_name)
            for queue_name in names:
                if queue_name in seen:
                    continue
                seen.add(queue_name)
                try:
                    queue = await channel.declare_queue(queue_name, passive=True)
                    declare_ok = getattr(queue, "declaration_result", None)
                    states.append(
                        {
                            "queue": queue_name,
                            "exists": True,
                            "messages": getattr(declare_ok, "message_count", None),
                            "consumers": getattr(declare_ok, "consumer_count", None),
                        }
                    )
                except Exception as exc:
                    states.append(
                        {
                            "queue": queue_name,
                            "exists": False,
                            "messages": None,
                            "consumers": None,
                            "error": str(exc),
                        }
                    )
        return states
    finally:
        if channel is not None:
            await channel.close()
        await connection.close()


async def check_rabbitmq_health(
    rabbitmq_url: str,
    required_queues: Iterable[str] | None = None,
) -> bool:
    """
    Return True only if RabbitMQ is reachable and all requested queues exist.
    """
    try:
        states = await inspect_queue_states(rabbitmq_url, required_queues)
    except Exception as exc:
        log.warning("rabbitmq_health_check_failed", error=str(exc))
        return False
    return all(state["exists"] for state in states)


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
        self._validated_queues: set[str] = set()

    async def connect(
        self,
        bootstrap_queues: Iterable[str] | None = None,
    ) -> None:
        """
        Establish a robust connection that auto-reconnects on failure.
        Call once at service startup.
        """
        if bootstrap_queues is not None:
            await ensure_queue_topology(self._url, bootstrap_queues)
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
            if queue_name not in self._validated_queues:
                await self._channel.declare_queue(queue_name, passive=True)
                self._validated_queues.add(queue_name)
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
