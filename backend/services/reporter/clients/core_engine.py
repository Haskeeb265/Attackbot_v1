from __future__ import annotations

import os
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


# Minimal helper used by reporter-worker legacy fallback and tests.
_DEFAULT_BASE_URL = os.environ.get("CORE_ENGINE_API_URL", "http://core-engine:8002")
core_engine_client = CoreEngineClient(base_url=_DEFAULT_BASE_URL)


async def get_scan_data(scan_id: str) -> dict:
    """
    Legacy convenience wrapper for fetching scan + findings + evidence via HTTP.
    """
    scan = await core_engine_client.get_scan(scan_id)
    findings = await core_engine_client.get_findings(scan_id)
    evidence_by_finding: dict[str, list[dict]] = {}
    for f in findings:
        finding_id = str(f.get("finding_id") or "")
        if not finding_id:
            continue
        evidence_by_finding[finding_id] = await core_engine_client.get_finding_evidence(
            scan_id, finding_id
        )
    return {
        "scan": scan,
        "findings": findings,
        "evidence_by_finding": evidence_by_finding,
    }
