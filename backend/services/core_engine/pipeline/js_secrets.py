import re
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import FindingCandidate, DiscoveredJsAsset
from backend.shared.storage import download_bytes
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage6")

STAGE_NUMBER = 6.0
STAGE_NAME = "js_secrets"

# Secret patterns — each entry: (regex, label, severity)
SECRET_PATTERNS: list[tuple[str, str, str]] = [
    (r'AIza[0-9A-Za-z\-_]{35}', "Google API Key", "high"),
    (r'AAAA[A-Za-z0-9_\-]{7}:[A-Za-z0-9_\-]{140}', "Firebase Server Key", "high"),
    (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key", "critical"),
    (r'xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9a-fA-F]{24}', "Slack Token", "high"),
    (r'(?i)(api[_\-]?key|apikey|api[_\-]?secret)\s*[=:]\s*["\'"]([A-Za-z0-9\-_]{20,})["\']',
     "Generic API Key Assignment", "medium"),
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'"]([^"\']{8,})["\']',
     "Hardcoded Password", "high"),
    (r'(?i)(secret[_\-]?key|private[_\-]?key)\s*[=:]\s*["\'"]([A-Za-z0-9\-_+/=]{20,})["\']',
     "Hardcoded Secret Key", "high"),
    (r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}',
     "JWT Token", "medium"),
    (r'-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----', "Private Key", "critical"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub Personal Access Token", "critical"),
    (r'(?i)aws[_\-]?access[_\-]?key[_\-]?id\s*[=:]\s*["\'"]?(AKIA[0-9A-Z]{16})["\'"]?',
     "AWS Access Key ID", "critical"),
    (r'(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*["\'"]?([A-Za-z0-9/+=]{40})["\'"]?',
     "AWS Secret Access Key", "critical"),
]

_COMPILED = [(re.compile(p), label, sev) for p, label, sev in SECRET_PATTERNS]


async def run(
    ctx: ScanContext,
    js_assets: list[DiscoveredJsAsset],
) -> list[FindingCandidate]:
    """
    Stage 6: Regex-based secret detection in downloaded JS files.
    Reads each JS file from MinIO, applies patterns, produces FindingCandidates.
    """
    candidates: list[FindingCandidate] = []

    for js_asset in js_assets:
        try:
            content_bytes = download_bytes(
                bucket="js-assets",
                object_name=js_asset.storage_path.removeprefix("js-assets/"),
            )
            content = content_bytes.decode(errors="replace")
            findings = _scan_content(content, js_asset.url)
            candidates.extend(findings)
        except Exception as e:
            logger.warning("JS secret scan failed",
                           url=js_asset.url, error=str(e))

    logger.info("Stage 6 complete",
                scan_id=ctx.scan_id,
                js_files_scanned=len(js_assets),
                secrets_found=len(candidates))
    return candidates


def _scan_content(content: str, source_url: str) -> list[FindingCandidate]:
    findings = []
    for pattern, label, severity in _COMPILED:
        matches = pattern.findall(content)
        if not matches:
            continue
        # Take first match only — don't emit one finding per occurrence
        match_preview = str(matches[0])[:80]
        findings.append(FindingCandidate(
            vulnerability_type="js_secret",
            title=f"{label} found in JavaScript",
            severity=severity,
            affected_url=source_url,
            description=(
                f"{label} detected in JavaScript file '{source_url}'. "
                f"Preview: {match_preview}..."
            ),
            source="js_secrets",
            payload=match_preview,
            reproduction_steps=(
                f"Fetch: {source_url}\n"
                f"Search for pattern matching: {label}\n"
                f"Matched: {match_preview}"
            ),
        ))
    return findings
