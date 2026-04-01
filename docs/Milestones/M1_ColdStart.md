# 🏗️ AttackBot — M1: Solid Ground
### Low-Level Implementation Plan

> **Version:** 1.0 &nbsp;|&nbsp; **Milestone:** M1 &nbsp;|&nbsp; **Date:** 2026-03-06

---

## 📋 Table of Contents

1. [Repository Structure](#1-️-repository-structure)
2. [Shared Library](#2--shared-library)
3. [Docker Compose Infrastructure](#3--docker-compose-infrastructure)
4. [Vault Dev Mode](#4--vault-dev-mode)
5. [MinIO Bucket Initialization](#5--minio-bucket-initialization)
6. [Database Migration System](#6-️-database-migration-system)
7. [Service Skeletons](#7--service-skeletons)
8. [CI Pipeline](#8-️-ci-pipeline)
9. [Observability Baseline](#9--observability-baseline)
10. [Message Envelope & Queue Contracts](#10--message-envelope--queue-contracts)
11. [Startup Order Validation](#11--startup-order-validation)
12. [Definition of Done Checklist](#12--definition-of-done-checklist)

---

## 1. 🗂️ Repository Structure

### 1.1 Monorepo Layout

```
attackbot/
├── backend/
│   ├── services/
│   │   ├── scraper/
│   │   │   ├── Dockerfile
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   └── requirements.txt
│   │   ├── core-engine/
│   │   ├── reporter/
│   │   ├── attack-graph-engine/
│   │   ├── browser-worker/
│   │   ├── api-fuzzer-worker/
│   │   ├── js-analysis-worker/
│   │   ├── scenario-runner/
│   │   ├── exploit-verifier/
│   │   └── ai-analysis-worker/
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── db.py
│   │   ├── health.py
│   │   ├── exceptions.py
│   │   ├── queue.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── envelope.py       ← canonical message envelope
│   │       ├── scan_jobs.py      ← scan.jobs payload schema
│   │       └── report_jobs.py    ← report.jobs payload schema
│   └── migrations/
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           └── 001_initial_schema.py
├── infra/
│   ├── docker-compose.yml
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   ├── provisioning/
│   │   │   ├── datasources/
│   │   │   │   └── datasources.yml
│   │   │   └── dashboards/
│   │   │       ├── dashboards.yml
│   │   │       └── services_alive.json
│   ├── loki/
│   │   └── loki-config.yml
│   └── README.md
├── scripts/
│   ├── bootstrap.sh              ← cold-boot helper
│   └── healthcheck_all.sh        ← post-start validation
├── tests/
│   ├── conftest.py
│   └── integration/
│       └── test_infra_startup.py
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
└── requirements/
    ├── base.txt
    ├── dev.txt
    └── test.txt
```

---

### 1.2 Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Service directories | kebab-case | `core-engine/` |
| Python modules | snake_case | `queue_publisher.py` |
| Python classes | PascalCase | `QueuePublisher` |
| Python functions | snake_case | `publish_message()` |
| Environment variables | SCREAMING_SNAKE | `RABBITMQ_URL` |
| Docker service names | kebab-case | `core-engine` |
| Queue names | dot.separated | `scan.jobs` |
| Redis keys | colon:separated | `scan:lock:{program_id}` |
| Alembic revisions | NNN_description | `001_initial_schema` |

---

### 1.3 Root Config Files

**`pyproject.toml`** — unified tool config:

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**`requirements/base.txt`** — shared across all services:

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
pydantic-settings==2.2.1
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
aio-pika==9.4.1
redis[hiredis]==5.0.4
celery[redis]==5.4.0
prometheus-fastapi-instrumentator==7.0.0
structlog==24.1.0
httpx==0.27.0
hvac==2.1.0
```

**`requirements/dev.txt`:**

```
ruff==0.4.4
mypy==1.10.0
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0
testcontainers==4.4.0
```

**`.gitignore`** must include:

```
__pycache__/
*.pyc
.env
.env.*
!.env.example
*.egg-info/
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/
dist/
node_modules/
```

---

## 2. 🔧 Shared Library

> 💡 The shared library is the **single most important artifact of M1**. Every service imports from it. Get it right once.

### 2.1 `config.py` — Base Settings

```python
# backend/shared/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class BaseServiceConfig(BaseSettings):
    """
    All services inherit from this. Each service overrides with its own
    additional fields. Settings are loaded from environment variables only —
    no .env files in production.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # ── Redis ─────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── RabbitMQ ──────────────────────────────────────────────────────
    rabbitmq_url: str = "amqp://attackbot:attackbot@localhost:5672/"

    # ── Vault ─────────────────────────────────────────────────────────
    vault_url: str = "http://localhost:8200"
    vault_token: str = "dev-root-token"

    # ── MinIO ─────────────────────────────────────────────────────────
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False

    # ── Service identity ──────────────────────────────────────────────
    service_name: str = "unknown"
    log_level: str = "INFO"
    environment: str = "development"
```

---

### 2.2 `logging.py` — Structured JSON Logger

```python
# backend/shared/logging.py
import structlog
import logging
import sys
from typing import Any

def configure_logging(service_name: str, log_level: str = "INFO") -> None:
    """
    Call once at service startup in main.py.
    All subsequent calls to get_logger() return a pre-configured structlog logger.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    # Bind service name to all log calls from this process
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)
```

**Usage in any service:**

```python
from shared.logging import get_logger
log = get_logger(__name__)

# Every log line automatically includes service + timestamp
log.info("nuclei_scan_completed", scan_id=scan_id, finding_count=3, duration_ms=4821)
log.warning("rate_limited", platform="hackerone", retry_after=60)
log.error("stage_failed", stage=4, error=str(e), scan_id=scan_id)
```

**Example JSON output:**

```json
{
  "event": "nuclei_scan_completed",
  "service": "core-engine",
  "level": "info",
  "timestamp": "2026-03-06T14:22:11.042Z",
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "finding_count": 3,
  "duration_ms": 4821
}
```

---

### 2.3 `db.py` — Async SQLAlchemy Engine Factory

```python
# backend/shared/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class Base(DeclarativeBase):
    pass

_engine = None
_session_factory = None

def init_db(database_url: str, pool_size: int = 10, max_overflow: int = 20) -> None:
    """Call once at service startup."""
    global _engine, _session_factory
    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=False,
        pool_pre_ping=True,   # detects stale connections before use
    )
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Use as: async with get_session() as session:"""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def check_db_health() -> bool:
    """Used by /health endpoints."""
    try:
        from sqlalchemy import text
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

---

### 2.4 `health.py` — Health Check Response Model

```python
# backend/shared/health.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ComponentHealth(BaseModel):
    status: HealthStatus
    latency_ms: float | None = None
    detail: str | None = None

class HealthResponse(BaseModel):
    status: HealthStatus
    service: str
    timestamp: datetime
    version: str = "1.0.0"
    components: dict[str, ComponentHealth] = {}

    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY
```

**Usage in any FastAPI service:**

```python
@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    db_ok = await check_db_health()
    rmq_ok = await check_rabbitmq_health()

    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        ),
        "rabbitmq": ComponentHealth(
            status=HealthStatus.HEALTHY if rmq_ok else HealthStatus.UNHEALTHY
        ),
    }
    overall = (
        HealthStatus.HEALTHY
        if all(c.status == HealthStatus.HEALTHY for c in components.values())
        else HealthStatus.UNHEALTHY
    )
    return HealthResponse(
        status=overall,
        service=settings.service_name,
        timestamp=datetime.utcnow(),
        components=components,
    )
```

---

### 2.5 `exceptions.py` — Common Exception Hierarchy

```python
# backend/shared/exceptions.py

class AttackBotError(Exception):
    """Base for all AttackBot exceptions."""

# ── Scan lifecycle ─────────────────────────────────────────────────────
class ScanError(AttackBotError):
    """Non-fatal scan stage failure. Scan continues as partial."""

class ScanTimeoutError(ScanError):
    """A CLI tool or external request exceeded its timeout."""

class ScopeFatalError(AttackBotError):
    """Stage 0 fatal: scope cannot be resolved. Scan must abort."""

class ScanInternalError(AttackBotError):
    """Stage 10 fatal: aggregation failed. Data integrity at risk."""

# ── Infrastructure ─────────────────────────────────────────────────────
class QueueError(AttackBotError):
    """RabbitMQ publish/consume failure."""

class QueueConnectionError(QueueError):
    """Cannot establish RabbitMQ connection."""

class StorageError(AttackBotError):
    """MinIO read/write failure."""

# ── Platform collectors ────────────────────────────────────────────────
class CollectorError(AttackBotError):
    """Generic platform scraping failure."""

class CollectorRateLimitError(CollectorError):
    """Platform returned HTTP 429 after all retries."""

class CollectorAuthError(CollectorError):
    """Platform API credentials rejected."""

# ── Schema ─────────────────────────────────────────────────────────────
class MessageSchemaError(AttackBotError):
    """Incoming queue message failed schema validation."""
```

---

### 2.6 `queue.py` — RabbitMQ Base Classes

```python
# backend/shared/queue.py
import aio_pika
import asyncio
import json
from typing import Any, Callable, Awaitable
from shared.logging import get_logger
from shared.exceptions import QueueConnectionError, QueueError

log = get_logger(__name__)

# ── Queue name registry ────────────────────────────────────────────────
# All queue names declared once. Import from here — never hardcode strings.
class Queues:
    SCAN_JOBS          = "scan.jobs"
    SCAN_JOBS_DLQ      = "scan.jobs.dlq"
    BROWSER_JOBS       = "browser.jobs"
    BROWSER_JOBS_DLQ   = "browser.jobs.dlq"
    API_FUZZ_JOBS      = "api.fuzz.jobs"
    API_FUZZ_JOBS_DLQ  = "api.fuzz.jobs.dlq"
    JS_ANALYSIS_JOBS   = "js.analysis.jobs"
    JS_ANALYSIS_DLQ    = "js.analysis.jobs.dlq"
    SCENARIO_JOBS      = "scenario.jobs"
    SCENARIO_JOBS_DLQ  = "scenario.jobs.dlq"
    VERIFY_JOBS        = "verify.jobs"
    VERIFY_JOBS_DLQ    = "verify.jobs.dlq"
    AI_ANALYSIS_JOBS   = "ai.analysis.jobs"
    AI_ANALYSIS_DLQ    = "ai.analysis.jobs.dlq"
    REPORT_JOBS        = "report.jobs"
    REPORT_JOBS_DLQ    = "report.jobs.dlq"
    REPORTS_COMPLETED  = "reports.completed"


class QueuePublisher:
    """
    Persistent RabbitMQ publisher with reconnect loop.
    Uses passive queue declaration to avoid argument mismatch errors.
    """

    def __init__(self, rabbitmq_url: str):
        self._url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
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
        Publish a message. Returns True on success, False on failure.
        Caller is responsible for setting queued_for_scan = true on False.
        """
        if self._channel is None:
            raise QueueConnectionError("Publisher not connected. Call connect() first.")
        try:
            # Passive declare — queue must already exist (created by consumer)
            queue = await self._channel.get_queue(queue_name, ensure=False)
            await self._channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    priority=priority,
                ),
                routing_key=queue_name,
            )
            log.info("message_published", queue=queue_name, event_type=message.get("event_type"))
            return True
        except Exception as e:
            log.error("publish_failed", queue=queue_name, error=str(e))
            return False

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
```

---

## 3. 🐳 Docker Compose Infrastructure

### 3.1 Environment File

Create `.env.example` (committed) and `.env` (gitignored, local copy):

```bash
# PostgreSQL
POSTGRES_USER=attackbot
POSTGRES_PASSWORD=attackbot
POSTGRES_DB=attackbot

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_DEFAULT_USER=attackbot
RABBITMQ_DEFAULT_PASS=attackbot

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Vault
VAULT_DEV_ROOT_TOKEN_ID=dev-root-token

# Neo4j
NEO4J_AUTH=neo4j/attackbot
```

---

### 3.2 Full `docker-compose.yml`

```yaml
# infra/docker-compose.yml
version: "3.9"

networks:
  attackbot-net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
  neo4j_data:
  minio_data:
  vault_data:
  prometheus_data:
  grafana_data:
  loki_data:

# ═══════════════════════════════════════════════════════════════
# PHASE 1 — INFRASTRUCTURE (no depends_on)
# ═══════════════════════════════════════════════════════════════
services:

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "1.0", memory: "1G" }
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} && psql -U ${POSTGRES_USER} -c 'SELECT 1'"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "256M" }
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_DEFAULT_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_DEFAULT_PASS}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks: [attackbot-net]
    ports:
      - "15672:15672"   # management UI — internal only in prod
    deploy:
      resources:
        limits: { cpus: "1.0", memory: "512M" }
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_port_connectivity"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s

  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: ${NEO4J_AUTH}
    volumes:
      - neo4j_data:/data
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "1.0", memory: "1G" }
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:7474 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s    # Neo4j takes 30-60s to boot — do not reduce

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "512M" }
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  vault:
    image: hashicorp/vault:1.15
    command: vault server -dev -dev-root-token-id="dev-root-token"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: ${VAULT_DEV_ROOT_TOKEN_ID}
      VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
    cap_add:
      - IPC_LOCK
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "256M" }
    healthcheck:
      test: ["CMD", "vault", "status", "-address=http://localhost:8200"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s

# ═══════════════════════════════════════════════════════════════
# PHASE 2 — INIT (one-shot services)
# ═══════════════════════════════════════════════════════════════

  migrate:
    build:
      context: ../backend
      dockerfile: migrations/Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    networks: [attackbot-net]
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"    # one-shot — must not restart on exit 0

  minio-init:
    image: minio/mc
    networks: [attackbot-net]
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set local http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} &&
      mc mb --ignore-existing local/reports &&
      mc mb --ignore-existing local/evidence &&
      mc mb --ignore-existing local/js-assets &&
      mc mb --ignore-existing local/summaries &&
      echo 'MinIO buckets initialized'
      "
    restart: "no"
    # CRITICAL: mc anonymous set download is intentionally ABSENT.
    # All report access must go through pre-signed URLs via the Reporter API.

  vault-init:
    image: hashicorp/vault:1.15
    networks: [attackbot-net]
    environment:
      VAULT_ADDR: "http://vault:8200"
      VAULT_TOKEN: ${VAULT_DEV_ROOT_TOKEN_ID}
    depends_on:
      vault:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      vault kv put secret/attackbot/platform placeholder=true &&
      vault kv put secret/attackbot/scanner placeholder=true &&
      echo 'Vault initialized with placeholder secrets'
      "
    restart: "no"

# ═══════════════════════════════════════════════════════════════
# PHASE 3 — CORE SERVICES
# ═══════════════════════════════════════════════════════════════

  scraper:
    build:
      context: ../backend/services/scraper
    environment:
      SERVICE_NAME: scraper
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/
      VAULT_URL: http://vault:8200
      VAULT_TOKEN: ${VAULT_DEV_ROOT_TOKEN_ID}
    networks: [attackbot-net]
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
      minio-init:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "512M" }

  core-engine:
    build:
      context: ../backend/services/core-engine
    environment:
      SERVICE_NAME: core-engine
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/
      VAULT_URL: http://vault:8200
      VAULT_TOKEN: ${VAULT_DEV_ROOT_TOKEN_ID}
    networks: [attackbot-net]
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "512M" }

  reporter:
    build:
      context: ../backend/services/reporter
    environment:
      SERVICE_NAME: reporter
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
    networks: [attackbot-net]
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
      minio-init:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "512M" }

  attack-graph-engine:
    build:
      context: ../backend/services/attack-graph-engine
    environment:
      SERVICE_NAME: attack-graph-engine
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USERNAME: neo4j
      NEO4J_PASSWORD: attackbot
    networks: [attackbot-net]
    depends_on:
      neo4j:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "512M" }

