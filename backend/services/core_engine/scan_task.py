import asyncio
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import (
    ScanContext, ScopeDefinition, FeatureFlags
)
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.services.core_engine.pipeline import (
    asset_discovery,
    fingerprinting,
    enumeration,
    nuclei_scan,
    web_vuln_tests,
    js_secrets,
    aggregator,
)
from backend.services.core_engine.models import ScanResult
from backend.services.core_engine.repository import ScanRepository
from backend.services.core_engine.config import EngineConfig
from backend.shared.db import get_session
from backend.shared.queue import QueuePublisher
from backend.shared.schemas.envelope import MessageEnvelope
from backend.shared.logging import get_logger

logger = get_logger("core_engine.scan_task")


def run_scan_task(payload: dict) -> None:
    """
    Celery task entry point. Synchronous wrapper around the async pipeline.
    Called by the Celery worker when a message arrives on scan.jobs.
    """
    asyncio.run(_async_scan_pipeline(payload))


async def _async_scan_pipeline(payload: dict) -> None:
    """
    Full async pipeline. Any unhandled exception here marks the scan failed_internal.
    Redis lock prevents concurrent scans for the same program.
    """
    import redis.asyncio as aioredis

    config = EngineConfig()
    from backend.shared.db import init_db
    init_db(config.database_url)
    program_id = payload.get("program_id")
    scan_id = None

    # Redis lock — one scan per program at a time
    redis = aioredis.from_url(config.redis_url)
    lock_key = f"scan:lock:{program_id}"

    async with redis.lock(lock_key, timeout=config.scan_lock_ttl_seconds):
        async with get_session() as session:
            repo = ScanRepository(session)

            # Build scan context from message
            scope_raw = payload.get("scope", {})
            scope = ScopeDefinition(
                in_scope=scope_raw.get("in_scope", []),
                out_of_scope=scope_raw.get("out_of_scope", []),
            )
            flags_raw = payload.get("feature_flags", {})
            feature_flags = FeatureFlags(
                sqli=flags_raw.get("sqli", False),
                ssrf=flags_raw.get("ssrf", False),
                crlf=flags_raw.get("crlf", False),
                browser_session=flags_raw.get("browser_session", False),
                api_fuzzing=flags_raw.get("api_fuzzing", False),
                ai_hypothesis=flags_raw.get("ai_hypothesis", False),
            )

            scan_id = await repo.create_or_resume_scan(
                program_id=program_id,
                feature_flags=flags_raw,
                priority=payload.get("priority", 1),
            )

            ctx = ScanContext(
                scan_id=scan_id,
                program_id=program_id,
                scope=scope,
                feature_flags=feature_flags,
                priority=payload.get("priority", 1),
            )

            scan_result = ScanResult()
            publisher = QueuePublisher(config.rabbitmq_url)
            await publisher.connect()

            try:
                 await _execute_pipeline(ctx, scan_result, repo, publisher, config)
            except Exception as e:
                logger.error("Pipeline fatal error",
                             scan_id=scan_id, error=str(e))
                await repo.mark_scan_complete(
                    scan_id=scan_id,
                    status="failed_internal",
                    finding_count=0,
                    severity_breakdown={},
                    error_detail=str(e),
                )


