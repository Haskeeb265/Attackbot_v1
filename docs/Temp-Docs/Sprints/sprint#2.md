# Sprint #2: P0/P1 - Resilience Foundation

> **Document Type:** Implementation Guide  
> **Target Audience:** Senior Engineers, Architects, QA Team  
> **Date:** 2026-04-19  
> **Branch:** M4_ReadTheRoom  
> **Duration:** Weeks 3-4  
> **Status:** Ready for Implementation  

---

## Sprint Overview

**Theme:** *Prevent cascading failures and enable cross-service debugging*  
**Business Impact:** **High** — Improves system reliability and debugging speed  
**Sprint Goal:** Services fail gracefully, all requests are traceable across boundaries

### Key Outcomes

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Cascading failures | Services timeout after 30-60s | **Fail fast in <1ms** | Circuit breaker metrics |
| Cross-service debugging | Manual log correlation | **Single trace view** | Jaeger UI |
| Request latency visibility | None | **Per-span timing** | Jaeger flame graphs |
| Service dependency graph | None | **Automatic** | Jaeger dependency view |

---

## Sprint Statistics

| Attribute | Value |
|-----------|-------|
| **Priority** | P0/P1 (Critical/High) |
| **Effort** | 16-22 hours |
| **Issues** | 2-3 |
| **Team Weeks** | 2 weeks |
| **Assignees** | 2 Engineers |

---

## Issues Included

| # | Issue | Category | Severity | Effort | Assignee | Days | Status |
|---|-------|----------|----------|--------|----------|-------|--------|
| **2** | Dead Letter Queue Blind Spot | Critical | 🔴 | 6-8h | Engineer B | Day 1-2 | *If not completed in S1* |
| **4** | Missing Circuit Breaker Pattern | Architectural | 🟡 | 4-6h | Engineer A | Day 1-3 | Not Started |
| **5** | Lack of Distributed Tracing | Architectural | 🟡 | 6-8h | Engineer B | Day 3-5 | Not Started |

> **Note:** Issue #2 (DLQ Blind Spot) should only be included in Sprint 2 if it was NOT completed in Sprint 1. If completed, focus on #4 and #5 only.

---

## Prerequisites

Before starting Sprint 2, ensure the following from Sprint 1 are complete:
- [ ] Issue #1: Watchdog Scan Recovery Mechanism (Data Integrity)
- [ ] Issue #3: Idempotency Guarantee Gaps (Data Integrity)
- [ ] Verified: No stuck scans in production
- [ ] Verified: No duplicate message processing

---

## Issue #2: Dead Letter Queue Blind Spot (Conditional)

> **⚠️ Only implement if NOT completed in Sprint 1**

If Issue #2 was already completed in Sprint 1, skip to Issue #4. Otherwise, see [Sprint #1 Implementation Guide](../sprint#1.md#issue-2-dead-letter-queue-blind-spot) for complete details.

### Quick Reference

**If needing to implement in Sprint 2:**
- Create `backend/shared/dlq_monitor.py`
- Add Prometheus metrics: `rabbitmq_dlq_depth`, `dlq_messages_replayed_total`, `dlq_messages_archived_total`
- Add scheduled job running every 60 seconds
- Add API endpoints: `/api/v1/queue/dlq/monitor`, `/api/v1/queue/dlq/{name}/inspect`, `/api/v1/queue/dlq/{name}/replay`
- Configure Grafana alerts in `grafana/alerts/dlq_alerts.yml`

**Acceptance Criteria:**
- [ ] `rabbitmq_dlq_depth` metric per queue
- [ ] Scheduled job runs every 60s
- [ ] Grafana alert triggers when DLQ depth > 0 for 5min
- [ ] All API endpoints functional

---

## Issue #4: Missing Circuit Breaker Pattern

### Objective
Prevent cascading failures when downstream services are unavailable.

### Problem Statement
When downstream services are unavailable:
1. **Slow degradation:** Caller waits for full timeout (default: 30-60s)
2. **Resource exhaustion:** Blocked threads/connections pile up
3. **Cascading failure:** Upstream service becomes unresponsive
4. **No recovery:** Service keeps hammering unavailable endpoint

**Evidence:** Reporter → Core Engine calls wait full timeout when Core Engine is down, causing report generation to take 60+ seconds.

### Root Causes
- No circuit breaker pattern implemented
- Direct HTTP calls without fail-fast mechanism
- No visibility into service health status

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 1 | Install `aiobreaker` library | `requirements.txt` | 0.5h | Engineer A |
| 1 | Create ServiceCircuitBreakers registry | `shared/circuit_breaker.py` | 2h | Engineer A |
| 1 | Add Prometheus metrics for circuit state | `shared/circuit_breaker.py` | 1h | Engineer A |
| 2 | Add state change event listeners (logging + metrics) | `shared/circuit_breaker.py` | 1h | Engineer A |
| 2 | Decorate Core Engine → Scraper HTTP calls | `core_engine/main.py` (or clients) | 1h | Engineer A |
| 3 | Decorate Reporter → Core Engine HTTP calls | `reporter/clients/core_engine.py` | 1h | Engineer A |
| 3 | Add admin endpoints for circuit breaker status | `core_engine/main.py` | 1h | Engineer A |

### Solution Code

#### 1. Install Dependencies

```bash
# Add to requirements.txt for all services
pip install aiobreaker==1.4.0
```

#### 2. Circuit Breaker Implementation

