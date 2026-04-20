# Sprint #1: P0 - Data Integrity

> **Document Type:** Implementation Guide  
> **Target Audience:** Senior Engineers, Architects, QA Team  
> **Date:** 2026-04-19  
> **Branch:** M4_ReadTheRoom  
> **Duration:** Weeks 1-2  
> **Status:** Ready for Implementation  

---

## Sprint Overview

**Theme:** *Eliminate data loss and stuck state*  
**Business Impact:** **Critical** — Prevents scan data loss, duplicate processing, and message loss  
**Sprint Goal:** All scans complete successfully, no duplicates, full visibility into failures

### Key Outcomes

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Stuck scans >2h | Unknown | **0** | Prometheus: `stuck_scans_current` |
| Message redelivery | Duplicate processing | **0 duplicates** | DB: `idempotency_keys` table |
| DLQ visibility | None | **Full visibility** | API + Grafana |
| Watchdog reliability | Silent failures | **100% execution** | Prometheus: `watchdog_executions_total` |

---

## Sprint Statistics

| Attribute | Value |
|-----------|-------|
| **Priority** | P0 (Critical) |
| **Effort** | 18-24 hours |
| **Issues** | 3 |
| **Team Weeks** | 2-2.5 weeks |
| **Assignees** | 2 Engineers |

---

## Issues Included

| # | Issue | Category | Severity | Effort | Assignee | Days |
|---|-------|----------|----------|--------|----------|-------|
| **1** | Watchdog Scan Recovery Mechanism Failure | Critical | 🔴 | 4-6h | Engineer A | Day 1-2 |
| **3** | Idempotency Guarantee Gaps | Critical | 🔴 | 8-10h | Engineer A | Day 1-5 |
| **2** | Dead Letter Queue Blind Spot | Critical | 🔴 | 6-8h | Engineer B | Day 3-5 |

---

## Issue #1: Watchdog Scan Recovery Mechanism Failure

### Objective
Ensure watchdog reliably marks stuck scans as `failed_internal` and provides full observability.

### Problem Statement
Watchdog doesn't reliably mark stuck scans, lacks metrics/logging. Evidenced by scan `7ee68848-8ba3-4fb6-ab50-24256e2255eb` running for 12+ hours.

### Root Causes
1. **Scheduler Not Starting:** APScheduler job may not be registering during service startup
2. **Silent Exception Handling:** Exceptions caught but suppressed without re-raising
3. **Query Logic Error:** SQL query may not correctly identify stuck scans
4. **Timezone Mismatch:** Comparison between `started_at` (UTC) and `datetime.now()` (local) causes incorrect time delta

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 1 | Add Prometheus metrics to watchdog | `watchdog.py` | 1h | Engineer A |
| 1 | Add comprehensive logging (start/end/in-progress) | `watchdog.py` | 1h | Engineer A |
| 1 | Fix silent exception handling (re-raise after logging) | `watchdog.py` | 1h | Engineer A |
| 1 | Add startup verification of watchdog job | `main.py` | 1h | Engineer A |
| 2 | Add timezone-aware timestamp validation | `watchdog.py`, `alembic/versions/005_...py` | 2h | Engineer A |
| 2 | Test watchdog with stuck scan simulation | Test scripts | 2h | Engineer A |

### Solution Code

#### 1. Enhanced Watchdog Implementation

