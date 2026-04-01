# backend/services/attack_graph_engine/main.py
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from backend.shared.config import BaseServiceConfig
from backend.shared.db import check_db_health, init_db
from backend.shared.health import ComponentHealth, HealthResponse, HealthStatus
from backend.shared.logging import configure_logging, get_logger


class AttackGraphEngineConfig(BaseServiceConfig):
    service_name: str = "attack-graph-engine"
    port: int = 8006
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "attackbot"


settings = AttackGraphEngineConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    log.info("service_starting", service=settings.service_name, port=settings.port)
    init_db(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
    log.info("service_ready", service=settings.service_name)
    yield
    log.info("service_stopping", service=settings.service_name)


app = FastAPI(title="AttackBot Attack Graph Engine", version="1.0.0", lifespan=lifespan)

Instrumentator().instrument(app).expose(app)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_ok = await check_db_health()
    # Neo4j health check added in M8 when the driver is fully wired up.
    # For M1, database connectivity is sufficient proof of life.
    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        )
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