```python
# File: backend/shared/circuit_breaker.py

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

from typing import Optional, Callable, Any, Tuple, List
from datetime import timedelta
from enum import Enum

from aiobreaker import CircuitBreaker, CircuitBreakerError
import httpx
from prometheus_client import Gauge, Counter

from backend.shared.logging import get_logger

logger = get_logger(__name__)

# Prometheus metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Current state of circuit breaker (0=closed, 1=open, 2=half_open)',
    ['service', 'target_service']
)

circuit_breaker_transitions = Counter(
    'circuit_breaker_transitions_total',
    'Total circuit breaker state transitions',
    ['service', 'target_service', 'from_state', 'to_state']
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures_total',
    'Total failures counted by circuit breaker',
    ['service', 'target_service']
)

circuit_breaker_rejections = Counter(
    'circuit_breaker_rejections_total',
    'Total requests rejected by open circuit',
    ['service', 'target_service']
)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ServiceCircuitBreakers:
    """
    Registry of circuit breakers for external services.
    
    Provides centralized access to all circuit breakers with consistent
    configuration and metrics.
    """
    
    # Service-specific circuit breakers
    # Each has different sensitivity based on service criticality
    _breakers: dict[str, CircuitBreaker] = {}
    
    @classmethod
    def scraper_api(cls) -> CircuitBreaker:
        """Circuit breaker for Scraper API service."""
        if 'scraper_api' not in cls._breakers:
            cls._breakers['scraper_api'] = CircuitBreaker(
                fail_max=5,                    # Open after 5 failures
                timeout_duration=timedelta(seconds=60),  # Stay open for 60s
                expected_exception=httpx.HTTPStatusError,
                name="scraper_api",
                allow_half_open=True
            )
            cls._setup_listeners('scraper_api')
        return cls._breakers['scraper_api']
    
    @classmethod
    def core_engine_api(cls) -> CircuitBreaker:
        """Circuit breaker for Core Engine API service."""
        if 'core_engine_api' not in cls._breakers:
            cls._breakers['core_engine_api'] = CircuitBreaker(
                fail_max=5,
                timeout_duration=timedelta(seconds=60),
                expected_exception=httpx.HTTPStatusError,
                name="core_engine_api",
                allow_half_open=True
            )
            cls._setup_listeners('core_engine_api')
        return cls._breakers['core_engine_api']
    
    @classmethod
    def hackerone_api(cls) -> CircuitBreaker:
        """Circuit breaker for HackerOne API (external service)."""
        if 'hackerone_api' not in cls._breakers:
            cls._breakers['hackerone_api'] = CircuitBreaker(
                fail_max=3,                    # More sensitive for external API
                timeout_duration=timedelta(seconds=120),  # Longer recovery time
                expected_exception=(httpx.HTTPStatusError, httpx.TimeoutException),
                name="hackerone_api",
                allow_half_open=True
            )
            cls._setup_listeners('hackerone_api')
        return cls._breakers['hackerone_api']
    
    @classmethod
    def _setup_listeners(cls, breaker_name: str):
        """Setup state change listeners for a circuit breaker."""
        breaker = cls._breakers[breaker_name]
        
        # Track state in metrics
        @breaker.state_change_hook
        def on_state_change(old_state: int, new_state: int):
            from_state = CircuitState(CircuitBreaker.STATE_NAMES[old_state])
            to_state = CircuitState(CircuitBreaker.STATE_NAMES[new_state])
            
            # Update state gauge
            circuit_breaker_state.labels(
                service='attackbot',
                target_service=breaker_name
            ).set(new_state)
            
            # Increment transition counter
            circuit_breaker_transitions.labels(
                service='attackbot',
                target_service=breaker_name,
                from_state=from_state.value,
                to_state=to_state.value
            ).inc()
            
            # Log state change
            if to_state == CircuitState.OPEN:
                logger.error(
                    "Circuit breaker OPENED - service unavailable",
                    circuit=breaker_name,
                    fail_count=breaker.fail_counter
                )
            elif to_state == CircuitState.CLOSED:
                logger.info(
                    "Circuit breaker CLOSED - service recovered",
                    circuit=breaker_name
                )
            elif to_state == CircuitState.HALF_OPEN:
                logger.warning(
                    "Circuit breaker HALF-OPEN - testing service recovery",
                    circuit=breaker_name
                )
    
    @classmethod
    def get_state_summary(cls) -> dict[str, str]:
        """Get current state of all circuit breakers."""
        return {
            name: CircuitBreaker.STATE_NAMES[breaker.current_state]
            for name, breaker in cls._breakers.items()
        }
    
    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers (admin operation)."""
        for name, breaker in cls._breakers.items():
            breaker.close()
            logger.info(f"Circuit breaker reset: {name}")
        logger.info("All circuit breakers reset")
    
    @classmethod
    def get_breaker(cls, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return cls._breakers.get(name)


class CircuitBreakerErrorHandler:
    """Custom error handler for circuit breaker rejections."""
    
    @staticmethod
    async def handle_breaker_open(breaker_name: str, target_service: str, original_func: Callable, *args, **kwargs):
        """
        Handle circuit breaker open state.
        
        Args:
            breaker_name: Name of the circuit breaker
            target_service: The service being called
            original_func: The original function that was decorated
            *args, **kwargs: Original function arguments
        
        Returns:
            Tuple of (status_code, response_dict) for HTTP-like responses
        """
        # Increment rejection counter
        circuit_breaker_rejections.labels(
            service='attackbot',
            target_service=target_service
        ).inc()
        
        logger.warning(
            "Circuit breaker rejected request",
            circuit=breaker_name,
            target_service=target_service,
            circuit_state="open"
        )
        
        return (503, {
            "error": "Service unavailable",
            "message": f"{target_service} is currently unavailable (circuit breaker open)",
            "circuit_breaker": breaker_name,
            "retry_after": 60  # Suggest retry after timeout_duration
        })


# Wrap circuit breaker to add custom rejection handling
class CircuitBreakerWrapper:
    """
    Wrapper that adds custom handling for circuit breaker open state.
    
    This creates a decorator that:
    1. Applies the circuit breaker
    2. Handles CircuitBreakerError with custom response
    3. Metrics tracking
    """
    
    def __init__(self, breaker: CircuitBreaker, service_name: str, target_service: str):
        self.breaker = breaker
        self.service_name = service_name
        self.target_service = target_service
    
    def __call__(self, func: Callable):
        async def wrapped(*args, **kwargs):
            try:
                # Apply circuit breaker
                result = await self.breaker.call(func, *args, **kwargs)
                return result
            except CircuitBreakerError as e:
                # Custom handling for open circuit
                return await CircuitBreakerErrorHandler.handle_breaker_open(
                    self.breaker.name,
                    self.target_service,
                    func,
                    *args,
                    **kwargs
                )
            except Exception as e:
                # Increment failure counter for expected exceptions
                if isinstance(e, self.breaker.expected_exception):
                    circuit_breaker_failures.labels(
                        service=self.service_name,
                        target_service=self.target_service
                    ).inc()
                raise
        
        return wrapped


# Convenience decorators
def circuit_breaker_scraper(func: Callable):
    """Decorator for Scraper API calls."""
    return CircuitBreakerWrapper(
        ServiceCircuitBreakers.scraper_api(),
        'attackbot',
        'scraper_api'
    )(func)


def circuit_breaker_core_engine(func: Callable):
    """Decorator for Core Engine API calls."""
    return CircuitBreakerWrapper(
        ServiceCircuitBreakers.core_engine_api(),
        'attackbot',
        'core_engine_api'
    )(func)


def circuit_breaker_hackerone(func: Callable):
    """Decorator for HackerOne API calls."""
    return CircuitBreakerWrapper(
        ServiceCircuitBreakers.hackerone_api(),
        'attackbot',
        'hackerone_api'
    )(func)
```

