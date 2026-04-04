"""Unit tests for report_task.py core logic with mocking."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.models import (
    EvidenceArtifact,
    ParsedFinding,
    ParsedScan,
    ProgramInfo,
    ReproductionPackDraft,
)


def _sample_parsed_scan() -> ParsedScan:
    return ParsedScan(
        scan_id=uuid4(),
        status="completed",
        partial=False,
        finding_count=1,
        verified_count=0,
        severity_breakdown={"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0},
        include_evidence_screenshots=False,
        program=ProgramInfo(
            program_id=uuid4(),
            platform="hackerone",
            handle="demo",
            name="Demo Program",
            url="https://example.com",
            bounty_type=None,
            max_bounty=None,
            is_active=True,
        ),
        scope=[],
        findings=[],
    )


def test_dedupe_preserve_order() -> None:
    from backend.services.reporter.report_task import _dedupe_preserve_order
    items = ["a", "b", "a", "c", "b", "d"]
    result = _dedupe_preserve_order(items)
    assert result == ["a", "b", "c", "d"]


def test_dedupe_preserve_order_empty() -> None:
    from backend.services.reporter.report_task import _dedupe_preserve_order
    assert _dedupe_preserve_order([]) == []


def test_safe_unlink_deletes_file(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _safe_unlink
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
    _safe_unlink(str(test_file))
    assert not test_file.exists()


def test_safe_unlink_missing_file_silently_ignored(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _safe_unlink
    test_file = tmp_path / "nonexistent.txt"
    _safe_unlink(str(test_file))


def test_validate_rendered_artifact_pdf_valid(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _validate_rendered_artifact
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")
    _validate_rendered_artifact("pdf", str(pdf_file))


def test_validate_rendered_artifact_pdf_invalid_header(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _validate_rendered_artifact
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("Not a PDF file")
    with pytest.raises(ValueError, match="missing %PDF header"):
        _validate_rendered_artifact("pdf", str(pdf_file))


def test_validate_rendered_artifact_docx_valid(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _validate_rendered_artifact
    docx_file = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_file, "w") as zf:
        zf.writestr("word/document.xml", "<w:document/>")
    _validate_rendered_artifact("docx", str(docx_file))


def test_validate_rendered_artifact_docx_not_zip(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _validate_rendered_artifact
    docx_file = tmp_path / "test.docx"
    docx_file.write_text("Not a zip file")
    with pytest.raises(ValueError, match="not a zip archive"):
        _validate_rendered_artifact("docx", str(docx_file))


def test_validate_rendered_artifact_docx_missing_document_xml(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _validate_rendered_artifact
    docx_file = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_file, "w") as zf:
        zf.writestr("some/other/file.txt", "content")
    with pytest.raises(ValueError, match="missing word/document.xml"):
        _validate_rendered_artifact("docx", str(docx_file))


def test_build_report_lines() -> None:
    from backend.services.reporter.report_task import _build_report_lines
    scan = _sample_parsed_scan()
    lines = _build_report_lines(scan)
    assert isinstance(lines, list)
    assert len(lines) > 0


def test_render_artifact_pdf_delegates_to_renderer(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _render_artifact

    settings = ReporterConfig(temp_output_dir=str(tmp_path))
    scan = _sample_parsed_scan()
    packs: list[ReproductionPackDraft] = []

    with patch("backend.services.reporter.report_task.PdfRenderer") as mock_renderer_cls, \
         patch("backend.services.reporter.report_task.settings", settings):
        mock_renderer = MagicMock()
        mock_renderer.generate.return_value = ("/path/to/output.pdf", [])
        mock_renderer_cls.return_value = mock_renderer

        result_path, partial_reasons = _render_artifact("report-123", scan, "pdf", packs)

    assert result_path == "/path/to/output.pdf"
    assert partial_reasons == []
    mock_renderer_cls.assert_called_once_with(settings)


def test_render_artifact_docx_delegates_to_renderer(tmp_path: Path) -> None:
    from backend.services.reporter.report_task import _render_artifact

    settings = ReporterConfig(temp_output_dir=str(tmp_path))
    scan = _sample_parsed_scan()
    packs: list[ReproductionPackDraft] = []

    with patch("backend.services.reporter.report_task.DocxRenderer") as mock_renderer_cls, \
         patch("backend.services.reporter.report_task.settings", settings):
        mock_renderer = MagicMock()
        mock_renderer.generate.return_value = ("/path/to/output.docx", [])
        mock_renderer_cls.return_value = mock_renderer

        result_path, partial_reasons = _render_artifact("report-123", scan, "docx", packs)

    assert result_path == "/path/to/output.docx"
    assert partial_reasons == []
    mock_renderer_cls.assert_called_once()


def test_render_artifact_unsupported_format() -> None:
    from backend.services.reporter.report_task import _render_artifact

    scan = _sample_parsed_scan()
    packs: list[ReproductionPackDraft] = []

    with pytest.raises(ValueError, match="Unsupported format: txt"):
        _render_artifact("report-123", scan, "txt", packs)


def test_assert_upload_not_forced_failure_no_forced_ids() -> None:
    from backend.services.reporter.report_task import _assert_upload_not_forced_failure

    with patch.object(ReporterConfig, "get_force_upload_failure_report_ids", return_value=set()):
        _assert_upload_not_forced_failure("report-123")


def test_assert_upload_not_forced_failure_report_id_none() -> None:
    from backend.services.reporter.report_task import _assert_upload_not_forced_failure

    with patch.object(ReporterConfig, "get_force_upload_failure_report_ids", return_value={"report-123"}):
        _assert_upload_not_forced_failure(None)


def test_assert_upload_not_forced_failure_wildcard_raises() -> None:
    from backend.services.reporter.report_task import _assert_upload_not_forced_failure

    with patch.object(ReporterConfig, "get_force_upload_failure_report_ids", return_value={"*"}):
        with pytest.raises(RuntimeError, match="forced_upload_failure"):
            _assert_upload_not_forced_failure("any-report-id")


def test_assert_upload_not_forced_failure_specific_id_raises() -> None:
    from backend.services.reporter.report_task import _assert_upload_not_forced_failure

    with patch.object(ReporterConfig, "get_force_upload_failure_report_ids", return_value={"report-abc"}):
        with pytest.raises(RuntimeError, match="forced_upload_failure:report-abc"):
            _assert_upload_not_forced_failure("report-abc")
