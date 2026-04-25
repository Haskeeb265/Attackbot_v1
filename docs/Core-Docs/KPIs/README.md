# AttackBot KPI System - README

## Overview

This directory contains the complete KPI (Key Performance Indicator) system for AttackBot, an automated bug bounty discovery and reporting platform. The KPI system provides comprehensive monitoring, alerting, and analytics capabilities across all AttackBot services.

## Structure

```
KPIs/
├── KPI_Framework.md           # KPI definitions, categories, targets, and thresholds
├── KPI_Integration_Guide.md   # Implementation and integration guide
└── README.md                  # This file
```

## Files Created

### 1. KPI Framework Definition
- **Location:** `docs/Core-Docs/KPIs/KPI_Framework.md`
- **Purpose:** Defines all KPI categories, metrics, targets, and alert thresholds
- **Categories:**
  - **SH (System Health):** 6 KPIs for monitoring platform health
  - **TP (Throughput):** 8 KPIs for tracking volume and velocity
  - **PF (Performance):** 10 KPIs for measuring speed and efficiency
  - **QL (Quality):** 8 KPIs for assessing finding accuracy
  - **RL (Reliability):** 8 KPIs for measuring stability
  - **SC (Security):** 6 KPIs for tracking security metrics
  - **RU (Resource Utilization):** 8 KPIs for resource consumption
  - **OP (Operational):** 7 KPIs for operational metrics

### 2. Prometheus Metrics Implementation
- **Location:** `backend/shared/kpi_metrics.py`
- **Purpose:** Python module with all Prometheus metrics and helper functions
- **Features:**
  - 40+ Prometheus Counter, Gauge, Histogram, and Summary metrics
  - Helper functions for common operations (scan start/complete, findings, etc.)
  - KpiCalculator utility class for derived metrics
  - Comprehensive documentation and type hints

### 3. Grafana Dashboard Configurations
- **Location:** `grafana/dashboards/`
- **Files:**
  - `kpi_executive_dashboard.json` - High-level executive overview
- **Features:**
  - Real-time KPI visualization
  - Threshold-based color coding
  - All Level 1 KPIs displayed
  - Responsive layout

### 4. Alert Rules
- **Location:** `grafana/alerts/kpi_alerts.yml`
- **Purpose:** Grafana-compatible alert rules for KPI thresholds
- **Features:**
  - Critical, Warning, and Info alert levels
  - 20+ alert rules across all KPI categories
  - Actionable annotations with impact and remediation steps

### 5. REST API Endpoints
- **Location:** `backend/services/api_gateway/kpi_routes.py`
- **Purpose:** HTTP endpoints for programmatic KPI access
- **Endpoints:**
  - `GET /api/v1/kpi/` - All KPIs organized by category
  - `GET /api/v1/kpi/{kpi_id}` - Specific KPI by ID
  - `GET /api/v1/kpi/category/{category}` - All KPIs in a category
  - `GET /api/v1/kpi/calculated/scan_success_rate` - Calculated success rate
  - `GET /api/v1/kpi/calculated/verification_rate` - Calculated verification rate
  - `GET /api/v1/kpi/calculated/report_generation_success_rate` - Calculated report success rate
  - `GET /api/v1/kpi/prometheus/metrics` - Raw Prometheus metrics
  - `GET /api/v1/kpi/health` - KPI service health check

### 6. Integration Guide
- **Location:** `docs/Core-Docs/KPIs/KPI_Integration_Guide.md`
- **Purpose:** Complete guide for integrating KPIs into services
- **Contents:**
  - Quick start guide
  - Service-specific integration examples
  - PromQL query examples
  - Custom KPI creation guide
  - Testing recommendations
  - Troubleshooting
  - Best practices

## Implementation Summary

### KPI Categories

| Category | KPIs | Priority | Status |
|----------|------|----------|--------|
| System Health (SH) | 6 | Critical/High | Implemented |
| Throughput (TP) | 8 | High/Medium | Implemented |
| Performance (PF) | 10 | Critical/High/Medium | Implemented |
| Quality (QL) | 8 | Critical/High/Medium | Implemented |
| Reliability (RL) | 8 | Critical/High/Medium | Implemented |
| Security (SC) | 6 | High/Medium | Implemented |
| Resource Utilization (RU) | 8 | Medium | Implemented |
| Operational (OP) | 7 | High/Medium/Low | Implemented |

