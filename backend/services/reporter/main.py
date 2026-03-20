# backend/services/reporter/main.py
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from backend.shared.config import BaseServiceConfig
from backend.shared.db import check_db_health, init_db
from backend.shared.health import ComponentHealth, HealthResponse, HealthStatus
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import Queues, check_rabbitmq_health, ensure_queue_topology
from backend.shared.storage import init_storage, check_storage_health


class ReporterConfig(BaseServiceConfig):
    service_name: str = "reporter"
    port: int = 8003


settings = ReporterConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    log.info("service_starting", service=settings.service_name, port=settings.port)
    settings.require_fields(
        [
            "database_url",
            "rabbitmq_url",
            "minio_endpoint",
            "minio_access_key",
            "minio_secret_key",
        ]
    )
    init_db(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
    init_storage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    await ensure_queue_topology(settings.rabbitmq_url)
    log.info("service_ready", service=settings.service_name)
    yield
    log.info("service_stopping", service=settings.service_name)


app = FastAPI(title="AttackBot Reporter", version="1.0.0", lifespan=lifespan)

Instrumentator().instrument(app).expose(app)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_ok = await check_db_health()
    rabbitmq_ok = await check_rabbitmq_health(
        settings.rabbitmq_url,
        [Queues.REPORT_JOBS, Queues.REPORTS_COMPLETED],
    )
    storage_ok = check_storage_health()
    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        ),
        "rabbitmq": ComponentHealth(
            status=HealthStatus.HEALTHY if rabbitmq_ok else HealthStatus.UNHEALTHY
        ),
        "storage": ComponentHealth(
            status=HealthStatus.HEALTHY if storage_ok else HealthStatus.UNHEALTHY
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
        timestamp=datetime.now(timezone.utc),
        components=components,
    )
