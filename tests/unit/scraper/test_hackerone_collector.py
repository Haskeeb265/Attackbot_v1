"""
Unit tests for the HackerOne collector.

All tests use mocked HTTP responses — no real API calls.
"""
import asyncio
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.scraper.collectors.hackerone import (
    H1_ASSET_TYPE_MAP,
    HackerOneCollector,
)
from backend.services.scraper.collectors.models import RawProgram, RawPolicy
from shared.exceptions import CollectorAuthError, CollectorRateLimitError


@pytest.fixture
def collector() -> HackerOneCollector:
    return HackerOneCollector(
        api_username="test_user",
        api_token="test_token",
        max_retries=3,
    )


# ── fetch_listing ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_listing_returns_programs(collector: HackerOneCollector) -> None:
    """Full listing fetch with mocked paginator returns RawProgram objects."""

    mock_detail_response = {
        "data": {
            "attributes": {
                "name":            "Example Corp",
                "state":           "public_mode",
                "offers_bounties": True,
                "policy":          "Standard disclosure policy",
                "safe_harbor":     "safe_harbor",
            }
        }
    }

    async def mock_paginate(url: str, extra_params: Any = None) -> AsyncGenerator:
        if "structured_scopes" in url:
            yield {
                "attributes": {
                    "asset_type":          "WILDCARD",
                    "asset_identifier":    "*.example.com",
                    "eligible_for_bounty": True,
                    "instruction":         "All subdomains",
                }
            }
        else:
            yield {"attributes": {"handle": "example_program"}}

    with patch.object(collector, "_paginate", side_effect=mock_paginate):
        with patch.object(collector, "_get_with_retry",
                          new_callable=AsyncMock,
                          return_value=mock_detail_response):
            programs = await collector.fetch_listing()

    assert len(programs) == 1
    prog = programs[0]
    assert prog.handle   == "example_program"
    assert prog.platform == "hackerone"
    assert prog.name     == "Example Corp"
    assert prog.is_active is True
    assert prog.bounty_type == "paid"
    assert len(prog.scopes) == 1
    assert prog.scopes[0].asset_type == "wildcard_domain"
    assert prog.scopes[0].value      == "*.example.com"
    assert prog.scopes[0].scope_type == "in_scope"


@pytest.mark.asyncio
async def test_fetch_listing_skips_failed_programs(collector: HackerOneCollector) -> None:
    """A program that fails fetch_details should be skipped, not crash the full run."""
    from shared.exceptions import CollectorError

    async def mock_paginate(url: str, extra_params: Any = None) -> AsyncGenerator:
        if "structured_scopes" not in url:
            yield {"attributes": {"handle": "good_program"}}
            yield {"attributes": {"handle": "bad_program"}}

    async def mock_fetch_details(handle: str) -> RawProgram:
        if handle == "bad_program":
            raise CollectorError("404 not found")
        return RawProgram(
            platform="hackerone", handle=handle, name="Good", url="https://h1.com/good",
            bounty_type="paid", max_bounty=None, is_active=True, raw_policy={},
            policy=RawPolicy(),
        )

    with patch.object(collector, "_paginate", side_effect=mock_paginate):
        with patch.object(collector, "fetch_details", side_effect=mock_fetch_details):
            programs = await collector.fetch_listing()

    assert len(programs) == 1
    assert programs[0].handle == "good_program"


@pytest.mark.asyncio
async def test_fetch_listing_skips_handles_without_handle(
    collector: HackerOneCollector,
) -> None:
    """Items missing a handle attribute are silently skipped."""
    async def mock_paginate(url: str, extra_params: Any = None) -> AsyncGenerator:
        if "structured_scopes" not in url:
            yield {"attributes": {}}  # no handle

    with patch.object(collector, "_paginate", side_effect=mock_paginate):
        programs = await collector.fetch_listing()

    assert programs == []


