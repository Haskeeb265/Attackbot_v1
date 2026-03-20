import asyncio
import tempfile
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.subprocess_utils import (
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

    # Step 1: subfinder — passive subdomain enumeration (file output to avoid non-TTY buffering)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        subfinder_out = tf.name
    try:
        await run_tool_communicate(
            args=[
                "subfinder", "-d", domain, "-all",
                "-pc", "/app/subfinder-config/provider-config.yaml",
                "-timeout", "30",
                "-o", subfinder_out,
            ],
            timeout=config.subfinder_timeout,
            label=f"subfinder[{domain}]",
        )
        with open(subfinder_out) as f:
            subfinder_lines = f.read().splitlines()
    finally:
        os.unlink(subfinder_out)
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
        live_domains = [
            l.strip().split()[0]   # extract just the domain, strip " [1.2.3.4]" suffix
            for l in dnsx_stdout.splitlines() if l.strip()
        ]

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
        if entry.get("failed"):
            continue
        url = _normalize_httpx_url(entry)
        if not url:
            continue
        if not scope_filter.is_in_scope(url):
            continue
        assets.append(DiscoveredAsset(
            asset_type="subdomain",
            value=url,
            http_status=entry.get("status_code"),
            technology_stack={"technologies": [t.get("name", str(t)) if isinstance(t, dict) else str(t)
            for t in entry.get("tech", [])]
            },
            waf_detected=_extract_waf(entry),
        ))

    return assets


def _normalize_httpx_url(entry: dict) -> str:
    """Extract URL string from httpx JSON entry; handles string/dict 'url' and 'input' fallback."""
    url = entry.get("url") or entry.get("input") or ""
    if isinstance(url, dict):
        url = url.get("url") or url.get("host") or ""
    return str(url).strip() if url else ""


def _extract_root_domains(in_scope: list) -> list[str]:
    """
    Extract bare root domains from scope entries.
    Only processes domain and wildcard_domain asset types.
    Skips: url, ip_range, mobile_app, api — subfinder can't use these.
    """
    DOMAIN_TYPES = {"domain", "wildcard_domain"}
    domains = set()
    for rule in in_scope:
        if isinstance(rule, dict):
            asset_type = rule.get("asset_type", "")
            raw = rule.get("value", "")
        elif hasattr(rule, "value"):
            asset_type = getattr(rule, "asset_type", "")
            raw = getattr(rule, "value", "")
        else:
            # plain string — no type info, attempt to use it
            asset_type = "domain"
            raw = rule

        if asset_type not in DOMAIN_TYPES:
            continue

        clean = raw.lstrip("*.").split("/")[0].strip()
        if clean and "." in clean:
            domains.add(clean)

    return list(domains)


def _extract_waf(httpx_entry: dict) -> str | None:
    """Extract WAF name from httpx tech detection output if present."""
    for tech in httpx_entry.get("tech", []):
        name = tech.get("name", "") if isinstance(tech, dict) else str(tech)
        if "waf" in name.lower() or "cloudflare" in name.lower() or "akamai" in name.lower():
            return name
    return None
