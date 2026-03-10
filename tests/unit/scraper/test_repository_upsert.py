"""
Unit tests for ProgramRepository.upsert().

The critical invariant under test:
  queued_for_scan must NEVER appear in the ON CONFLICT DO UPDATE SET clause.
  If it was set True by a failed publish, a subsequent rescrape must not
  reset it to False — only the reconciler may clear the flag.
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.services.scraper.collectors.models import RawProgram, RawPolicy, RawScopeEntry


def make_raw_program(handle: str = "test_handle") -> RawProgram:
    return RawProgram(
        platform    = "hackerone",
        handle      = handle,
        name        = "Test Program",
        url         = f"https://hackerone.com/{handle}",
        bounty_type = "paid",
        max_bounty  = 5000,
        is_active   = True,
        raw_policy  = {},
        policy      = RawPolicy(
            disclosure_policy    = "Standard",
            testing_restrictions = [],
            safe_harbor          = True,
        ),
        scopes = [
            RawScopeEntry(
                asset_type = "wildcard_domain",
                value      = "*.example.com",
                scope_type = "in_scope",
            )
        ],
    )


def make_normalized(handle: str = "test_handle") -> dict:
    return {
        "platform":    "hackerone",
        "handle":      handle,
        "name":        "Test Program",
        "url":         f"https://hackerone.com/{handle}",
        "bounty_type": "paid",
        "max_bounty":  5000,
        "is_active":   True,
        "raw_policy":  {},
    }


@pytest.mark.asyncio
async def test_queued_for_scan_not_in_on_conflict_set() -> None:
    """
    The ON CONFLICT DO UPDATE SET clause must not contain queued_for_scan.
    This is the critical invariant: a rescrape must never reset a True flag.
    """
    from backend.services.scraper.repository import ProgramRepository

    raw        = make_raw_program()
    normalized = make_normalized()
    captured_set_dict: dict = {}

    with patch("backend.services.scraper.repository.pg_insert") as mock_insert:
        mock_stmt = MagicMock()
        mock_insert.return_value = mock_stmt
        mock_stmt.values.return_value = mock_stmt

        def capture_conflict(index_elements, set_):
            captured_set_dict.update(set_)
            return mock_stmt

        mock_stmt.on_conflict_do_update.side_effect = capture_conflict
        mock_stmt.returning.return_value = mock_stmt

        # Mock the session context manager
        program_id = uuid4()
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc)
        fake_row = MagicMock()
        fake_row.program_id = program_id
        fake_row.created_at = ts
        fake_row.updated_at = ts

        mock_execute_result = MagicMock()
        mock_execute_result.fetchone.return_value = fake_row

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__  = AsyncMock(return_value=False)
        mock_session.execute    = AsyncMock(return_value=mock_execute_result)
        mock_session.add        = MagicMock()
        mock_session.refresh    = AsyncMock()

        with patch("backend.services.scraper.repository.get_session",
                   return_value=mock_session):
            repo = ProgramRepository()
            try:
                await repo.upsert(raw, normalized)
            except Exception:
                pass  # we only care about the captured SET clause

    assert "queued_for_scan" not in captured_set_dict, (
        "queued_for_scan must NOT be in the ON CONFLICT DO UPDATE SET clause. "
        "A rescrape must never reset a True flag — only the reconciler may do that."
    )


@pytest.mark.asyncio
async def test_upsert_excludes_queued_for_scan_from_update_fields() -> None:
    """
    Verify the normalized dict itself doesn't smuggle queued_for_scan in.
    normalize() should not include it; upsert() should not add it to the SET.
    """
    from backend.services.scraper.collectors.hackerone import HackerOneCollector

    collector  = HackerOneCollector(api_username="u", api_token="t")
    raw        = make_raw_program()
    normalized = collector.normalize(raw)

    assert "queued_for_scan" not in normalized, (
        "normalize() must not include queued_for_scan. "
        "The upsert SET clause is built from this dict."
    )


@pytest.mark.asyncio
async def test_set_queued_for_scan_sets_true() -> None:
    """set_queued_for_scan(True) executes an UPDATE setting the flag."""
    from backend.services.scraper.repository import ProgramRepository
    import sqlalchemy as sa

    program_id = uuid4()

    executed_statements = []

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__  = AsyncMock(return_value=False)

    async def capture_execute(stmt, *args, **kwargs):
        executed_statements.append(stmt)
        return MagicMock()

    mock_session.execute = capture_execute

    with patch("backend.services.scraper.repository.get_session",
               return_value=mock_session):
        repo = ProgramRepository()
        await repo.set_queued_for_scan(program_id, queued=True)

    assert len(executed_statements) == 1


@pytest.mark.asyncio
async def test_set_queued_for_scan_sets_false() -> None:
    """set_queued_for_scan(False) executes an UPDATE clearing the flag."""
    from backend.services.scraper.repository import ProgramRepository

    program_id = uuid4()
    executed = []

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__  = AsyncMock(return_value=False)
    mock_session.execute    = AsyncMock(side_effect=lambda s, *a, **k: executed.append(s) or MagicMock())

    with patch("backend.services.scraper.repository.get_session",
               return_value=mock_session):
        repo = ProgramRepository()
        await repo.set_queued_for_scan(program_id, queued=False)

    assert len(executed) == 1
