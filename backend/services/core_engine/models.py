from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
import uuid


@dataclass
class DiscoveredAsset:
    """A live host discovered by Stage 1."""
    asset_type: str          # "subdomain" | "ip" | "url"
    value: str               # e.g. "api.example.com" or "https://api.example.com"
    http_status: Optional[int] = None
    technology_stack: Optional[dict] = None
    waf_detected: Optional[str] = None
    asset_id: Optional[UUID] = None  # set after DB persist


@dataclass
class DiscoveredEndpoint:
    """A single endpoint discovered by Stage 3."""
    asset_id: UUID
    method: str              # "GET" | "POST" etc.
    path: str                # "/api/v1/users"
    full_url: str
    response_code: Optional[int] = None
    content_type: Optional[str] = None
    parameters: Optional[dict] = None
    headers: Optional[dict] = None
    requires_auth: bool = False
    endpoint_id: Optional[UUID] = None  # set after DB persist


@dataclass
class DiscoveredJsAsset:
    """A downloaded JS file stored in MinIO."""
    scan_id: UUID
    url: str
    storage_path: str
    content_hash: str
    size_bytes: int
    js_asset_id: Optional[UUID] = None  # set after DB persist


@dataclass
class FindingCandidate:
    """
    A raw, unverified vulnerability candidate produced by any pipeline stage.
    These are deduplicated and persisted by the aggregator.
    """
    vulnerability_type: str  # "xss" | "cors" | "nuclei_finding" | "js_secret" etc.
    title: str
    severity: str            # "critical" | "high" | "medium" | "low" | "info"
    affected_url: str
    description: str
    source: str              # which stage produced this
    affected_parameter: Optional[str] = None
    payload: Optional[str] = None
    reproduction_steps: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    raw_output: Optional[dict] = None


@dataclass
class ScanResult:
    """Aggregated output of the entire pipeline. Passed to aggregator."""
    assets: list[DiscoveredAsset] = field(default_factory=list)
    endpoints: list[DiscoveredEndpoint] = field(default_factory=list)
    js_assets: list[DiscoveredJsAsset] = field(default_factory=list)
    finding_candidates: list[FindingCandidate] = field(default_factory=list)
    stage_errors: dict[str, str] = field(default_factory=dict)  # stage_name → error