import os
import tempfile
from numbers import Real
from urllib.parse import urlparse

from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.services.core_engine.pipeline.waf_utils import detect_waf_technology
from backend.services.core_engine.subprocess_utils import parse_jsonl, run_tool_communicate
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage1")

STAGE_NUMBER = 1.0
STAGE_NAME = "asset_discovery"

_DOMAIN_TYPES = {"domain", "wildcard_domain"}
_NON_WEB_SCOPE_TYPES = {"mobile_app", "api", "ip_range"}
_HTTP_SCHEMES = {"http", "https"}


async def run(
    ctx: ScanContext,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredAsset]:
    """
    Stage 1: Discover live assets within scope.

    Seed-first behavior:
    - Domain and wildcard_domain rules are always seed candidates.
    - URL rules are seed candidates only when HTTP(S) and domain-led by
      in-scope domain/wildcard rules.
    - Explicit in-scope domain/url targets are also probed directly so
      narrow scope entries are not lost when passive enumeration is sparse.
    """
    assets: list[DiscoveredAsset] = []
    errors: dict[str, str] = {}
    seed_domains, skipped_scope_counts = _extract_seed_domains(ctx.scope.in_scope, scope_filter)
    explicit_targets, explicit_skipped_counts = _extract_explicit_web_targets(
        ctx.scope.in_scope,
        scope_filter,
    )

    combined_skipped_counts = dict(skipped_scope_counts)
    for key, count in explicit_skipped_counts.items():
        combined_skipped_counts[key] = combined_skipped_counts.get(key, 0) + count

    if combined_skipped_counts:
        logger.info(
            "asset_discovery_seed_scope_skipped",
            scan_id=ctx.scan_id,
            skipped_counts=combined_skipped_counts,
        )

    if not seed_domains and not explicit_targets:
        logger.warning(
            "No web seed domains or explicit web targets found in scope - skipping asset discovery",
            scan_id=ctx.scan_id,
        )
        return assets

    for domain in seed_domains:
        try:
            domain_assets = await _discover_domain(domain, scope_filter, config)
            assets.extend(domain_assets)
        except Exception as exc:
            logger.warning(
                "Asset discovery failed for domain",
                domain=domain,
                error=str(exc),
            )
            errors[domain] = str(exc)

    if explicit_targets:
        try:
            explicit_assets = await _probe_explicit_targets(explicit_targets, scope_filter, config)
            assets.extend(explicit_assets)
        except Exception as exc:
            logger.warning(
                "asset_discovery_explicit_probe_failed",
                scan_id=ctx.scan_id,
                error=str(exc),
            )
            errors["explicit_scope"] = str(exc)

    deduped_assets = _dedupe_assets_by_origin(assets)
    logger.info(
        "Stage 1 complete",
        scan_id=ctx.scan_id,
        seed_domains=len(seed_domains),
        explicit_targets=len(explicit_targets),
        assets_found=len(deduped_assets),
        errors=len(errors),
    )
    return deduped_assets


async def _discover_domain(
    domain: str,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredAsset]:
    """Run subfinder -> alterx -> dnsx -> httpx for one seed domain."""
    subfinder_lines: list[str] = []

    # Step 1: subfinder (non-fatal; seed-only path continues on failure/empty output)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        subfinder_out = tf.name
    try:
        try:
            await run_tool_communicate(
                args=[
                    "subfinder",
                    "-d",
                    domain,
                    "-all",
                    "-pc",
                    "/app/subfinder-config/provider-config.yaml",
                    "-timeout",
                    "30",
                    "-o",
                    subfinder_out,
                ],
                timeout=_effective_timeout(config, int(getattr(config, "subfinder_timeout", 600))),
                label=f"subfinder[{domain}]",
            )
            with open(subfinder_out, encoding="utf-8", errors="ignore") as handle:
                subfinder_lines = handle.read().splitlines()
        except Exception as exc:
            logger.warning(
                "subfinder_failed_seed_only",
                domain=domain,
                error=str(exc),
            )
    finally:
        os.unlink(subfinder_out)

    subdomains = sorted({line.strip() for line in subfinder_lines if line.strip()})
    logger.debug("subfinder complete", domain=domain, found=len(subdomains))

    # Step 2: alterx permutations (only when this domain had subfinder results)
    all_candidates = {domain}
    all_candidates.update(subdomains)
    if subdomains:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
            tf.write("\n".join(subdomains))
            subfinder_file = tf.name
        try:
            try:
                alterx_stdout, _ = await run_tool_communicate(
                    args=["alterx", "-l", subfinder_file, "-silent"],
                    timeout=_effective_timeout(config, int(getattr(config, "alterx_timeout", 300))),
                    label=f"alterx[{domain}]",
                )
                permutations = [line.strip() for line in alterx_stdout.splitlines() if line.strip()]
                all_candidates.update(permutations)
            except Exception as exc:
                logger.warning("alterx_failed_non_fatal", domain=domain, error=str(exc))
        finally:
            os.unlink(subfinder_file)
    else:
        logger.info("alterx_skipped_no_subfinder_results", domain=domain)

    # Step 3: dnsx resolution of seed + discovered candidates
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(sorted(all_candidates)))
        candidates_file = tf.name
    try:
        dnsx_stdout, _ = await run_tool_communicate(
            args=["dnsx", "-l", candidates_file, "-silent", "-resp"],
            timeout=_effective_timeout(config, int(getattr(config, "dnsx_timeout", 900))),
            label=f"dnsx[{domain}]",
        )
        live_domains = sorted(
            {
                line.strip().split()[0]
                for line in dnsx_stdout.splitlines()
                if line.strip()
            }
        )
    finally:
        os.unlink(candidates_file)

    if not live_domains:
        return []

    # Step 4: httpx probing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(live_domains))
        live_file = tf.name
    try:
        httpx_stdout, _ = await run_tool_communicate(
            args=[
                "httpx",
                "-l",
                live_file,
                "-json",
                "-silent",
                "-tech-detect",
                "-status-code",
                "-title",
            ],
            timeout=_effective_timeout(config, int(getattr(config, "httpx_timeout", 600))),
            label=f"httpx[{domain}]",
        )
    finally:
        os.unlink(live_file)

    return _httpx_entries_to_assets(httpx_stdout, scope_filter)


