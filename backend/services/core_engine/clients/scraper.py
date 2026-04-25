from __future__ import annotations

import httpx


async def get_data(base_url: str, path: str, timeout_seconds: int = 10) -> dict:
    """
    Tiny scraper API helper used by circuit-breaker integration tests.
    """
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds) as client:
        response = await client.get(path)
    response.raise_for_status()
    return response.json()