# ═══════════════════════════════════════════════════════════════
# PHASE 4 — CORE WORKERS (skeletons for M1)
# ═══════════════════════════════════════════════════════════════

  core-worker:
    build:
      context: ../backend/services/core-engine
    command: celery -A worker worker -Q scan.jobs -c 2 --loglevel=info
    environment:
      SERVICE_NAME: core-worker
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/
    networks: [attackbot-net]
    depends_on:
      core-engine:
        condition: service_healthy
    deploy:
      resources:
        limits: { cpus: "2.0", memory: "2G" }

  reporter-worker:
    build:
      context: ../backend/services/reporter
    command: celery -A worker worker -Q report.jobs -c 1 --loglevel=info
    environment:
      SERVICE_NAME: reporter-worker
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/
    networks: [attackbot-net]
    depends_on:
      reporter:
        condition: service_healthy
    deploy:
      resources:
        limits: { cpus: "1.0", memory: "1G" }

# ═══════════════════════════════════════════════════════════════
# PHASE 5 — SPECIALIST WORKERS (skeletons — no real work in M1)
# ═══════════════════════════════════════════════════════════════

  browser-worker:
    build:
      context: ../backend/services/browser-worker
    command: celery -A worker worker -Q browser.jobs -c 2 --loglevel=info
    environment:
      SERVICE_NAME: browser-worker
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/
    networks: [attackbot-net]
    depends_on:
      rabbitmq:
        condition: service_healthy
    deploy:
      resources:
        limits: { cpus: "2.0", memory: "2G" }

  # api-fuzzer-worker, js-analysis-worker, scenario-runner,
  # exploit-verifier, ai-analysis-worker — same pattern, omitted for brevity

