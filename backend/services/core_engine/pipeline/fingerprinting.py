import tempfile
import os
from numbers import Real
from urllib.parse import urlparse

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.pipeline.waf_utils import detect_waf_technology
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
            timeout=_effective_timeout(config, int(getattr(config, "httpx_timeout", 600))),
            label="httpx_fingerprint",
        )
    finally:
        os.unlink(targets_file)

    # Build lookup by normalized input/url so redirects and trailing-slash
    # differences do not break enrichment mapping.
    fingerprints: dict[str, dict] = {}
    for entry in parse_jsonl(stdout):
        if not isinstance(entry, dict):
            continue
        input_key = _normalize_url_for_lookup(str(entry.get("input") or ""))
        url_key = _normalize_url_for_lookup(str(entry.get("url") or ""))
        if input_key and input_key not in fingerprints:
            fingerprints[input_key] = entry
        if url_key and url_key not in fingerprints:
            fingerprints[url_key] = entry

    enriched_assets = 0
    for asset in assets:
        lookup_key = _normalize_url_for_lookup(asset.value)
        fp = fingerprints.get(lookup_key)
        if not fp:
            continue
        enriched_assets += 1
        asset.http_status = fp.get("status_code", asset.http_status)
        asset.technology_stack = {
            "technologies": fp.get("tech", []),
            "title": fp.get("title", ""),
            "content_type": fp.get("content_type", ""),
            "server": fp.get("webserver", ""),
        }
        if not asset.waf_detected:
            asset.waf_detected = detect_waf_technology(fp.get("tech", []))

    logger.info("Stage 2 complete",
                scan_id=ctx.scan_id,
                assets_enriched=enriched_assets)
    return assets


def _effective_timeout(config, base_timeout: int) -> int:
    scale_fn = getattr(config, "scaled_timeout", None)
    if callable(scale_fn):
        try:
            scaled = scale_fn(base_timeout)
            if isinstance(scaled, Real):
                return int(scaled)
        except Exception:
            pass
    return int(base_timeout)


def _normalize_url_for_lookup(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    if not scheme or not host:
        return raw.rstrip("/").lower()

    if parsed.port is None:
        port_part = ""
    else:
        default_port = (scheme == "http" and parsed.port == 80) or (
            scheme == "https" and parsed.port == 443
        )
        port_part = "" if default_port else f":{parsed.port}"

    path = (parsed.path or "").rstrip("/")
    normalized = f"{scheme}://{host}{port_part}{path}"
    if parsed.query:
        normalized = f"{normalized}?{parsed.query}"
    return normalized
