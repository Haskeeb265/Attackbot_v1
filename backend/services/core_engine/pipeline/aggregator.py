from datetime import datetime, timezone
from typing import Optional

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import FindingCandidate, ScanResult
from backend.services.core_engine.repository import ScanRepository
from backend.services.core_engine.dedup import compute_dedup_hash
from backend.shared.queue import QueuePublisher
from backend.shared.schemas.report_jobs import build_report_job_message, ReportJobsPayload, SeverityBreakdown
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage7")

STAGE_NUMBER = 7.0
STAGE_NAME = "aggregation"


async def run(
    ctx: ScanContext,
    scan_result: ScanResult,
    repo: ScanRepository,
    publisher: QueuePublisher,
) -> dict:
    """
    Stage 7: Deduplication, persistence, vulnerability grouping, scan finalization.
    Returns severity_breakdown dict.
    Raises on fatal failure (e.g., DB down) — caller marks scan failed_internal.
    """
    # Deduplicate finding candidates by hash
    seen_hashes: set[str] = set()
    deduped: list[FindingCandidate] = []
    for candidate in scan_result.finding_candidates:
        h = compute_dedup_hash(candidate)
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduped.append(candidate)

    duplicate_count = len(scan_result.finding_candidates) - len(deduped)
    if duplicate_count > 0:
        logger.info("Deduplication complete",
                    scan_id=ctx.scan_id,
                    before=len(scan_result.finding_candidates),
                    after=len(deduped),
                    duplicates_removed=duplicate_count)

    # Persist findings
    saved_count = await repo.save_findings(
        scan_id=ctx.scan_id,
        program_id=ctx.program_id,
        candidates=deduped,
    )

    # Build severity breakdown
    breakdown: dict[str, int] = {
        "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
    }
    for c in deduped:
        sev = c.severity.lower()
        if sev in breakdown:
            breakdown[sev] += 1

    # Determine final scan status
    has_errors = bool(scan_result.stage_errors)
    status = "partial" if has_errors else "completed"

    partial_detail = None
    if has_errors:
        partial_detail = {
            "failed_stages": list(scan_result.stage_errors.keys()),
            "errors": scan_result.stage_errors,
        }

    # Finalize scan row
    await repo.mark_scan_complete(
        scan_id=ctx.scan_id,
        status=status,
        finding_count=saved_count,
        severity_breakdown=breakdown,
        partial_detail=partial_detail,
    )

    # Publish scan.completed → report.jobs
    try:
        sev_breakdown = SeverityBreakdown(
            critical=breakdown.get("critical", 0),
            high=breakdown.get("high", 0),
            medium=breakdown.get("medium", 0),
            low=breakdown.get("low", 0),
            info=breakdown.get("info", 0),
        )
        payload = ReportJobsPayload(
            scan_id=ctx.scan_id,
            program_id=ctx.program_id,
            finding_count=saved_count,
            severity_breakdown=sev_breakdown,
        )
        message = build_report_job_message(payload)
        await publisher.publish("report.jobs", message)
        logger.info("Published scan.completed to report.jobs",
                    scan_id=ctx.scan_id)
    except Exception as e:
        # Non-fatal — scan is complete, report will be picked up by reconciler
        logger.error("Failed to publish to report.jobs",
                     scan_id=ctx.scan_id, error=str(e))

    logger.info("Stage 7 complete",
                scan_id=ctx.scan_id,
                findings_saved=saved_count,
                status=status,
                breakdown=breakdown)
    return breakdown