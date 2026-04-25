# AttackBot KPI Integration Guide

## Overview

This guide explains how to integrate KPI tracking into the AttackBot platform. KPIs are implemented using Prometheus metrics and are exposed through multiple channels:

1. **Prometheus Metrics** - Direct metric collection by Prometheus
2. **REST API** - Programmatic access via HTTP endpoints
3. **Grafana Dashboards** - Visual monitoring and alerting

---

## Quick Start

### 1. Import KPI Metrics in Your Service

In any service that needs to track KPIs, import the metrics module:

```python
from backend.shared.kpi_metrics import (
    # System Health
    system_uptime_seconds,
    service_health_status,
    database_connection_errors,
    
    # Throughput
    scans_initiated_total,
    scans_completed_total,
    findings_discovered_total,
    
    # Performance
    scan_duration_seconds,
    stage_duration_seconds,
    
    # Quality
    verified_findings_total,
    false_positive_findings_total,
    
    # Reliability
    scans_succeeded_total,
    scans_failed_total,
    
    # Helper functions
    record_scan_start,
    record_scan_complete,
    record_finding,
    record_stage_duration,
)
```

### 2. Record KPI Events

Use the helper functions to record KPI-relevant events:

```python
# When a scan starts
record_scan_start(
    platform="hackerone",
    program_handle="example-program"
)

# When a scan completes
record_scan_complete(
    status="completed",
    platform="hackerone", 
    duration_seconds=180.5,
    finding_count=5,
    severity_breakdown={
        "critical": 1,
        "high": 2,
        "medium": 1,
        "low": 1,
        "info": 0
    }
)

# When a finding is discovered
record_finding(
    severity="high",
    vulnerability_type="xss",
    platform="hackerone",
    is_verified=False,
    evidence_quality=85
)

# When a pipeline stage completes
record_stage_duration(
    stage_name="asset_discovery",
    duration_seconds=120.3,
    status="completed"
)
```

---

## Metrics Collection

### Prometheus Configuration

Add the following to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'attackbot'
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: '/api/v1/kpi/prometheus/metrics'
    static_configs:
      - targets: ['api-gateway:8000']
```

Prometheus will scrape all AttackBot KPI metrics from the endpoint.

### Direct Metric Access

All metrics are registered with the default Prometheus registry and can be accessed:

```python
from prometheus_client import REGISTRY, generate_latest

metrics = generate_latest(REGISTRY)
```

---

## API Integration

### Endpoints

The KPI API is available at `/api/v1/kpi/` on the API Gateway service.

#### GET /api/v1/kpi/
Returns all KPIs organized by category.

**Example Response:**
```json
{
  "categories": {
    "System Health": {
      "category": "System Health",
      "kpis": {
        "SH-001": {
          "kpi_id": "SH-001",
          "category": "System Health",
          "name": "System Uptime",
          "value": 86400.5,
          "unit": "seconds",
          "target": "> 99.9%",
          "calculated_at": "2026-03-29T10:00:00Z"
        },
        ...
      },
      "calculated_at": "2026-03-29T10:00:00Z"
    },
    ...
  },
  "total_kpis": 24,
  "calculated_at": "2026-03-29T10:00:00Z"
}
```

#### GET /api/v1/kpi/{kpi_id}
Returns a specific KPI by ID.

**Example:**
```bash
curl http://localhost:8000/api/v1/kpi/RL-001
```

#### GET /api/v1/kpi/category/{category}
Returns all KPIs in a category.

**Example:**
```bash
curl http://localhost:8000/api/v1/kpi/category/Reliability
```

#### GET /api/v1/kpi/calculated/scan_success_rate
Returns calculated scan success rate.

**Example Response:**
```json
{
  "kpi_id": "RL-001",
  "category": "Reliability",
  "name": "Scan Success Rate",
  "value": 98.5,
  "unit": "percent",
  "target": "> 95%",
  "calculated_at": "2026-03-29T10:00:00Z",
  "labels": {
    "numerator": 985,
    "denominator": 1000
  }
}
```

#### GET /api/v1/kpi/prometheus/metrics
Returns raw Prometheus metrics in OpenMetrics format.

---

## Service-Specific Integration

### Core Engine Service

Integrate KPI tracking into scan processing:

```python
# In scan_task.py or similar
from backend.shared.kpi_metrics import (
    record_scan_start,
    record_scan_complete,
    record_stage_duration,
    record_finding,
)

