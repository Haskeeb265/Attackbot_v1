import hashlib
from urllib.parse import urlparse, parse_qsl, urlencode

from backend.services.core_engine.models import FindingCandidate


def normalize_url(url: str) -> str:
    """
    Normalize a URL for stable deduplication.
    Lowercases scheme+host, sorts query parameters alphabetically.
    Without this: ?b=2&a=1 and ?a=1&b=2 produce different hashes for the same endpoint.
    """
    try:
        parsed = urlparse(url.lower())
        sorted_query = urlencode(sorted(parse_qsl(parsed.query)))
        normalized = parsed._replace(query=sorted_query)
        return normalized.geturl()
    except Exception:
        return url.lower()


def compute_dedup_hash(candidate: FindingCandidate) -> str:
    """
    Produce a stable, content-based hash for a finding candidate.

    Rules:
    - Must NOT include scan_id, timestamps, evidence paths — those change between scans
    - Must include: vuln type, normalized URL, parameter, truncated payload
    - Payload is truncated to 100 chars — nuclei payloads vary slightly across runs

    Two candidates with the same vuln type + URL + parameter + payload prefix
    are considered the same finding.
    """
    components = "|".join([
        candidate.vulnerability_type.lower(),
        normalize_url(candidate.affected_url),
        (candidate.affected_parameter or "").lower(),
        (candidate.payload or "")[:100],
    ])
    return hashlib.sha256(components.encode()).hexdigest()