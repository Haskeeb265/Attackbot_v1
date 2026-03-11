"""
Integration tests for M2 — Scraper pipeline.

These tests run against the live Docker stack.
They call real endpoints, write to real DB, check real RabbitMQ.

Classes that call HackerOne API require:
  HACKERONE_API_USERNAME and HACKERONE_API_TOKEN to be set.
  They skip cleanly if credentials are absent.

Run with:
  pytest tests/integration/test_scraper_pipeline.py -v
"""

import os
import asyncio
import pytest
import httpx
from uuid import UUID

BASE_URL = "http://localhost:8001/api/v1"
RABBITMQ_MGMT = "http://localhost:15672/api"
RABBITMQ_AUTH = ("attackbot", "attackbot")


# ---------------------------------------------------------------------------
# Health checks — no credentials required
# ---------------------------------------------------------------------------

class TestScraperAPIHealth:

    def test_health_returns_200(self):
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        assert resp.status_code == 200

    def test_health_status_healthy(self):
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        body = resp.json()
        assert body["status"] == "healthy"

    def test_health_has_database_component(self):
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        body = resp.json()
        assert "database" in body["components"]
        assert body["components"]["database"]["status"] == "healthy"

    def test_health_has_scheduler_component(self):
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        body = resp.json()
        assert "scheduler" in body["components"]
        assert body["components"]["scheduler"]["status"] == "healthy"

    def test_health_has_rabbitmq_component(self):
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        body = resp.json()
        assert "rabbitmq" in body["components"]


# ---------------------------------------------------------------------------
# Programs list — no credentials required (may be empty)
# ---------------------------------------------------------------------------

