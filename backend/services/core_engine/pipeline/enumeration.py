import hashlib
import json
import os
import tempfile
from typing import Iterable
from urllib.parse import urlparse

import httpx as httpx_client

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.services.core_engine.models import (
    DiscoveredAsset,
    DiscoveredEndpoint,
    DiscoveredJsAsset,
)
from backend.services.core_engine.subprocess_utils import run_tool_communicate
from backend.shared.logging import get_logger
from backend.shared.storage import upload_bytes

logger = get_logger("core_engine.stage3")

STAGE_NUMBER = 3.0
STAGE_NAME = "enumeration"


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
) -> tuple[list[DiscoveredEndpoint], list[DiscoveredJsAsset]]:
    """
    Stage 3: Enumeration.
    - ffuf: directory/path discovery per live asset
    - waybackurls: historical URL discovery per domain
    - JS download: upload JS files to MinIO (best-effort; failures are non-fatal)
    """
    if not assets:
        return [], []

    in_scope_assets = [a for a in assets if scope_filter.is_in_scope(a.value)]
    if not in_scope_assets:
        logger.warning("No in-scope assets — skipping enumeration", scan_id=ctx.scan_id)
        return [], []

    endpoints: list[DiscoveredEndpoint] = []
    js_assets: list[DiscoveredJsAsset] = []

    for asset in in_scope_assets:
        asset_endpoints, asset_js = await _enumerate_asset(ctx, asset, scope_filter, config)
        endpoints.extend(asset_endpoints)
        js_assets.extend(asset_js)

    endpoints = _dedupe_endpoints(endpoints)

    logger.info(
        "Stage 3 complete",
        scan_id=ctx.scan_id,
        endpoints=len(endpoints),
        js_assets=len(js_assets),
    )
    return endpoints, js_assets


async def _enumerate_asset(
    ctx: ScanContext,
    asset: DiscoveredAsset,
    scope_filter: ScopeFilter,
    config,
) -> tuple[list[DiscoveredEndpoint], list[DiscoveredJsAsset]]:
    base_url = _normalize_base_url(asset.value)
    if not base_url:
        return [], []

    out_endpoints: list[DiscoveredEndpoint] = []
    out_js_assets: list[DiscoveredJsAsset] = []

    # 1) ffuf
    out_endpoints.extend(await _run_ffuf(asset, base_url, config))

    # 2) waybackurls
    out_endpoints.extend(await _run_waybackurls(asset, base_url, scope_filter, config))

    # 3) JS discovery + download/upload (best-effort)
    js_urls = [
        ep.full_url
        for ep in out_endpoints
        if ep.full_url.lower().endswith(".js") and scope_filter.is_in_scope(ep.full_url)
    ]
    for js_url in js_urls:
        js = await _download_and_store_js(ctx, js_url, scope_filter, config)
        if js:
            out_js_assets.append(js)

    return out_endpoints, out_js_assets


def _normalize_base_url(value: str) -> str:
    v = value.strip()
    if not v:
        return ""
    if "://" not in v:
        v = "https://" + v
    parsed = urlparse(v)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


async def _run_ffuf(
    asset: DiscoveredAsset,
    base_url: str,
    config,
) -> list[DiscoveredEndpoint]:
    if asset.asset_id is None:
        return []

    wordlist = getattr(config, "ffuf_wordlist", "/wordlists/common.txt")
    timeout = _effective_timeout(config, int(getattr(config, "ffuf_timeout", 600)))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        out_file = tf.name

    try:
        await run_tool_communicate(
            args=[
                "ffuf",
                "-u", f"{base_url}/FUZZ",
                "-w", wordlist,
                "-o", out_file,
                "-of", "json",
                "-mc", "200,201,204,301,302,307,401,403",
                "-t", "50",
                "-timeout", "10",
                "-s",
            ],
            timeout=timeout,
            label=f"ffuf[{base_url}]",
        )
        try:
            with open(out_file, "r", encoding="utf-8", errors="replace") as f:
                stdout = f.read()
        except Exception:
            stdout = ""
    except Exception as e:
        logger.warning("ffuf failed", asset=base_url, error=str(e))
        return []
    finally:
        try:
            os.unlink(out_file)
        except Exception:
            pass

    try:
        data = json.loads(stdout) if stdout.strip().startswith("{") else {}
        results = data.get("results", []) if isinstance(data, dict) else []
    except Exception:
        results = []

    endpoints: list[DiscoveredEndpoint] = []
    for r in results:
        url = r.get("url")
        if not url:
            continue
        parsed = urlparse(url)
        path = parsed.path or "/"
        endpoints.append(
            DiscoveredEndpoint(
                asset_id=asset.asset_id,
                method="GET",
                path=path,
                full_url=url,
                response_code=r.get("status"),
            )
        )
    return endpoints