# ═══════════════════════════════════════════════════════════════
# PHASE 6 — GATEWAY (last to start)
# ═══════════════════════════════════════════════════════════════

  api-gateway:
    build:
      context: ../backend/services/api-gateway
    ports:
      - "8000:8000"
    environment:
      SERVICE_NAME: api-gateway
      SCRAPER_URL: http://scraper:8001
      ENGINE_URL: http://core-engine:8002
      REPORTER_URL: http://reporter:8003
      GRAPH_URL: http://attack-graph-engine:8006
      REDIS_URL: redis://redis:6379/0
    networks: [attackbot-net]
    depends_on:
      scraper:
        condition: service_healthy
      core-engine:
        condition: service_healthy
      reporter:
        condition: service_healthy
      attack-graph-engine:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 60s
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "256M" }

# ═══════════════════════════════════════════════════════════════
# OBSERVABILITY
# ═══════════════════════════════════════════════════════════════

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "512M" }

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks: [attackbot-net]
    depends_on:
      - prometheus
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "256M" }

  loki:
    image: grafana/loki:latest
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "256M" }

  tempo:
    image: grafana/tempo:latest
    networks: [attackbot-net]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: "256M" }
```

---

## 4. 🔐 Vault Dev Mode

### 4.1 `vault-init` Secret Path Structure

The `vault-init` one-shot container seeds placeholder paths. The canonical secret path structure is:

```
secret/attackbot/platform/{platform_name}
  ├── api_username
  └── api_token

