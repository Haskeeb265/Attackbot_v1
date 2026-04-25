from __future__ import annotations

import asyncio
import os
import time
import zipfile
from pathlib import Path
from typing import Any

from backend.services.reporter.clients.attack_graph import AttackGraphClient
from backend.services.reporter.clients.core_engine import CoreEngineClient
from backend.services.reporter.clients.scraper import ScraperClient
from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.evidence import cleanup_evidence_temp_files, fetch_all_evidence
from backend.services.reporter.metrics import (
    record_generation,
    record_generation_failure,
    record_partial_reason,
    zero_findings_total,
)
from backend.services.reporter.models import ParsedScan, ReproductionPackDraft
from backend.services.reporter.parsing import ParsedScanBuilder
from backend.services.reporter.publisher import ReportsCompletedPublisher
from backend.services.reporter.renderers.docx import DocxRenderer
from backend.services.reporter.renderers.pdf import PdfRenderer
from backend.services.reporter.renderers.sections import build_render_plan
from backend.services.reporter.repository import ReportRepository
from backend.services.reporter.reproduction import build_reproduction_packs
from backend.services.reporter.storage import ReporterStorage
from backend.shared.db import get_session, init_db
from backend.shared.logging import get_logger
from backend.shared.queue import QueuePublisher, Queues
from backend.shared.idempotency import IdempotencyService
from backend.shared.schemas.envelope import MessageEnvelope
from backend.shared.schemas.report_jobs import ReportJobsPayload
from backend.shared.storage import init_storage

settings = ReporterConfig()
log = get_logger(__name__)

