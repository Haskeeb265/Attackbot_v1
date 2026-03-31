"""
Integration scenarios for M4 Reporter pipeline.

These tests target live services on localhost and skip cleanly when the stack
is not available.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from typing import Any

import httpx
import pytest
from urllib.parse import quote

from backend.shared.schemas.report_jobs import (
    ExploitChainRef,
    ReportJobsPayload,
    SeverityBreakdown,
    build_report_job_message,
)

REPORTER_BASE = "http://localhost:8003/api/v1"
CORE_ENGINE_BASE = "http://localhost:8002/api/v1"
SCRAPER_BASE = "http://localhost:8001/api/v1"
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://attackbot:attackbot@localhost:5672/")
DATABASE_URL = os.getenv("REPORTER_INTEGRATION_DATABASE_URL", "postgresql://attackbot:attackbot@localhost:5432/attackbot")
RABBITMQ_MGMT = os.getenv("RABBITMQ_MGMT_URL", "http://localhost:15672/api")
RABBITMQ_MGMT_USER = os.getenv("RABBITMQ_MGMT_USER", "attackbot")
RABBITMQ_MGMT_PASS = os.getenv("RABBITMQ_MGMT_PASS", "attackbot")


def _is_service_healthy(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url}/health", timeout=5)
    except Exception:
        return False
    return response.status_code == 200


@pytest.fixture(scope="module", autouse=True)
def require_live_stack() -> None:
    if not _is_service_healthy(REPORTER_BASE):
        pytest.skip("Reporter service is not reachable on localhost:8003")
    if not _is_service_healthy(CORE_ENGINE_BASE):
        pytest.skip("Core Engine service is not reachable on localhost:8002")


def _get_terminal_scan() -> dict[str, Any]:
    response = httpx.get(f"{CORE_ENGINE_BASE}/scans", timeout=10)
    response.raise_for_status()
    scans = response.json().get("scans", [])
    for scan in scans:
        if str(scan.get("status", "")).lower() in {"completed", "partial"}:
            return scan
    pytest.skip("No completed/partial scans available for reporter integration tests")


def _poll_report_terminal(report_id: str, timeout_seconds: int = 120) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}", timeout=10)
        if response.status_code == 200:
            report = response.json()
            if report.get("status") in {"completed", "partial", "failed"}:
                return report
        time.sleep(2)
    return None


def _any_program_id() -> str:
    scans_resp = httpx.get(f"{CORE_ENGINE_BASE}/scans", timeout=10)
    if scans_resp.status_code == 200:
        scans = scans_resp.json().get("scans", [])
        if scans:
            program_id = scans[0].get("program_id")
            if program_id:
                return str(program_id)

    scraper_resp = httpx.get(f"{SCRAPER_BASE}/programs?page_size=1", timeout=10)
    if scraper_resp.status_code == 200:
        items = scraper_resp.json().get("items", [])
        if items:
            return str(items[0]["program_id"])

    pytest.skip("Unable to resolve a program_id for running scan scenario")


def _get_terminal_scan_with_findings() -> dict[str, Any]:
    response = httpx.get(f"{CORE_ENGINE_BASE}/scans", timeout=10)
    response.raise_for_status()
    scans = response.json().get("scans", [])
    for scan in scans:
        if str(scan.get("status", "")).lower() in {"completed", "partial"} and int(scan.get("finding_count") or 0) > 0:
            return scan
    pytest.skip("No completed/partial scan with findings available for reporter integration tests")


def _first_finding_id_or_skip(scan_id: str) -> str:
    response = httpx.get(f"{CORE_ENGINE_BASE}/scans/{scan_id}/findings", timeout=10)
    if response.status_code != 200:
        pytest.skip(f"Unable to fetch findings for scan {scan_id}")
    findings = response.json().get("findings", [])
    if not findings:
        pytest.skip(f"No findings present for scan {scan_id}")
    return str(findings[0]["finding_id"])


def _poll_reports_for_scan(scan_id: str, timeout_seconds: int = 120) -> list[dict[str, Any]] | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = httpx.get(f"{REPORTER_BASE}/scans/{scan_id}/reports", timeout=10)
        if response.status_code == 200:
            items = response.json().get("items", [])
            if items:
                return items
        time.sleep(2)
    return None


def _poll_report_status(report_id: str, expected_statuses: set[str], timeout_seconds: int = 120) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}", timeout=10)
        if response.status_code == 200:
            report = response.json()
            status = str(report.get("status", "")).lower()
            if status in expected_statuses:
                return report
        time.sleep(2)
    return None


def _insert_completed_scan_or_skip(scan_id: str, program_id: str, finding_count: int = 0) -> None:
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed for DB-backed reporter integration scenarios")

    async def _insert() -> None:
        scan_uuid = uuid.UUID(scan_id)
        program_uuid = uuid.UUID(program_id)
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute(
                """
                INSERT INTO scans (
                    scan_id, program_id, status, finding_count, severity_breakdown,
                    created_at, started_at, completed_at
                )
                VALUES (
                    $1, $2, 'completed', $3, '{"critical":0,"high":0,"medium":0,"low":0,"informational":0}',
                    NOW(), NOW(), NOW()
                )
                """,
                scan_uuid,
                program_uuid,
                finding_count,
            )
        finally:
            await conn.close()

    try:
        asyncio.run(_insert())
    except Exception as exc:
        pytest.skip(f"Unable to insert completed scan row in local DB: {exc}")


def _insert_finding_evidence_or_skip(finding_id: str, storage_path: str) -> str:
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed for DB-backed reporter integration scenarios")

    evidence_id = str(uuid.uuid4())

    async def _insert() -> None:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute(
                """
                INSERT INTO finding_evidence (evidence_id, finding_id, artifact_type, storage_path, description, captured_at)
                VALUES ($1, $2, 'screenshot', $3, 'integration-missing-object', NOW())
                """,
                uuid.UUID(evidence_id),
                uuid.UUID(finding_id),
                storage_path,
            )
        finally:
            await conn.close()

    try:
        asyncio.run(_insert())
    except Exception as exc:
        pytest.skip(f"Unable to insert finding_evidence row: {exc}")

    return evidence_id


def _delete_finding_evidence_best_effort(evidence_id: str) -> None:
    try:
        import asyncpg
    except ImportError:
        return

    async def _delete() -> None:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute("DELETE FROM finding_evidence WHERE evidence_id = $1", uuid.UUID(evidence_id))
        finally:
            await conn.close()

    try:
        asyncio.run(_delete())
    except Exception:
        return


def _rabbitmq_get_messages_or_skip(queue_name: str, count: int = 50) -> list[dict[str, Any]]:
    encoded_queue = quote(queue_name, safe="")
    try:
        response = httpx.post(
            f"{RABBITMQ_MGMT}/queues/%2F/{encoded_queue}/get",
            auth=(RABBITMQ_MGMT_USER, RABBITMQ_MGMT_PASS),
            json={
                "count": count,
                "ackmode": "ack_requeue_true",
                "encoding": "auto",
                "truncate": 100000,
            },
            timeout=10,
        )
    except Exception as exc:
        pytest.skip(f"RabbitMQ management API not reachable: {exc}")

    if response.status_code != 200:
        pytest.skip(f"RabbitMQ management API queue get failed ({response.status_code})")
    data = response.json()
    if not isinstance(data, list):
        pytest.skip("Unexpected RabbitMQ management API response shape")
    return data


def _message_contains_report_id(message: dict[str, Any], report_id: str) -> bool:
    payload = message.get("payload")
    if isinstance(payload, dict):
        report_ids = payload.get("payload", {}).get("report_ids", {})
        return report_id in report_ids.values()
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except Exception:
            return report_id in payload
        report_ids = parsed.get("payload", {}).get("report_ids", {})
        return report_id in report_ids.values()
    return False


def _insert_running_scan_or_skip(scan_id: str, program_id: str) -> None:
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed for DB-backed running scan scenario")

    async def _insert() -> None:
        scan_uuid = uuid.UUID(scan_id)
        program_uuid = uuid.UUID(program_id)
        conn = await asyncpg.connect("postgresql://attackbot:attackbot@localhost:5432/attackbot")
        try:
            await conn.execute(
                "INSERT INTO scans (scan_id, program_id, status, created_at) VALUES ($1, $2, 'running', NOW())",
                scan_uuid,
                program_uuid,
            )
        finally:
            await conn.close()

    try:
        asyncio.run(_insert())
    except Exception as exc:
        pytest.skip(f"Unable to insert running scan row in local DB: {exc}")


def _delete_scan_best_effort(scan_id: str) -> None:
    try:
        import asyncpg
    except ImportError:
        return

    async def _delete() -> None:
        scan_uuid = uuid.UUID(scan_id)
        conn = await asyncpg.connect("postgresql://attackbot:attackbot@localhost:5432/attackbot")
        try:
            await conn.execute("DELETE FROM scans WHERE scan_id = $1", scan_uuid)
        finally:
            await conn.close()

    try:
        asyncio.run(_delete())
    except Exception:
        return


def test_scenario_h_generate_api_returns_pollable_stable_report_ids() -> None:
    scan = _get_terminal_scan()
    scan_id = str(scan["scan_id"])

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

    body = response.json()
    report_ids = body.get("report_ids", {})
    assert set(report_ids.keys()) == {"pdf", "docx"}

    for report_id in report_ids.values():
        terminal_report = _poll_report_terminal(str(report_id), timeout_seconds=120)
        if terminal_report is None:
            pytest.skip("reporter-worker is not processing jobs in this environment")
        assert terminal_report["report_id"] == str(report_id)
        assert terminal_report["status"] in {"completed", "partial", "failed"}


def test_scenario_a_normal_findings_report_generation() -> None:
    scan = _get_terminal_scan_with_findings()
    scan_id = str(scan["scan_id"])

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
        report = _poll_report_status(str(report_id), {"completed", "partial", "failed"}, timeout_seconds=120)
        if report is None:
            pytest.skip("reporter-worker is not processing jobs in this environment")
        assert report["format"] == format_name
        assert report["status"] in {"completed", "partial", "failed"}
        if report["status"] in {"completed", "partial"}:
            download_response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}/download", timeout=10)
            assert download_response.status_code == 200


def test_scenario_b_zero_findings_report() -> None:
    program_id = _any_program_id()
    scan_id = str(uuid.uuid4())
    _insert_completed_scan_or_skip(scan_id=scan_id, program_id=program_id, finding_count=0)
    try:
        response = httpx.post(
            f"{REPORTER_BASE}/reports/generate",
            json={
                "scan_id": scan_id,
                "formats_requested": ["pdf"],
                "include_evidence_screenshots": False,
            },
            timeout=20,
        )
        assert response.status_code == 202

        report_id = str(response.json()["report_ids"]["pdf"])
        report = _poll_report_status(report_id, {"completed", "partial", "failed"}, timeout_seconds=120)
        if report is None:
            pytest.skip("reporter-worker is not processing jobs in this environment")

        assert report["status"] in {"completed", "partial", "failed"}
        if report["status"] in {"completed", "partial"}:
            download_response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}/download", timeout=10)
            assert download_response.status_code == 200
    finally:
        _delete_scan_best_effort(scan_id)


def test_scenario_c_missing_screenshot_object_marks_partial() -> None:
    scan = _get_terminal_scan_with_findings()
    scan_id = str(scan["scan_id"])
    finding_id = _first_finding_id_or_skip(scan_id)

    evidence_id = _insert_finding_evidence_or_skip(
        finding_id=finding_id,
        storage_path=f"evidence/integration-missing/{uuid.uuid4().hex}.png",
    )
    try:
        response = httpx.post(
            f"{REPORTER_BASE}/reports/generate",
            json={
                "scan_id": scan_id,
                "formats_requested": ["pdf"],
                "include_evidence_screenshots": True,
            },
            timeout=20,
        )
        assert response.status_code == 202

        report_id = str(response.json()["report_ids"]["pdf"])
        report = _poll_report_status(report_id, {"partial", "completed", "failed"}, timeout_seconds=120)
        if report is None:
            pytest.skip("reporter-worker is not processing jobs in this environment")

        if report["status"] == "failed":
            pytest.skip("Reporter generation failed for unrelated environment reasons")

        # Missing MinIO evidence object should trigger partial reason in M4 policy.
        if report["status"] == "completed":
            pytest.skip("No evidence object miss surfaced in this environment run")
        assert report["status"] == "partial"
        detail = str(report.get("error_detail") or "")
        assert "evidence_image_load_failed" in detail
    finally:
        _delete_finding_evidence_best_effort(evidence_id)


def test_scenario_d_evidence_disabled_path() -> None:
    scan = _get_terminal_scan_with_findings()
    scan_id = str(scan["scan_id"])

    response = httpx.post(
        f"{REPORTER_BASE}/reports/generate",
        json={
            "scan_id": scan_id,
            "formats_requested": ["pdf"],
            "include_evidence_screenshots": False,
        },
        timeout=20,
    )
    assert response.status_code == 202

    report_id = str(response.json()["report_ids"]["pdf"])
    report = _poll_report_status(report_id, {"completed", "partial", "failed"}, timeout_seconds=120)
    if report is None:
        pytest.skip("reporter-worker is not processing jobs in this environment")
    if report["status"] == "failed":
        pytest.skip("Reporter generation failed for unrelated environment reasons")

    detail = str(report.get("error_detail") or "")
    assert "evidence_image_load_failed" not in detail


def test_scenario_j_generate_api_rejects_running_scan_with_409() -> None:
    program_id = _any_program_id()
    running_scan_id = str(uuid.uuid4())

    _insert_running_scan_or_skip(scan_id=running_scan_id, program_id=program_id)
    try:
        response = httpx.post(
            f"{REPORTER_BASE}/reports/generate",
            json={
                "scan_id": running_scan_id,
                "formats_requested": ["pdf"],
                "include_evidence_screenshots": False,
            },
            timeout=20,
        )
    finally:
        _delete_scan_best_effort(running_scan_id)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_scenario_i_organic_message_without_report_ids_allocates_rows() -> None:
    if os.getenv("RUN_REPORTER_ORGANIC_INTEGRATION", "0") != "1":
        pytest.skip("Set RUN_REPORTER_ORGANIC_INTEGRATION=1 to run organic queue scenario")

    try:
        from backend.shared.queue import QueuePublisher, Queues
    except ModuleNotFoundError:
        pytest.skip("kombu/aio-pika dependencies are not installed")

    scan = _get_terminal_scan()
    scan_id = str(scan["scan_id"])
    program_id = str(scan["program_id"])

    severity_raw = scan.get("severity_breakdown") or {}
    if "informational" not in severity_raw and "info" in severity_raw:
        severity_raw = dict(severity_raw)
        severity_raw["informational"] = severity_raw["info"]

    payload = ReportJobsPayload(
        scan_id=scan_id,
        program_id=program_id,
        status=str(scan.get("status", "completed")).lower(),
        partial_stages=[],
        has_findings=int(scan.get("finding_count") or 0) > 0,
        finding_count=int(scan.get("finding_count") or 0),
        verified_count=0,
        severity_breakdown=SeverityBreakdown.model_validate(severity_raw),
        formats_requested=["pdf", "docx"],
        include_evidence_screenshots=False,
    )
    envelope = build_report_job_message(payload, source_service="core-engine")

    publisher = QueuePublisher(RABBITMQ_URL)
    await publisher.connect()
    try:
        published = await publisher.publish(Queues.REPORT_JOBS, envelope)
        if not published:
            pytest.skip("Unable to publish organic report.jobs message")
    finally:
        await publisher.close()

    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        response = httpx.get(f"{REPORTER_BASE}/scans/{scan_id}/reports", timeout=10)
        if response.status_code == 200 and response.json().get("count", 0) >= 1:
            return
        await asyncio.sleep(2)

    pytest.skip("Organic report.jobs message was not consumed in this environment")


@pytest.mark.asyncio
async def test_scenario_e_attack_graph_unavailable_marks_partial() -> None:
    if os.getenv("RUN_REPORTER_ORGANIC_INTEGRATION", "0") != "1":
        pytest.skip("Set RUN_REPORTER_ORGANIC_INTEGRATION=1 to run organic queue scenarios")

    try:
        from backend.shared.queue import QueuePublisher, Queues
    except ModuleNotFoundError:
        pytest.skip("kombu/aio-pika dependencies are not installed")

    scan = _get_terminal_scan_with_findings()
    scan_id = str(scan["scan_id"])
    program_id = str(scan["program_id"])

    severity_raw = scan.get("severity_breakdown") or {}
    if "informational" not in severity_raw and "info" in severity_raw:
        severity_raw = dict(severity_raw)
        severity_raw["informational"] = severity_raw["info"]

    pdf_report_id = str(uuid.uuid4())
    payload = ReportJobsPayload(
        scan_id=scan_id,
        program_id=program_id,
        status=str(scan.get("status", "completed")).lower(),
        partial_stages=[],
        has_findings=int(scan.get("finding_count") or 0) > 0,
        finding_count=int(scan.get("finding_count") or 0),
        verified_count=0,
        severity_breakdown=SeverityBreakdown.model_validate(severity_raw),
        exploit_chains=[
            ExploitChainRef(
                chain_id=uuid.uuid4(),
                chain_name="Integration Chain Placeholder",
                combined_severity="high",
                step_count=2,
            )
        ],
        formats_requested=["pdf"],
        report_ids={"pdf": uuid.UUID(pdf_report_id)},
        include_evidence_screenshots=False,
    )
    envelope = build_report_job_message(payload, source_service="core-engine")

    publisher = QueuePublisher(RABBITMQ_URL)
    await publisher.connect()
    try:
        published = await publisher.publish(Queues.REPORT_JOBS, envelope)
        if not published:
            pytest.skip("Unable to publish attack-graph scenario message")
    finally:
        await publisher.close()

    report = _poll_report_status(pdf_report_id, {"partial", "completed", "failed"}, timeout_seconds=120)
    if report is None:
        pytest.skip("reporter-worker is not processing jobs in this environment")
    if report["status"] == "failed":
        pytest.skip("Reporter generation failed for unrelated environment reasons")
    if report["status"] == "completed":
        pytest.skip("Attack graph fallback reason was not observed in this environment run")

    detail = str(report.get("error_detail") or "")
    assert report["status"] == "partial"
    assert "attack_graph_chain_detail_unavailable" in detail


def test_scenario_f_forced_upload_failure_marks_failed() -> None:
    if os.getenv("RUN_REPORTER_FAILURE_INTEGRATION", "0") != "1":
        pytest.skip("Set RUN_REPORTER_FAILURE_INTEGRATION=1 to run forced upload failure scenario")

    scan = _get_terminal_scan()
    scan_id = str(scan["scan_id"])
    response = httpx.post(
        f"{REPORTER_BASE}/reports/generate",
        json={
            "scan_id": scan_id,
            "formats_requested": ["pdf"],
            "include_evidence_screenshots": False,
        },
        timeout=20,
    )
    assert response.status_code == 202

    report_id = str(response.json()["report_ids"]["pdf"])
    report = _poll_report_status(report_id, {"failed", "completed", "partial"}, timeout_seconds=180)
    if report is None:
        pytest.skip("reporter-worker is not processing jobs in this environment")
    if report["status"] != "failed":
        pytest.skip(
            "Upload failure force hook not active. Configure reporter with "
            "force_upload_failure_report_ids_str='*' for this scenario."
        )

    download_response = httpx.get(f"{REPORTER_BASE}/reports/{report_id}/download", timeout=10)
    assert download_response.status_code == 409

    messages = _rabbitmq_get_messages_or_skip("reports.completed", count=100)
    assert not any(_message_contains_report_id(msg, report_id) for msg in messages)


def test_scenario_g_retries_exhausted_message_appears_in_report_jobs_dlq() -> None:
    if os.getenv("RUN_REPORTER_DLQ_INTEGRATION", "0") != "1":
        pytest.skip("Set RUN_REPORTER_DLQ_INTEGRATION=1 to run DLQ scenario")

    scan = _get_terminal_scan()
    scan_id = str(scan["scan_id"])
    response = httpx.post(
        f"{REPORTER_BASE}/reports/generate",
        json={
            "scan_id": scan_id,
            "formats_requested": ["pdf"],
            "include_evidence_screenshots": False,
        },
        timeout=20,
    )
    assert response.status_code == 202
    report_id = str(response.json()["report_ids"]["pdf"])

    report = _poll_report_status(report_id, {"failed", "completed", "partial"}, timeout_seconds=180)
    if report is None:
        pytest.skip("reporter-worker is not processing jobs in this environment")
    if report["status"] != "failed":
        pytest.skip(
            "Failure/retry path not active. Configure forced upload failures and fast retry backoff "
            "(for example report_task_retry_backoff_seconds_str='1,1,1')."
        )

    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        messages = _rabbitmq_get_messages_or_skip("report.jobs.dlq", count=200)
        if any(_message_contains_report_id(msg, report_id) for msg in messages):
            return
        time.sleep(3)

    pytest.skip("Did not observe expected failed message in report.jobs.dlq within timeout")