async def _run_waybackurls(
    asset: DiscoveredAsset,
    base_url: str,
    scope_filter: ScopeFilter,
    config,
) -> list[DiscoveredEndpoint]:
    if asset.asset_id is None:
        return []

    parsed = urlparse(base_url)
    domain = parsed.hostname or ""
    if not domain:
        return []

    timeout = _effective_timeout(config, int(getattr(config, "waybackurls_timeout", 300)))
    try:
        stdout, _ = await run_tool_communicate(
            args=["waybackurls", domain],
            timeout=timeout,
            label=f"waybackurls[{domain}]",
        )
    except FileNotFoundError:
        logger.warning("waybackurls not installed — skipping", domain=domain)
        return []
    except Exception as e:
        logger.warning("waybackurls failed", domain=domain, error=str(e))
        return []

    endpoints: list[DiscoveredEndpoint] = []
    for line in stdout.splitlines():
        url = line.strip()
        if not url or not scope_filter.is_in_scope(url):
            continue
        p = urlparse(url)
        endpoints.append(
            DiscoveredEndpoint(
                asset_id=asset.asset_id,
                method="GET",
                path=p.path or "/",
                full_url=url,
            )
        )
    return endpoints


async def _download_and_store_js(
    ctx: ScanContext,
    js_url: str,
    scope_filter: ScopeFilter,
    config,
) -> DiscoveredJsAsset | None:
    timeout_s = int(getattr(config, "js_download_timeout_seconds", 30))
    max_size = int(getattr(config, "js_max_file_size_bytes", 5_242_880))

    try:
        async with httpx_client.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
            resp = await client.get(js_url)
            if resp.status_code != 200:
                return None
            final_url = str(resp.url)
            if not scope_filter.is_in_scope(final_url):
                logger.warning("js_redirect_out_of_scope", original_url=js_url, final_url=final_url)
                return None
            content_bytes = resp.content
    except Exception as e:
        logger.warning("js_download_failed", url=js_url, error=str(e))
        return None

    if len(content_bytes) > max_size:
        logger.warning("js_too_large_skipping", url=js_url, size_bytes=len(content_bytes))
        return None

    content_hash = hashlib.sha256(content_bytes).hexdigest()
    object_name = f"{ctx.scan_id}/{content_hash}.js"
    storage_path = f"js-assets/{object_name}"

    # Best-effort upload: if storage not initialized, skip JS asset persistence.
    try:
        upload_bytes(bucket="js-assets", object_name=object_name, data=content_bytes, content_type="application/javascript")
    except Exception as e:
        logger.warning("js_upload_failed", url=js_url, error=str(e))
        return None

    return DiscoveredJsAsset(
        scan_id=_scan_id_as_uuid(ctx.scan_id),
        url=final_url,
        storage_path=storage_path,
        content_hash=content_hash,
        size_bytes=len(content_bytes),
    )


def _scan_id_as_uuid(scan_id: str):
    # Avoid importing uuid at module import time; also supports non-UUID scan ids in tests.
    import uuid
    try:
        return uuid.UUID(scan_id)
    except Exception:
        return uuid.uuid4()


def _dedupe_endpoints(endpoints: Iterable[DiscoveredEndpoint]) -> list[DiscoveredEndpoint]:
    seen: set[tuple[str, str, str]] = set()
    out: list[DiscoveredEndpoint] = []
    for ep in endpoints:
        key = (str(ep.asset_id), ep.method.upper(), ep.path)
        if key in seen:
            continue
        seen.add(key)
        out.append(ep)
    return out
