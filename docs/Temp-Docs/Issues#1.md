# Attackbot v1 — Technical Issues Analysis & Solutions

> **Document Type:** Technical Analysis Report  
> **Target Audience:** Senior Engineers, Architects  
> **Date:** 2026-04-19  
> **Branch:** M4_ReadTheRoom  
> **Analysis Depth:** Low-level (code-level)

---

## Table of Contents

1. [Critical Issues](#critical-issues)
   - [Issue #1: Watchdog Scan Recovery Mechanism Failure](#issue-1-watchdog-scan-recovery-mechanism-failure)
   - [Issue #2: Dead Letter Queue Blind Spot](#issue-2-dead-letter-queue-blind-spot)
   - [Issue #3: Idempotency Guarantee Gaps](#issue-3-idempotency-guarantee-gaps)

2. [Architectural Issues](#architectural-issues)
   - [Issue #4: Missing Circuit Breaker Pattern](#issue-4-missing-circuit-breaker-pattern)
   - [Issue #5: Lack of Distributed Tracing](#issue-5-lack-of-distributed-tracing)
   - [Issue #6: Synchronous Inter-Service Dependencies](#issue-6-synchronous-inter-service-dependencies)
   - [Issue #7: Absence of Event Sourcing](#issue-7-absence-of-event-sourcing)

3. [Operational Issues](#operational-issues)
   - [Issue #8: Health Check False Positives](#issue-8-health-check-false-positives)
   - [Issue #9: Missing API Rate Limiting](#issue-9-missing-api-rate-limiting)
   - [Issue #10: No Backpressure Mechanism](#issue-10-no-backpressure-mechanism)
   - [Issue #11: Database Connection Pool Monitoring Gap](#issue-11-database-connection-pool-monitoring-gap)
   - [Issue #12: File Upload Size Validation Timing](#issue-12-file-upload-size-validation-timing)

4. [Strategic Enhancements](#strategic-enhancements)
   - [Enhancement #1: CQRS Implementation](#enhancement-1-cqrs-implementation)
   - [Enhancement #2: Feature Flag Service](#enhancement-2-feature-flag-service)

---

## Critical Issues

### Issue #1: Watchdog Scan Recovery Mechanism Failure

**Severity:** 🔴 Critical  
**Component:** `backend/services/core_engine/watchdog.py`  
**Evidence:** E2E test log shows scan `7ee68848-8ba3-4fb6-ab50-24256e2255eb` running for 12+ hours (started `2026-04-05T12:57:45`, still running on `2026-04-06T01:03:55`)

#### Root Cause Analysis

The watchdog mechanism is designed to mark scans as `failed_internal` after exceeding the stale threshold (2 hours). The failure occurs due to one or more of the following:

1. **Scheduler Not Starting:** The APScheduler job may not be registering during service startup
2. **Silent Exception Handling:** Exceptions in the watchdog function may be caught and suppressed without logging
3. **Query Logic Error:** The SQL query may not be correctly identifying stuck scans
4. **Timezone Mismatch:** Comparison between `started_at` (UTC) and `datetime.now()` (local) may cause incorrect time delta calculation

#### Current Implementation

**File:** `backend/services/core_engine/watchdog.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.repository import ScanRepository
from backend.shared.db import get_session
from backend.shared.logging import get_logger

logger = get_logger(__name__)
config = EngineConfig()

async def recover_stuck_scans():
    """Mark scans running longer than threshold as failed_internal."""
    try:
        async with get_session() as session:
            repo = ScanRepository(session)
            threshold = datetime.now(timezone.utc) - timedelta(
                seconds=config.watchdog_stale_threshold
            )
            
            # Query for stuck scans
            result = await session.execute(
                select(Scan)
                .where(Scan.status == "running")
                .where(Scan.started_at < threshold)
            )
            stuck_scans = result.scalars().all()
            
            for scan in stuck_scans:
                await repo.mark_scan_complete(
                    scan_id=scan.scan_id,
                    status="failed_internal",
                    finding_count=0,
                    severity_breakdown={},
                    error_detail="Scan exceeded watchdog threshold"
                )
                logger.warning(
                    "Recovered stuck scan",
                    scan_id=str(scan.scan_id),
                    started_at=scan.started_at.isoformat()
                )
    except Exception as e:
        logger.error(f"Watchdog recovery failed: {e}")
        # Exception is logged but not re-raised - silently fails

def start_watchdog(scheduler: AsyncIOScheduler):
    """Register watchdog job with scheduler."""
    scheduler.add_job(
        recover_stuck_scans,
        trigger='interval',
        seconds=config.watchdog_interval_seconds,
        id='scan_watchdog',
        replace_existing=True
    )
```

**File:** `backend/services/core_engine/main.py` (lifespan)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize infrastructure
    init_db(settings.database_url)
    
    # Start scheduler
    global scheduler
    scheduler = AsyncIOScheduler()
    
    # Register watchdog - POTENTIAL BUG: This may not be called
    start_watchdog(scheduler)
    
    scheduler.start()
    
    yield
    
    scheduler.shutdown()
```

#### Problem Identification

1. **No verification logging:** The watchdog function doesn't log when it starts or how many scans it found
2. **Silent failure:** Exceptions are caught but the function doesn't re-raise, making diagnosis impossible
3. **No metrics:** No Prometheus metrics to track watchdog execution count or recovered scans
4. **Timezone ambiguity:** `datetime.now(timezone.utc)` is correct, but if `Scan.started_at` was stored without timezone awareness, comparison fails

#### Solution

**Enhanced Watchdog Implementation:**

```python
# backend/services/core_engine/watchdog.py

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

**Enhanced Lifespan with Verification:**

```python
# backend/services/core_engine/main.py

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

**Additional: Database Migration for Timezone Awareness**

```python
# alembic/versions/005_ensure_timezone_aware_timestamps.py

"""ensure timezone-aware timestamps

Revision ID: 005
Revises: 004
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
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

#### Behavior Comparison

| Aspect | Old Behavior | New Behavior |
|--------|-------------|--------------|
| **Logging** | Silent execution, no start/end logs | Comprehensive logging: execution start, scans found, recovery actions, completion |
| **Exception Handling** | Exceptions caught and logged, execution continues | Exceptions logged with full stack trace and re-raised to alert monitoring |
| **Metrics** | No metrics exposed | Prometheus metrics: execution count, scans recovered, errors, current stuck scans |
| **Verification** | No verification that watchdog is scheduled | Startup verification that job is registered and next run time is set |
| **Scan Processing** | If one scan recovery fails, entire function aborts | Individual scan failures logged but don't abort processing of other scans |
| **Timezone Handling** | Potential timezone mismatch | Explicit UTC timezone on all datetime operations, database column enforcement |
| **Diagnostics** | Cannot determine if watchdog is running | Can verify via logs, metrics, and scheduler inspection endpoint |
| **Error Visibility** | Errors hidden in logs | Errors increment Prometheus counter, trigger alerts |
| **Recovery Detail** | Generic error message | Detailed error message including actual runtime and threshold |
| **Overlapping Runs** | Potential overlapping executions | `max_instances=1` prevents overlapping runs |

---

### Issue #2: Dead Letter Queue Blind Spot

**Severity:** 🔴 Critical  
**Component:** All services (system-wide)  
**Impact:** Failed messages accumulate in DLQ with no visibility, monitoring, or recovery mechanism

#### Root Cause Analysis

The system correctly routes failed messages to Dead Letter Queues (DLQs) via RabbitMQ's `x-dead-letter-exchange` configuration. However:

1. **No Monitoring:** No metrics track DLQ depth
2. **No Alerting:** No alerts when messages arrive in DLQ
3. **No Recovery:** No mechanism to replay DLQ messages after fixing root cause
4. **No Inspection:** DLQ inspection endpoint exists but is manual and not integrated with observability

#### Current Implementation

**Queue Topology Setup:**

```python
# backend/shared/queue.py

async def ensure_queue_topology(rabbitmq_url: str):
    """Declare all queues and their DLQs."""
    connection = await aio_pika.connect_robust(rabbitmq_url)
    
    async with connection:
        channel = await connection.channel()
        
        for queue_name in Queues.all():
            dlq_name = f"{queue_name}.dlq"
            
            # Declare DLQ (no dead-lettering for DLQ itself)
            await channel.declare_queue(
                dlq_name,
                durable=True,
                arguments={}
            )
            
            # Declare main queue with DLQ routing
            await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": dlq_name
                }
            )
```

**Inspection Endpoint (Manual):**

```python
# backend/services/core_engine/main.py

@app.get("/api/v1/queue/dlq/inspect")
async def inspect_dlq():
    """Manually inspect DLQ state."""
    states = await inspect_queue_states()
    
    dlq_states = {
        name: state
        for name, state in states.items()
        if name.endswith('.dlq')
    }
    
    return {
        "dlqs": dlq_states,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

#### Solution

**Enhanced DLQ Monitoring and Recovery:**

```python
# backend/shared/dlq_monitor.py

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

**Enhanced API Endpoints:**

```python
# backend/services/core_engine/main.py

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

**Scheduler Integration:**

```python
# backend/services/core_engine/main.py

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

**Grafana Alert Configuration:**

```yaml
# grafana/alerts/dlq_alerts.yml

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

#### Behavior Comparison

| Aspect | Old Behavior | New Behavior |
|--------|-------------|--------------|
| **Visibility** | No visibility into DLQ state | Real-time Prometheus metrics for DLQ depth |
| **Monitoring** | Manual inspection via API only | Automatic monitoring every 60 seconds |
| **Alerting** | No alerts | Grafana alerts when DLQ depth > 0 for 5 minutes |
| **Classification** | No failure classification | Automatic classification: transient, poison, permanent, max_retries |
| **Recovery** | No recovery mechanism | Automatic recovery for transient failures |
| **Replay** | No replay capability | Manual replay via API + automatic replay for classified messages |
| **Archiving** | Messages stuck in DLQ forever | Poison and permanent failures archived to prevent DLQ bloat |
| **Metrics** | No metrics | Comprehensive metrics: depth, replayed count, archived count |
| **Diagnostics** | Cannot diagnose why message failed | Full message inspection with headers, retry count, error details |
| **Operator Actions** | Must manually inspect RabbitMQ management UI | Can inspect, classify, and replay via REST API or automated job |

---

### Issue #3: Idempotency Guarantee Gaps

**Severity:** 🔴 Critical  
**Component:** All message consumers  
**Risk:** Duplicate processing if message is redelivered

#### Root Cause Analysis

RabbitMQ guarantees **at-least-once delivery**. If a consumer crashes after processing a message but before acknowledging it, RabbitMQ will redeliver the message to another consumer. Without idempotency guarantees:

1. **Scan could be started twice** if Core Worker crashes after creating scan row but before publishing to queue
2. **Report could be generated twice** if Reporter Worker crashes after generating report but before marking as completed
3. **Program could have duplicate scope entries** if Scraper crashes mid-transaction during program upsert

**Current protections:**
- ✅ Redis locks prevent concurrent scans for same program
- ✅ Database deduplication hash prevents duplicate findings (per scan)
- ❌ **No idempotency keys** on message processing
- ❌ **No transaction atomicity** on program upserts

#### Current Implementation

**Core Worker Message Processing:**

```python
# backend/services/core_engine/worker.py

@celery.task(bind=True, max_retries=0)
def run_scan_task(self, payload: dict):
    """Process scan job from queue."""
    asyncio.run(_async_scan_pipeline(payload))
```

**Problem:** If worker crashes after Stage 10 publishes report job but before acking message, the entire scan will re-run.

**Reporter Worker Message Processing:**

```python
# backend/services/reporter/worker.py

def callback(ch, method, properties, body):
    """Raw Kombu consumer callback."""
    envelope = MessageEnvelope.model_validate_json(body)
    payload = ReportJobsPayload.model_validate(envelope.payload)
    
    # Enqueue Celery task
    process_report_envelope_sync.apply_async(args=[payload.dict()])
    
    # Ack message
    ch.basic_ack(delivery_tag=method.delivery_tag)
```

**Problem:** If Celery worker crashes after generating report but before updating database, message is already acked so report generation is lost.

#### Solution

**Idempotency Key Tracking:**

```python
# backend/shared/models/idempotency.py

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

**Database Migration:**

```python
# alembic/versions/006_add_idempotency_keys.py

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

**Idempotency Service:**

```python
# backend/shared/idempotency.py

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

**Enhanced Core Worker:**

```python
# backend/services/core_engine/scan_task.py

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

**Enhanced Reporter Worker:**

```python
# backend/services/reporter/report_task.py

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

**Cleanup Job:**

```python
# backend/shared/jobs/idempotency_cleanup.py

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

**Scheduler Integration:**

```python
# backend/services/core_engine/main.py

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

#### Behavior Comparison

| Aspect | Old Behavior | New Behavior |
|--------|-------------|--------------|
| **Message Redelivery** | Duplicate processing if message redelivered | Idempotency key check prevents duplicate processing |
| **Scan Re-execution** | Entire scan re-runs if worker crashes after Stage 10 | Cached response returned, scan not re-executed |
| **Report Regeneration** | Report regenerated if worker crashes mid-generation | Cached report IDs returned, no regeneration |
| **Response Consistency** | Redelivered message may produce different result | Always returns same response for same event_id |
| **Key Storage** | No tracking of processed messages | Processed event_ids stored for 7 days |
| **Cleanup** | N/A | Automatic daily cleanup of expired keys |
| **Backward Compatibility** | N/A | Works with or without event_id in payload |
| **Diagnostics** | Cannot determine if message was processed before | Can query idempotency_keys table to see processing history |
| **Performance Impact** | No overhead | Single DB query per message (negligible with indexes) |

---

## Architectural Issues

### Issue #4: Missing Circuit Breaker Pattern

**Severity:** 🟡 Medium  
**Component:** All inter-service HTTP calls  
**Risk:** Cascading failures when downstream service is unavailable

#### Root Cause Analysis

The system makes synchronous HTTP calls between services:
- Reporter → Core Engine (fetch scan data)
- Core Engine → Scraper (fetch program scope)
- Scraper → HackerOne API (fetch programs)

When a downstream service is unavailable:
1. **Slow degradation:** Caller waits for full timeout (default: 30-60s)
2. **Resource exhaustion:** Blocked threads/connections pile up
3. **Cascading failure:** Upstream service becomes unresponsive
4. **No recovery:** Service keeps hammering unavailable endpoint

**Current implementation:**

```python
# backend/services/reporter/main.py

async def _fetch_scan(scan_id: str) -> dict[str, Any] | None:
    """Fetch scan from Core Engine."""
    timeout = httpx.Timeout(
        timeout=settings.upstream_timeout_seconds,
        connect=settings.upstream_connect_timeout_seconds,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(
            f"{settings.core_engine_api_url}/api/v1/scans/{scan_id}"
        )
    
    if response.status_code == 404:
        return None
    
    response.raise_for_status()  # Raises exception on 5xx
    return response.json()
```

**Problem:** If Core Engine is down, every report generation waits 60 seconds before failing.

#### Solution

**Install Circuit Breaker Library:**

```bash
pip install aiobreaker==1.4.0
```

**Circuit Breaker Implementation:**

```python
# backend/shared/circuit_breaker.py

"""
Circuit breaker implementation for external service calls.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failure threshold exceeded, all requests fail immediately
- HALF_OPEN: Testing if service recovered, limited requests allowed

Configuration per service:
- fail_max: Number of failures before opening circuit
- timeout_duration: How long to keep circuit open before testing recovery
- expected_exception: Exception type that triggers circuit breaker
"""

from typing import Optional, Callable, Any
from datetime import timedelta

from aiobreaker import CircuitBreaker, CircuitBreakerError
import httpx

from backend.shared.logging import get_logger

logger = get_logger(__name__)

class ServiceCircuitBreakers:
    """
    Registry of circuit breakers for external services.
    """
    
    # Scraper API circuit breaker
    scraper_api = CircuitBreaker(
        fail_max=5,                    # Open after 5 failures
        timeout_duration=timedelta(seconds=60),  # Stay open for 60s
        expected_exception=httpx.HTTPStatusError,
        name="scraper_api"
    )
    
    # Core Engine API circuit breaker
    core_engine_api = CircuitBreaker(
        fail_max=5,
        timeout_duration=timedelta(seconds=60),
        expected_exception=httpx.HTTPStatusError,
        name="core_engine_api"
    )
    
    # HackerOne API circuit breaker
    hackerone_api = CircuitBreaker(
        fail_max=3,                    # More sensitive for external API
        timeout_duration=timedelta(seconds=120),  # Longer recovery time
        expected_exception=(httpx.HTTPStatusError, httpx.TimeoutException),
        name="hackerone_api"
    )
    
    @classmethod
    def get_state_summary(cls) -> dict[str, str]:
        """Get current state of all circuit breakers."""
        return {
            "scraper_api": cls.scraper_api.current_state,
            "core_engine_api": cls.core_engine_api.current_state,
            "hackerone_api": cls.hackerone_api.current_state,
        }
    
    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers (admin operation)."""
        cls.scraper_api.close()
        cls.core_engine_api.close()
        cls.hackerone_api.close()
        logger.info("All circuit breakers reset")


# Event handlers for circuit breaker state changes
def on_circuit_open(breaker: CircuitBreaker):
    """Called when circuit opens."""
    logger.error(
        "Circuit breaker OPENED - service unavailable",
        circuit=breaker.name,
        fail_count=breaker.fail_counter
    )

def on_circuit_close(breaker: CircuitBreaker):
    """Called when circuit closes."""
    logger.info(
        "Circuit breaker CLOSED - service recovered",
        circuit=breaker.name
    )

def on_circuit_half_open(breaker: CircuitBreaker):
    """Called when circuit enters half-open state."""
    logger.warning(
        "Circuit breaker HALF-OPEN - testing service recovery",
        circuit=breaker.name
    )

# Register event listeners
ServiceCircuitBreakers.scraper_api.add_listener(on_circuit_open, CircuitBreaker.EVENT_OPENED)
ServiceCircuitBreakers.scraper_api.add_listener(on_circuit_close, CircuitBreaker.EVENT_CLOSED)
ServiceCircuitBreakers.scraper_api.add_listener(on_circuit_half_open, CircuitBreaker.EVENT_HALF_OPENED)

ServiceCircuitBreakers.core_engine_api.add_listener(on_circuit_open, CircuitBreaker.EVENT_OPENED)
ServiceCircuitBreakers.core_engine_api.add_listener(on_circuit_close, CircuitBreaker.EVENT_CLOSED)
ServiceCircuitBreakers.core_engine_api.add_listener(on_circuit_half_open, CircuitBreaker.EVENT_HALF_OPENED)

ServiceCircuitBreakers.hackerone_api.add_listener(on_circuit_open, CircuitBreaker.EVENT_OPENED)
ServiceCircuitBreakers.hackerone_api.add_listener(on_circuit_close, CircuitBreaker.EVENT_CLOSED)
ServiceCircuitBreakers.hackerone_api.add_listener(on_circuit_half_open, CircuitBreaker.EVENT_HALF_OPENED)
```

**Enhanced Reporter with Circuit Breaker:**

```python
# backend/services/reporter/main.py

from backend.shared.circuit_breaker import ServiceCircuitBreakers, CircuitBreakerError

@ServiceCircuitBreakers.core_engine_api
async def _fetch_scan(scan_id: str) -> dict[str, Any] | None:
    """
    Fetch scan from Core Engine with circuit breaker protection.
    
    Raises:
        CircuitBreakerError: If circuit is open (service unavailable)
        httpx.HTTPStatusError: If request fails with 4xx/5xx
    """
    timeout = httpx.Timeout(
        timeout=settings.upstream_timeout_seconds,
        connect=settings.upstream_connect_timeout_seconds,
    )
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(
            f"{settings.core_engine_api_url}/api/v1/scans/{scan_id}"
        )
    
    if response.status_code == 404:
        return None
    
    response.raise_for_status()
    return response.json()

# Usage in report generation
async def generate_report(request: GenerateReportsRequest):
    try:
        scan_data = await _fetch_scan(request.scan_id)
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Core Engine service unavailable - circuit breaker is open"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to fetch scan: {str(e)}"
        )
```

**Enhanced Core Engine with Circuit Breaker:**

```python
# backend/services/core_engine/scan_task.py

from backend.shared.circuit_breaker import ServiceCircuitBreakers, CircuitBreakerError

@ServiceCircuitBreakers.scraper_api
async def _fetch_scope_from_scraper(
    program_id: str,
    config: EngineConfig,
    client: httpx.AsyncClient | None = None,
) -> SharedScopeDefinition:
    """
    Fetch scope from Scraper API with circuit breaker protection.
    
    Raises:
        CircuitBreakerError: If circuit is open
        ScanError: If scope fetch fails
    """
    close_client = False
    if client is None:
        client = httpx.AsyncClient(
            base_url=config.scraper_api_url,
            timeout=config.scraper_api_timeout_seconds,
        )
        close_client = True
    
    try:
        resp = await client.get(f"/api/v1/programs/{program_id}/scope")
        resp.raise_for_status()
        data = resp.json()
    except CircuitBreakerError:
        raise ScanError("Scraper API unavailable - circuit breaker is open")
    except Exception as e:
        raise ScanError(f"Scope fetch failed: {e}") from e
    finally:
        if close_client:
            await client.aclose()
    
    try:
        return SharedScopeDefinition.model_validate(
            {
                "in_scope": data.get("in_scope") or [],
                "out_of_scope": data.get("out_of_scope") or [],
            }
        )
    except ValidationError as e:
        raise ScanError(f"Scope definition invalid: {e}") from e
```

**Circuit Breaker Status Endpoint:**

```python
# backend/services/core_engine/main.py

from backend.shared.circuit_breaker import ServiceCircuitBreakers

@app.get("/api/v1/circuit-breakers")
async def get_circuit_breaker_status():
    """Get current state of all circuit breakers."""
    return {
        "circuit_breakers": ServiceCircuitBreakers.get_state_summary(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/v1/circuit-breakers/reset")
async def reset_circuit_breakers():
    """Reset all circuit breakers (admin operation)."""
    ServiceCircuitBreakers.reset_all()
    return {
        "status": "reset",
        "circuit_breakers": ServiceCircuitBreakers.get_state_summary(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

**Prometheus Metrics:**

```python
# backend/shared/circuit_breaker.py

from prometheus_client import Counter, Enum as PrometheusEnum

circuit_breaker_state = PrometheusEnum(
    'circuit_breaker_state',
    'Current circuit breaker state',
    ['circuit'],
    states=['closed', 'open', 'half_open']
)

circuit_breaker_transitions = Counter(
    'circuit_breaker_transitions_total',
    'Total circuit breaker state transitions',
    ['circuit', 'from_state', 'to_state']
)

def on_circuit_open(breaker: CircuitBreaker):
    circuit_breaker_state.labels(circuit=breaker.name).state('open')
    circuit_breaker_transitions.labels(
        circuit=breaker.name,
        from_state='closed',
        to_state='open'
    ).inc()
    logger.error(...)

# Similar for close and half_open
```

#### Behavior Comparison

| Aspect | Old Behavior | New Behavior |
|--------|-------------|--------------|
| **Service Down** | All requests wait for full timeout (30-60s) | Circuit opens after 5 failures, subsequent requests fail immediately |
| **Response Time** | 30-60s timeout per failed request | <1ms rejection when circuit is open |
| **Resource Usage** | Connections/threads blocked waiting | Resources freed immediately |
| **Recovery** | Service keeps hammering unavailable endpoint | Circuit stays open for 60s, then tests with single request |
| **Error Messages** | Generic timeout errors | Clear "circuit breaker is open" message |
| **Cascading Failures** | Upstream service becomes unresponsive | Upstream service remains healthy, returns 503 quickly |
| **Monitoring** | No visibility into service health | Prometheus metrics expose circuit state |
| **Diagnostics** | Cannot determine why requests failing | Circuit breaker logs show exact failure threshold |
| **Recovery Testing** | No controlled recovery | Half-open state tests recovery with single request |
| **Admin Control** | No manual intervention possible | Admin can manually reset circuit breakers |

---

*Due to length constraints, I'll continue with the remaining issues in the next section of the document. Should I create a second file for the remaining issues, or would you like me to condense the format?*