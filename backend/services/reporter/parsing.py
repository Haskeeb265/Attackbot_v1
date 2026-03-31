from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.services.reporter.models import (
    ExploitChain,
    ParsedFinding,
    ParsedScan,
    ProgramInfo,
    ScopeEntry,
)
from backend.shared.logging import get_logger

log = get_logger(__name__)

_SEVERITY_ALIASES: dict[str, str] = {
    "informational": "info",
}
_SEVERITY_RANK: dict[str, int] = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


def _normalize_severity_key(key: str) -> str:
    return _SEVERITY_ALIASES.get(key.lower(), key.lower())


def _normalize_severity_breakdown(raw: dict[str, Any]) -> dict[str, int]:
    canonical = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for key, count in raw.items():
        normalized_key = _normalize_severity_key(str(key))
        if normalized_key in canonical:
            try:
                canonical[normalized_key] += int(count)
            except (TypeError, ValueError):
                continue
    return canonical


class ParsedScanBuilder:
    def build(
        self,
        scan_payload: dict,
        findings_payload: list[dict],
        program_payload: dict,
        scope_payload: dict,
        exploit_chain_refs: list[dict],
        include_evidence_screenshots: bool,
    ) -> ParsedScan:
        program = ProgramInfo(
            program_id=UUID(str(program_payload["program_id"])),
            platform=str(program_payload.get("platform") or "unknown"),
            handle=str(program_payload.get("handle") or "unknown"),
            name=str(program_payload.get("name") or "unknown"),
            url=program_payload.get("url"),
            bounty_type=program_payload.get("bounty_type"),
            max_bounty=program_payload.get("max_bounty"),
            is_active=bool(program_payload.get("is_active", True)),
        )

        scope_entries = [
            ScopeEntry(
                scope_type=str(item.get("scope_type") or "in_scope"),
                asset_type=str(item.get("asset_type") or "unknown"),
                value=str(item.get("value") or ""),
                notes=item.get("notes"),
            )
            for item in scope_payload.get("scope", [])
            if item.get("value")
        ]

        findings = [self._build_finding(item) for item in findings_payload]
        findings.sort(
            key=lambda finding: (
                -_SEVERITY_RANK.get(finding.severity, 0),
                finding.title.lower(),
                finding.affected_url.lower(),
            )
        )

        chains = [
            ExploitChain(
                chain_id=UUID(str(chain["chain_id"])),
                chain_name=str(chain.get("chain_name") or "Unnamed chain"),
                combined_severity=str(chain.get("combined_severity") or "medium").lower(),
                step_count=int(chain.get("step_count") or 0),
                description=chain.get("description"),
            )
            for chain in exploit_chain_refs
        ]

        if not findings and chains:
            log.warning(
                "reporter_exploit_chains_ignored_without_findings",
                chain_count=len(chains),
                scan_id=str(scan_payload.get("scan_id")),
            )
            chains = []

        return ParsedScan(
            scan_id=UUID(str(scan_payload["scan_id"])),
            status=str(scan_payload.get("status") or "completed"),
            partial=str(scan_payload.get("status") or "").lower() == "partial",
            finding_count=int(scan_payload.get("finding_count") or len(findings)),
            verified_count=sum(1 for finding in findings if finding.is_verified),
            severity_breakdown=_normalize_severity_breakdown(
                dict(scan_payload.get("severity_breakdown") or {})
            ),
            include_evidence_screenshots=include_evidence_screenshots,
            program=program,
            scope=scope_entries,
            findings=findings,
            exploit_chains=chains,
        )

    @staticmethod
    def _build_finding(item: dict[str, Any]) -> ParsedFinding:
        severity = _normalize_severity_key(str(item.get("severity") or "info"))
        if severity not in _SEVERITY_RANK:
            severity = "info"

        return ParsedFinding(
            finding_id=UUID(str(item["finding_id"])),
            title=str(item.get("title") or "Untitled finding"),
            vulnerability_type=str(item.get("vulnerability_type") or "unknown"),
            severity=severity,
            cvss_score=float(item["cvss_score"]) if item.get("cvss_score") is not None else None,
            cvss_vector=item.get("cvss_vector"),
            affected_url=str(item.get("affected_url") or ""),
            affected_parameter=item.get("affected_parameter"),
            description=str(item.get("description") or ""),
            reproduction_steps=item.get("reproduction_steps"),
            source=item.get("source"),
            is_verified=bool(item.get("is_verified", False)),
            raw_output=item.get("raw_output"),
        )
