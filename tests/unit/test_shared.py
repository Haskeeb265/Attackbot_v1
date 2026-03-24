# tests/unit/test_shared.py
"""
Unit tests for the shared library.
These tests run without any infrastructure (no DB, no RabbitMQ, no MinIO).
"""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.shared.config import BaseServiceConfig

from backend.shared.exceptions import (
    AttackBotError,
    CollectorRateLimitError,
    MessageSchemaError,
    QueueConnectionError,
    ScanError,
    ScanTimeoutError,
    ScopeFatalError,
)
from backend.shared.health import HealthResponse, HealthStatus, ComponentHealth
from backend.shared.schemas.envelope import MessageEnvelope, build_envelope
from backend.shared.schemas.report_jobs import (
    ExploitChainRef,
    ReportJobsPayload,
    SeverityBreakdown,
    build_report_job_message,
)
from backend.shared.schemas.scan_jobs import (
    FeatureFlags,
    ScanJobsPayload,
    ScopeDefinition,
    ScopeEntry,
    build_scan_job_message,
)

class _DummyServiceConfig(BaseServiceConfig):
    service_name: str = "dummy"


class TestBaseServiceConfigScaling:
    def test_scaled_timeout_respects_floor(self):
        cfg = _DummyServiceConfig(
            e2e_tool_timeout_scale=0.1,
            e2e_tool_timeout_floor_seconds=30,
        )
        assert cfg.scaled_timeout(60) == 30
        assert cfg.scaled_scan_timeout_seconds(60) == 300


# ── Exception hierarchy ────────────────────────────────────────────────────

class TestExceptionHierarchy:
    def test_scan_timeout_is_scan_error(self):
        assert issubclass(ScanTimeoutError, ScanError)

    def test_scan_error_is_attackbot_error(self):
        assert issubclass(ScanError, AttackBotError)

    def test_scope_fatal_is_attackbot_error(self):
        assert issubclass(ScopeFatalError, AttackBotError)

    def test_queue_connection_is_queue_error(self):
        from backend.shared.exceptions import QueueError
        assert issubclass(QueueConnectionError, QueueError)

    def test_collector_rate_limit_is_collector_error(self):
        from backend.shared.exceptions import CollectorError
        assert issubclass(CollectorRateLimitError, CollectorError)

    def test_exceptions_are_catchable_as_base(self):
        with pytest.raises(AttackBotError):
            raise ScanTimeoutError("timed out")


# ── HealthResponse ─────────────────────────────────────────────────────────

class TestHealthResponse:
    def test_healthy_response(self):
        resp = HealthResponse(
            status=HealthStatus.HEALTHY,
            service="test-service",
            timestamp=datetime.now(timezone.utc),
        )
        assert resp.is_healthy()

    def test_unhealthy_response(self):
        resp = HealthResponse(
            status=HealthStatus.UNHEALTHY,
            service="test-service",
            timestamp=datetime.now(timezone.utc),
        )
        assert not resp.is_healthy()

    def test_with_components(self):
        resp = HealthResponse(
            status=HealthStatus.DEGRADED,
            service="test-service",
            timestamp=datetime.now(timezone.utc),
            components={
                "database": ComponentHealth(status=HealthStatus.HEALTHY),
                "rabbitmq": ComponentHealth(status=HealthStatus.UNHEALTHY, detail="connection refused"),
            },
        )
        assert resp.components["database"].status == HealthStatus.HEALTHY
        assert resp.components["rabbitmq"].detail == "connection refused"


# ── MessageEnvelope ────────────────────────────────────────────────────────

class TestMessageEnvelope:
    def test_build_envelope_produces_valid_envelope(self):
        msg = build_envelope(
            event_type="test.event",
            payload={"key": "value"},
            source_service="test-service",
        )
        envelope = MessageEnvelope.model_validate(msg)
        assert envelope.event_type == "test.event"
        assert envelope.source_service == "test-service"
        assert envelope.schema_version == "1.0"
        assert envelope.payload == {"key": "value"}

    def test_envelope_has_auto_event_id(self):
        msg = build_envelope("x.y", {}, "svc")
        assert msg["event_id"]
        # Should be a valid UUID string
        uuid.UUID(msg["event_id"])

    def test_envelope_has_utc_timestamp(self):
        msg = build_envelope("x.y", {}, "svc")
        envelope = MessageEnvelope.model_validate(msg)
        assert envelope.timestamp.tzinfo is not None

    def test_get_major_version(self):
        envelope = MessageEnvelope(
            event_type="x.y",
            schema_version="2.3",
            source_service="svc",
            payload={},
        )
        assert envelope.get_major_version() == 2

    def test_envelope_ignores_extra_fields(self):
        """Forward-compatibility: extra fields should not cause validation error."""
        msg = build_envelope("x.y", {}, "svc")
        msg["future_field"] = "some_value"
        envelope = MessageEnvelope.model_validate(msg)
        assert envelope.event_type == "x.y"

    def test_trace_id_is_optional(self):
        msg = build_envelope("x.y", {}, "svc", trace_id=None)
        envelope = MessageEnvelope.model_validate(msg)
        assert envelope.trace_id is None

    def test_trace_id_propagated(self):
        msg = build_envelope("x.y", {}, "svc", trace_id="abc123")
        envelope = MessageEnvelope.model_validate(msg)
        assert envelope.trace_id == "abc123"


