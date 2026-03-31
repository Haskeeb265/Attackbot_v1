from uuid import uuid4

from backend.services.reporter.models import ParsedFinding, ParsedScan, ProgramInfo, ReproductionPackDraft
from backend.services.reporter.renderers.sections import (
    NO_FINDINGS_STATEMENT,
    UNVERIFIED_CAVEAT,
    build_render_plan,
)


def _parsed_scan(with_findings: bool = True, include_evidence: bool = True) -> ParsedScan:
    findings = []
    if with_findings:
        findings = [
            ParsedFinding(
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
        ]

    return ParsedScan(
        scan_id=uuid4(),
        status="completed",
        partial=False,
        finding_count=len(findings),
        verified_count=0,
        severity_breakdown={"high": 1, "info": 0, "low": 0, "medium": 0, "critical": 0},
        include_evidence_screenshots=include_evidence,
        program=ProgramInfo(
            program_id=uuid4(),
            platform="hackerone",
            handle="demo",
            name="Demo Program",
            url=None,
            bounty_type=None,
            max_bounty=None,
            is_active=True,
        ),
        scope=[],
        findings=findings,
    )


def _packs_for(scan: ParsedScan) -> list[ReproductionPackDraft]:
    if not scan.findings:
        return []
    finding = scan.findings[0]
    return [
        ReproductionPackDraft(
            finding_id=finding.finding_id,
            curl_command="curl -i -sS 'https://example.com/app' --data-urlencode 'q=<payload>'",
            http_request_raw="GET /app?q=%3Cpayload%3E HTTP/1.1",
            browser_steps="1. open page",
            notes="demo",
            is_fallback=False,
        )
    ]


def test_build_render_plan_includes_verification_status_column_and_caveat() -> None:
    scan = _parsed_scan(with_findings=True, include_evidence=True)
    plan = build_render_plan(scan, _packs_for(scan), include_raw_http_appendix=False)
    joined = "\n".join(plan.lines)

    assert "Findings Table" in joined
    assert "Verification Status" in joined
    assert UNVERIFIED_CAVEAT in joined


def test_build_render_plan_omits_raw_http_appendix_when_disabled() -> None:
    scan = _parsed_scan(with_findings=True, include_evidence=True)
    plan = build_render_plan(scan, _packs_for(scan), include_raw_http_appendix=False)
    joined = "\n".join(plan.lines)

    assert "Appendix - Raw HTTP Requests" not in joined


def test_build_render_plan_includes_raw_http_appendix_when_enabled() -> None:
    scan = _parsed_scan(with_findings=True, include_evidence=True)
    plan = build_render_plan(scan, _packs_for(scan), include_raw_http_appendix=True)
    joined = "\n".join(plan.lines)

    assert "Appendix - Raw HTTP Requests" in joined
    assert "GET /app?q=%3Cpayload%3E HTTP/1.1" in joined


def test_build_render_plan_clean_mode_uses_no_findings_statement() -> None:
    scan = _parsed_scan(with_findings=False, include_evidence=False)
    plan = build_render_plan(scan, [], include_raw_http_appendix=True)
    joined = "\n".join(plan.lines)

    assert "No Findings Statement" in joined
    assert NO_FINDINGS_STATEMENT in joined
    assert "Findings Table" not in joined
