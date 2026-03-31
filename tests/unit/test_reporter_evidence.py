from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from backend.services.reporter.config import ReporterConfig
from backend.services.reporter.evidence import (
    _extract_bucket_and_key,
    cleanup_evidence_temp_files,
    fetch_all_evidence,
)
from backend.services.reporter.metrics import evidence_missing_total
from backend.services.reporter.models import EvidenceArtifact, ParsedFinding, ParsedScan, ProgramInfo


def _parsed_scan(include_evidence: bool) -> ParsedScan:
    finding = ParsedFinding(
        finding_id=uuid4(),
        title="Stored XSS",
        vulnerability_type="xss",
        severity="high",
        cvss_score=8.0,
        cvss_vector=None,
        affected_url="https://example.com/app",
        affected_parameter="q",
        description="desc",
        reproduction_steps=None,
        source="unit",
        is_verified=False,
        raw_output=None,
    )
    return ParsedScan(
        scan_id=uuid4(),
        status="completed",
        partial=False,
        finding_count=1,
        verified_count=0,
        severity_breakdown={"high": 1, "info": 0, "low": 0, "medium": 0, "critical": 0},
        include_evidence_screenshots=include_evidence,
        program=ProgramInfo(
            program_id=uuid4(),
            platform="hackerone",
            handle="demo",
            name="Demo",
            url=None,
            bounty_type=None,
            max_bounty=None,
            is_active=True,
        ),
        scope=[],
        findings=[finding],
    )


def _counter_value(counter) -> float:
    return counter._value.get()


@pytest.mark.asyncio
async def test_fetch_all_evidence_skips_when_flag_false() -> None:
    parsed = _parsed_scan(include_evidence=False)
    core_client = AsyncMock()
    storage = AsyncMock()
    settings = ReporterConfig()

    reasons = await fetch_all_evidence(parsed, core_client, storage, settings)

    assert reasons == []
    core_client.get_finding_evidence.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_all_evidence_marks_partial_reason_when_object_missing() -> None:
    parsed = _parsed_scan(include_evidence=True)

    core_client = AsyncMock()
    core_client.get_finding_evidence = AsyncMock(
        return_value=[
            {
                "artifact_type": "screenshot",
                "storage_path": "evidence/abc/screen.png",
                "description": "shot",
            }
        ]
    )

    class _Storage:
        def get_evidence_bucket(self) -> str:
            return "evidence"

        object_exists = AsyncMock(return_value=False)
        download_temp_object = AsyncMock()

    storage = _Storage()

    settings = ReporterConfig()
    metric_before = _counter_value(evidence_missing_total)
    reasons = await fetch_all_evidence(parsed, core_client, storage, settings)
    metric_after = _counter_value(evidence_missing_total)

    assert reasons == ["evidence_image_load_failed"]
    assert len(parsed.findings[0].evidence) == 1
    assert parsed.findings[0].evidence[0].exists is False
    storage.download_temp_object.assert_not_awaited()
    assert metric_after == metric_before + 1


@pytest.mark.asyncio
async def test_cleanup_evidence_temp_files_deletes_downloaded_file(tmp_path) -> None:
    parsed = _parsed_scan(include_evidence=True)

    evidence_path = tmp_path / "evidence.png"
    evidence_path.write_bytes(b"abc")

    parsed.findings[0].evidence.append(
        EvidenceArtifact(
            artifact_type="screenshot",
            storage_path="evidence/demo/evidence.png",
            description="shot",
            exists=True,
            local_tmp_path=str(evidence_path),
        )
    )

    cleanup_evidence_temp_files(parsed)

    assert evidence_path.exists() is False
    artifact = parsed.findings[0].evidence[0]
    assert artifact.local_tmp_path is None
    assert artifact.exists is False


@pytest.mark.asyncio
async def test_fetch_all_evidence_downloads_when_object_exists(tmp_path) -> None:
    parsed = _parsed_scan(include_evidence=True)

    core_client = AsyncMock()
    core_client.get_finding_evidence = AsyncMock(
        return_value=[
            {
                "artifact_type": "screenshot",
                "storage_path": "evidence/demo/screen.png",
                "description": "shot",
            }
        ]
    )

    downloaded = tmp_path / "downloaded.png"
    downloaded.write_bytes(b"img")

    class _Storage:
        def get_evidence_bucket(self) -> str:
            return "evidence"

        object_exists = AsyncMock(return_value=True)
        download_temp_object = AsyncMock(return_value=str(downloaded))

    storage = _Storage()

    settings = ReporterConfig(max_inline_evidence_images_per_finding=1)
    reasons = await fetch_all_evidence(parsed, core_client, storage, settings)

    assert reasons == []
    assert len(parsed.findings[0].evidence) == 1
    artifact = parsed.findings[0].evidence[0]
    assert artifact.exists is True
    assert artifact.local_tmp_path == str(downloaded)


def test_extract_bucket_and_key_with_prefixed_path() -> None:
    bucket, key = _extract_bucket_and_key("evidence/abc/screen.png", "evidence")
    assert bucket == "evidence"
    assert key == "abc/screen.png"


def test_extract_bucket_and_key_with_bare_key() -> None:
    bucket, key = _extract_bucket_and_key("abc/screen.png", "evidence")
    assert bucket == "evidence"
    assert key == "abc/screen.png"
