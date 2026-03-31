from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvidenceImageEntry:
    finding_title: str
    artifact_type: str
    local_tmp_path: str


@dataclass
class RenderPlan:
    lines: list[str]
    evidence_images: list[EvidenceImageEntry] = field(default_factory=list)