```python
# File: backend/services/core_engine/watchdog.py

from datetime import datetime, timedelta, timezone
from typing import List
from prometheus_client import Counter, Gauge
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.repository import ScanRepository
from backend.shared.db import get_session
from backend.shared.logging import get_logger

logger = get_logger(__name__)
config = EngineConfig()

# Prometheus metrics
watchdog_executions = Counter(
    'watchdog_executions_total',
    'Total watchdog executions'
)
watchdog_scans_recovered = Counter(
    'watchdog_scans_recovered_total',
    'Total scans recovered by watchdog'
)
watchdog_errors = Counter(
    'watchdog_errors_total',
    'Total watchdog errors'
)
stuck_scans_gauge = Gauge(
    'stuck_scans_current',
    'Current number of stuck scans'
)

async def recover_stuck_scans():
    """
    Mark scans running longer than threshold as failed_internal.
    
    This function:
    1. Queries for scans with status='running' that started before threshold
    2. Marks each as failed_internal with error detail
    3. Logs recovery actions and metrics
    4. Re-raises exceptions to ensure visibility
    """
    execution_start = datetime.now(timezone.utc)
    
    logger.info(
        "Watchdog starting scan recovery check",
        threshold_seconds=config.watchdog_stale_threshold,
        execution_time=execution_start.isoformat()
    )
    
    watchdog_executions.inc()
    
    try:
        async with get_session() as session:
            repo = ScanRepository(session)
            
            # Calculate threshold with explicit timezone
            threshold = datetime.now(timezone.utc) - timedelta(
                seconds=config.watchdog_stale_threshold
            )
            
            logger.info(
                "Watchdog threshold calculated",
                threshold=threshold.isoformat(),
                current_time=datetime.now(timezone.utc).isoformat()
            )
            
            # Query for stuck scans with explicit status filter
            result = await session.execute(
                select(Scan)
                .where(Scan.status == "running")
                .where(Scan.started_at < threshold)
            )
            stuck_scans = result.scalars().all()
            
            scan_count = len(stuck_scans)
            stuck_scans_gauge.set(scan_count)
            
            logger.info(
                "Watchdog found stuck scans",
                count=scan_count,
                scan_ids=[str(s.scan_id) for s in stuck_scans]
            )
            
            if scan_count == 0:
                logger.info("Watchdog completed: no stuck scans found")
                return
            
            # Process each stuck scan
            recovered_count = 0
            for scan in stuck_scans:
                runtime = datetime.now(timezone.utc) - scan.started_at
                
                logger.warning(
                    "Recovering stuck scan",
                    scan_id=str(scan.scan_id),
                    program_id=str(scan.program_id),
                    started_at=scan.started_at.isoformat(),
                    runtime_seconds=runtime.total_seconds(),
                    threshold_seconds=config.watchdog_stale_threshold
                )
                
                try:
                    await repo.mark_scan_complete(
                        scan_id=scan.scan_id,
                        status="failed_internal",
                        finding_count=0,
                        severity_breakdown={},
                        error_detail=f"Watchdog recovery: scan exceeded {config.watchdog_stale_threshold}s threshold (runtime: {runtime.total_seconds()}s)"
                    )
                    
                    recovered_count += 1
                    watchdog_scans_recovered.inc()
                    
                    logger.info(
                        "Successfully recovered stuck scan",
                        scan_id=str(scan.scan_id),
                        runtime_seconds=runtime.total_seconds()
                    )
                except Exception as scan_error:
                    logger.error(
                        "Failed to recover individual scan",
                        scan_id=str(scan.scan_id),
                        error=str(scan_error),
                        exc_info=True
                    )
                    # Continue processing other scans
            
            execution_duration = (datetime.now(timezone.utc) - execution_start).total_seconds()
            
            logger.info(
                "Watchdog completed",
                scans_found=scan_count,
                scans_recovered=recovered_count,
                execution_duration_seconds=execution_duration
            )
            
    except Exception as e:
        watchdog_errors.inc()
        logger.error(
            "Watchdog recovery failed critically",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        # Re-raise to ensure visibility in logs and metrics
        raise

def start_watchdog(scheduler: AsyncIOScheduler):
    """
    Register watchdog job with scheduler.
    
    Args:
        scheduler: APScheduler instance
    """
    logger.info(
        "Registering watchdog job",
        interval_seconds=config.watchdog_interval_seconds,
        stale_threshold_seconds=config.watchdog_stale_threshold
    )
    
    scheduler.add_job(
        recover_stuck_scans,
        trigger='interval',
        seconds=config.watchdog_interval_seconds,
        id='scan_watchdog',
        replace_existing=True,
        max_instances=1,  # Prevent overlapping executions
        coalesce=True,    # Combine missed runs into one
        misfire_grace_time=30  # Allow 30s grace period for missed runs
    )
    
    logger.info("Watchdog job registered successfully")
```

#### 2. Enhanced Lifespan with Verification

```python
# File: backend/services/core_engine/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Core Engine starting up")
    
    # Initialize infrastructure
    init_db(settings.database_url)
    init_storage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure
    )
    
    # Initialize queue topology
    await ensure_queue_topology(settings.rabbitmq_url)
    
    # Start scheduler
    global scheduler
    scheduler = AsyncIOScheduler()
    
    # Register watchdog with verification
    try:
        start_watchdog(scheduler)
        logger.info("Watchdog registration completed")
    except Exception as e:
        logger.error(f"Failed to register watchdog: {e}", exc_info=True)
        raise
    
    # Start scheduler and verify
    scheduler.start()
    logger.info(
        "Scheduler started",
        jobs=[job.id for job in scheduler.get_jobs()]
    )
    
    # Verify watchdog job is scheduled
    watchdog_job = scheduler.get_job('scan_watchdog')
    if watchdog_job:
        logger.info(
            "Watchdog job verified",
            next_run_time=watchdog_job.next_run_time.isoformat() if watchdog_job.next_run_time else None
        )
    else:
        logger.error("Watchdog job not found in scheduler - CRITICAL")
        raise RuntimeError("Watchdog job registration failed")
    
    yield
    
    logger.info("Core Engine shutting down")
    scheduler.shutdown(wait=True)
```

#### 3. Database Migration for Timezone Awareness

