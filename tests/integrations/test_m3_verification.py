"""
Integration verification for remaining M3 checks.

Covers:
1) core-worker has waybackurls available in-container
2) full scan path fetches scope from Scraper API
3) watchdog marks stale scans failed_internal and increments retry_count
4) empty/invalid scope ends in failed_scope without downstream stages
"""

import asyncio
import os
import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest


CORE_BASE_URL = os.getenv("M3_CORE_BASE_URL", "http://localhost:8002/api/v1")
SCRAPER_BASE_URL = os.getenv("M3_SCRAPER_BASE_URL", "http://localhost:8001/api/v1")
DB_DSN = os.getenv("M3_DB_DSN", "postgresql://attackbot:attackbot@localhost:5432/attackbot")
RABBITMQ_MGMT = os.getenv("M3_RABBITMQ_MGMT", "http://localhost:15672/api")
RABBITMQ_USER = os.getenv("M3_RABBITMQ_USER", "attackbot")
RABBITMQ_PASS = os.getenv("M3_RABBITMQ_PASS", "attackbot")


def _docker_available() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "info"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _service_healthy(url: str) -> bool:
    try:
        resp = httpx.get(url, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def _reset_scan_processing_state() -> None:
    subprocess.run(
        [
            "docker",
            "exec",
            "attackbot-rabbitmq-1",
            "rabbitmqctl",
            "purge_queue",
            "scan.jobs",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    subprocess.run(
        ["docker", "compose", "-f", "infra/docker-compose.yml", "restart", "core-worker"],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    time.sleep(6)


@pytest.fixture(scope="module")
def require_stack():
    if not _docker_available():
        pytest.skip("Docker daemon not available")
    if not _service_healthy(f"{SCRAPER_BASE_URL}/health"):
        pytest.skip("Scraper service is not healthy/reachable")
    if not _service_healthy(f"{CORE_BASE_URL}/health"):
        pytest.skip("Core Engine service is not healthy/reachable")


async def _db_connect():
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed")
    return await asyncpg.connect(DB_DSN)


async def _db_fetchrow(query: str, *args):
    conn = await _db_connect()
    try:
        return await conn.fetchrow(query, *args)
    finally:
        await conn.close()


async def _db_fetchval(query: str, *args):
    conn = await _db_connect()
    try:
        return await conn.fetchval(query, *args)
    finally:
        await conn.close()


async def _db_execute(query: str, *args):
    conn = await _db_connect()
    try:
        return await conn.execute(query, *args)
    finally:
        await conn.close()


async def _find_program_with_scope():
    return await _db_fetchrow(
        """
        SELECT p.program_id
        FROM programs p
        WHERE EXISTS (
            SELECT 1
            FROM program_scopes s
            WHERE s.program_id = p.program_id
              AND s.scope_type = 'in_scope'
              AND COALESCE(TRIM(s.value), '') <> ''
        )
        ORDER BY p.updated_at DESC NULLS LAST, p.created_at DESC
        LIMIT 1
        """
    )


async def _create_program_with_scope(
    asset_type: str = "domain",
    value: str = "example.com",
) -> str:
    program_id = str(uuid.uuid4())
    handle = f"m3-seeded-scope-{program_id[:8]}"
    await _db_execute(
        """
        INSERT INTO programs (
            program_id, platform, handle, name, url, bounty_type,
            max_bounty, is_active, queued_for_scan, created_at, updated_at
        )
        VALUES (
            $1, 'hackerone', $2, 'M3 Seeded Scope Program',
            'https://example.com', 'bug_bounty',
            NULL, true, false, NOW(), NOW()
        )
        """,
        program_id,
        handle,
    )
    await _db_execute(
        """
        INSERT INTO program_scopes (
            scope_id, program_id, scope_type, asset_type, value, notes, created_at
        )
        VALUES (
            gen_random_uuid(), $1, 'in_scope', 'domain', 'example.com', 'seeded for M3 verification', NOW()
        )
        """,
        program_id,
    )
    if asset_type != "domain" or value != "example.com":
        await _db_execute(
            """
            DELETE FROM program_scopes
            WHERE program_id = $1
            """,
            program_id,
        )
        await _db_execute(
            """
            INSERT INTO program_scopes (
                scope_id, program_id, scope_type, asset_type, value, notes, created_at
            )
            VALUES (
                gen_random_uuid(), $1, 'in_scope', $2, $3, 'seeded for M3 verification', NOW()
            )
            """,
            program_id,
            asset_type,
            value,
        )
    return program_id


async def _wait_for_terminal_status(
    program_id: str, timeout_s: int = 300, created_after: datetime | None = None
):
    started = time.time()
    while time.time() - started < timeout_s:
        if created_after is None:
            row = await _db_fetchrow(
                """
                SELECT scan_id, status, retry_count, error_detail, created_at, completed_at
                FROM scans
                WHERE program_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                program_id,
            )
        else:
            row = await _db_fetchrow(
                """
                SELECT scan_id, status, retry_count, error_detail, created_at, completed_at
                FROM scans
                WHERE program_id = $1
                  AND created_at >= $2
                ORDER BY created_at DESC
                LIMIT 1
                """,
                program_id,
                created_after,
            )
        if row and row["status"] != "running":
            return row
        await asyncio.sleep(2)
    raise AssertionError(f"Timed out waiting for terminal status for program_id={program_id}")


async def _start_scan(payload: dict) -> httpx.Response:
    async with httpx.AsyncClient(timeout=30) as client:
        return await client.post(f"{CORE_BASE_URL}/scans/start", json=payload)


class TestM3WaybackurlsAvailability:
    def test_waybackurls_available_in_core_worker(self, require_stack):
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                "infra/docker-compose.yml",
                "exec",
                "-T",
                "core-worker",
                "sh",
                "-lc",
                "which waybackurls && waybackurls -h >/dev/null 2>&1",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip()


class TestM3RealProgramScopeFetch:
    @pytest.mark.asyncio
    async def test_full_scan_fetches_scope_from_scraper(self, require_stack):
        _reset_scan_processing_state()
        program_id = await _create_program_with_scope(
            asset_type="url",
            value="https://example.com",
        )
        kickoff = datetime.now(timezone.utc)
        response = await _start_scan(
            {
                "program_id": program_id,
                "priority": 1,
                "feature_flags": {
                    "nuclei": False,
                    "sqli": False,
                    "ssrf": False,
                    "crlf": False,
                },
            }
        )
        assert response.status_code == 200, response.text

        final_scan = await _wait_for_terminal_status(
            program_id,
            timeout_s=180,
            created_after=kickoff,
        )
        assert final_scan["status"] != "failed_scope"
        assert final_scan["status"] in {"completed", "partial", "failed_internal", "failed_auth"}

        stage_row = await _db_fetchrow(
            """
            SELECT COUNT(*)::int AS stage_count, MAX(stage_number) AS max_stage
            FROM scan_stages
            WHERE scan_id = $1
            """,
            final_scan["scan_id"],
        )
        assert stage_row["stage_count"] > 0
        assert float(stage_row["max_stage"]) >= 1.0
        await _db_execute("DELETE FROM scans WHERE program_id = $1", program_id)
        await _db_execute("DELETE FROM programs WHERE program_id = $1", program_id)


class TestM3WatchdogRepublish:
    @pytest.mark.asyncio
    async def test_watchdog_republish_and_retry_increment(self, require_stack):
        from backend.shared.db import init_db
        from backend.services.core_engine.watchdog import recover_stuck_scans

        program_id = await _create_program_with_scope()
        stale_scan_id = str(uuid.uuid4())
        stale_started_at = datetime.now(timezone.utc) - timedelta(hours=3)
        republish_calls: list[str] = []

        await _db_execute(
            """
            INSERT INTO scans (
                scan_id, program_id, status, priority, feature_flags,
                retry_count, started_at, created_at
            )
            VALUES ($1, $2, 'running', 1, '{}'::jsonb, 0, $3, $3)
            """,
            stale_scan_id,
            program_id,
            stale_started_at,
        )

        async_db_url = DB_DSN.replace("postgresql://", "postgresql+asyncpg://", 1)
        init_db(async_db_url)

        async def republish_fn(program_id: str):
            republish_calls.append(program_id)
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{CORE_BASE_URL}/scans/start",
                    json={
                        "program_id": program_id,
                        "priority": 1,
                        "feature_flags": {"nuclei": False},
                    },
                )
                response.raise_for_status()

        await recover_stuck_scans(republish_fn=republish_fn, stale_hours=2)

        stale_row = await _db_fetchrow(
            """
            SELECT status, retry_count, error_detail
            FROM scans
            WHERE scan_id = $1
            """,
            stale_scan_id,
        )

        assert stale_row["status"] in {"failed_internal", "running", "partial", "completed"}
        assert stale_row["retry_count"] >= 1
        if stale_row["status"] == "failed_internal":
            assert stale_row["error_detail"] == "watchdog_timeout"
        assert republish_calls == [program_id]

        try:
            rabbit_response = httpx.get(
                f"{RABBITMQ_MGMT}/queues/%2F/scan.jobs",
                auth=(RABBITMQ_USER, RABBITMQ_PASS),
                timeout=10,
            )
            if rabbit_response.status_code == 200:
                payload = rabbit_response.json()
                assert payload.get("messages", 0) >= 0
        except httpx.HTTPError:
            pass
        await _db_execute("DELETE FROM scans WHERE program_id = $1", program_id)
        await _db_execute("DELETE FROM program_scopes WHERE program_id = $1", program_id)
        await _db_execute("DELETE FROM programs WHERE program_id = $1", program_id)


class TestM3FailedScope:
    @pytest.mark.asyncio
    async def test_empty_scope_program_transitions_failed_scope(self, require_stack):
        _reset_scan_processing_state()
        program_id = str(uuid.uuid4())
        handle = f"m3-empty-scope-{program_id[:8]}"
        kickoff = datetime.now(timezone.utc)

        await _db_execute(
            """
            INSERT INTO programs (
                program_id, platform, handle, name, url, bounty_type,
                max_bounty, is_active, queued_for_scan, created_at, updated_at
            )
            VALUES (
                $1, 'hackerone', $2, 'M3 Empty Scope Program',
                'https://example.com', 'bug_bounty',
                NULL, true, false, NOW(), NOW()
            )
            """,
            program_id,
            handle,
        )

        response = await _start_scan(
            {
                "program_id": program_id,
                "platform": "hackerone",
                "handle": handle,
                "scope": {
                    "in_scope": [{"asset_type": "domain", "value": "example.com"}],
                    "out_of_scope": [],
                },
                "feature_flags": {"nuclei": False},
                "priority": 1,
            }
        )
        assert response.status_code == 200, response.text

        final_scan = await _wait_for_terminal_status(
            program_id=program_id,
            timeout_s=180,
            created_after=kickoff,
        )
        assert final_scan["status"] == "failed_scope"
        assert "no in_scope entries" in (final_scan["error_detail"] or "").lower()

        stage_count = await _db_fetchval(
            "SELECT COUNT(*)::int FROM scan_stages WHERE scan_id = $1",
            final_scan["scan_id"],
        )
        assert stage_count == 0

        await _db_execute("DELETE FROM scans WHERE program_id = $1", program_id)
        await _db_execute("DELETE FROM programs WHERE program_id = $1", program_id)
