from __future__ import annotations

import httpx


class ScraperClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30, connect_timeout_seconds: int = 5) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout=timeout_seconds, connect=connect_timeout_seconds)

    async def get_program(self, program_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/api/v1/programs/{program_id}")
        response.raise_for_status()
        return response.json()

    async def get_scope(self, program_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/api/v1/programs/{program_id}/scope")
        response.raise_for_status()
        return response.json()