```python
# File: alembic/versions/005_ensure_timezone_aware_timestamps.py

"""ensure timezone-aware timestamps

Revision ID: 005
Revises: 004
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade():
    # Ensure all timestamp columns are timezone-aware
    # PostgreSQL: TIMESTAMP WITH TIME ZONE
    
    # Convert scans.started_at to timestamptz
    op.execute("""
        ALTER TABLE scans 
        ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE 
        USING started_at AT TIME ZONE 'UTC'
    """)
    
    # Convert scans.completed_at to timestamptz
    op.execute("""
        ALTER TABLE scans 
        ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE 
        USING completed_at AT TIME ZONE 'UTC'
    """)
    
    # Convert scan_stages timestamps
    op.execute("""
        ALTER TABLE scan_stages 
        ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE 
        USING started_at AT TIME ZONE 'UTC'
    """)
    
    op.execute("""
        ALTER TABLE scan_stages 
        ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE 
        USING completed_at AT TIME ZONE 'UTC'
    """)
    
    # Convert reports timestamps
    op.execute("""
        ALTER TABLE reports 
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
        USING created_at AT TIME ZONE 'UTC'
    """)
    
    op.execute("""
        ALTER TABLE reports 
        ALTER COLUMN generated_at TYPE TIMESTAMP WITH TIME ZONE 
        USING generated_at AT TIME ZONE 'UTC'
    """)

def downgrade():
    # Revert to timestamp without timezone
    op.execute("ALTER TABLE scans ALTER COLUMN started_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE scans ALTER COLUMN completed_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE scan_stages ALTER COLUMN started_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE scan_stages ALTER COLUMN completed_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE reports ALTER COLUMN created_at TYPE TIMESTAMP")
    op.execute("ALTER TABLE reports ALTER COLUMN generated_at TYPE TIMESTAMP")
```

### Acceptance Criteria

- [ ] `watchdog_executions_total` metric increments on every run
- [ ] `watchdog_scans_recovered_total` metric increments per recovered scan
- [ ] Watchdog logs: start time, threshold, scans found, recovery actions, completion
- [ ] Startup fails if watchdog job not registered
- [ ] Stuck scan test: Inject a scan stuck for >2h, verify auto-recovery
- [ ] Timezone test: Verify UTC timestamps in DB and code

### Rollback Strategy

**Rollback Time:** <5 minutes

```bash
# Revert watchdog.py
cd /path/to/backend/services/core_engine
git checkout HEAD~1 -- watchdog.py

# Revert main.py  
git checkout HEAD~1 -- main.py
```

### Testing Checklist

- [ ] Unit test: Watchdog threshold calculation
- [ ] Unit test: Stuck scan marking logic
- [ ] Integration test: Watchdog + database interaction
- [ ] Manual test: Simulate stuck scan, verify recovery
- [ ] Manual test: Verify Prometheus metrics

---

## Issue #2: Dead Letter Queue Blind Spot

### Objective
Full visibility into DLQ state with automatic monitoring and recovery.

### Problem Statement
Failed messages accumulate in DLQ with no visibility, monitoring, or recovery mechanism. No metrics track DLQ depth, no alerts when messages arrive, no mechanism to replay messages.

### Root Causes
1. **No Monitoring:** No metrics track DLQ depth
2. **No Alerting:** No alerts when messages arrive in DLQ
3. **No Recovery:** No mechanism to replay DLQ messages after fixing root cause
4. **No Inspection:** DLQ inspection endpoint exists but is manual and not integrated with observability

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 3 | Create DLQMonitor service class | `shared/dlq_monitor.py` | 3h | Engineer B |
| 3 | Add Prometheus metrics for DLQ depth | `shared/dlq_monitor.py` | 1h | Engineer B |
| 4 | Implement scheduled monitoring job | `main.py` (both services) | 2h | Engineer B |
| 4 | Add API endpoints for DLQ inspection | `main.py` (Core Engine) | 2h | Engineer B |
| 5 | Test DLQ monitoring with injected failures | Test scripts | 2h | Engineer B |

### Solution Code

#### 1. DLQ Monitor Service