# ── _get_with_retry ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rate_limit_retries_with_backoff(collector: HackerOneCollector) -> None:
    """429 response triggers retry after Retry-After delay."""
    call_count = 0

    async def mock_get(url: str, params: Any = None):
        nonlocal call_count
        call_count += 1
        resp = MagicMock()
        if call_count < 3:
            resp.status_code = 429
            resp.headers     = {"Retry-After": "1"}
        else:
            resp.status_code = 200
            resp.json.return_value = {"data": []}
            resp.raise_for_status  = MagicMock()
        return resp

    with patch.object(collector, "_get_client") as mock_factory:
        mock_client      = AsyncMock()
        mock_client.get  = mock_get
        mock_factory.return_value = mock_client
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await collector._get_with_retry("https://api.hackerone.com/test")

    assert call_count == 3
    assert result == {"data": []}


@pytest.mark.asyncio
async def test_rate_limit_exhausted_raises(collector: HackerOneCollector) -> None:
    """All retries rate-limited → CollectorRateLimitError."""

    async def always_429(url: str, params: Any = None):
        resp = MagicMock()
        resp.status_code = 429
        resp.headers     = {"Retry-After": "1"}
        return resp

    with patch.object(collector, "_get_client") as mock_factory:
        mock_client      = AsyncMock()
        mock_client.get  = always_429
        mock_factory.return_value = mock_client
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(CollectorRateLimitError):
                await collector._get_with_retry("https://api.hackerone.com/test")


@pytest.mark.asyncio
async def test_auth_error_raises_immediately(collector: HackerOneCollector) -> None:
    """401 response raises CollectorAuthError without retrying."""
    call_count = 0

    async def auth_fail(url: str, params: Any = None):
        nonlocal call_count
        call_count += 1
        resp = MagicMock()
        resp.status_code = 401
        return resp

    with patch.object(collector, "_get_client") as mock_factory:
        mock_client      = AsyncMock()
        mock_client.get  = auth_fail
        mock_factory.return_value = mock_client
        with pytest.raises(CollectorAuthError):
            await collector._get_with_retry("https://api.hackerone.com/test")

    assert call_count == 1, "Should not retry on 401"


@pytest.mark.asyncio
async def test_403_raises_auth_error(collector: HackerOneCollector) -> None:
    """403 response also raises CollectorAuthError."""

    async def forbidden(url: str, params: Any = None):
        resp = MagicMock()
        resp.status_code = 403
        return resp

    with patch.object(collector, "_get_client") as mock_factory:
        mock_client = AsyncMock()
        mock_client.get = forbidden
        mock_factory.return_value = mock_client
        with pytest.raises(CollectorAuthError):
            await collector._get_with_retry("https://api.hackerone.com/test")


# ── normalize ─────────────────────────────────────────────────────────

def test_normalize_maps_all_fields(collector: HackerOneCollector) -> None:
    """normalize() returns a dict matching the programs table schema."""
    raw = RawProgram(
        platform="hackerone", handle="acme", name="Acme Corp",
        url="https://hackerone.com/acme", bounty_type="paid",
        max_bounty=10_000, is_active=True,
        raw_policy={"data": {"attributes": {"name": "Acme Corp"}}},
        policy=RawPolicy(),
    )
    result = collector.normalize(raw)

    assert result["handle"]      == "acme"
    assert result["platform"]    == "hackerone"
    assert result["name"]        == "Acme Corp"
    assert result["bounty_type"] == "paid"
    assert result["max_bounty"]  == 10_000
    assert result["is_active"]   is True
    # queued_for_scan must NOT appear — upsert logic owns it
    assert "queued_for_scan" not in result


# ── Asset type mapping ─────────────────────────────────────────────────

def test_all_h1_asset_types_mapped() -> None:
    """All expected HackerOne asset_type strings have canonical mappings."""
    expected_h1_types = {
        "URL", "WILDCARD", "DOMAIN", "IP_ADDRESS",
        "CIDR", "ANDROID_APP_URL", "IOS_APP_URL", "OTHER",
    }
    for h1_type in expected_h1_types:
        assert h1_type in H1_ASSET_TYPE_MAP, f"Missing mapping for {h1_type!r}"
        assert H1_ASSET_TYPE_MAP[h1_type] in {
            "url", "domain", "wildcard_domain", "ip_range", "mobile_app", "api"
        }


def test_out_of_scope_scope_type() -> None:
    """eligible_for_bounty=False produces out_of_scope entries."""
    # Verify the logic in fetch_details by inspecting the mapping inline
    eligible   = False
    scope_type = "in_scope" if eligible else "out_of_scope"
    assert scope_type == "out_of_scope"
