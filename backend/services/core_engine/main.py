import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.services.core_engine.config import EngineConfig
from backend.services.core_engine.watchdog import recover_stuck_scans
from backend.shared.db import init_db, get_session, check_db_health
from backend.shared.health import HealthResponse, ComponentHealth, HealthStatus
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import QueuePublisher

config = EngineConfig()
configure_logging(config.service_name)
logger = get_logger("core_engine.main")

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(config.database_url)
    publisher = QueuePublisher(config)

    async def _republish(program_id: str):
        # Minimal republish — fetch program scope from Scraper API and requeue
        # Full implementation: call scraper API GET /programs/{id}/scope
        logger.info("Republish requested", program_id=program_id)

    scheduler.add_job(
        recover_stuck_scans,
        "interval",
        seconds=config.watchdog_interval_seconds,
        kwargs={"republish_fn": _republish,
                "stale_hours": config.watchdog_stale_threshold_hours},
    )
    scheduler.start()
    logger.info("Core Engine started", watchdog_interval=config.watchdog_interval_seconds)
    yield
    scheduler.shutdown()


app = FastAPI(title="Core Engine", lifespan=lifespan)


@app.get("/api/v1/health")
async def health() -> JSONResponse:
    from datetime import datetime, timezone
    db_ok = await check_db_health()
    status = HealthStatus.HEALTHY if db_ok else HealthStatus.DEGRADED
    return JSONResponse(
        content=HealthResponse(
            status=status,
            service=config.service_name,
            timestamp=datetime.now(timezone.utc),
            components={
                "database": ComponentHealth(
                    status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
                ),
                "scheduler": ComponentHealth(
                    status=HealthStatus.HEALTHY if scheduler.running else HealthStatus.UNHEALTHY
                ),
            },
        ).model_dump(mode="json")
    )


@app.post("/api/v1/scans/start")
async def start_scan(body: dict) -> JSONResponse:
    """
    Manual scan trigger — for testing. Publishes directly to scan.jobs.
    Body: { "program_id": "uuid", "scope": {...}, "feature_flags": {...} }
    """
    from backend.shared.schemas.scan_jobs import build_scan_job_message, ScanJobsPayload
    publisher = QueuePublisher(config)
    msg = build_scan_job_message(ScanJobsPayload(**body))
    await publisher.publish("scan.jobs", msg)
    return JSONResponse({"status": "queued", "program_id": body.get("program_id")})


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
                       is_verified, source, created_at
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
            }
            for r in rows.fetchall()
        ]
    return JSONResponse({"findings": findings, "count": len(findings)})


@app.get("/api/v1/queue/dlq/inspect")
async def inspect_dlq() -> JSONResponse:
    """Stub — DLQ inspection via RabbitMQ management API. Full impl in M10."""
    return JSONResponse({"message": "DLQ inspection not yet implemented", "queues": []})