#### 3. Enhanced HTTP Client with Circuit Breaker

```python
# File: backend/services/core_engine/clients/scraper.py

"""
Core Engine's HTTP client for Scraper service with circuit breaker.
"""

import httpx
from typing import Optional, Dict, Any

from backend.shared.circuit_breaker import circuit_breaker_scraper
from backend.shared.logging import get_logger
from backend.services.core_engine.config import EngineConfig

logger = get_logger(__name__)
config = EngineConfig()


class ScraperClient:
    """HTTP client for Scraper service with circuit breaker protection."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or config.scraper_api_url
        self.timeout = httpx.Timeout(
            timeout=config.upstream_timeout_seconds,
            connect=config.upstream_connect_timeout_seconds,
        )
    
    @circuit_breaker_scraper
    async def get_program_scope(self, program_id: str) -> Dict[str, Any]:
        """
        Get program scope from Scraper service.
        
        Protected by circuit breaker - will fail fast if Scraper is down.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/api/v1/programs/{program_id}/scope"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    @circuit_breaker_scraper
    async def list_programs(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """List all programs from Scraper service."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/api/v1/programs?page={page}&per_page={per_page}"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()


# Singleton instance
scraper_client = ScraperClient()
```

```python
# File: backend/services/reporter/clients/core_engine.py

"""
Reporter's HTTP client for Core Engine service with circuit breaker.
"""

import httpx
from typing import Optional, Dict, Any, List

from backend.shared.circuit_breaker import circuit_breaker_core_engine
from backend.shared.logging import get_logger
from backend.services.reporter.config import ReporterConfig

logger = get_logger(__name__)
config = ReporterConfig()


class CoreEngineClient:
    """HTTP client for Core Engine service with circuit breaker protection."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or config.core_engine_api_url
        self.timeout = httpx.Timeout(
            timeout=config.upstream_timeout_seconds,
            connect=config.upstream_connect_timeout_seconds,
        )
    
    @circuit_breaker_core_engine
    async def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan details from Core Engine."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/api/v1/scans/{scan_id}"
            response = await client.get(url)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
    
    @circuit_breaker_core_engine
    async def get_scan_findings(self, scan_id: str, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """Get scan findings from Core Engine."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/api/v1/scans/{scan_id}/findings?page={page}&per_page={per_page}"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    @circuit_breaker_core_engine
    async def get_finding_evidence(self, scan_id: str, finding_id: str) -> Dict[str, Any]:
        """Get evidence for a specific finding."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/api/v1/scans/{scan_id}/findings/{finding_id}/evidence"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()


# Singleton instance
core_engine_client = CoreEngineClient()
```

#### 4. Admin API Endpoints

```python
# File: backend/services/core_engine/main.py (add these endpoints)

from fastapi import HTTPException
from backend.shared.circuit_breaker import ServiceCircuitBreakers, CircuitState


@app.get("/api/v1/circuit-breakers")
async def get_circuit_breakers():
    """
    Get current state of all circuit breakers.
    
    Returns:
        Dict mapping service name to circuit breaker state
    """
    states = ServiceCircuitBreakers.get_state_summary()
    
    # Add detailed information
    detailed = {}
    for name, state_str in states.items():
        breaker = ServiceCircuitBreakers.get_breaker(name)
        if breaker:
            detailed[name] = {
                "state": state_str,
                "fail_count": breaker.fail_counter,
                "timeout_duration_seconds": breaker.timeout_duration.total_seconds(),
                "fail_max": breaker.fail_max,
                "next_attempt": None
            }
            if breaker.current_state == CircuitBreaker.STATE_OPEN:
                detailed[name]["next_attempt"] = breaker.opened_at.isoformat()
    
    return {
        "circuit_breakers": detailed,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/v1/circuit-breakers/reset")
async def reset_circuit_breakers():
    """
    Reset all circuit breakers to CLOSED state.
    
    This is an administrative endpoint for manual intervention.
    Use with caution - should only be called when downstream service is confirmed recovered.
    """
    ServiceCircuitBreakers.reset_all()
    
    return {
        "status": "success",
        "message": "All circuit breakers reset",
        "new_states": ServiceCircuitBreakers.get_state_summary(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/circuit-breakers/{service_name}")
async def get_circuit_breaker(service_name: str):
    """
    Get details for a specific circuit breaker.
    """
    breaker = ServiceCircuitBreakers.get_breaker(service_name)
    
    if not breaker:
        raise HTTPException(
            status_code=404,
            detail=f"Circuit breaker not found: {service_name}"
        )
    
    state_name = CircuitBreaker.STATE_NAMES[breaker.current_state]
    
    return {
        "service": service_name,
        "state": state_name,
        "fail_count": breaker.fail_counter,
        "fail_max": breaker.fail_max,
        "timeout_duration_seconds": breaker.timeout_duration.total_seconds(),
        "opened_at": breaker.opened_at.isoformat() if breaker.opened_at else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/v1/circuit-breakers/{service_name}/reset")
async def reset_circuit_breaker(service_name: str):
    """
    Reset a specific circuit breaker to CLOSED state.
    """
    breaker = ServiceCircuitBreakers.get_breaker(service_name)
    
    if not breaker:
        raise HTTPException(
            status_code=404,
            detail=f"Circuit breaker not found: {service_name}"
        )
    
    breaker.close()
    logger.info(f"Circuit breaker manually reset: {service_name}")
    
    return {
        "status": "success",
        "service": service_name,
        "new_state": "closed",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

#### 5. Configuration Updates

```python
# File: backend/services/core_engine/config.py