async def process_scan(scan_id: str, program_id: str, platform: str):
    # Record scan start
    record_scan_start(platform=platform, program_handle="...")
    
    start_time = time.time()
    
    try:
        # Process stages
        stage_start = time.time()
        await process_asset_discovery()
        record_stage_duration(
            stage_name="asset_discovery",
            duration_seconds=time.time() - stage_start,
            status="completed"
        )
        
        # ... other stages
        
        # Record scan completion
        duration = time.time() - start_time
        record_scan_complete(
            status="completed",
            platform=platform,
            duration_seconds=duration,
            finding_count=findings_count,
            severity_breakdown=severity_counts
        )
        
    except Exception as e:
        record_scan_complete(
            status=f"failed_{type(e).__name__}",
            platform=platform,
            duration_seconds=time.time() - start_time,
            finding_count=0
        )
        raise
```

### Reporter Service

Integrate KPI tracking into report generation:

```python
# In report_task.py
from backend.shared.kpi_metrics import (
    record_report_generation,
    record_finding,
    verified_findings_total,
)

async def generate_report(report_id: str, format: str, scan_data: dict):
    start_time = time.time()
    
    try:
        # Process findings
        for finding in scan_data.findings:
            record_finding(
                severity=finding.severity,
                vulnerability_type=finding.vulnerability_type,
                platform=scan_data.platform,
                is_verified=finding.is_verified,
                evidence_quality=finding.evidence_quality
            )
            
            if finding.is_verified:
                verified_findings_total.labels(
                    severity=finding.severity,
                    platform=scan_data.platform
                ).inc()
        
        # Generate report
        await _generate_report_file(...)
        
        # Record successful generation
        duration = time.time() - start_time
        record_report_generation(
            format=format,
            duration_seconds=duration,
            success=True
        )
        
    except Exception as e:
        record_report_generation(
            format=format,
            duration_seconds=time.time() - start_time,
            success=False,
            failure_reason=str(type(e).__name__)
        )
        raise
```

### Scraper Service

Integrate KPI tracking into program sync:

```python
# In scraper tasks
from backend.shared.kpi_metrics import programs_synced_total

async def sync_platform(platform: str):
    try:
        count = await _sync_platform_programs(platform)
        programs_synced_total.labels(platform=platform, status="success").inc(count)
    except Exception as e:
        programs_synced_total.labels(platform=platform, status="failed").inc()
        raise
```

### API Gateway Service

Integrate KPI tracking for API requests:

```python
# In middleware or request handlers
from backend.shared.kpi_metrics import record_api_request
import time

@app.middleware("http")
async def track_api_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    record_api_request(
        service="api-gateway",
        endpoint=request.url.path,
        http_method=request.method,
        status_code=response.status_code,
        duration_seconds=duration
    )
    
    return response
```

---

## Grafana Setup

### Import Dashboards

1. Copy the dashboard JSON files from `grafana/dashboards/` to your Grafana dashboards directory
2. In Grafana, go to Dasboards > Import
3. Upload the JSON file or paste the JSON content

### Configure Data Source

1. In Grafana, go to Configuration > Data Sources
2. Click "Add data source" and select Prometheus
3. Set the URL to `http://prometheus:9090` (or your Prometheus server)
4. Save the data source

### Alert Rules

Import the alert rules from `grafana/alerts/kpi_alerts.yml`:

1. In Grafana, go to Alerting > Alert rules
2. Click "Import" and upload the YAML file
3. Ensure the Contact Points are configured for notifications

---

## PromQL Examples

### Scan Success Rate (RL-001)
```promql
(
  sum(rate(attackbot_rl_001_scans_succeeded_total[1h]))
  /
  sum(rate(attackbot_tp_001_scans_initiated_total[1h]))
) * 100
```

### Average Scan Duration (PF-001)
```promql
avg(attackbot_pf_001_scan_duration_seconds_sum) 
/
avg(attackbot_pf_001_scan_duration_seconds_count)
```

### 95th Percentile Scan Duration (PF-002)
```promql
quantile(
  0.95,
  attackbot_pf_002_scan_duration_summary_seconds_sum 
  / 
  attackbot_pf_002_scan_duration_summary_seconds_count
)
```

### Verification Rate (QL-001)
```promql
(
  sum(rate(attackbot_ql_001_verified_findings_total[1d]))
  /
  sum(rate(attackbot_tp_004_findings_discovered_total[1d]))
) * 100
```

### False Positive Rate (QL-002)
```promql
(
  sum(rate(attackbot_ql_002_false_positive_findings_total[1d]))
  /
  sum(rate(attackbot_ql_001_verified_findings_total[1d]))
) * 100
```

---

## Custom KPIs

### Adding New KPIs

To add a new KPI:

1. **Define the metric** in `backend/shared/kpi_metrics.py`:

```python
from prometheus_client import Counter

# New metric for tracking API authentication failures
authentication_failures_total = Counter(
    'attackbot_custom_auth_failures_total',
    'Total authentication failures',
    ['service', 'reason']
)
```

2. **Add helper function**:

```python
def record_authentication_failure(service: str, reason: str) -> None:
    """Record an authentication failure."""
    authentication_failures_total.labels(service=service, reason=reason).inc()
```