```python
# File: backend/shared/dlq_monitor.py

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
import json
from enum import Enum

import aio_pika
from prometheus_client import Gauge, Counter
from pydantic import BaseModel

from backend.shared.logging import get_logger
from backend.shared.queue import Queues

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
        
        for queue_name in Queues.all():
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
            List of DLQMessage objects
        """
        if not self.channel:
            await self.connect()
        
        messages = []
        
        try:
            queue = await self.channel.declare_queue(dlq_name, passive=True)
            
            for _ in range(min(limit, queue.declaration_result.message_count)):
                # Get message without ack (peek)
                message = await queue.get(no_ack=False)
                
                if message is None:
                    break
                
                # Parse message
                try:
                    body = json.loads(message.body.decode('utf-8'))
                except Exception:
                    body = {"raw": message.body.decode('utf-8', errors='replace')}
                
                # Extract retry count from headers
                retry_count = 0
                if message.headers:
                    retry_count = message.headers.get('x-retry-count', 0)
                
                dlq_msg = DLQMessage(
                    queue=dlq_name.replace('.dlq', ''),
                    message_id=message.message_id or "unknown",
                    body=body,
                    headers=dict(message.headers) if message.headers else {},
                    timestamp=message.timestamp or datetime.now(timezone.utc),
                    retry_count=retry_count,
                    failure_reason=message.headers.get('x-failure-reason') if message.headers else None,
                    error_detail=message.headers.get('x-error-detail') if message.headers else None
                )
                
                messages.append(dlq_msg)
                
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
    
    def classify_failure(self, message: DLQMessage) -> FailureReason:
        """
        Classify the failure reason for a DLQ message.
        
        Args:
            message: DLQMessage to classify
        
        Returns:
            FailureReason enum value
        """
        # Check if message is malformed (poison message)
        if not isinstance(message.body, dict):
            return FailureReason.POISON_MESSAGE
        
        if 'event_type' not in message.body:
            return FailureReason.POISON_MESSAGE
        
        # Check retry count
        if message.retry_count >= 3:
            return FailureReason.MAX_RETRIES
        
        # Check explicit failure reason in headers
        if message.failure_reason:
            if 'schema' in message.failure_reason.lower():
                return FailureReason.PERMANENT_FAILURE
            if 'validation' in message.failure_reason.lower():
                return FailureReason.PERMANENT_FAILURE
        
        # Check error detail for transient failures
        if message.error_detail:
            transient_keywords = [
                'timeout', 'connection', 'network',
                'temporary', 'unavailable'
            ]
            if any(kw in message.error_detail.lower() for kw in transient_keywords):
                return FailureReason.TRANSIENT_FAILURE
        
        return FailureReason.UNKNOWN
    
    async def replay_message(
        self,
        dlq_name: str,
        message: DLQMessage,
        target_queue: Optional[str] = None
    ) -> bool:
        """
        Replay a message from DLQ to target queue.
        
        Args:
            dlq_name: Name of the source DLQ
            message: DLQMessage to replay
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
            # Increment retry count
            new_retry_count = message.retry_count + 1
            
            # Prepare headers
            headers = message.headers.copy()
            headers['x-retry-count'] = new_retry_count
            headers['x-replayed-at'] = datetime.now(timezone.utc).isoformat()
            headers['x-replayed-from'] = dlq_name
            
            # Publish to target queue
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message.body).encode('utf-8'),
                    headers=headers,
                    message_id=message.message_id,
                    timestamp=datetime.now(timezone.utc)
                ),
                routing_key=target_queue
            )
            
            # Remove from DLQ
            # (This requires consuming the original message)
            queue = await self.channel.declare_queue(dlq_name, passive=True)
            async with queue.iterator() as queue_iter:
                async for msg in queue_iter:
                    if msg.message_id == message.message_id:
                        await msg.ack()
                        break
            
            dlq_messages_replayed.labels(queue=target_queue, result='success').inc()
            
            logger.info(
                "Replayed DLQ message",
                dlq=dlq_name,
                target_queue=target_queue,
                message_id=message.message_id,
                retry_count=new_retry_count
            )
            
            return True
            
        except Exception as e:
            dlq_messages_replayed.labels(queue=target_queue, result='failure').inc()
            
            logger.error(
                "Failed to replay DLQ message",
                dlq=dlq_name,
                message_id=message.message_id,
                error=str(e),
                exc_info=True
            )
            
            return False
    
    async def archive_message(
        self,
        dlq_name: str,
        message: DLQMessage,
        reason: FailureReason
    ) -> bool:
        """
        Archive a message from DLQ to permanent storage.
        
        Args:
            dlq_name: Name of the source DLQ
            message: DLQMessage to archive
            reason: Reason for archiving
        
        Returns:
            True if archive succeeded, False otherwise
        """
        try:
            # In production, would write to S3, database, etc.
            # For now, just log and remove from DLQ
            
            logger.warning(
                "Archiving DLQ message",
                dlq=dlq_name,
                message_id=message.message_id,
                reason=reason.value,
                body=message.body,
                error_detail=message.error_detail
            )
            
            # Remove from DLQ
            queue = await self.channel.declare_queue(dlq_name, passive=True)
            async with queue.iterator() as queue_iter:
                async for msg in queue_iter:
                    if msg.message_id == message.message_id:
                        await msg.ack()
                        break
            
            dlq_messages_archived.labels(queue=dlq_name, reason=reason.value).inc()
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to archive DLQ message",
                dlq=dlq_name,
                message_id=message.message_id,
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
            
            logger.info(
                "Processing DLQ message",
                dlq=dlq_name,
                message_id=message.message_id,
                failure_reason=failure_reason.value,
                retry_count=message.retry_count
            )
            
            if failure_reason == FailureReason.TRANSIENT_FAILURE and message.retry_count < 3:
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
```

#### 2. Enhanced API Endpoints

