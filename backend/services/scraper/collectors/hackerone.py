"""
HackerOne platform collector.

Authentication: HTTP Basic Auth
  - api_username = username
  - api_token    = password
  - Requires Professional, Community, or Enterprise account

Rate limits:
  - 600 req/min (read)
  - 25 req/20s  (write)
  - 429 response includes Retry-After header

Key design decisions:
  - Uses /structured_scopes endpoint, NOT raw policy markdown
  - Structured scopes return pre-parsed asset_type + value fields
  - Skips individual program failures without aborting the full listing run
"""
import asyncio
from typing import Any, AsyncGenerator

import httpx

from shared.logging import get_logger
from shared.exceptions import (
    CollectorRateLimitError,
    CollectorAuthError,
    CollectorError,
)
from .base import BaseCollector, register
from .models import RawProgram, RawScopeEntry, RawPolicy

log = get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────────
H1_BASE_URL   = "https://api.hackerone.com"
H1_PAGE_SIZE  = 100

# Maps HackerOne asset_type strings → AttackBot canonical asset types
H1_ASSET_TYPE_MAP: dict[str, str] = {
    "URL":             "url",
    "WILDCARD":        "wildcard_domain",
    "DOMAIN":          "domain",
    "IP_ADDRESS":      "ip_range",
    "CIDR":            "ip_range",
    "ANDROID_APP_URL": "mobile_app",
    "IOS_APP_URL":     "mobile_app",
    "OTHER":           "api",
    "SOURCE_CODE":     "api",
    "HARDWARE":        "api",
}