secret/attackbot/scanner
  ├── nuclei_templates_path
  └── interactsh_token

secret/programs/{program_id}/totp_secret   ← added at scan time, not in init
```

---

### 4.2 Vault Client in Shared Library

Add to `backend/shared/vault.py`:

```python
# backend/shared/vault.py
import hvac
from shared.logging import get_logger

log = get_logger(__name__)

_client: hvac.Client | None = None

def init_vault(vault_url: str, vault_token: str) -> None:
    global _client
    _client = hvac.Client(url=vault_url, token=vault_token)
    if not _client.is_authenticated():
        raise RuntimeError("Vault authentication failed")
    log.info("vault_connected", url=vault_url)

def get_secret(path: str, key: str) -> str:
    """Read a single key from a KV v2 secret path."""
    if _client is None:
        raise RuntimeError("Vault not initialized. Call init_vault() first.")
    response = _client.secrets.kv.read_secret_version(path=path)
    return response["data"]["data"][key]
```

> ⚠️ **Critical reminder:** Dev mode does **NOT** persist secrets across container restarts. This is acceptable locally. Do not use dev mode in production.

---

## 5. 🪣 MinIO Bucket Initialization

The `minio-init` one-shot service creates four buckets:

| Bucket | Purpose |
|---|---|
| `reports` | Final PDF/DOCX report files |
| `evidence` | Screenshots, HTTP captures, OOB receipts |
| `js-assets` | Downloaded JavaScript files |
| `summaries` | Program AI summaries (M10) |

> ⚠️ All bucket access goes through **pre-signed URLs** via the Reporter API. No bucket is ever set to public/anonymous download.

Add MinIO client to shared library at `backend/shared/storage.py`:

```python
# backend/shared/storage.py
from minio import Minio
from minio.error import S3Error
from shared.logging import get_logger

log = get_logger(__name__)
_client: Minio | None = None

def init_storage(endpoint: str, access_key: str, secret_key: str, secure: bool = False) -> None:
    global _client
    _client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    log.info("minio_connected", endpoint=endpoint)

def get_presigned_url(bucket: str, object_name: str, expires_hours: int = 1) -> str:
    from datetime import timedelta
    if _client is None:
        raise RuntimeError("Storage not initialized.")
    return _client.presigned_get_object(
        bucket, object_name, expires=timedelta(hours=expires_hours)
    )
```

---

## 6. 🗄️ Database Migration System

### 6.1 Alembic Setup

```
backend/migrations/
├── Dockerfile
├── env.py
├── script.py.mako
└── versions/
    └── 001_initial_schema.py
```

**`env.py`** — async-aware:

```python
# backend/migrations/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os

config = context.config
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async def do_run():
        async with connectable.connect() as connection:
            await connection.run_sync(context.run_migrations)
    asyncio.run(do_run())