3. **Update KPI Framework** in `docs/Core-Docs/KPIs/KPI_Framework.md`:

```markdown
| KPI ID | Metric Name | Description | Target | Priority |
|--------|-------------|-------------|--------|----------|
| CUSTOM-001 | `authentication_failures_total` | Authentication failures | < 1% | High |
```

4. **Create alerts** in `grafana/alerts/kpi_alerts.yml`:

```yaml
- alert: AuthenticationFailuresHigh
  expr: rate(attackbot_custom_auth_failures_total[5m]) > 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High authentication failure rate"
```

5. **Add to dashboards** - Update the Grafana dashboard JSON files to include the new metric.

---

## Testing KPIs

### Unit Tests

Create unit tests to verify KPI recording:

```python
# tests/unit/test_kpi_metrics.py
from backend.shared.kpi_metrics import (
    scans_initiated_total,
    record_scan_start,
    record_scan_complete,
)

def test_record_scan_start():
    """Test scan start recording."""
    record_scan_start(platform="hackerone", program_handle="test")
    
    # Verify counter was incremented
    samples = list(scans_initiated_total.collect()[0].samples)
    assert len(samples) == 1
    assert samples[0].value == 1.0
    assert samples[0].labels == {'platform': 'hackerone', 'program_handle': 'test'}
```

### Integration Tests

Verify KPIs are properly recorded in end-to-end flows:

```python
# tests/integration/test_kpi_integration.py
async def test_scan_kpi_flow():
    """Test KPI recording during scan flow."""
    # Trigger a scan
    scan_id = await trigger_scan(platform="hackerone")
    
    # Wait for completion
    await wait_for_scan_completion(scan_id)
    
    # Verify KPIs were recorded
    response = await client.get("/api/v1/kpi/RL-001")
    assert response.status_code == 200
    
    data = response.json()
    assert data["kpi_id"] == "RL-001"
    assert data["category"] == "Reliability"
```

---

## Performance Considerations

### Metric Cardinality

Prometheus metrics have cardinality constraints. Be mindful of label combinations:

**High Cardinality Labels (AVOID):**
- User IDs
- Request IDs
- Timestamps as labels
- IP addresses

**Low Cardinality Labels (OK):**
- Service names
- Platform names
- Severity levels
- Status codes
- HTTP methods

### Metric Retention

Configure appropriate retention policies in Prometheus:

```yaml
# prometheus.yml
storage:
  tsdb:
    retention:
      time: 90d  # Keep 90 days of data
      size: "500GB"  # Or by size
```

### Scrape Interval

Balance scrape interval with load:
- Critical metrics: 15-30 seconds
- Standard metrics: 30-60 seconds
- Long-term trends: 1-5 minutes

---

## Troubleshooting

### Metrics Not Appearing

1. **Check Prometheus scraping:**
   ```bash
   curl http://api-gateway:8000/api/v1/kpi/prometheus/metrics
   ```

2. **Verify metric registration:**
   ```python
   from prometheus_client import REGISTRY
   print(list(REGISTRY.collect()))
   ```

3. **Check Prometheus targets:**
   - Go to Prometheus UI
   - Navigate to Status > Targets
   - Verify all targets are UP

### Grafana Dashboard Issues

1. **Verify data source:**
   - Check that Prometheus data source is configured
   - Test query in Grafana Explore

2. **Check metric names:**
   - Ensure metric names in dashboard match actual metric names
   - Use Prometheus UI to verify metric names

3. **Import errors:**
   - Ensure JSON formatting is correct
   - Check for duplicate dashboard UIDs

---

## Best Practices

1. **Consistent Naming:** Follow the KPI naming convention (Category-ID)
2. **Label Consistency:** Use consistent label names across similar metrics
3. **Unit Clarity:** Always specify units in metric descriptions
4. **Documentation:** Document all KPIs in the framework document
5. **Alert Thresholds:** Set meaningful, actionable thresholds
6. **Review Regularly:** Review KPIs regularly to ensure relevance
7. **Avoid Duplication:** Don't create multiple metrics for the same concept

---

## Files Reference

| File | Purpose |
|------|---------|
| `backend/shared/kpi_metrics.py` | Prometheus metrics definitions |
| `backend/services/api_gateway/kpi_routes.py` | KPI REST API endpoints |
| `docs/Core-Docs/KPIs/KPI_Framework.md` | KPI definitions and categories |
| `docs/Core-Docs/KPIs/KPI_Integration_Guide.md` | This guide |
| `grafana/dashboards/kpi_executive_dashboard.json` | Executive dashboard |
| `grafana/alerts/kpi_alerts.yml` | Alert rules |

---

## Support

For issues or questions about KPIs:

1. Check the KPI Framework document for definitions
2. Review this integration guide for implementation details
3. Check Prometheus/Grafana logs for errors
4. Consult the AttackBot architecture documentation
