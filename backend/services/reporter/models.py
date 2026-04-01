from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

Severity = Literal["critical", "high", "medium", "low", "info"]


@dataclass
class ProgramInfo:
    program_id: UUID
    platform: str
    handle: str
    name: str
    url: str | None
    bounty_type: str | None
    max_bounty: int | None
    is_active: bool


@dataclass
class ScopeEntry:
    scope_type: str
    asset_type: str
    value: str
    notes: str | None = None


@dataclass
class EvidenceArtifact:
    artifact_type: str
    storage_path: str | None
    description: str | None = None
    exists: bool = False
    local_tmp_path: str | None = None


@dataclass
class ParsedFinding:
    finding_id: UUID
    title: str
    vulnerability_type: str
    severity: Severity
    cvss_score: float | None
    cvss_vector: str | None
    affected_url: str
    affected_parameter: str | None
    description: str
    reproduction_steps: str | None
    source: str | None
    is_verified: bool
    raw_output: dict | None
    evidence: list[EvidenceArtifact] = field(default_factory=list)


@dataclass
class ExploitChain:
    chain_id: UUID
    chain_name: str
    combined_severity: str
    step_count: int
    description: str | None = None


@dataclass
class ReproductionPackDraft:
    finding_id: UUID
    curl_command: str
    http_request_raw: str
    browser_steps: str
    notes: str | None = None
    is_fallback: bool = False


@dataclass
class ParsedScan:
    scan_id: UUID
    status: str
    partial: bool
    finding_count: int
    verified_count: int
    severity_breakdown: dict[str, int]
    include_evidence_screenshots: bool
    program: ProgramInfo
    scope: list[ScopeEntry]
    findings: list[ParsedFinding]
    exploit_chains: list[ExploitChain] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.findings) == 0
