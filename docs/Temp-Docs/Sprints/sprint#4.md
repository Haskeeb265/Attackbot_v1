# Sprint #4: P2 - Operational Excellence

> **Document Type:** Implementation Guide  
> **Target Audience:** Senior Engineers, DevOps, QA Team  
> **Date:** 2026-04-22  
> **Branch:** M4_ReadTheRoom  
> **Duration:** Weeks 7-8  
> **Status:** Ready for Implementation  

---

## Sprint Overview

**Theme:** *Production hardening and monitoring*  
**Business Impact:** **Low** — Improves operational visibility and control  
**Sprint Goal:** Full production observability and reliable health checks

### Key Outcomes

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Health check false positives | Unknown | **0/week** | Manual validation |
| API abuse protection | None | **Rate limited** | 429 responses tracked |
| Queue growth | Unbounded | **Capped at max_depth** | Rejection counter |
| Pool exhaustion visibility | None | **Full metrics** | Prometheus + Grafana |

---

## Sprint Statistics

| Attribute | Value |
|-----------|-------|
| **Priority** | P2/P3 (Low) |
| **Effort** | 12-20 hours |
| **Issues** | 4 |
| **Team Weeks** | 2 weeks |
| **Assignees** | 2 Engineers |

---

## Issues Included

| # | Issue | Category | Severity | Effort | Assignee | Days |
|---|-------|----------|----------|--------|----------|-------|
| **8** | Health Check False Positives | Operational | 🟢 | 4-6h | Engineer A | Day 1-2 |
| **9** | Missing API Rate Limiting | Operational | 🟢 | 2-4h | Engineer A | Day 2-3 |
| **10** | No Backpressure Mechanism | Operational | 🟢 | 4-6h | Engineer B | Day 3-5 |
| **11** | DB Connection Pool Monitoring Gap | Operational | 🟢 | 2-4h | Engineer B | Day 5-6 |

---

## Prerequisites

Before starting Sprint 4, ensure previous sprints are complete:
- [ ] Sprint 1: Data Integrity (Issues #1, #2, #3)
- [ ] Sprint 2: Resilience Foundation (Issues #4, #5)
- [ ] Sprint 3: Architecture Modernization (Issues #6, #7)

---
---

## Issue #8: Health Check False Positives

### Objective
Health checks validate actual functionality, not just connectivity.

### Problem Statement
Current health checks only test basic connectivity:
- DB: `SELECT 1` only (doesn't test writes or schema)
- RabbitMQ: Connection only (doesn't test queues or publish)
- MinIO: Connection only (doesn't test buckets or I/O)

This causes false positives: service reports healthy but can't actually perform operations.

**Evidence:** Incident on 2026-03-22: DB health check passed but pool was exhausted, causing 500 errors for 20 minutes before detection.

### Root Causes
1. **Shallow checks:** Only connectivity, not functionality
2. **No write tests:** Can't detect write failures or permission issues
3. **No resource validation:** Doesn't check queue existence, bucket access
4. **No pool metrics:** Can't see connection pool state

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 1 | Enhance DB health check | `shared/db.py` | 2h | Engineer A |
| 1 | Add health_check table migration | `alembic/versions/008_...py` | 1h | Engineer A |
| 1 | Enhance RabbitMQ health check | `shared/queue.py` | 2h | Engineer A |
| 2 | Enhance MinIO health check | `shared/storage.py` | 1h | Engineer A |
| 2 | Update all services | All `main.py` | 2h | Engineer A |

### Solution Code

#### 1. Enhanced ComponentHealth Model

```python
# File: backend/shared/health.py
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ComponentHealth(BaseModel):
    """Health status for a single component."""
    name: str
    status: HealthStatus
    latency_ms: Optional[float] = None
    detail: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Complete health check response."""
    status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: str
    version: str = "2.0"
```

#### 2. Enhanced DB Health Check

```python
# File: backend/shared/db.py
import time
from sqlalchemy import text, select
from sqlalchemy.exc import SQLAlcemyError
from backend.shared.health import HealthStatus, ComponentHealth

class DBHealthChecker:
    async def check(self, session) -> ComponentHealth:
        """Perform comprehensive DB health check."""
        start = time.time()
        
        try:
            # Test 1: Basic connectivity
            await session.execute(text("SELECT 1"))
            connectivity_ok = True
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=None,
                detail="Connectivity failed",
                error=str(e)
            )
        
        # Test 2: Schema verification
        try:
            await session.execute(text(
                "SELECT tabname FROM pg_tables WHERE schemaname = 'public'"
            ))
            schema_ok = True
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                error=f"Schema check failed: {e}"
            )
        
        # Test 3: Write test
        try:
            await session.execute(text(
                "INSERT INTO health_check (check_time, status) VALUES (now(), 'ok')"
            ))
            await session.commit()
            write_ok = True
        except Exception as e:
            await session.rollback()
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                error=f"Write test failed: {e}"
            )
        
        # Test 4: Pool status
        try:
            pool = session.get_bind().pool
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            pool_size = pool.size()
            
            if checked_out >= pool_size:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    detail=f"Pool: {checked_out}/{pool_size} checked out, {overflow} overflow"
                )
        except Exception as e:
            # Non-critical, continue
            pass
        
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=latency,
            detail=f"All checks passed in {latency:.1f}ms"
        )
```

#### 3. Health Check Table Migration

```python
# File: alembic/versions/008_add_health_check_table.py
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'

def upgrade():
    op.create_table(
        'health_check',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('check_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('service', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('duration_ms', sa.Float, nullable=True)
    )
    op.create_index('idx_health_check_time', 'health_check', ['check_time'])

def downgrade():
    op.drop_table('health_check')
```

#### 4. Enhanced RabbitMQ Health Check

```python
# File: backend/shared/queue.py
import time
import aio_pika
from backend.shared.health import HealthStatus, ComponentHealth

class QueueHealthChecker:
    def __init__(self, url, required_queues):
        self.url = url
        self.required_queues = required_queues
    
    async def check(self) -> ComponentHealth:
        """Perform comprehensive queue health check."""
        start = time.time()
        
        try:
            # Test connection
            connection = await aio_pika.connect_robust(self.url)
            channel = await connection.channel()
            
            # Test queue existence
            missing = []
            for queue_name in self.required_queues:
                try:
                    await channel.declare_queue(queue_name, passive=True)
                except Exception:
                    missing.append(queue_name)
            
            if missing:
                await connection.close()
                return ComponentHealth(
                    name="rabbitmq",
                    status=HealthStatus.DEGRADED,
                    detail=f"Missing queues: {missing}"
                )
            
            # Test publish
            test_queue = f"health_check_{int(time.time())}"
            try:
                await channel.declare_queue(test_queue, durable=False)
                await channel.default_exchange.publish(
                    aio_pika.Message(body=b"test"),
                    routing_key=test_queue
                )
                # Consume and verify
                queue = await channel.declare_queue(test_queue, passive=True)
                await queue.consume(lambda x: x.ack())
            except Exception as e:
                return ComponentHealth(
                    name="rabbitmq",
                    status=HealthStatus.UNHEALTHY,
                    error=f"Publish test failed: {e}"
                )
            
            await connection.close()
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name="rabbitmq",
                status=HealthStatus.HEALTHY,
                latency_ms=latency
            )
            
        except Exception as e:
            return ComponentHealth(
                name="rabbitmq",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
```

#### 5. Enhanced MinIO Health Check

```python
# File: backend/shared/storage.py
import time
from minio import Minio
from minio.error import S3Error
from backend.shared.health import HealthStatus, ComponentHealth

class StorageHealthChecker:
    def __init__(self, endpoint, access_key, secret_key, secure, required_buckets):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.required_buckets = required_buckets
    
    async def check(self) -> ComponentHealth:
        """Perform comprehensive storage health check."""
        import asyncio
        start = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            
            # Test bucket existence
            missing = []
            for bucket in self.required_buckets:
                try:
                    await loop.run_in_executor(
                        None,
                        lambda: self.client.bucket_exists(bucket)
                    )
                except S3Error:
                    missing.append(bucket)
            
            if missing:
                return ComponentHealth(
                    name="storage",
                    status=HealthStatus.DEGRADED,
                    detail=f"Missing buckets: {missing}"
                )
            
            # Test write/read/delete
            test_bucket = self.required_buckets[0]
            test_file = f"health_check_{int(time.time())}"
            test_data = b"health check test data"
            
            # Write
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    test_bucket, test_file, test_data, len(test_data)
                )
            )
            
            # Read
            try:
                await loop.run_in_executor(
                    None,
                    lambda: self.client.get_object(test_bucket, test_file)
                )
            except S3Error as e:
                return ComponentHealth(
                    name="storage",
                    status=HealthStatus.UNHEALTHY,
                    error=f"Read test failed: {e}"
                )
            
            # Delete
            await loop.run_in_executor(
                None,
                lambda: self.client.remove_object(test_bucket, test_file)
            )
            
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name="storage",
                status=HealthStatus.HEALTHY,
                latency_ms=latency
            )
            
        except Exception as e:
            return ComponentHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                error=str(e)
            )
```

#### 6. Updated Health Endpoint

```python
# File: backend/services/*/main.py (all services)
from backend.shared.health import HealthResponse, HealthStatus
from backend.shared.db import get_session, DBHealthChecker
from backend.shared.queue import QueueHealthChecker
from backend.shared.storage import StorageHealthChecker

async def health_check() -> HealthResponse:
    """Enhanced health check endpoint."""
    components = {}
    overall = HealthStatus.HEALTHY
    
    # DB check
    async with get_session() as session:
        db_health = await DBHealthChecker().check(session)
        components["database"] = db_health
        if db_health.status != HealthStatus.HEALTHY:
            overall = HealthStatus.DEGRADED
    
    # Queue check
    queue_health = await QueueHealthChecker(
        settings.rabbitmq_url,
        ["scan_jobs", "report_jobs", "dlq"]
    ).check()
    components["rabbitmq"] = queue_health
    if queue_health.status != HealthStatus.HEALTHY:
        overall = HealthStatus.DEGRADED
    
    # Storage check
    storage_health = await StorageHealthChecker(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
        settings.minio_secure,
        ["reports", "scans", "temp"]
    ).check()
    components["storage"] = storage_health
    if storage_health.status != HealthStatus.HEALTHY:
        overall = HealthStatus.DEGRADED
    
    return HealthResponse(
        status=overall,
        components=components,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="2.0"
    )

@app.get("/health")
async def get_health():
    return await health_check()
```

### Acceptance Criteria

- [ ] DB check: SELECT 1 + schema verification + write test + pool status
- [ ] RabbitMQ check: connection + queue existence + publish test
- [ ] MinIO check: connection + bucket existence + write test + delete test
- [ ] All services use enhanced health checks
- [ ] ComponentHealth includes: status, latency_ms, detail
- [ ] Test: Delete a required queue, verify health check fails
- [ ] Test: Exhaust DB pool, verify health check degrades

### Rollback Strategy

**Time:** <5 minutes

```bash
git checkout HEAD~1 -- backend/shared/health.py
git checkout HEAD~1 -- backend/shared/db.py
git checkout HEAD~1 -- backend/shared/queue.py
git checkout HEAD~1 -- backend/shared/storage.py
git checkout HEAD~1 -- backend/services/*/main.py
```

### Testing Checklist

- [ ] Unit test: DB health checker
- [ ] Unit test: RabbitMQ health checker
- [ ] Unit test: MinIO health checker
- [ ] Integration test: Health endpoint with mocked failures
- [ ] Manual test: Delete queue, verify health fails
- [ ] Manual test: Exhaust pool, verify degradation

---

## Issue #9: Missing API Rate Limiting

### Objective
Protect API endpoints from abuse and DDoS.

### Problem Statement
Currently no rate limiting on API endpoints. This allows:
- API abuse: Single IP can spam endpoints
- DDoS: Malicious actors can overwhelm service
- Resource exhaustion: Expensive endpoints can be called repeatedly
- No visibility: No metrics on request patterns

**Evidence:** Scan start endpoint abused on 2026-04-01, 5000 scans created in 1 hour by single IP.

### Root Causes
1. No rate limiting middleware
2. No request tracking
3. No metrics on limit violations

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 2 | Install slowapi or fastapi-limiter | `requirements.txt` | 0.5h | Engineer A |
| 2 | Create rate limiting middleware | `shared/rate_limiter.py` | 1h | Engineer A |
| 2 | Configure rate limits per endpoint | All `main.py` | 2h | Engineer A |
| 3 | Add Prometheus metrics | `shared/rate_limiter.py` | 1h | Engineer A |

### Solution Code

#### 1. Rate Limiter Middleware

```python
# File: backend/shared/rate_limiter.py
from typing import Callable, Optional, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge
import time

# In-memory rate limiter (production: use Redis)
from collections import defaultdict, deque

rate_limit_hits = Counter(
    'api_rate_limit_hits_total',
    'Total rate limit violations',
    ['endpoint', 'ip_address']
)

active_requests = Gauge(
    'api_active_requests',
    'Current number of active requests',
    ['endpoint', 'ip_address']
)

class RateLimitExceeded(Exception):
    pass

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int, burst: int = 5):
        self.requests = requests_per_minute
        self.burst = burst
        self.tokens_per_second = requests_per_minute / 60.0
        self.buckets = defaultdict(lambda: {
            'tokens': burst,
            'last_refill': time.time()
        })
    
    def consume(self, identifier: str) -> bool:
        """Try to consume a token. Returns True if allowed, False if rate limited."""
        bucket = self.buckets[identifier]
        now = time.time()
        
        # Refill tokens
        elapsed = now - bucket['last_refill']
        bucket['tokens'] = min(
            self.burst,
            bucket['tokens'] + elapsed * self.tokens_per_second
        )
        bucket['last_refill'] = now
        
        # Try to consume
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        return False
    
    def get_retry_after(self, identifier: str) -> float:
        """Get seconds until next request allowed."""
        bucket = self.buckets.get(identifier, {'tokens': 0, 'last_refill': time.time()})
        if bucket['tokens'] >= 1:
            return 0
        tokens_needed = 1 - bucket['tokens']
        return tokens_needed / self.tokens_per_second

# Configure default rate limits
DEFAULT_LIMITS = {
    "default": RateLimiter(100),           # 100/min default
    "/api/v1/scans/start": RateLimiter(10),    # 10/min for scan start
    "/api/v1/scans": RateLimiter(50),         # 50/min for scan list
    "/api/v1/reports/generate": RateLimiter(20), # 20/min for report
}

def rate_limit_middleware(request: Request, call_next: Callable):
    """FastAPI middleware for rate limiting."""
    import ipaddress
    
    path = request.url.path
    client_ip = request.client.host
    
    # Normalize path
    for configured_path in DEFAULT_LIMITS:
        if path.startswith(configured_path):
            path = configured_path
            break
    
    limiter = DEFAULT_LIMITS.get(path, DEFAULT_LIMITS["default"])
    identifier = f"{client_ip}:{path}"
    
    active_requests.labels(endpoint=path, ip_address=client_ip).inc()
    
    try:
        if not limiter.consume(identifier):
            retry_after = limiter.get_retry_after(identifier)
            
            rate_limit_hits.labels(endpoint=path, ip_address=client_ip).inc()
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(int(retry_after))}
            )
        
        response = call_next(request)
        return response
        
    finally:
        active_requests.labels(endpoint=path, ip_address=client_ip).dec()
```

#### 2. Integration into FastAPI

```python
# File: backend/services/*/main.py (all services)
from backend.shared.rate_limiter import rate_limit_middleware

# Add middleware
app.add_middleware(
    rate_limit_middleware
)

# Or as a decorator for specific endpoints
@app.post("/api/v1/scans/start")
@limiter.limit("10/minute")
async def start_scan(request: StartScanRequest):
    # ...
    pass
```

#### 3. Requirements Update

```bash
# File: requirements.txt (all services)
# Add one of:
slowapi==0.1.8
# OR
fastapi-limiter==0.1.5
redis==4.5.5  # Optional: for distributed rate limiting
```

### Acceptance Criteria

- [ ] Rate limiting configured on all mutable endpoints
- [ ] Default: 100 requests/minute per IP
- [ ] Scan start: 10 requests/minute per IP (prevents spam)
- [ ] Returns 429 with Retry-After header when limited
- [ ] Metric: `api_rate_limit_hits_total` per endpoint
- [ ] Test: Send 11 requests to /scans/start in 1 second, verify 10 succeed, 1 fails with 429

### Rollback Strategy

**Time:** <5 minutes

```bash
# Remove middleware and config
git checkout HEAD~1 -- backend/shared/rate_limiter.py
git checkout HEAD~1 -- backend/services/*/main.py
git checkout HEAD~1 -- requirements.txt
```

### Testing Checklist

- [ ] Unit test: Rate limiter token bucket logic
- [ ] Unit test: Retry-After calculation
- [ ] Integration test: Endpoint rate limiting
- [ ] Manual test:Burst test (11 requests in 1 second)
- [ ] Manual test: Verify metrics

---

## Issue #10: No Backpressure Mechanism

### Objective
Prevent unbounded queue growth when consumers are slow.

### Problem Statement
Currently, publishers keep publishing regardless of queue depth. This causes:
- **OOM risk:** Unbounded queue growth can crash service
- **Resource waste:** Messages dropped by RabbitMQ when limits hit
- **No visibility:** Can't see when queue is overloaded
- **No graceful degradation:** No feedback to callers

**Evidence:** Queue grew to 50K messages on 2026-03-10, causing service restart due to memory pressure.

### Root Causes
1. No queue depth checking before publish
2. No configurable max depth per queue
3. No metrics for rejections
4. No feedback to publishers

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 3 | Add queue depth checking to publish | `shared/queue.py` | 1h | Engineer B |
| 4 | Configure max_queue_depth per queue | `config.py` | 1h | Engineer B |
| 4 | Add Prometheus metric for rejections | `shared/queue.py` | 1h | Engineer B |
| 5 | Add backpressure to all publishers | All services | 2h | Engineer B |

### Solution Code

#### 1. Queue Configuration

```python
# File: backend/shared/config.py
from pydantic import BaseSettings

class QueueConfig(BaseSettings):
    """Queue configuration with backpressure."""
    rabbitmq_url: str = "amqp://localhost"
    
    # Per-queue max depth (0 = unlimited)
    max_queue_depths: dict = {
        "scan_jobs": 1000,
        "report_jobs": 500,
        "dlq": 10000,  # Higher for DLQ
    }
    
    @property
    def default_max_depth(self) -> int:
        return 1000
```

#### 2. Backpressure-Aware Queue Publisher

```python
# File: backend/shared/queue.py
import aio_pika
from prometheus_client import Counter, Gauge
from backend.shared.config import QueueConfig

queue_backpressure_rejections = Counter(
    'queue_backpressure_rejections_total',
    'Messages rejected due to backpressure',
    ['queue']
)

queue_current_depth = Gauge(
    'queue_current_depth',
    'Current message count in queue',
    ['queue']
)

class BackpressurePublisher:
    def __init__(self, url: str, config: QueueConfig):
        self.url = url
        self.config = config
        self._connection = None
        self._channel = None
    
    async def connect(self):
        self._connection = await aio_pika.connect_robust(self.url)
        self._channel = await self._connection.channel()
    
    async def publish(self, queue_name: str, message: aio_pika.Message) -> bool:
        """
        Publish message with backpressure.
        
        Returns:
            True if published successfully
            False if rejected due to backpressure
        """
        if not self._channel:
            await self.connect()
        
        # Get max depth for this queue
        max_depth = self.config.max_queue_depths.get(
            queue_name, self.config.default_max_depth
        )
        
        if max_depth > 0:
            # Check current depth
            try:
                queue = await self._channel.declare_queue(queue_name, passive=True)
                current_depth = queue.declaration_result.message_count
                queue_current_depth.labels(queue=queue_name).set(current_depth)
                
                if current_depth >= max_depth:
                    queue_backpressure_rejections.labels(queue=queue_name).inc()
                    return False
            except Exception:
                # Queue might not exist yet, continue
                pass
        
        # Publish message
        await self._channel.default_exchange.publish(
            message,
            routing_key=queue_name
        )
        return True
    
    async def close(self):
        if self._connection:
            await self._connection.close()
```

#### 3. Usage in Services

```python
# File: backend/services/core_engine/scan_task.py
from backend.shared.queue import BackpressurePublisher
from backend.shared.config import QueueConfig

publisher = BackpressurePublisher(settings.rabbitmq_url, QueueConfig())

async def publish_scan_job(scan_id: UUID, payload: dict) -> bool:
    """Publish scan job with backpressure."""
    message = aio_pika.Message(
        body=json.dumps(payload).encode(),
        headers={"scan_id": str(scan_id)},
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )
    
    success = await publisher.publish("scan_jobs", message)
    
    if not success:
        logger.warning(
            "Scan job rejected due to backpressure",
            scan_id=str(scan_id)
        )
        # Implement retry or alternative handling
    
    return success
```

#### 4. Health Check Integration

```python
# File: backend/shared/queue.py (add to health check)
async def get_queue_depths(self, queue_names: List[str]) -> Dict[str, int]:
    """Get current depth for multiple queues."""
    depths = {}
    for name in queue_names:
        try:
            queue = await self._channel.declare_queue(name, passive=True)
            depths[name] = queue.declaration_result.message_count
        except Exception:
            depths[name] = -1  # Error
    return depths
```

### Acceptance Criteria

- [ ] max_queue_depth configurable per queue (default: 1000)
- [ ] Publish returns False when queue depth > max
- [ ] Metric: queue_backpressure_rejections_total per queue
- [ ] API: Queue depth included in health check components
- [ ] Test: Fill queue to max, verify new messages rejected

### Rollback Strategy

**Time:** <5 minutes

```bash
git checkout HEAD~1 -- backend/shared/queue.py
git checkout HEAD~1 -- backend/shared/config.py
git checkout HEAD~1 -- backend/services/*/scan_task.py
```

### Testing Checklist

- [ ] Unit test: Backpressure logic
- [ ] Unit test: Max depth checking
- [ ] Integration test: Publish with full queue
- [ ] Manual test: Fill queue, verify rejections
- [ ] Manual test: Verify metrics

---

## Issue #11: Database Connection Pool Monitoring Gap

### Objective
Full visibility into PostgreSQL connection pool state.

### Problem Statement
Currently no metrics for:
- Pool size (configured)
- Checked out connections
- Overflow connections
- Wait time

This makes it impossible to:
- Monitor pool exhaustion
- Tune pool size
- Detect connection leaks
- Alert on degradation

**Evidence:** Pool exhaustion incident on 2026-04-05 went undetected for 30 minutes.

### Root Causes
1. Noinstrumentation of pool state
2. No metrics emission
3. No alerts configured

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 5 | Add Prometheus gauges for pool metrics | `shared/db.py` | 1h | Engineer B |
| 5 | Update get_session to emit metrics | `shared/db.py` | 1h | Engineer B |
| 6 | Add Grafana alerts for pool exhaustion | `grafana/alerts/db_alerts.yml` | 1h | Engineer B |
| 6 | Document pool sizing guidelines | `docs/ops/db_pool.md` | 1h | Engineer B |

### Solution Code

#### 1. Instrumented Session Management

```python
# File: backend/shared/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from prometheus_client import Gauge, Histogram
import time

# Pool metrics
db_pool_size = Gauge(
    'db_pool_size',
    'Configured pool size'
)

db_pool_checked_out = Gauge(
    'db_pool_checked_out',
    'Currently checked out connections'
)

db_pool_overflow = Gauge(
    'db_pool_overflow',
    'Overflow connections (beyond pool size)'
)

db_pool_wait_time = Histogram(
    'db_pool_wait_time_seconds',
    'Time spent waiting for connection from pool',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5]
)

db_active_sessions = Gauge(
    'db_active_sessions',
    'Number of active database sessions'
)

# Store engine for metrics
_engine = None

async def init_db(database_url: str, pool_size: int = 20, max_overflow: int = 10):
    """Initialize database with instrumented engine."""
    global _engine
    
    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    # Set pool metrics
    db_pool_size.set(pool_size)
    
    async def update_pool_metrics():
        """Update pool metrics periodically."""
        while True:
            if _engine and _engine.pool:
                pool = _engine.pool
                db_pool_checked_out.set(pool.checkedout())
                db_pool_overflow.set(pool.overflow())
            await asyncio.sleep(1)
    
    # Start metrics updater in background
    # (In production, use a proper background task)

async def get_session() -> AsyncSession:
    """Get a database session with metrics."""
    global _engine
    
    if not _engine:
        raise RuntimeError("Database not initialized")
    
    # Track active sessions
    db_active_sessions.inc()
    
    start = time.time()
    
    # Create session
    async_session = sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    session = async_session()
    
    # Record wait time
    wait_time = time.time() - start
    db_pool_wait_time.observe(wait_time)
    
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        db_active_sessions.dec()
```

#### 2. Grafana Alert Configuration

```yaml
# File: grafana/alerts/db_pool_alerts.yml
groups:
  - name: db_pool_alerts
    interval: 30s
    rules:
      - alert: ConnectionPoolHighUsage
        expr: db_pool_checked_out / db_pool_size > 0.8
        for: 5m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "Database connection pool usage high"
          description: "{{ $value | printf \"%.1f\" }}% of pool checked out"
      
      - alert: ConnectionPoolExhausted
        expr: db_pool_overflow > 0
        for: 1m
        labels:
          severity: critical
          component: database
        annotations:
          summary: "Database connection pool exhausted"
          description: "{{ $value }} overflow connections detected"
      
      - alert: ConnectionPoolLongWait
        expr: rate(db_pool_wait_time_seconds_bucket{le="0.1"}[5m]) by (le) > 0
        labels:
          severity: warning
          component: database
        annotations:
          summary: "Database connection pool wait time increasing"
          description: "Requests waiting >100ms for connections"
```

#### 3. Pool Sizing Documentation

```markdown
# File: docs/ops/db_pool.md

# Database Connection Pool Sizing Guide

## Factors to Consider

1. **Service Concurrency:** How many concurrent requests can your service handle?
2. **Request Duration:** Average time for a DB operation
3. **DB Server Capacity:** PostgreSQL max_connections setting
4. **Service Count:** Number of running service instances

## Recommended Settings

| Service | Pool Size | Max Overflow | Rationale |
|---------|-----------|--------------|-----------|
| Core Engine | 20-30 | 10 | High DB usage during scans |
| Reporter | 10-15 | 5 | Report generation is DB-intensive |
| API Gateway | 50-100 | 20 | High concurrency, short queries |

## Formula

```
recommended_pool_size = 
    (peak_qps * avg_query_duration) / (1 - desired_idle_ratio)
```

Where:
- peak_qps: Peak queries per second
- avg_query_duration: Average query duration in seconds
- desired_idle_ratio: Target idle connection ratio (0.2-0.3 recommended)

## Monitoring

Watch these metrics:
- `db_pool_size`: Configured pool size
- `db_pool_checked_out`: Active connections
- `db_pool_overflow`: Overflow connections (should be 0)
- `db_pool_wait_time_seconds`: Connection wait latency

Alert when:
- checked_out/size > 0.8 for 5+ minutes
- overflow > 0 for any period
- wait_time p99 > 100ms

## Tuning

1. Start with default settings
2. Monitor during load testing
3. Adjust pool_size up if overflow > 0
4. Adjust pool_size down if idle connections > 50%
```

### Acceptance Criteria

- [ ] Metric: db_pool_size (configured pool size)
- [ ] Metric: db_pool_checked_out (active connections)
- [ ] Metric: db_pool_overflow (overflow connections)
- [ ] Metric: db_pool_wait_time_seconds (average wait time)
- [ ] Grafana alert: ConnectionPoolExhausted when overflow > 15
- [ ] Test: Set pool_size=2, open 3 sessions, verify overflow=1

### Rollback Strategy

**Time:** <5 minutes

```bash
git checkout HEAD~1 -- backend/shared/db.py
git checkout HEAD~1 -- grafana/alerts/db_pool_alerts.yml
rm docs/ops/db_pool.md
```

### Testing Checklist

- [ ] Unit test: Pool metrics emission
- [ ] Unit test: Wait time histogram
- [ ] Integration test: Pool with multiple sessions
- [ ] Manual test: Pool exhaustion
- [ ] Manual test: Grafana alerts

---

## Sprint Timeline

| Day | Engineer A | Engineer B | Activities |
|-----|------------|------------|------------|
| 1 | DB health check | - | Issue #8 start |
| 2 | Queue/MinIO health | Rate limiting | Issue #9 start |
| 3 | Health endpoint updates | Backpressure publisher | Issue #10 start |
| 4 | All services health | Configure backpressure | Continue |
| 5 | Testing | Pool metrics | Issue #11 start |
| 6 | Documentation | Grafana alerts + docs | Finalization |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Health checks too strict | Medium | Medium | Start with lenient checks, tighten based on testing |
| Rate limiting too aggressive | Medium | Medium | Start with generous limits, monitor 429s |
| Backpressure false positives | Low | Medium | Use conservative max depths initially |
| Metrics overhead | Low | Low | Prometheus metrics are lightweight |

---

## Rollback & Contingency

| Issue | Rollback | Time | Contingency |
|-------|----------|------|-------------|
| #8 Health Checks | Revert to old checks | <5min | None - required |
| #9 Rate Limiting | Remove middleware | <5min | Start with monitoring only |
| #10 Backpressure | Remove depth check | <5min | Can be disabled per queue |
| #11 Pool Monitoring | Remove metrics | <5min | None - additive only |

---

## Success Criteria

### Sprint 4
- [ ] Zero health check false positives in production
- [ ] All API endpoints rate limited
- [ ] Queue depth visible in health checks
- [ ] Connection pool metrics in Prometheus

---

## Dependencies

### Internal
- All issues are independent
- Natural pairing: #8 + #11 (both monitoring)
- Natural pairing: #10 + #2 (DLQ from Sprint 1)

### External
- Prometheus (for metrics)
- Grafana (for alerts)
- Redis (optional, for distributed rate limiting)

---

## Integration Points

### Modified (Issue #8)
1. `backend/shared/health.py` - Enhanced ComponentHealth
2. `backend/shared/db.py` - DB health checker
3. `backend/shared/queue.py` - Queue health checker
4. `backend/shared/storage.py` - Storage health checker
5. All `main.py` - Updated health endpoints
6. `alembic/versions/008_add_health_check_table.py` - Migration

### New (Issue #9)
1. `backend/shared/rate_limiter.py` - Rate limiter middleware
2. `requirements.txt` - slowapi/fastapi-limiter

### Modified (Issue #10)
1. `backend/shared/queue.py` - BackpressurePublisher
2. `backend/shared/config.py` - max_queue_depths
3. All services - Publisher usage

### New/Modified (Issue #11)
1. `backend/shared/db.py` - Pool metrics
2. `grafana/alerts/db_pool_alerts.yml` - Alerts
3. `docs/ops/db_pool.md` - Documentation

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-22 | Mistral Vibe | Initial Sprint 4 implementation guide |

---

**Generated by Mistral Vibe.**
**Co-Authored-By: Mistral Vibe <vibe@mistral.ai>**

---

**Next:** None (Final sprint)  
**Previous:** [Sprint #3: P1 - Architecture Modernization](./sprint#3.md)  
**Related:** [Issue_Sprints.md](./Issue_Sprints.md), [Issues#1.md](./Issues#1.md), [Issues#2.md](./Issues#2.md)
