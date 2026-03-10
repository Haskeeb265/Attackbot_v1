"""
AttackBot shared health check models.
Every service exposes GET /api/v1/health returning HealthResponse.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ComponentHealth(BaseModel):
    status: HealthStatus
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: HealthStatus
    service: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    components: dict[str, ComponentHealth] = Field(default_factory=dict)