```python
# File: backend/services/core_engine/main.py (add these endpoints)

from backend.shared.dlq_monitor import DLQMonitor, FailureReason

@app.get("/api/v1/queue/dlq/monitor")
async def monitor_dlqs():
    """Get current DLQ depths for all queues."""
    monitor = DLQMonitor(settings.rabbitmq_url)
    
    try:
        await monitor.connect()
        depths = await monitor.monitor_all_dlqs()
        
        return {
            "dlqs": depths,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_messages": sum(depths.values())
        }
    finally:
        await monitor.close()

@app.get("/api/v1/queue/dlq/{dlq_name}/inspect")
async def inspect_dlq_messages(
    dlq_name: str,
    limit: int = Query(default=100, ge=1, le=1000)
):
    """Inspect messages in a specific DLQ."""
    monitor = DLQMonitor(settings.rabbitmq_url)
    
    try:
        await monitor.connect()
        messages = await monitor.inspect_messages(dlq_name, limit=limit)
        
        # Classify failures
        classified = []
        for msg in messages:
            failure_reason = monitor.classify_failure(msg)
            classified.append({
                **msg.dict(),
                "classified_failure": failure_reason.value
            })
        
        return {
            "dlq": dlq_name,
            "messages": classified,
            "count": len(classified),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        await monitor.close()

@app.post("/api/v1/queue/dlq/{dlq_name}/replay")
async def replay_dlq_messages(
    dlq_name: str,
    message_ids: List[str] = None,
    auto_recover: bool = False
):
    """
    Replay messages from DLQ.
    
    - If message_ids provided: Replay specific messages
    - If auto_recover=True: Auto-recover all messages based on classification
    """
    monitor = DLQMonitor(settings.rabbitmq_url)
    
    try:
        await monitor.connect()
        
        if auto_recover:
            # Auto-recover based on failure classification
            stats = await monitor.auto_recover_dlq(dlq_name)
            return {
                "dlq": dlq_name,
                "mode": "auto_recover",
                "stats": stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        elif message_ids:
            # Replay specific messages
            messages = await monitor.inspect_messages(dlq_name, limit=1000)
            
            replayed = 0
            failed = 0
            
            for msg in messages:
                if msg.message_id in message_ids:
                    success = await monitor.replay_message(dlq_name, msg)
                    if success:
                        replayed += 1
                    else:
                        failed += 1
            
            return {
                "dlq": dlq_name,
                "mode": "manual",
                "requested": len(message_ids),
                "replayed": replayed,
                "failed": failed,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either message_ids or set auto_recover=true"
            )
    
    finally:
        await monitor.close()
```

#### 3. Scheduler Integration

```python
# File: backend/services/core_engine/main.py (in lifespan)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup ...
    
    # Register DLQ monitoring job
    scheduler.add_job(
        monitor_all_dlqs_job,
        args=[settings.rabbitmq_url],
        trigger='interval',
        seconds=60,  # Every minute
        id='dlq_monitor',
        replace_existing=True
    )
    
    logger.info("DLQ monitoring job registered")
    
    yield
    
    # ... existing shutdown ...
```

#### 4. Grafana Alert Configuration

```yaml
# File: grafana/alerts/dlq_alerts.yml

groups:
  - name: dlq_alerts
    interval: 60s
    rules:
      - alert: DLQMessagesPresent
        expr: rabbitmq_dlq_depth > 0
        for: 5m
        labels:
          severity: warning
          component: messaging
        annotations:
          summary: "Dead Letter Queue has messages"
          description: "DLQ {{ $labels.queue }} has {{ $value }} messages for over 5 minutes"
      
      - alert: DLQDepthCritical
        expr: rabbitmq_dlq_depth > 100
        for: 1m
        labels:
          severity: critical
          component: messaging
        annotations:
          summary: "Dead Letter Queue depth critical"
          description: "DLQ {{ $labels.queue }} has {{ $value }} messages (critical threshold: 100)"
```

### Acceptance Criteria

- [ ] `rabbitmq_dlq_depth` metric per queue
- [ ] Scheduled job runs every 60s
- [ ] Grafana alert triggers when DLQ depth > 0 for 5min
- [ ] API endpoint: `GET /api/v1/queue/dlq/monitor` returns all DLQ depths
- [ ] API endpoint: `GET /api/v1/queue/dlq/{name}/inspect` returns messages
- [ ] Failure injection: Force a message to DLQ, verify detection

### Rollback Strategy

**Rollback Time:** <5 minutes

```bash
# Disable scheduled job and remove endpoints
git checkout HEAD~1 -- backend/shared/dlq_monitor.py
git checkout HEAD~1 -- backend/services/core_engine/main.py
git checkout HEAD~1 -- grafana/alerts/dlq_alerts.yml
```

### Testing Checklist

- [ ] Unit test: DLQMonitor message classification
- [ ] Unit test: Message replay and archive logic
- [ ] Integration test: Monitor + RabbitMQ interaction
- [ ] E2E test: DLQ message injection and recovery
- [ ] Manual test: Verify Grafana alerts

---

## Issue #3: Idempotency Guarantee Gaps

### Objective
Prevent duplicate processing of redelivered messages.

### Problem Statement
RabbitMQ guarantees **at-least-once delivery**. Without idempotency guarantees, if a consumer crashes after processing but before acknowledging, messages are redelivered causing duplicate processing:
- Scan could be started twice
- Report could be generated twice
- Program could have duplicate scope entries

### Root Causes
1. **No idempotency keys:** No tracking of processed message IDs
2. **No transaction atomicity:** Program upserts not transactional
3. **Redis locks only:** Prevent concurrent scans but don't prevent duplicate message processing

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 1 | Create idempotency_keys table migration | `alembic/versions/006_...py` | 1h | Engineer A |
| 2 | Implement IdempotencyService | `shared/idempotency.py` | 3h | Engineer A |
| 3 | Create with_idempotency decorator | `shared/idempotency.py` | 2h | Engineer A |
| 4 | Integrate with Core Worker | `core_engine/worker.py` | 2h | Engineer A |
| 4 | Integrate with Reporter Worker | `reporter/worker.py` | 2h | Engineer A |
| 5 | Add cleanup job for expired keys | `shared/jobs/idempotency_cleanup.py` | 1h | Engineer A |

### Solution Code

#### 1. Idempotency Key Model

```python
# File: backend/shared/models/idempotency.py

"""
Idempotency key tracking for at-least-once message delivery.

Ensures that redelivered messages do not cause duplicate processing.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import Column, String, DateTime, Index, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.shared.db import Base

class IdempotencyKey(Base):
    """
    Tracks processed message IDs to ensure idempotent message handling.
    
    When a message arrives, check if its event_id exists in this table:
    - If exists: Return cached response (message already processed)
    - If not exists: Process message, store response, then ack
    
    TTL: Keys expire after 7 days to prevent unbounded growth.
    """
    __tablename__ = "idempotency_keys"
    
    # event_id from MessageEnvelope
    key = Column(String(36), primary_key=True)
    
    # Service that processed the message
    service = Column(String(50), nullable=False)
    
    # Operation performed (e.g., "scan.start", "report.generate")
    operation = Column(String(100), nullable=False)
    
    # When message was first processed
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    # When key expires (auto-cleanup)
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )
    
    # Response cached for replay (optional)
    response = Column(JSONB, nullable=True)
    
    # Related entity ID (e.g., scan_id, report_id)
    entity_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_idempotency_created_at', 'created_at'),
        Index('idx_idempotency_expires_at', 'expires_at'),
        Index('idx_idempotency_service_operation', 'service', 'operation'),
    )
```

#### 2. Database Migration

```python
# File: alembic/versions/006_add_idempotency_keys.py

"""add idempotency keys table

Revision ID: 006
Revises: 005
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'idempotency_keys',
        sa.Column('key', sa.String(36), primary_key=True),
        sa.Column('service', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response', postgresql.JSONB, nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    op.create_index(
        'idx_idempotency_created_at',
        'idempotency_keys',
        ['created_at']
    )
    
    op.create_index(
        'idx_idempotency_expires_at',
        'idempotency_keys',
        ['expires_at']
    )
    
    op.create_index(
        'idx_idempotency_service_operation',
        'idempotency_keys',
        ['service', 'operation']
    )

def downgrade():
    op.drop_table('idempotency_keys')
```

#### 3. Idempotency Service

```python
# File: backend/shared/idempotency.py

"""
Idempotency service for message processing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Callable
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.models.idempotency import IdempotencyKey
from backend.shared.logging import get_logger

logger = get_logger(__name__)

class IdempotencyService:
    """
    Service for ensuring idempotent message processing.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_and_record(
        self,
        event_id: str,
        service: str,
        operation: str,
        entity_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if message has already been processed.
        
        Args:
            event_id: Unique event ID from MessageEnvelope
            service: Service name (e.g., "core_engine", "reporter")
            operation: Operation name (e.g., "scan.start", "report.generate")
            entity_id: Optional related entity ID
        
        Returns:
            Cached response if message already processed, None otherwise
        """
        # Check for existing key
        result = await self.session.execute(
            select(IdempotencyKey)
            .where(IdempotencyKey.key == event_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(
                "Idempotent message detected - returning cached response",
                event_id=event_id,
                service=service,
                operation=operation,
                original_processed_at=existing.created_at.isoformat()
            )
            return existing.response
        
        # Record new key
        key = IdempotencyKey(
            key=event_id,
            service=service,
            operation=operation,
            entity_id=entity_id,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            response=None  # Will be updated after processing
        )
        
        self.session.add(key)
        await self.session.commit()
        
        logger.info(
            "Recorded idempotency key",
            event_id=event_id,
            service=service,
            operation=operation
        )
        
        return None
    
    async def store_response(
        self,
        event_id: str,
        response: Dict[str, Any]
    ):
        """
        Store response for cached replay.
        
        Args:
            event_id: Unique event ID
            response: Response data to cache
        """
        result = await self.session.execute(
            select(IdempotencyKey)
            .where(IdempotencyKey.key == event_id)
        )
        key = result.scalar_one_or_none()
        
        if key:
            key.response = response
            await self.session.commit()
            
            logger.info(
                "Stored idempotent response",
                event_id=event_id,
                response_keys=list(response.keys())
            )
    
    async def cleanup_expired(self):
        """
        Remove expired idempotency keys.
        Called periodically by scheduler.
        """
        cutoff = datetime.now(timezone.utc)
        
        result = await self.session.execute(
            delete(IdempotencyKey)
            .where(IdempotencyKey.expires_at < cutoff)
        )
        
        deleted_count = result.rowcount
        await self.session.commit()
        
        if deleted_count > 0:
            logger.info(
                "Cleaned up expired idempotency keys",
                count=deleted_count,
                cutoff=cutoff.isoformat()
            )


async def with_idempotency(
    event_id: str,
    service: str,
    operation: str,
    handler: Callable,
    session: AsyncSession,
    entity_id: Optional[UUID] = None
) -> Any:
    """
    Decorator-style wrapper for idempotent message processing.
    
    Usage:
        async def process_scan_message(envelope):
            async with get_session() as session:
                result = await with_idempotency(
                    event_id=envelope.event_id,
                    service="core_engine",
                    operation="scan.start",
                    handler=lambda: _do_scan(envelope),
                    session=session
                )
                return result
    
    Args:
        event_id: Unique event ID
        service: Service name
        operation: Operation name
        handler: Async function to execute if message not yet processed
        session: Database session
        entity_id: Optional related entity ID
    
    Returns:
        Handler result or cached response
    """
    idempotency = IdempotencyService(session)
    
    # Check for duplicate
    cached = await idempotency.check_and_record(
        event_id=event_id,
        service=service,
        operation=operation,
        entity_id=entity_id
    )
    
    if cached is not None:
        return cached
    
    # Process message
    result = await handler()
    
    # Cache response
    if isinstance(result, dict):
        await idempotency.store_response(event_id, result)
    
    return result
```

