from dataclasses import dataclass, field
from typing import Any

from backend.shared.schemas.scan_jobs import (
    FeatureFlags as SharedFeatureFlags,
    ScopeDefinition as SharedScopeDefinition,
)


@dataclass
class ScopeDefinition:
    """Parsed scope from the scan.jobs message."""
    in_scope: list[Any] = field(default_factory=list)
    out_of_scope: list[Any] = field(default_factory=list)

    @classmethod
    def from_shared(cls, scope: SharedScopeDefinition) -> "ScopeDefinition":
        data = scope.model_dump(mode="python")
        return cls(
            in_scope=data.get("in_scope", []),
            out_of_scope=data.get("out_of_scope", []),
        )


@dataclass
class FeatureFlags:
    """Which optional scanning modules are enabled for this scan."""
    asset_discovery: bool = True
    fingerprinting: bool = True
    enumeration: bool = True
    nuclei: bool = True
    xss: bool = True
    cors: bool = True
    secret_js: bool = True
    browser_session: bool = True
    api_fuzzing: bool = True
    sqli: bool = False
    ssrf: bool = False
    crlf: bool = False
    takeover: bool = False
    secret_repo: bool = False
    scenario_runner: bool = False
    ai_hypothesis: bool = False
    idor_verification: bool = False

    @classmethod
    def from_shared(cls, flags: SharedFeatureFlags) -> "FeatureFlags":
        return cls(**flags.model_dump(mode="python"))


@dataclass
class ScanContext:
    """
    Immutable configuration bundle for a scan run.
    Created once in scan_task.py from the queue message.
    Passed down to every pipeline stage — stages must not modify it.
    """
    scan_id: str
    program_id: str
    scope: ScopeDefinition
    feature_flags: FeatureFlags
    priority: int = 1
    # Populated after Stage 1 completes — available to Stages 2+
    live_assets: list[str] = field(default_factory=list)
    # Populated after Stage 3 completes — available to Stages 4+
    js_asset_ids: list[str] = field(default_factory=list)
