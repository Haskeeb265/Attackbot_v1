from __future__ import annotations

import httpx

from backend.shared.logging import get_logger

log = get_logger(__name__)


class AttackGraphClient:
    def __init__(self, base_url: str, timeout_seconds: int = 5) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def get_chain_detail(self, chain_id: str) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/api/v1/chains/{chain_id}")
            if response.status_code == 200:
                return response.json()
            log.debug(
                "attack_graph_chain_detail_unavailable",
                chain_id=chain_id,
                status_code=response.status_code,
            )
            return None
        except Exception as exc:
            log.debug(
                "attack_graph_chain_detail_request_failed",
                chain_id=chain_id,
                error=str(exc),
            )
            return None