#### 4. Enhanced Core Worker

```python
# File: backend/services/core_engine/scan_task.py

from backend.shared.idempotency import with_idempotency
from backend.shared.schemas.envelope import MessageEnvelope

async def _async_scan_pipeline(payload: ScanJobsPayload | dict) -> None:
    """
    Full async pipeline with idempotency protection.
    """
    if not isinstance(payload, ScanJobsPayload):
        payload = ScanJobsPayload.model_validate(payload)
    
    program_id = str(payload.program_id)
    
    # Extract event_id from envelope (passed through Celery)
    event_id = payload.metadata.get('event_id') if hasattr(payload, 'metadata') else None
    
    if not event_id:
        logger.warning(
            "No event_id in payload - idempotency not guaranteed",
            program_id=program_id
        )
        # Continue without idempotency (backward compatibility)
        await _execute_scan_pipeline(payload)
        return
    
    # Use idempotency wrapper
    async with get_session() as session:
        await with_idempotency(
            event_id=event_id,
            service="core_engine",
            operation="scan.execute",
            handler=lambda: _execute_scan_pipeline(payload),
            session=session
        )

async def _execute_scan_pipeline(payload: ScanJobsPayload) -> Dict[str, Any]:
    """
    Execute scan pipeline (extracted for idempotency wrapping).
    """
    # ... existing pipeline logic ...
    
    return {
        "scan_id": str(scan_id),
        "status": "completed",
        "finding_count": finding_count
    }
```

#### 5. Enhanced Reporter Worker

```python
# File: backend/services/reporter/report_task.py

from backend.shared.idempotency import with_idempotency

async def process_report_envelope_async(envelope: MessageEnvelope, payload: ReportJobsPayload):
    """
    Process report generation with idempotency protection.
    """
    async with get_session() as session:
        result = await with_idempotency(
            event_id=envelope.event_id,
            service="reporter",
            operation="report.generate",
            handler=lambda: _generate_reports(payload),
            session=session,
            entity_id=payload.scan_id
        )
        
        return result

async def _generate_reports(payload: ReportJobsPayload) -> Dict[str, Any]:
    """
    Generate reports (extracted for idempotency wrapping).
    """
    # ... existing report generation logic ...
    
    return {
        "scan_id": str(payload.scan_id),
        "report_ids": report_ids,
        "formats": formats_requested
    }
```

#### 6. Cleanup Job

```python
# File: backend/shared/jobs/idempotency_cleanup.py

async def cleanup_expired_idempotency_keys_job():
    """
    Scheduled job to remove expired idempotency keys.
    Runs daily.
    """
    from backend.shared.db import get_session
    from backend.shared.idempotency import IdempotencyService
    
    async with get_session() as session:
        service = IdempotencyService(session)
        await service.cleanup_expired()
```

#### 7. Scheduler Integration

```python
# File: backend/services/core_engine/main.py (in lifespan)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup ...
    
    # Register idempotency cleanup job
    scheduler.add_job(
        cleanup_expired_idempotency_keys_job,
        trigger='cron',
        hour=2,  # Run at 2 AM daily
        id='idempotency_cleanup',
        replace_existing=True
    )
    
    logger.info("Idempotency cleanup job registered")
    
    yield
    
    # ... existing shutdown ...
```

### Acceptance Criteria

