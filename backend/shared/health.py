from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status for a single dependency/component."""

    name: str
    status: HealthStatus
    latency_ms: float | None = None
    detail: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Full health response returned by /health endpoints."""

    status: HealthStatus
    components: dict[str, ComponentHealth] = Field(default_factory=dict)
    timestamp: str
    version: str = "2.0"
    service: str | None = None

    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY