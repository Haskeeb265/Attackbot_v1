from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from backend.services.scraper import main
from backend.services.scraper.models import Program, ProgramScope, RawProgram


class _DummyLock:
    async def acquire(self, blocking: bool = False) -> bool:
        return True

    async def release(self) -> None:
        return None


class _DummyRedis:
    def lock(self, key: str, timeout: int) -> _DummyLock:
        return _DummyLock()


class _DummyCollector:
    def __init__(self, **kwargs):
        pass

    def fetch_listing(self):
        return [RawProgram("hackerone", {"handle": "demo"}, "demo", "2026-03-22T00:00:00Z")]

    def fetch_details(self, handle: str):
        return RawProgram("hackerone", {"handle": handle}, handle, "2026-03-22T00:00:01Z")

    def normalize(self, raw: RawProgram) -> Program:
        return Program(
            platform="hackerone",
            handle=raw.handle,
            name="Demo",
            scopes=[ProgramScope("in_scope", "domain", "example.com")],
        )


@pytest.mark.asyncio
async def test_platform_scrape_is_metadata_only_no_scan_publish() -> None:
    main._redis = _DummyRedis()
    main._repository = AsyncMock()
    main._repository.upsert.return_value = uuid4()
    main._publisher = AsyncMock()

    with (
        patch.object(main.CollectorRegistry, "get", return_value=_DummyCollector),
        patch.object(main._scope_parser, "parse", side_effect=lambda scopes: scopes),
    ):
        result = await main._run_platform_scrape("hackerone")

    assert result["status"] == "completed"
    assert result["upserted"] == 1
    assert result["published"] == 0
    main._repository.upsert.assert_called_once()
    main._publisher.publish_scan_job.assert_not_called()


@pytest.mark.asyncio
async def test_publish_due_scan_jobs_uses_bounded_batch() -> None:
    program_id = uuid4()
    main._repository = AsyncMock()
    main._repository.get_programs_due_for_scan.return_value = [
        {
            "program_id": program_id,
            "platform": "hackerone",
            "handle": "demo",
            "name": "Demo",
        }
    ]
    main._repository.get_scope.return_value = [
        {
            "scope_type": "in_scope",
            "asset_type": "domain",
            "value": "example.com",
            "notes": None,
        }
    ]
    main._publisher = AsyncMock()
    main._publisher.publish_scan_job.return_value = True

    with patch.object(main.log, "info") as info_mock:
        result = await main._publish_due_scan_jobs(batch_size=1)

    main._repository.get_programs_due_for_scan.assert_called_once_with(
        interval_minutes=main.settings.scraper_scan_publish_interval_minutes,
        batch_size=1,
    )
    main._publisher.publish_scan_job.assert_called_once()
    assert result["published"] == 1
    assert result["attempted"] == 1
    assert result["queue"] == "scan.jobs"

    info_event_names = [call.args[0] for call in info_mock.call_args_list]
    assert "scan_publish_batch_completed" in info_event_names