async def _probe_explicit_targets(
    targets: list[str],
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredAsset]:
    unique_targets = sorted({str(target).strip() for target in targets if str(target).strip()})
    if not unique_targets:
        return []

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(unique_targets))
        explicit_targets_file = tf.name
    try:
        httpx_stdout, _ = await run_tool_communicate(
            args=[
                "httpx",
                "-l",
                explicit_targets_file,
                "-json",
                "-silent",
                "-tech-detect",
                "-status-code",
                "-title",
            ],
            timeout=_effective_timeout(config, int(getattr(config, "httpx_timeout", 600))),
            label="httpx[explicit_scope]",
        )
    finally:
        os.unlink(explicit_targets_file)

    return _httpx_entries_to_assets(httpx_stdout, scope_filter)


def _httpx_entries_to_assets(httpx_stdout: str, scope_filter: ScopeFilter) -> list[DiscoveredAsset]:
    found_assets: list[DiscoveredAsset] = []
    for entry in parse_jsonl(httpx_stdout):
        if entry.get("failed"):
            continue
        url = _normalize_httpx_url(entry)
        if not url or not scope_filter.is_in_scope(url):
            continue
        found_assets.append(
            DiscoveredAsset(
                asset_type="subdomain",
                value=url,
                http_status=entry.get("status_code"),
                technology_stack={
                    "technologies": [
                        tech.get("name", str(tech)) if isinstance(tech, dict) else str(tech)
                        for tech in entry.get("tech", [])
                    ]
                },
                waf_detected=_extract_waf(entry),
            )
        )
    return found_assets


def _extract_seed_domains(in_scope: list, scope_filter: ScopeFilter) -> tuple[list[str], dict[str, int]]:
    domains: set[str] = set()
    skipped_counts: dict[str, int] = {}

    for rule in in_scope:
        asset_type, raw_value = _coerce_scope_rule(rule)
        if not raw_value:
            skipped_counts["empty_value"] = skipped_counts.get("empty_value", 0) + 1
            continue

        if asset_type in _DOMAIN_TYPES or asset_type is None:
            normalized = _normalize_seed_domain(raw_value)
            if normalized:
                domains.add(normalized)
            else:
                skipped_counts["invalid_domain_value"] = skipped_counts.get("invalid_domain_value", 0) + 1
            continue

        if asset_type == "url":
            parsed = urlparse(raw_value)
            scheme = (parsed.scheme or "").lower()
            host = (parsed.hostname or "").lower()
            if scheme not in _HTTP_SCHEMES or not host:
                skipped_counts["non_http_url"] = skipped_counts.get("non_http_url", 0) + 1
                continue
            if not scope_filter.is_host_in_domain_scope(host):
                skipped_counts["url_host_not_domain_led"] = (
                    skipped_counts.get("url_host_not_domain_led", 0) + 1
                )
                continue
            domains.add(host.lstrip("*."))
            continue

        if asset_type in _NON_WEB_SCOPE_TYPES:
            key = f"non_web_{asset_type}"
            skipped_counts[key] = skipped_counts.get(key, 0) + 1
            continue

        key = f"unsupported_{asset_type or 'unknown'}"
        skipped_counts[key] = skipped_counts.get(key, 0) + 1

    return sorted(domains), skipped_counts