run_migrations_online()
```

**`001_initial_schema.py`** — proof-of-life migration:

```python
# backend/migrations/versions/001_initial_schema.py
"""Initial schema - programs and scans tables (proof of life)"""
revision = "001"
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        "programs",
        sa.Column("program_id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("platform", sa.VARCHAR(50), nullable=False),
        sa.Column("handle", sa.VARCHAR(255), unique=True, nullable=False),
        sa.Column("name", sa.VARCHAR(500)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("queued_for_scan", sa.Boolean(), server_default="false"),
        sa.Column("last_scraped_at", sa.TIMESTAMPTZ()),
        sa.Column("created_at", sa.TIMESTAMPTZ(), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMPTZ(), server_default=sa.text("NOW()")),
    )
    op.create_table(
        "scans",
        sa.Column("scan_id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("program_id", sa.UUID(), sa.ForeignKey("programs.program_id"), nullable=False),
        sa.Column("status", sa.VARCHAR(50), server_default="pending"),
        sa.Column("created_at", sa.TIMESTAMPTZ(), server_default=sa.text("NOW()")),
    )

def downgrade():
    op.drop_table("scans")
    op.drop_table("programs")
```

**Migrations `Dockerfile`:**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements/base.txt .
RUN pip install -r base.txt
COPY . .
CMD ["alembic", "upgrade", "head"]
```

---

### 6.2 Migration Revision Plan

The `001` migration is M1 proof-of-life only. Full schema lands across these revisions:

| Revision | Milestone | Contents |
|---|---|---|
| `001_initial_schema` | M1 | `programs`, `scans` (skeleton) |
| `002_scraper_full` | M2 | Full `programs`, `program_scopes`, `program_policies` |
| `003_engine_core` | M3 | `scans`, `scan_stages`, `assets`, `endpoints` |
| `004_engine_scan_data` | M3 | `js_assets`, `browser_sessions`, `api_schemas` |
| `005_findings` | M3 | `findings`, `finding_evidence`, `vulnerability_groups` |
| `006_chains` | M8 | `exploit_chains` |
| `007_reporter` | M4 | `reports`, `reproduction_packs` |

---

## 7. 🦴 Service Skeletons

> 💡 Every FastAPI service follows the **exact same skeleton structure**. Implement it identically for all four Phase 3 services.

### 7.1 FastAPI Skeleton Pattern

```python
# backend/services/scraper/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from shared.config import BaseServiceConfig
from shared.logging import configure_logging, get_logger
from shared.db import init_db
from shared.health import HealthResponse, HealthStatus, ComponentHealth
from datetime import datetime

class ScraperConfig(BaseServiceConfig):
    service_name: str = "scraper"
    # Add scraper-specific config fields here in M2

settings = ScraperConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("service_starting", service=settings.service_name)
    init_db(settings.database_url, settings.db_pool_size)
    log.info("service_ready", service=settings.service_name)
    yield
    log.info("service_stopping", service=settings.service_name)

app = FastAPI(
    title="AttackBot Scraper",
    version="1.0.0",
    lifespan=lifespan,
)

# Prometheus metrics on /metrics
Instrumentator().instrument(app).expose(app)

@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    from shared.db import check_db_health
    db_ok = await check_db_health()
    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        )
    }
    overall = HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
    return HealthResponse(
        status=overall,
        service=settings.service_name,
        timestamp=datetime.utcnow(),
        components=components,
    )
```

```dockerfile
# backend/services/scraper/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY ../../requirements/base.txt .
RUN pip install -r base.txt
COPY ../../shared /app/shared
COPY . .
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

> Repeat for: `core-engine` (`:8002`), `reporter` (`:8003`), `attack-graph-engine` (`:8006`).

---

### 7.2 Celery Worker Skeleton Pattern

```python
# backend/services/core-engine/worker.py
from celery import Celery
from shared.config import BaseServiceConfig
from shared.logging import configure_logging, get_logger

class EngineConfig(BaseServiceConfig):
    service_name: str = "core-worker"

settings = EngineConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

app = Celery(
    "core-worker",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,          # ack only after task completes
    worker_prefetch_multiplier=1, # don't prefetch — tasks are long-running
    task_reject_on_worker_lost=True,
    task_default_queue="scan.jobs",
)

@app.task(name="scan_task", bind=True, max_retries=3)
def scan_task(self, message: dict):
    """M1 skeleton — logs receipt, does nothing."""
    log.info("scan_task_received", event_id=message.get("event_id"))
    # Full implementation in M3
```

> Repeat for: `reporter-worker` and all specialist workers.

---

## 8. ⚙️ CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: ["*"]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check backend/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements/dev.txt
      - run: mypy backend/shared/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: attackbot
          POSTGRES_PASSWORD: attackbot
          POSTGRES_DB: attackbot
        ports: ["5432:5432"]
        options: >-
          --health-cmd="pg_isready -U attackbot"
          --health-interval=5s --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements/dev.txt -r requirements/base.txt
      - run: pytest tests/ --cov=backend/shared --cov-report=xml -v
      - uses: codecov/codecov-action@v4

  build:
    runs-on: ubuntu-latest
    needs: [lint, typecheck, test]
    steps:
      - uses: actions/checkout@v4
      - run: |
          for service in scraper core-engine reporter attack-graph-engine; do
            docker build -t attackbot-$service backend/services/$service
          done
```

---

## 9. 📊 Observability Baseline

### 9.1 Prometheus Config

```yaml
# infra/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: scraper
    static_configs:
      - targets: ["scraper:8001"]
    metrics_path: /metrics

  - job_name: core-engine
    static_configs:
      - targets: ["core-engine:8002"]
    metrics_path: /metrics

  - job_name: reporter
    static_configs:
      - targets: ["reporter:8003"]
    metrics_path: /metrics

  - job_name: attack-graph-engine
    static_configs:
      - targets: ["attack-graph-engine:8006"]
    metrics_path: /metrics

  - job_name: api-gateway
    static_configs:
      - targets: ["api-gateway:8000"]
    metrics_path: /metrics

  # RabbitMQ management API metric export (add rabbitmq_exporter in M2+)
  - job_name: rabbitmq
    static_configs:
      - targets: ["rabbitmq:15692"]
```

---

### 9.2 Grafana Provisioning

```yaml
# infra/grafana/provisioning/datasources/datasources.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
  - name: Loki
    type: loki
    url: http://loki:3100
  - name: Tempo
    type: tempo
    url: http://tempo:3200
```

> 💡 **"Services Alive" dashboard** — import as JSON. Panels: one stat panel per service showing the last `/api/v1/health` status scraped from Prometheus. A green panel = service is up.

---

## 10. 📨 Message Envelope & Queue Contracts

> 💡 This is the **foundational contract section**. Every message on every queue shares the same outer envelope. This is defined once and never changed.

### 10.1 Versioning Strategy

| Rule | Detail |
|---|---|
| Field addition | ✅ Backward compatible. Consumers ignore unknown fields (`model_config = ConfigDict(extra='ignore')`). |
| Field removal | ❌ Breaking change. Requires `schema_version` bump and a coordinated deploy. |
| Field rename | ❌ Breaking change. Treated as removal + addition — version bump required. |
| Type change | ❌ Breaking change. Even widening (`int → float`) is a version bump. |
| Version bump procedure | 1) Deploy new consumer that handles both old and new version. 2) Deploy new producer emitting new version. 3) After all in-flight old-version messages drain, remove old handler. |
| `schema_version` format | `"1.0"` — major.minor string. Major bumps = breaking. Minor bumps = additive. |
| DLQ behavior | Messages rejected due to schema mismatch land in DLQ with `rejection_reason: schema_version_mismatch`. Never silently dropped. |

