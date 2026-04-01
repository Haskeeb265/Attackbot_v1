from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.reporter.repository import ReportRepository


@pytest.mark.asyncio
async def test_create_or_reset_report_returns_report_id_and_commits() -> None:
    session = AsyncMock()
    fetch_result = MagicMock()
    fetch_result.fetchone.return_value = ("report-id-1",)
    session.execute.return_value = fetch_result

    repository = ReportRepository(session)
    report_id = await repository.create_or_reset_report(
        scan_id="scan-id",
        program_id="program-id",
        format_name="pdf",
    )

    assert report_id == "report-id-1"
    assert session.execute.await_count == 1
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_partial_sets_generated_at() -> None:
    session = AsyncMock()
    session.execute.return_value = MagicMock()

    repository = ReportRepository(session)
    await repository.mark_partial(
        report_id="report-id",
        storage_path="reports/report-id/report.pdf",
        file_size_bytes=123,
        reason="fallback_pack_used",
    )

    sql_text = session.execute.await_args.args[0].text.lower()
    assert "generated_at = now()" in sql_text
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_failed_does_not_set_generated_at() -> None:
    session = AsyncMock()
    session.execute.return_value = MagicMock()

    repository = ReportRepository(session)
    await repository.mark_failed(report_id="report-id", error_detail="boom")

    sql_text = session.execute.await_args.args[0].text.lower()
    assert "generated_at" not in sql_text
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_reports_serializes_rows() -> None:
    session = AsyncMock()

    count_result = MagicMock()
    count_result.scalar.return_value = 1

    rows_result = MagicMock()
    rows_result.fetchall.return_value = [
        (
            "report-1",
            "scan-1",
            "program-1",
            "pdf",
            "completed",
            "reports/report-1/report.pdf",
            42,
            None,
            None,
            None,
        )
    ]

    session.execute.side_effect = [count_result, rows_result]

    repository = ReportRepository(session)
    response = await repository.list_reports(page=1, page_size=20, scan_id_filter=None, status_filter=None)

    assert response["total"] == 1
    assert response["page"] == 1
    assert response["page_size"] == 20
    assert len(response["items"]) == 1
    assert response["items"][0]["report_id"] == "report-1"