from pydantic import BaseSettings, Field
from typing import Optional

class EngineConfig(BaseSettings):
    # ... existing config ...
    
    # Circuit breaker configuration
    circuit_breaker_fail_max: int = Field(default=5, env="CIRCUIT_BREAKER_FAIL_MAX")
    circuit_breaker_timeout_seconds: int = Field(default=60, env="CIRCUIT_BREAKER_TIMEOUT_SECONDS")
    
    # Upstream service URLs
    scraper_api_url: str = Field(
        default="http://scraper:8000",
        env="SCRAPER_API_URL"
    )


# File: backend/services/reporter/config.py

class ReporterConfig(BaseSettings):
    # ... existing config ...
    
    # Upstream service URLs
    core_engine_api_url: str = Field(
        default="http://core_engine:8000",
        env="CORE_ENGINE_API_URL"
    )
    upstream_timeout_seconds: int = Field(default=30, env="UPSTREAM_TIMEOUT_SECONDS")
    upstream_connect_timeout_seconds: int = Field(default=5, env="UPSTREAM_CONNECT_TIMEOUT_SECONDS")
```

### Acceptance Criteria

- [ ] Circuit breakers configured for: scraper_api, core_engine_api, hackerone_api
- [ ] `circuit_breaker_state` metric per service
- [ ] `circuit_breaker_transitions_total` metric tracks state changes
- [ ] Circuit opens after 5 consecutive failures
- [ ] Circuit stays open for 60 seconds (configurable)
- [ ] Service returns 503 when circuit is open
- [ ] Admin endpoint: `GET /api/v1/circuit-breakers` returns all states
- [ ] Admin endpoint: `POST /api/v1/circuit-breakers/reset` resets all
- [ ] Manual endpoint: `GET /api/v1/circuit-breakers/{service}` returns details
- [ ] Test: Take down Core Engine, verify Reporter fails fast with 503 (not timeout after 60s)

### Rollback Strategy

**Rollback Time:** <10 minutes

```bash
# Revert circuit breaker implementation
git checkout HEAD~1 -- backend/shared/circuit_breaker.py
git checkout HEAD~1 -- backend/services/core_engine/clients/scraper.py
git checkout HEAD~1 -- backend/services/reporter/clients/core_engine.py
git checkout HEAD~1 -- backend/services/core_engine/main.py
git checkout HEAD~1 -- backend/services/core_engine/config.py
git checkout HEAD~1 -- backend/services/reporter/config.py

# Revert requirements
git checkout HEAD~1 -- requirements.txt
```

### Testing Checklist

- [ ] Unit test: Circuit breaker state transitions
- [ ] Unit test: Circuit breaker timeout recovery
- [ ] Integration test: Circuit breaker + HTTP client interaction
- [ ] Manual test: Downstream failure simulation
- [ ] Manual test: Circuit breaker reset functionality

---

## Issue #5: Lack of Distributed Tracing

### Objective
Full cross-service request tracing for debugging and latency analysis.

### Problem Statement
Cannot trace requests across service boundaries. Current limitations:
1. **No trace propagation:** Each service logs independently with no parent/child trace relationship
2. **No span timing:** Cannot measure time spent in each stage or service
3. **No cross-service visualization:** Cannot see the full request flow in a single view
4. **Manual correlation:** Must manually search logs across services using `scan_id`
5. **No dependency mapping:** Cannot visualize which services call which services

**Example:** Diagnosing why a scan took 45 minutes currently requires manual log analysis across multiple services. With distributed tracing, this becomes a single query in Jaeger.

### Root Causes
- No distributed tracing infrastructure implemented
- No trace context propagation between services
- No centralized trace collection

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 3 | Install OpenTelemetry packages | `requirements.txt` (all services) | 1h | Engineer B |
| 3 | Create tracing initialization module | `shared/tracing.py` | 2h | Engineer B |
| 4 | Add trace context to MessageEnvelope | `shared/schemas/envelope.py` | 1h | Engineer B |
| 4 | Instrument FastAPI (auto) | All `main.py` | 1h | Engineer B |
| 5 | Instrument httpx (auto) | `shared/tracing.py` | 1h | Engineer B |
| 5 | Instrument Celery (auto) | `shared/tracing.py` | 1h | Engineer B |
| 5 | Deploy Jaeger (Docker) | `docker-compose.yml` | 1h | Engineer B |

### Solution Code

#### 1. Install Dependencies

```bash
# Add to requirements.txt for ALL services
pip install opentelemetry-api==1.23.0
pip install opentelemetry-sdk==1.23.0
pip install opentelemetry-instrumentation-fastapi==0.44b0
pip install opentelemetry-instrumentation-httpx==0.44b0
pip install opentelemetry-instrumentation-celery==0.44b0
pip install opentelemetry-instrumentation-sqlalchemy==0.44b0
pip install opentelemetry-exporter-jaeger==1.23.0
```

#### 2. OpenTelemetry Configuration

```python
# File: backend/shared/tracing.py