### Key Metrics

#### Level 1 (Must Have)
- SH-001: System Uptime
- SH-002: Service Health Status
- TP-001: Scans Initiated
- TP-002: Scans Completed
- TP-004: Findings Discovered
- TP-006: Reports Generated
- PF-001: Average Scan Duration
- PF-002: Scan Duration P95
- QL-001: Verification Rate
- QL-002: False Positive Rate
- RL-001: Scan Success Rate
- RL-002: Scan Failure Rate
- RL-003: Partial Scan Rate
- RL-004: Report Generation Success Rate

#### Level 2 (Should Have)
- All remaining PF (Performance) metrics
- All remaining QL (Quality) metrics
- All remaining RL (Reliability) metrics
- All RU (Resource Utilization) metrics

#### Level 3 (Nice to Have)
- All SC (Security) metrics
- All OP (Operational) metrics

## Setup Instructions

### 1. Prometheus Configuration

Add the KPI endpoint to Prometheus scraping:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'attackbot-kpi'
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: '/api/v1/kpi/prometheus/metrics'
    static_configs:
      - targets: ['api-gateway:8000']
```

### 2. Import Grafana Dashboards

1. In Grafana, go to Dashboards > Import
2. Upload `grafana/dashboards/kpi_executive_dashboard.json`
3. Configure Prometheus as the data source
4. Save the dashboard

### 3. Import Alert Rules

1. In Grafana, go to Alerting > Alert rules
2. Click "Import" and upload `grafana/alerts/kpi_alerts.yml`
3. Configure Contact Points for notifications
4. Enable the alert rules

### 4. Integrate KPI Tracking

In each service, import and use the KPI metrics:

```python
from backend.shared.kpi_metrics import (
    record_scan_start,
    record_scan_complete,
    record_finding,
    record_stage_duration,
)

# Record a scan start
record_scan_start(platform="hackerone", program_handle="example")

# Record a scan complete
record_scan_complete(
    status="completed",
    platform="hackerone",
    duration_seconds=180.5,
    finding_count=5
)
```

### 5. Integrate API Endpoints

In the API Gateway, include the KPI routes:

```python
# In backend/services/api_gateway/main.py
from backend.services.api_gateway.kpi_routes import router as kpi_router

app.include_router(kpi_router)
```

## Usage Examples

### Query KPIs via API

```bash
# Get all KPIs
curl http://localhost:8000/api/v1/kpi/

# Get specific KPI
curl http://localhost:8000/api/v1/kpi/RL-001

# Get KPIs by category
curl http://localhost:8000/api/v1/kpi/category/Reliability

# Get calculated metrics
curl http://localhost:8000/api/v1/kpi/calculated/scan_success_rate
```

### Query KPIs via PromQL

```promql
# Scan success rate
(sum(rate(attackbot_rl_001_scans_succeeded_total[1h])) / sum(rate(attackbot_tp_001_scans_initiated_total[1h]))) * 100

# Average scan duration
avg(attackbot_pf_001_scan_duration_seconds_sum) / avg(attackbot_pf_001_scan_duration_seconds_count)

# Verification rate
(sum(rate(attackbot_ql_001_verified_findings_total[1d])) / sum(rate(attackbot_tp_004_findings_discovered_total[1d]))) * 100
```

### python usage

```python
# Record KPI events in services
from backend.shared.kpi_metrics import (
    scans_initiated_total,
    record_scan_start,
    record_finding,
)

# Increment a counter directly
scans_initiated_total.labels(platform="hackerone", program_handle="test").inc()

# Use helper functions
record_scan_start(platform="hackerone", program_handle="test")

record_finding(
    severity="critical",
    vulnerability_type="sqli",
    platform="hackerone",
    is_verified=True
)

# Calculate derived metrics
from backend.shared.kpi_metrics import KpiCalculator

