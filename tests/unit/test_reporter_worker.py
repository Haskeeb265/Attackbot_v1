from unittest.mock import patch
from uuid import uuid4

import pytest

try:
    from backend.services.reporter import worker
except ModuleNotFoundError:
    worker = None


pytestmark = pytest.mark.skipif(worker is None, reason="celery/kombu not installed")


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


def test_handle_report_job_message_valid_envelope_enqueues_task() -> None:
    envelope = _valid_report_envelope()
    with (
        patch.object(worker.log, "info") as info_mock,
        patch.object(worker.log, "error") as error_mock,
        patch.object(worker.reporter_worker_task, "apply_async") as apply_async_mock,
    ):
        worker._handle_report_job_message(envelope)

    error_mock.assert_not_called()
    apply_async_mock.assert_called_once()

    info_event_names = [call.args[0] for call in info_mock.call_args_list]
    assert "report_job_received" in info_event_names
    assert "report_job_formats_requested" in info_event_names
    assert "report_generation_task_enqueued" in info_event_names


def test_handle_report_job_message_malformed_body_logs_error() -> None:
    with (
        patch.object(worker.log, "error") as error_mock,
        patch.object(worker.log, "info") as info_mock,
    ):
        worker._handle_report_job_message("not-json")

    error_mock.assert_called_once()
    assert error_mock.call_args.args[0] == "report_job_malformed_envelope"
    info_mock.assert_not_called()


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


def test_reporter_worker_task_invokes_report_processing() -> None:
    envelope = _valid_report_envelope()
    with patch.object(worker, "process_report_envelope_sync") as process_mock:
        worker.reporter_worker_task.run(envelope)

    process_mock.assert_called_once_with(envelope)


def test_retry_countdown_clamps_to_final_backoff_entry() -> None:
    assert worker._retry_countdown(0, [60, 300, 600]) == 60
    assert worker._retry_countdown(2, [60, 300, 600]) == 600
    assert worker._retry_countdown(8, [60, 300, 600]) == 600


def test_handle_task_exception_retries_before_exhaustion() -> None:
    class _RetrySignal(Exception):
        pass

    class _DummyTask:
        request = type("_Req", (), {"retries": 0})()

        @staticmethod
        def retry(*, exc, countdown):
            raise _RetrySignal(f"countdown={countdown}")

    with pytest.raises(_RetrySignal):
        worker._handle_task_exception(_DummyTask(), _valid_report_envelope(), RuntimeError("boom"))


def test_handle_task_exception_exhausted_publishes_to_dlq() -> None:
    class _DummyTask:
        request = type("_Req", (), {"retries": worker.settings.report_task_max_retries})()

        @staticmethod
        def retry(*, exc, countdown):
            raise AssertionError("retry should not be called when retries are exhausted")

    with (
        patch.object(worker, "_publish_to_report_jobs_dlq_sync", return_value=True) as dlq_mock,
        patch.object(worker.log, "error") as log_error_mock,
        pytest.raises(RuntimeError, match="boom"),
    ):
        worker._handle_task_exception(_DummyTask(), _valid_report_envelope(), RuntimeError("boom"))

    dlq_mock.assert_called_once()
    assert any(call.args[0] == "report_generation_retries_exhausted" for call in log_error_mock.call_args_list)