- [ ] `idempotency_keys` table exists with proper indexes
- [ ] IdempotencyService.check_and_record() prevents duplicate processing
- [ ] with_idempotency() wrapper caches responses
- [ ] Core Worker rejects duplicate scan messages
- [ ] Reporter Worker rejects duplicate report messages
- [ ] Test: Process same message twice, verify second is ignored
- [ ] Cleanup job removes keys older than 7 days

### Rollback Strategy

**Rollback Time:** <10 minutes

```bash
# Drop idempotency_keys table, revert wrapper
psql -h postgres -U attackbot -c "DROP TABLE IF EXISTS idempotency_keys;"
git checkout HEAD~1 -- backend/shared/idempotency.py
git checkout HEAD~1 -- backend/services/core_engine/scan_task.py
git checkout HEAD~1 -- backend/services/reporter/report_task.py
git checkout HEAD~1 -- backend/shared/jobs/idempotency_cleanup.py
git checkout HEAD~1 -- backend/services/core_engine/main.py
```

### Testing Checklist

- [ ] Unit test: IdempotencyService check/record logic
- [ ] Unit test: with_idempotency() wrapper caching
- [ ] Integration test: Message redelivery simulation
- [ ] E2E test: Duplicate message processing
- [ ] Manual test: Verify cleanup job

---

## Sprint Timeline

| Day | Engineer A | Engineer B | Key Activities |
|-----|------------|------------|----------------|
| 1 | Watchdog enhancements | - | Metrics, logging, exception handling |
| 2 | Timezone migration + scan pipeline | - | Watchdog testing |
| 3 | Idempotency service + decorator | DLQ Monitor service | Code integration |
| 4 | Core Worker integration | DLQ metrics + API endpoints | Parallel development |
| 5 | Reporter Worker + cleanup job | DLQ testing + scheduler | Final integration |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database migration fails | Low | High | Test migrations in staging before production |
| Watchdog changes cause stuck scans | Low | High | Canary deploy, monitor stuck_scan metric |
| Idempotency keys cause performance issues | Low | Medium | Indexed queries, cleanup job |
| DLQ monitoring false positives | Low | Medium | Alert tuning |

---

## Rollback & Contingency Plans

### Per-Issue Rollback

| Issue | Rollback Strategy | Time to Rollback |
|-------|-------------------|------------------|
| #1 Watchdog | Revert to original watchdog.py | <5min |
| #2 DLQ Monitor | Disable scheduled job, remove endpoints | <5min |
| #3 Idempotency | Drop idempotency_keys table, revert wrapper | <10min |

### Contingency
If Sprint 1 overruns, descope **Issue #2 (DLQ)** to Sprint 2 and deliver **#1 + #3** as minimum viable sprint.

---

## Success Criteria

### Sprint 1
- [ ] Zero stuck scans in production after deployment
- [ ] All messages processed exactly once (no duplicates)
- [ ] DLQ messages visible in Grafana
- [ ] Watchdog execution logged and metered

---

## Dependencies

### Internal
- All issues are independent (no blocking dependencies)
- Natural pairing: #1 and #3 both involve scan processing

### External
- PostgreSQL (for idempotency keys table)
- Prometheus (for metrics)
- RabbitMQ (for DLQ monitoring)

---

## Integration Points

### Modified Files
1. `backend/services/core_engine/watchdog.py` - Enhanced with metrics, logging, timezone handling
2. `backend/services/core_engine/main.py` - Scheduler verification, DLQ/Idempotency jobs
3. `backend/shared/dlq_monitor.py` - **NEW** DLQ monitoring service
4. `backend/shared/idempotency.py` - **NEW** Idempotency service
5. `backend/shared/models/idempotency.py` - **NEW** IdempotencyKey model
6. `backend/services/core_engine/scan_task.py` - Idempotency wrapper
7. `backend/services/reporter/report_task.py` - Idempotency wrapper
8. `backend/shared/jobs/idempotency_cleanup.py` - **NEW** Cleanup job
9. `alembic/versions/005_ensure_timezone_aware_timestamps.py` - **NEW** Migration
10. `alembic/versions/006_add_idempotency_keys.py` - **NEW** Migration
11. `grafana/alerts/dlq_alerts.yml` - **NEW** Grafana alerts

### New Dependencies
- `prometheus_client` - Already installed (for metrics)
- `aio_pika` - Already installed (for RabbitMQ monitoring)
- No new Python packages required

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-19 | Mistral Vibe | Initial implementation guide based on Issues#1.md, Issues#2.md, and Issue_Sprints.md |

---

**Generated by Mistral Vibe.**
**Co-Authored-By: Mistral Vibe <vibe@mistral.ai>**

---

**Next Sprint:** [Sprint #2: P0/P1 - Resilience Foundation](./sprint#2.md)  
**Previous Sprint:** None (This is Sprint 1)  
**Related Documents:**  
- [Issue_Sprints.md](./Issue_Sprints.md) - Sprint planning overview  
- [Issues#1.md](./Issues#1.md) - Detailed issue definitions  
- [Issues#2.md](./Issues#2.md) - Detailed issue definitions