# ── ScanJobsPayload ────────────────────────────────────────────────────────

def _make_scope(**kwargs):
    defaults = {
        "in_scope": [ScopeEntry(asset_type="wildcard_domain", value="*.example.com")],
        "out_of_scope": [],
    }
    defaults.update(kwargs)
    return ScopeDefinition(**defaults)


def _make_scan_payload(**kwargs):
    defaults = {
        "program_id": uuid.uuid4(),
        "platform": "hackerone",
        "handle": "test_program",
        "scope": _make_scope(),
    }
    defaults.update(kwargs)
    return ScanJobsPayload(**defaults)


class TestScanJobsPayload:
    def test_valid_payload_constructs(self):
        payload = _make_scan_payload()
        assert payload.platform == "hackerone"
        assert payload.feature_flags.asset_discovery is True
        assert payload.feature_flags.sqli is False

    def test_scope_must_have_in_scope_entries(self):
        with pytest.raises(ValidationError, match="in_scope"):
            _make_scan_payload(scope=ScopeDefinition(in_scope=[]))

    def test_feature_flags_defaults(self):
        flags = FeatureFlags()
        # Enabled by default
        assert flags.asset_discovery is True
        assert flags.nuclei is True
        assert flags.browser_session is True
        # Disabled by default
        assert flags.sqli is False
        assert flags.ssrf is False
        assert flags.ai_hypothesis is False
        assert flags.idor_verification is False

    def test_feature_flags_ignore_extra(self):
        """Future flags should not break existing deployments."""
        flags = FeatureFlags.model_validate({"asset_discovery": True, "future_flag": True})
        assert flags.asset_discovery is True

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            _make_scan_payload(priority=0)  # below minimum
        with pytest.raises(ValidationError):
            _make_scan_payload(priority=11)  # above maximum

    def test_scan_timeout_bounds(self):
        with pytest.raises(ValidationError):
            _make_scan_payload(scan_timeout_seconds=100)  # below 300
        with pytest.raises(ValidationError):
            _make_scan_payload(scan_timeout_seconds=999999)  # above 86400

    def test_build_scan_job_message(self):
        payload = _make_scan_payload()
        msg = build_scan_job_message(payload, source_service="scraper", trace_id="t1")
        assert msg["event_type"] == "program.scraped"
        assert msg["source_service"] == "scraper"
        assert msg["trace_id"] == "t1"
        # Nested payload has the program_id
        inner = ScanJobsPayload.model_validate(msg["payload"])
        assert inner.program_id == payload.program_id

    def test_scope_entry_types(self):
        scope = ScopeDefinition(
            in_scope=[
                ScopeEntry(asset_type="url", value="https://example.com"),
                ScopeEntry(asset_type="wildcard_domain", value="*.example.com"),
                ScopeEntry(asset_type="ip_range", value="10.0.0.0/8"),
            ]
        )
        assert len(scope.in_scope) == 3

    def test_invalid_platform_rejected(self):
        with pytest.raises(ValidationError):
            _make_scan_payload(platform="unknown_platform")


# ── ReportJobsPayload ──────────────────────────────────────────────────────

def _make_report_payload(**kwargs):
    defaults = {
        "scan_id": uuid.uuid4(),
        "program_id": uuid.uuid4(),
        "status": "completed",
        "has_findings": True,
        "finding_count": 5,
        "verified_count": 5,
        "severity_breakdown": SeverityBreakdown(high=3, medium=2),
    }
    defaults.update(kwargs)
    return ReportJobsPayload(**defaults)


class TestReportJobsPayload:
    def test_valid_payload_constructs(self):
        payload = _make_report_payload()
        assert payload.status == "completed"
        assert payload.has_findings is True

    def test_severity_breakdown_total(self):
        bd = SeverityBreakdown(critical=1, high=3, medium=4, low=1)
        assert bd.total == 9

    def test_no_findings_consistency(self):
        """has_findings=False must have finding_count=0."""
        payload = _make_report_payload(has_findings=False, finding_count=0)
        assert payload.has_findings is False

    def test_has_findings_false_but_count_nonzero_raises(self):
        with pytest.raises(ValidationError, match="Inconsistent"):
            _make_report_payload(has_findings=False, finding_count=3)

    def test_has_findings_true_but_count_zero_raises(self):
        with pytest.raises(ValidationError, match="Inconsistent"):
            _make_report_payload(has_findings=True, finding_count=0)

    def test_exploit_chains_default_empty(self):
        payload = _make_report_payload()
        assert payload.exploit_chains == []

    def test_exploit_chain_ref(self):
        chain = ExploitChainRef(
            chain_id=uuid.uuid4(),
            chain_name="Subdomain Takeover → IDOR",
            combined_severity="critical",
            step_count=3,
        )
        assert chain.combined_severity == "critical"

    def test_formats_requested_default(self):
        payload = _make_report_payload()
        assert "pdf" in payload.formats_requested
        assert "docx" in payload.formats_requested

    def test_formats_requested_min_one(self):
        with pytest.raises(ValidationError):
            _make_report_payload(formats_requested=[])

    def test_build_report_job_message(self):
        payload = _make_report_payload()
        msg = build_report_job_message(payload, source_service="core-engine")
        assert msg["event_type"] == "scan.completed"
        assert msg["source_service"] == "core-engine"
        inner = ReportJobsPayload.model_validate(msg["payload"])
        assert inner.scan_id == payload.scan_id
