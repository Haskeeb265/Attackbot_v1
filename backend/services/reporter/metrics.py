from __future__ import annotations

from prometheus_client import Counter, Histogram

generation_total = Counter(
    "attackbot_reporter_generation_total",
    "Track generation outcomes by format and final status.",
    labelnames=("format", "status"),
)
generation_duration_seconds = Histogram(
    "attackbot_reporter_generation_duration_seconds",
    "Wall-clock generation duration by output format.",
    labelnames=("format",),
)
generation_failures_total = Counter(
    "attackbot_reporter_generation_failures_total",
    "Count failed generation reasons by format.",
    labelnames=("format", "reason"),
)
download_requests_total = Counter(
    "attackbot_reporter_download_requests_total",
    "Count download endpoint requests by outcome status.",
    labelnames=("status",),
)
presign_duration_seconds = Histogram(
    "attackbot_reporter_presign_duration_seconds",
    "Duration to generate presigned URLs.",
)
evidence_missing_total = Counter(
    "attackbot_reporter_evidence_missing_total",
    "Referenced evidence objects that were not available.",
)
zero_findings_total = Counter(
    "attackbot_reporter_zero_findings_total",
    "Scans that generated zero-findings reports.",
)
partial_generation_total = Counter(
    "attackbot_reporter_partial_generation_total",
    "Partial generation outcomes grouped by reason.",
    labelnames=("reason",),
)


def record_generation(format_name: str, status: str, duration_seconds: float) -> None:
    generation_total.labels(format=format_name, status=status).inc()
    generation_duration_seconds.labels(format=format_name).observe(max(duration_seconds, 0.0))


def record_generation_failure(format_name: str, reason: str) -> None:
    generation_failures_total.labels(format=format_name, reason=reason).inc()


def record_partial_reason(reason: str) -> None:
    partial_generation_total.labels(reason=reason).inc()
