from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Awaitable

from fastapi import Request, HTTPException, status
from prometheus_client import Gauge


rate_limit_hits = Gauge(
    "api_rate_limit_hits_total",
    "Total rate limit violations",
    ["endpoint", "ip_address"],
)

active_requests = Gauge(
    "api_active_requests",
    "Current number of active requests",
    ["endpoint", "ip_address"],
)


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    """Simple token-bucket rate limiter (in-memory)."""

    def __init__(self, requests_per_minute: int, burst: int = 5):
        self.requests = int(requests_per_minute)
        self.burst = int(burst)
        self.tokens_per_second = self.requests / 60.0
        self.buckets = defaultdict(lambda: {"tokens": float(self.burst), "last_refill": time.time()})

    def consume(self, identifier: str) -> bool:
        bucket = self.buckets[identifier]
        now = time.time()
        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(float(self.burst), bucket["tokens"] + elapsed * self.tokens_per_second)
        bucket["last_refill"] = now
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            return True
        return False

    def get_retry_after(self, identifier: str) -> float:
        bucket = self.buckets.get(identifier)
        if not bucket:
            return 0.0
        if bucket["tokens"] >= 1.0:
            return 0.0
        tokens_needed = 1.0 - float(bucket["tokens"])
        if self.tokens_per_second <= 0:
            return 60.0
        return tokens_needed / self.tokens_per_second


DEFAULT_LIMITS: dict[str, RateLimiter] = {
    "default": RateLimiter(100),
    "/api/v1/scans/start": RateLimiter(10),
    "/api/v1/reports/generate": RateLimiter(20),
    # Used by verification tests
    "/test-rate-limit": RateLimiter(2, burst=2),
}


class rate_limit_middleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        path = request.url.path
        client_ip = (request.client.host if request.client else "unknown") or "unknown"

        # normalize path: use exact configured prefix match
        configured = None
        for key in DEFAULT_LIMITS.keys():
            if key != "default" and path.startswith(key):
                configured = key
                break
        endpoint_key = configured or "default"
        limiter = DEFAULT_LIMITS.get(endpoint_key, DEFAULT_LIMITS["default"])
        identifier = f"{endpoint_key}:{client_ip}"

        active_requests.labels(endpoint=endpoint_key, ip_address=client_ip).inc()
        try:
            if not limiter.consume(identifier):
                retry_after = limiter.get_retry_after(identifier)
                rate_limit_hits.labels(endpoint=endpoint_key, ip_address=client_ip).inc()
                headers = [(b"retry-after", str(int(retry_after)).encode())]
                exc = HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"error": "Rate limit exceeded", "retry_after": retry_after},
                    headers={"Retry-After": str(int(retry_after))},
                )
                # Starlette will translate HTTPException when raised inside routing,
                # but we are in ASGI middleware; emit response directly.
                from starlette.responses import JSONResponse

                response = JSONResponse(
                    status_code=exc.status_code,
                    content=exc.detail,
                    headers=exc.headers,
                )
                await response(scope, receive, send)
                return
            await self.app(scope, receive, send)
        finally:
            active_requests.labels(endpoint=endpoint_key, ip_address=client_ip).dec()

