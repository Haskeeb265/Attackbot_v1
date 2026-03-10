"""
Integration test: full scrape pipeline against mocked HackerOne API.

These tests require a real Postgres instance and RabbitMQ instance.
They are skipped automatically if the required environment variables
are not set — CI can opt in by setting the ATTACKBOT_INTEGRATION env var.

Run with:
    ATTACKBOT_INTEGRATION=1 pytest tests/integration/ -v

The tests use mocked HackerOne API responses (no real API calls),
but use real Postgres + RabbitMQ to test the full data path.
"""
import json
import os
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

INTEGRATION = os.getenv("ATTACKBOT_INTEGRATION", "").strip() == "1"
pytestmark   = pytest.mark.skipif(
    not INTEGRATION,
    reason="Set ATTACKBOT_INTEGRATION=1 to run integration tests",
)


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot",
    )


@pytest.fixture(scope="module")
def rabbitmq_url() -> str:
    return os.getenv("RABBITMQ_URL", "amqp://attackbot:attackbot@localhost:5672/")


@pytest.fixture(scope="module")
def redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


# ── Mock HackerOne data ────────────────────────────────────────────────

MOCK_H1_PROGRAM = {
    "data": {
        "attributes": {
            "name":            "Integration Test Corp",
            "state":           "public_mode",
            "offers_bounties": True,
            "policy":          "Standard disclosure.",
            "safe_harbor":     "safe_harbor",
        }
    }
}

MOCK_H1_SCOPE = [
    {
        "attributes": {
            "asset_type":          "WILDCARD",
            "asset_identifier":    "*.integrationtest.com",
            "eligible_for_bounty": True,
            "instruction":         "All subdomains in scope",
        }
    },
    {
        "attributes": {
            "asset_type":          "URL",
            "asset_identifier":    "https://api.integrationtest.com",
            "eligible_for_bounty": True,
            "instruction":         "",
        }
    },
    {
        "attributes": {
            "asset_type":          "DOMAIN",
            "asset_identifier":    "admin.integrationtest.com",
            "eligible_for_bounty": False,
            "instruction":         "Do not test admin",
        }
    },
]


# ── Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_scrape_produces_db_rows(db_url: str, rabbitmq_url: str) -> None:
    """
    Mocked HackerOne → upsert to Postgres → verify rows in programs + program_scopes.
    """
    from backend.services.scraper.collectors.hackerone import HackerOneCollector
    from backend.services.scraper.repository import ProgramRepository
    from shared.db import init_db

    init_db(db_url)

    collector = HackerOneCollector(api_username="test", api_token="test")

    async def mock_paginate(url: str, extra_params: Any = None) -> AsyncGenerator:
        if "structured_scopes" in url:
            for scope in MOCK_H1_SCOPE:
                yield scope
        else:
            yield {"attributes": {"handle": "integration_test_corp"}}

    with patch.object(collector, "_paginate", side_effect=mock_paginate):
        with patch.object(collector, "_get_with_retry",
                          new_callable=AsyncMock,
                          return_value=MOCK_H1_PROGRAM):
            programs = await collector.fetch_listing()

    assert len(programs) == 1
    raw        = programs[0]
    normalized = collector.normalize(raw)

    repo              = ProgramRepository()
    program_id, created = await repo.upsert(raw, normalized)

    assert isinstance(program_id, UUID)
    # created or updated — both are valid if run multiple times
    assert program_id is not None

    # Verify scopes were written
    full_program = await repo.get_program_with_scopes(program_id)
    assert full_program is not None
    assert full_program.handle == "integration_test_corp"

    # 2 in_scope + 1 out_of_scope = 3 total
    assert len(full_program.scopes) == 3

    in_scope  = [s for s in full_program.scopes if s.scope_type == "in_scope"]
    out_scope = [s for s in full_program.scopes if s.scope_type == "out_of_scope"]
    assert len(in_scope)  == 2
    assert len(out_scope) == 1


@pytest.mark.asyncio
async def test_publish_to_rabbitmq_succeeds(rabbitmq_url: str, db_url: str) -> None:
    """
    After upsert, publishing scan.jobs message to RabbitMQ succeeds.
    """
    from backend.services.scraper.collectors.hackerone import HackerOneCollector
    from backend.services.scraper.repository import ProgramRepository
    from backend.services.scraper.publisher import ScanJobPublisher
    from shared.db import init_db
    from shared.queue import QueuePublisher

    init_db(db_url)

    collector = HackerOneCollector(api_username="test", api_token="test")

    async def mock_paginate(url: str, extra_params: Any = None) -> AsyncGenerator:
        if "structured_scopes" in url:
            for scope in MOCK_H1_SCOPE:
                yield scope
        else:
            yield {"attributes": {"handle": "integration_publish_test"}}

    with patch.object(collector, "_paginate", side_effect=mock_paginate):
        with patch.object(collector, "_get_with_retry",
                          new_callable=AsyncMock,
                          return_value=MOCK_H1_PROGRAM):
            programs = await collector.fetch_listing()

    raw        = programs[0]
    raw.handle = "integration_publish_test"
    normalized = collector.normalize(raw)
    normalized["handle"] = "integration_publish_test"

    repo              = ProgramRepository()
    program_id, _     = await repo.upsert(raw, normalized)
    full_program      = await repo.get_program_with_scopes(program_id)

    assert full_program is not None
    assert len([s for s in full_program.scopes if s.scope_type == "in_scope"]) > 0

    queue_publisher = QueuePublisher(rabbitmq_url)
    await queue_publisher.connect()

    scan_publisher = ScanJobPublisher(queue_publisher)
    success = await scan_publisher.publish_scan_job(
        program = full_program,
        scopes  = list(full_program.scopes),
    )

    await queue_publisher.close()

    assert success is True

    # After successful publish, flag should be False
    refreshed = await repo.get_program_with_scopes(program_id)
    assert refreshed is not None
    assert refreshed.queued_for_scan is False