"""
Distributed tracing configuration using OpenTelemetry.

Exports traces to Jaeger for visualization and analysis.
"""

from typing import Optional
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, SERVICE_INSTANCE_ID
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.trace import get_current_span, Status, StatusCode

from backend.shared.logging import get_logger

logger = get_logger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_tracer_provider: Optional[TracerProvider] = None


def init_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    jaeger_host: str = "jaeger",
    jaeger_port: int = 6831,
    enable_console_export: bool = False,
    sample_rate: float = 1.0  # 1.0 = 100% sampling, 0.1 = 10%
):
    """
    Initialize OpenTelemetry distributed tracing.
    
    Args:
        service_name: Name of the service (e.g., "core_engine")
        service_version: Version string
        jaeger_host: Jaeger agent hostname
        jaeger_port: Jaeger agent port (UDP)
        enable_console_export: If True, also print spans to console
        sample_rate: Sampling rate (0.0 to 1.0)
    """
    global _tracer, _tracer_provider
    
    # Create resource with service metadata
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        SERVICE_INSTANCE_ID: os.getenv("HOSTNAME", os.getenv("POD_NAME", "unknown"))
    })
    
    # Create tracer provider with sampling
    _tracer_provider = TracerProvider(
        resource=resource,
        sampler=trace.sampling.TraceIdRatioBased(sample_rate)
    )
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    
    # Add batch span processor (async, batched)
    _tracer_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Optional: Console exporter for debugging
    if enable_console_export:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )
    
    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)
    
    # Get tracer for this service
    _tracer = trace.get_tracer(service_name, service_version)
    
    logger.info(
        "Distributed tracing initialized",
        service_name=service_name,
        service_version=service_version,
        jaeger_host=jaeger_host,
        jaeger_port=jaeger_port,
        sampling_rate=sample_rate
    )


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    if _tracer is None:
        # Auto-initialize with defaults if not already done
        init_tracing(
            service_name="unknown",
            enable_console_export=True
        )
    return _tracer


def get_tracer_provider() -> Optional[TracerProvider]:
    """Get the global tracer provider."""
    return _tracer_provider


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled."""
    return _tracer is not None


def instrument_fastapi(app):
    """
    Auto-instrument FastAPI application.
    Creates spans for all HTTP requests automatically.
    """
    if not is_tracing_enabled():
        logger.warning("Tracing not initialized, skipping FastAPI instrumentation")
        return
    
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumented for tracing")


def instrument_httpx():
    """
    Auto-instrument httpx HTTP client.
    Propagates trace context in HTTP headers.
    """
    if not is_tracing_enabled():
        logger.warning("Tracing not initialized, skipping httpx instrumentation")
        return
    
    HTTPXClientInstrumentor().instrument()
    logger.info("HTTPX instrumented for tracing")


def instrument_celery():
    """
    Auto-instrument Celery.
    Creates spans for task execution and propagates context.
    """
    if not is_tracing_enabled():
        logger.warning("Tracing not initialized, skipping Celery instrumentation")
        return
    
    CeleryInstrumentor().instrument()
    logger.info("Celery instrumented for tracing")


def instrument_sqlalchemy(engine):
    """
    Auto-instrument SQLAlchemy.
    Creates spans for database queries.
    
    Args:
        engine: SQLAlchemy engine (sync)
    """
    if not is_tracing_enabled():
        logger.warning("Tracing not initialized, skipping SQLAlchemy instrumentation")
        return
    
    SQLAlchemyInstrumentor().instrument(engine=engine)
    logger.info("SQLAlchemy instrumented for tracing")


# Context propagation utilities
def inject_trace_context(headers: dict) -> dict:
    """
    Inject current trace context into HTTP headers.
    
    Args:
        headers: Existing headers dict
    
    Returns:
        Headers dict with trace context added
    """
    from opentelemetry.propagate import inject
    
    if not is_tracing_enabled():
        return headers
    
    carrier = headers.copy()
    inject(carrier)
    return carrier


def extract_trace_context(headers: dict):
    """
    Extract trace context from HTTP headers and set as current.
    
    Args:
        headers: Headers dict from incoming request
    
    Returns:
        Context object (can be used with trace.set_span_in_context)
    """
    from opentelemetry.propagate import extract
    
    if not is_tracing_enabled():
        return None
    
    return extract(headers)


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID as hex string."""
    span = get_current_span()
    if span:
        context = span.get_span_context()
        return format(context.trace_id, '032x')
    return None


def get_current_span_id() -> Optional[str]:
    """Get the current span ID as hex string."""
    span = get_current_span()
    if span:
        context = span.get_span_context()
        return format(context.span_id, '016x')
    return None


# Utility for manually creating spans
def trace_function(service: str, function_name: str, attributes: Optional[dict] = None):
    """
    Context manager for manually tracing a function.
    
    Usage:
        with trace_function("core_engine", "process_scan", {"scan_id": scan_id}):
            # function body
    
    Args:
        service: Service name
        function_name: Name of the function/operation
        attributes: Optional dict of span attributes
    """
    from contextlib import contextmanager
    
    @contextmanager
    def wrapper():
        tracer = get_tracer()
        with tracer.start_as_current_span(
            function_name,
            attributes=attributes or {}
        ) as span:
            try:
                yield
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, description=str(e)))
                span.record_exception(e)
                raise
    
    return wrapper


