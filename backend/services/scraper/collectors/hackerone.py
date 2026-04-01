"""
HackerOne collector — API v1.

Authentication: HTTP Basic Auth (API_USERNAME + API_TOKEN)
Rate limit: 600 req/min on read endpoints.
Scopes: always uses /structured_scopes (pre-parsed asset_type + value).

The collector is intentionally synchronous (uses `requests`).
It must always be invoked via loop.run_in_executor() — never called directly
from an async context, as it will block the event loop.
"""

import time
import requests
from datetime import datetime, timezone

from backend.shared.exceptions import CollectorRateLimitError, CollectorAuthError
from backend.shared.logging import get_logger
from backend.services.scraper.models import RawProgram, Program, ProgramScope, ProgramPolicy
from backend.services.scraper.collectors.base import BaseCollector, CollectorRegistry

log = get_logger(__name__)

H1_BASE_URL = "https://api.hackerone.com/v1"

# HackerOne structured_scopes asset_type → our canonical asset_type
ASSET_TYPE_MAP = {
    "URL": "url",
    "WILDCARD": "wildcard_domain",
    "DOMAIN": "domain",
    "IP_ADDRESS": "ip_range",
    "CIDR": "ip_range",
    "ANDROID": "mobile_app",
    "IOS": "mobile_app",
    "OTHER_IPA": "mobile_app",
    "OTHER_APK": "mobile_app",
    "API": "api",
    "SOURCE_CODE": "api",       # treat source code repos as api-adjacent
    "HARDWARE": "api",          # out-of-scope in practice, still needs a type
    "OTHER": "url",             # fallback
}


class HackerOneCollector(BaseCollector):

    def __init__(
        self,
        api_username: str,
        api_token: str,
        max_retries: int = 3,
        page_size: int = 100,
    ):
        self.auth = (api_username, api_token)
        self.max_retries = max_retries
        self.page_size = page_size
        self.headers = {"Accept": "application/json"}

    # ------------------------------------------------------------------
    # Internal HTTP helper
    # ------------------------------------------------------------------

    def _get(self, url: str, params: dict | None = None) -> dict:
        """
        GET with automatic 429 retry.

        Raises CollectorRateLimitError after exhausting max_retries.
        Raises CollectorAuthError on 401/403.
        Raises requests.HTTPError on other 4xx/5xx.
        """
        for attempt in range(self.max_retries):
            try:
                resp = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
            except requests.RequestException as e:
                log.warning("h1_request_failed", url=url, attempt=attempt, error=str(e))
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(5)
                continue

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                log.warning("h1_rate_limited", retry_after=retry_after, attempt=attempt)
                if attempt == self.max_retries - 1:
                    raise CollectorRateLimitError(
                        f"HackerOne rate limited after {self.max_retries} retries"
                    )
                time.sleep(retry_after)
                continue

            if resp.status_code in (401, 403):
                raise CollectorAuthError(
                    f"HackerOne auth failed: {resp.status_code}. "
                    "Check HACKERONE_API_USERNAME and HACKERONE_API_TOKEN."
                )

            resp.raise_for_status()
            return resp.json()

        # Should not reach here — loop always returns or raises
        raise CollectorRateLimitError("Exhausted retries without success")

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    def _paginate(self, url: str, extra_params: dict | None = None) -> list[dict]:
        """Fetch all pages from a paginated HackerOne endpoint. Returns flat list."""
        results = []
        page = 1
        while True:
            params: dict = {"page[number]": page, "page[size]": self.page_size}
            if extra_params:
                params.update(extra_params)

            data = self._get(url, params=params)
            # HackerOne `data` field can be None on edge cases — use `or []`
            page_data = data.get("data") or []
            if not page_data:
                break

            results.extend(page_data)
            log.debug("h1_page_fetched", url=url, page=page, count=len(page_data))
            page += 1

        return results

    # ------------------------------------------------------------------
    # BaseCollector interface
    # ------------------------------------------------------------------

    def fetch_listing(self) -> list[RawProgram]:
        """Fetch all accessible programs. Returns one RawProgram per item."""
        fetched_at = datetime.now(timezone.utc).isoformat()
        raw_list = self._paginate(f"{H1_BASE_URL}/hackers/programs")

        return [
            RawProgram(
                platform="hackerone",
                raw_data=item,
                handle=item["attributes"]["handle"],
                fetched_at=fetched_at,
            )
            for item in raw_list
        ]

    def fetch_details(self, handle: str) -> RawProgram:
        """Fetch full detail + structured scopes for one program."""
        fetched_at = datetime.now(timezone.utc).isoformat()

        detail = self._get(f"{H1_BASE_URL}/hackers/programs/{handle}")
        scopes = self._paginate(
            f"{H1_BASE_URL}/hackers/programs/{handle}/structured_scopes"
        )

        # Attach scopes to the raw detail for normalization
        detail["_scopes"] = scopes

        return RawProgram(
            platform="hackerone",
            raw_data=detail,
            handle=handle,
            fetched_at=fetched_at,
        )

    def normalize(self, raw: RawProgram) -> Program:
        """
        Map raw HackerOne API response to canonical Program.
        Never raises — returns best-effort on partial data.
        """
        # Handle both listing shape {attributes: ...} and detail shape {data: {attributes: ...}}
        attrs = raw.raw_data.get("data", raw.raw_data).get("attributes", {})
        scopes_raw = raw.raw_data.get("_scopes") or []

        # Parse scopes
        scopes: list[ProgramScope] = []
        for scope_item in scopes_raw:
            s_attrs = scope_item.get("attributes", {})
            eligible_submission = s_attrs.get("eligible_for_submission", True)
            asset_identifier = s_attrs.get("asset_identifier", "")
            asset_type_raw = s_attrs.get("asset_type", "OTHER")

            # in_scope: eligible for submission; out_of_scope: explicitly excluded
            scope_type = "in_scope" if eligible_submission else "out_of_scope"
            asset_type = ASSET_TYPE_MAP.get(asset_type_raw, "url")

            if not asset_identifier:
                continue  # skip blank scope entries

            scopes.append(ProgramScope(
                scope_type=scope_type,
                asset_type=asset_type,
                value=asset_identifier,
                notes=s_attrs.get("instruction") or None,
            ))

        # Parse policy
        policy = ProgramPolicy(
            disclosure_policy=attrs.get("disclosure_policy"),
            testing_restrictions=[],
            safe_harbor=attrs.get("safe_harbor") == "yes",
        )

        # bounty_type: if offers_bounties is True it's bug_bounty, else VDP
        bounty_type = "bug_bounty" if attrs.get("offers_bounties") else "vdp"

        return Program(
            platform="hackerone",
            handle=raw.handle,
            name=attrs.get("name", raw.handle),
            url=attrs.get("url") or f"https://hackerone.com/{raw.handle}",
            bounty_type=bounty_type,
            max_bounty=attrs.get("maximum_bounty"),
            is_active=not attrs.get("ended", False),
            raw_policy={"source": "hackerone", "attributes": attrs},
            scopes=scopes,
            policy=policy,
        )


# Self-register on import
CollectorRegistry.register("hackerone", HackerOneCollector)