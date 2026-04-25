"""
Dead Letter Queue monitoring and recovery module.

Provides:
- Automatic DLQ depth monitoring with Prometheus metrics
- Alert triggering when DLQ depth exceeds threshold
- Message inspection and classification
- Replay mechanism for recoverable failures
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import asyncio
import json
from enum import Enum

import aio_pika
from prometheus_client import Gauge, Counter
from pydantic import BaseModel

from backend.shared.logging import get_logger

logger = get_logger(__name__)

# Prometheus metrics
dlq_depth = Gauge(
    'rabbitmq_dlq_depth',
    'Current number of messages in DLQ',
    ['queue']
)

dlq_messages_replayed = Counter(
    'dlq_messages_replayed_total',
    'Total messages replayed from DLQ',
    ['queue', 'result']  # result: success | failure
)

dlq_messages_archived = Counter(
    'dlq_messages_archived_total',
    'Total messages archived from DLQ',
    ['queue', 'reason']  # reason: poison | permanent_failure | max_retries
)


class FailureReason(str, Enum):
    """Classification of DLQ message failure reasons."""
    POISON_MESSAGE = "poison_message"          # Malformed message
    TRANSIENT_FAILURE = "transient_failure"    # Retry may succeed
    PERMANENT_FAILURE = "permanent_failure"    # Will never succeed
    MAX_RETRIES = "max_retries"               # Exceeded retry limit
    UNKNOWN = "unknown"


class DLQMessage(BaseModel):
    """Represents a message in the DLQ."""
    queue: str
    message_id: str
    body: Dict[str, Any]
    headers: Dict[str, Any]
    timestamp: datetime
    retry_count: int
    failure_reason: Optional[str]
    error_detail: Optional[str]


class DLQMonitor:
    """
    Monitors Dead Letter Queues and provides recovery mechanisms.
    """
    
    # List of all main queues that have DLQs
    MAIN_QUEUES = [
        "scan.jobs",
        "browser.jobs",
        "api.fuzz.jobs",
        "js.analysis.jobs",
        "scenario.jobs",
        "verify.jobs",
        "ai.analysis.jobs",
        "report.jobs",
    ]
    
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
    
    async def connect(self):
        """Establish connection to RabbitMQ."""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        logger.info("DLQ Monitor connected to RabbitMQ")
    
    async def close(self):
        """Close connection to RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("DLQ Monitor disconnected from RabbitMQ")
    
    async def monitor_all_dlqs(self) -> Dict[str, int]:
        """
        Monitor depth of all DLQs and update metrics.
        
        Returns:
            Dict mapping DLQ name to message count
        """
        if not self.channel:
            await self.connect()
        
        dlq_depths = {}
        
        for queue_name in self.MAIN_QUEUES:
            dlq_name = f"{queue_name}.dlq"
            
            try:
                # Passive declare to get queue state without creating
                queue = await self.channel.declare_queue(
                    dlq_name,
                    passive=True
                )
                
                message_count = queue.declaration_result.message_count
                dlq_depths[dlq_name] = message_count
                
                # Update Prometheus metric
                dlq_depth.labels(queue=dlq_name).set(message_count)
                
                if message_count > 0:
                    logger.warning(
                        "DLQ has messages",
                        dlq=dlq_name,
                        count=message_count
                    )
                
            except Exception as e:
                logger.error(
                    "Failed to inspect DLQ",
                    dlq=dlq_name,
                    error=str(e)
                )
        
        return dlq_depths
    
    async def inspect_messages(
        self,
        dlq_name: str,
        limit: int = 100
    ) -> List[DLQMessage]:
        """
        Inspect messages in a DLQ without consuming them.
        
        Args:
            dlq_name: Name of the DLQ to inspect
            limit: Maximum number of messages to inspect
        
        Returns:
            List of message dicts
        """
        if not self.channel:
            await self.connect()
        
        messages = []
        seen_ids: set[str] = set()
        
        try:
            queue = await self.channel.declare_queue(dlq_name, passive=True)

            empty_polls = 0
            while len(messages) < limit:
                message = await queue.get(fail=False)
                if message is None:
                    empty_polls += 1
                    if empty_polls >= 3:
                        break
                    await asyncio.sleep(0.05)
                    continue
                empty_polls = 0

                # Parse message
                try:
                    body = json.loads(message.body.decode('utf-8'))
                except Exception:
                    body = {"raw": message.body.decode('utf-8', errors='replace')}

                # Extract retry count from headers
                retry_count = 0
                if message.headers:
                    retry_count = message.headers.get('x-retry-count', 0)

                msg = DLQMessage(
                    queue=dlq_name.replace('.dlq', ''),
                    message_id=message.message_id or "unknown",
                    body=body,
                    headers=dict(message.headers) if message.headers else {},
                    timestamp=message.timestamp or datetime.now(timezone.utc),
                    retry_count=retry_count,
                    failure_reason=message.headers.get('x-failure-reason') if message.headers else None,
                    error_detail=message.headers.get('x-error-detail') if message.headers else None
                )
                if msg.message_id in seen_ids:
                    await message.reject(requeue=True)
                    break
                seen_ids.add(msg.message_id)
                messages.append(msg)

                # Reject message back to queue (return without consuming)
                await message.reject(requeue=True)
            
            logger.info(
                "Inspected DLQ messages",
                dlq=dlq_name,
                count=len(messages)
            )
            
        except Exception as e:
            logger.error(
                "Failed to inspect DLQ messages",
                dlq=dlq_name,
                error=str(e),
                exc_info=True
            )
        
        return messages
    
    def classify_failure(self, message: DLQMessage | Dict[str, Any]) -> FailureReason:
        """
        Classify the failure reason for a DLQ message.
        
        Args:
            message: DLQMessage dict to classify
        
        Returns:
            FailureReason enum value
        """
        if isinstance(message, DLQMessage):
            body = message.body
            retry_count = message.retry_count
            failure_reason = message.failure_reason
            error_detail = message.error_detail
        else:
            body = message.get('body')
            retry_count = message.get('retry_count', 0)
            failure_reason = message.get('failure_reason')
            error_detail = message.get('error_detail')

        # Check if message is malformed (poison message)
        if not isinstance(body, dict):
            return FailureReason.POISON_MESSAGE
        
        if 'event_type' not in body:
            return FailureReason.POISON_MESSAGE
        
        # Check retry count
        if retry_count >= 3:
            return FailureReason.MAX_RETRIES
        
        # Check explicit failure reason in headers
        if failure_reason:
            failure_reason_lower = failure_reason.lower()
            if 'schema' in failure_reason_lower:
                return FailureReason.PERMANENT_FAILURE
            if 'validation' in failure_reason_lower:
                return FailureReason.PERMANENT_FAILURE
        
        # Check error detail for transient failures
        if error_detail:
            transient_keywords = [
                'timeout', 'connection', 'network',
                'temporary', 'unavailable'
            ]
            error_detail_lower = error_detail.lower()
            if any(kw in error_detail_lower for kw in transient_keywords):
                return FailureReason.TRANSIENT_FAILURE
        
        return FailureReason.UNKNOWN
    
    async def replay_message(
        self,
        dlq_name: str,
        message: DLQMessage | Dict[str, Any],
        target_queue: Optional[str] = None
    ) -> bool:
        """
        Replay a message from DLQ to target queue.
        
        Args:
            dlq_name: Name of the source DLQ
            message: message dict to replay
            target_queue: Optional target queue (defaults to original queue)
        
        Returns:
            True if replay succeeded, False otherwise
        """
        if not self.channel:
            await self.connect()
        
        # Default target is the original queue
        if target_queue is None:
            target_queue = dlq_name.replace('.dlq', '')
        
        try:
            # Prepare headers
            # Handle both DLQMessage objects and dicts
            if isinstance(message, DLQMessage):
                body = message.body
                headers = message.headers.copy()
                msg_id = message.message_id
                retry_count = message.retry_count
            else:
                body = message.get('body', {})
                headers = message.get('headers', {}).copy()
                msg_id = message.get('message_id', 'unknown')
                retry_count = message.get('retry_count', 0)
            
            # Increment retry count
            new_retry_count = retry_count + 1
            
            headers['x-retry-count'] = new_retry_count
            headers['x-replayed-at'] = datetime.now(timezone.utc).isoformat()
            headers['x-replayed-from'] = dlq_name
            
            # Publish to target queue
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(body).encode('utf-8'),
                    headers=headers,
                    message_id=msg_id,
                    timestamp=datetime.now(timezone.utc)
                ),
                routing_key=target_queue
            )
            
            # Remove from DLQ
            queue = await self.channel.declare_queue(dlq_name, passive=True)
            async with queue.iterator() as queue_iter:
                async for dlq_msg in queue_iter:
                    msg_id_to_match = message.message_id if isinstance(message, DLQMessage) else message.get('message_id', 'unknown')
                    if dlq_msg.message_id == msg_id_to_match:
                        await dlq_msg.ack()
                        break
            
            dlq_messages_replayed.labels(queue=target_queue, result='success').inc()
            
            logger.info(
                "Replayed DLQ message",
                dlq=dlq_name,
                target_queue=target_queue,
                message_id=msg_id,
                retry_count=new_retry_count
            )
            
            return True
            
        except Exception as e:
            dlq_messages_replayed.labels(queue=target_queue, result='failure').inc()
            
            logger.error(
                "Failed to replay DLQ message",
                dlq=dlq_name,
                message_id=msg_id if 'msg_id' in locals() else 'unknown',
                error=str(e),
                exc_info=True
            )
            
            return False
    
    async def archive_message(
        self,
        dlq_name: str,
        message: DLQMessage | Dict[str, Any],
        reason: FailureReason
    ) -> bool:
        """
        Archive a message from DLQ to permanent storage.
        
        Args:
            dlq_name: Name of the source DLQ
            message: message dict to archive
            reason: Reason for archiving
        
        Returns:
            True if archive succeeded, False otherwise
        """
        try:
            # In production, would write to S3, database, etc.
            # For now, just log and remove from DLQ
            
            if isinstance(message, DLQMessage):
                msg_id = message.message_id
                body = message.body
                error_detail = message.error_detail
            else:
                msg_id = message.get('message_id', 'unknown')
                body = message.get('body')
                error_detail = message.get('error_detail')

            logger.warning(
                "Archiving DLQ message",
                dlq=dlq_name,
                message_id=msg_id,
                reason=reason.value,
                body=body,
                error_detail=error_detail
            )
            
            # Remove from DLQ
            queue = await self.channel.declare_queue(dlq_name, passive=True)
            async with queue.iterator() as queue_iter:
                async for dlq_msg in queue_iter:
                    msg_id_to_match = message.message_id if isinstance(message, DLQMessage) else message.get('message_id', 'unknown')
                    if dlq_msg.message_id == msg_id_to_match:
                        await dlq_msg.ack()
                        break
            
            dlq_messages_archived.labels(queue=dlq_name, reason=reason.value).inc()
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to archive DLQ message",
                dlq=dlq_name,
                message_id=msg_id if 'msg_id' in locals() else 'unknown',
                error=str(e),
                exc_info=True
            )
            
            return False
    
    async def auto_recover_dlq(self, dlq_name: str) -> Dict[str, int]:
        """
        Automatically recover messages from a DLQ based on failure classification.
        
        - Transient failures: Replay to original queue
        - Poison messages: Archive
        - Max retries: Archive
        - Permanent failures: Archive
        
        Args:
            dlq_name: Name of the DLQ to recover
        
        Returns:
            Dictionary with recovery statistics
        """
        stats = {
            'inspected': 0,
            'replayed': 0,
            'archived': 0,
            'failed': 0
        }
        
        logger.info("Starting auto-recovery for DLQ", dlq=dlq_name)
        
        messages = await self.inspect_messages(dlq_name, limit=1000)
        stats['inspected'] = len(messages)
        
        for message in messages:
            failure_reason = self.classify_failure(message)
            message_id = message.message_id if isinstance(message, DLQMessage) else message.get('message_id', 'unknown')
            retry_count = message.retry_count if isinstance(message, DLQMessage) else message.get('retry_count', 0)
            
            logger.info(
                "Processing DLQ message",
                dlq=dlq_name,
                message_id=message_id,
                failure_reason=failure_reason.value,
                retry_count=retry_count
            )
            
            if failure_reason == FailureReason.TRANSIENT_FAILURE and retry_count < 3:
                # Replay transient failures
                success = await self.replay_message(dlq_name, message)
                if success:
                    stats['replayed'] += 1
                else:
                    stats['failed'] += 1
            else:
                # Archive everything else
                success = await self.archive_message(dlq_name, message, failure_reason)
                if success:
                    stats['archived'] += 1
                else:
                    stats['failed'] += 1
        
        logger.info(
            "Completed auto-recovery for DLQ",
            dlq=dlq_name,
            stats=stats
        )
        
        return stats


# Monitoring job for scheduler
async def monitor_all_dlqs_job(rabbitmq_url: str):
    """
    Scheduled job to monitor all DLQs.
    Called every 60 seconds by APScheduler.
    """
    monitor = DLQMonitor(rabbitmq_url)
    
    try:
        await monitor.connect()
        depths = await monitor.monitor_all_dlqs()
        
        # Check for alerts
        for dlq_name, depth in depths.items():
            if depth > 0:
                logger.warning(
                    "DLQ alert: messages present",
                    dlq=dlq_name,
                    depth=depth
                )
                
                # Optional: Trigger auto-recovery for specific queues
                # if depth > 10:
                #     await monitor.auto_recover_dlq(dlq_name)
        
    finally:
        await monitor.close()