async def trace_async_function(service: str, function_name: str, attributes: Optional[dict] = None):
    """
    Async context manager for manually tracing an async function.
    
    Usage:
        async with trace_async_function("core_engine", "process_scan", {"scan_id": scan_id}):
            # async function body
    
    Args:
        service: Service name
        function_name: Name of the function/operation
        attributes: Optional dict of span attributes
    """
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def wrapper():
        tracer = get_tracer()
        with tracer.start_as_current_span(
            function_name,
            attributes=attributes or {}
        ) as span:
            try:
                yield
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, description=str(e)))
                span.record_exception(e)
                raise
    
    return wrapper
```

#### 3. Message Envelope with Trace Context

```python
# File: backend/shared/schemas/envelope.py

from pydantic import BaseModel, Field
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone


class MessageEnvelope(BaseModel):
    """
    Standard envelope for all messages in the system.
    
    Includes trace context for distributed tracing across service boundaries.
    """
    # Unique message identifier
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Message type for routing
    event_type: str
    
    # Schema version for backwards compatibility
    schema_version: str = "1.0"
    
    # Timestamp when message was created
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # OpenTelemetry trace context for distributed tracing
    trace_id: Optional[str] = None  # Hex string, 32 chars
    span_id: Optional[str] = None   # Hex string, 16 chars
    
    # Message source
    source_service: str
    
    # Message payload (service-specific)
    payload: dict
    
    class Config:
        json_schema_extra = {
            "examples": [{
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "scan.started",
                "schema_version": "1.0",
                "timestamp": "2026-04-19T10:00:00+00:00",
                "trace_id": "5b8aa3b09f138340b104d2b8b4d27598",
                "span_id": "e42eef90e6761086",
                "source_service": "core_engine",
                "payload": {}
            }]
        }


def build_envelope(
    event_type: str,
    payload: dict,
    source_service: str,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None
) -> MessageEnvelope:
    """
    Build message envelope with optional trace context.
    
    Automatically injects current trace context if available.
    
    Args:
        event_type: Message type (e.g., "scan.started", "report.generate")
        payload: Message payload (service-specific data)
        source_service: Name of the service sending the message
        trace_id: Optional trace ID (auto-injected from current context)
        span_id: Optional span ID (auto-injected from current context)
    
    Returns:
        MessageEnvelope with trace context
    """
    # Auto-inject current trace context if not provided
    if trace_id is None or span_id is None:
        from backend.shared.tracing import get_current_trace_id, get_current_span_id
        if trace_id is None:
            trace_id = get_current_trace_id()
        if span_id is None:
            span_id = get_current_span_id()
    
    return MessageEnvelope(
        event_id=str(uuid4()),
        event_type=event_type,
        schema_version="1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        trace_id=trace_id,
        span_id=span_id,
        source_service=source_service,
        payload=payload
    )


def get_trace_context_from_envelope(envelope: MessageEnvelope) -> dict:
    """
    Extract trace context from message envelope for setting as current context.
    
    Use this when receiving a message to continue the trace.
    
    Args:
        envelope: MessageEnvelope with trace context
    
    Returns:
        Dict with trace_id and span_id (or empty dict if no context)
    """
    return {
        "trace_id": envelope.trace_id,
        "span_id": envelope.span_id
    }
```

#### 4. Enhanced FastAPI Application with Tracing

```python
# File: backend/services/core_engine/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

from backend.shared.tracing import (
    init_tracing,
    instrument_fastapi,
    instrument_httpx,
    instrument_sqlalchemy,
    get_tracer,
    get_current_trace_id
)
from backend.services.core_engine.config import EngineConfig

config = EngineConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Core Engine starting up")
    
    # Initialize tracing FIRST (before any other instrumentation)
    init_tracing(
        service_name="core_engine",
        service_version="1.0.0",
        jaeger_host=config.jaeger_host,
        jaeger_port=config.jaeger_port,
        enable_console_export=config.tracing_console_export,
        sample_rate=config.tracing_sample_rate
    )
    
    # Instrument libraries
    instrument_httpx()
    instrument_fastapi(app)
    
    # Initialize database
    init_db(settings.database_url)
    from backend.shared.db import get_engine
    engine = get_engine()
    instrument_sqlalchemy(engine)
    
    # Instrument Celery (if worker process)
    if "celery" in os.getenv(" specifically for worker", ""):
        instrument_celery()
    
    # ... rest of existing startup ...
    
    yield
    
    logger.info("Core Engine shutting down")
    scheduler.shutdown(wait=True)


app = FastAPI(lifespan=lifespan)


# Example of manual span creation
from fastapi import Request
from backend.shared.tracing import get_tracer, trace_async_function

@app.post("/api/v1/scans/start")
async def start_scan(request: StartScanRequest):
    """Start a new scan with distributed tracing."""
    tracer = get_tracer()
    
    # Create a span for the entire request
    with tracer.start_as_current_span(
        "start_scan",
        attributes={
            "program_id": str(request.program_id),
            "priority": request.priority
        }
    ) as span:
        try:
            # Build payload
            async with trace_async_function("core_engine", "build_payload", {
                "program_id": str(request.program_id)
            }):
                payload = await _build_payload_from_scraper(request.program_id)
            
            # Reserve scan ID
            async with trace_async_function("core_engine", "reserve_scan_id"):
                scan_id = await _reserve_scan_id(payload, request.priority)
            
            # Enqueue scan
            async with trace_async_function("core_engine", "enqueue_scan", {
                "scan_id": str(scan_id)
            }):
                await _enqueue_scan(scan_id, payload, request)
            
            # Set span attributes with results
            span.set_attribute("scan_id", str(scan_id))
            span.set_attribute("queued", True)
            span.set_status(trace.Status(trace.StatusCode.OK))
            
            return {
                "status": "queued",
                "scan_id": str(scan_id),
                "program_id": str(request.program_id),
                "trace_id": get_current_trace_id()
            }
            
        except Exception as e:
            span.set_status(
                trace.Status(
                    trace.StatusCode.ERROR,
                    description=str(e)
                )
            )
            span.record_exception(e)
            raise