success_rate = KpiCalculator.calculate_scan_success_rate(succeeded=950, total=1000)
# Returns: 95.0
```

## Alerting

### Alert Severity Levels

| Severity | Response Time | Example Alerts |
|----------|---------------|----------------|
| Critical | Immediate | Service unhealthy, High failure rate |
| Warning | Within hours | Low verification rate, High CPU usage |
| Info | Within 24h | Trend changes, Resource warnings |

### Alert Categories

- **System Health:** Service status, connection errors
- **Reliability:** Scan failures, report generation issues
- **Performance:** Slow scans, high latency
- **Quality:** Low verification, high false positives
- **Resource:** High CPU/memory, disk space
- **Security:** Detection gaps, CVE coverage

## Data Retention

| Metric Type | Retention | Purpose |
|-------------|-----------|---------|
| High-frequency (seconds) | 30 days | Detailed analysis |
| Medium-frequency (minutes) | 90 days | Trend analysis |
| Low-frequency (hours/daily) | 365 days | Historical analysis |

Configure in Prometheus:

```yaml
storage:
  tsdb:
    retention:
      time: 90d
      size: "500GB"
```

## Performance Optimization

### Metric Cardinality

**AVOID** high-cardinality labels:
- User IDs
- Request IDs
- IP addresses
- Timestamps as labels

**USE** low-cardinality labels:
- Service names (scraper, core-engine, etc.)
- Platform names (hackerone, bugcrowd, etc.)
- Severity levels (critical, high, medium, low, info)
- Status codes (200, 404, 500, etc.)

### Scrape Interval Recommendations

| Metric Type | Scrape Interval | Use Case |
|-------------|-----------------|----------|
| Critical metrics | 15s | Real-time monitoring |
| Standard metrics | 30s | General monitoring |
| Long-term metrics | 1m-5m | Historical trends |

## Testing

### Unit Tests

Create tests for KPI recording:

```python
from backend.shared.kpi_metrics import scans_initiated_total, record_scan_start

def test_record_scan_start():
    record_scan_start(platform="hackerone", program_handle="test")
    samples = list(scans_initiated_total.collect()[0].samples)
    assert len(samples) == 1
    assert samples[0].value == 1.0
```

### Integration Tests

Verify KPIs in end-to-end flows:

```python
async def test_scan_kpi_flow():
    scan_id = await trigger_scan(platform="hackerone")
    await wait_for_scan_completion(scan_id)
    
    response = await client.get("/api/v1/kpi/RL-001")
    assert response.status_code == 200
    data = response.json()
    assert data["kpi_id"] == "RL-001"
```

## Files Reference

| File | Type | Purpose |
|------|------|---------|
| `docs/Core-Docs/KPIs/KPI_Framework.md` | Documentation | KPI definitions and targets |
| `docs/Core-Docs/KPIs/KPI_Integration_Guide.md` | Documentation | Integration guide |
| `backend/shared/kpi_metrics.py` | Code | Prometheus metrics implementation |
| `backend/services/api_gateway/kpi_routes.py` | Code | REST API endpoints |
| `grafana/dashboards/kpi_executive_dashboard.json` | Configuration | Executive dashboard |
| `grafana/alerts/kpi_alerts.yml` | Configuration | Alert rules |

## Version Information

| Component | Version | Date |
|-----------|---------|------|
| KPI Framework | 1.0 | 2026-03-29 |
| Prometheus Metrics | 1.0 | 2026-03-29 |
| Grafana Dashboards | 1.0 | 2026-03-29 |
| Alert Rules | 1.0 | 2026-03-29 |
| API Endpoints | 1.0 | 2026-03-29 |

## Next Steps

1. **Integrate KPI tracking** into existing services
2. **Deploy Prometheus scraping** configuration
3. **Import Grafana dashboards** and alert rules
4. **Test KPI flow** end-to-end
5. **Monitor and adjust** thresholds as needed
6. **Add custom KPIs** for specific use cases
7. **Create additional dashboards** (Operational, Security, Performance)

## Support

For issues or questions:

1. Review the KPI Framework document
2. Check the Integration Guide
3. Inspect Prometheus/Grafana logs
4. Refer to AttackBot architecture documentation

---

## License

This KPI system is part of the AttackBot platform and is licensed under the same terms.
