import tempfile
import os
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.subprocess_utils import (
    run_tool_communicate, parse_jsonl
)
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage2")

STAGE_NUMBER = 2.0
STAGE_NAME = "fingerprinting"


async def run(
    ctx: ScanContext,
    assets: list[DiscoveredAsset],
    config,
) -> list[DiscoveredAsset]:
    """
    Stage 2: Enrich existing assets with detailed tech stack and WAF info.
    Runs httpx with extended fingerprinting options on the already-discovered live assets.
    Updates assets in-place and returns them.
    """
    if not assets:
        return assets

    targets = [a.value for a in assets]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(targets))
        targets_file = tf.name

    try:
        stdout, _ = await run_tool_communicate(
            args=[
                "httpx", "-l", targets_file, "-json", "-silent",
                "-tech-detect", "-status-code", "-title",
                "-no-color",
            ],
            timeout=config.httpx_timeout,
            label="httpx_fingerprint",
        )
    finally:
        os.unlink(targets_file)

    # Build lookup by URL
    fingerprints = {e["url"]: e for e in parse_jsonl(stdout) if "url" in e}

    for asset in assets:
        fp = fingerprints.get(asset.value)
        if not fp:
            continue
        asset.http_status = fp.get("status_code", asset.http_status)
        asset.technology_stack = {
            "technologies": fp.get("tech", []),
            "title": fp.get("title", ""),
            "content_type": fp.get("content_type", ""),
            "server": fp.get("webserver", ""),
        }
        # Re-check WAF from enriched output
        if not asset.waf_detected:
            for tech in fp.get("tech", []):
                if any(w in tech.lower() for w in ["cloudflare", "akamai", "waf", "f5", "sucuri"]):
                    asset.waf_detected = tech
                    break

    logger.info("Stage 2 complete",
                scan_id=ctx.scan_id,
                assets_enriched=len(fingerprints))
    return assets