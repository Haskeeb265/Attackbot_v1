"""
Unit tests for M2 — Scraper service.

All external I/O is mocked:
  - No real HackerOne API calls
  - No real DB connections
  - No real RabbitMQ

Coverage target: ≥ 80% for backend/services/scraper + backend/shared/exceptions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

from backend.services.scraper.models import Program, ProgramScope, RawProgram
from backend.services.scraper.collectors.hackerone import HackerOneCollector, ASSET_TYPE_MAP
from backend.services.scraper.scope_parser import ScopeParser
from backend.shared.exceptions import CollectorRateLimitError, CollectorAuthError


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_h1_scope_entry(asset_type: str, value: str, eligible: bool = True) -> dict:
    return {
        "attributes": {
            "asset_type": asset_type,
            "asset_identifier": value,
            "eligible_for_submission": eligible,
            "eligible_for_bounty": eligible,
            "instruction": None,
        }
    }


def make_h1_program(handle: str = "test-program", offers_bounties: bool = True) -> dict:
    return {
        "data": {
            "attributes": {
                "handle": handle,
                "name": "Test Program",
                "url": f"https://hackerone.com/{handle}",
                "offers_bounties": offers_bounties,
                "ended": False,
                "safe_harbor": "yes",
                "disclosure_policy": "90 days",
                "maximum_bounty": 5000,
            }
        },
        "_scopes": [
            make_h1_scope_entry("URL", "https://example.com/api/"),
            make_h1_scope_entry("WILDCARD", "*.example.com"),
            make_h1_scope_entry("CIDR", "10.0.0.0/8"),
            make_h1_scope_entry("ANDROID", "com.example.app"),
            make_h1_scope_entry("URL", "https://admin.example.com", eligible=False),
        ],
    }


# ---------------------------------------------------------------------------
# HackerOne Collector — normalization
# ---------------------------------------------------------------------------

class TestHackerOneCollectorNormalize:

    def setup_method(self):
        self.collector = HackerOneCollector("user", "token")

    def test_normalize_produces_program(self):
        raw = RawProgram("hackerone", make_h1_program(), "test-program", "2026-01-01T00:00:00Z")
        program = self.collector.normalize(raw)
        assert isinstance(program, Program)
        assert program.handle == "test-program"
        assert program.platform == "hackerone"

    def test_normalize_bounty_type_bug_bounty(self):
        raw = RawProgram("hackerone", make_h1_program(offers_bounties=True), "h", "now")
        program = self.collector.normalize(raw)
        assert program.bounty_type == "bug_bounty"

    def test_normalize_bounty_type_vdp(self):
        raw = RawProgram("hackerone", make_h1_program(offers_bounties=False), "h", "now")
        program = self.collector.normalize(raw)
        assert program.bounty_type == "vdp"

    def test_normalize_scopes_count(self):
        raw = RawProgram("hackerone", make_h1_program(), "h", "now")
        program = self.collector.normalize(raw)
        # 4 eligible (in_scope) + 1 ineligible (out_of_scope) = 5 total
        assert len(program.scopes) == 5

    def test_normalize_ineligible_scope_is_out_of_scope(self):
        raw = RawProgram("hackerone", make_h1_program(), "h", "now")
        program = self.collector.normalize(raw)
        out_of_scope = [s for s in program.scopes if s.scope_type == "out_of_scope"]
        assert len(out_of_scope) == 1
        assert out_of_scope[0].value == "https://admin.example.com"

    def test_normalize_wildcard_asset_type(self):
        raw = RawProgram("hackerone", make_h1_program(), "h", "now")
        program = self.collector.normalize(raw)
        wildcard = next(s for s in program.scopes if "*.example.com" in s.value)
        assert wildcard.asset_type == "wildcard_domain"

    def test_normalize_cidr_asset_type(self):
        raw = RawProgram("hackerone", make_h1_program(), "h", "now")
        program = self.collector.normalize(raw)
        cidr = next(s for s in program.scopes if "10.0.0.0" in s.value)
        assert cidr.asset_type == "ip_range"

    def test_normalize_android_asset_type(self):
        raw = RawProgram("hackerone", make_h1_program(), "h", "now")
        program = self.collector.normalize(raw)
        mobile = next(s for s in program.scopes if "com.example.app" in s.value)
        assert mobile.asset_type == "mobile_app"

    def test_normalize_handles_missing_maximum_bounty(self):
        data = make_h1_program()
        data["data"]["attributes"].pop("maximum_bounty")
        raw = RawProgram("hackerone", data, "h", "now")
        program = self.collector.normalize(raw)
        assert program.max_bounty is None

    def test_normalize_handles_empty_scopes(self):
        data = make_h1_program()
        data["_scopes"] = []
        raw = RawProgram("hackerone", data, "h", "now")
        program = self.collector.normalize(raw)
        assert program.scopes == []

    def test_normalize_handles_none_scopes(self):
        data = make_h1_program()
        data["_scopes"] = None
        raw = RawProgram("hackerone", data, "h", "now")
        program = self.collector.normalize(raw)
        assert program.scopes == []

    def test_normalize_safe_harbor_yes(self):
        raw = RawProgram("hackerone", make_h1_program(), "h", "now")
        program = self.collector.normalize(raw)
        assert program.policy.safe_harbor is True

    def test_normalize_safe_harbor_no(self):
        data = make_h1_program()
        data["data"]["attributes"]["safe_harbor"] = "no"
        raw = RawProgram("hackerone", data, "h", "now")
        program = self.collector.normalize(raw)
        assert program.policy.safe_harbor is False

    def test_normalize_url_fallback(self):
        data = make_h1_program()
        data["data"]["attributes"].pop("url", None)
        raw = RawProgram("hackerone", data, "test-h", "now")
        program = self.collector.normalize(raw)
        assert program.url == "https://hackerone.com/test-h"

    def test_normalize_ended_program_is_inactive(self):
        data = make_h1_program()
        data["data"]["attributes"]["ended"] = True
        raw = RawProgram("hackerone", data, "h", "now")
        program = self.collector.normalize(raw)
        assert program.is_active is False

    def test_normalize_skips_blank_scope_identifiers(self):
        data = make_h1_program()
        data["_scopes"].append(make_h1_scope_entry("URL", ""))
        raw = RawProgram("hackerone", data, "h", "now")
        program = self.collector.normalize(raw)
        # blank entry should be skipped
        assert all(s.value != "" for s in program.scopes)


# ---------------------------------------------------------------------------
# HackerOne Collector — 429 retry and HTTP error handling
# ---------------------------------------------------------------------------

class TestHackerOneRetry:

    def test_retries_on_429_then_succeeds(self):
        collector = HackerOneCollector("u", "t", max_retries=3)
        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            if call_count < 3:
                resp.status_code = 429
                resp.headers = {"Retry-After": "0"}
                return resp
            resp.status_code = 200
            resp.json.return_value = {"data": []}
            resp.raise_for_status = MagicMock()
            return resp

        with patch("requests.get", side_effect=mock_get):
            with patch("time.sleep"):
                result = collector._get("https://api.hackerone.com/v1/test")
        assert call_count == 3

    def test_raises_after_max_retries(self):
        collector = HackerOneCollector("u", "t", max_retries=2)

        def always_429(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 429
            resp.headers = {"Retry-After": "0"}
            return resp

        with patch("requests.get", side_effect=always_429):
            with patch("time.sleep"):
                with pytest.raises(CollectorRateLimitError):
                    collector._get("https://api.hackerone.com/v1/test")

    def test_raises_collector_auth_error_on_401(self):
        collector = HackerOneCollector("u", "t")

        def return_401(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 401
            return resp

        with patch("requests.get", side_effect=return_401):
            with pytest.raises(CollectorAuthError):
                collector._get("https://api.hackerone.com/v1/test")

    def test_raises_collector_auth_error_on_403(self):
        collector = HackerOneCollector("u", "t")

        def return_403(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 403
            return resp

        with patch("requests.get", side_effect=return_403):
            with pytest.raises(CollectorAuthError):
                collector._get("https://api.hackerone.com/v1/test")

    def test_retries_on_request_exception(self):
        import requests as req_lib
        collector = HackerOneCollector("u", "t", max_retries=3)
        call_count = 0

        def flaky_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise req_lib.ConnectionError("connection refused")
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"data": []}
            resp.raise_for_status = MagicMock()
            return resp

        with patch("requests.get", side_effect=flaky_request):
            with patch("time.sleep"):
                result = collector._get("https://api.hackerone.com/v1/test")
        assert call_count == 3

    def test_pagination_stops_on_empty_data(self):
        collector = HackerOneCollector("u", "t")
        responses = [
            {"data": [{"id": "1"}, {"id": "2"}]},
            {"data": [{"id": "3"}]},
            {"data": []},
        ]
        call_count = 0

        def mock_get_json(*args, **kwargs):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        with patch.object(collector, "_get", side_effect=mock_get_json):
            results = collector._paginate("https://api.hackerone.com/v1/programs")

        assert len(results) == 3
        assert call_count == 3  # stopped after empty page

    def test_pagination_stops_on_none_data(self):
        """HackerOne quirk: data field can be None on empty pages."""
        collector = HackerOneCollector("u", "t")
        responses = [
            {"data": [{"id": "1"}]},
            {"data": None},
        ]
        call_count = 0

        def mock_get_json(*args, **kwargs):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        with patch.object(collector, "_get", side_effect=mock_get_json):
            results = collector._paginate("https://api.hackerone.com/v1/programs")

        assert len(results) == 1  # only the first page
        assert call_count == 2

    def test_retry_after_header_is_respected(self):
        collector = HackerOneCollector("u", "t", max_retries=3)
        sleep_calls = []
        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            if call_count == 1:
                resp.status_code = 429
                resp.headers = {"Retry-After": "42"}
                return resp
            resp.status_code = 200
            resp.json.return_value = {"data": []}
            resp.raise_for_status = MagicMock()
            return resp

        with patch("requests.get", side_effect=mock_get):
            with patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
                collector._get("https://api.hackerone.com/v1/test")

        assert 42 in sleep_calls


# ---------------------------------------------------------------------------
# Collector registry
# ---------------------------------------------------------------------------

class TestCollectorRegistry:

    def test_hackerone_is_registered(self):
        from backend.services.scraper.collectors.base import CollectorRegistry
        assert "hackerone" in CollectorRegistry.all_platforms()

    def test_get_unknown_platform_raises(self):
        from backend.services.scraper.collectors.base import CollectorRegistry
        with pytest.raises(ValueError, match="No collector registered"):
            CollectorRegistry.get("unknown_platform_xyz")

    def test_register_and_retrieve(self):
        from backend.services.scraper.collectors.base import CollectorRegistry, BaseCollector

        class FakeCollector(BaseCollector):
            def fetch_listing(self): return []
            def fetch_details(self, handle): return None
            def normalize(self, raw): return None

        CollectorRegistry.register("fake_test", FakeCollector)
        assert CollectorRegistry.get("fake_test") is FakeCollector
        # Cleanup
        del CollectorRegistry._registry["fake_test"]


# ---------------------------------------------------------------------------
# Scope Parser
# ---------------------------------------------------------------------------

class TestScopeParser:

    def setup_method(self):
        self.parser = ScopeParser()

    def test_wildcard_domain_preserved(self):
        scope = ProgramScope("in_scope", "wildcard_domain", "*.example.com")
        result = self.parser.parse([scope])
        assert len(result) == 1
        assert result[0].asset_type == "wildcard_domain"

    def test_url_preserved(self):
        scope = ProgramScope("in_scope", "url", "https://example.com/api/")
        result = self.parser.parse([scope])
        assert result[0].asset_type == "url"

    def test_cidr_preserved(self):
        scope = ProgramScope("in_scope", "ip_range", "10.0.0.0/8")
        result = self.parser.parse([scope])
        assert result[0].asset_type == "ip_range"

    def test_mobile_bundle_id_preserved(self):
        scope = ProgramScope("in_scope", "mobile_app", "com.example.myapp")
        result = self.parser.parse([scope])
        assert result[0].asset_type == "mobile_app"

    def test_empty_value_dropped(self):
        scope = ProgramScope("in_scope", "url", "   ")
        result = self.parser.parse([scope])
        assert result == []

    def test_out_of_scope_type_preserved(self):
        scope = ProgramScope("out_of_scope", "url", "https://admin.example.com")
        result = self.parser.parse([scope])
        assert result[0].scope_type == "out_of_scope"

    def test_mismatched_asset_type_corrected(self):
        # Value is a wildcard but collector said "url" — parser must correct this
        scope = ProgramScope("in_scope", "url", "*.example.com")
        result = self.parser.parse([scope])
        assert result[0].asset_type == "wildcard_domain"

    def test_infer_cidr_from_value(self):
        assert self.parser._infer_asset_type("192.168.1.0/24") == "ip_range"

    def test_infer_ipv6_cidr(self):
        assert self.parser._infer_asset_type("2001:db8::/32") == "ip_range"

    def test_infer_wildcard_from_value(self):
        assert self.parser._infer_asset_type("*.example.com") == "wildcard_domain"

    def test_infer_url_from_value(self):
        assert self.parser._infer_asset_type("https://example.com") == "url"

    def test_infer_http_url(self):
        assert self.parser._infer_asset_type("http://example.com") == "url"

    def test_infer_domain_from_value(self):
        assert self.parser._infer_asset_type("example.com") == "domain"

    def test_mixed_scope_list(self):
        scopes = [
            ProgramScope("in_scope", "wildcard_domain", "*.example.com"),
            ProgramScope("in_scope", "url", "https://api.example.com"),
            ProgramScope("out_of_scope", "url", "https://admin.example.com"),
            ProgramScope("in_scope", "url", ""),  # should be dropped
        ]
        result = self.parser.parse(scopes)
        assert len(result) == 3
        assert sum(1 for s in result if s.scope_type == "in_scope") == 2
        assert sum(1 for s in result if s.scope_type == "out_of_scope") == 1

    def test_whitespace_trimmed(self):
        scope = ProgramScope("in_scope", "url", "  https://example.com  ")
        result = self.parser.parse([scope])
        assert result[0].value == "https://example.com"


# ---------------------------------------------------------------------------
# Publisher — failure path
# ---------------------------------------------------------------------------

class TestScraperPublisher:

    @pytest.mark.asyncio
    async def test_publish_failure_marks_queued(self):
        from backend.services.scraper.publisher import ScraperPublisher

        mock_repo = AsyncMock()
        mock_task_dispatcher = Mock()
        mock_task_dispatcher.send_task.side_effect = RuntimeError("publish_failed")

        publisher = ScraperPublisher.__new__(ScraperPublisher)
        publisher._task_dispatcher = mock_task_dispatcher
        publisher._repository = mock_repo

        program = Program(
            platform="hackerone",
            handle="test",
            name="Test",
            scopes=[ProgramScope("in_scope", "domain", "example.com")],
        )
        result = await publisher.publish_scan_job(uuid4(), program)

        assert result is False
        mock_repo.mark_queued.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_success_does_not_mark_queued(self):
        from backend.services.scraper.publisher import ScraperPublisher

        mock_repo = AsyncMock()
        mock_task_dispatcher = Mock()
        mock_task_dispatcher.send_task.return_value = Mock()

        publisher = ScraperPublisher.__new__(ScraperPublisher)
        publisher._task_dispatcher = mock_task_dispatcher
        publisher._repository = mock_repo

        program = Program(
            platform="hackerone",
            handle="test",
            name="Test",
            scopes=[ProgramScope("in_scope", "domain", "example.com")],
        )
        result = await publisher.publish_scan_job(uuid4(), program)

        assert result is True
        mock_repo.mark_queued.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_skipped_when_no_in_scope_entries(self):
        from backend.services.scraper.publisher import ScraperPublisher

        mock_repo = AsyncMock()
        mock_task_dispatcher = Mock()

        publisher = ScraperPublisher.__new__(ScraperPublisher)
        publisher._task_dispatcher = mock_task_dispatcher
        publisher._repository = mock_repo

        program = Program(
            platform="hackerone",
            handle="test",
            name="Test",
            scopes=[],  # no in-scope entries
        )
        result = await publisher.publish_scan_job(uuid4(), program)

        assert result is False
        mock_task_dispatcher.send_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_skipped_only_out_of_scope(self):
        from backend.services.scraper.publisher import ScraperPublisher

        mock_repo = AsyncMock()
        mock_task_dispatcher = Mock()

        publisher = ScraperPublisher.__new__(ScraperPublisher)
        publisher._task_dispatcher = mock_task_dispatcher
        publisher._repository = mock_repo

        program = Program(
            platform="hackerone",
            handle="test",
            name="Test",
            scopes=[ProgramScope("out_of_scope", "domain", "example.com")],
        )
        result = await publisher.publish_scan_job(uuid4(), program)

        assert result is False
        mock_task_dispatcher.send_task.assert_not_called()


# ---------------------------------------------------------------------------
# Reconciler
# ---------------------------------------------------------------------------

class TestReconciler:

    @pytest.mark.asyncio
    async def test_reconciler_clears_flag_on_success(self):
        from backend.services.scraper.reconciler import Reconciler

        program_id = uuid4()
        mock_repo = AsyncMock()
        mock_repo.get_queued_programs.return_value = [{
            "program_id": program_id,
            "handle": "test",
            "platform": "hackerone",
            "name": "Test",
        }]
        mock_repo.get_scope.return_value = [
            {
                "scope_type": "in_scope",
                "asset_type": "domain",
                "value": "example.com",
                "notes": None,
            }
        ]

        mock_publisher = AsyncMock()
        mock_publisher.publish_scan_job.return_value = True

        reconciler = Reconciler(mock_repo, mock_publisher)
        result = await reconciler.reconcile()

        assert result["published"] == 1
        assert result["failed"] == 0
        mock_repo.clear_queued.assert_called_once_with(program_id)

    @pytest.mark.asyncio
    async def test_reconciler_leaves_flag_on_failure(self):
        from backend.services.scraper.reconciler import Reconciler

        mock_repo = AsyncMock()
        mock_repo.get_queued_programs.return_value = [{
            "program_id": uuid4(),
            "handle": "test",
            "platform": "hackerone",
            "name": "Test",
        }]
        mock_repo.get_scope.return_value = [
            {
                "scope_type": "in_scope",
                "asset_type": "domain",
                "value": "example.com",
                "notes": None,
            }
        ]

        mock_publisher = AsyncMock()
        mock_publisher.publish_scan_job.return_value = False  # publish fails

        reconciler = Reconciler(mock_repo, mock_publisher)
        result = await reconciler.reconcile()

        assert result["published"] == 0
        assert result["failed"] == 1
        mock_repo.clear_queued.assert_not_called()

    @pytest.mark.asyncio
    async def test_reconciler_no_queued_programs(self):
        from backend.services.scraper.reconciler import Reconciler

        mock_repo = AsyncMock()
        mock_repo.get_queued_programs.return_value = []
        mock_publisher = AsyncMock()

        reconciler = Reconciler(mock_repo, mock_publisher)
        result = await reconciler.reconcile()

        assert result == {"checked": 0, "published": 0, "failed": 0}
        mock_publisher.publish_scan_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_reconciler_multiple_programs_mixed_results(self):
        from backend.services.scraper.reconciler import Reconciler

        id_success = uuid4()
        id_fail = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get_queued_programs.return_value = [
            {"program_id": id_success, "handle": "ok-prog", "platform": "hackerone", "name": "OK"},
            {"program_id": id_fail, "handle": "fail-prog", "platform": "hackerone", "name": "Fail"},
        ]
        mock_repo.get_scope.return_value = [
            {"scope_type": "in_scope", "asset_type": "domain", "value": "x.com", "notes": None}
        ]

        results_iter = iter([True, False])
        mock_publisher = AsyncMock()
        mock_publisher.publish_scan_job.side_effect = lambda pid, prog: next(results_iter)

        reconciler = Reconciler(mock_repo, mock_publisher)
        result = await reconciler.reconcile()

        assert result["checked"] == 2
        assert result["published"] == 1
        assert result["failed"] == 1


# ---------------------------------------------------------------------------
# Asset type map coverage
# ---------------------------------------------------------------------------

class TestAssetTypeMap:

    def test_all_known_h1_types_are_mapped(self):
        known_types = [
            "URL", "WILDCARD", "DOMAIN", "IP_ADDRESS", "CIDR",
            "ANDROID", "IOS", "OTHER_IPA", "OTHER_APK",
            "API", "SOURCE_CODE", "HARDWARE", "OTHER",
        ]
        for t in known_types:
            assert t in ASSET_TYPE_MAP, f"Missing mapping for {t}"

    def test_unknown_type_falls_back_gracefully(self):
        collector = HackerOneCollector("u", "t")
        data = make_h1_program()
        data["_scopes"] = [make_h1_scope_entry("UNKNOWN_FUTURE_TYPE", "something.com")]
        raw = RawProgram("hackerone", data, "h", "now")
        # normalize() must not raise — unknown type gets fallback
        program = collector.normalize(raw)
        assert len(program.scopes) == 1
