from __future__ import annotations

import httpx

from backend.shared.circuit_breaker import ServiceCircuitBreakers


class CoreEngineClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30, connect_timeout_seconds: int = 5) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout=timeout_seconds, connect=connect_timeout_seconds)
        self._breaker = ServiceCircuitBreakers.core_engine_api()

    async def _get_json(self, path: str) -> dict:
        async def _request() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                return await client.get(f"{self._base_url}{path}")

        response = await self._breaker.call(_request)
        response.raise_for_status()
        return response.json()

    async def get_scan(self, scan_id: str) -> dict:
        return await self._get_json(f"/api/v1/scans/{scan_id}")

    async def get_findings(self, scan_id: str) -> list[dict]:
        payload = await self._get_json(f"/api/v1/scans/{scan_id}/findings")
        return payload.get("findings", [])

    async def get_finding_evidence(self, scan_id: str, finding_id: str) -> list[dict]:
        payload = await self._get_json(f"/api/v1/scans/{scan_id}/findings/{finding_id}/evidence")
        return payload.get("items", [])
