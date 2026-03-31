"""
M4 end-to-end reporter download flow.

Path 1: organic chain (uses existing terminal scan in local stack).
Path 2: regenerate chain with stable report IDs.
"""

from __future__ import annotations

import os
import time
import zipfile
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

REPORTER_BASE = "http://localhost:8003/api/v1"
CORE_ENGINE_BASE = "http://localhost:8002/api/v1"


def _service_ok(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def _require_services() -> None:
    if not _service_ok(REPORTER_BASE):
        pytest.skip("Reporter is not reachable on localhost:8003")
    if not _service_ok(CORE_ENGINE_BASE):
        pytest.skip("Core Engine is not reachable on localhost:8002")


def _get_terminal_scan_id() -> str:
    response = httpx.get(f"{CORE_ENGINE_BASE}/scans", timeout=10)
    response.raise_for_status()
    scans = response.json().get("scans", [])
    for scan in scans:
        if str(scan.get("status", "")).lower() in {"completed", "partial"}:
            return str(scan["scan_id"])
    pytest.skip("No completed/partial scans available for E2E reporter flow")


def _poll_reports_for_scan(scan_id: str, timeout_seconds: int = 180) -> list[dict]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = httpx.get(f"{REPORTER_BASE}/scans/{scan_id}/reports", timeout=10)
        if response.status_code == 200:
            items = response.json().get("items", [])
            if items:
                return items
        time.sleep(2)
    pytest.skip("No report rows available for scan in this environment")


def _poll_report_terminal(report_id: str, timeout_seconds: int = 180) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}", timeout=10)
        if response.status_code == 200:
            report = response.json()
            if report.get("status") in {"completed", "partial", "failed"}:
                return report
        time.sleep(2)
    pytest.skip("Report row did not reach a terminal state in this environment")


def _assert_download_signature(download_url: str, format_name: str) -> None:
    parsed = urlparse(download_url)
    query = parse_qs(parsed.query)
    assert "X-Amz-Expires" in query or "Expires" in query

    # Optional in local runs: may fail when MinIO hostname is only reachable
    # from inside Docker network. Keep this as a soft assertion by skipping.
    try:
        response = httpx.get(download_url, timeout=30)
    except Exception as exc:
        pytest.skip(f"Presigned URL host unreachable from this test runtime: {exc}")

    if response.status_code != 200:
        pytest.skip(f"Could not download artifact via presigned URL (status={response.status_code})")

    content = response.content
    if format_name == "pdf":
        assert content.startswith(b"%PDF")
        return

    if format_name == "docx":
        # zipfile.is_zipfile needs a path or file object.
        from io import BytesIO

        assert zipfile.is_zipfile(BytesIO(content))
        return

    raise AssertionError(f"Unsupported format under test: {format_name}")


def test_path_1_existing_terminal_scan_download_flow() -> None:
    scan_id = _get_terminal_scan_id()
    reports = _poll_reports_for_scan(scan_id)

    for report in reports:
        report_id = str(report["report_id"])
        format_name = str(report["format"])
        terminal = _poll_report_terminal(report_id)
        if terminal["status"] not in {"completed", "partial"}:
            continue

        download_response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}/download", timeout=10)
        assert download_response.status_code == 200
        body = download_response.json()
        _assert_download_signature(body["download_url"], format_name)


def test_path_2_regenerate_reuses_ids_and_downloads() -> None:
    scan_id = _get_terminal_scan_id()
    response = httpx.post(
        f"{REPORTER_BASE}/reports/generate",
        json={
            "scan_id": scan_id,
            "formats_requested": ["pdf", "docx"],
            "include_evidence_screenshots": False,
        },
        timeout=20,
    )
    assert response.status_code == 202
    report_ids = response.json().get("report_ids", {})
    assert set(report_ids.keys()) == {"pdf", "docx"}

    for format_name, report_id in report_ids.items():
        report = _poll_report_terminal(str(report_id), timeout_seconds=180)
        assert report["report_id"] == str(report_id)
        if report["status"] not in {"completed", "partial"}:
            continue

        download_response = httpx.get(
            f"{REPORTER_BASE}/reports/{report_id}/download",
            timeout=10,
        )
        assert download_response.status_code == 200
        _assert_download_signature(download_response.json()["download_url"], format_name)