@register("hackerone")
class HackerOneCollector(BaseCollector):
    """
    Fetches bug bounty programs from the HackerOne API v1.

    Docs: https://api.hackerone.com/customer-facing/
    """

    def __init__(
        self,
        api_username: str,
        api_token: str,
        page_size: int = H1_PAGE_SIZE,
        max_retries: int = 3,
    ) -> None:
        self._auth        = (api_username, api_token)
        self._page_size   = page_size
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    # ── HTTP primitives ────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                auth=self._auth,
                headers={"Accept": "application/json"},
                timeout=30.0,
            )
        return self._client

    async def _get_with_retry(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        GET request with automatic 429 back-off.

        Raises:
            CollectorAuthError      — on 401 or 403 (no retry)
            CollectorRateLimitError — if all retries are exhausted
            CollectorError          — on 404
        """
        client = await self._get_client()

        for attempt in range(self._max_retries):
            try:
                resp = await client.get(url, params=params)
            except httpx.RequestError as exc:
                wait = 5 * (attempt + 1)
                log.warning("h1_request_error", url=url, attempt=attempt,
                            error=str(exc), wait=wait)
                await asyncio.sleep(wait)
                continue

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                log.warning("h1_rate_limited", retry_after=retry_after,
                            attempt=attempt, url=url)
                await asyncio.sleep(retry_after)
                continue

            if resp.status_code in (401, 403):
                raise CollectorAuthError(
                    f"HackerOne authentication failed (HTTP {resp.status_code}). "
                    "Check api_username and api_token in Vault."
                )

            if resp.status_code == 404:
                raise CollectorError(f"HackerOne resource not found: {url}")

            resp.raise_for_status()
            return resp.json()

        raise CollectorRateLimitError(
            f"HackerOne rate limited after {self._max_retries} retries on {url}"
        )

    async def _paginate(
        self,
        url: str,
        extra_params: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Generic paginator using page[number] + page[size] parameters.
        Stops when the API returns an empty data array.
        """
        page = 1
        while True:
            params: dict[str, Any] = {
                "page[number]": page,
                "page[size]":   self._page_size,
            }
            if extra_params:
                params.update(extra_params)

            data  = await self._get_with_retry(url, params=params)
            items = data.get("data", [])

            if not items:
                break

            for item in items:
                yield item

            log.info("h1_page_fetched", url=url, page=page, count=len(items))
            page += 1

    # ── Public collector interface ─────────────────────────────────

    async def fetch_listing(self) -> list[RawProgram]:
        """
        Fetch all programs accessible to the authenticated user.
        Per-program failures are logged and skipped — does not abort the run.
        """
        url      = f"{H1_BASE_URL}/v1/hackers/programs"
        programs: list[RawProgram] = []

        async for item in self._paginate(url):
            handle = item.get("attributes", {}).get("handle", "")
            if not handle:
                log.warning("h1_program_missing_handle", item_id=item.get("id"))
                continue

            try:
                raw = await self.fetch_details(handle)
                programs.append(raw)
                log.info("h1_program_fetched", handle=handle)
            except CollectorError as exc:
                log.warning("h1_program_fetch_failed", handle=handle, error=str(exc))

        log.info("h1_listing_complete", total=len(programs))
        return programs

    async def fetch_details(self, handle: str) -> RawProgram:
        """
        Fetch full program detail and structured scopes for one program.

        CRITICAL: uses /structured_scopes endpoint, not raw policy markdown.
        structured_scopes returns pre-parsed asset_type + value fields that
        map directly to program_scopes without a markdown parser.
        """
        # ── Program detail ─────────────────────────────────────────
        detail_url  = f"{H1_BASE_URL}/v1/hackers/programs/{handle}"
        detail_data = await self._get_with_retry(detail_url)
        attrs       = detail_data.get("data", {}).get("attributes", {})

        # ── Structured scopes ──────────────────────────────────────
        scopes_url    = f"{H1_BASE_URL}/v1/hackers/programs/{handle}/structured_scopes"
        scope_entries: list[RawScopeEntry] = []

        async for scope_item in self._paginate(scopes_url):
            scope_attrs    = scope_item.get("attributes", {})
            asset_type_raw = scope_attrs.get("asset_type", "OTHER")
            canonical_type = H1_ASSET_TYPE_MAP.get(asset_type_raw, "api")

            # H1: eligible_for_bounty=True → in_scope, False → out_of_scope
            eligible   = scope_attrs.get("eligible_for_bounty", True)
            scope_type = "in_scope" if eligible else "out_of_scope"

            value = scope_attrs.get("asset_identifier", "").strip()
            if not value:
                continue

            scope_entries.append(RawScopeEntry(
                asset_type = canonical_type,
                value      = value,
                scope_type = scope_type,
                notes      = scope_attrs.get("instruction", ""),
            ))

        # ── Policy ─────────────────────────────────────────────────
        policy = RawPolicy(
            disclosure_policy    = attrs.get("policy", ""),
            testing_restrictions = (
                attrs.get("testing_instructions", "").splitlines()
                if attrs.get("testing_instructions")
                else []
            ),
            safe_harbor = attrs.get("safe_harbor") == "safe_harbor",
        )

        # ── Determine bounty type ──────────────────────────────────
        if attrs.get("offers_bounties"):
            bounty_type = "paid"
        elif attrs.get("offers_swag"):
            bounty_type = "swag"
        else:
            bounty_type = "rep_only"

        # ── Extract max bounty ─────────────────────────────────────
        max_bounty: int | None = None
        bounty_table = attrs.get("maximum_bounty_table", {})
        if bounty_table and isinstance(bounty_table, dict):
            max_bounty = bounty_table.get("value")

        return RawProgram(
            platform    = "hackerone",
            handle      = handle,
            name        = attrs.get("name", handle),
            url         = f"https://hackerone.com/{handle}",
            bounty_type = bounty_type,
            max_bounty  = max_bounty,
            is_active   = attrs.get("state") == "public_mode",
            raw_policy  = detail_data.get("data", {}),
            scopes      = scope_entries,
            policy      = policy,
        )

    def normalize(self, raw: RawProgram) -> dict[str, Any]:
        """
        Map a RawProgram to a dict matching the programs table schema.
        Intentionally excludes queued_for_scan — that is managed by upsert logic only.
        """
        return {
            "platform":    raw.platform,
            "handle":      raw.handle,
            "name":        raw.name,
            "url":         raw.url,
            "bounty_type": raw.bounty_type,
            "max_bounty":  raw.max_bounty,
            "is_active":   raw.is_active,
            "raw_policy":  raw.raw_policy,
        }

    async def close(self) -> None:
        """Close the underlying httpx client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
