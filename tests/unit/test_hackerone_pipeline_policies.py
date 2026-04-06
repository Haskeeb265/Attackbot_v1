from tests.e2e import test_hackerone_full_pipeline_trace as pipeline_trace


def test_adaptive_scan_wait_seconds_for_small_scope() -> None:
    assert (
        pipeline_trace._adaptive_scan_wait_seconds(pipeline_trace.SCAN_WAIT_SCOPE_THRESHOLD)
        == pipeline_trace.SCAN_WAIT_SECONDS_SMALL
    )


def test_adaptive_scan_wait_seconds_for_large_scope() -> None:
    assert (
        pipeline_trace._adaptive_scan_wait_seconds(pipeline_trace.SCAN_WAIT_SCOPE_THRESHOLD + 1)
        == pipeline_trace.SCAN_WAIT_SECONDS_LARGE
    )


def test_scan_source_outcome_is_fresh_when_terminal_with_findings() -> None:
    outcome = pipeline_trace._scan_source_outcome({"status": "completed"}, 1, allow_findings_fallback=False)
    assert outcome == "fresh"


def test_scan_source_outcome_is_strict_fail_when_fallback_disabled() -> None:
    outcome = pipeline_trace._scan_source_outcome(None, 0, allow_findings_fallback=False)
    assert outcome == "strict_fail"


def test_scan_source_outcome_is_fallback_when_enabled() -> None:
    outcome = pipeline_trace._scan_source_outcome(None, 0, allow_findings_fallback=True)
    assert outcome == "fallback"


def test_result_label_exact_for_fallback_enabled_path() -> None:
    assert pipeline_trace._result_label(True) == "passed_with_fallback"


def test_download_proof_required_only_when_strict_and_host_port_set() -> None:
    assert pipeline_trace._is_download_proof_required(True, "9000") is True
    assert pipeline_trace._is_download_proof_required(True, "") is False
    assert pipeline_trace._is_download_proof_required(False, "9000") is False
