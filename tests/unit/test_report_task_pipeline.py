from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.services.reporter.models import ParsedScan, ProgramInfo
from backend.shared.schemas.report_jobs import ReportJobsPayload, SeverityBreakdown

try:
    from backend.services.reporter import report_task
except ModuleNotFoundError:
    report_task = None


pytestmark = pytest.mark.skipif(report_task is None, reason="kombu/celery/reporter deps not installed")


class _SessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return None


def _parsed_scan() -> ParsedScan:
    return ParsedScan(
        scan_id=uuid4(),
        status="completed",
        partial=False,
        finding_count=0,
        verified_count=0,
        severity_breakdown={"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
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
        findings=[],
    )


def _payload(scan_id: str, program_id: str, report_id: str) -> ReportJobsPayload:
    return ReportJobsPayload(
        scan_id=scan_id,
        program_id=program_id,
        status="completed",
        partial_stages=[],
        has_findings=False,
        finding_count=0,
        verified_count=0,
        severity_breakdown=SeverityBreakdown(
            critical=0,
            high=0,
            medium=0,
            low=0,
            informational=0,
        ),
        formats_requested=["pdf"],
        report_ids={"pdf": report_id},
        include_evidence_screenshots=False,
    )


@pytest.mark.asyncio
async def test_publish_failure_after_upload_does_not_mark_failed(monkeypatch, tmp_path: Path) -> None:
    report_id = str(uuid4())
    scan_id = str(uuid4())
    program_id = str(uuid4())
    parsed = _parsed_scan()
    payload = _payload(scan_id=scan_id, program_id=program_id, report_id=report_id)

    artifact_path = tmp_path / "artifact.pdf"
    artifact_path.write_bytes(b"%PDF-1.4\nx")

    class _Repo:
        mark_completed_calls = 0
        mark_failed_calls = 0

        def __init__(self, session):
            pass

        async def mark_generating(self, report_id: str) -> None:
            return None

        async def create_or_reset_report(self, scan_id: str, program_id: str, format_name: str) -> str:
            return report_id

        async def replace_reproduction_packs(self, report_id: str, packs) -> None:
            return None

        async def mark_partial(self, report_id: str, storage_path: str, file_size_bytes: int, reason: str) -> None:
            raise AssertionError("mark_partial should not be called in this scenario")

        async def mark_completed(self, report_id: str, storage_path: str, file_size_bytes: int) -> None:
            _Repo.mark_completed_calls += 1

        async def mark_failed(self, report_id: str, error_detail: str) -> None:
            _Repo.mark_failed_calls += 1

        async def get_report(self, report_id: str):
            return {
                "report_id": report_id,
                "scan_id": scan_id,
                "program_id": program_id,
                "format": "pdf",
                "status": "completed",
                "storage_path": "reports/x/report.pdf",
                "file_size_bytes": 10,
                "generated_at": "2026-03-29T00:00:00+00:00",
            }

    class _Storage:
        async def upload_report(self, report_id: str, format_name: str, local_path: str):
            return "reports/x/report.pdf", 10

    class _CompletionPublisher:
        async def publish_report_completed(self, report: dict) -> bool:
            return False

    session = SimpleNamespace()
    monkeypatch.setattr(report_task, "get_session", lambda: _SessionContext(session))
    monkeypatch.setattr(report_task, "ReportRepository", _Repo)
    monkeypatch.setattr(report_task, "_storage", _Storage())
    monkeypatch.setattr(
        report_task,
        "_render_artifact",
        lambda report_id, parsed_scan, format_name, packs: (str(artifact_path), []),
    )
    monkeypatch.setattr(report_task, "_validate_rendered_artifact", lambda format_name, local_path: None)

    await report_task._process_single_format(
        payload=payload,
        parsed_scan=parsed,
        format_name="pdf",
        shared_partial_reasons=[],
        completion_publisher=_CompletionPublisher(),
    )

    assert _Repo.mark_completed_calls == 1
    assert _Repo.mark_failed_calls == 0


@pytest.mark.asyncio
async def test_forced_upload_failure_marks_report_failed(monkeypatch, tmp_path: Path) -> None:
    report_id = str(uuid4())
    scan_id = str(uuid4())
    program_id = str(uuid4())
    parsed = _parsed_scan()
    payload = _payload(scan_id=scan_id, program_id=program_id, report_id=report_id)

    artifact_path = tmp_path / "artifact.pdf"
    artifact_path.write_bytes(b"%PDF-1.4\nx")

    class _Repo:
        mark_completed_calls = 0
        mark_failed_calls = 0

        def __init__(self, session):
            pass

        async def mark_generating(self, report_id: str) -> None:
            return None

        async def create_or_reset_report(self, scan_id: str, program_id: str, format_name: str) -> str:
            return report_id

        async def replace_reproduction_packs(self, report_id: str, packs) -> None:
            return None

        async def mark_partial(self, report_id: str, storage_path: str, file_size_bytes: int, reason: str) -> None:
            raise AssertionError("mark_partial should not be called in this scenario")

        async def mark_completed(self, report_id: str, storage_path: str, file_size_bytes: int) -> None:
            _Repo.mark_completed_calls += 1

        async def mark_failed(self, report_id: str, error_detail: str) -> None:
            _Repo.mark_failed_calls += 1

        async def get_report(self, report_id: str):
            return None

    class _Storage:
        async def upload_report(self, report_id: str, format_name: str, local_path: str):
            return "reports/x/report.pdf", 10

    class _CompletionPublisher:
        async def publish_report_completed(self, report: dict) -> bool:
            return True

    session = SimpleNamespace()
    monkeypatch.setattr(report_task, "get_session", lambda: _SessionContext(session))
    monkeypatch.setattr(report_task, "ReportRepository", _Repo)
    monkeypatch.setattr(report_task, "_storage", _Storage())
    monkeypatch.setattr(
        report_task,
        "_render_artifact",
        lambda report_id, parsed_scan, format_name, packs: (str(artifact_path), []),
    )
    monkeypatch.setattr(report_task, "_validate_rendered_artifact", lambda format_name, local_path: None)
    monkeypatch.setattr(
        report_task.settings,
        "get_force_upload_failure_report_ids",
        lambda: {"*"},
    )

    await report_task._process_single_format(
        payload=payload,
        parsed_scan=parsed,
        format_name="pdf",
        shared_partial_reasons=[],
        completion_publisher=_CompletionPublisher(),
    )

    assert _Repo.mark_completed_calls == 0
    assert _Repo.mark_failed_calls == 1