```

#### 5. Enhanced Celery Worker with Tracing

```python
# File: backend/services/core_engine/worker.py

import os
import asyncio

# Initialize tracing for worker process
from backend.shared.tracing import (
    init_tracing,
    instrument_celery,
    instrument_httpx,
    instrument_sqlalchemy,
    get_tracer
)
from backend.shared.db import get_engine
from backend.services.core_engine.config import EngineConfig

config = EngineConfig()

# Initialize tracing
init_tracing(
    service_name="core_worker",
    service_version="1.0.0",
    jaeger_host=os.getenv("JAEGER_HOST", config.jaeger_host),
    jaeger_port=int(os.getenv("JAEGER_PORT", str(config.jaeger_port))),
    enable_console_export=os.getenv("TRACING_CONSOLE", "false").lower() == "true"
)

# Auto-instrument Celery
instrument_celery()

# Auto-instrument httpx
instrument_httpx()

# Auto-instrument SQLAlchemy
engine = get_engine()
instrument_sqlalchemy(engine)


# Celery task now has automatic tracing
from celery import Celery
from backend.shared.tracing import get_current_trace_id, get_current_span_id

@app.task(bind=True, max_retries=0)
def run_scan_task(self, payload: dict):
    """Process scan job from queue with tracing context."""
    # Extract trace context from payload if present
    if isinstance(payload, dict):
        trace_id = payload.get("trace_id")
        span_id = payload.get("span_id")
        
        # Set as current context for this task
        if trace_id and span_id:
            # Note: This would need custom context management
            # In practice, trace context should be in Celery message headers
            pass
    
    # Run async pipeline
    asyncio.run(_async_scan_pipeline_with_tracing(payload))


async def _async_scan_pipeline_with_tracing(payload: dict) -> None:
    """Full async pipeline with distributed tracing."""
    tracer = get_tracer()
    
    # Extract data from payload
    scan_id = payload.get("scan_id")
    program_id = payload.get("program_id")
    
    # Parent span for entire pipeline
    with tracer.start_as_current_span(
        "scan_pipeline",
        attributes={
            "scan_id": str(scan_id),
            "program_id": str(program_id),
        }
    ) as pipeline_span:
        try:
            # Stage 0: Scope Filter
            with tracer.start_as_current_span("stage_0_scope_filter") as span:
                try:
                    scope_filter = ScopeFilter(payload.get("scope", {}))
                    span.set_attribute("scope_entries", len(scope_filter.in_scope))
                    span.set_status(trace.Status(trace.StatusCode.OK))
                except ScanError as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    pipeline_span.set_status(trace.Status(trace.StatusCode.ERROR))
                    raise
            
            # Stage 1: Asset Discovery
            with tracer.start_as_current_span("stage_1_asset_discovery") as span:
                try:
                    assets = await asset_discovery.run(payload)
                    span.set_attribute("assets_discovered", len(assets))
                    span.set_status(trace.Status(trace.StatusCode.OK))
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
            
            # Continue with other stages...
            # Each stage gets its own span
            
            # Set final pipeline status
            pipeline_span.set_attribute("status", "completed")
            
        except Exception as e:
            pipeline_span.set_status(
                trace.Status(trace.StatusCode.ERROR, str(e))
            )
            pipeline_span.record_exception(e)
            raise
```

#### 6. Docker Compose Jaeger Service

```yaml
# File: infra/docker-compose.yml (add to services)

services:
  jaeger:
    image: jaegertracing/all-in-one:1.52
    container_name: attackbot-jaeger
    ports:
      - "5775:5775/udp"   # Zipkin compatibility
      - "6831:6831/udp"   # Jaeger agent (compact thrift)
      - "6832:6832/udp"   # Jaeger agent (binary thrift)
      - "5778:5778"       # Serve configs
      - "16686:16686"     # Jaeger UI
      - "14268:14268"     # Direct span submission
      - "14250:14250"     # gRPC
      - "9411:9411"       # Zipkin compatibility
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - LOG_LEVEL=debug
    volumes:
      - jaeger_data:/tmp/jaeger
    networks:
      - attackbot-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:16686"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  jaeger_data:
    driver: local
```

#### 7. Configuration Updates

```python
# File: backend/services/core_engine/config.py

from pydantic import BaseSettings, Field

class EngineConfig(BaseSettings):
    # ... existing config ...
    
    # Tracing configuration
    jaeger_host: str = Field(default="jaeger", env="JAEGER_HOST")
    jaeger_port: int = Field(default=6831, env="JAEGER_PORT")
    tracing_enabled: bool = Field(default=True, env="TRACING_ENABLED")
    tracing_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0, env="TRACING_SAMPLE_RATE")
    tracing_console_export: bool = Field(default=False, env="TRACING_CONSOLE_EXPORT")


# Similarly for Reporter and Scraper configs
```

### Acceptance Criteria

- [ ] Jaeger all-in-one container running on port 16686
- [ ] All services emit spans to Jaeger
- [ ] Trace context propagated via MessageEnvelope (trace_id, span_id)
- [ ] HTTP calls between services show parent/child relationship
- [ ] Query Jaeger: Search for scan_id, see complete request flow
- [ ] Test: Start scan, verify trace visible in Jaeger
- [ ] Latency: Measure end-to-end scan time in Jaeger

### Rollback Strategy

**Rollback Time:** <5 minutes

```bash
# Revert tracing implementation
git checkout HEAD~1 -- backend/shared/tracing.py
git checkout HEAD~1 -- backend/shared/schemas/envelope.py
git checkout HEAD~1 -- backend/services/core_engine/main.py
git checkout HEAD~1 -- backend/services/core_engine/worker.py
git checkout HEAD~1 -- backend/services/reporter/main.py
git checkout HEAD~1 -- docker-compose.yml