---

### 10.2 Canonical Envelope Schema

Every message on every queue in the system is wrapped in this envelope. The `payload` field contains the event-specific data.

```python
# backend/shared/schemas/envelope.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Any
import uuid

class MessageEnvelope(BaseModel):
    """
    Canonical wrapper for all AttackBot queue messages.
    Every producer MUST use this. Every consumer MUST validate against this.
    """
    model_config = ConfigDict(extra="ignore")  # forward-compat: ignore unknown fields

    # ── Identity ──────────────────────────────────────────────────
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Globally unique message ID. Used for deduplication and DLQ tracing.",
    )
    event_type: str = Field(
        description="Identifies the message type. Must match a registered handler. "
                    "Format: noun.verb (e.g. 'program.scraped', 'scan.completed'). "
                    "Consumers reject unknown event_types to DLQ.",
    )
    schema_version: str = Field(
        default="1.0",
        description="Version of the payload schema. Breaking changes bump major. "
                    "Additive changes bump minor. Consumers check major version only.",
    )

    # ── Tracing ───────────────────────────────────────────────────
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of message creation. ISO 8601 with timezone.",
    )
    trace_id: str | None = Field(
        default=None,
        description="Distributed trace ID propagated from originating HTTP request. "
                    "Set by api-gateway on inbound requests. Pass through to all "
                    "downstream messages to enable end-to-end trace correlation in Tempo.",
    )
    source_service: str = Field(
        description="Name of the service that produced this message. "
                    "Matches the SERVICE_NAME environment variable.",
    )

    # ── Payload ───────────────────────────────────────────────────
    payload: dict[str, Any] = Field(
        description="Event-specific data. Schema is defined per event_type "
                    "in backend/shared/schemas/.",
    )

    def get_major_version(self) -> int:
        """Returns the major version integer for compatibility checks."""
        return int(self.schema_version.split(".")[0])


def build_envelope(
    event_type: str,
    payload: dict[str, Any],
    source_service: str,
    schema_version: str = "1.0",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """
    Factory function. Always use this to create messages — never construct dicts manually.
    """
    return MessageEnvelope(
        event_type=event_type,
        payload=payload,
        source_service=source_service,
        schema_version=schema_version,
        trace_id=trace_id,
    ).model_dump(mode="json")
```

**Example wire format:**

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "program.scraped",
  "schema_version": "1.0",
  "timestamp": "2026-03-06T14:22:11.042Z",
  "trace_id": "abc123def456",
  "source_service": "scraper",
  "payload": {
    "...event specific fields..."
  }
}
```

---

### 10.3 Full `scan.jobs` Payload Schema

```python
# backend/shared/schemas/scan_jobs.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal
from uuid import UUID

# ── Sub-schemas ────────────────────────────────────────────────────────

class ScopeEntry(BaseModel):
    """One scope entry from program_scopes."""
    asset_type: Literal["url", "domain", "wildcard_domain", "ip_range", "mobile_app", "api"]
    value: str
    notes: str | None = None

class ScopeDefinition(BaseModel):
    in_scope: list[ScopeEntry] = Field(min_length=1)
    out_of_scope: list[ScopeEntry] = []

class FeatureFlags(BaseModel):
    """
    All flags default to their production-safe default as per architecture doc.
    Consumers read these flags to gate individual pipeline stages.
    """
    model_config = ConfigDict(extra="ignore")  # future flags are ignored, not rejected

    # Enabled by default
    asset_discovery:    bool = True
    fingerprinting:     bool = True
    enumeration:        bool = True
    nuclei:             bool = True
    xss:                bool = True
    cors:               bool = True
    secret_js:          bool = True
    browser_session:    bool = True
    api_fuzzing:        bool = True

    # Disabled by default — require explicit opt-in
    crlf:               bool = False
    sqli:               bool = False
    ssrf:               bool = False
    takeover:           bool = False
    secret_repo:        bool = False
    scenario_runner:    bool = False
    ai_hypothesis:      bool = False
    idor_verification:  bool = False   # gates two-session bootstrap in M5


# ── Primary payload ────────────────────────────────────────────────────

class ScanJobsPayload(BaseModel):
    """
    Payload schema for queue: scan.jobs
    Event type:     program.scraped
    Schema version: 1.0
    Producer:       scraper
    Consumer:       core-worker

    Version history:
      1.0 — initial schema
    """
    model_config = ConfigDict(extra="ignore")

    # ── Program identity ───────────────────────────────────────────
    program_id: UUID
    platform: Literal["hackerone", "bugcrowd", "intigriti", "yeswehack"]
    handle: str

    # ── Scope ─────────────────────────────────────────────────────
    scope: ScopeDefinition

    # ── Assets hint ───────────────────────────────────────────────
    summary_file: str | None = None

    # ── Scan configuration ────────────────────────────────────────
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    priority: int = Field(default=1, ge=1, le=10)
    scan_timeout_seconds: int = Field(default=14400, ge=300, le=86400)
    max_concurrent_requests: int = Field(default=10, ge=1, le=50)

    @field_validator("scope")
    @classmethod
    def scope_must_have_in_scope_entries(cls, v: ScopeDefinition) -> ScopeDefinition:
        if not v.in_scope:
            raise ValueError("scope.in_scope must contain at least one entry")
        return v


# ── Envelope builder helper ────────────────────────────────────────────

