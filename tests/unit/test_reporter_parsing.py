from uuid import uuid4

from backend.services.reporter.parsing import ParsedScanBuilder


def _scan_payload() -> dict:
    return {
        "scan_id": str(uuid4()),
        "status": "completed",
        "finding_count": 2,
        "severity_breakdown": {
            "high": 1,
            "informational": 1,
        },
    }


def _program_payload() -> dict:
    return {
        "program_id": str(uuid4()),
        "platform": "hackerone",
        "handle": "demo",
        "name": "Demo Program",
        "url": "https://hackerone.com/demo",
        "bounty_type": "bug_bounty",
        "max_bounty": 10000,
        "is_active": True,
    }


def _scope_payload() -> dict:
    return {
        "scope": [
            {
                "scope_type": "in_scope",
                "asset_type": "domain",
                "value": "example.com",
            }
        ]
    }


def test_parsed_scan_includes_unverified_findings_with_flag() -> None:
    findings_payload = [
        {
            "finding_id": str(uuid4()),
            "title": "Reflected XSS",
            "vulnerability_type": "xss",
            "severity": "high",
            "cvss_score": 7.5,
            "affected_url": "https://example.com/search",
            "is_verified": False,
        }
    ]

    parsed = ParsedScanBuilder().build(
        scan_payload=_scan_payload(),
        findings_payload=findings_payload,
        program_payload=_program_payload(),
        scope_payload=_scope_payload(),
        exploit_chain_refs=[],
        include_evidence_screenshots=True,
    )

    assert len(parsed.findings) == 1
    assert parsed.findings[0].is_verified is False


def test_zero_findings_returns_clean_mode() -> None:
    scan_payload = _scan_payload()
    scan_payload["finding_count"] = 0

    parsed = ParsedScanBuilder().build(
        scan_payload=scan_payload,
        findings_payload=[],
        program_payload=_program_payload(),
        scope_payload=_scope_payload(),
        exploit_chain_refs=[],
        include_evidence_screenshots=False,
    )

    assert parsed.is_clean() is True


def test_severity_breakdown_normalizes_info_and_informational() -> None:
    scan_payload = _scan_payload()
    scan_payload["severity_breakdown"] = {
        "critical": 1,
        "informational": 2,
        "info": 1,
    }

    parsed = ParsedScanBuilder().build(
        scan_payload=scan_payload,
        findings_payload=[],
        program_payload=_program_payload(),
        scope_payload=_scope_payload(),
        exploit_chain_refs=[],
        include_evidence_screenshots=False,
    )

    assert parsed.severity_breakdown["critical"] == 1
    assert parsed.severity_breakdown["info"] == 3


def test_findings_are_sorted_by_severity_then_title() -> None:
    findings_payload = [
        {
            "finding_id": str(uuid4()),
            "title": "B low",
            "vulnerability_type": "misc",
            "severity": "low",
            "affected_url": "https://example.com/b",
            "is_verified": False,
        },
        {
            "finding_id": str(uuid4()),
            "title": "A critical",
            "vulnerability_type": "rce",
            "severity": "critical",
            "affected_url": "https://example.com/a",
            "is_verified": True,
        },
    ]

    parsed = ParsedScanBuilder().build(
        scan_payload=_scan_payload(),
        findings_payload=findings_payload,
        program_payload=_program_payload(),
        scope_payload=_scope_payload(),
        exploit_chain_refs=[],
        include_evidence_screenshots=False,
    )

    assert parsed.findings[0].title == "A critical"
    assert parsed.findings[1].title == "B low"


def _finding_payload(**overrides) -> dict:
    payload = {
        "finding_id": str(uuid4()),
        "title": "Template finding",
        "vulnerability_type": "misc",
        "severity": "info",
        "affected_url": "https://example.com",
        "description": None,
        "raw_output": {},
    }
    payload.update(overrides)
    return payload


def test_finding_description_prefers_non_blank_description_field() -> None:
    finding = ParsedScanBuilder._build_finding(
        _finding_payload(
            description=" Top level description ",
            raw_output={"info": {"description": "scanner desc", "details": "scanner details"}},
        )
    )
    assert finding.description == "Top level description"


def test_finding_description_falls_back_to_raw_info_description() -> None:
    finding = ParsedScanBuilder._build_finding(
        _finding_payload(
            description="   ",
            raw_output={"info": {"description": " Nuclei description ", "details": "scanner details"}},
        )
    )
    assert finding.description == "Nuclei description"


def test_finding_description_falls_back_to_raw_info_details() -> None:
    finding = ParsedScanBuilder._build_finding(
        _finding_payload(
            description="",
            raw_output={"info": {"description": "   ", "details": " Nuclei details text "}},
        )
    )
    assert finding.description == "Nuclei details text"


def test_finding_description_uses_default_when_all_values_blank() -> None:
    finding = ParsedScanBuilder._build_finding(
        _finding_payload(
            description="   ",
            raw_output={"info": {"description": "", "details": "   "}},
        )
    )
    assert finding.description == "No scanner description provided."