# Revert requirements
git checkout HEAD~1 -- requirements.txt
```

### Testing Checklist

- [ ] Unit test: Trace context injection/extraction
- [ ] Unit test: Manual span creation
- [ ] Integration test: Multi-service span propagation
- [ ] E2E test: Full trace from scan start to report generation
- [ ] Manual test: Query Jaeger UI for sample traces

---

## Sprint Timeline

| Day | Engineer A | Engineer B | Key Activities |
|-----|------------|------------|----------------|
| 1 | Circuit breaker implementation | - | Library, service, metrics |
| 2 | Decorate HTTP clients | - | Scraper, Core Engine clients |
| 3 | Admin endpoints | Install OpenTelemetry packages | All services |
| 4 | Finalize circuit breaker | Tracing initialization module | Configuration |
| 5 | Testing | Message envelope + Jaeger deploy | Integration |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Jaeger deployment issues | Medium | Medium | Use Jaeger all-in-one Docker image, test in staging first |
| Circuit breaker opens too aggressively | Medium | Medium | Start with fail_max=10, tune based on metrics |
| Tracing impacts performance | Low | Medium | Sampling rate configurable (default 100%), async batch export |
| Trace context not propagated correctly | Medium | High | Test thoroughly with manual context injection |

---

## Rollback & Contingency Plans

### Per-Issue Rollback

| Issue | Rollback Strategy | Time to Rollback |
|-------|-------------------|------------------|
| #4 Circuit Breaker | Remove decorator, revert to direct HTTP calls | <10min |
| #5 Tracing | Disable OpenTelemetry instrumentation | <5min |

### Contingency
If Sprint 2 overruns, deliver **#4 (Circuit Breaker)** and defer **#5 (Tracing)** to Sprint 3. Circuit breaker provides immediate value for production reliability.

---

## Success Criteria

### Sprint 2
- [ ] Circuit breaker prevents >5 consecutive failures to any service
- [ ] All requests traceable in Jaeger
- [ ] Cross-service latency visible in Jaeger
- [ ] Service failure results in <1ms rejection (vs 30-60s timeout)

---

## Dependencies

### Internal
- Issue #4 (Circuit Breaker) is independent
- Issue #5 (Tracing) is independent but benefits from Issue #4 being in place

### External
- **Jaeger**: Requires Docker deployment
- **Prometheus**: For circuit breaker metrics (already in place from Sprint 1)
- **OpenTelemetry libraries**: New Python dependencies

---

## Integration Points

### Modified Files
1. `backend/shared/circuit_breaker.py` - **NEW** Circuit breaker service and decorators
2. `backend/shared/tracing.py` - **NEW** OpenTelemetry configuration
3. `backend/shared/schemas/envelope.py` - MODIFY: Add trace_id, span_id fields
4. `backend/services/core_engine/clients/scraper.py` - **NEW** Enhanced HTTP client with CB
5. `backend/services/reporter/clients/core_engine.py` - **NEW** Enhanced HTTP client with CB
6. `backend/services/core_engine/main.py` - MODIFY: Tracing init, CB admin endpoints
7. `backend/services/reporter/main.py` - MODIFY: Tracing initialization
8. `backend/services/core_engine/worker.py` - MODIFY: Tracing for Celery tasks
9. `backend/services/core_engine/config.py` - MODIFY: Tracing and CB config
10. `backend/services/reporter/config.py` - MODIFY: Tracing config
11. `docker-compose.yml` - MODIFY: Add Jaeger service
12. `requirements.txt` (all services) - MODIFY: Add OpenTelemetry and aiobreaker

### New Dependencies
- `aiobreaker==1.4.0` - Circuit breaker library
- `opentelemetry-api==1.23.0` - OpenTelemetry core
- `opentelemetry-sdk==1.23.0` - OpenTelemetry SDK
- `opentelemetry-instrumentation-fastapi==0.44b0` - FastAPI instrumentation
- `opentelemetry-instrumentation-httpx==0.44b0` - HTTPX instrumentation
- `opentelemetry-instrumentation-celery==0.44b0` - Celery instrumentation
- `opentelemetry-instrumentation-sqlalchemy==0.44b0` - SQLAlchemy instrumentation
- `opentelemetry-exporter-jaeger==1.23.0` - Jaeger exporter

---

## Health Check Updates

Add circuit breaker state to health check endpoint:

```python
# File: backend/services/core_engine/main.py

@app.get("/api/v1/health")
async def health_check():
    # ... existing health checks ...
    
    # Add circuit breaker status
    cb_states = ServiceCircuitBreakers.get_state_summary()
    open_breakers = [name for name, state in cb_states.items() if state == "open"]
    
    if open_breakers:
        health_status = "degraded"
        health_details["circuit_breakers"] = {
            "open": open_breakers,
            "status": "warning"
        }
    else:
        health_details["circuit_breakers"] = {
            "status": "healthy",
            "all_closed": True
        }
    
    # ... rest of health check ...
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-19 | Mistral Vibe | Initial implementation guide based on Issues#1.md, Issues#2.md, and Issue_Sprints.md |

---

**Generated by Mistral Vibe.**
**Co-Authored-By: Mistral Vibe <vibe@mistral.ai>**

---

**Next Sprint:** [Sprint #3: P1 - Architecture Modernization](../sprint#3.md)  
**Previous Sprint:** [Sprint #1: P0 - Data Integrity](../sprint#1.md)  
**Related Documents:**  
- [../Issue_Sprints.md](../Issue_Sprints.md) - Sprint planning overview  
- [../Issues#1.md](../Issues#1.md) - Detailed issue definitions  
- [../Issues#2.md](../Issues#2.md) - Detailed issue definitions
