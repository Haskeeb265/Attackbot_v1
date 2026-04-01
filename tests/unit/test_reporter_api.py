import json
from unittest.mock import AsyncMock

import pytest

try:
    from backend.services.reporter import main as reporter_main
except ModuleNotFoundError:
    reporter_main = None


pytestmark = pytest.mark.skipif(reporter_main is None, reason="kombu/celery dependencies not installed")


class _SessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return None


def _counter_value(counter, **labels: str) -> float:
    return counter.labels(**labels)._value.get()


def _histogram_count(histogram) -> float:
    for metric in histogram.collect():
        for sample in metric.samples:
            if sample.name.endswith("_count"):
                return float(sample.value)
    return 0.0


@pytest.mark.asyncio
async def test_generate_reports_returns_202_and_report_ids(monkeypatch):
    class _Repo:
        def __init__(self, session):
            pass

        async def create_or_reset_report(self, scan_id: str, program_id: str, format_name: str) -> str:
            return f"{format_name}-id"

    class _Publisher:
        async def publish(self, queue_name, message):
            return True

    session = AsyncMock()
    monkeypatch.setattr(reporter_main, "get_session", lambda: _SessionContext(session))
    monkeypatch.setattr(reporter_main, "ReportRepository", _Repo)
    monkeypatch.setattr(reporter_main, "_get_queue_publisher", lambda: _Publisher())
    monkeypatch.setattr(
        reporter_main,
        "_fetch_scan",
        AsyncMock(
            return_value={
                "scan_id": "scan-1",
                "program_id": "program-1",
                "status": "completed",
                "finding_count": 2,
                "severity_breakdown": {"high": 1, "medium": 1, "info": 0},
            }
        ),
    )

    request = reporter_main.GenerateReportsRequest(
        scan_id="scan-1",
        formats_requested=["pdf", "docx"],
        include_evidence_screenshots=True,
    )
    response = await reporter_main.generate_reports(request)
    body = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 202
    assert body["enqueued"] is True
    assert body["report_ids"] == {"pdf": "pdf-id", "docx": "docx-id"}


@pytest.mark.asyncio
async def test_generate_reports_returns_409_for_non_terminal_scan(monkeypatch):
    monkeypatch.setattr(
        reporter_main,
        "_fetch_scan",
        AsyncMock(return_value={"scan_id": "scan-1", "program_id": "program-1", "status": "running"}),
    )

    request = reporter_main.GenerateReportsRequest(scan_id="scan-1")
    with pytest.raises(reporter_main.HTTPException) as exc_info:
        await reporter_main.generate_reports(request)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_download_report_status_gate_and_success(monkeypatch):
    class _Repo:
        def __init__(self, session):
            pass

        async def get_report(self, report_id: str):
            return {
                "report_id": report_id,
                "status": "completed",
                "storage_path": f"reports/{report_id}/report.pdf",
            }

    class _Storage:
        async def get_presigned_download_url(self, storage_path: str, expiry_seconds: int) -> str:
            return f"https://signed.test/{storage_path}?Expires={expiry_seconds}"

    session = AsyncMock()
    monkeypatch.setattr(reporter_main, "get_session", lambda: _SessionContext(session))
    monkeypatch.setattr(reporter_main, "ReportRepository", _Repo)
    monkeypatch.setattr(reporter_main, "_get_storage", lambda: _Storage())

    success_before = _counter_value(reporter_main.download_requests_total, status="success")
    presign_before = _histogram_count(reporter_main.presign_duration_seconds)
    body = await reporter_main.download_report("report-1")
    success_after = _counter_value(reporter_main.download_requests_total, status="success")
    presign_after = _histogram_count(reporter_main.presign_duration_seconds)

    assert body["status"] == "completed"
    assert body["download_url"].startswith("https://signed.test/")
    assert success_after == success_before + 1
    assert presign_after == presign_before + 1


@pytest.mark.asyncio
async def test_download_report_returns_409_for_generating(monkeypatch):
    class _Repo:
        def __init__(self, session):
            pass

        async def get_report(self, report_id: str):
            return {
                "report_id": report_id,
                "status": "generating",
                "storage_path": None,
            }

    session = AsyncMock()
    monkeypatch.setattr(reporter_main, "get_session", lambda: _SessionContext(session))
    monkeypatch.setattr(reporter_main, "ReportRepository", _Repo)

    before = _counter_value(reporter_main.download_requests_total, status="not_ready")
    with pytest.raises(reporter_main.HTTPException) as exc_info:
        await reporter_main.download_report("report-1")
    after = _counter_value(reporter_main.download_requests_total, status="not_ready")

    assert exc_info.value.status_code == 409
    assert after == before + 1


@pytest.mark.asyncio
async def test_download_report_returns_404_and_increments_not_found_metric(monkeypatch):
    class _Repo:
        def __init__(self, session):
            pass

        async def get_report(self, report_id: str):
            return None

    session = AsyncMock()
    monkeypatch.setattr(reporter_main, "get_session", lambda: _SessionContext(session))
    monkeypatch.setattr(reporter_main, "ReportRepository", _Repo)

    before = _counter_value(reporter_main.download_requests_total, status="not_found")
    with pytest.raises(reporter_main.HTTPException) as exc_info:
        await reporter_main.download_report("missing-report")
    after = _counter_value(reporter_main.download_requests_total, status="not_found")

    assert exc_info.value.status_code == 404
    assert after == before + 1


@pytest.mark.asyncio
async def test_health_marks_attack_graph_degraded(monkeypatch):
    monkeypatch.setattr(reporter_main, "check_db_health", AsyncMock(return_value=True))
    monkeypatch.setattr(reporter_main, "check_rabbitmq_health", AsyncMock(return_value=True))
    monkeypatch.setattr(reporter_main, "check_storage_health", lambda: True)
    monkeypatch.setattr(reporter_main, "_check_upstream_cached", AsyncMock(return_value=True))
    monkeypatch.setattr(reporter_main, "scheduler", type("_Scheduler", (), {"running": True})())

    response = await reporter_main.health()

    assert response.components["attack_graph_engine"].status.value == "degraded"
    assert response.status.value == "degraded"
