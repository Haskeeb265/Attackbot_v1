from pathlib import Path
from uuid import UUID

import pytest

from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.models import ParsedFinding, ParsedScan, ProgramInfo, ReproductionPackDraft
from backend.services.reporter.renderers.sections import NO_FINDINGS_STATEMENT, build_render_plan

try:
    import pdfplumber
    from docx import Document

    from backend.services.reporter.renderers.docx import DocxRenderer
    from backend.services.reporter.renderers.pdf import PdfRenderer
except ModuleNotFoundError:
    pdfplumber = None
    Document = None
    DocxRenderer = None
    PdfRenderer = None


pytestmark = pytest.mark.skipif(
    PdfRenderer is None or DocxRenderer is None or pdfplumber is None or Document is None,
    reason="reporter rendering dependencies not installed",
)


def _sample_scan(with_findings: bool = True) -> ParsedScan:
    findings = []
    if with_findings:
        findings = [
            ParsedFinding(
                finding_id=UUID("00000000-0000-0000-0000-000000000011"),
                title="Stored XSS",
                vulnerability_type="xss",
                severity="high",
                cvss_score=8.0,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                affected_url="https://example.com/app",
                affected_parameter="q",
                description="Stored XSS in comment field",
                reproduction_steps=None,
                source="unit",
                is_verified=False,
                raw_output=None,
            )
        ]

    return ParsedScan(
        scan_id=UUID("00000000-0000-0000-0000-000000000001"),
        status="completed",
        partial=False,
        finding_count=len(findings),
        verified_count=0,
        severity_breakdown={"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0},
        include_evidence_screenshots=False,
        program=ProgramInfo(
            program_id=UUID("00000000-0000-0000-0000-000000000002"),
            platform="hackerone",
            handle="demo-handle",
            name="Demo Program",
            url="https://example.com",
            bounty_type=None,
            max_bounty=None,
            is_active=True,
        ),
        scope=[],
        findings=findings,
    )


def _sample_packs() -> list[ReproductionPackDraft]:
    return [
        ReproductionPackDraft(
            finding_id=UUID("00000000-0000-0000-0000-000000000011"),
            curl_command="curl -i -sS 'https://example.com/app' --data-urlencode 'q=<payload>'",
            http_request_raw="GET /app?q=%3Cpayload%3E HTTP/1.1",
            browser_steps="1. Navigate to app",
            notes="Generated from finding metadata using deterministic ordering.",
            is_fallback=False,
        )
    ]


def _extract_pdf_outline(pdf_path: str) -> str:
    lines: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    return "\n".join(lines)


def _extract_docx_outline(docx_path: str) -> str:
    doc = Document(docx_path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(lines)


def _load_golden(name: str) -> list[str]:
    golden_path = Path("tests/fixtures/reporter/golden") / name
    return [line.strip() for line in golden_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_pdf_outline_contains_golden_lines(tmp_path: Path) -> None:
    scan = _sample_scan(with_findings=True)
    settings = ReporterConfig(temp_output_dir=str(tmp_path), include_raw_http_appendix=True)
    renderer = PdfRenderer(settings)

    output_path, partial_reasons = renderer.generate(
        report_id="00000000-0000-0000-0000-00000000abcd",
        parsed_scan=scan,
        packs=_sample_packs(),
    )
    assert partial_reasons == []

    outline = _extract_pdf_outline(output_path)
    for expected_line in _load_golden("report_outline_pdf.txt"):
        assert expected_line in outline


def test_docx_outline_contains_golden_lines(tmp_path: Path) -> None:
    scan = _sample_scan(with_findings=True)
    settings = ReporterConfig(temp_output_dir=str(tmp_path), include_raw_http_appendix=True)
    renderer = DocxRenderer(settings)

    output_path, partial_reasons = renderer.generate(
        report_id="00000000-0000-0000-0000-00000000dcba",
        parsed_scan=scan,
        packs=_sample_packs(),
    )
    assert partial_reasons == []

    outline = _extract_docx_outline(output_path)
    for expected_line in _load_golden("report_outline_docx.txt"):
        assert expected_line in outline


def test_no_findings_statement_matches_golden() -> None:
    plan = build_render_plan(
        parsed_scan=_sample_scan(with_findings=False),
        packs=[],
        include_raw_http_appendix=True,
    )
    expected = Path("tests/fixtures/reporter/golden/no_findings_summary.txt").read_text(
        encoding="utf-8"
    ).strip()
    assert NO_FINDINGS_STATEMENT == expected
    assert expected in "\n".join(plan.lines)
