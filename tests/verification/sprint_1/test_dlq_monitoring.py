"""
Test verification for Issue #2: Dead Letter Queue Blind Spot

These tests verify that DLQ messages are monitored, visible, and can be recovered.
"""

import pytest
import json
import aio_pika
from uuid import uuid4
from datetime import datetime, timezone


async def _purge_queue(rabbitmq_client, queue_name: str) -> None:
    channel = await rabbitmq_client.get_channel()
    try:
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.purge()
    finally:
        await channel.close()


TEST_DLQ = "scan_jobs.dlq"
METRIC_DLQ = "scan.jobs.dlq"


class TestDLQMonitoring:
    """Tests for DLQ monitoring and recovery."""

    @pytest.mark.asyncio
    async def test_dlq_depth_metrics(self, rabbitmq_client):
        """Verify DLQ depth metrics are emitted."""
        from backend.shared.dlq_monitor import DLQMonitor, dlq_depth
        await _purge_queue(rabbitmq_client, METRIC_DLQ)
        
        monitor = DLQMonitor(rabbitmq_client.url)
        await monitor.connect()
        
        # Inject message into DLQ
        channel = await rabbitmq_client.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps({"test": "failed", "scan_id": str(uuid4())}).encode(),
                message_id="test-dlq-msg-1"
            ),
            routing_key=METRIC_DLQ
        )
        await channel.close()

        # Execute monitoring
        await monitor.monitor_all_dlqs()
        await monitor.close()

        # Verify metric exists
        from prometheus_client import REGISTRY
        for metric in REGISTRY.collect():
            if metric.name == 'rabbitmq_dlq_depth':
                assert len(metric.samples) > 0
                return
        
        pytest.fail("rabbitmq_dlq_depth metric not found")

    @pytest.mark.asyncio
    async def test_dlq_inspection(self, rabbitmq_client):
        """Verify DLQ messages can be inspected."""
        from backend.shared.dlq_monitor import DLQMonitor
        from backend.shared.schemas.envelope import MessageEnvelope
        await _purge_queue(rabbitmq_client, TEST_DLQ)
        
        monitor = DLQMonitor(rabbitmq_client.url)
        await monitor.connect()
        
        # Inject test message
        channel = await rabbitmq_client.get_channel()
        test_scan_id = str(uuid4())
        test_payload = {
            "scan_id": test_scan_id,
            "target": "test.com",
            "error": "simulated_failure"
        }
        
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(test_payload).encode(),
                message_id="inspect-test-msg",
                headers={
                    "x-retry-count": 3,
                    "x-failure-reason": "validation_error",
                    "x-error-detail": "Schema validation failed"
                }
            ),
            routing_key=TEST_DLQ
        )
        await channel.close()

        # Inspect DLQ
        messages = await monitor.inspect_messages(TEST_DLQ, limit=10)
        await monitor.close()
        
        assert len(messages) >= 1
        msg = next(
            (
                m
                for m in messages
                if isinstance(m.body, dict) and m.body.get("scan_id") == test_scan_id
            ),
            None,
        )
        assert msg is not None
        assert msg.body["scan_id"] == test_scan_id
        assert msg.retry_count == 3

    @pytest.mark.asyncio
    async def test_dlq_message_classification(self, rabbitmq_client):
        """Verify DLQ messages are correctly classified."""
        from backend.shared.dlq_monitor import DLQMonitor, FailureReason
        
        monitor = DLQMonitor(rabbitmq_client.url)
        
        # Test poison message classification
        poison_msg = {
            "queue": "scan_jobs",
            "message_id": "poison-1",
            "body": "invalid-json",  # Not parseable
            "headers": {},
            "timestamp": datetime.now(timezone.utc),
            "retry_count": 0,
            "failure_reason": None,
            "error_detail": None
        }
        
        classification = monitor.classify_failure(poison_msg)
        assert classification == FailureReason.POISON_MESSAGE
        
        # Test max retries classification
        max_retry_msg = {
            "queue": "scan_jobs",
            "message_id": "max-retry-1",
            "body": {"event_type": "scan.start"},
            "headers": {},
            "timestamp": datetime.now(timezone.utc),
            "retry_count": 5,
            "failure_reason": None,
            "error_detail": None
        }
        
        classification = monitor.classify_failure(max_retry_msg)
        assert classification == FailureReason.MAX_RETRIES
        
        # Test transient failure classification
        transient_msg = {
            "queue": "scan_jobs",
            "message_id": "transient-1",
            "body": {"event_type": "scan.start"},
            "headers": {},
            "timestamp": datetime.now(timezone.utc),
            "retry_count": 1,
            "failure_reason": None,
            "error_detail": "connection timeout to downstream service"
        }
        
        classification = monitor.classify_failure(transient_msg)
        assert classification == FailureReason.TRANSIENT_FAILURE

    @pytest.mark.asyncio
    async def test_dlq_auto_recovery(self, rabbitmq_client):
        """Verify DLQ auto-recovery works."""
        from backend.shared.dlq_monitor import DLQMonitor, FailureReason
        await _purge_queue(rabbitmq_client, TEST_DLQ)
        
        monitor = DLQMonitor(rabbitmq_client.url)
        await monitor.connect()
        
        # Inject transient failure message
        channel = await rabbitmq_client.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps({"event_type": "scan.start", "scan_id": str(uuid4())}).encode(),
                message_id="recover-test-1",
                headers={
                    "x-retry-count": 1,
                    "x-failure-reason": "connection_timeout"
                }
            ),
            routing_key=TEST_DLQ
        )
        await channel.close()

        # Run auto-recovery
        stats = await monitor.auto_recover_dlq(TEST_DLQ)
        await monitor.close()
        
        # Should have inspected and replayed
        assert stats["inspected"] >= 1
        # Message should be replayed (transient failure, retry_count < 3)
        assert stats["replayed"] + stats["archived"] >= 1

    @pytest.mark.asyncio
    async def test_dlq_scheduled_monitoring(self, rabbitmq_client):
        """Verify scheduled DLQ monitoring job works."""
        from backend.shared.dlq_monitor import monitor_all_dlqs_job
        
        # Run the scheduled job
        await monitor_all_dlqs_job(rabbitmq_client.url)
        
        # If it runs without error, test passes
        assert True


