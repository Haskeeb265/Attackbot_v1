"""Unit tests for report_task.py _process_single_format."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.models import (
    ParsedFinding,
    ParsedScan,
    ProgramInfo,
    ReproductionPackDraft,
)


def _sample_scan() -> ParsedScan:
    return ParsedScan(
        scan_id=uuid4(),
        status="completed",
        partial=False,
        finding_count=1,
        verified_count=0,
        severity_breakdown={"high": 1},
        include_evidence_screenshots=False,
        program=ProgramInfo(
            program_id=uuid4(),
            platform="hackerone",
            handle="demo",
            name="Demo",
            url=None,
            bounty_type=None,
            max_bounty=None,
            is_active=True,
        ),
        scope=[],
        findings=[
            ParsedFinding(
                finding_id=UUID("00000000-0000-0000-0000-000000000011"),
                title="XSS",
                vulnerability_type="xss",
                severity="high",
                cvss_score=8.0,
                cvss_vector=None,
                affected_url="https://example.com",
                affected_parameter="q",
                description="XSS",
                reproduction_steps=None,
                source="unit",
                is_verified=False,
                raw_output=None,
            )
        ],
    )


@pytest.mark.asyncio
async def test_process_single_format_mark_failed_on_exception() -> None:
    from backend.services.reporter.report_task import _process_single_format
    from backend.shared.schemas.report_jobs import ReportJobsPayload

    payload = ReportJobsPayload(
        scan_id=str(uuid4()),
        program_id=str(uuid4()),
        status="completed",
        has_findings=True,
        finding_count=1,
        verified_count=0,
        severity_breakdown={},
        formats_requested=["pdf"],
    )

    parsed_scan = _sample_scan()
    completion_publisher = AsyncMock()
    completion_publisher.publish_report_completed = AsyncMock()

    report_id = str(uuid4())

    with tempfile.TemporaryDirectory() as tmpdir:
        settings = ReporterConfig(temp_output_dir=tmpdir)

        with patch("backend.services.reporter.report_task.get_session") as mock_get_session, \
             patch("backend.services.reporter.report_task.ReportRepository") as mock_repo_cls, \
             patch("backend.services.reporter.report_task.settings", settings), \
             patch("backend.services.reporter.report_task.record_generation") as mock_record_gen, \
             patch("backend.services.reporter.report_task.record_generation_failure") as mock_fail:

            mock_session = AsyncMock()
            mock_cm = MagicMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_cm.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_cm

            mock_repo = AsyncMock()
            mock_repo.create_or_reset_report = AsyncMock(return_value=report_id)
            mock_repo.mark_generating = AsyncMock()
            mock_repo.mark_failed = AsyncMock()
            mock_repo_cls.return_value = mock_repo

            # Make reproduction raise an exception
            with patch("backend.services.reporter.report_task.build_reproduction_packs", side_effect=RuntimeError("boom")):
                await _process_single_format(
                    payload=payload,
                    parsed_scan=parsed_scan,
                    format_name="pdf",
                    shared_partial_reasons=[],
                    completion_publisher=completion_publisher,
                )

            mock_repo.mark_failed.assert_called_once()
            mock_fail.assert_called_once()
            mock_record_gen.assert_called_once()


@pytest.mark.asyncio
async def test_process_single_format_uses_existing_report_id() -> None:
    from backend.services.reporter.report_task import _process_single_format
    from backend.shared.schemas.report_jobs import ReportJobsPayload

    existing_report_id = str(uuid4())
    payload = ReportJobsPayload(
        scan_id=str(uuid4()),
        program_id=str(uuid4()),
        status="completed",
        has_findings=True,
        finding_count=1,
        verified_count=0,
        severity_breakdown={},
        formats_requested=["pdf"],
        report_ids={"pdf": UUID(existing_report_id)},
    )

    parsed_scan = _sample_scan()
    completion_publisher = AsyncMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        settings = ReporterConfig(temp_output_dir=tmpdir)

        with patch("backend.services.reporter.report_task.ReporterStorage") as mock_storage_cls, \
             patch("backend.services.reporter.report_task.ReportRepository") as mock_repo_cls, \
             patch("backend.services.reporter.report_task.settings", settings), \
             patch("backend.services.reporter.report_task.get_session") as mock_get_session, \
             patch("backend.services.reporter.report_task._render_artifact") as mock_render, \
             patch("backend.services.reporter.report_task.build_reproduction_packs", return_value=([], [], False)), \
             patch("backend.services.reporter.report_task.record_generation"):

            mock_session = AsyncMock()
            mock_cm = MagicMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_cm.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_cm

            mock_repo = AsyncMock()
            mock_repo.mark_generating = AsyncMock()
            mock_repo.replace_reproduction_packs = AsyncMock()
            mock_repo.mark_completed = AsyncMock()
            mock_repo.get_report = AsyncMock(return_value={
                "report_id": existing_report_id,
                "scan_id": str(payload.scan_id),
                "program_id": str(payload.program_id),
                "format": "pdf",
                "status": "completed",
                "storage_path": "path",
                "file_size_bytes": 100,
                "generated_at": "2026-01-01T00:00:00Z",
            })
            mock_repo_cls.return_value = mock_repo

            mock_storage = AsyncMock()
            mock_storage.upload_report = AsyncMock(return_value=("path/to/file", 100))
            mock_storage_cls.return_value = mock_storage

            output_file = Path(tmpdir) / "output.pdf"
            output_file.write_bytes(b"%PDF test")
            mock_render.return_value = (str(output_file), [])

            await _process_single_format(
                payload=payload,
                parsed_scan=parsed_scan,
                format_name="pdf",
                shared_partial_reasons=[],
                completion_publisher=completion_publisher,
            )

            mock_repo.mark_generating.assert_called_once_with(existing_report_id)


@pytest.mark.asyncio
async def test_process_single_format_creates_new_report_id() -> None:
    from backend.services.reporter.report_task import _process_single_format
    from backend.shared.schemas.report_jobs import ReportJobsPayload

    payload = ReportJobsPayload(
        scan_id=str(uuid4()),
        program_id=str(uuid4()),
        status="completed",
        has_findings=True,
        finding_count=1,
        verified_count=0,
        severity_breakdown={},
        formats_requested=["pdf"],
        report_ids=None,
    )

    parsed_scan = _sample_scan()
    completion_publisher = AsyncMock()
    new_report_id = str(uuid4())

    with tempfile.TemporaryDirectory() as tmpdir:
        settings = ReporterConfig(temp_output_dir=tmpdir)

        with patch("backend.services.reporter.report_task.ReporterStorage") as mock_storage_cls, \
             patch("backend.services.reporter.report_task.ReportRepository") as mock_repo_cls, \
             patch("backend.services.reporter.report_task.settings", settings), \
             patch("backend.services.reporter.report_task.get_session") as mock_get_session, \
             patch("backend.services.reporter.report_task._render_artifact") as mock_render, \
             patch("backend.services.reporter.report_task.build_reproduction_packs", return_value=([], [], False)), \
             patch("backend.services.reporter.report_task.record_generation"):

            mock_session = AsyncMock()
            mock_cm = MagicMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_cm.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_cm

            mock_repo = AsyncMock()
            mock_repo.create_or_reset_report = AsyncMock(return_value=new_report_id)
            mock_repo.mark_generating = AsyncMock()
            mock_repo.replace_reproduction_packs = AsyncMock()
            mock_repo.mark_completed = AsyncMock()
            mock_repo.get_report = AsyncMock(return_value={
                "report_id": new_report_id,
                "scan_id": str(payload.scan_id),
                "program_id": str(payload.program_id),
                "format": "pdf",
                "status": "completed",
                "storage_path": "path",
                "file_size_bytes": 100,
                "generated_at": "2026-01-01T00:00:00Z",
            })
            mock_repo_cls.return_value = mock_repo

            mock_storage = AsyncMock()
            mock_storage.upload_report = AsyncMock(return_value=("path/to/file", 100))
            mock_storage_cls.return_value = mock_storage

            output_file = Path(tmpdir) / "output.pdf"
            output_file.write_bytes(b"%PDF test")
            mock_render.return_value = (str(output_file), [])

            await _process_single_format(
                payload=payload,
                parsed_scan=parsed_scan,
                format_name="pdf",
                shared_partial_reasons=[],
                completion_publisher=completion_publisher,
            )

            mock_repo.create_or_reset_report.assert_called_once()
