"""
AttackBot KPI Metrics Module

This module provides Prometheus metrics for tracking Key Performance Indicators (KPIs)
across the AttackBot platform. All metrics follow the KPI framework defined in
docs/Core-Docs/KPIs/KPI_Framework.md

Categories:
- SH: System Health KPIs
- TP: Throughput KPIs
- PF: Performance KPIs
- QL: Quality KPIs
- RL: Reliability KPIs
- SC: Security KPIs
- RU: Resource Utilization KPIs
- OP: Operational KPIs
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
)

# =============================================================================
# SYSTEM HEALTH KPIs (SH)
# =============================================================================

# SH-001: System uptime in seconds
system_uptime_seconds = Gauge(
    'attackbot_sh_001_system_uptime_seconds',
    'Total system uptime in seconds (SH-001)',
)

# SH-002: Health status of services (1=healthy, 0=unhealthy, 0.5=degraded)
service_health_status = Gauge(
    'attackbot_sh_002_service_health_status',
    'Health status of individual services (SH-002)',
    ['service_name'],
)

# SH-003: Database connection errors
database_connection_errors = Counter(
    'attackbot_sh_003_database_connection_errors_total',
    'Total database connection failures (SH-003)',
    ['database', 'operation'],
)

# SH-004: RabbitMQ connection errors
rabbitmq_connection_errors = Counter(
    'attackbot_sh_004_rabbitmq_connection_errors_total',
    'Total RabbitMQ connection failures (SH-004)',
    ['operation'],
)

# SH-005: MinIO connection errors
minio_connection_errors = Counter(
    'attackbot_sh_005_minio_connection_errors_total',
    'Total MinIO storage connection failures (SH-005)',
    ['operation'],
)

# SH-006: Vault connection errors
vault_connection_errors = Counter(
    'attackbot_sh_006_vault_connection_errors_total',
    'Total Vault connection failures (SH-006)',
    ['operation'],
)


# =============================================================================
# THROUGHPUT KPIs (TP)
# =============================================================================

# TP-001: Total scans initiated
scans_initiated_total = Counter(
    'attackbot_tp_001_scans_initiated_total',
    'Total number of scans initiated (TP-001)',
    ['platform', 'program_handle'],
)

# TP-002: Total scans completed
scans_completed_total = Counter(
    'attackbot_tp_002_scans_completed_total',
    'Total number of scans completed (TP-002)',
    ['status', 'platform'],
)

# TP-003: Scans completed per hour (calculated, not a raw metric)
# Tracked via rate(scans_completed_total[1h])

# TP-004: Total findings discovered
findings_discovered_total = Counter(
    'attackbot_tp_004_findings_discovered_total',
    'Total number of findings discovered (TP-004)',
    ['severity', 'vulnerability_type', 'platform'],
)

# TP-005: Average findings per scan (calculated)
# Tracked via rate(findings_discovered_total) / rate(scans_completed_total)

# TP-006: Total reports generated
reports_generated_total = Counter(
    'attackbot_tp_006_reports_generated_total',
    'Total number of reports generated (TP-006)',
    ['format', 'status'],
)

# TP-007: Reports generated per hour (calculated)
# Tracked via rate(reports_generated_total[1h])

# TP-008: Platform programs synced
programs_synced_total = Counter(
    'attackbot_tp_008_programs_synced_total',
    'Total platform programs synced (TP-008)',
    ['platform', 'status'],
)


# =============================================================================
# PERFORMANCE KPIs (PF)
# =============================================================================

# PF-001: Scan duration histogram
scan_duration_seconds = Histogram(
    'attackbot_pf_001_scan_duration_seconds',
    'Scan completion time in seconds (PF-001)',
    ['platform', 'status'],
    buckets=[300, 600, 900, 1200, 1800, 2700, 3600, 5400, 7200],  # 5min to 2hrs
)

# PF-002: 95th percentile scan duration (use histogram with summary)
scan_duration_summary = Summary(
    'attackbot_pf_002_scan_duration_summary_seconds',
    'Scan completion time summary for percentile calculation (PF-002)',
    ['platform'],
)

# PF-003: Stage duration by pipeline stage
stage_duration_seconds = Histogram(
    'attackbot_pf_003_stage_duration_seconds',
    'Duration by pipeline stage in seconds (PF-003)',
    ['stage_name', 'status'],
    buckets=[10, 30, 60, 120, 300, 600, 1200, 1800],
)

# PF-004: Asset discovery stage duration
asset_discovery_duration = Histogram(
    'attackbot_pf_004_asset_discovery_duration_seconds',
    'Asset discovery stage duration in seconds (PF-004)',
    buckets=[30, 60, 120, 300, 600],
)

# PF-005: Fingerprinting stage duration
fingerprinting_duration = Histogram(
    'attackbot_pf_005_fingerprinting_duration_seconds',
    'Fingerprinting stage duration in seconds (PF-005)',
    buckets=[10, 30, 60, 120, 180],
)

# PF-006: Enumeration stage duration
enumeration_duration = Histogram(
    'attackbot_pf_006_enumeration_duration_seconds',
    'Enumeration stage duration in seconds (PF-006)',
    buckets=[30, 60, 120, 300, 600, 900],
)

# PF-007: Nuclei scan stage duration
nuclei_scan_duration = Histogram(
    'attackbot_pf_007_nuclei_scan_duration_seconds',
    'Nuclei vulnerability scan duration in seconds (PF-007)',
    buckets=[60, 300, 600, 900, 1200, 1800],
)

# PF-008: Report generation duration
report_generation_duration = Histogram(
    'attackbot_pf_008_report_generation_duration_seconds',
    'Report generation time in seconds (PF-008)',
    ['format'],
    buckets=[10, 30, 60, 120, 180, 300],
)

# PF-009: API response time
api_response_time_seconds = Histogram(
    'attackbot_pf_009_api_response_time_seconds',
    'API response time in seconds (PF-009)',
    ['service', 'endpoint', 'http_method'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)

# PF-010: 95th percentile API response time (use summary)
api_response_time_summary = Summary(
    'attackbot_pf_010_api_response_time_summary_seconds',
    'API response time summary for percentile calculation (PF-010)',
    ['service', 'endpoint'],
)


# =============================================================================
# QUALITY KPIs (QL)
# =============================================================================

# QL-001: Verified findings counter
verified_findings_total = Counter(
    'attackbot_ql_001_verified_findings_total',
    'Total number of verified findings (QL-001)',
    ['severity', 'platform'],
)

# QL-002: False positive findings counter
false_positive_findings_total = Counter(
    'attackbot_ql_002_false_positive_findings_total',
    'Total number of false positive findings (QL-002)',
    ['severity', 'reason'],
)

# QL-003: Severity distribution (use findings_discovered_total with severity label)
# Already covered by TP-004

# QL-004: Critical findings per scan
critical_findings_per_scan = Gauge(
    'attackbot_ql_004_critical_findings_per_scan',
    'Average critical findings per scan (QL-004)',
)

# QL-005: High severity findings per scan
high_findings_per_scan = Gauge(
    'attackbot_ql_005_high_findings_per_scan',
    'Average high severity findings per scan (QL-005)',
)

# QL-006: Clean scan rate (calculated)
# Tracked via: rate(scans_completed_total{status="completed"} and findings_discovered_total == 0)
clean_scans_total = Counter(
    'attackbot_ql_006_clean_scans_total',
    'Total clean scans (zero findings) (QL-006)',
    ['platform'],
)

# QL-007: Evidence quality score
evidence_quality_score = Histogram(
    'attackbot_ql_007_evidence_quality_score',
    'Evidence quality score per finding (QL-007)',
    buckets=[0, 20, 40, 60, 80, 100],
)

# QL-008: Reproduction pack generation success
reproduction_pack_success_total = Counter(
    'attackbot_ql_008_reproduction_pack_success_total',
    'Reproduction pack generation success count (QL-008)',
    ['format'],
)
reproduction_pack_failure_total = Counter(
    'attackbot_ql_008_reproduction_pack_failure_total',
    'Reproduction pack generation failure count (QL-008)',
    ['format', 'reason'],
)


# =============================================================================
# RELIABILITY KPIs (RL)
# =============================================================================

# RL-001: Scan success rate (calculated)
# Calculated as: (scans_completed_total{status="completed"} / scans_initiated_total) * 100
# Track components separately
scans_succeeded_total = Counter(
    'attackbot_rl_001_scans_succeeded_total',
    'Total successful scans (RL-001)',
)

# RL-002: Scan failure rate (calculated)
# Calculated as: (scans_completed_total{status="failed*"} / scans_initiated_total) * 100
scans_failed_total = Counter(
    'attackbot_rl_002_scans_failed_total',
    'Total failed scans (RL-002)',
    ['failure_reason'],
)

# RL-003: Partial scan rate (calculated)
# Calculated as: (scans_completed_total{status="partial"} / scans_initiated_total) * 100
scans_partial_total = Counter(
    'attackbot_rl_003_scans_partial_total',
    'Total partial scans (RL-003)',
    ['reason'],
)

# RL-004: Report generation success rate
report_generation_success_total = Counter(
    'attackbot_rl_004_report_generation_success_total',
    'Total successful report generations (RL-004)',
    ['format'],
)
report_generation_failure_total = Counter(
    'attackbot_rl_004_report_generation_failure_total',
    'Total failed report generations (RL-004)',
    ['format', 'reason'],
)

# RL-005: Queue message loss rate (should be 0)
queue_message_loss_total = Counter(
    'attackbot_rl_005_queue_message_loss_total',
    'Total queue messages lost (RL-005)',
    ['queue_name'],
)

# RL-006: Worker crash rate
worker_crash_total = Counter(
    'attackbot_rl_006_worker_crash_total',
    'Total worker crashes (RL-006)',
    ['service'],
)

# RL-007: Task retry rate
# Tracked via existing retry mechanisms in Celery
beaaa_task_retries_total = Counter(
    'attackbot_rl_007_task_retries_total',
    'Total task retries (RL-007)',
    ['queue_name', 'reason'],
)

# RL-008: DLQ message rate (already tracked in dlq_monitor.py)
# Reference: rabbitmq_dlq_depth from shared.dlq_monitor


# =============================================================================
# SECURITY KPIs (SC)
# =============================================================================

# SC-001: Total security findings (use findings_discovered_total with security filter)
# Covered by TP-004 with appropriate labels

# SC-002: Critical security findings
critical_security_findings_total = Counter(
    'attackbot_sc_002_critical_security_findings_total',
    'Total critical security findings (SC-002)',
    ['cve_id', 'platform'],
)

# SC-003: Zero-day detection rate (track findings without CVE)
zero_day_findings_total = Counter(
    'attackbot_sc_003_zero_day_findings_total',
    'Total zero-day findings (no CVE) (SC-003)',
    ['vulnerability_type'],
)

# SC-004: Exploit chain detection rate
exploit_chains_detected_total = Counter(
    'attackbot_sc_004_exploit_chains_detected_total',
    'Total exploit chains detected (SC-004)',
    ['chain_type', 'complexity'],
)

# SC-005: CVE coverage percentage (calculated)
cves_covered_total = Counter(
    'attackbot_sc_005_cves_covered_total',
    'Total unique CVEs covered (SC-005)',
)
cves_detected_total = Counter(
    'attackbot_sc_005_cves_detected_total',
    'Total CVE detections (SC-005)',
)

# SC-006: Vulnerability type coverage
vulnerability_type_coverage = Gauge(
    'attackbot_sc_006_vulnerability_type_coverage',
    'Number of unique vulnerability types detected (SC-006)',
)


# =============================================================================
# RESOURCE UTILIZATION KPIs (RU)
# =============================================================================

# RU-001: CPU usage percentage (tracked by Prometheus node_exporter or similar)
# External monitoring

# RU-002: Memory usage percentage (tracked by Prometheus node_exporter)
# External monitoring

# RU-003: Disk usage percentage
disk_usage_percentage = Gauge(
    'attackbot_ru_003_disk_usage_percentage',
    'Disk usage percentage (RU-003)',
    ['mount_point'],
)

# RU-004: Database size in GB
database_size_gb = Gauge(
    'attackbot_ru_004_database_size_gb',
    'Database size in GB (RU-004)',
)

# RU-005: MinIO storage usage in GB
minio_storage_usage_gb = Gauge(
    'attackbot_ru_005_minio_storage_usage_gb',
    'MinIO storage usage in GB (RU-005)',
)

# RU-006: Queue depth
queue_depth = Gauge(
    'attackbot_ru_006_queue_depth',
    'Current queue depth (RU-006)',
    ['queue_name'],
)

# RU-007: RabbitMQ memory usage (tracked by RabbitMQ exporter)
# External monitoring

# RU-008: PostgreSQL connection count
postgres_connections = Gauge(
    'attackbot_ru_008_postgres_connections',
    'Current PostgreSQL connection count (RU-008)',
)


# =============================================================================
# OPERATIONAL KPIs (OP)
# =============================================================================

# OP-001: Total programs monitored
programs_monitored = Gauge(
    'attackbot_op_001_programs_monitored',
    'Total programs being monitored (OP-001)',
    ['platform'],
)

# OP-002: Currently active scans
active_scans = Gauge(
    'attackbot_op_002_active_scans',
    'Currently active (running) scans (OP-002)',
)

# OP-003: Currently queued scans
queued_scans = Gauge(
    'attackbot_op_003_queued_scans',
    'Currently queued scans (OP-003)',
)

# OP-004: User activity (API requests, UI interactions)
user_activity_total = Counter(
    'attackbot_op_004_user_activity_total',
    'Total user interactions (OP-004)',
    ['action_type', 'user_id'],
)

# OP-005: Report downloads
report_downloads_total = Counter(
    'attackbot_op_005_report_downloads_total',
    'Total report downloads (OP-005)',
    ['format', 'status'],
)

# OP-006: API requests total
api_requests_total = Counter(
    'attackbot_op_006_api_requests_total',
    'Total API requests (OP-006)',
    ['service', 'endpoint', 'http_method', 'status_code'],
)

# OP-007: Overall error rate (calculated)
# Calculated as: (api_requests_total{status_code=~"^[45].."} / api_requests_total) * 100


# =============================================================================
# KPI HELPER FUNCTIONS
# =============================================================================

def record_scan_start(platform: str, program_handle: str) -> None:
    """Record a scan start event."""
    scans_initiated_total.labels(platform=platform, program_handle=program_handle).inc()
    active_scans.inc()


def record_scan_complete(
    status: str,
    platform: str,
    duration_seconds: float,
    finding_count: int = 0,
    severity_breakdown: dict = None,
) -> None:
    """Record a scan completion event."""
    active_scans.dec()
    scans_completed_total.labels(status=status, platform=platform).inc()
    scan_duration_seconds.labels(platform=platform, status=status).observe(duration_seconds)
    scan_duration_summary.labels(platform=platform).observe(duration_seconds)
    
    if status == 'completed':
        scans_succeeded_total.inc()
    elif status.startswith('failed'):
        scans_failed_total.labels(failure_reason=status).inc()
    elif status == 'partial':
        scans_partial_total.labels(reason='unknown').inc()
    
    # Record findings if provided
    if finding_count > 0:
        if severity_breakdown:
            for severity, count in severity_breakdown.items():
                findings_discovered_total.labels(
                    severity=severity,
                    vulnerability_type='unknown',
                    platform=platform
                ).inc(count)
        else:
            findings_discovered_total.labels(
                severity='unknown',
                vulnerability_type='unknown',
                platform=platform
            ).inc(finding_count)
    else:
        clean_scans_total.labels(platform=platform).inc()


def record_finding(
    severity: str,
    vulnerability_type: str,
    platform: str,
    is_verified: bool = False,
    has_evidence: bool = False,
    evidence_quality: int = None,
) -> None:
    """Record a finding discovery."""
    findings_discovered_total.labels(
        severity=severity,
        vulnerability_type=vulnerability_type,
        platform=platform
    ).inc()
    
    if is_verified:
        verified_findings_total.labels(
            severity=severity,
            platform=platform
        ).inc()
    
    if evidence_quality is not None:
        evidence_quality_score.labels(severity=severity).observe(evidence_quality)


def record_false_positive(
    severity: str,
    reason: str = 'unknown',
) -> None:
    """Record a false positive finding."""
    false_positive_findings_total.labels(
        severity=severity,
        reason=reason
    ).inc()


def record_stage_duration(
    stage_name: str,
    duration_seconds: float,
    status: str = 'completed',
) -> None:
    """Record a pipeline stage duration."""
    stage_duration_seconds.labels(stage_name=stage_name, status=status).observe(duration_seconds)


def record_report_generation(
    format: str,
    duration_seconds: float,
    success: bool = True,
    failure_reason: str = None,
) -> None:
    """Record a report generation event."""
    reports_generated_total.labels(format=format, status='completed' if success else 'failed').inc()
    report_generation_duration.labels(format=format).observe(duration_seconds)
    
    if success:
        report_generation_success_total.labels(format=format).inc()
    else:
        report_generation_failure_total.labels(
            format=format,
            reason=failure_reason or 'unknown'
        ).inc()


def record_api_request(
    service: str,
    endpoint: str,
    http_method: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """Record an API request."""
    api_requests_total.labels(
        service=service,
        endpoint=endpoint,
        http_method=http_method,
        status_code=str(status_code)
    ).inc()
    api_response_time_seconds.labels(
        service=service,
        endpoint=endpoint,
        http_method=http_method
    ).observe(duration_seconds)
    api_response_time_summary.labels(
        service=service,
        endpoint=endpoint
    ).observe(duration_seconds)


def record_exploit_chain(
    chain_type: str,
    complexity: str = 'unknown',
    steps: int = 0,
) -> None:
    """Record an exploit chain detection."""
    exploit_chains_detected_total.labels(
        chain_type=chain_type,
        complexity=complexity
    ).inc()
    stage_duration_seconds.labels(
        stage_name='exploit_chain_analysis',
        status='completed'
    ).observe(steps * 60)  # Estimate based on steps


def record_error(
    error_type: str,
    service: str,
    severity: str = 'warning',
) -> None:
    """Record a general error event."""
    api_requests_total.labels(
        service=service,
        endpoint='error',
        http_method='N/A',
        status_code='500'
    ).inc()


# =============================================================================
# KPI CALCULATION UTILITIES
# These are helper functions for calculating derived KPIs
# =============================================================================

class KpiCalculator:
    """Utility class for calculating derived KPIs from raw metrics."""
    
    @staticmethod
    def calculate_scan_success_rate(scans_succeeded: float, scans_total: float) -> float:
        """Calculate scan success rate percentage."""
        if scans_total == 0:
            return 0.0
        return (scans_succeeded / scans_total) * 100
    
    @staticmethod
    def calculate_verification_rate(verified: float, total_findings: float) -> float:
        """Calculate verification rate percentage."""
        if total_findings == 0:
            return 0.0
        return (verified / total_findings) * 100
    
    @staticmethod
    def calculate_false_positive_rate(false_positives: float, verified: float) -> float:
        """Calculate false positive rate percentage."""
        if verified == 0:
            return 0.0
        return (false_positives / verified) * 100
    
    @staticmethod
    def calculate_report_generation_success_rate(
        succeeded: float,
        total: float
    ) -> float:
        """Calculate report generation success rate percentage."""
        if total == 0:
            return 0.0
        return (succeeded / total) * 100
    
    @staticmethod
    def calculate_clean_scan_rate(clean_scans: float, total_scans: float) -> float:
        """Calculate clean scan rate percentage."""
        if total_scans == 0:
            return 0.0
        return (clean_scans / total_scans) * 100
    
    @staticmethod
    def calculate_findings_per_scan(findings: float, scans: float) -> float:
        """Calculate average findings per scan."""
        if scans == 0:
            return 0.0
        return findings / scans
    
    @staticmethod
    def calculate_cve_coverage(cves_covered: float, cves_detected: float) -> float:
        """Calculate CVE coverage percentage."""
        if cves_detected == 0:
            return 0.0
        return (cves_covered / cves_detected) * 100


# =============================================================================
# MODULE METADATA
# =============================================================================

KPI_CATEGORIES = {
    'SH': 'System Health',
    'TP': 'Throughput',
    'PF': 'Performance',
    'QL': 'Quality',
    'RL': 'Reliability',
    'SC': 'Security',
    'RU': 'Resource Utilization',
    'OP': 'Operational',
}

KPI_VERSION = '1.0.0'
KPI_DATE = '2026-03-29'
