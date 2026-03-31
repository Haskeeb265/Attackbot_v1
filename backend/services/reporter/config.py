from backend.shared.config import BaseServiceConfig


class ReporterConfig(BaseServiceConfig):
    service_name: str = "reporter"
    port: int = 8003

    core_engine_api_url: str = "http://core-engine:8002"
    scraper_api_url: str = "http://scraper:8001"
    attack_graph_api_url: str = "http://attack-graph-engine:8006"

    upstream_timeout_seconds: int = 30
    upstream_connect_timeout_seconds: int = 5

    # Comma-separated string; consumed via get_default_formats().
    default_formats_str: str = "pdf,docx"

    reports_bucket: str = "reports"
    evidence_bucket: str = "evidence"
    report_presign_expiry_seconds: int = 900

    report_watchdog_interval_seconds: int = 300
    report_watchdog_stale_minutes: int = 30

    upstream_health_cache_ttl_seconds: int = 30

    max_inline_evidence_images_per_finding: int = 2
    evidence_download_concurrency: int = 10
    include_raw_http_appendix: bool = True
    temp_output_dir: str = "/tmp/attackbot-reports"

    report_task_max_retries: int = 3

    # Comma-separated string; consumed via get_retry_backoff().
    report_task_retry_backoff_seconds_str: str = "60,300,600"
    # Comma-separated list of report IDs that should fail before upload.
    # Use "*" to force-fail every report artifact upload path.
    force_upload_failure_report_ids_str: str = ""

    def get_default_formats(self) -> list[str]:
        return [f.strip() for f in self.default_formats_str.split(",") if f.strip()]

    def get_retry_backoff(self) -> list[int]:
        return [int(x.strip()) for x in self.report_task_retry_backoff_seconds_str.split(",")]

    def get_force_upload_failure_report_ids(self) -> set[str]:
        return {
            token.strip()
            for token in self.force_upload_failure_report_ids_str.split(",")
            if token.strip()
        }
