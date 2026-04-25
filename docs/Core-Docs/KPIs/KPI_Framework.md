# AttackBot KPI Framework

## Overview

This document defines the Key Performance Indicators (KPIs) for AttackBot, an automated bug bounty discovery and reporting platform. KPIs are organized into categories that reflect the system's health, performance, security effectiveness, and operational efficiency.

---

## KPI Categories

### 1. System Health KPIs (SH)
Monitor the overall health and availability of the AttackBot platform.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| SH-001 | `system_uptime_seconds` | Total system uptime | > 99.9% | Critical |
| SH-002 | `service_health_status` | Health status of all services (healthy/degraded/unhealthy) | All healthy | Critical |
| SH-003 | `database_connection_errors` | Database connection failures | < 0.1% | High |
| SH-004 | `rabbitmq_connection_errors` | RabbitMQ connection failures | < 0.1% | High |
| SH-005 | `minio_connection_errors` | MinIO storage connection failures | < 0.1% | High |
| SH-006 | `vault_connection_errors` | Vault connection failures | < 0.1% | High |

### 2. Throughput KPIs (TP)
Measure the volume and velocity of scan operations.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| TP-001 | `scans_initiated_total` | Total number of scans initiated | Track trend | High |
| TP-002 | `scans_completed_total` | Total number of scans completed | Track trend | High |
| TP-003 | `scans_per_hour` | Scans completed per hour | > 5 | Medium |
| TP-004 | `findings_discovered_total` | Total findings discovered | Track trend | High |
| TP-005 | `findings_per_scan` | Average findings per scan | > 0.5 | Medium |
| TP-006 | `reports_generated_total` | Total reports generated | Track trend | High |
| TP-007 | `reports_per_hour` | Reports generated per hour | > 5 | Medium |
| TP-008 | `programs_sync_per_hour` | Platform programs synced per hour | > 10 | Medium |

### 3. Performance KPIs (PF)
Track the speed and efficiency of operations.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| PF-001 | `scan_duration_seconds` | Average scan completion time | < 30 min | Critical |
| PF-002 | `scan_duration_p95_seconds` | 95th percentile scan duration | < 45 min | High |
| PF-003 | `stage_duration_seconds` | Duration by pipeline stage | Stage-specific | High |
| PF-004 | `asset_discovery_duration` | Asset discovery stage duration | < 5 min | High |
| PF-005 | `fingerprinting_duration` | Fingerprinting stage duration | < 2 min | High |
| PF-006 | `enumeration_duration` | Enumeration stage duration | < 10 min | High |
| PF-007 | `nuclei_scan_duration` | Nuclei vulnerability scan duration | < 15 min | High |
| PF-008 | `report_generation_duration` | Report generation time | < 2 min | High |
| PF-009 | `api_response_time_seconds` | Average API response time | < 500ms | High |
| PF-010 | `api_response_time_p95_seconds` | 95th percentile API response time | < 1s | Medium |

### 4. Quality KPIs (QL)
Assess the quality and accuracy of findings.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| QL-001 | `verification_rate` | Percentage of verified findings | > 70% | Critical |
| QL-002 | `false_positive_rate` | Rate of false positive findings | < 5% | Critical |
| QL-003 | `severity_distribution` | Distribution across severity levels | Monitor | High |
| QL-004 | `critical_findings_per_scan` | Critical findings per scan | > 0 | Medium |
| QL-005 | `high_findings_per_scan` | High severity findings per scan | > 0.2 | Medium |
| QL-006 | `clean_scan_rate` | Percentage of scans with zero findings | < 30% | Medium |
| QL-007 | `evidence_quality_score` | Average evidence quality per finding | > 80% | Medium |
| QL-008 | `reproduction_pack_success_rate` | Reproduction pack generation success rate | > 95% | Medium |

### 5. Reliability KPIs (RL)
Measure system stability and error rates.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| RL-001 | `scan_success_rate` | Percentage of successful scans | > 95% | Critical |
| RL-002 | `scan_failure_rate` | Percentage of failed scans | < 5% | Critical |
| RL-003 | `partial_scan_rate` | Percentage of partial scans | < 10% | High |
| RL-004 | `report_generation_success_rate` | Report generation success rate | > 98% | Critical |
| RL-005 | `queue_message_loss_rate` | Message loss rate in queues | 0% | Critical |
| RL-006 | `worker_crash_rate` | Worker crash rate per hour | < 0.1 | Critical |
| RL-007 | `retry_rate` | Task retry rate | < 2% | Medium |
| RL-008 | `dlq_message_rate` | DLQ message rate per hour | < 0.01 | High |

### 6. Security KPIs (SC)
Track security-related metrics.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| SC-001 | `security_findings_total` | Total security findings | Track trend | High |
| SC-002 | `critical_security_findings` | Critical security findings | > 0/month | High |
| SC-003 | `zero_day_detection_rate` | Zero-day detection rate | Track trend | Medium |
| SC-004 | `exploit_chain_detection_rate` | Exploit chain detection rate | Track trend | Medium |
| SC-005 | `cve_coverage_percentage` | CVE coverage percentage | > 80% | Medium |
| SC-006 | `vulnerability_type_coverage` | Coverage across vulnerability types | > 15 types | Medium |

### 7. Resource Utilization KPIs (RU)
Monitor resource consumption.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| RU-001 | `cpu_usage_percentage` | CPU usage across services | < 70% | Medium |
| RU-002 | `memory_usage_percentage` | Memory usage across services | < 70% | Medium |
| RU-003 | `disk_usage_percentage` | Disk usage percentage | < 80% | Medium |
| RU-004 | `database_size_gb` | Database size in GB | < 100 | Medium |
| RU-005 | `minio_storage_usage_gb` | MinIO storage usage | < 500 | Medium |
| RU-006 | `queue_depth` | Average queue depth | < 100 | Medium |
| RU-007 | `rabbitmq_memory_usage` | RabbitMQ memory usage | < 80% | Medium |
| RU-008 | `postgres_connections` | PostgreSQL connection count | < max_connections * 0.8 | Medium |

