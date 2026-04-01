# backend/shared/health.py
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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