"""
KPI API Routes for AttackBot

This module provides REST API endpoints for accessing KPI data programmatically.
All endpoints return aggregated KPI values in JSON format.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from prometheus_client import REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST

router = APIRouter(prefix="/api/v1/kpi", tags=["KPI"])


class KpiResponse(BaseModel):
    """Base response model for KPI endpoints."""
    kpi_id: str
    category: str
    name: str
    value: float | int | Dict[str, Any]
    unit: str | None = None
    target: str | None = None
    calculated_at: datetime
    labels: Dict[str, Any] | None = None


class KpiCategoryResponse(BaseModel):
    """Response model for category-based KPI endpoints."""
    category: str
    kpis: Dict[str, KpiResponse]
    calculated_at: datetime


class AllKpisResponse(BaseModel):
    """Response model for all KPIs."""
    categories: Dict[str, KpiCategoryResponse]
    total_kpis: int
    calculated_at: datetime


class PrometheusMetricsResponse(BaseModel):
    """Response model for raw Prometheus metrics."""
    metrics: str
    content_type: str = CONTENT_TYPE_LATEST


# KPI metadata for reference
KPI_METADATA = {
    "SH-001": {
        "category": "System Health",
        "name": "System Uptime",
        "metric": "attackbot_sh_001_system_uptime_seconds",
        "unit": "seconds",
        "target": "> 99.9%",
        "description": "Total system uptime"
    },
    "SH-002": {
        "category": "System Health",
        "name": "Service Health Status",
        "metric": "attackbot_sh_002_service_health_status",
        "unit": "status",
        "target": "All healthy",
        "description": "Health status of all services"
    },
    "TP-001": {
        "category": "Throughput",
        "name": "Scans Initiated",
        "metric": "attackbot_tp_001_scans_initiated_total",
        "unit": "count",
        "target": "Track trend",
        "description": "Total number of scans initiated"
    },
    "TP-002": {
        "category": "Throughput",
        "name": "Scans Completed",
        "metric": "attackbot_tp_002_scans_completed_total",
        "unit": "count",
        "target": "Track trend",
        "description": "Total number of scans completed"
    },
    "TP-004": {
        "category": "Throughput",
        "name": "Findings Discovered",
        "metric": "attackbot_tp_004_findings_discovered_total",
        "unit": "count",
        "target": "Track trend",
        "description": "Total findings discovered"
    },
    "TP-006": {
        "category": "Throughput",
        "name": "Reports Generated",
        "metric": "attackbot_tp_006_reports_generated_total",
        "unit": "count",
        "target": "Track trend",
        "description": "Total reports generated"
    },
    "PF-001": {
        "category": "Performance",
        "name": "Average Scan Duration",
        "metric": "attackbot_pf_001_scan_duration_seconds",
        "unit": "seconds",
        "target": "< 30 min",
        "description": "Average scan completion time"
    },
    "PF-002": {
        "category": "Performance",
        "name": "Scan Duration P95",
        "metric": "attackbot_pf_002_scan_duration_summary_seconds",
        "unit": "seconds",
        "target": "< 45 min",
        "description": "95th percentile scan duration"
    },
    "PF-008": {
        "category": "Performance",
        "name": "Report Generation Duration",
        "metric": "attackbot_pf_008_report_generation_duration_seconds",
        "unit": "seconds",
        "target": "< 2 min",
        "description": "Report generation time"
    },
    "QL-001": {
        "category": "Quality",
        "name": "Verification Rate",
        "metric": "attackbot_ql_001_verified_findings_total",
        "unit": "percent",
        "target": "> 70%",
        "description": "Percentage of verified findings"
    },
    "QL-002": {
        "category": "Quality",
        "name": "False Positive Rate",
        "metric": "attackbot_ql_002_false_positive_findings_total",
        "unit": "percent",
        "target": "< 5%",
        "description": "Rate of false positive findings"
    },
    "QL-006": {
        "category": "Quality",
        "name": "Clean Scan Rate",
        "metric": "attackbot_ql_006_clean_scans_total",
        "unit": "percent",
        "target": "< 30%",
        "description": "Percentage of scans with zero findings"
    },
    "RL-001": {
        "category": "Reliability",
        "name": "Scan Success Rate",
        "metric": "attackbot_rl_001_scans_succeeded_total",
        "unit": "percent",
        "target": "> 95%",
        "description": "Percentage of successful scans"
    },
    "RL-002": {
        "category": "Reliability",
        "name": "Scan Failure Rate",
        "metric": "attackbot_rl_002_scans_failed_total",
        "unit": "percent",
        "target": "< 5%",
        "description": "Percentage of failed scans"
    },
    "RL-004": {
        "category": "Reliability",
        "name": "Report Generation Success Rate",
        "metric": "attackbot_rl_004_report_generation_success_total",
        "unit": "percent",
        "target": "> 98%",
        "description": "Report generation success rate"
    },
    "OP-001": {
        "category": "Operational",
        "name": "Programs Monitored",
        "metric": "attackbot_op_001_programs_monitored",
        "unit": "count",
        "target": "Track growth",
        "description": "Total programs being monitored"
    },
    "OP-002": {
        "category": "Operational",
        "name": "Active Scans",
        "metric": "attackbot_op_002_active_scans",
        "unit": "count",
        "target": "< max_capacity",
        "description": "Currently active scans"
    },
}


@router.get("/", response_model=AllKpisResponse)
async def get_all_kpis():
    """
    Get all KPIs organized by category.
    
    Returns comprehensive KPI data across all categories with current values.
    """
    from backend.shared.kpi_metrics import (
        # System Health
        system_uptime_seconds,
        service_health_status,
        database_connection_errors,
        rabbitmq_connection_errors,
        minio_connection_errors,
        vault_connection_errors,
        # Throughput
        scans_initiated_total,
        scans_completed_total,
        findings_discovered_total,
        reports_generated_total,
        programs_synced_total,
        # Performance
        scan_duration_seconds,
        scan_duration_summary,
        report_generation_duration,
        # Quality
        verified_findings_total,
        false_positive_findings_total,
        clean_scans_total,
        # Reliability
        scans_succeeded_total,
        scans_failed_total,
        report_generation_success_total,
        report_generation_failure_total,
        # Operational
        programs_monitored,
        active_scans,
        queued_scans,
        report_downloads_total,
        api_requests_total,
    )
    
    from backend.shared.kpi_metrics import KpiCalculator
    
    calculated_at = datetime.utcnow()
    
    # Build response
    categories = {}
    
    # System Health
    sh_kpis = {
        "SH-001": KpiResponse(
            kpi_id="SH-001",
            category="System Health",
            name="System Uptime",
            value=system_uptime_seconds._value.get(),
            unit="seconds",
            target="> 99.9%",
            calculated_at=calculated_at
        ),
        "SH-002": KpiResponse(
            kpi_id="SH-002",
            category="System Health",
            name="Service Health",
            value={
                service: val
                for service, val in service_health_status.collect()[0].samples
            },
            unit="status",
            target="All healthy",
            calculated_at=calculated_at
        ),
        "SH-003": KpiResponse(
            kpi_id="SH-003",
            category="System Health",
            name="Database Connection Errors",
            value=database_connection_errors._value.get(),
            unit="count",
            target="< 0.1%",
            calculated_at=calculated_at
        ),
    }
    categories["System Health"] = KpiCategoryResponse(
        category="System Health",
        kpis=sh_kpis,
        calculated_at=calculated_at
    )
    
    # Throughput
    tp_kpis = {
        "TP-001": KpiResponse(
            kpi_id="TP-001",
            category="Throughput",
            name="Scans Initiated",
            value=scans_initiated_total._value.get(),
            unit="count",
            target="Track trend",
            calculated_at=calculated_at
        ),
        "TP-002": KpiResponse(
            kpi_id="TP-002",
            category="Throughput",
            name="Scans Completed",
            value=scans_completed_total._value.get(),
            unit="count",
            target="Track trend",
            calculated_at=calculated_at
        ),
        "TP-004": KpiResponse(
            kpi_id="TP-004",
            category="Throughput",
            name="Findings Discovered",
            value=findings_discovered_total._value.get(),
            unit="count",
            target="Track trend",
            calculated_at=calculated_at
        ),
        "TP-006": KpiResponse(
            kpi_id="TP-006",
            category="Throughput",
            name="Reports Generated",
            value=reports_generated_total._value.get(),
            unit="count",
            target="Track trend",
            calculated_at=calculated_at
        ),
    }
    categories["Throughput"] = KpiCategoryResponse(
        category="Throughput",
        kpis=tp_kpis,
        calculated_at=calculated_at
    )
    
    # Performance
    pf_kpis = {
        "PF-001": KpiResponse(
            kpi_id="PF-001",
            category="Performance",
            name="Average Scan Duration",
            value={
                "sum": scan_duration_seconds._sum.get(),
                "count": scan_duration_seconds._count.get(),
                "average": scan_duration_seconds._sum.get() / max(scan_duration_seconds._count.get(), 1)
            },
            unit="seconds",
            target="< 30 min",
            calculated_at=calculated_at
        ),
        "PF-002": KpiResponse(
            kpi_id="PF-002",
            category="Performance",
            name="Scan Duration P95",
            value={
                "sum": scan_duration_summary._sum.get(),
                "count": scan_duration_summary._count.get(),
                "quantile_0.95": "Use PromQL quantile() function"
            },
            unit="seconds",
            target="< 45 min",
            calculated_at=calculated_at
        ),
        "PF-008": KpiResponse(
            kpi_id="PF-008",
            category="Performance",
            name="Report Generation Duration",
            value={
                "sum": report_generation_duration._sum.get(),
                "count": report_generation_duration._count.get(),
                "average": report_generation_duration._sum.get() / max(report_generation_duration._count.get(), 1)
            },
            unit="seconds",
            target="< 2 min",
            calculated_at=calculated_at
        ),
    }
    categories["Performance"] = KpiCategoryResponse(
        category="Performance",
        kpis=pf_kpis,
        calculated_at=calculated_at
    )
    
    # Quality
    ql_kpis = {
        "QL-001": KpiResponse(
            kpi_id="QL-001",
            category="Quality",
            name="Verified Findings",
            value=verified_findings_total._value.get(),
            unit="count",
            target="> 70%",
            calculated_at=calculated_at
        ),
        "QL-002": KpiResponse(
            kpi_id="QL-002",
            category="Quality",
            name="False Positives",
            value=false_positive_findings_total._value.get(),
            unit="count",
            target="< 5%",
            calculated_at=calculated_at
        ),
        "QL-006": KpiResponse(
            kpi_id="QL-006",
            category="Quality",
            name="Clean Scans",
            value=clean_scans_total._value.get(),
            unit="count",
            target="< 30%",
            calculated_at=calculated_at
        ),
    }
    categories["Quality"] = KpiCategoryResponse(
        category="Quality",
        kpis=ql_kpis,
        calculated_at=calculated_at
    )
    
    # Reliability
    rl_kpis = {
        "RL-001": KpiResponse(
            kpi_id="RL-001",
            category="Reliability",
            name="Scans Succeeded",
            value=scans_succeeded_total._value.get(),
            unit="count",
            target="> 95%",
            calculated_at=calculated_at
        ),
        "RL-002": KpiResponse(
            kpi_id="RL-002",
            category="Reliability",
            name="Scans Failed",
            value=scans_failed_total._value.get(),
            unit="count",
            target="< 5%",
            calculated_at=calculated_at
        ),
        "RL-004": KpiResponse(
            kpi_id="RL-004",
            category="Reliability",
            name="Report Generation Success",
            value={
                "success": report_generation_success_total._value.get(),
                "failure": report_generation_failure_total._value.get()
            },
            unit="count",
            target="> 98%",
            calculated_at=calculated_at
        ),
    }
    categories["Reliability"] = KpiCategoryResponse(
        category="Reliability",
        kpis=rl_kpis,
        calculated_at=calculated_at
    )
    
    # Operational
    op_kpis = {
        "OP-001": KpiResponse(
            kpi_id="OP-001",
            category="Operational",
            name="Programs Monitored",
            value=programs_monitored._value.get(),
            unit="count",
            target="Track growth",
            calculated_at=calculated_at
        ),
        "OP-002": KpiResponse(
            kpi_id="OP-002",
            category="Operational",
            name="Active Scans",
            value=active_scans._value.get(),
            unit="count",
            target="< max_capacity",
            calculated_at=calculated_at
        ),
        "OP-003": KpiResponse(
            kpi_id="OP-003",
            category="Operational",
            name="Queued Scans",
            value=queued_scans._value.get(),
            unit="count",
            target="< max_capacity",
            calculated_at=calculated_at
        ),
        "OP-005": KpiResponse(
            kpi_id="OP-005",
            category="Operational",
            name="Report Downloads",
            value=report_downloads_total._value.get(),
            unit="count",
            target="Track trend",
            calculated_at=calculated_at
        ),
        "OP-006": KpiResponse(
            kpi_id="OP-006",
            category="Operational",
            name="API Requests",
            value=api_requests_total._value.get(),
            unit="count",
            target="Track trend",
            calculated_at=calculated_at
        ),
    }
    categories["Operational"] = KpiCategoryResponse(
        category="Operational",
        kpis=op_kpis,
        calculated_at=calculated_at
    )
    
    return AllKpisResponse(
        categories=categories,
        total_kpis=sum(len(c.kpis) for c in categories.values()),
        calculated_at=calculated_at
    )


@router.get("/{kpi_id}", response_model=KpiResponse)
async def get_kpi_by_id(kpi_id: str):
    """
    Get a specific KPI by its ID.
    
    Args:
        kpi_id: The KPI identifier (e.g., "SH-001", "TP-001", "RL-001")
    
    Returns:
        The specific KPI value and metadata
    """
    if kpi_id not in KPI_METADATA:
        raise HTTPException(status_code=404, detail=f"KPI {kpi_id} not found")
    
    metadata = KPI_METADATA[kpi_id]
    
    # Dummy implementation - in practice, fetch from Prometheus
    # This is a placeholder that should be replaced with actual Prometheus queries
    value = 0
    
    return KpiResponse(
        kpi_id=kpi_id,
        category=metadata["category"],
        name=metadata["name"],
        value=value,
        unit=metadata["unit"],
        target=metadata["target"],
        calculated_at=datetime.utcnow()
    )


@router.get("/category/{category}", response_model=KpiCategoryResponse)
async def get_kpis_by_category(category: str):
    """
    Get all KPIs in a specific category.
    
    Args:
        category: The category name (e.g., "System Health", "Throughput", etc.)
    
    Returns:
        All KPIs in the specified category
    """
    if category not in KPI_METADATA.values():
        # Validate category exists
        available = set(m["category"] for m in KPI_METADATA.values())
        if category not in available:
            raise HTTPException(
                status_code=404,
                detail=f"Category '{category}' not found. Available: {sorted(available)}"
            )
    
    # Get all KPIs in this category - simplified implementation
    category_kpis = {}
    for kpi_id, metadata in KPI_METADATA.items():
        if metadata["category"] == category:
            category_kpis[kpi_id] = KpiResponse(
                kpi_id=kpi_id,
                category=category,
                name=metadata["name"],
                value=0,  # Placeholder
                unit=metadata["unit"],
                target=metadata["target"],
                calculated_at=datetime.utcnow()
            )
    
    return KpiCategoryResponse(
        category=category,
        kpis=category_kpis,
        calculated_at=datetime.utcnow()
    )


@router.get("/calculated/scan_success_rate", response_model=KpiResponse)
async def get_scan_success_rate():
    """
    Get calculated scan success rate (RL-001).
    
    Formula: (scans_succeeded_total / scans_initiated_total) * 100
    """
    from backend.shared.kpi_metrics import (
        scans_succeeded_total,
        scans_initiated_total,
        KpiCalculator
    )
    
    succeeded = scans_succeeded_total._value.get() or 0
    initiated = scans_initiated_total._value.get() or 0
    
    rate = KpiCalculator.calculate_scan_success_rate(succeeded, initiated)
    
    return KpiResponse(
        kpi_id="RL-001",
        category="Reliability",
        name="Scan Success Rate",
        value=rate,
        unit="percent",
        target="> 95%",
        calculated_at=datetime.utcnow(),
        labels={"numerator": succeeded, "denominator": initiated}
    )


@router.get("/calculated/verification_rate", response_model=KpiResponse)
async def get_verification_rate():
    """
    Get calculated verification rate (QL-001).
    
    Formula: (verified_findings_total / findings_discovered_total) * 100
    """
    from backend.shared.kpi_metrics import (
        verified_findings_total,
        findings_discovered_total,
        KpiCalculator
    )
    
    verified = verified_findings_total._value.get() or 0
    discovered = findings_discovered_total._value.get() or 0
    
    rate = KpiCalculator.calculate_verification_rate(verified, discovered)
    
    return KpiResponse(
        kpi_id="QL-001",
        category="Quality",
        name="Verification Rate",
        value=rate,
        unit="percent",
        target="> 70%",
        calculated_at=datetime.utcnow(),
        labels={"numerator": verified, "denominator": discovered}
    )


@router.get("/calculated/report_generation_success_rate", response_model=KpiResponse)
async def get_report_generation_success_rate():
    """
    Get calculated report generation success rate (RL-004).
    
    Formula: (report_generation_success_total / reports_generated_total) * 100
    """
    from backend.shared.kpi_metrics import (
        report_generation_success_total,
        reports_generated_total,
        KpiCalculator
    )
    
    succeeded = report_generation_success_total._value.get() or 0
    generated = reports_generated_total._value.get() or 0
    
    # Get only completed/failed reports
    # This is simplified - actual implementation needs to filter
    rate = KpiCalculator.calculate_report_generation_success_rate(succeeded, generated)
    
    return KpiResponse(
        kpi_id="RL-004",
        category="Reliability",
        name="Report Generation Success Rate",
        value=rate,
        unit="percent",
        target="> 98%",
        calculated_at=datetime.utcnow(),
        labels={"numerator": succeeded, "denominator": generated}
    )


@router.get("/prometheus/metrics")
async def get_prometheus_metrics():
    """
    Get raw Prometheus metrics for all KPIs.
    
    This endpoint exposes the raw Prometheus metrics that can be scraped
    by Prometheus itself or other monitoring tools.
    
    Returns:
        Raw Prometheus metrics in OpenMetrics format
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    metrics_data = generate_latest(REGISTRY)
    
    return PrometheusMetricsResponse(
        metrics=metrics_data.decode('utf-8'),
        content_type=CONTENT_TYPE_LATEST
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for KPI service.
    
    Returns:
        Simple health status
    """
    return {
        "status": "healthy",
        "service": "kpi-api",
        "timestamp": datetime.utcnow().isoformat(),
        "kpi_count": len(KPI_METADATA)
    }