def build_scan_job_message(
    payload: ScanJobsPayload,
    source_service: str = "scraper",
    trace_id: str | None = None,
) -> dict:
    from shared.schemas.envelope import build_envelope
    return build_envelope(
        event_type="program.scraped",
        payload=payload.model_dump(mode="json"),
        source_service=source_service,
        schema_version="1.0",
        trace_id=trace_id,
    )
```

**Example `scan.jobs` wire message:**

```json
{
  "event_id": "7f3d9c2a-4b8e-4f1a-9c6d-2e5f8a1b3c7d",
  "event_type": "program.scraped",
  "schema_version": "1.0",
  "timestamp": "2026-03-06T14:22:11.042Z",
  "trace_id": "abc123",
  "source_service": "scraper",
  "payload": {
    "program_id": "550e8400-e29b-41d4-a716-446655440000",
    "platform": "hackerone",
    "handle": "example_program",
    "scope": {
      "in_scope": [
        { "asset_type": "wildcard_domain", "value": "*.example.com" },
        { "asset_type": "url", "value": "https://api.example.com" }
      ],
      "out_of_scope": [
        { "asset_type": "domain", "value": "admin.example.com" }
      ]
    },
    "summary_file": null,
    "feature_flags": {
      "asset_discovery": true,
      "fingerprinting": true,
      "enumeration": true,
      "nuclei": true,
      "xss": true,
      "cors": true,
      "secret_js": true,
      "browser_session": true,
      "api_fuzzing": true,
      "crlf": false,
      "sqli": false,
      "ssrf": false,
      "takeover": false,
      "secret_repo": false,
      "scenario_runner": false,
      "ai_hypothesis": false,
      "idor_verification": false
    },
    "priority": 1,
    "scan_timeout_seconds": 14400,
    "max_concurrent_requests": 10
  }
}
```

---

### 10.4 Full `report.jobs` Payload Schema

```python
# backend/shared/schemas/report_jobs.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal
from uuid import UUID

# ── Sub-schemas ────────────────────────────────────────────────────────

class SeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low + self.informational


class ExploitChainRef(BaseModel):
    """Lightweight reference to a chain — full data fetched by Reporter from Postgres."""
    chain_id: UUID
    chain_name: str
    combined_severity: Literal["critical", "high", "medium", "low", "informational"]
    step_count: int


# ── Primary payload ────────────────────────────────────────────────────

class ReportJobsPayload(BaseModel):
    """
    Payload schema for queue: report.jobs
    Event type:     scan.completed
    Schema version: 1.0
    Producer:       core-engine (core-worker)
    Consumer:       reporter-worker

    Version history:
      1.0 — initial schema
    """
    model_config = ConfigDict(extra="ignore")

    # ── Scan identity ──────────────────────────────────────────────
    scan_id: UUID
    program_id: UUID

    # ── Scan outcome ───────────────────────────────────────────────
    status: Literal["completed", "partial"]
    partial_stages: list[str] = []

    # ── Finding summary ────────────────────────────────────────────
    has_findings: bool
    finding_count: int = Field(ge=0)
    verified_count: int = Field(ge=0)
    severity_breakdown: SeverityBreakdown

    # ── Exploit chains ─────────────────────────────────────────────
    exploit_chains: list[ExploitChainRef] = []

    # ── Report generation parameters ──────────────────────────────
    formats_requested: list[Literal["pdf", "docx"]] = Field(default=["pdf", "docx"], min_length=1)
    include_evidence_screenshots: bool = True

    @field_validator("finding_count")
    @classmethod
    def finding_count_matches_has_findings(cls, v: int, info) -> int:
        has_findings = info.data.get("has_findings")
        if has_findings is True and v == 0:
            raise ValueError("has_findings=True but finding_count=0. Inconsistent state.")
        if has_findings is False and v > 0:
            raise ValueError("has_findings=False but finding_count>0. Inconsistent state.")
        return v


# ── Envelope builder helper ────────────────────────────────────────────

def build_report_job_message(
    payload: ReportJobsPayload,
    source_service: str = "core-engine",
    trace_id: str | None = None,
) -> dict:
    from shared.schemas.envelope import build_envelope
    return build_envelope(
        event_type="scan.completed",
        payload=payload.model_dump(mode="json"),
        source_service=source_service,
        schema_version="1.0",
        trace_id=trace_id,
    )
```

**Example `report.jobs` wire message:**

```json
{
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event_type": "scan.completed",
  "schema_version": "1.0",
  "timestamp": "2026-03-06T18:45:33.102Z",
  "trace_id": "abc123",
  "source_service": "core-engine",
  "payload": {
    "scan_id": "550e8400-e29b-41d4-a716-446655440001",
    "program_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "partial_stages": [],
    "has_findings": true,
    "finding_count": 9,
    "verified_count": 9,
    "severity_breakdown": {
      "critical": 1,
      "high": 3,
      "medium": 4,
      "low": 1,
      "informational": 0
    },
    "exploit_chains": [
      {
        "chain_id": "c9d8e7f6-a5b4-3210-9876-543210fedcba",
        "chain_name": "Subdomain Takeover → Session Fixation",
        "combined_severity": "critical",
        "step_count": 3
      }
    ],
    "formats_requested": ["pdf", "docx"],
    "include_evidence_screenshots": true
  }
}
```

---

### 10.5 Consumer Validation Pattern

Every consumer applies this pattern — **never trust queue input**:

```python
from shared.schemas.envelope import MessageEnvelope
from shared.schemas.scan_jobs import ScanJobsPayload
from pydantic import ValidationError
from shared.logging import get_logger

log = get_logger(__name__)

