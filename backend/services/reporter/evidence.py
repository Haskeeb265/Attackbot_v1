from __future__ import annotations

import asyncio
import os
from typing import Any

from backend.services.reporter.clients.core_engine import CoreEngineClient
from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.metrics import evidence_missing_total
from backend.services.reporter.models import EvidenceArtifact, ParsedScan
from backend.services.reporter.storage import ReporterStorage
from backend.shared.logging import get_logger

log = get_logger(__name__)


def _extract_bucket_and_key(storage_path: str, default_bucket: str) -> tuple[str, str]:
    normalized = storage_path.lstrip("/")
    if not normalized:
        return default_bucket, ""
    prefix = f"{default_bucket}/"
    if normalized.startswith(prefix):
        return default_bucket, normalized[len(prefix) :]
    return default_bucket, normalized


async def fetch_all_evidence(
    parsed_scan: ParsedScan,
    core_client: CoreEngineClient,
    storage: ReporterStorage,
    settings: ReporterConfig,
) -> list[str]:
    """
    Enrich parsed findings with local evidence paths.
    Returns partial-reason tags.
    """
    if not parsed_scan.include_evidence_screenshots:
        return []

    semaphore = asyncio.Semaphore(settings.evidence_download_concurrency)
    partial_reasons: list[str] = []

    async def _fetch_for_finding(finding: Any) -> list[str]:
        finding_reasons: list[str] = []
        items = await core_client.get_finding_evidence(str(parsed_scan.scan_id), str(finding.finding_id))
        max_items = settings.max_inline_evidence_images_per_finding

        for item in items[:max_items]:
            storage_path = item.get("storage_path")
            artifact = EvidenceArtifact(
                artifact_type=str(item.get("artifact_type") or "unknown"),
                storage_path=storage_path,
                description=item.get("description"),
                exists=False,
                local_tmp_path=None,
            )

            if not storage_path:
                finding_reasons.append("evidence_image_load_failed")
                evidence_missing_total.inc()
                finding.evidence.append(artifact)
                continue

            bucket, key = _extract_bucket_and_key(storage_path, storage.get_evidence_bucket())
            if not key:
                finding_reasons.append("evidence_image_load_failed")
                evidence_missing_total.inc()
                finding.evidence.append(artifact)
                continue

            try:
                async with semaphore:
                    exists = await storage.object_exists(bucket, key)
                    if not exists:
                        finding_reasons.append("evidence_image_load_failed")
                        evidence_missing_total.inc()
                        finding.evidence.append(artifact)
                        continue

                    tmp_path = await storage.download_temp_object(
                        bucket=bucket,
                        key=key,
                        tmp_dir=settings.temp_output_dir,
                    )
            except Exception as exc:
                finding_reasons.append("evidence_image_load_failed")
                evidence_missing_total.inc()
                log.warning(
                    "reporter_evidence_download_failed",
                    scan_id=str(parsed_scan.scan_id),
                    finding_id=str(finding.finding_id),
                    storage_path=storage_path,
                    error=str(exc),
                )
                finding.evidence.append(artifact)
                continue

            artifact.exists = True
            artifact.local_tmp_path = tmp_path
            finding.evidence.append(artifact)

        return finding_reasons

    tasks = [_fetch_for_finding(finding) for finding in parsed_scan.findings]
    results = await asyncio.gather(*tasks)
    for finding_reasons in results:
        partial_reasons.extend(finding_reasons)

    # Deduplicate while preserving order for deterministic status detail.
    deduped: list[str] = []
    for reason in partial_reasons:
        if reason not in deduped:
            deduped.append(reason)
    return deduped


def cleanup_evidence_temp_files(parsed_scan: ParsedScan) -> None:
    for finding in parsed_scan.findings:
        for artifact in finding.evidence:
            local_path = artifact.local_tmp_path
            if not local_path:
                continue
            try:
                os.remove(local_path)
            except FileNotFoundError:
                pass
            except Exception:
                log.warning("reporter_evidence_temp_cleanup_failed", path=local_path)
            finally:
                artifact.local_tmp_path = None
                artifact.exists = False