async def _execute_pipeline(
    ctx: ScanContext,
    scan_result: ScanResult,
    repo: ScanRepository,
    publisher: QueuePublisher,
    config: "EngineConfig",
) -> None:
    """
    Ordered pipeline execution. Stages 4 and 5 run in parallel.
    Stage failures are non-fatal unless Stage 0 (scope) or Stage 7 (aggregation) fail.
    """
    scan_id = ctx.scan_id

    # ── Stage 0: Scope Filter (FATAL) ───────────────────────────────────
    logger.info("Stage 0: Scope filter", scan_id=scan_id)
    scope_filter = ScopeFilter(ctx.scope)  # raises ScanError if scope empty

    # ── Stage 1: Asset Discovery ─────────────────────────────────────────
    s1_start = datetime.now(timezone.utc)
    try:
        assets = await asset_discovery.run(ctx, scope_filter, config)
        scan_result.assets = assets
        await repo.save_assets(scan_id, assets)
        await repo.record_stage(scan_id, 1.0, "asset_discovery", "completed",
                                s1_start, {"assets_found": len(assets)})
    except Exception as e:
        scan_result.stage_errors["asset_discovery"] = str(e)
        await repo.record_stage(scan_id, 1.0, "asset_discovery", "failed",
                                s1_start, error_detail=str(e))
        logger.warning("Stage 1 failed — continuing", scan_id=scan_id, error=str(e))

    if not scan_result.assets:
        logger.warning("No assets found — skipping Stages 2–6", scan_id=scan_id)
        await aggregator.run(ctx, scan_result, repo, publisher)
        return

    # ── Stage 2: Fingerprinting ─────────────────────────────────────────
    s2_start = datetime.now(timezone.utc)
    try:
        scan_result.assets = await fingerprinting.run(ctx, scan_result.assets, config)
        await repo.save_assets(scan_id, scan_result.assets)  # update with enrichment
        await repo.record_stage(scan_id, 2.0, "fingerprinting", "completed", s2_start)
    except Exception as e:
        scan_result.stage_errors["fingerprinting"] = str(e)
        await repo.record_stage(scan_id, 2.0, "fingerprinting", "failed",
                                s2_start, error_detail=str(e))
        logger.warning("Stage 2 failed — continuing", scan_id=scan_id, error=str(e))

    # ── Stage 3: Enumeration ─────────────────────────────────────────────
    s3_start = datetime.now(timezone.utc)
    try:
        endpoints, js_assets = await enumeration.run(
            ctx, scan_result.assets, scope_filter, config
        )
        scan_result.endpoints = endpoints
        scan_result.js_assets = js_assets
        await repo.save_endpoints(scan_id, endpoints)
        for js in js_assets:
            await repo.save_js_asset(scan_id, js)
        ctx.js_asset_ids = [str(j.js_asset_id) for j in js_assets if j.js_asset_id]
        await repo.record_stage(scan_id, 3.0, "enumeration", "completed", s3_start,
                                {"endpoints": len(endpoints), "js_assets": len(js_assets)})
    except Exception as e:
        scan_result.stage_errors["enumeration"] = str(e)
        await repo.record_stage(scan_id, 3.0, "enumeration", "failed",
                                s3_start, error_detail=str(e))
        logger.warning("Stage 3 failed — continuing", scan_id=scan_id, error=str(e))

    # ── Stages 4 + 5: Parallel ───────────────────────────────────────────
    s4_start = datetime.now(timezone.utc)
    nuclei_task = asyncio.create_task(
        nuclei_scan.run(ctx, scan_result.assets, scope_filter, config)
    )
    web_task = asyncio.create_task(
        web_vuln_tests.run(ctx, scan_result.endpoints, scope_filter, ctx.feature_flags)
    )
    nuclei_findings, web_findings = await asyncio.gather(
        nuclei_task, web_task, return_exceptions=True
    )

    if isinstance(nuclei_findings, Exception):
        scan_result.stage_errors["nuclei_scan"] = str(nuclei_findings)
        await repo.record_stage(scan_id, 4.0, "nuclei_scan", "failed",
                                s4_start, error_detail=str(nuclei_findings))
    else:
        scan_result.finding_candidates.extend(nuclei_findings)
        await repo.record_stage(scan_id, 4.0, "nuclei_scan", "completed", s4_start,
                                {"findings": len(nuclei_findings)})

    if isinstance(web_findings, Exception):
        scan_result.stage_errors["web_vuln_tests"] = str(web_findings)
        await repo.record_stage(scan_id, 5.0, "web_vuln_tests", "failed",
                                s4_start, error_detail=str(web_findings))
    else:
        scan_result.finding_candidates.extend(web_findings)
        await repo.record_stage(scan_id, 5.0, "web_vuln_tests", "completed", s4_start,
                                {"findings": len(web_findings)})

    # ── Stage 6: JS Secrets ──────────────────────────────────────────────
    s6_start = datetime.now(timezone.utc)
    try:
        js_findings = await js_secrets.run(ctx, scan_result.js_assets)
        scan_result.finding_candidates.extend(js_findings)
        await repo.record_stage(scan_id, 6.0, "js_secrets", "completed", s6_start,
                                {"findings": len(js_findings)})
    except Exception as e:
        scan_result.stage_errors["js_secrets"] = str(e)
        await repo.record_stage(scan_id, 6.0, "js_secrets", "failed",
                                s6_start, error_detail=str(e))
        logger.warning("Stage 6 failed — continuing", scan_id=scan_id, error=str(e))

    # ── Stage 7: Aggregation (FATAL if fails) ───────────────────────────
    await aggregator.run(ctx, scan_result, repo, publisher)