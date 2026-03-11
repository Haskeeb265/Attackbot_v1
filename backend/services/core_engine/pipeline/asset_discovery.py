import asyncio
import tempfile
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.subprocess_utils import (
    run_tool_streaming,
    run_tool_communicate,
    parse_jsonl,
)
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage1")

STAGE_NUMBER = 1.0
STAGE_NAME = "asset_discovery"


async def run(
    ctx: ScanContext,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredAsset]:
    """
    Stage 1: Discover live assets within scope.
    Returns a list of DiscoveredAsset objects (not yet persisted).
    Never raises — returns partial results on tool failure.
    """
    started_at = datetime.now(timezone.utc)
    assets: list[DiscoveredAsset] = []
    errors: dict[str, str] = {}

    # Collect root domains from in_scope
    root_domains = _extract_root_domains(ctx.scope.in_scope)
    if not root_domains:
        logger.warning("No root domains found in scope — skipping asset discovery",
                       scan_id=ctx.scan_id)
        return assets

    for domain in root_domains:
        try:
            domain_assets = await _discover_domain(
                domain, scope_filter, config
            )
            assets.extend(domain_assets)
        except Exception as e:
            logger.warning("Asset discovery failed for domain",
                           domain=domain, error=str(e))
            errors[domain] = str(e)

    logger.info("Stage 1 complete",
                scan_id=ctx.scan_id,
                assets_found=len(assets),
                errors=len(errors))
    return assets


async def _discover_domain(
    domain: str,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredAsset]:
    """Run the full subfinder → alterx → dnsx → httpx pipeline for one domain."""

    # Step 1: subfinder — passive subdomain enumeration
    subfinder_lines = await run_tool_streaming(
        args=["subfinder", "-d", domain, "-silent", "-all"],
        timeout=config.subfinder_timeout,
        label=f"subfinder[{domain}]",
    )
    subdomains = list({line.strip() for line in subfinder_lines if line.strip()})
    logger.debug("subfinder complete", domain=domain, found=len(subdomains))

    if not subdomains:
        return []

    # Step 2: alterx — permutation generation
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(subdomains))
        subfinder_file = tf.name
    try:
        alterx_stdout, _ = await run_tool_communicate(
            args=["alterx", "-l", subfinder_file, "-silent"],
            timeout=300,
            label=f"alterx[{domain}]",
        )
        permutations = [
            l.strip() for l in alterx_stdout.splitlines() if l.strip()
        ]
    except Exception:
        permutations = []  # alterx failure is non-fatal — continue with subdomains only
    finally:
        os.unlink(subfinder_file)

    all_candidates = list(set(subdomains + permutations))

    # Step 3: dnsx — DNS resolution, filter live hosts only
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(all_candidates))
        candidates_file = tf.name
    try:
        dnsx_stdout, _ = await run_tool_communicate(
            args=["dnsx", "-l", candidates_file, "-silent", "-resp"],
            timeout=config.dnsx_timeout,
            label=f"dnsx[{domain}]",
        )
        live_domains = [l.strip() for l in dnsx_stdout.splitlines() if l.strip()]
    finally:
        os.unlink(candidates_file)

    if not live_domains:
        return []

    # Step 4: httpx — HTTP probing + tech detection
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(live_domains))
        live_file = tf.name
    try:
        httpx_stdout, _ = await run_tool_communicate(
            args=[
                "httpx", "-l", live_file, "-json", "-silent",
                "-tech-detect", "-status-code", "-title",
            ],
            timeout=config.httpx_timeout,
            label=f"httpx[{domain}]",
        )
    finally:
        os.unlink(live_file)

    # Parse httpx JSON output into DiscoveredAsset objects
    assets: list[DiscoveredAsset] = []
    for entry in parse_jsonl(httpx_stdout):
        url = entry.get("url", "")
        if not url:
            continue
        if not scope_filter.is_in_scope(url):
            continue
        assets.append(DiscoveredAsset(
            asset_type="subdomain",
            value=url,
            http_status=entry.get("status_code"),
            technology_stack={"technologies": entry.get("tech", [])},
            waf_detected=_extract_waf(entry),
        ))

    return assets


def _extract_root_domains(in_scope: list[str]) -> list[str]:
    """Extract bare root domains from scope entries like '*.example.com' or 'example.com'."""
    domains = set()
    for rule in in_scope:
        # Strip wildcard, URL scheme, path
        clean = rule.lstrip("*.")
        if "://" in clean:
            parsed = urlparse(clean)
            clean = parsed.hostname or ""
        clean = clean.split("/")[0]
        if clean:
            domains.add(clean)
    return list(domains)


def _extract_waf(httpx_entry: dict) -> str | None:
    """Extract WAF name from httpx tech detection output if present."""
    for tech in httpx_entry.get("tech", []):
        if "waf" in tech.lower() or "cloudflare" in tech.lower() or "akamai" in tech.lower():
            return tech
    return None