class TestDLQAPIEndpoints:
    """Tests for DLQ API endpoints."""

    @pytest.mark.asyncio
    async def test_dlq_monitor_endpoint(self, client, rabbitmq_client):
        """Test GET /api/v1/queue/dlq/monitor endpoint."""
        await _purge_queue(rabbitmq_client, TEST_DLQ)
        # Inject message into DLQ
        channel = await rabbitmq_client.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps({"test": "data"}).encode(),
                message_id="api-test-1"
            ),
            routing_key=TEST_DLQ
        )
        await channel.close()
        
        # Call API
        response = client.get("/api/v1/queue/dlq/monitor")
        
        assert response.status_code == 200
        data = response.json()
        assert "dlqs" in data
        assert isinstance(data["dlqs"], dict)
        assert "timestamp" in data
        assert "total_messages" in data

    @pytest.mark.asyncio
    async def test_dlq_inspect_endpoint(self, client, rabbitmq_client):
        """Test GET /api/v1/queue/dlq/{dlq_name}/inspect endpoint."""
        await _purge_queue(rabbitmq_client, TEST_DLQ)
        # Inject message into DLQ
        channel = await rabbitmq_client.get_channel()
        test_payload = {"scan_id": str(uuid4()), "error": "test_error"}
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(test_payload).encode(),
                message_id="inspect-api-test"
            ),
            routing_key=TEST_DLQ
        )
        await channel.close()
        
        # Call API
        response = client.get("/api/v1/queue/dlq/scan_jobs.dlq/inspect")
        
        assert response.status_code == 200
        data = response.json()
        assert "dlq" in data
        assert data["dlq"] == "scan_jobs"
        assert "messages" in data
        assert "count" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_dlq_replay_endpoint(self, client, rabbitmq_client):
        """Test POST /api/v1/queue/dlq/{dlq_name}/replay endpoint."""
        await _purge_queue(rabbitmq_client, TEST_DLQ)
        # Inject message into DLQ
        channel = await rabbitmq_client.get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps({"test": "replay"}).encode(),
                message_id="replay-test-msg"
            ),
            routing_key=TEST_DLQ
        )
        await channel.close()
        
        # Call API to replay
        response = client.post(
            "/api/v1/queue/dlq/scan_jobs.dlq/replay",
            json={"message_ids": ["replay-test-msg"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dlq" in data
        assert "mode" in data
        assert "replayed" in data
        assert "failed" in data
