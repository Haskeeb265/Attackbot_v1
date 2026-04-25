import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.future import select
from backend.shared.models.scans import Scan


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.services.core_engine.models import (
    DiscoveredAsset, DiscoveredEndpoint, DiscoveredJsAsset, FindingCandidate
)
from backend.services.core_engine.dedup import compute_dedup_hash
from backend.services.core_engine.cvss import severity_to_cvss
from backend.shared.logging import get_logger

logger = get_logger("core_engine.repository")


class ScanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_scan(
        self,
        scan_id: UUID,
        program_id: UUID,
        config: dict,
        status: str = "running",
        priority: int = 1
    ) -> Scan:
        """Create a new scan with initial state."""  
        scan = Scan(
            scan_id=scan_id,
            program_id=program_id,
            status=status,
            priority=priority,
            feature_flags=config,
            created_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc)
        )
        self.session.add(scan)
        await self.session.commit()
        await self.session.refresh(scan)
        return scan


    # ── Scan lifecycle ──────────────────────────────────────────────────

    async def create_or_resume_scan(
        self, program_id: str, feature_flags: dict, priority: int = 1
    ) -> str:
        """
        Returns scan_id. Creates a new scan row or resumes an existing
        'running' scan for this program (in case of restart after crash).
        """
        # Check for an existing running scan for this program
        row = await self.session.execute(
            text("""
                SELECT scan_id FROM scans
                WHERE program_id = :program_id AND status = 'running'
                ORDER BY created_at DESC LIMIT 1
            """),
            {"program_id": program_id},
        )
        existing = row.fetchone()
        if existing:
            logger.info("Resuming existing scan", scan_id=str(existing[0]))
            return str(existing[0])

        # Check for a recent failed_internal scan eligible for retry
        row = await self.session.execute(
            text("""
                SELECT scan_id, retry_count FROM scans
                WHERE program_id = :program_id
                  AND status = 'failed_internal'
                  AND retry_count < 2
                ORDER BY completed_at DESC NULLS LAST, created_at DESC
                LIMIT 1
            """),
            {"program_id": program_id},
        )
        failed = row.fetchone()
        if failed and len(failed) >= 2:
            scan_id, retry_count = failed
            await self.session.execute(
                text("""
                    UPDATE scans
                    SET status = 'running',
                        started_at = NOW(),
                        error_detail = NULL,
                        partial_detail = NULL
                    WHERE scan_id = :scan_id
                """),
                {"scan_id": str(scan_id)},
            )
            await self.session.commit()
            logger.info("Retrying failed_internal scan",
                        scan_id=str(scan_id), retry_count=retry_count)
            return str(scan_id)

        scan_id = str(uuid.uuid4())
        await self.session.execute(
            text("""
                INSERT INTO scans
                  (scan_id, program_id, status, priority, feature_flags,
                   retry_count, started_at, created_at)
                VALUES
                  (:scan_id, :program_id, 'running', :priority, :feature_flags,
                   0, NOW(), NOW())
            """),
            {
                "scan_id": scan_id,
                "program_id": program_id,
                "priority": priority,
                "feature_flags": json.dumps(feature_flags),  # JSONB — must be valid JSON
            },
        )
        await self.session.commit()
        logger.info("Scan created", scan_id=scan_id, program_id=program_id)
        return scan_id

    async def mark_scan_complete(
        self,
        scan_id: str,
        status: str,
        finding_count: int,
        severity_breakdown: dict,
        partial_detail: Optional[dict] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        await self.session.execute(
            text("""
                UPDATE scans
                SET status = :status,
                    finding_count = :finding_count,
                    severity_breakdown = :severity_breakdown,
                    partial_detail = :partial_detail,
                    error_detail = :error_detail,
                    completed_at = NOW()
                WHERE scan_id = :scan_id
            """),
            {
                "scan_id": scan_id,
                "status": status,
                "finding_count": finding_count,
                "severity_breakdown": json.dumps(severity_breakdown),        # JSONB
                "partial_detail": json.dumps(partial_detail) if partial_detail else None,  # JSONB
                "error_detail": error_detail,                                # plain text — do NOT json.dumps
            },
        )
        await self.session.commit()

    async def record_stage(
        self,
        scan_id: str,
        stage_number: float,
        stage_name: str,
        status: str,
        started_at: datetime,
        output_summary: Optional[dict] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        await self.session.execute(
            text("""
                INSERT INTO scan_stages
                  (stage_id, scan_id, stage_number, stage_name, status,
                   started_at, completed_at, output_summary, error_detail)
                VALUES
                  (:stage_id, :scan_id, :stage_number, :stage_name, :status,
                   :started_at, NOW(), :output_summary, :error_detail)
                ON CONFLICT DO NOTHING
            """),
            {
                "stage_id": str(uuid.uuid4()),
                "scan_id": scan_id,
                "stage_number": stage_number,
                "stage_name": stage_name,
                "status": status,
                "started_at": started_at,
                "output_summary": json.dumps(output_summary) if output_summary else None,  # JSONB
                "error_detail": error_detail,                                               # plain text
            },
        )
        await self.session.commit()

    # ── Asset persistence ───────────────────────────────────────────────

    async def save_assets(
        self, scan_id: str, assets: list[DiscoveredAsset]
    ) -> list[DiscoveredAsset]:
        """Persists assets and stamps each with its asset_id."""
        for asset in assets:
            asset_id = str(uuid.uuid4())
            await self.session.execute(
                text("""
                    INSERT INTO assets
                      (asset_id, scan_id, asset_type, value, is_in_scope,
                       technology_stack, waf_detected, http_status, discovered_at)
                    VALUES
                      (:asset_id, :scan_id, :asset_type, :value, true,
                       :technology_stack, :waf_detected, :http_status, NOW())
                    ON CONFLICT DO NOTHING
                """),
                {
                    "asset_id": asset_id,
                    "scan_id": scan_id,
                    "asset_type": asset.asset_type,
                    "value": asset.value,
                    "technology_stack": json.dumps(asset.technology_stack) if asset.technology_stack else None,  # JSONB
                    "waf_detected": asset.waf_detected,
                    "http_status": asset.http_status,
                },
            )
            asset.asset_id = uuid.UUID(asset_id)
        await self.session.commit()
        return assets

    async def save_endpoints(
        self, scan_id: str, endpoints: list[DiscoveredEndpoint]
    ) -> None:
        for ep in endpoints:
            await self.session.execute(
                text("""
                    INSERT INTO endpoints
                      (endpoint_id, asset_id, scan_id, method, path, full_url,
                       content_type, response_code, parameters, headers,
                       requires_auth, discovered_at)
                    VALUES
                      (:endpoint_id, :asset_id, :scan_id, :method, :path, :full_url,
                       :content_type, :response_code, :parameters, :headers,
                       :requires_auth, NOW())
                    ON CONFLICT DO NOTHING
                """),
                {
                    "endpoint_id": str(uuid.uuid4()),
                    "asset_id": str(ep.asset_id),
                    "scan_id": scan_id,
                    "method": ep.method,
                    "path": ep.path,
                    "full_url": ep.full_url,
                    "content_type": ep.content_type,
                    "response_code": ep.response_code,
                    "parameters": json.dumps(ep.parameters) if ep.parameters else None,  # JSONB
                    "headers": json.dumps(ep.headers) if ep.headers else None,            # JSONB
                    "requires_auth": ep.requires_auth,
                },
            )
        await self.session.commit()

    async def save_js_asset(
        self, scan_id: str, js_asset: DiscoveredJsAsset
    ) -> DiscoveredJsAsset:
        js_asset_id = str(uuid.uuid4())
        await self.session.execute(
            text("""
                INSERT INTO js_assets
                  (js_asset_id, scan_id, url, content_hash, storage_path,
                   size_bytes, analyzed, discovered_at)
                VALUES
                  (:js_asset_id, :scan_id, :url, :content_hash, :storage_path,
                   :size_bytes, false, NOW())
                ON CONFLICT (content_hash) DO NOTHING
            """),
            {
                "js_asset_id": js_asset_id,
                "scan_id": scan_id,
                "url": js_asset.url,
                "content_hash": js_asset.content_hash,
                "storage_path": js_asset.storage_path,
                "size_bytes": js_asset.size_bytes,
            },
        )
        await self.session.commit()
        js_asset.js_asset_id = uuid.UUID(js_asset_id)
        return js_asset

    # ── Finding persistence ─────────────────────────────────────────────

    async def save_findings(
        self,
        scan_id: str,
        program_id: str,
        candidates: list[FindingCandidate],
    ) -> int:
        """
        Deduplicates by hash + scan_id before insert. Returns count of new findings saved.
        ON CONFLICT on (deduplication_hash, scan_id) is a no-op — do not count it.
        """
        saved = 0
        for candidate in candidates:
            dedup_hash = compute_dedup_hash(candidate)
            cvss_score = candidate.cvss_score or severity_to_cvss(candidate.severity)
            try:
                result = await self.session.execute(
                    text("""
                        INSERT INTO findings
                          (finding_id, scan_id, program_id, title, vulnerability_type,
                           severity, cvss_score, cvss_vector, affected_url,
                           affected_parameter, description, reproduction_steps,
                           is_verified, is_false_positive, deduplication_hash,
                           source, raw_output, created_at)
                        VALUES
                          (:finding_id, :scan_id, :program_id, :title, :vulnerability_type,
                           :severity, :cvss_score, :cvss_vector, :affected_url,
                           :affected_parameter, :description, :reproduction_steps,
                           false, false, :dedup_hash,
                           :source, :raw_output, NOW())
                        ON CONFLICT (deduplication_hash, scan_id) DO NOTHING
                    """),
                    {
                        "finding_id": str(uuid.uuid4()),
                        "scan_id": scan_id,
                        "program_id": program_id,
                        "title": candidate.title,
                        "vulnerability_type": candidate.vulnerability_type,
                        "severity": candidate.severity,
                        "cvss_score": cvss_score,
                        "cvss_vector": candidate.cvss_vector,
                        "affected_url": candidate.affected_url,
                        "affected_parameter": candidate.affected_parameter,
                        "description": candidate.description,
                        "reproduction_steps": candidate.reproduction_steps,
                        "dedup_hash": dedup_hash,
                        "source": candidate.source,
                        "raw_output": json.dumps(candidate.raw_output) if candidate.raw_output else None,  # JSONB
                    },
                )
                if result.rowcount > 0:
                    saved += 1
            except Exception as e:
                logger.warning("Finding insert failed", error=str(e),
                               vuln_type=candidate.vulnerability_type,
                               url=candidate.affected_url)
        await self.session.commit()
        return saved