### 8. Operational KPIs (OP)
Track operational metrics and business value.

| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| OP-001 | `programs_monitored` | Total programs being monitored | Track growth | High |
| OP-002 | `active_scans` | Currently active scans | < max_capacity | Medium |
| OP-003 | `queued_scans` | Currently queued scans | < max_capacity | Medium |
| OP-004 | `user_activity` | User interactions with the system | Track trend | Low |
| OP-005 | `report_downloads_total` | Total report downloads | Track trend | Medium |
| OP-006 | `api_requests_total` | Total API requests | Track trend | Medium |
| OP-007 | `error_rate` | Overall error rate | < 1% | High |

---

## KPI Implementation Hierarchy

### Level 1: Core System KPIs (Must Have)
- SH-001, SH-002 (System Health)
- TP-001, TP-002, TP-004, TP-006 (Throughput)
- PF-001, PF-002 (Performance)
- QL-001, QL-002 (Quality)
- RL-001, RL-002, RL-003, RL-004 (Reliability)

### Level 2: Extended Monitoring (Should Have)
- All PF-* (Performance by stage)
- All QL-* (Quality metrics)
- All RL-* (Reliability metrics)
- All RU-* (Resource utilization)

### Level 3: Advanced Analytics (Nice to Have)
- SC-* (Security metrics)
- OP-* (Operational metrics)

---

## KPI Calculation Formulas

### Scan Success Rate
```
RL-001 = (TP-002 / TP-001) * 100
Target: > 95%
```

### Verification Rate
```
QL-001 = (Verified Findings / TP-004) * 100
Target: > 70%
```

### False Positive Rate
```
QL-002 = (False Positives / Verified Findings) * 100
Target: < 5%
```

### Mean Time To Detection (MTTD)
```
MTTD = Average time from program sync to first finding
Track trend, lower is better
```

### Mean Time To Report (MTTR)
```
MTTR = Average time from scan completion to report availability
Target: < 2 minutes
```

### System Availability
```
SH-001 = (Total Uptime / (Total Uptime + Downtime)) * 100
Target: > 99.9%
```

---

## Alert Thresholds

### Critical Alerts (Immediate Action Required)
- System Health: Any service unhealthy for > 5 minutes
- Scan Success Rate: < 90% for 1 hour
- Report Generation Success Rate: < 95% for 1 hour
- DLQ Messages: Any message stuck for > 30 minutes
- Database Connection Errors: > 1% for 5 minutes
- Scan Failure Rate: > 10% for 1 hour
- Worker Crash Rate: > 0.5 per hour

### Warning Alerts (Monitor and Investigate)
- Scan Duration P95: > 60 minutes
- Verification Rate: < 60% for 24 hours
- Clean Scan Rate: > 40% for 24 hours
- CPU Usage: > 80% for 15 minutes
- Memory Usage: > 80% for 15 minutes
- Retry Rate: > 5% for 1 hour
- False Positive Rate: > 3% for 24 hours

### Info Alerts (Track Trends)
- Scans per hour: Sudden drop (> 50%)
- Findings per scan: Sudden drop (> 50%)
- Report generation time: > 5 minutes
- Queue depth: > 50 for 5 minutes
- Disk usage: > 70% for 1 hour

---

## Dashboard Requirements

### Executive Dashboard
- System Health Overview (SH-001, SH-002)
- Throughput Summary (TP-001, TP-002, TP-004, TP-006)
- Quality Summary (QL-001, QL-002, QL-006)
- Reliability Summary (RL-001, RL-002, RL-004)
- Resource Utilization Summary (RU-001, RU-002, RU-005)

### Operational Dashboard
- All Level 1 and Level 2 KPIs
- Pipeline stage performance
- Queue depths and DLQ status
- Service-specific metrics
- Error rates and retry rates

### Security Dashboard
- Security findings by type and severity
- CVE coverage
- Exploit chain detection
- Vulnerability type distribution
- False positive tracking

### Performance Dashboard
- Scan duration percentiles
- Stage duration breakdown
- API response times
- Resource consumption per service
- Bottleneck identification

---

## Data Retention Policy

| Metric Type | Retention Period |
|-------------|------------------|
| High-frequency metrics (seconds) | 30 days |
| Medium-frequency metrics (minutes) | 90 days |
| Low-frequency metrics (hours/daily) | 365 days |
| Raw logs | 90 days |
| Aggregated reports | 2 years |

---

## Implementation Notes

1. All KPIs should be exposed via Prometheus metrics
2. Grafana dashboards will visualize KPIs with appropriate thresholds
3. Alerts will be configured based on KPI thresholds
4. KPI data should be queryable via API for external integrations
5. Regular KPI reviews should be conducted to adjust targets
6. KPIs are implemented in `backend/shared/kpi_metrics.py`
7. Grafana dashboards are in `grafana/dashboards/`

---

## Related Files

- `backend/shared/kpi_metrics.py` - Prometheus metrics implementation
- `grafana/dashboards/kpi_executive_dashboard.json` - Executive dashboard
- `grafana/dashboards/kpi_operational_dashboard.json` - Operational dashboard
- `grafana/alerts/kpi_alerts.yml` - KPI alert rules
- `docs/Core-Docs/KPIs/KPI_Integration_Guide.md` - Integration guide

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-29 | Initial KPI Framework |