def consume_scan_job(raw_message: dict) -> None:
    # Step 1: validate envelope
    try:
        envelope = MessageEnvelope.model_validate(raw_message)
    except ValidationError as e:
        log.error("envelope_validation_failed", error=str(e), raw=raw_message)
        # Reject to DLQ — do not requeue
        raise

    # Step 2: check major version
    if envelope.get_major_version() != 1:
        log.error("unsupported_schema_version", version=envelope.schema_version)
        raise ValueError(f"Unsupported schema version: {envelope.schema_version}")

    # Step 3: validate payload
    try:
        payload = ScanJobsPayload.model_validate(envelope.payload)
    except ValidationError as e:
        log.error("payload_validation_failed",
                  event_id=envelope.event_id,
                  event_type=envelope.event_type,
                  error=str(e))
        raise

    # Step 4: bind trace context for all subsequent log calls
    import structlog
    structlog.contextvars.bind_contextvars(
        trace_id=envelope.trace_id,
        event_id=envelope.event_id,
        scan_program_id=str(payload.program_id),
    )

    # Step 5: process
    log.info("scan_job_accepted", program_id=str(payload.program_id))
    # ... actual work
```

---

## 11. ✅ Startup Order Validation

### 11.1 Cold Boot Test Script

```bash
#!/bin/bash
# scripts/healthcheck_all.sh
# Run after: docker compose up -d

set -e

SERVICES=(
  "scraper:http://localhost:8001/api/v1/health"
  "core-engine:http://localhost:8002/api/v1/health"
  "reporter:http://localhost:8003/api/v1/health"
  "attack-graph-engine:http://localhost:8006/api/v1/health"
  "api-gateway:http://localhost:8000/api/v1/health"
)

echo "Waiting for all services to be healthy..."
for entry in "${SERVICES[@]}"; do
  service="${entry%%:*}"
  url="${entry#*:}"
  echo -n "  $service... "
  for i in $(seq 1 30); do
    if curl -sf "$url" > /dev/null 2>&1; then
      echo "✅ healthy"
      break
    fi
    if [ $i -eq 30 ]; then
      echo "❌ TIMEOUT"
      exit 1
    fi
    sleep 5
  done
done

echo ""
echo "Checking MinIO buckets..."
docker compose exec minio-init \
  mc ls local/ | grep -E "reports|evidence|js-assets|summaries" \
  && echo "✅ All buckets exist" || echo "❌ Bucket check failed"

echo ""
echo "Checking Alembic migration..."
docker compose run --rm migrate alembic current \
  && echo "✅ Migration applied" || echo "❌ Migration check failed"

echo ""
echo "All checks passed. System is ready. 🚀"
```

---

### 11.2 `infra/README.md` — Bootstrap Notes

| Constraint | Detail |
|---|---|
| Cold boot time | ~3–4 minutes from `docker compose up` to all services healthy |
| Neo4j startup | 30–60s; `start_period: 60s` on healthcheck is mandatory |
| Vault restart | Dev mode does not persist secrets. After restart, `vault-init` re-seeds placeholders |
| `h2spacex` (M9+) | Requires raw socket access. Works in standard Docker. Fails in AWS Fargate and some GCP Cloud Run configs |
| MinIO anonymous access | Intentionally disabled. All report access via pre-signed URLs only |

---

## 12. 📋 Definition of Done Checklist

> Work through this list in order before calling M1 complete. No milestone is done until every box is checked.

### 🏗️ Infrastructure

- [ ] `docker compose up` completes with zero manual intervention on a cold boot
- [ ] All 6 Phase 1 infra containers show `healthy` in `docker ps`
- [ ] `migrate` container exits `0` and shows `service_completed_successfully`
- [ ] `minio-init` container exits `0` — all 4 buckets exist
- [ ] `vault-init` container exits `0` — placeholder secrets seeded
- [ ] No `mc anonymous set download` present in any init script
- [ ] `scripts/healthcheck_all.sh` passes end-to-end

### 📚 Shared Library

- [ ] `shared/config.py` — all services inherit, loads from env
- [ ] `shared/logging.py` — structured JSON output with `service` field on every line
- [ ] `shared/db.py` — async engine factory with `pool_pre_ping`
- [ ] `shared/health.py` — `HealthResponse` model
- [ ] `shared/exceptions.py` — full hierarchy
- [ ] `shared/queue.py` — `Queues` registry + `QueuePublisher` with passive declare
- [ ] `shared/vault.py` — Vault client
- [ ] `shared/storage.py` — MinIO client with presigned URL helper

### 📨 Message Contracts

- [ ] `shared/schemas/envelope.py` — canonical `MessageEnvelope` with `event_id`, `event_type`, `schema_version`, `timestamp`, `trace_id`, `source_service`, `payload`
- [ ] `shared/schemas/scan_jobs.py` — full `ScanJobsPayload` with `ScopeDefinition`, `FeatureFlags`, validators
- [ ] `shared/schemas/report_jobs.py` — full `ReportJobsPayload` with `SeverityBreakdown`, `ExploitChainRef`, validators
- [ ] Consumer validation pattern implemented in all worker skeletons
- [ ] Versioning strategy documented in `infra/README.md`

### 🦴 Service Skeletons

- [ ] All 4 FastAPI services return `200` on `GET /api/v1/health`
- [ ] All worker skeletons start without errors and log ready
- [ ] All services expose `/metrics` scraped by Prometheus

### 🗄️ Database

- [ ] `alembic upgrade head` runs cleanly from `migrate` container
- [ ] `programs` and `scans` tables exist in PostgreSQL after cold boot
- [ ] `alembic current` shows revision `001`

### 📊 Observability

- [ ] Grafana accessible at `http://localhost:3000`
- [ ] Prometheus, Loki, Tempo configured as Grafana data sources
- [ ] "Services Alive" dashboard shows all service health states
- [ ] At least one log line from each service visible in Loki

### ⚙️ CI

- [ ] `ruff check` passes on clean push
- [ ] `mypy` passes on shared library
- [ ] `pytest` runs (even if no tests yet beyond infra smoke test)
- [ ] Docker builds succeed for all 4 core services

---

> 📌 **End of M1 Implementation Plan.** The next document to produce is the M2 implementation plan covering the HackerOne collector, scope parser, and queue publisher — but only after this checklist is fully green.