def _extract_explicit_web_targets(
    in_scope: list,
    scope_filter: ScopeFilter,
) -> tuple[list[str], dict[str, int]]:
    targets: set[str] = set()
    skipped_counts: dict[str, int] = {}

    for rule in in_scope:
        asset_type, raw_value = _coerce_scope_rule(rule)
        if not raw_value:
            skipped_counts["explicit_empty_value"] = skipped_counts.get("explicit_empty_value", 0) + 1
            continue

        if asset_type == "domain" or asset_type is None:
            host = _normalize_seed_domain(raw_value)
            if not host:
                skipped_counts["explicit_invalid_domain_value"] = (
                    skipped_counts.get("explicit_invalid_domain_value", 0) + 1
                )
                continue
            if scope_filter.is_in_scope(host):
                targets.add(host)
            else:
                skipped_counts["explicit_target_out_of_scope"] = (
                    skipped_counts.get("explicit_target_out_of_scope", 0) + 1
                )
            continue

        if asset_type == "url":
            candidate = _normalize_explicit_url(raw_value)
            if not candidate:
                skipped_counts["explicit_non_http_url"] = (
                    skipped_counts.get("explicit_non_http_url", 0) + 1
                )
                continue
            if scope_filter.is_in_scope(candidate):
                targets.add(candidate)
            else:
                skipped_counts["explicit_target_out_of_scope"] = (
                    skipped_counts.get("explicit_target_out_of_scope", 0) + 1
                )
            continue

        if asset_type == "wildcard_domain":
            skipped_counts["explicit_wildcard_domain_skipped"] = (
                skipped_counts.get("explicit_wildcard_domain_skipped", 0) + 1
            )
            continue

        if asset_type in _NON_WEB_SCOPE_TYPES:
            key = f"explicit_non_web_{asset_type}"
            skipped_counts[key] = skipped_counts.get(key, 0) + 1
            continue

        key = f"explicit_unsupported_{asset_type or 'unknown'}"
        skipped_counts[key] = skipped_counts.get(key, 0) + 1

    return sorted(targets), skipped_counts


def _dedupe_assets_by_origin(assets: list[DiscoveredAsset]) -> list[DiscoveredAsset]:
    """
    Deduplicate by canonical origin key.

    Merge semantics are deterministic:
    - first seen wins for all existing fields
    - later duplicates only fill missing/null fields
    """
    deduped: list[DiscoveredAsset] = []
    by_key: dict[str, DiscoveredAsset] = {}

    for asset in assets:
        key = _origin_key(asset.value)
        if not key:
            key = f"raw:{asset.value.strip().lower()}"

        existing = by_key.get(key)
        if existing is None:
            by_key[key] = asset
            deduped.append(asset)
            continue

        if existing.http_status is None and asset.http_status is not None:
            existing.http_status = asset.http_status
        if not existing.technology_stack and asset.technology_stack:
            existing.technology_stack = asset.technology_stack
        if not existing.waf_detected and asset.waf_detected:
            existing.waf_detected = asset.waf_detected

    return deduped


def _origin_key(url: str) -> str | None:
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    if not scheme or not host:
        return None

    if parsed.port is not None:
        port = parsed.port
    elif scheme == "https":
        port = 443
    elif scheme == "http":
        port = 80
    else:
        port = -1
    return f"{scheme}://{host}:{port}"


def _normalize_httpx_url(entry: dict) -> str:
    url = entry.get("url") or entry.get("input") or ""
    if isinstance(url, dict):
        url = url.get("url") or url.get("host") or ""
    return str(url).strip() if url else ""


def _coerce_scope_rule(rule: object) -> tuple[str | None, str]:
    if isinstance(rule, dict):
        return rule.get("asset_type"), str(rule.get("value") or rule.get("url") or "").strip()
    if hasattr(rule, "value"):
        return getattr(rule, "asset_type", None), str(getattr(rule, "value", "") or "").strip()
    return None, str(rule or "").strip()


def _normalize_seed_domain(raw_value: str) -> str:
    candidate = raw_value.strip()
    if not candidate:
        return ""
    if "://" in candidate:
        host = (urlparse(candidate).hostname or "").strip()
    else:
        host = candidate.split("/")[0].split(":")[0].strip()
    host = host.lower().lstrip("*.")
    if not host:
        return ""
    if "." not in host and ":" not in host:
        return ""
    return host


def _normalize_explicit_url(raw_value: str) -> str:
    candidate = raw_value.strip()
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    if scheme not in _HTTP_SCHEMES or not host:
        return ""
    return candidate


def _extract_waf(httpx_entry: dict) -> str | None:
    return detect_waf_technology(httpx_entry.get("tech", []))


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
