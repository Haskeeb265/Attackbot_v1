from unittest.mock import patch
from uuid import uuid4

import pytest

try:
    from backend.services.reporter import worker
except ModuleNotFoundError:
    worker = None


pytestmark = pytest.mark.skipif(worker is None, reason="celery not installed")


def _valid_report_envelope() -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "scan.completed",
        "schema_version": "1.0",
        "timestamp": "2026-03-22T00:00:00Z",
        "trace_id": None,
        "source_service": "core-engine",
        "payload": {
            "scan_id": str(uuid4()),
            "program_id": str(uuid4()),
            "status": "completed",
            "partial_stages": [],
            "has_findings": True,
            "finding_count": 3,
            "verified_count": 0,
            "severity_breakdown": {
                "critical": 1,
                "high": 1,
                "medium": 1,
                "low": 0,
                "informational": 0,
            },
            "exploit_chains": [],
            "formats_requested": ["pdf", "docx"],
            "include_evidence_screenshots": True,
        },
    }


def test_handle_report_job_message_valid_envelope_logs_and_returns() -> None:
    envelope = _valid_report_envelope()
    with (
        patch.object(worker.log, "info") as info_mock,
        patch.object(worker.log, "warning") as warning_mock,
        patch.object(worker.log, "error") as error_mock,
    ):
        worker._handle_report_job_message(envelope)

    error_mock.assert_not_called()
    info_event_names = [call.args[0] for call in info_mock.call_args_list]
    assert "report_job_received" in info_event_names
    assert "report_job_formats_requested" in info_event_names
    warning_mock.assert_called_once()
    assert warning_mock.call_args.args[0] == "report_generation_not_yet_implemented"


def test_handle_report_job_message_malformed_body_logs_error() -> None:
    with (
        patch.object(worker.log, "error") as error_mock,
        patch.object(worker.log, "info") as info_mock,
        patch.object(worker.log, "warning") as warning_mock,
    ):
        worker._handle_report_job_message("not-json")

    error_mock.assert_called_once()
    assert error_mock.call_args.args[0] == "report_job_malformed_envelope"
    info_mock.assert_not_called()
    warning_mock.assert_not_called()


def test_raw_consumer_callback_always_acks() -> None:
    class _DummyMessage:
        def __init__(self) -> None:
            self.acked = False

        def ack(self) -> None:
            self.acked = True

    dummy_message = _DummyMessage()
    with patch.object(worker.log, "error"):
        worker._on_report_jobs_message("not-json", dummy_message)

    assert dummy_message.acked is True


def test_reporter_worker_task_logs_compat_invocation_source() -> None:
    envelope = _valid_report_envelope()
    with (
        patch.object(worker.log, "warning") as warning_mock,
        patch.object(worker.log, "info"),
        patch.object(worker.log, "error"),
    ):
        worker.reporter_worker_task.run(envelope)

    compat_calls = [
        call for call in warning_mock.call_args_list
        if call.args and call.args[0] == "report_job_received_via_celery_task_path"
    ]
    assert compat_calls
    assert compat_calls[0].kwargs.get("invocation_source") == "celery_compat"
