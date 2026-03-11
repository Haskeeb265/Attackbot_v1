import tempfile
import os
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import FindingCandidate, DiscoveredAsset
from backend.services.core_engine.subprocess_utils import (
    run_tool_communicate, parse_jsonl
)
from backend.services.core_engine.cvss import nuclei_severity, severity_to_cvss
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage4")

STAGE_NUMBER = 4.0
STAGE_NAME = "nuclei_scan"


async def run(
    ctx: ScanContext,
    assets: list[DiscoveredAsset],
    scope_filter: ScopeFilter,
    config,
) -> list[FindingCandidate]:
    """
    Stage 4: Run nuclei against all live assets.
    Only unauthenticated templates in M3. Browser-based templates are skipped
    until M5 (browser_session feature flag).
    """
    targets = scope_filter.filter_targets([a.value for a in assets])
    if not targets:
        logger.warning("No in-scope targets for nuclei", scan_id=ctx.scan_id)
        return []

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(targets))
        targets_file = tf.name

    try:
        stdout, _ = await run_tool_communicate(
            args=[
                "nuclei",
                "-l", targets_file,
                "-json",
                "-silent",
                "-rate-limit", str(config.nuclei_rate_limit),
                "-bulk-size", str(config.nuclei_bulk_size),
                "-concurrency", str(config.nuclei_concurrency),
                # Exclude templates that require browser — M5 handles those
                "-exclude-tags", "headless",
            ],
            timeout=config.nuclei_timeout,
            label="nuclei",
        )
    finally:
        os.unlink(targets_file)

    candidates: list[FindingCandidate] = []
    for entry in parse_jsonl(stdout):
        matched_url = entry.get("matched-at") or entry.get("host", "")
        if not matched_url or not scope_filter.is_in_scope(matched_url):
            continue

        raw_severity = entry.get("info", {}).get("severity", "info")
        severity = nuclei_severity(raw_severity)

        candidates.append(FindingCandidate(
            vulnerability_type=f"nuclei_{entry.get('template-id', 'unknown').replace('-', '_')}",
            title=entry.get("info", {}).get("name", entry.get("template-id", "Unknown")),
            severity=severity,
            affected_url=matched_url,
            description=entry.get("info", {}).get("description", ""),
            source="nuclei",
            payload=entry.get("matched-at"),
            cvss_score=severity_to_cvss(severity),
            raw_output=entry,
        ))

    logger.info("Stage 4 complete",
                scan_id=ctx.scan_id,
                findings=len(candidates))
    return candidates