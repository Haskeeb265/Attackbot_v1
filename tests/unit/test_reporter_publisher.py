"""Unit tests for publisher.py."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from backend.services.reporter.publisher import ReportsCompletedPublisher


@pytest.fixture
def mock_queue_publisher() -> AsyncMock:
    publisher = AsyncMock()
    publisher.publish = AsyncMock(return_value=True)
    return publisher


@pytest.fixture
def sample_report() -> dict[str, Any]:
    return {
        "report_id": str(UUID("11111111-1111-1111-1111-111111111111")),
        "scan_id": str(UUID("22222222-2222-2222-2222-222222222222")),
        "program_id": str(UUID("33333333-3333-3333-3333-333333333333")),
        "format": "pdf",
        "status": "completed",
        "storage_path": "reports/report-123/report.pdf",
        "file_size_bytes": 1024,
        "generated_at": "2026-04-04T12:00:00+00:00",
    }


@pytest.mark.asyncio
async def test_publish_report_completed_success(
    mock_queue_publisher: AsyncMock,
    sample_report: dict[str, Any],
) -> None:
    publisher = ReportsCompletedPublisher(mock_queue_publisher)
    result = await publisher.publish_report_completed(sample_report)
    assert result is True
    mock_queue_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_publish_report_completed_without_generated_at(
    mock_queue_publisher: AsyncMock,
) -> None:
    publisher = ReportsCompletedPublisher(mock_queue_publisher)
    report_without_timestamp = {
        "report_id": str(UUID("11111111-1111-1111-1111-111111111111")),
        "scan_id": str(UUID("22222222-2222-2222-2222-222222222222")),
        "program_id": str(UUID("33333333-3333-3333-3333-333333333333")),
        "format": "pdf",
        "status": "completed",
        "storage_path": "reports/report-123/report.pdf",
        "file_size_bytes": 1024,
    }
    result = await publisher.publish_report_completed(report_without_timestamp)
    assert result is True


@pytest.mark.asyncio
async def test_publish_report_completed_partial_status(
    mock_queue_publisher: AsyncMock,
) -> None:
    publisher = ReportsCompletedPublisher(mock_queue_publisher)
    partial_report = {
        "report_id": str(UUID("11111111-1111-1111-1111-111111111111")),
        "scan_id": str(UUID("22222222-2222-2222-2222-222222222222")),
        "program_id": str(UUID("33333333-3333-3333-3333-333333333333")),
        "format": "pdf",
        "status": "partial",
        "storage_path": "reports/report-123/report.pdf",
        "file_size_bytes": 1024,
        "generated_at": "2026-04-04T12:00:00+00:00",
    }
    result = await publisher.publish_report_completed(partial_report)
    assert result is True


@pytest.mark.asyncio
async def test_publish_report_completed_docx_format(
    mock_queue_publisher: AsyncMock,
) -> None:
    publisher = ReportsCompletedPublisher(mock_queue_publisher)
    docx_report = {
        "report_id": str(UUID("44444444-4444-4444-4444-444444444444")),
        "scan_id": str(UUID("55555555-5555-5555-5555-555555555555")),
        "program_id": str(UUID("66666666-6666-6666-6666-666666666666")),
        "format": "docx",
        "status": "completed",
        "storage_path": "reports/report-456/report.docx",
        "file_size_bytes": 2048,
        "generated_at": "2026-04-04T12:00:00+00:00",
    }
    result = await publisher.publish_report_completed(docx_report)
    assert result is True


@pytest.mark.asyncio
async def test_publish_report_completed_publish_fails(
    mock_queue_publisher: AsyncMock,
    sample_report: dict[str, Any],
) -> None:
    mock_queue_publisher.publish.return_value = False
    publisher = ReportsCompletedPublisher(mock_queue_publisher)
    with patch("backend.services.reporter.publisher.log") as mock_log:
        result = await publisher.publish_report_completed(sample_report)
    assert result is False
    mock_log.error.assert_called_once()


@pytest.mark.asyncio
async def test_publish_report_completed_logs_error_details(
    mock_queue_publisher: AsyncMock,
    sample_report: dict[str, Any],
) -> None:
    mock_queue_publisher.publish.return_value = False
    publisher = ReportsCompletedPublisher(mock_queue_publisher)
    with patch("backend.services.reporter.publisher.log") as mock_log:
        await publisher.publish_report_completed(sample_report)
    error_call_args = mock_log.error.call_args
    assert error_call_args.kwargs.get("report_id") == sample_report["report_id"]
