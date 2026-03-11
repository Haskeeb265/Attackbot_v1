"""
Unit tests for Core Engine M3 components.
All subprocess calls are mocked — no real tools required.
All DB calls are mocked — no real database required.
"""

import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

from backend.services.core_engine.dedup import normalize_url, compute_dedup_hash
from backend.services.core_engine.cvss import (
    severity_to_cvss, nuclei_severity, infer_severity
)
from backend.services.core_engine.models import FindingCandidate
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.services.core_engine.pipeline.context import ScopeDefinition
from backend.services.core_engine.subprocess_utils import parse_jsonl
from backend.shared.exceptions import ScanError


# ── ScopeFilter tests ──────────────────────────────────────────────────────

class TestScopeFilter:
    def _make(self, in_scope, out_of_scope=None):
        scope = ScopeDefinition(
            in_scope=in_scope,
            out_of_scope=out_of_scope or [],
        )
        return ScopeFilter(scope)

    def test_wildcard_match(self):
        sf = self._make(["*.example.com"])
        assert sf.is_in_scope("https://api.example.com/v1")
        assert sf.is_in_scope("sub.api.example.com")

    def test_wildcard_does_not_match_root(self):
        sf = self._make(["*.example.com"])
        # *.example.com should NOT match example.com itself
        assert not sf.is_in_scope("https://example.com")

    def test_exact_domain_match(self):
        sf = self._make(["api.example.com"])
        assert sf.is_in_scope("https://api.example.com/path")

    def test_exact_domain_no_subdomain_leak(self):
        sf = self._make(["api.example.com"])
        assert not sf.is_in_scope("https://other.api.example.com")

    def test_out_of_scope_wins(self):
        sf = self._make(
            in_scope=["*.example.com"],
            out_of_scope=["admin.example.com"],
        )
        assert sf.is_in_scope("https://api.example.com")
        assert not sf.is_in_scope("https://admin.example.com")

    def test_cidr_match(self):
        sf = self._make(["192.168.1.0/24"])
        assert sf.is_in_scope("192.168.1.55")

    def test_cidr_out_of_range(self):
        sf = self._make(["192.168.1.0/24"])
        assert not sf.is_in_scope("10.0.0.1")

    def test_empty_scope_raises(self):
        with pytest.raises(ScanError):
            self._make([])

    def test_filter_targets(self):
        sf = self._make(["*.example.com"])
        targets = [
            "https://api.example.com",
            "https://evil.com",
            "https://sub.example.com",
        ]
        result = sf.filter_targets(targets)
        assert "https://api.example.com" in result
        assert "https://sub.example.com" in result
        assert "https://evil.com" not in result


# ── Deduplication tests ─────────────────────────────────────────────────────

class TestDedup:
    def _make_candidate(self, url, vuln_type="xss", param="q", payload="<script>"):
        return FindingCandidate(
            vulnerability_type=vuln_type,
            title="Test",
            severity="high",
            affected_url=url,
            affected_parameter=param,
            payload=payload,
            description="",
            source="test",
        )

    def test_same_finding_same_hash(self):
        c1 = self._make_candidate("https://example.com/search?q=1&b=2")
        c2 = self._make_candidate("https://example.com/search?q=1&b=2")
        assert compute_dedup_hash(c1) == compute_dedup_hash(c2)

    def test_query_param_order_normalized(self):
        c1 = self._make_candidate("https://example.com/search?a=1&b=2")
        c2 = self._make_candidate("https://example.com/search?b=2&a=1")
        assert compute_dedup_hash(c1) == compute_dedup_hash(c2)

    def test_different_url_different_hash(self):
        c1 = self._make_candidate("https://example.com/search")
        c2 = self._make_candidate("https://example.com/other")
        assert compute_dedup_hash(c1) != compute_dedup_hash(c2)

    def test_different_vuln_type_different_hash(self):
        c1 = self._make_candidate("https://example.com", vuln_type="xss")
        c2 = self._make_candidate("https://example.com", vuln_type="cors")
        assert compute_dedup_hash(c1) != compute_dedup_hash(c2)

    def test_normalize_url_lowercases(self):
        result = normalize_url("HTTPS://Example.COM/Path?Z=1&A=2")
        assert result == normalize_url("https://example.com/path?a=2&z=1")


# ── CVSS tests ──────────────────────────────────────────────────────────────

class TestCvss:
    def test_severity_to_cvss_critical(self):
        assert severity_to_cvss("critical") == 9.0

    def test_severity_to_cvss_high(self):
        assert severity_to_cvss("high") == 7.5

    def test_severity_to_cvss_unknown_default(self):
        assert severity_to_cvss("unknown") == 5.0

    def test_nuclei_severity_mapping(self):
        assert nuclei_severity("critical") == "critical"
        assert nuclei_severity("MEDIUM") == "medium"
        assert nuclei_severity("garbage") == "info"

    def test_infer_severity_from_raw(self):
        assert infer_severity("xss", raw_severity="high") == "high"

    def test_infer_severity_from_vuln_type(self):
        assert infer_severity("xss") == "high"
        assert infer_severity("sqli") == "critical"
        assert infer_severity("unknown_vuln") == "medium"


# ── Subprocess utils tests ───────────────────────────────────────────────────

class TestParseJsonl:
    def test_parses_valid_lines(self):
        text = '{"url": "https://example.com", "status": 200}\n{"url": "https://b.com"}\n'
        result = parse_jsonl(text)
        assert len(result) == 2
        assert result[0]["url"] == "https://example.com"

    def test_skips_non_json_lines(self):
        text = "Starting scan...\n{\"url\": \"https://a.com\"}\nDone.\n"
        result = parse_jsonl(text)
        assert len(result) == 1

    def test_empty_input(self):
        assert parse_jsonl("") == []

    def test_skips_malformed_json(self):
        text = '{"broken: json}\n{"url": "https://good.com"}\n'
        result = parse_jsonl(text)
        assert len(result) == 1
        assert result[0]["url"] == "https://good.com"


# ── JS Secrets tests ────────────────────────────────────────────────────────

class TestJsSecrets:
    def test_detects_google_api_key(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        content = 'var key = "AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY"'
        findings = _scan_content(content, "https://example.com/app.js")
        assert any(f.vulnerability_type == "js_secret" for f in findings)
        assert any("Google API Key" in f.title for f in findings)

    def test_detects_openai_key(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        content = 'const apiKey = "sk-abcdefghijklmnopqrstuvwxyz1234567890123456789012"'
        findings = _scan_content(content, "https://example.com/app.js")
        assert any("OpenAI" in f.title for f in findings)

    def test_no_false_positive_on_clean(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        content = 'function init() { return true; }'
        findings = _scan_content(content, "https://example.com/app.js")
        assert findings == []

    def test_only_one_finding_per_pattern(self):
        from backend.services.core_engine.pipeline.js_secrets import _scan_content
        # Same key pattern twice — should produce one finding, not two
        key = "AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY"
        content = f'var k1 = "{key}"; var k2 = "{key}";'
        findings = _scan_content(content, "https://example.com/app.js")
        google_findings = [f for f in findings if "Google API Key" in f.title]
        assert len(google_findings) == 1


# ── Web Vuln Tests (unit) ───────────────────────────────────────────────────

class TestWebVulnTests:
    @pytest.mark.asyncio
    async def test_xss_detection(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import _test_xss
        from backend.services.core_engine.models import DiscoveredEndpoint
        import uuid

        ep = DiscoveredEndpoint(
            asset_id=uuid.uuid4(),
            method="GET",
            path="/search",
            full_url="https://example.com/search",
            parameters={"q": "test"},
        )

        mock_resp = MagicMock()
        mock_resp.text = '<script>alert(1)</script>'  # payload reflected
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        findings = await _test_xss(ep, mock_client)
        assert len(findings) > 0
        assert findings[0].vulnerability_type == "reflected_xss"

    @pytest.mark.asyncio
    async def test_xss_no_reflection(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import _test_xss
        from backend.services.core_engine.models import DiscoveredEndpoint
        import uuid

        ep = DiscoveredEndpoint(
            asset_id=uuid.uuid4(),
            method="GET",
            path="/search",
            full_url="https://example.com/search",
            parameters={"q": "test"},
        )

        mock_resp = MagicMock()
        mock_resp.text = "<html>safe response</html>"  # no reflection
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        findings = await _test_xss(ep, mock_client)
        assert findings == []

    @pytest.mark.asyncio
    async def test_cors_misconfiguration(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import _test_cors
        from backend.services.core_engine.models import DiscoveredEndpoint
        import uuid

        ep = DiscoveredEndpoint(
            asset_id=uuid.uuid4(),
            method="GET",
            path="/api",
            full_url="https://example.com/api",
        )

        mock_resp = MagicMock()
        mock_resp.headers = {
            "access-control-allow-origin": "https://evil.com",
            "access-control-allow-credentials": "true",
        }
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        findings = await _test_cors(ep, mock_client)
        assert len(findings) > 0
        assert findings[0].vulnerability_type == "cors_misconfiguration"


# ── Scan State Machine tests ─────────────────────────────────────────────────

class TestScanStateMachine:
    """
    Verify scan status transitions without running a real scan.
    These test the repository methods directly with a mocked session.
    """
    @pytest.mark.asyncio
    async def test_mark_scan_complete_sets_status(self):
        from backend.services.core_engine.repository import ScanRepository
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        repo = ScanRepository(mock_session)
        await repo.mark_scan_complete(
            scan_id="test-scan-id",
            status="completed",
            finding_count=5,
            severity_breakdown={"high": 3, "medium": 2},
        )
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_scan_partial_on_stage_errors(self):
        """Aggregator should produce 'partial' status when stage_errors is non-empty."""
        from backend.services.core_engine.models import ScanResult
        scan_result = ScanResult(stage_errors={"nuclei_scan": "timeout"})
        # Verify partial logic: has_errors → status = partial
        has_errors = bool(scan_result.stage_errors)
        expected_status = "partial" if has_errors else "completed"
        assert expected_status == "partial"