@pytest.mark.asyncio
async def test_publish_failure_sets_queued_for_scan(db_url: str) -> None:
    """
    When publish fails, queued_for_scan is set to True on the program row.
    """
    from backend.services.scraper.collectors.hackerone import HackerOneCollector
    from backend.services.scraper.repository import ProgramRepository
    from backend.services.scraper.publisher import ScanJobPublisher
    from shared.db import init_db
    from shared.queue import QueuePublisher

    init_db(db_url)

    # Use a bad RabbitMQ URL to force publish failure
    bad_queue = QueuePublisher("amqp://invalid:invalid@localhost:9999/")

    # Mock connect to succeed but publish to fail
    bad_queue._channel = None
    with patch.object(bad_queue, "connect", new_callable=AsyncMock):
        with patch.object(bad_queue, "publish", new_callable=AsyncMock, return_value=False):
            scan_publisher = ScanJobPublisher(bad_queue)

            collector  = HackerOneCollector(api_username="test", api_token="test")
            handle     = "integration_failure_test"
            raw        = __import__(
                "backend.services.scraper.collectors.models",
                fromlist=["RawProgram", "RawPolicy"]
            ).RawProgram(
                platform    = "hackerone",
                handle      = handle,
                name        = "Failure Test",
                url         = f"https://hackerone.com/{handle}",
                bounty_type = "paid",
                max_bounty  = None,
                is_active   = True,
                raw_policy  = {},
                policy      = __import__(
                    "backend.services.scraper.collectors.models",
                    fromlist=["RawPolicy"]
                ).RawPolicy(),
                scopes = [
                    __import__(
                        "backend.services.scraper.collectors.models",
                        fromlist=["RawScopeEntry"]
                    ).RawScopeEntry(
                        asset_type = "wildcard_domain",
                        value      = "*.failuretest.com",
                        scope_type = "in_scope",
                    )
                ],
            )
            normalized = collector.normalize(raw)
            normalized["handle"] = handle

            repo         = ProgramRepository()
            program_id, _ = await repo.upsert(raw, normalized)
            # Reset the flag to False first to test the failure path
            await repo.set_queued_for_scan(program_id, queued=False)

            full_program = await repo.get_program_with_scopes(program_id)
            success      = await scan_publisher.publish_scan_job(
                program = full_program,
                scopes  = list(full_program.scopes),
            )

    assert success is False
    flagged = await repo.get_program_with_scopes(program_id)
    assert flagged.queued_for_scan is True


@pytest.mark.asyncio
async def test_upsert_does_not_reset_queued_for_scan_flag(db_url: str) -> None:
    """
    A second upsert call must not reset queued_for_scan=True to False.
    This is the core data-integrity invariant.
    """
    from backend.services.scraper.collectors.hackerone import HackerOneCollector
    from backend.services.scraper.collectors.models import (
        RawProgram, RawPolicy, RawScopeEntry
    )
    from backend.services.scraper.repository import ProgramRepository
    from shared.db import init_db

    init_db(db_url)

    handle     = "integration_flag_invariant_test"
    collector  = HackerOneCollector(api_username="test", api_token="test")
    raw        = RawProgram(
        platform="hackerone", handle=handle, name="Flag Test",
        url=f"https://hackerone.com/{handle}", bounty_type="paid",
        max_bounty=None, is_active=True, raw_policy={}, policy=RawPolicy(),
        scopes=[RawScopeEntry("wildcard_domain", "*.flagtest.com", "in_scope")],
    )
    normalized = collector.normalize(raw)
    normalized["handle"] = handle

    repo = ProgramRepository()

    # First upsert — creates the row
    program_id, _ = await repo.upsert(raw, normalized)

    # Manually set the flag to True (simulating a failed publish)
    await repo.set_queued_for_scan(program_id, queued=True)

    # Second upsert (rescrape) — must NOT touch the flag
    await repo.upsert(raw, normalized)

    program = await repo.get_program_with_scopes(program_id)
    assert program.queued_for_scan is True, (
        "queued_for_scan was reset to False by a rescrape upsert. "
        "This violates the invariant — only the reconciler may clear this flag."
    )
