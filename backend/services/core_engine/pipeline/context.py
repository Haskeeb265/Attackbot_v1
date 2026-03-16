from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class ScopeDefinition:
    """Parsed scope from the scan.jobs message."""
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)


@dataclass
class FeatureFlags:
    """Which optional scanning modules are enabled for this scan."""
    sqli: bool = False
    ssrf: bool = False
    crlf: bool = False
    nuclei: bool = False
    browser_session: bool = False
    api_fuzzing: bool = False
    ai_hypothesis: bool = False


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