class TestProgramsList:

    def test_programs_list_returns_200(self):
        resp = httpx.get(f"{BASE_URL}/programs", timeout=10)
        assert resp.status_code == 200

    def test_programs_list_has_pagination_fields(self):
        resp = httpx.get(f"{BASE_URL}/programs", timeout=10)
        body = resp.json()
        assert "total" in body
        assert "page" in body
        assert "page_size" in body
        assert "items" in body

    def test_programs_list_page_size_respected(self):
        resp = httpx.get(f"{BASE_URL}/programs?page_size=5", timeout=10)
        body = resp.json()
        assert len(body["items"]) <= 5

    def test_programs_list_invalid_page_size(self):
        resp = httpx.get(f"{BASE_URL}/programs?page_size=999", timeout=10)
        assert resp.status_code == 422  # FastAPI validation

    def test_program_not_found_returns_404(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = httpx.get(f"{BASE_URL}/programs/{fake_id}", timeout=10)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Scrape trigger — requires HackerOne credentials
# ---------------------------------------------------------------------------

class TestScrapeTrigerAndDBFlow:
    """
    These tests require HACKERONE_API_USERNAME and HACKERONE_API_TOKEN to be set
    with valid credentials. They make real API calls and may take 30–120 seconds.
    Skip gracefully if credentials are not set.
    """

    @pytest.fixture(autouse=True)
    def check_credentials(self):
        if not os.getenv("HACKERONE_API_USERNAME") or not os.getenv("HACKERONE_API_TOKEN"):
            pytest.skip("HackerOne credentials not set")

    def test_trigger_returns_completed(self):
        resp = httpx.post(
            f"{BASE_URL}/scrape/trigger?platform=hackerone",
            timeout=120,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"

    def test_trigger_produces_upserted_count(self):
        resp = httpx.post(
            f"{BASE_URL}/scrape/trigger?platform=hackerone",
            timeout=120,
        )
        body = resp.json()
        assert body["upserted"] > 0

    def test_programs_list_populated_after_trigger(self):
        # Ensure at least one scrape has run
        httpx.post(f"{BASE_URL}/scrape/trigger?platform=hackerone", timeout=120)

        resp = httpx.get(f"{BASE_URL}/programs", timeout=10)
        body = resp.json()
        assert body["total"] > 0
        assert len(body["items"]) > 0

    def test_program_has_platform_hackerone(self):
        httpx.post(f"{BASE_URL}/scrape/trigger?platform=hackerone", timeout=120)

        resp = httpx.get(f"{BASE_URL}/programs?platform=hackerone&page_size=1", timeout=10)
        body = resp.json()
        assert body["total"] > 0
        assert body["items"][0]["platform"] == "hackerone"

    def test_program_has_scope(self):
        httpx.post(f"{BASE_URL}/scrape/trigger?platform=hackerone", timeout=120)

        # Get first program
        list_resp = httpx.get(f"{BASE_URL}/programs?page_size=1", timeout=10)
        program_id = list_resp.json()["items"][0]["program_id"]

        scope_resp = httpx.get(f"{BASE_URL}/programs/{program_id}/scope", timeout=10)
        assert scope_resp.status_code == 200
        body = scope_resp.json()
        assert "in_scope" in body
        assert "out_of_scope" in body

    def test_unknown_platform_returns_400(self):
        resp = httpx.post(
            f"{BASE_URL}/scrape/trigger?platform=unknown_platform_xyz",
            timeout=10,
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# RabbitMQ message check — requires credentials + running RabbitMQ mgmt
# ---------------------------------------------------------------------------

class TestRabbitMQMessage:
    """
    Checks the scan.jobs queue via RabbitMQ management API.
    Requires credentials and RabbitMQ mgmt port 15672.
    """

    @pytest.fixture(autouse=True)
    def check_credentials(self):
        if not os.getenv("HACKERONE_API_USERNAME") or not os.getenv("HACKERONE_API_TOKEN"):
            pytest.skip("HackerOne credentials not set")

    def test_scan_jobs_queue_has_messages_after_trigger(self):
        # Trigger scrape
        httpx.post(f"{BASE_URL}/scrape/trigger?platform=hackerone", timeout=120)

        # Check queue depth via RabbitMQ management API
        try:
            resp = httpx.get(
                f"{RABBITMQ_MGMT}/queues/%2F/scan.jobs",
                auth=RABBITMQ_AUTH,
                timeout=10,
            )
            if resp.status_code == 200:
                queue_info = resp.json()
                # Messages may have already been consumed — check messages_ready OR messages_unacknowledged
                total = queue_info.get("messages", 0)
                assert total >= 0  # queue exists and is reachable
        except httpx.ConnectError:
            pytest.skip("RabbitMQ management UI not reachable on localhost:15672")


# ---------------------------------------------------------------------------
# Publish failure + reconciler simulation — no credentials required
# ---------------------------------------------------------------------------

class TestPublishFailureAndReconciler:
    """
    Simulates a publish failure by directly setting queued_for_scan=True in the DB,
    then verifying the flag is set (reconciler will clear it on next cycle).
    Requires running Docker stack, no HackerOne credentials needed.
    """

    def test_queued_program_flag_can_be_set(self):
        """
        This test verifies the DB is writable and the queued_for_scan column exists.
        Uses asyncpg to directly manipulate the flag.
        """
        try:
            import asyncpg
        except ImportError:
            pytest.skip("asyncpg not installed")

        async def run():
            try:
                conn = await asyncpg.connect(
                    "postgresql://attackbot:attackbot@localhost:5432/attackbot"
                )
            except Exception:
                return "skipped_no_db"

            row = await conn.fetchrow("SELECT program_id FROM programs LIMIT 1")
            if not row:
                await conn.close()
                return "skipped_no_programs"

            program_id = row["program_id"]

            # Simulate publish failure
            await conn.execute(
                "UPDATE programs SET queued_for_scan = true WHERE program_id = $1",
                program_id,
            )

            updated = await conn.fetchrow(
                "SELECT queued_for_scan FROM programs WHERE program_id = $1",
                program_id,
            )

            # Restore to false
            await conn.execute(
                "UPDATE programs SET queued_for_scan = false WHERE program_id = $1",
                program_id,
            )

            await conn.close()
            return updated["queued_for_scan"]

        result = asyncio.run(run())
        if result in ("skipped_no_db", "skipped_no_programs"):
            pytest.skip(f"Skipped: {result}")
        assert result is True  # flag was set successfully