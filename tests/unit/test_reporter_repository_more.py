"""Additional unit tests for repository.py to increase coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest


@pytest.mark.asyncio
async def test_report_repository_mark_generating() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    repo = ReportRepository(mock_session)

    report_id = str(uuid4())
    await repo.mark_generating(report_id)

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_report_repository_mark_completed() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    repo = ReportRepository(mock_session)

    report_id = str(uuid4())
    await repo.mark_completed(report_id, "storage/path", 1024)

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_report_repository_mark_partial() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    repo = ReportRepository(mock_session)

    report_id = str(uuid4())
    await repo.mark_partial(report_id, "storage/path", 1024, "reason")

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_report_repository_mark_failed() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    repo = ReportRepository(mock_session)

    report_id = str(uuid4())
    await repo.mark_failed(report_id, "error detail")

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_report_repository_get_report() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (
        str(uuid4()),  # report_id
        str(uuid4()),  # scan_id
        str(uuid4()),  # program_id
        "pdf",  # format
        "completed",  # status
        "path/to/file",  # storage_path
        1024,  # file_size_bytes
        None,  # error_detail
        datetime.now(timezone.utc),  # generated_at
        datetime.now(timezone.utc),  # created_at
    )
    mock_session.execute.return_value = mock_result

    repo = ReportRepository(mock_session)
    report = await repo.get_report(str(uuid4()))

    assert report is not None
    assert report["format"] == "pdf"
    assert report["status"] == "completed"


@pytest.mark.asyncio
async def test_report_repository_get_report_not_found() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_session.execute.return_value = mock_result

    repo = ReportRepository(mock_session)
    report = await repo.get_report(str(uuid4()))

    assert report is None


@pytest.mark.asyncio
async def test_report_repository_list_reports() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1
    mock_rows_result = MagicMock()
    mock_rows_result.fetchall.return_value = [
        (
            str(uuid4()), str(uuid4()), str(uuid4()), "pdf", "completed",
            "path", 1024, None, datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
    ]
    # First call is count, second is rows
    mock_session.execute.side_effect = [mock_count_result, mock_rows_result]

    repo = ReportRepository(mock_session)
    result = await repo.list_reports(page=1, page_size=10, scan_id_filter=None, status_filter=None)

    assert result["total"] == 1
    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_report_repository_get_reports_by_scan() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (
            str(uuid4()), str(uuid4()), str(uuid4()), "pdf", "completed",
            "path", 1024, None, datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
    ]
    mock_session.execute.return_value = mock_result

    repo = ReportRepository(mock_session)
    reports = await repo.get_reports_by_scan(str(uuid4()))

    assert len(reports) == 1


@pytest.mark.asyncio
async def test_report_repository_get_stale_generating_reports() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (
            str(uuid4()), str(uuid4()), str(uuid4()), "pdf", "generating",
            None, None, None, None, datetime.now(timezone.utc)
        )
    ]
    mock_session.execute.return_value = mock_result

    repo = ReportRepository(mock_session)
    result = await repo.get_stale_generating_reports(stale_minutes=30)

    assert len(result) == 1


@pytest.mark.asyncio
async def test_report_repository_replace_reproduction_packs() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    repo = ReportRepository(mock_session)

    class MockPack:
        finding_id = str(uuid4())
        curl_command = "curl test"
        http_request_raw = "GET /test"
        browser_steps = "step 1"
        notes = "test notes"

    packs = [MockPack()]
    await repo.replace_reproduction_packs(str(uuid4()), packs)

    assert mock_session.execute.call_count == 2  # Delete + Insert
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_report_repository_replace_reproduction_packs_with_dicts() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    repo = ReportRepository(mock_session)

    packs = [{
        "finding_id": str(uuid4()),
        "curl_command": "curl test",
        "http_request_raw": "GET /test",
        "browser_steps": "step 1",
        "notes": "test notes",
    }]
    await repo.replace_reproduction_packs(str(uuid4()), packs)

    assert mock_session.execute.call_count == 2
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_report_repository_list_reports_with_filters() -> None:
    from backend.services.reporter.repository import ReportRepository

    mock_session = AsyncMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1
    mock_rows_result = MagicMock()
    mock_rows_result.fetchall.return_value = [
        (
            str(uuid4()), str(uuid4()), str(uuid4()), "pdf", "completed",
            "path", 1024, None, datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
    ]
    mock_session.execute.side_effect = [mock_count_result, mock_rows_result]

    repo = ReportRepository(mock_session)
    result = await repo.list_reports(
        page=1, page_size=10,
        scan_id_filter=str(uuid4()),
        status_filter="completed"
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
