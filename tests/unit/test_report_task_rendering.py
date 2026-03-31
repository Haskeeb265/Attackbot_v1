from uuid import uuid4

from backend.services.reporter.models import ParsedFinding, ParsedScan, ProgramInfo
import pytest

try:
    from backend.services.reporter.report_task import (
        _build_report_lines,
        _validate_rendered_artifact,
    )
except ModuleNotFoundError:
    _build_report_lines = None
    _validate_rendered_artifact = None


pytestmark = pytest.mark.skipif(_build_report_lines is None, reason="kombu/celery dependencies not installed")


def _parsed_scan_with_findings() -> ParsedScan:
    finding = ParsedFinding(
        finding_id=uuid4(),
        title="Stored XSS",
        vulnerability_type="xss",
        severity="high",
        cvss_score=8.0,
        cvss_vector=None,
        affected_url="https://example.com/app",
        affected_parameter="q",
        description="desc",
        reproduction_steps=None,
        source="unit",
        is_verified=False,
        raw_output=None,
    )
    return ParsedScan(
        scan_id=uuid4(),
        status="completed",
        partial=False,
        finding_count=1,
        verified_count=0,
        severity_breakdown={"high": 1, "info": 0, "low": 0, "medium": 0, "critical": 0},
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
        findings=[finding],
    )


def test_build_report_lines_includes_verification_status_text() -> None:
    lines = _build_report_lines(_parsed_scan_with_findings())
    joined = "\n".join(lines)

    assert "Findings Table" in joined
    assert "Verification Status" in joined
    assert "unverified" in joined


def test_build_report_lines_zero_findings_contains_no_findings_statement() -> None:
    parsed = _parsed_scan_with_findings()
    parsed.findings = []
    parsed.finding_count = 0

    lines = _build_report_lines(parsed)
    joined = "\n".join(lines)

    assert "No findings were produced for this scan" in joined


def test_validate_rendered_artifact_accepts_valid_pdf(tmp_path) -> None:
    artifact = tmp_path / "report.pdf"
    artifact.write_bytes(b"%PDF-1.4\nrest")
    _validate_rendered_artifact("pdf", str(artifact))


def test_validate_rendered_artifact_rejects_invalid_docx(tmp_path) -> None:
    artifact = tmp_path / "report.docx"
    artifact.write_bytes(b"not-a-zip")

    with pytest.raises(ValueError, match="not a zip archive"):
        _validate_rendered_artifact("docx", str(artifact))