init_db(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
init_storage(
    endpoint=settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)

_storage = ReporterStorage(settings.reports_bucket, settings.evidence_bucket)

def process_report_task(envelope_dict: dict[str, Any]) -> None:
    """
    Process a report task message from the queue.
    Entry point for Celery workers.
    """
    process_report_envelope_sync(envelope_dict)



def process_report_envelope_sync(envelope_dict: dict[str, Any]) -> None:
    asyncio.run(process_report_envelope(envelope_dict))


async def process_report_envelope(envelope_dict: dict[str, Any]) -> None:
    envelope = MessageEnvelope.model_validate(envelope_dict)
    payload = ReportJobsPayload.model_validate(envelope.payload)
    
    # Idempotency check
    event_id = envelope.event_id
    if event_id:
        async with get_session() as session:
            idempotency = IdempotencyService(session)
            cached = await idempotency.check_and_record(
                event_id=event_id,
                service="reporter",
                operation="report.generate",
            )
            if cached is not None:
                log.info("Report message already processed - skipping", event_id=event_id)
                return

    formats = payload.formats_requested or settings.get_default_formats()
    Path(settings.temp_output_dir).mkdir(parents=True, exist_ok=True)

    parsed_scan, shared_partial_reasons = await _build_parsed_scan(payload)

    queue_publisher = QueuePublisher(settings.rabbitmq_url)
    await queue_publisher.connect()
    await queue_publisher.ensure_queue(Queues.REPORTS_COMPLETED)
    completion_publisher = ReportsCompletedPublisher(queue_publisher)

    try:
        # Formats rendered sequentially - both renderers share the ParsedScan object
        # including mutable evidence.local_tmp_path fields. Parallel rendering would
        # require deep-copying or coordinated temp-file ownership.
        for format_name in formats:
            await _process_single_format(
                payload=payload,
                parsed_scan=parsed_scan,
                format_name=format_name,
                shared_partial_reasons=list(shared_partial_reasons),
                completion_publisher=completion_publisher,
            )
    finally:
        cleanup_evidence_temp_files(parsed_scan)
        await queue_publisher.close()


async def _build_parsed_scan(payload: ReportJobsPayload) -> tuple[ParsedScan, list[str]]:
    core_client = CoreEngineClient(
        settings.core_engine_api_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        connect_timeout_seconds=settings.upstream_connect_timeout_seconds,
    )
    scraper_client = ScraperClient(
        settings.scraper_api_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        connect_timeout_seconds=settings.upstream_connect_timeout_seconds,
    )
    attack_graph_client = AttackGraphClient(settings.attack_graph_api_url, timeout_seconds=5)

    scan_payload = await core_client.get_scan(str(payload.scan_id))
    findings_payload = await core_client.get_findings(str(payload.scan_id))
    program_payload = await scraper_client.get_program(str(payload.program_id))
    scope_payload = await scraper_client.get_scope(str(payload.program_id))

    shared_partial_reasons: list[str] = []
    if str(payload.status).lower() == "partial":
        shared_partial_reasons.append("scan_partial")

    if payload.exploit_chains:
        missing_details = 0
        for chain_ref in payload.exploit_chains:
            chain_detail = await attack_graph_client.get_chain_detail(str(chain_ref.chain_id))
            if chain_detail is None:
                missing_details += 1
        if missing_details > 0:
            shared_partial_reasons.append("attack_graph_chain_detail_unavailable")

    parsed_scan = ParsedScanBuilder().build(
        scan_payload=scan_payload,
        findings_payload=findings_payload,
        program_payload=program_payload,
        scope_payload=scope_payload,
        exploit_chain_refs=[chain.model_dump(mode="json") for chain in payload.exploit_chains],
        include_evidence_screenshots=payload.include_evidence_screenshots,
    )

    if parsed_scan.is_clean():
        zero_findings_total.inc()
        log.info("reporter_zero_findings_scan", scan_id=str(parsed_scan.scan_id))

    evidence_partial_reasons = await fetch_all_evidence(
        parsed_scan=parsed_scan,
        core_client=core_client,
        storage=_storage,
        settings=settings,
    )
    shared_partial_reasons.extend(evidence_partial_reasons)

    return parsed_scan, shared_partial_reasons


async def _process_single_format(
    payload: ReportJobsPayload,
    parsed_scan: ParsedScan,
    format_name: str,
    shared_partial_reasons: list[str],
    completion_publisher: ReportsCompletedPublisher,
) -> None:
    report_id: str | None = None
    local_path: str | None = None
    format_partial_reasons = list(shared_partial_reasons)
    packs: list[ReproductionPackDraft] = []
    started_at = time.monotonic()

    try:
        async with get_session() as session:
            repository = ReportRepository(session)
            if payload.report_ids and format_name in payload.report_ids:
                report_id = str(payload.report_ids[format_name])
                await repository.mark_generating(report_id)
            else:
                report_id = await repository.create_or_reset_report(
                    scan_id=str(payload.scan_id),
                    program_id=str(payload.program_id),
                    format_name=format_name,
                )
            packs, pack_errors, used_fallback = build_reproduction_packs(parsed_scan.findings)
            await repository.replace_reproduction_packs(report_id=report_id, packs=packs)
            if pack_errors:
                log.warning(
                    "report_reproduction_pack_errors",
                    report_id=report_id,
                    scan_id=str(payload.scan_id),
                    format=format_name,
                    errors=pack_errors,
                )
            if used_fallback:
                format_partial_reasons.append("reproduction_pack_fallback")

        local_path, render_partial_reasons = _render_artifact(
            report_id=report_id,
            parsed_scan=parsed_scan,
            format_name=format_name,
            packs=packs,
        )
        format_partial_reasons.extend(render_partial_reasons)
        _validate_rendered_artifact(format_name, local_path)

        _assert_upload_not_forced_failure(report_id)

        storage_path, file_size_bytes = await _storage.upload_report(
            report_id=report_id,
            format_name=format_name,
            local_path=local_path,
        )

        deduped_reasons = _dedupe_preserve_order(format_partial_reasons)
        final_status = "partial" if deduped_reasons else "completed"
        reason_text = ",".join(deduped_reasons) if deduped_reasons else None

        async with get_session() as session:
            repository = ReportRepository(session)
            if final_status == "partial":
                await repository.mark_partial(
                    report_id=report_id,
                    storage_path=storage_path,
                    file_size_bytes=file_size_bytes,
                    reason=reason_text or "partial_generation",
                )
                for reason in deduped_reasons:
                    record_partial_reason(reason)
            else:
                await repository.mark_completed(
                    report_id=report_id,
                    storage_path=storage_path,
                    file_size_bytes=file_size_bytes,
                )
            report_row = await repository.get_report(report_id)

        record_generation(
            format_name=format_name,
            status=final_status,
            duration_seconds=time.monotonic() - started_at,
        )

        if report_row is not None:
            await completion_publisher.publish_report_completed(report_row)

        log.info(
            "report_artifact_generated",
            report_id=report_id,
            scan_id=str(payload.scan_id),
            program_id=str(payload.program_id),
            format=format_name,
            status=final_status,
        )
    except Exception as exc:
        log.error(
            "report_artifact_generation_failed",
            report_id=report_id,
            scan_id=str(payload.scan_id),
            program_id=str(payload.program_id),
            format=format_name,
            error=str(exc),
        )
        record_generation_failure(format_name=format_name, reason=type(exc).__name__.lower())
        record_generation(
            format_name=format_name,
            status="failed",
            duration_seconds=time.monotonic() - started_at,
        )
        if report_id is not None:
            async with get_session() as session:
                repository = ReportRepository(session)
                await repository.mark_failed(report_id=report_id, error_detail=str(exc))
    finally:
        if local_path is not None:
            _safe_unlink(local_path)


def _safe_unlink(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        return
    except Exception:
        log.warning("report_temp_file_cleanup_failed", path=path)


def _render_artifact(
    report_id: str,
    parsed_scan: ParsedScan,
    format_name: str,
    packs: list[ReproductionPackDraft],
) -> tuple[str, list[str]]:
    if format_name == "pdf":
        return PdfRenderer(settings).generate(
            report_id=report_id,
            parsed_scan=parsed_scan,
            packs=packs,
        )
    if format_name == "docx":
        return DocxRenderer(settings).generate(
            report_id=report_id,
            parsed_scan=parsed_scan,
            packs=packs,
        )
    raise ValueError(f"Unsupported format: {format_name}")


def _build_report_lines(parsed_scan: ParsedScan) -> list[str]:
    plan = build_render_plan(
        parsed_scan=parsed_scan,
        packs=[],
        include_raw_http_appendix=settings.include_raw_http_appendix,
    )
    return plan.lines


def _validate_rendered_artifact(format_name: str, local_path: str) -> None:
    if not os.path.exists(local_path):
        raise ValueError(f"Rendered artifact missing at path: {local_path}")

    if os.path.getsize(local_path) <= 0:
        raise ValueError(f"Rendered artifact is empty: {local_path}")

    if format_name == "pdf":
        with open(local_path, "rb") as handle:
            prefix = handle.read(4)
        if prefix != b"%PDF":
            raise ValueError("Rendered PDF is invalid: missing %PDF header")
        return

    if format_name == "docx":
        if not zipfile.is_zipfile(local_path):
            raise ValueError("Rendered DOCX is invalid: not a zip archive")
        with zipfile.ZipFile(local_path, "r") as archive:
            names = set(archive.namelist())
        if "word/document.xml" not in names:
            raise ValueError("Rendered DOCX is invalid: missing word/document.xml")
        return

    raise ValueError(f"Unsupported report format for validation: {format_name}")


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _assert_upload_not_forced_failure(report_id: str | None) -> None:
    if report_id is None:
        return
    forced_ids = settings.get_force_upload_failure_report_ids()
    if not forced_ids:
        return
    if "*" in forced_ids or report_id in forced_ids:
        raise RuntimeError(f"forced_upload_failure:{report_id}")
