from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.metrics import download_requests_total, presign_duration_seconds
from backend.services.reporter.repository import ReportRepository
from backend.services.reporter.storage import ReporterStorage
from backend.services.reporter.watchdog import recover_stale_reports
from backend.shared.db import check_db_health, get_session, init_db
from backend.shared.health import ComponentHealth, HealthResponse, HealthStatus
from backend.shared.logging import configure_logging, get_logger
from backend.shared.queue import QueuePublisher, Queues, check_rabbitmq_health, ensure_queue_topology
from backend.shared.schemas.report_jobs import ReportJobsPayload, SeverityBreakdown, build_report_job_message
from backend.shared.storage import check_storage_health, init_storage

settings = ReporterConfig()
configure_logging(settings.service_name, settings.log_level)
log = get_logger(__name__)

scheduler = AsyncIOScheduler()
_queue_publisher: QueuePublisher | None = None
_storage: ReporterStorage | None = None
_upstream_cache: dict[str, tuple[bool, float]] = {}


class GenerateReportsRequest(BaseModel):
    scan_id: str
    formats_requested: list[Literal["pdf", "docx"]] = Field(default_factory=list)
    include_evidence_screenshots: bool = True


def _get_queue_publisher() -> QueuePublisher:
    if _queue_publisher is None:
        raise RuntimeError("Queue publisher is not initialized")
    return _queue_publisher


def _get_storage() -> ReporterStorage:
    if _storage is None:
        raise RuntimeError("Reporter storage is not initialized")
    return _storage


def _normalize_formats(requested: list[str]) -> list[str]:
    if not requested:
        return settings.get_default_formats()
    normalized = [fmt.strip().lower() for fmt in requested if fmt and fmt.strip()]
    deduped: list[str] = []
    for fmt in normalized:
        if fmt not in deduped:
            deduped.append(fmt)
    return deduped or settings.get_default_formats()


async def _check_upstream_cached(url: str, service_name: str, ttl: int) -> bool:
    cached = _upstream_cache.get(service_name)
    if cached and (time.monotonic() - cached[1]) < ttl:
        return cached[0]

    timeout = httpx.Timeout(
        timeout=settings.upstream_timeout_seconds,
        connect=settings.upstream_connect_timeout_seconds,
    )
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/api/v1/health")
            healthy = response.status_code == 200
    except Exception:
        healthy = False

    _upstream_cache[service_name] = (healthy, time.monotonic())
    return healthy


