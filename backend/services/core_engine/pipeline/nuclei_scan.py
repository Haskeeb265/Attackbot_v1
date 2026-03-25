import os
import re
import tempfile

from backend.services.core_engine.cvss import nuclei_severity, severity_to_cvss
from backend.services.core_engine.models import DiscoveredAsset, FindingCandidate
from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.services.core_engine.subprocess_utils import parse_jsonl, run_tool_communicate
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage4")

STAGE_NUMBER = 4.0
STAGE_NAME = "nuclei_scan"

_RETURN_CODE_PATTERN = re.compile(r"exited with code\s+(\d+)")


def _effective_timeout(config, timeout_seconds: int) -> int:
    scale_fn = getattr(config, "scaled_timeout", None)
    timeout = int(timeout_seconds)
    if callable(scale_fn):
        try:
            return int(scale_fn(timeout))
        except Exception:
            return timeout
    return timeout


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
    targets = scope_filter.filter_targets([asset.value for asset in assets])
    if not targets:
        logger.warning("No in-scope targets for nuclei", scan_id=ctx.scan_id)
        return []

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(targets))
        targets_file = tf.name

    try:
        try:
            stdout, _ = await run_tool_communicate(
                args=[
                    "nuclei",
                    "-l",
                    targets_file,
                    "-jsonl",
                    "-silent",
                    "-rate-limit",
                    str(config.nuclei_rate_limit),
                    "-bulk-size",
                    str(config.nuclei_bulk_size),
                    "-concurrency",
                    str(config.nuclei_concurrency),
                    # Exclude templates that require browser - M5 handles those.
                    "-exclude-tags",
                    "headless",
                ],
                timeout=_effective_timeout(
                    config, int(getattr(config, "nuclei_timeout", 3600))
                ),
                label="nuclei",
            )
        except Exception as exc:
            return_code = _extract_return_code(exc)
            if return_code == 2:
                logger.error(
                    "nuclei_startup_failure_detected",
                    scan_id=ctx.scan_id,
                    return_code=2,
                    reason_bucket=_classify_exit_code_2_reason(targets, config, str(exc)),
                    target_count=len(targets),
                    sample_targets=targets[:5],
                    error=str(exc),
                )
            else:
                logger.error(
                    "nuclei_subprocess_failed",
                    scan_id=ctx.scan_id,
                    return_code=return_code,
                    target_count=len(targets),
                    sample_targets=targets[:5],
                    error=str(exc),
                )
            raise
    finally:
        os.unlink(targets_file)

    candidates: list[FindingCandidate] = []
    for entry in parse_jsonl(stdout):
        matched_url = entry.get("matched-at") or entry.get("host", "")
        if not matched_url or not scope_filter.is_in_scope(matched_url):
            continue

        raw_severity = entry.get("info", {}).get("severity", "info")
        severity = nuclei_severity(raw_severity)

        candidates.append(
            FindingCandidate(
                vulnerability_type=f"nuclei_{entry.get('template-id', 'unknown').replace('-', '_')}",
                title=entry.get("info", {}).get("name", entry.get("template-id", "Unknown")),
                severity=severity,
                affected_url=matched_url,
                description=entry.get("info", {}).get("description", ""),
                source="nuclei",
                payload=entry.get("matched-at"),
                cvss_score=severity_to_cvss(severity),
                raw_output=entry,
            )
        )

    logger.info("Stage 4 complete", scan_id=ctx.scan_id, findings=len(candidates))
    return candidates


def _extract_return_code(exc: Exception) -> int | None:
    for attr_name in ("returncode", "exit_code", "code"):
        code = getattr(exc, attr_name, None)
        if isinstance(code, int):
            return code

    match = _RETURN_CODE_PATTERN.search(str(exc))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _classify_exit_code_2_reason(targets: list[str], config, error_text: str) -> str:
    templates_path = str(getattr(config, "nuclei_templates", "") or "").strip()
    lowered_error = error_text.lower()

    if templates_path:
        return "templates_configured_verify_path_or_contents"
    if "template" in lowered_error:
        return "templates_missing_or_unreadable"
    if any("host.docker.internal" in target for target in targets):
        return "target_resolution_or_parsing"
    if not targets:
        return "empty_target_list"
    return "nuclei_startup_initialization_failure"
