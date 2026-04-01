from __future__ import annotations

import httpx


class CoreEngineClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30, connect_timeout_seconds: int = 5) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout=timeout_seconds, connect=connect_timeout_seconds)

    async def get_scan(self, scan_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/api/v1/scans/{scan_id}")
        response.raise_for_status()
        return response.json()

    async def get_findings(self, scan_id: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/api/v1/scans/{scan_id}/findings")
        response.raise_for_status()
        payload = response.json()
        return payload.get("findings", [])

    async def get_finding_evidence(self, scan_id: str, finding_id: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/api/v1/scans/{scan_id}/findings/{finding_id}/evidence"
            )
        response.raise_for_status()
        payload = response.json()
        return payload.get("items", [])
