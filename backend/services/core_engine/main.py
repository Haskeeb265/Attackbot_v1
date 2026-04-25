from contextlib import asynccontextmanager
import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.repository import ScanRepository
from backend.services.core_engine.startup_checks import (
    collect_toolchain_checks,
    startup_checks_ok,
)
from backend.services.core_engine.watchdog import recover_stuck_scans, start_watchdog
from backend.shared.db import init_db, get_session, check_db_health
from backend.shared.dlq_monitor import monitor_all_dlqs_job
from backend.shared.jobs.idempotency_cleanup import cleanup_expired_idempotency_keys_job
from backend.shared.health import HealthResponse, ComponentHealth, HealthStatus
from backend.shared.logging import configure_logging, get_logger
from backend.shared.circuit_breaker import ServiceCircuitBreakers
from backend.shared.queue import (
    Queues,
    check_rabbitmq_health,
    ensure_queue_topology,
    inspect_queue_states,
)
from backend.shared.schemas.scan_jobs import (
    ScanJobsPayload,
    ScopeDefinition as SchemaScopeDefinition,
    ScopeEntry,
    FeatureFlags as SchemaFeatureFlags,
    build_scan_job_message,
)
from backend.shared.storage import init_storage, check_storage_health

config = EngineConfig()
configure_logging(config.service_name)
logger = get_logger("core_engine.main")

scheduler = AsyncIOScheduler()
_scraper_client: httpx.AsyncClient | None = None
_toolchain_checks = []


class ScanStartRequest(BaseModel):
    """Minimal input for manual scan trigger."""
    model_config = ConfigDict(extra="ignore")
    program_id: str
    feature_flags: dict = Field(default_factory=dict)
    priority: int = 1


async def _get_scraper_client() -> httpx.AsyncClient:
    if _scraper_client is None:
        raise RuntimeError("Scraper client not initialized")
    return _scraper_client


async def _check_scraper_health() -> bool:
    client = await _get_scraper_client()
    try:
        resp = await client.get("/api/v1/health")
        if resp.status_code != 200:
            return False
        body = resp.json()
        return body.get("status") in {
            HealthStatus.HEALTHY.value,
            HealthStatus.DEGRADED.value,
        }
    except Exception:
        return False


def _to_scope_entries(items: list[dict]) -> list[ScopeEntry]:
    entries: list[ScopeEntry] = []
    for item in items:
        value = item.get("value")
        if not value:
            continue
        entries.append(ScopeEntry(
            asset_type=item.get("asset_type", "domain"),
            value=value,
            notes=item.get("notes"),
        ))
    return entries


async def _fetch_program(program_id: str) -> dict:
    client = await _get_scraper_client()
    resp = await client.get(f"/api/v1/programs/{program_id}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Program not found")
    resp.raise_for_status()
    return resp.json()


async def _fetch_scope(program_id: str) -> dict:
    client = await _get_scraper_client()
    resp = await client.get(f"/api/v1/programs/{program_id}/scope")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Program scope not found")
    resp.raise_for_status()
    return resp.json()


async def _build_payload_from_scraper(
    program_id: str,
    feature_flags: dict | None = None,
    priority: int = 1,
) -> ScanJobsPayload:
    program = await _fetch_program(program_id)
    scope_data = await _fetch_scope(program_id)
    in_scope = _to_scope_entries(scope_data.get("in_scope", []))
    out_scope = _to_scope_entries(scope_data.get("out_of_scope", []))
    if not in_scope:
        raise HTTPException(status_code=400, detail="Scope has no in_scope entries")

    platform = program.get("platform")
    handle = program.get("handle")
    if not platform or not handle:
        raise HTTPException(status_code=400, detail="Program missing platform/handle")

    flags = SchemaFeatureFlags(**(feature_flags or {}))
    return ScanJobsPayload(
        program_id=program_id,
        platform=platform,
        handle=handle,
        scope=SchemaScopeDefinition(in_scope=in_scope, out_of_scope=out_scope),
        feature_flags=flags,
        priority=priority,
    )


def _build_payload_from_minimal_body(body: dict) -> ScanJobsPayload:
    target = body.get("target") or body.get("program_id")
    in_scope = [ScopeEntry(asset_type="domain", value=str(target), notes="manual_start")]
    return ScanJobsPayload(
        program_id=body["program_id"],
        platform="hackerone",
        handle=str(body["program_id"]),
        scope=SchemaScopeDefinition(in_scope=in_scope, out_of_scope=[]),
        feature_flags=SchemaFeatureFlags(**body.get("feature_flags", {})),
        priority=int(body.get("priority", 1)),
    )


async def _reserve_scan_id(payload: ScanJobsPayload) -> str:
    """
    Reserve the scan row before queueing so callers can correlate on scan_id.
    """
    async with get_session() as session:
        repo = ScanRepository(session)
        return await repo.create_or_resume_scan(
            program_id=str(payload.program_id),
            feature_flags=payload.feature_flags.model_dump(mode="python"),
            priority=payload.priority,
        )


def _enqueue_scan(payload: ScanJobsPayload) -> None:
    from backend.services.core_engine.worker import scan_task

    effective_payload = payload
    raw_scan_timeout = getattr(payload, "scan_timeout_seconds", None)
    if raw_scan_timeout is None:
        logger.warning(
            "scan_timeout_scaling_skipped_missing_field",
            program_id=str(payload.program_id),
        )
    else:
        try:
            effective_scan_timeout = int(
                config.scaled_scan_timeout_seconds(int(raw_scan_timeout))
            )
            if effective_scan_timeout != int(raw_scan_timeout):
                effective_payload = payload.model_copy(
                    update={"scan_timeout_seconds": effective_scan_timeout}
                )
        except (TypeError, ValueError) as exc:
            logger.warning(
                "scan_timeout_scaling_skipped_invalid_value",
                program_id=str(payload.program_id),
                scan_timeout_seconds=raw_scan_timeout,
                error=str(exc),
            )
            effective_payload = payload

    message = build_scan_job_message(
        effective_payload,
        source_service=config.service_name,
    )
    scan_task.apply_async(args=[message], queue=Queues.SCAN_JOBS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from backend.shared.tracing import init_tracing, instrument_httpx

        init_tracing(config.service_name, config.jaeger_endpoint)
        instrument_httpx()
    except Exception as exc:
        logger.warning("tracing_init_failed", error=str(exc))
    config.require_fields(
        [
            "database_url",
            "rabbitmq_url",
            "minio_endpoint",
            "minio_access_key",
            "minio_secret_key",
        ]
    )
    init_db(config.database_url)
    init_storage(
        endpoint=config.minio_endpoint,
        access_key=config.minio_access_key,
        secret_key=config.minio_secret_key,
        secure=config.minio_secure,
    )
    await ensure_queue_topology(config.rabbitmq_url)
    global _toolchain_checks
    _toolchain_checks = collect_toolchain_checks(
        nuclei_timeout_seconds=config.nuclei_template_check_timeout_seconds
    )
    if not startup_checks_ok(_toolchain_checks):
        failed = {
            check.name: check.detail
            for check in _toolchain_checks
            if not check.ok
        }
        raise RuntimeError(f"Core engine startup checks failed: {failed}")
    global _scraper_client
    _scraper_client = httpx.AsyncClient(
        base_url=config.scraper_api_url,
        timeout=config.scraper_api_timeout_seconds,
    )

    async def _republish(program_id: str):
        # Minimal republish — fetch program scope from Scraper API and requeue
        # Full implementation: call scraper API GET /programs/{id}/scope
        payload = await _build_payload_from_scraper(program_id)
        _enqueue_scan(payload)
        logger.info("Republished scan job", program_id=program_id)

    # Start watchdog using the new start_watchdog function
    start_watchdog(scheduler)
    
    # Add DLQ monitoring job
    scheduler.add_job(
        monitor_all_dlqs_job,
        "interval",
        seconds=60,
        kwargs={"rabbitmq_url": config.rabbitmq_url},
        id='dlq_monitor',
        replace_existing=True,
    )
    
    # Add idempotency cleanup job (runs daily)
    scheduler.add_job(
        cleanup_expired_idempotency_keys_job,
        "interval",
        hours=24,
        id='idempotency_cleanup',
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Core Engine started", watchdog_interval=config.watchdog_interval_seconds)
    yield
    scheduler.shutdown()
    if _scraper_client:
        await _scraper_client.aclose()


app = FastAPI(title="Core Engine", lifespan=lifespan)
try:
    from backend.shared.tracing import instrument_fastapi

    instrument_fastapi(app)
except Exception as exc:
    logger.warning("tracing_fastapi_instrumentation_failed", error=str(exc))


@app.get("/api/v1/health")
async def health() -> JSONResponse:
    from datetime import datetime, timezone
    db_ok = await check_db_health()
    rabbitmq_ok = await check_rabbitmq_health(
        config.rabbitmq_url,
        [Queues.SCAN_JOBS, Queues.REPORT_JOBS],
    )
    scraper_ok = False
    if _scraper_client is not None:
        scraper_ok = await _check_scraper_health()
    storage_ok = check_storage_health()
    scheduler_ok = scheduler.running
    toolchain_ok = startup_checks_ok(_toolchain_checks)
    statuses = [
        HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY,
        HealthStatus.HEALTHY if rabbitmq_ok else HealthStatus.UNHEALTHY,
        HealthStatus.HEALTHY if scraper_ok else HealthStatus.UNHEALTHY,
        HealthStatus.HEALTHY if storage_ok else HealthStatus.UNHEALTHY,
        HealthStatus.HEALTHY if scheduler_ok else HealthStatus.UNHEALTHY,
        HealthStatus.HEALTHY if toolchain_ok else HealthStatus.UNHEALTHY,
    ]
    status = (
        HealthStatus.UNHEALTHY
        if any(component == HealthStatus.UNHEALTHY for component in statuses)
        else HealthStatus.HEALTHY
    )
    breaker_states = ServiceCircuitBreakers.get_state_summary()
    return JSONResponse(
        content=HealthResponse(
            status=status,
            service=config.service_name,
            timestamp=datetime.now(timezone.utc),
            components={
                "database": ComponentHealth(
                    status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
                ),
                "rabbitmq": ComponentHealth(
                    status=HealthStatus.HEALTHY if rabbitmq_ok else HealthStatus.UNHEALTHY
                ),
                "scraper_api": ComponentHealth(
                    status=HealthStatus.HEALTHY if scraper_ok else HealthStatus.UNHEALTHY
                ),
                "storage": ComponentHealth(
                    status=HealthStatus.HEALTHY if storage_ok else HealthStatus.UNHEALTHY
                ),
                "scheduler": ComponentHealth(
                    status=HealthStatus.HEALTHY if scheduler_ok else HealthStatus.UNHEALTHY
                ),
                "toolchain": ComponentHealth(
                    status=HealthStatus.HEALTHY if toolchain_ok else HealthStatus.UNHEALTHY,
                    detail=(
                        None
                        if toolchain_ok
                        else ", ".join(
                            f"{check.name}: {check.detail}"
                            for check in _toolchain_checks
                            if not check.ok
                        )
                    ),
                ),
                "circuit_breakers": ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    detail=", ".join(f"{k}:{v}" for k, v in sorted(breaker_states.items()))
                    if breaker_states
                    else "none",
                ),
            },
        ).model_dump(mode="json")
    )


@app.get("/health")
async def legacy_health() -> JSONResponse:
    return await health()


@app.get("/api/v1/circuit-breakers")
async def list_circuit_breakers() -> JSONResponse:
    return JSONResponse({"circuit_breakers": ServiceCircuitBreakers.get_state_summary()})


@app.post("/api/v1/circuit-breakers/reset")
async def reset_circuit_breakers() -> JSONResponse:
    reset_count = ServiceCircuitBreakers.reset_all()
    return JSONResponse({"status": "success", "reset_count": reset_count})


@app.post("/api/v1/scans/start")
async def start_scan(body: dict) -> JSONResponse:
    minimal_body = set(body.keys()).issubset({"program_id", "feature_flags", "priority"})
    if minimal_body:
        req = ScanStartRequest(**body)
        payload = await _build_payload_from_scraper(
            program_id=req.program_id,
            feature_flags=req.feature_flags,
            priority=req.priority,
        )
    elif "program_id" in body and ("target" in body or "scan_type" in body):
        payload = _build_payload_from_minimal_body(body)
    else:
        payload = ScanJobsPayload(**body)
    scan_id = await _reserve_scan_id(payload)
    _enqueue_scan(payload)
    return JSONResponse(
        {
            "status": "queued",
            "program_id": str(payload.program_id),
            "scan_id": scan_id,
        }
    )


@app.get("/api/v1/scans")
async def list_scans() -> JSONResponse:
    async with get_session() as session:
        from sqlalchemy import text
        rows = await session.execute(
            text("SELECT scan_id, program_id, status, finding_count, started_at "
                 "FROM scans ORDER BY created_at DESC LIMIT 50")
        )
        scans = [
            {
                "scan_id": str(r[0]),
                "program_id": str(r[1]),
                "status": r[2],
                "finding_count": r[3],
                "started_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows.fetchall()
        ]
    return JSONResponse({"scans": scans})


@app.get("/api/v1/scans/{scan_id}")
async def get_scan(scan_id: str) -> JSONResponse:
    async with get_session() as session:
        from sqlalchemy import text
        row = await session.execute(
            text("SELECT scan_id, program_id, status, finding_count, "
                 "severity_breakdown, started_at, completed_at, error_detail "
                 "FROM scans WHERE scan_id = :scan_id"),
            {"scan_id": scan_id},
        )
        r = row.fetchone()
        if not r:
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse({
            "scan_id": str(r[0]),
            "program_id": str(r[1]),
            "status": r[2],
            "finding_count": r[3],
            "severity_breakdown": r[4],
            "started_at": r[5].isoformat() if r[5] else None,
            "completed_at": r[6].isoformat() if r[6] else None,
            "error_detail": r[7],
        })


@app.get("/api/v1/scans/{scan_id}/findings")
async def get_findings(scan_id: str) -> JSONResponse:
    async with get_session() as session:
        from sqlalchemy import text
        rows = await session.execute(
            text("""
                SELECT finding_id, vulnerability_type, title, severity,
                       cvss_score, affected_url, affected_parameter,
                       is_verified, source, created_at,
                       description, reproduction_steps, raw_output
                FROM findings WHERE scan_id = :scan_id
                ORDER BY cvss_score DESC NULLS LAST
            """),
            {"scan_id": scan_id},
        )
        findings = [
            {
                "finding_id": str(r[0]),
                "vulnerability_type": r[1],
                "title": r[2],
                "severity": r[3],
                "cvss_score": r[4],
                "affected_url": r[5],
                "affected_parameter": r[6],
                "is_verified": r[7],
                "source": r[8],
                "created_at": r[9].isoformat() if r[9] else None,
                "description": r[10],
                "reproduction_steps": r[11],
                "raw_output": r[12],
            }
            for r in rows.fetchall()
        ]
    return JSONResponse({"findings": findings, "count": len(findings)})


@app.get("/api/v1/scans/{scan_id}/findings/{finding_id}/evidence")
async def get_finding_evidence(scan_id: str, finding_id: str) -> JSONResponse:
    """
    Read-only evidence endpoint for reporter.
    Returns an empty list when no evidence rows exist.
    Returns 404 only when finding_id does not belong to scan_id.
    """
    async with get_session() as session:
        from sqlalchemy import text

        finding_row = await session.execute(
            text(
                """
                SELECT finding_id
                FROM findings
                WHERE scan_id = :scan_id AND finding_id = :finding_id
                """
            ),
            {"scan_id": scan_id, "finding_id": finding_id},
        )
        if finding_row.fetchone() is None:
            return JSONResponse({"error": "not found"}, status_code=404)

        rows = await session.execute(
            text(
                """
                SELECT evidence_id, artifact_type, storage_path, description, captured_at
                FROM finding_evidence
                WHERE finding_id = :finding_id
                ORDER BY captured_at ASC
                """
            ),
            {"finding_id": finding_id},
        )
        items = [
            {
                "evidence_id": str(row[0]),
                "artifact_type": row[1],
                "storage_path": row[2],
                "description": row[3],
                "captured_at": row[4].isoformat() if row[4] else None,
            }
            for row in rows.fetchall()
        ]

    return JSONResponse(
        {
            "finding_id": finding_id,
            "scan_id": scan_id,
            "items": items,
        }
    )


@app.get("/api/v1/queue/dlq/inspect")
async def inspect_dlq() -> JSONResponse:
    queue_states = await inspect_queue_states(
        config.rabbitmq_url,
        [Queues.SCAN_JOBS, Queues.REPORT_JOBS],
    )
    return JSONResponse({"queues": queue_states})


# DLQ Monitoring endpoints
@app.get("/api/v1/queue/dlq/monitor")
async def monitor_dlq() -> JSONResponse:
    "Monitor all DLQ depths and return current state."
    from backend.shared.dlq_monitor import DLQMonitor
    from datetime import datetime, timezone
    monitor = DLQMonitor(config.rabbitmq_url)
    try:
        await monitor.connect()
        depths = await monitor.monitor_all_dlqs()
        total_messages = sum(depths.values())
        return JSONResponse({
            "dlqs": depths,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_messages": total_messages
        })
    finally:
        await monitor.close()


@app.get("/api/v1/queue/dlq/{dlq_name}/inspect")
async def inspect_dlq_messages(dlq_name: str, limit: int = 100) -> JSONResponse:
    "Inspect messages in a specific DLQ."
    from backend.shared.dlq_monitor import DLQMonitor
    from datetime import datetime, timezone
    monitor = DLQMonitor(config.rabbitmq_url)
    try:
        await monitor.connect()
        messages = await monitor.inspect_messages(dlq_name, limit=limit)
        serialized_messages = [
            message.model_dump(mode="json") if hasattr(message, "model_dump") else message
            for message in messages
        ]
        return JSONResponse({
            "dlq": dlq_name.replace(".dlq", ""),
            "messages": serialized_messages,
            "count": len(serialized_messages),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    finally:
        await monitor.close()


@app.post("/api/v1/queue/dlq/{dlq_name}/replay")
async def replay_dlq_messages(dlq_name: str, request: Request) -> JSONResponse:
    "Replay messages from a DLQ to their original queue."
    from backend.shared.dlq_monitor import DLQMonitor
    from datetime import datetime, timezone
    
    request_body = await request.json()
    message_ids = request_body.get("message_ids", [])
    
    monitor = DLQMonitor(config.rabbitmq_url)
    try:
        await monitor.connect()
        
        # Get all messages from the DLQ
        all_messages = await monitor.inspect_messages(dlq_name, limit=1000)
        
        replayed = 0
        failed = 0
        
        for msg in all_messages:
            if msg.message_id in message_ids:
                success = await monitor.replay_message(dlq_name, msg)
                if success:
                    replayed += 1
                else:
                    failed += 1
        
        return JSONResponse({
            "dlq": dlq_name.replace(".dlq", ""),
            "mode": "selective",
            "replayed": replayed,
            "failed": failed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    finally:
        await monitor.close()
