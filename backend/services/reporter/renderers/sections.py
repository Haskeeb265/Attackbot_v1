from __future__ import annotations

from backend.services.reporter.models import ParsedScan, ReproductionPackDraft
from backend.services.reporter.renderers.base import EvidenceImageEntry, RenderPlan

_SEVERITY_RANK: dict[str, int] = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}

UNVERIFIED_CAVEAT = (
    "Verification note: This report may include unverified findings from the current "
    "scan pipeline. Evidence-backed verification gating is scheduled for M7."
)
NO_FINDINGS_STATEMENT = (
    "No findings were produced for this scan. This report reflects the completed scan "
    "state and the scope reviewed at generation time. It should not be interpreted as "
    "proof of absence of vulnerabilities beyond the tested coverage captured below."
)


def build_render_plan(
    parsed_scan: ParsedScan,
    packs: list[ReproductionPackDraft],
    include_raw_http_appendix: bool,
) -> RenderPlan:
    if parsed_scan.is_clean():
        return _build_clean_render_plan(parsed_scan)
    return _build_findings_render_plan(parsed_scan, packs, include_raw_http_appendix)


def _build_clean_render_plan(parsed_scan: ParsedScan) -> RenderPlan:
    lines: list[str] = [
        "# AttackBot Security Report",
        f"Program: {parsed_scan.program.name} ({parsed_scan.program.handle})",
        f"Scan ID: {parsed_scan.scan_id}",
        "## Executive Summary",
        "No findings were identified in this scan run.",
        "## Scope Overview",
    ]

    lines.extend(_render_scope_lines(parsed_scan))
    lines.extend(
        [
            "## No Findings Statement",
            NO_FINDINGS_STATEMENT,
            "## Coverage Notes",
            "Coverage reflects discovered and in-scope assets available at scan time.",
            "## Appendix - Scan Metadata",
            f"Scan status: {parsed_scan.status}",
            f"Severity breakdown: {parsed_scan.severity_breakdown}",
        ]
    )
    return RenderPlan(lines=lines)


def _build_findings_render_plan(
    parsed_scan: ParsedScan,
    packs: list[ReproductionPackDraft],
    include_raw_http_appendix: bool,
) -> RenderPlan:
    lines: list[str] = [
        "# AttackBot Security Report",
        f"Program: {parsed_scan.program.name} ({parsed_scan.program.handle})",
        f"Scan ID: {parsed_scan.scan_id}",
        "## Executive Summary",
        (
            f"Findings: {parsed_scan.finding_count} total "
            f"({parsed_scan.verified_count} verified / "
            f"{parsed_scan.finding_count - parsed_scan.verified_count} unverified)."
        ),
    ]

    if any(not finding.is_verified for finding in parsed_scan.findings):
        lines.append(UNVERIFIED_CAVEAT)

    lines.extend(["## Scope Overview"])
    lines.extend(_render_scope_lines(parsed_scan))

    sorted_findings = sorted(
        parsed_scan.findings,
        key=lambda finding: (
            -_SEVERITY_RANK.get(finding.severity, 0),
            finding.title.lower(),
            finding.affected_url.lower(),
        ),
    )

    lines.extend(
        [
            "## Findings Table",
            "Severity | Verification Status | Title | Affected URL",
        ]
    )
    for finding in sorted_findings:
        verification = "verified" if finding.is_verified else "unverified"
        lines.append(
            f"{finding.severity} | {verification} | {finding.title} | {finding.affected_url}"
        )

    packs_by_finding = {str(pack.finding_id): pack for pack in packs}
    evidence_images: list[EvidenceImageEntry] = []

    lines.append("## Per-Finding Detail")
    for finding in sorted_findings:
        verification = "verified" if finding.is_verified else "unverified"
        lines.extend(
            [
                f"### Finding: {finding.title}",
                f"Severity: {finding.severity}",
                f"Verification Status: {verification}",
                f"Affected URL: {finding.affected_url}",
                f"Description: {finding.description}",
            ]
        )
        pack = packs_by_finding.get(str(finding.finding_id))
        if pack is not None:
            lines.append(f"Reproduction note: {pack.notes or 'N/A'}")

    if parsed_scan.exploit_chains:
        lines.append("## Exploit Chains")
        for chain in parsed_scan.exploit_chains:
            lines.append(
                f"{chain.chain_name} | severity={chain.combined_severity} | steps={chain.step_count}"
            )
    else:
        lines.extend(
            [
                "## Chain Availability Note",
                "Exploit chain details are unavailable in M4 and will expand in M8.",
            ]
        )

    lines.append("## Appendix - Reproduction Packs")
    for pack in packs:
        lines.extend(
            [
                f"### Reproduction Pack: {pack.finding_id}",
                f"curl: {pack.curl_command}",
                f"notes: {pack.notes or 'N/A'}",
            ]
        )

    lines.append("## Appendix - Evidence Notes")
    if not parsed_scan.include_evidence_screenshots:
        lines.append("Evidence screenshots were disabled for this report generation request.")
    else:
        for finding in sorted_findings:
            lines.append(f"### Evidence for: {finding.title}")
            if not finding.evidence:
                lines.append("No evidence artifacts were attached to this finding.")
                continue
            for artifact in finding.evidence:
                if artifact.exists and artifact.local_tmp_path:
                    lines.append(
                        f"[Evidence screenshot attached - {artifact.artifact_type}]"
                    )
                    evidence_images.append(
                        EvidenceImageEntry(
                            finding_title=finding.title,
                            artifact_type=artifact.artifact_type,
                            local_tmp_path=artifact.local_tmp_path,
                        )
                    )
                else:
                    lines.append(
                        f"[Evidence screenshot unavailable - {artifact.artifact_type}]"
                    )

    if include_raw_http_appendix:
        lines.append("## Appendix - Raw HTTP Requests")
        for pack in packs:
            lines.extend(
                [
                    f"### HTTP Raw: {pack.finding_id}",
                    pack.http_request_raw,
                ]
            )

    return RenderPlan(lines=lines, evidence_images=evidence_images)


def _render_scope_lines(parsed_scan: ParsedScan) -> list[str]:
    lines: list[str] = []
    if not parsed_scan.scope:
        return ["No scope entries were returned for this scan."]

    for entry in parsed_scan.scope:
        lines.append(f"{entry.scope_type} | {entry.asset_type} | {entry.value}")
    return lines
