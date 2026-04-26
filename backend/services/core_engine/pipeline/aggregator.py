from datetime import datetime, timezone
from typing import Optional, Any
from uuid import UUID

from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.models import FindingCandidate, ScanResult
from backend.services.core_engine.repository import ScanRepository
from backend.services.core_engine.dedup import compute_dedup_hash
from backend.shared.queue import QueuePublisher
from backend.shared.schemas.report_jobs import (
    build_report_job_message, 
    ReportJobsPayload, 
    SeverityBreakdown,
    ScanSummary,
    FindingData,
    EvidenceData
)
from backend.shared.models.scans import Scan
from backend.shared.db import get_session
from backend.shared.logging import get_logger

logger = get_logger("core_engine.stage10")

STAGE_NUMBER = 10.0
STAGE_NAME = "aggregation"


class ReportAggregator:
    """
    Aggregates scan data and prepares payload for report generation.
    Supports v2 payloads with embedded data to eliminate HTTP calls from Reporter.
    """
    
    def __init__(self, repo: Optional[ScanRepository] = None):
        self.repo = repo
        self._session = None
    
    async def _get_session(self):
        """Get or create database session."""
        if self._session is None:
            self._session = await get_session().__aenter__()
        return self._session
    
    async def _get_scan(self, scan_id: UUID) -> Optional[Scan]:
        """Get scan by ID from database."""
        if self.repo:
            # Use provided repository
            session = self.repo.session
        else:
            session = await self._get_session()
        
        result = await session.execute(
            select(Scan).where(Scan.scan_id == scan_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_findings_for_scan(self, scan_id: UUID) -> list[dict]:
        """Get findings for a scan from database."""
        if self.repo:
            session = self.repo.session
        else:
            session = await self._get_session()
        
        from sqlalchemy import text
        rows = await session.execute(
            text("""
                SELECT finding_id, scan_id, program_id, title, vulnerability_type,
                       severity, cvss_score, cvss_vector, affected_url,
                       affected_parameter, description, reproduction_steps,
                       is_verified, is_false_positive, false_positive_reason,
                       deduplication_hash, source, raw_output, created_at
                FROM findings WHERE scan_id = :scan_id ORDER BY created_at
            """),
            {"scan_id": str(scan_id)},
        )
        
        findings = []
        for row in rows.fetchall():
            findings.append({
                "finding_id": str(row[0]),
                "scan_id": str(row[1]),
                "program_id": str(row[2]),
                "title": row[3],
                "vulnerability_type": row[4],
                "severity": row[5] or "unknown",
                "cvss_score": float(row[6]) if row[6] is not None else None,
                "cvss_vector": row[7],
                "affected_url": row[8],
                "affected_parameter": row[9],
                "description": row[10],
                "reproduction_steps": row[11],
                "is_verified": bool(row[12]),
                "is_false_positive": bool(row[13]),
                "false_positive_reason": row[14],
                "deduplication_hash": row[15],
                "source": row[16],
                "raw_output": row[17],
                "created_at": row[18],
            })
        return findings
    
    async def _get_evidence_for_scan(self, scan_id: UUID) -> list[dict]:
        """Get evidence for a scan from database."""
        if self.repo:
            session = self.repo.session
        else:
            session = await self._get_session()
        
        from sqlalchemy import text
        rows = await session.execute(
            text("""
                SELECT fe.evidence_id, fe.finding_id, fe.artifact_type,
                       fe.storage_path, fe.description, fe.captured_at
                FROM finding_evidence fe
                JOIN findings f ON fe.finding_id = f.finding_id
                WHERE f.scan_id = :scan_id ORDER BY fe.captured_at
            """),
            {"scan_id": str(scan_id)},
        )
        
        evidence = []
        for row in rows.fetchall():
            evidence.append({
                "evidence_id": str(row[0]),
                "finding_id": str(row[1]),
                "artifact_type": row[2],
                "storage_path": row[3],
                "description": row[4],
                "captured_at": row[5],
            })
        return evidence
    
    def _to_finding_data(self, finding_dict: dict) -> FindingData:
        """Convert finding dict to FindingData schema."""
        return FindingData(
            finding_id=UUID(finding_dict["finding_id"]),
            title=finding_dict.get("title", ""),
            severity=finding_dict.get("severity", "unknown"),
            vulnerability_type=finding_dict.get("vulnerability_type"),
            cvss_score=finding_dict.get("cvss_score"),
            cvss_vector=finding_dict.get("cvss_vector"),
            affected_url=finding_dict.get("affected_url"),
            affected_parameter=finding_dict.get("affected_parameter"),
            description=finding_dict.get("description"),
            reproduction_steps=finding_dict.get("reproduction_steps"),
            is_verified=finding_dict.get("is_verified", False),
            is_false_positive=finding_dict.get("is_false_positive", False),
            false_positive_reason=finding_dict.get("false_positive_reason"),
            deduplication_hash=finding_dict.get("deduplication_hash"),
            source=finding_dict.get("source"),
            raw_output=finding_dict.get("raw_output"),
            created_at=finding_dict.get("created_at"),
            program_id=UUID(finding_dict["program_id"]) if finding_dict.get("program_id") else None,
        )
    
    def _to_evidence_data(self, evidence_dict: dict) -> EvidenceData:
        """Convert evidence dict to EvidenceData schema."""
        return EvidenceData(
            evidence_id=UUID(evidence_dict["evidence_id"]),
            finding_id=UUID(evidence_dict["finding_id"]),
            artifact_type=evidence_dict.get("artifact_type"),
            storage_path=evidence_dict.get("storage_path"),
            description=evidence_dict.get("description"),
            captured_at=evidence_dict.get("captured_at"),
        )
    
    async def aggregate_and_publish(
        self,
        scan_id: UUID,
        program_id: UUID,
        formats: list[str] = ["pdf", "docx"]
    ) -> ReportJobsPayload:
        """
        Aggregate scan data and create v2 payload with embedded data.
        
        Args:
            scan_id: The scan ID to aggregate
            program_id: The program ID
            formats: List of report formats to generate
            
        Returns:
            ReportJobsPayload with embedded scan_summary, findings, and evidence
        """
        from sqlalchemy.future import select
        
        # Get scan from database
        if self.repo:
            session = self.repo.session
        else:
            session = await self._get_session()
        
        result = await session.execute(
            select(Scan).where(Scan.scan_id == scan_id)
        )
        scan = result.scalar_one_or_none()
        
        if scan is None:
            raise ValueError(f"Scan not found: {scan_id}")
        
        # Get findings and evidence
        findings_data = await self._get_findings_for_scan(scan.scan_id)
        evidence_data = await self._get_evidence_for_scan(scan.scan_id)
        
        # Build severity breakdown
        severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for f in findings_data:
            sev = f.get("severity", "unknown").lower()
            if sev in severity_breakdown:
                severity_breakdown[sev] += 1
        
        # Build v2 payload with embedded data
        payload = ReportJobsPayload(
            scan_id=scan.scan_id,
            program_id=scan.program_id,
            status=scan.status,
            partial_stages=[],
            has_findings=len(findings_data) > 0,
            finding_count=len(findings_data),
            verified_count=sum(1 for f in findings_data if f.get("is_verified", False)),
            severity_breakdown=SeverityBreakdown(
                critical=severity_breakdown.get("critical", 0),
                high=severity_breakdown.get("high", 0),
                medium=severity_breakdown.get("medium", 0),
                low=severity_breakdown.get("low", 0),
                informational=severity_breakdown.get("informational", 0),
            ),
            exploit_chains=[],
            formats_requested=formats,
            report_ids=None,
            include_evidence_screenshots=True,
            payload_version=2,
            scan_summary=ScanSummary(
                scan_id=scan.scan_id,
                program_id=scan.program_id,
                started_at=scan.started_at,
                completed_at=scan.completed_at,
                status=scan.status,
                total_findings=len(findings_data),
                severity_breakdown=severity_breakdown,
                partial_detail=scan.partial_detail,
                error_detail=scan.error_detail,
            ),
            findings=[self._to_finding_data(f) for f in findings_data],
            evidence=[self._to_evidence_data(e) for e in evidence_data],
        )
        
        return payload


async def run(
    ctx: ScanContext,
    scan_result: ScanResult,
    repo: ScanRepository,
    publisher: QueuePublisher,
) -> dict:
    """
    Stage 10: Deduplication, persistence, vulnerability grouping, scan finalization.
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

    # Publish scan.completed → report.jobs with v2 embedded data
    handoff_started_at = datetime.now(timezone.utc)
    try:
        # Get scan for embedded data
        scan = await repo.session.get(Scan, ctx.scan_id)
        
        # Get findings and evidence for embedding
        findings_data = []
        evidence_data = []
        
        if scan:
            # Query findings
            from sqlalchemy import text
            rows = await repo.session.execute(
                text("""
                    SELECT finding_id, scan_id, program_id, title, vulnerability_type,
                           severity, cvss_score, cvss_vector, affected_url,
                           affected_parameter, description, reproduction_steps,
                           is_verified, is_false_positive, false_positive_reason,
                           deduplication_hash, source, raw_output, created_at
                    FROM findings WHERE scan_id = :scan_id ORDER BY created_at
                """),
                {"scan_id": str(ctx.scan_id)},
            )
            for row in rows.fetchall():
                findings_data.append({
                    "finding_id": str(row[0]),
                    "scan_id": str(row[1]),
                    "program_id": str(row[2]),
                    "title": row[3],
                    "vulnerability_type": row[4],
                    "severity": row[5] or "unknown",
                    "cvss_score": float(row[6]) if row[6] is not None else None,
                    "cvss_vector": row[7],
                    "affected_url": row[8],
                    "affected_parameter": row[9],
                    "description": row[10],
                    "reproduction_steps": row[11],
                    "is_verified": bool(row[12]),
                    "is_false_positive": bool(row[13]),
                    "false_positive_reason": row[14],
                    "deduplication_hash": row[15],
                    "source": row[16],
                    "raw_output": row[17],
                    "created_at": row[18],
                })
            
            # Query evidence
            rows = await repo.session.execute(
                text("""
                    SELECT fe.evidence_id, fe.finding_id, fe.artifact_type,
                           fe.storage_path, fe.description, fe.captured_at
                    FROM finding_evidence fe
                    JOIN findings f ON fe.finding_id = f.finding_id
                    WHERE f.scan_id = :scan_id ORDER BY fe.captured_at
                """),
                {"scan_id": str(ctx.scan_id)},
            )
            for row in rows.fetchall():
                evidence_data.append({
                    "evidence_id": str(row[0]),
                    "finding_id": str(row[1]),
                    "artifact_type": row[2],
                    "storage_path": row[3],
                    "description": row[4],
                    "captured_at": row[5],
                })
        
        sev_breakdown = SeverityBreakdown(
            critical=breakdown.get("critical", 0),
            high=breakdown.get("high", 0),
            medium=breakdown.get("medium", 0),
            low=breakdown.get("low", 0),
            informational=breakdown.get("info", 0),  # schema uses "informational" not "info"
        )
        
        # Create v2 payload with embedded data
        scan_summary = None
        if scan:
            scan_summary = ScanSummary(
                scan_id=scan.scan_id,
                program_id=scan.program_id,
                started_at=scan.started_at,
                completed_at=scan.completed_at,
                status=scan.status,
                total_findings=saved_count,
                severity_breakdown=breakdown,
                partial_detail=scan.partial_detail,
                error_detail=scan.error_detail,
            )
        
        payload = ReportJobsPayload(
            scan_id=ctx.scan_id,
            program_id=ctx.program_id,
            status=status,
            partial_stages=list(scan_result.stage_errors.keys()),
            has_findings=saved_count > 0,
            finding_count=saved_count,
            verified_count=0,
            severity_breakdown=sev_breakdown,
            exploit_chains=[],
            formats_requested=["pdf", "docx"],
            report_ids=None,
            include_evidence_screenshots=True,
            payload_version=2,  # V2 with embedded data
            scan_summary=scan_summary,
            findings=[FindingData(
                finding_id=UUID(f["finding_id"]),
                title=f.get("title", ""),
                severity=f.get("severity", "unknown"),
                vulnerability_type=f.get("vulnerability_type"),
                cvss_score=f.get("cvss_score"),
                cvss_vector=f.get("cvss_vector"),
                affected_url=f.get("affected_url"),
                affected_parameter=f.get("affected_parameter"),
                description=f.get("description"),
                reproduction_steps=f.get("reproduction_steps"),
                is_verified=f.get("is_verified", False),
                is_false_positive=f.get("is_false_positive", False),
                false_positive_reason=f.get("false_positive_reason"),
                deduplication_hash=f.get("deduplication_hash"),
                source=f.get("source"),
                raw_output=f.get("raw_output"),
                created_at=f.get("created_at"),
                program_id=UUID(f["program_id"]) if f.get("program_id") else None,
            ) for f in findings_data],
            evidence=[EvidenceData(
                evidence_id=UUID(e["evidence_id"]),
                finding_id=UUID(e["finding_id"]),
                artifact_type=e.get("artifact_type"),
                storage_path=e.get("storage_path"),
                description=e.get("description"),
                captured_at=e.get("captured_at"),
            ) for e in evidence_data],
        )
        message = build_report_job_message(payload)
        published = await publisher.publish("report.jobs", message)
        if not published:
            raise RuntimeError("report.jobs publish returned False")
        await repo.record_stage(
            ctx.scan_id,
            10.1,
            "report_handoff",
            "completed",
            handoff_started_at,
            output_summary={"queue": "report.jobs", "has_findings": saved_count > 0, "payload_version": 2},
        )
        logger.info("Published scan.completed to report.jobs with embedded data",
                    scan_id=ctx.scan_id, finding_count=saved_count)
    except Exception as e:
        await repo.record_stage(
            ctx.scan_id,
            10.1,
            "report_handoff",
            "failed",
            handoff_started_at,
            error_detail=str(e),
        )
        logger.error("Failed to publish to report.jobs",
                     scan_id=ctx.scan_id, error=str(e))
        # Fallback to v1 payload without embedded data
        sev_breakdown_v1 = SeverityBreakdown(
            critical=breakdown.get("critical", 0),
            high=breakdown.get("high", 0),
            medium=breakdown.get("medium", 0),
            low=breakdown.get("low", 0),
            informational=breakdown.get("info", 0),
        )
        payload_v1 = ReportJobsPayload(
            scan_id=ctx.scan_id,
            program_id=ctx.program_id,
            status=status,
            partial_stages=list(scan_result.stage_errors.keys()),
            has_findings=saved_count > 0,
            finding_count=saved_count,
            verified_count=0,
            severity_breakdown=sev_breakdown_v1,
        )
        message = build_report_job_message(payload_v1)
        published = await publisher.publish("report.jobs", message)
        if not published:
            raise RuntimeError("report.jobs publish returned False")

    logger.info("Stage 10 complete",
                scan_id=ctx.scan_id,
                findings_saved=saved_count,
                status=status,
                breakdown=breakdown)
    return breakdown
