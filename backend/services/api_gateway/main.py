# backend/services/api_gateway/main.py
# Full implementation in M10. M1 skeleton: health endpoint only.
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from backend.shared.config import BaseServiceConfig
from backend.shared.health import ComponentHealth, HealthResponse, HealthStatus
from backend.shared.logging import configure_logging, get_logger


class GatewayConfig(BaseServiceConfig):
    service_name: str = "api-gateway"
    port: int = 8000

    scraper_url: str = "http://scraper:8001"
    engine_url: str = "http://core-engine:8002"
    reporter_url: str = "http://reporter:8003"
    graph_url: str = "http://attack-graph-engine:8006"


settings = GatewayConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    log.info("service_starting", service=settings.service_name, port=settings.port)
    log.info("service_ready", service=settings.service_name)
    yield
    log.info("service_stopping", service=settings.service_name)


app = FastAPI(title="AttackBot API Gateway", version="1.0.0", lifespan=lifespan)

Instrumentator().instrument(app).expose(app)


async def _probe_upstream(url: str) -> HealthStatus:
    """Probe an upstream service health endpoint."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{url}/api/v1/health")
            return HealthStatus.HEALTHY if resp.status_code == 200 else HealthStatus.DEGRADED
    except Exception:
        return HealthStatus.UNHEALTHY


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    statuses = {
        "scraper": await _probe_upstream(settings.scraper_url),
        "core-engine": await _probe_upstream(settings.engine_url),
        "reporter": await _probe_upstream(settings.reporter_url),
        "attack-graph-engine": await _probe_upstream(settings.graph_url),
    }
    components = {name: ComponentHealth(status=s) for name, s in statuses.items()}
    overall = (
        HealthStatus.HEALTHY
        if all(s == HealthStatus.HEALTHY for s in statuses.values())
        else HealthStatus.DEGRADED
        if any(s != HealthStatus.UNHEALTHY for s in statuses.values())
        else HealthStatus.UNHEALTHY
    )
    return HealthResponse(
        status=overall,
        service=settings.service_name,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )



    