async def _fetch_scan(scan_id: str) -> dict[str, Any] | None:
    timeout = httpx.Timeout(
        timeout=settings.upstream_timeout_seconds,
        connect=settings.upstream_connect_timeout_seconds,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{settings.core_engine_api_url}/api/v1/scans/{scan_id}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _extract_partial_stages(scan_payload: dict[str, Any]) -> list[str]:
    partial_detail = scan_payload.get("partial_detail")
    if not isinstance(partial_detail, dict):
        return []
    stages = partial_detail.get("failed_stages")
    if not isinstance(stages, list):
        return []
    return [str(stage) for stage in stages]


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    global _queue_publisher, _storage

    log.info("service_starting", service=settings.service_name, port=settings.port)
    try:
        from backend.shared.tracing import init_tracing, instrument_httpx

        init_tracing(settings.service_name, settings.jaeger_endpoint)
        instrument_httpx()
    except Exception as exc:
        log.warning("tracing_init_failed", error=str(exc))
    settings.require_fields(
        [
            "database_url",
            "rabbitmq_url",
            "minio_endpoint",
            "minio_access_key",
            "minio_secret_key",
        ]
    )

    init_db(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
    init_storage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    await ensure_queue_topology(settings.rabbitmq_url)

    _queue_publisher = QueuePublisher(settings.rabbitmq_url)
    await _queue_publisher.connect()
    await _queue_publisher.ensure_queue(Queues.REPORTS_COMPLETED)

    _storage = ReporterStorage(settings.reports_bucket, settings.evidence_bucket)

    Path(settings.temp_output_dir).mkdir(parents=True, exist_ok=True)

    scheduler.add_job(
        recover_stale_reports,
        "interval",
        seconds=settings.report_watchdog_interval_seconds,
        kwargs={"stale_minutes": settings.report_watchdog_stale_minutes},
        id="report_watchdog",
        replace_existing=True,
    )
    scheduler.start()
    log.info("service_ready", service=settings.service_name)
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        if _queue_publisher is not None:
            await _queue_publisher.close()
        log.info("service_stopping", service=settings.service_name)


app = FastAPI(title="AttackBot Reporter", version="1.0.0", lifespan=lifespan)
try:
    from backend.shared.tracing import instrument_fastapi

    instrument_fastapi(app)
except Exception as exc:
    log.warning("tracing_fastapi_instrumentation_failed", error=str(exc))
Instrumentator().instrument(app).expose(app)


@app.get("/api/v1/reports")
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    scan_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    async with get_session() as session:
        repository = ReportRepository(session)
        return await repository.list_reports(
            page=page,
            page_size=page_size,
            scan_id_filter=scan_id,
            status_filter=status,
        )


@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: str) -> dict[str, Any]:
    async with get_session() as session:
        repository = ReportRepository(session)
        report = await repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/api/v1/scans/{scan_id}/reports")
async def get_reports_by_scan(scan_id: str) -> dict[str, Any]:
    async with get_session() as session:
        repository = ReportRepository(session)
        items = await repository.get_reports_by_scan(scan_id)
    return {
        "scan_id": scan_id,
        "items": items,
        "count": len(items),
    }


@app.get("/api/v1/reports/{report_id}/download")
async def download_report(report_id: str) -> dict[str, Any]:
    async with get_session() as session:
        repository = ReportRepository(session)
        report = await repository.get_report(report_id)

    if report is None:
        download_requests_total.labels(status="not_found").inc()
        raise HTTPException(status_code=404, detail="Report not found")

    status = report["status"]
    if status in {"generating", "failed"}:
        download_requests_total.labels(status="not_ready").inc()
        raise HTTPException(
            status_code=409,
            detail=f"Report is not downloadable while status is '{status}'",
        )

    if status not in {"completed", "partial"}:
        download_requests_total.labels(status="invalid_state").inc()
        raise HTTPException(
            status_code=409,
            detail=f"Report is not in a terminal downloadable state: '{status}'",
        )

    storage_path = report.get("storage_path")
    if not storage_path:
        download_requests_total.labels(status="artifact_missing").inc()
        raise HTTPException(status_code=409, detail="Report artifact is not available")

    presign_started = time.monotonic()
    download_url = await _get_storage().get_presigned_download_url(
        storage_path=storage_path,
        expiry_seconds=settings.report_presign_expiry_seconds,
    )
    presign_duration_seconds.observe(max(time.monotonic() - presign_started, 0.0))
    download_requests_total.labels(status="success").inc()

    return {
        "report_id": report_id,
        "status": status,
        "download_url": download_url,
        "expires_in_seconds": settings.report_presign_expiry_seconds,
    }


@app.post("/api/v1/reports/generate", status_code=202)
async def generate_reports(request: GenerateReportsRequest) -> JSONResponse:
    scan_payload = await _fetch_scan(request.scan_id)
    if scan_payload is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_status = str(scan_payload.get("status", "")).lower()
    if scan_status not in {"completed", "partial"}:
        raise HTTPException(
            status_code=409,
            detail=f"Reports can only be generated for completed/partial scans (got '{scan_status}')",
        )

    program_id = scan_payload.get("program_id")
    if not program_id:
        raise HTTPException(status_code=500, detail="Scan payload missing program_id")

    formats = _normalize_formats(request.formats_requested)

    async with get_session() as session:
        repository = ReportRepository(session)
        report_ids: dict[str, str] = {}
        for format_name in formats:
            report_id = await repository.create_or_reset_report(
                scan_id=request.scan_id,
                program_id=str(program_id),
                format_name=format_name,
            )
            report_ids[format_name] = report_id

    severity_breakdown = dict(scan_payload.get("severity_breakdown") or {})
    if "info" in severity_breakdown and "informational" not in severity_breakdown:
        severity_breakdown["informational"] = severity_breakdown["info"]
    normalized_severity = SeverityBreakdown.model_validate(severity_breakdown)

    payload = ReportJobsPayload(
        scan_id=request.scan_id,
        program_id=str(program_id),
        status=scan_status,
        partial_stages=_extract_partial_stages(scan_payload),
        has_findings=int(scan_payload.get("finding_count") or 0) > 0,
        finding_count=int(scan_payload.get("finding_count") or 0),
        verified_count=0,
        severity_breakdown=normalized_severity,
        formats_requested=[fmt for fmt in formats if fmt in {"pdf", "docx"}],
        report_ids=report_ids,
        include_evidence_screenshots=request.include_evidence_screenshots,
    )
    message = build_report_job_message(payload, source_service=settings.service_name)

    published = await _get_queue_publisher().publish(Queues.REPORT_JOBS, message)
    if not published:
        raise HTTPException(status_code=503, detail="Failed to enqueue report generation")

    return JSONResponse(
        status_code=202,
        content={
            "scan_id": request.scan_id,
            "enqueued": True,
            "report_ids": report_ids,
        },
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_ok = await check_db_health()
    rabbitmq_ok = await check_rabbitmq_health(
        settings.rabbitmq_url,
        [Queues.REPORT_JOBS, Queues.REPORTS_COMPLETED],
    )
    storage_ok = check_storage_health()

    core_engine_ok = await _check_upstream_cached(
        settings.core_engine_api_url,
        "core_engine",
        settings.upstream_health_cache_ttl_seconds,
    )
    scraper_ok = await _check_upstream_cached(
        settings.scraper_api_url,
        "scraper",
        settings.upstream_health_cache_ttl_seconds,
    )

    components = {
        "database": ComponentHealth(
            status=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY
        ),
        "rabbitmq": ComponentHealth(
            status=HealthStatus.HEALTHY if rabbitmq_ok else HealthStatus.UNHEALTHY
        ),
        "storage": ComponentHealth(
            status=HealthStatus.HEALTHY if storage_ok else HealthStatus.UNHEALTHY
        ),
        "core_engine": ComponentHealth(
            status=HealthStatus.HEALTHY if core_engine_ok else HealthStatus.UNHEALTHY
        ),
        "scraper": ComponentHealth(
            status=HealthStatus.HEALTHY if scraper_ok else HealthStatus.UNHEALTHY
        ),
        "scheduler": ComponentHealth(
            status=HealthStatus.HEALTHY if scheduler.running else HealthStatus.UNHEALTHY
        ),
        "attack_graph_engine": ComponentHealth(
            status=HealthStatus.DEGRADED,
            detail="chain_detail_api_not_yet_available",
        ),
    }

    statuses = [component.status for component in components.values()]
    if any(status == HealthStatus.UNHEALTHY for status in statuses):
        overall = HealthStatus.UNHEALTHY
    elif any(status == HealthStatus.DEGRADED for status in statuses):
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.HEALTHY

    return HealthResponse(
        status=overall,
        service=settings.service_name,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )
