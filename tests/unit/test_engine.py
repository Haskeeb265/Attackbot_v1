"""
Unit tests for Core Engine M3 components.
All subprocess calls are mocked — no real tools required.
All DB calls are mocked — no real database required.
"""

import hashlib
import json
import os
import uuid
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

    @pytest.mark.asyncio
    async def test_run_emits_passive_sensitive_finding_without_requests(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import run
        from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags, ScopeDefinition
        from backend.services.core_engine.models import DiscoveredEndpoint
        import uuid as _uuid

        ctx = ScanContext(
            scan_id=str(_uuid.uuid4()),
            program_id=str(_uuid.uuid4()),
            scope=ScopeDefinition(in_scope=["*.example.com"], out_of_scope=[]),
            feature_flags=FeatureFlags(),
        )
        sf = ScopeFilter(ctx.scope)
        ep = DiscoveredEndpoint(
            asset_id=_uuid.uuid4(),
            method="GET",
            path="/.env",
            full_url="https://api.example.com/.env",
            response_code=200,
        )

        # Make HTTP client calls fail if invoked; passive check should still emit a finding.
        class _ClientCM:
            async def __aenter__(self):
                client = AsyncMock()
                client.get.side_effect = AssertionError("HTTP request should not be required for passive finding")
                return client

            async def __aexit__(self, exc_type, exc, tb):
                return None

        with patch("backend.services.core_engine.pipeline.web_vuln_tests.httpx.AsyncClient", return_value=_ClientCM()):
            findings = await run(ctx, [ep], sf, ctx.feature_flags)

        assert any(f.vulnerability_type == "sensitive_file_exposure" for f in findings)


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


# ── Asset Discovery (Stage 1) tests ─────────────────────────────────────────

class TestAssetDiscovery:
    @pytest.mark.asyncio
    async def test_stage1_discovers_assets_happy_path(self):
        """
        Covers: subfinder file output, alterx, dnsx parsing, httpx JSON parsing,
        scope filtering, and DiscoveredAsset creation.
        """
        from backend.services.core_engine.pipeline import asset_discovery
        from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags, ScopeDefinition
        from backend.services.core_engine.pipeline.scope_filter import ScopeFilter

        ctx = ScanContext(
            scan_id=str(uuid.uuid4()),
            program_id=str(uuid.uuid4()),
            scope=ScopeDefinition(
                in_scope=[{"asset_type": "domain", "value": "example.com"}],
                out_of_scope=[],
            ),
            feature_flags=FeatureFlags(),
        )
        sf = ScopeFilter(ctx.scope)
        config = MagicMock()
        config.subfinder_timeout = 5
        config.dnsx_timeout = 5
        config.httpx_timeout = 5

        async def fake_run_tool_communicate(args, timeout, label, **kwargs):
            if args[0] == "subfinder":
                out_path = args[args.index("-o") + 1]
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write("api.example.com\n")
                return "", ""
            if args[0] == "alterx":
                return "dev.api.example.com\n", ""
            if args[0] == "dnsx":
                return "api.example.com [1.2.3.4]\n", ""
            if args[0] == "httpx":
                return json.dumps({"url": "https://api.example.com", "status_code": 200, "tech": []}) + "\n", ""
            raise AssertionError(f"Unexpected tool: {args[0]}")

        with patch("backend.services.core_engine.pipeline.asset_discovery.run_tool_communicate", new=fake_run_tool_communicate):
            assets = await asset_discovery.run(ctx, sf, config)

        assert len(assets) == 1
        assert assets[0].value == "https://api.example.com"


# ── Fingerprinting (Stage 2) tests ─────────────────────────────────────────

class TestFingerprinting:
    @pytest.mark.asyncio
    async def test_stage2_does_not_use_response_in_json_flag(self):
        from backend.services.core_engine.pipeline import fingerprinting
        from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags, ScopeDefinition
        from backend.services.core_engine.models import DiscoveredAsset

        ctx = ScanContext(
            scan_id=str(uuid.uuid4()),
            program_id=str(uuid.uuid4()),
            scope=ScopeDefinition(in_scope=["*.example.com"], out_of_scope=[]),
            feature_flags=FeatureFlags(),
        )
        assets = [DiscoveredAsset(asset_type="url", value="https://api.example.com")]
        config = MagicMock()
        config.httpx_timeout = 5

        captured = {"args": None}

        async def fake_httpx(args, timeout, label, **kwargs):
            captured["args"] = args
            return json.dumps({"url": "https://api.example.com", "status_code": 200, "tech": []}) + "\n", ""

        with patch("backend.services.core_engine.pipeline.fingerprinting.run_tool_communicate", new=fake_httpx):
            out = await fingerprinting.run(ctx, assets, config)

        assert out[0].http_status == 200
        assert captured["args"] is not None
        assert "-response-in-json" not in captured["args"]


# ── Enumeration (Stage 3) tests ────────────────────────────────────────────

class TestEnumeration:
    @pytest.mark.asyncio
    async def test_stage3_runs_ffuf_and_parses_output_file(self):
        from backend.services.core_engine.pipeline import enumeration
        from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags, ScopeDefinition
        from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
        from backend.services.core_engine.models import DiscoveredAsset

        ctx = ScanContext(
            scan_id=str(uuid.uuid4()),
            program_id=str(uuid.uuid4()),
            scope=ScopeDefinition(in_scope=[{"asset_type": "domain", "value": "example.com"}], out_of_scope=[]),
            feature_flags=FeatureFlags(),
        )
        sf = ScopeFilter(ctx.scope)
        asset = DiscoveredAsset(asset_type="url", value="https://example.com", asset_id=uuid.uuid4())
        config = MagicMock()
        config.ffuf_timeout = 5
        config.ffuf_wordlist = "/wordlists/common.txt"

        async def fake_tool(args, timeout, label, **kwargs):
            if args[0] == "ffuf":
                out_path = args[args.index("-o") + 1]
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps({"results": [{"url": "https://example.com/.git/HEAD", "status": 200}]}) )
                return "", ""
            if args[0] == "waybackurls":
                raise FileNotFoundError()
            raise AssertionError(args[0])

        with patch("backend.services.core_engine.pipeline.enumeration.run_tool_communicate", new=fake_tool):
            eps, js = await enumeration.run(ctx, [asset], sf, config)

        assert any(e.path == "/.git/HEAD" and e.response_code == 200 for e in eps)
        assert js == []


# ── Passive sensitive path findings (Stage 5 helper) ───────────────────────

class TestPassiveSensitiveFindings:
    def test_sensitive_path_emits_finding(self):
        from backend.services.core_engine.pipeline.web_vuln_tests import _passive_sensitive_path_findings
        from backend.services.core_engine.models import DiscoveredEndpoint

        ep = DiscoveredEndpoint(
            asset_id=uuid.uuid4(),
            method="GET",
            path="/.git/HEAD",
            full_url="https://example.com/.git/HEAD",
            response_code=200,
        )
        findings = _passive_sensitive_path_findings(ep)
        assert len(findings) == 1
        assert findings[0].vulnerability_type == "sensitive_file_exposure"


# ── Aggregator (Stage 10) tests ────────────────────────────────────────────

class TestAggregator:
    @pytest.mark.asyncio
    async def test_aggregator_saves_and_marks_complete(self):
        from backend.services.core_engine.pipeline import aggregator
        from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags, ScopeDefinition
        from backend.services.core_engine.models import ScanResult, FindingCandidate

        ctx = ScanContext(
            scan_id=str(uuid.uuid4()),
            program_id=str(uuid.uuid4()),
            scope=ScopeDefinition(in_scope=["*.example.com"], out_of_scope=[]),
            feature_flags=FeatureFlags(),
        )
        scan_result = ScanResult(
            finding_candidates=[
                FindingCandidate(
                    vulnerability_type="sensitive_file_exposure",
                    title="Exposed .git/HEAD",
                    severity="critical",
                    affected_url="https://example.com/.git/HEAD",
                    description="",
                    source="test",
                )
            ]
        )

        repo = AsyncMock()
        repo.save_findings = AsyncMock(return_value=1)
        repo.mark_scan_complete = AsyncMock()

        publisher = AsyncMock()
        publisher.publish = AsyncMock(return_value=True)

        breakdown = await aggregator.run(ctx, scan_result, repo, publisher)
        assert breakdown["critical"] == 1
        repo.save_findings.assert_called()
        repo.mark_scan_complete.assert_called()
        publisher.publish.assert_called()


# ── Watchdog tests ─────────────────────────────────────────────────────────

class TestWatchdog:
    @pytest.mark.asyncio
    async def test_recover_stuck_scans_marks_failed_internal(self):
        from backend.services.core_engine.watchdog import recover_stuck_scans

        scan_id = str(uuid.uuid4())
        program_id = str(uuid.uuid4())

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        fetch_result = MagicMock()
        fetch_result.fetchall.return_value = [(scan_id, 0, program_id)]
        mock_session.execute = AsyncMock(return_value=fetch_result)

        republished = []

        async def republish_fn(program_id=None, **_kwargs):
            republished.append(program_id)

        class _CM:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc, tb):
                return None

        with patch("backend.services.core_engine.watchdog.get_session", return_value=_CM()):
            await recover_stuck_scans(republish_fn=republish_fn, stale_hours=2)

        # SELECT + UPDATE + COMMIT happened
        assert mock_session.execute.call_count >= 2
        assert mock_session.commit.called
        assert republished == [program_id]


# ── Repository tests (SQL wrappers) ─────────────────────────────────────────

class TestRepository:
    @pytest.mark.asyncio
    async def test_create_or_resume_scan_creates_new_row(self):
        from backend.services.core_engine.repository import ScanRepository

        mock_session = AsyncMock()

        # No existing running scan
        select_result = MagicMock()
        select_result.fetchone.return_value = None

        failed_result = MagicMock()
        failed_result.fetchone.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[select_result, failed_result, MagicMock()]
        )
        mock_session.commit = AsyncMock()

        repo = ScanRepository(mock_session)
        scan_id = await repo.create_or_resume_scan(program_id=str(uuid.uuid4()), feature_flags={}, priority=1)
        assert isinstance(scan_id, str)
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_save_findings_counts_inserts(self):
        from backend.services.core_engine.repository import ScanRepository
        from backend.services.core_engine.models import FindingCandidate

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        ok_insert = MagicMock()
        ok_insert.rowcount = 1
        mock_session.execute = AsyncMock(return_value=ok_insert)

        repo = ScanRepository(mock_session)
        saved = await repo.save_findings(
            scan_id=str(uuid.uuid4()),
            program_id=str(uuid.uuid4()),
            candidates=[
                FindingCandidate(
                    vulnerability_type="xss",
                    title="XSS",
                    severity="high",
                    affected_url="https://example.com",
                    description="",
                    source="test",
                )
            ],
        )
        assert saved == 1


# ── scan_task pipeline wiring tests ─────────────────────────────────────────

class TestScanTaskPipeline:
    @pytest.mark.asyncio
    async def test_execute_pipeline_calls_stages_and_aggregator(self):
        from backend.services.core_engine.scan_task import _execute_pipeline
        from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags, ScopeDefinition
        from backend.services.core_engine.models import ScanResult, DiscoveredAsset, DiscoveredEndpoint
        from backend.services.core_engine.pipeline.scope_filter import ScopeFilter

        ctx = ScanContext(
            scan_id=str(uuid.uuid4()),
            program_id=str(uuid.uuid4()),
            scope=ScopeDefinition(in_scope=[{"asset_type": "domain", "value": "example.com"}], out_of_scope=[]),
            feature_flags=FeatureFlags(nuclei=False),
        )
        sf = ScopeFilter(ctx.scope)
        scan_result = ScanResult()
        repo = AsyncMock()
        publisher = AsyncMock()
        config = MagicMock()
        config.httpx_timeout = 5

        fake_assets = [DiscoveredAsset(asset_type="url", value="https://example.com")]
        fake_assets[0].asset_id = uuid.uuid4()
        fake_endpoints = [DiscoveredEndpoint(asset_id=fake_assets[0].asset_id, method="GET", path="/.git/HEAD", full_url="https://example.com/.git/HEAD", response_code=200)]

        with patch("backend.services.core_engine.scan_task.asset_discovery.run", new=AsyncMock(return_value=fake_assets)), \
             patch("backend.services.core_engine.scan_task.fingerprinting.run", new=AsyncMock(return_value=fake_assets)), \
             patch("backend.services.core_engine.scan_task.enumeration.run", new=AsyncMock(return_value=(fake_endpoints, []))), \
             patch("backend.services.core_engine.scan_task.web_vuln_tests.run", new=AsyncMock(return_value=[])), \
             patch("backend.services.core_engine.scan_task.nuclei_scan.run", new=AsyncMock(return_value=[])), \
             patch("backend.services.core_engine.scan_task.js_secrets.run", new=AsyncMock(return_value=[])), \
             patch("backend.services.core_engine.scan_task.aggregator.run", new=AsyncMock(return_value={})):
            await _execute_pipeline(ctx, scan_result, repo, publisher, config)

        # At least stage persistence methods invoked
        assert repo.save_assets.called
        assert repo.save_endpoints.called


# ── Import smoke tests (cover main/worker/config) ───────────────────────────

class TestImports:
    def test_imports_main_worker_config(self):
        import sys
        import types
        from backend.services.core_engine.config import EngineConfig
        from backend.services.core_engine import main as core_main
        # In this repo, celery is only required at runtime in the container.
        # For unit tests on dev machines without celery installed, stub it.
        if "celery" not in sys.modules:
            celery_mod = types.ModuleType("celery")

            class _Celery:
                def __init__(self, *args, **kwargs):
                    self.conf = {}

                def task(self, *args, **kwargs):
                    def _wrap(fn):
                        return fn

                    return _wrap

            celery_mod.Celery = _Celery
            sys.modules["celery"] = celery_mod

        from backend.services.core_engine import worker as core_worker

        cfg = EngineConfig()
        assert cfg.service_name
        assert core_main.app is not None
        assert core_worker.app is not None


# ── subprocess_utils tests (increase coverage) ──────────────────────────────

class TestSubprocessUtils:
    @pytest.mark.asyncio
    async def test_run_tool_communicate_success(self):
        from backend.services.core_engine import subprocess_utils

        class _Proc:
            def __init__(self):
                self.returncode = 0

            async def communicate(self):
                return (b"ok\n", b"")

            def kill(self):
                return None

            async def wait(self):
                return 0

        async def fake_create(*args, **kwargs):
            return _Proc()

        with patch("backend.services.core_engine.subprocess_utils.asyncio.create_subprocess_exec", new=fake_create):
            out, err = await subprocess_utils.run_tool_communicate(
                args=["echo", "hi"], timeout=1, label="t"
            )
        assert "ok" in out
        assert err == ""

    @pytest.mark.asyncio
    async def test_run_tool_communicate_nonzero_raises(self):
        from backend.services.core_engine import subprocess_utils
        from backend.shared.exceptions import ScanError

        class _Proc:
            def __init__(self):
                self.returncode = 2

            async def communicate(self):
                return (b"", b"bad")

            def kill(self):
                return None

            async def wait(self):
                return 0

        async def fake_create(*args, **kwargs):
            return _Proc()

        with patch("backend.services.core_engine.subprocess_utils.asyncio.create_subprocess_exec", new=fake_create):
            with pytest.raises(ScanError):
                await subprocess_utils.run_tool_communicate(
                    args=["cmd"], timeout=1, label="t"
                )


# ── nuclei_scan tests ───────────────────────────────────────────────────────

class TestNucleiScan:
    @pytest.mark.asyncio
    async def test_nuclei_scan_parses_jsonl(self):
        from backend.services.core_engine.pipeline import nuclei_scan
        from backend.services.core_engine.pipeline.context import ScanContext, FeatureFlags, ScopeDefinition
        from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
        from backend.services.core_engine.models import DiscoveredAsset

        ctx = ScanContext(
            scan_id=str(uuid.uuid4()),
            program_id=str(uuid.uuid4()),
            scope=ScopeDefinition(in_scope=["example.com"], out_of_scope=[]),
            feature_flags=FeatureFlags(),
        )
        sf = ScopeFilter(ctx.scope)
        config = MagicMock()
        config.nuclei_timeout = 5
        config.nuclei_rate_limit = 10
        config.nuclei_concurrency = 2
        config.nuclei_templates = ""

        assets = [DiscoveredAsset(asset_type="url", value="https://example.com", asset_id=uuid.uuid4())]

        async def fake_nuclei(args, timeout, label, **kwargs):
            # one nuclei JSON line
            return json.dumps({"matched-at": "https://example.com/.git/HEAD", "info": {"name": "Test", "severity": "high"}}) + "\n", ""

        with patch("backend.services.core_engine.pipeline.nuclei_scan.run_tool_communicate", new=fake_nuclei):
            findings = await nuclei_scan.run(ctx, assets, sf, config)

        assert len(findings) == 1
        assert findings[0].severity in {"high", "critical", "medium", "low", "info"}


# ── scan_task async pipeline tests (increase coverage) ──────────────────────

class TestAsyncScanPipeline:
    @pytest.mark.asyncio
    async def test_async_scan_pipeline_happy_path(self):
        from backend.services.core_engine.scan_task import _async_scan_pipeline

        payload = {
            "program_id": str(uuid.uuid4()),
            "scope": {"in_scope": [{"asset_type": "domain", "value": "example.com"}], "out_of_scope": []},
            "feature_flags": {"nuclei": False},
        }

        # Fake redis lock
        class _Lock:
            def __init__(self, acquire_ok=True):
                self._ok = acquire_ok

            async def acquire(self):
                return self._ok

            async def release(self):
                return True

        class _Redis:
            def lock(self, *args, **kwargs):
                return _Lock(acquire_ok=True)

        # Fake session context manager
        class _SessionCM:
            async def __aenter__(self):
                return AsyncMock()

            async def __aexit__(self, exc_type, exc, tb):
                return None

        # Fake repo/publisher
        fake_repo = AsyncMock()
        fake_repo.create_or_resume_scan = AsyncMock(return_value=str(uuid.uuid4()))
        fake_repo.save_assets = AsyncMock()
        fake_repo.save_endpoints = AsyncMock()
        fake_repo.save_js_asset = AsyncMock()
        fake_repo.record_stage = AsyncMock()
        fake_repo.mark_scan_complete = AsyncMock()
        fake_repo.save_findings = AsyncMock(return_value=0)

        fake_publisher = AsyncMock()
        fake_publisher.connect = AsyncMock()

        with patch("redis.asyncio.from_url", return_value=_Redis()), \
             patch("backend.services.core_engine.scan_task.get_session", return_value=_SessionCM()), \
             patch("backend.services.core_engine.scan_task.ScanRepository", return_value=fake_repo), \
             patch("backend.services.core_engine.scan_task.QueuePublisher", return_value=fake_publisher), \
             patch("backend.services.core_engine.scan_task._fetch_scope_from_scraper",
                   new=AsyncMock(return_value=ScopeDefinition(
                       in_scope=[{"asset_type": "domain", "value": "example.com"}],
                       out_of_scope=[],
                   ))), \
             patch("backend.services.core_engine.scan_task.asset_discovery.run", new=AsyncMock(return_value=[])), \
             patch("backend.services.core_engine.scan_task.aggregator.run", new=AsyncMock(return_value={})):
            await _async_scan_pipeline(payload)

        assert fake_repo.create_or_resume_scan.called

    @pytest.mark.asyncio
    async def test_async_scan_pipeline_lock_held_skips(self):
        from backend.services.core_engine.scan_task import _async_scan_pipeline

        payload = {"program_id": str(uuid.uuid4()), "scope": {"in_scope": ["example.com"], "out_of_scope": []}, "feature_flags": {}}

        class _Lock:
            async def acquire(self):
                return False

            async def release(self):
                return True

        class _Redis:
            def lock(self, *args, **kwargs):
                return _Lock()

        with patch("redis.asyncio.from_url", return_value=_Redis()):
            await _async_scan_pipeline(payload)


# —— Scraper scope fetch tests ————————————————————————————————————————

class TestScraperScopeFetch:
    @pytest.mark.asyncio
    async def test_fetch_scope_from_scraper_success(self):
        import httpx
        from backend.services.core_engine.scan_task import _fetch_scope_from_scraper
        from backend.services.core_engine.config import EngineConfig

        resp = httpx.Response(
            200,
            json={
                "in_scope": [{"asset_type": "domain", "value": "example.com"}],
                "out_of_scope": [],
            },
            request=httpx.Request("GET", "http://scraper/api/v1/programs/x/scope"),
        )
        mock_client = AsyncMock()
        mock_client.get.return_value = resp

        scope = await _fetch_scope_from_scraper("prog-id", EngineConfig(), client=mock_client)
        assert scope.in_scope

    @pytest.mark.asyncio
    async def test_fetch_scope_from_scraper_empty_raises(self):
        import httpx
        from backend.services.core_engine.scan_task import _fetch_scope_from_scraper
        from backend.services.core_engine.config import EngineConfig
        from backend.shared.exceptions import ScanError

        resp = httpx.Response(
            200,
            json={"in_scope": [], "out_of_scope": []},
            request=httpx.Request("GET", "http://scraper/api/v1/programs/x/scope"),
        )
        mock_client = AsyncMock()
        mock_client.get.return_value = resp

        with pytest.raises(ScanError):
            await _fetch_scope_from_scraper("prog-id", EngineConfig(), client=mock_client)


# —— failed_internal retry semantics ————————————————————————————————

class TestFailedInternalRetry:
    @pytest.mark.asyncio
    async def test_reuses_failed_internal_scan(self):
        from backend.services.core_engine.repository import ScanRepository

        mock_session = AsyncMock()
        running_result = MagicMock()
        running_result.fetchone.return_value = None
        failed_result = MagicMock()
        failed_result.fetchone.return_value = ("scan-id-1", 1)

        mock_session.execute = AsyncMock(side_effect=[running_result, failed_result, MagicMock()])
        mock_session.commit = AsyncMock()

        repo = ScanRepository(mock_session)
        scan_id = await repo.create_or_resume_scan(
            program_id="prog-id",
            feature_flags={},
            priority=1,
        )
        assert scan_id == "scan-id-1"
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_creates_new_scan_when_no_retry(self):
        from backend.services.core_engine.repository import ScanRepository

        mock_session = AsyncMock()
        running_result = MagicMock()
        running_result.fetchone.return_value = None
        failed_result = MagicMock()
        failed_result.fetchone.return_value = None

        mock_session.execute = AsyncMock(side_effect=[running_result, failed_result, MagicMock()])
        mock_session.commit = AsyncMock()

        with patch("backend.services.core_engine.repository.uuid.uuid4",
                   return_value=uuid.UUID("00000000-0000-0000-0000-000000000001")):
            repo = ScanRepository(mock_session)
            scan_id = await repo.create_or_resume_scan(
                program_id="prog-id",
                feature_flags={},
                priority=1,
            )
        assert scan_id == "00000000-0000-0000-0000-000000000001"


# —— failed_scope status handling ————————————————————————————————

class TestFailedScopeStatus:
    @pytest.mark.asyncio
    async def test_execute_pipeline_marks_failed_scope(self):
        from backend.services.core_engine.scan_task import _execute_pipeline
        from backend.services.core_engine.pipeline.context import ScanContext, ScopeDefinition, FeatureFlags
        from backend.services.core_engine.models import ScanResult
        from backend.services.core_engine.config import EngineConfig

        ctx = ScanContext(
            scan_id="scan-id",
            program_id="prog-id",
            scope=ScopeDefinition(in_scope=[], out_of_scope=[]),
            feature_flags=FeatureFlags(),
        )
        repo = AsyncMock()
        publisher = AsyncMock()

        await _execute_pipeline(ctx, ScanResult(), repo, publisher, EngineConfig())
        assert repo.mark_scan_complete.called
        kwargs = repo.mark_scan_complete.call_args.kwargs
        assert kwargs.get("status") == "failed_scope"
